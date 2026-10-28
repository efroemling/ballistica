// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/debug_rect_widget.h"

#include <algorithm>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/rect_outline_mesh.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_group.h"

namespace ballistica::ui_v1 {

/// Labels' text scale and padding, in the units they draw in (screen
/// units for front rects, so labels read the same at any widget scale).
static const float kInfoTextScale{0.6f};
static const float kInfoPad{3.0f};

/// Where front rects draw in root space's depth (in front of the UI,
/// which fills 0 to 1 there; see UIV1FeatureSet::Draw()).
static const float kFrontDepthStart{0.99f};
static const float kFrontDepthEnd{0.9999f};

int DebugRectWidget::live_count_{};
std::vector<DebugRectWidget::Transform_> DebugRectWidget::transforms_;
std::vector<DebugRectWidget::Shape_> DebugRectWidget::front_queue_;
const Widget* DebugRectWidget::topmost_{};

DebugRectWidget::DebugRectWidget() {
  assert(g_base->InLogicThread());
  live_count_++;
}

DebugRectWidget::~DebugRectWidget() {
  assert(g_base->InLogicThread());
  live_count_--;
  assert(live_count_ >= 0);
}

auto DebugRectWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  return false;
}

void DebugRectWidget::SetInfo(const std::string& info) {
  if (info.empty()) {
    info_.Clear();
    return;
  }
  if (!info_.exists()) {
    info_ = Object::New<base::TextGroup>();
  }
  info_->SetText(info, base::TextMesh::HAlign::kCenter,
                 base::TextMesh::VAlign::kCenter);
  // (Measured at draw; negative until then.)
  info_width_ = -1.0f;
  g_base->text_graphics->WarmUpStringAsync(info);
}

void DebugRectWidget::SetSelectedWidget(Widget* w) {
  selected_widget_ = w;
  has_selected_widget_ = (w != nullptr);
}

void DebugRectWidget::BeginFrame(float x_offset, float y_offset) {
  assert(g_base->InLogicThread());
  transforms_.clear();
  front_queue_.clear();
  topmost_ = nullptr;
  Transform_ root;
  root.x = x_offset;
  root.y = y_offset;
  transforms_.push_back(root);
}

void DebugRectWidget::PushChildTransform(float x, float y, float scale,
                                         bool has_clip, const Rect& clip,
                                         const Widget* child, bool toplevel) {
  // Tracking may switch on mid-frame (a debug rect made while drawing);
  // wait for the next frame's BeginFrame() then.
  if (transforms_.empty()) {
    return;
  }
  const Transform_& parent{transforms_.back()};
  Transform_ out;
  out.x = parent.x + parent.s * x;
  out.y = parent.y + parent.s * y;
  out.s = parent.s * scale;
  out.has_clip = parent.has_clip;
  out.clip = parent.clip;
  if (has_clip) {
    Rect sclip{parent.x + parent.s * clip.l, parent.y + parent.s * clip.b,
               parent.x + parent.s * clip.r, parent.y + parent.s * clip.t};
    if (out.has_clip) {
      out.clip =
          Rect{std::max(out.clip.l, sclip.l), std::max(out.clip.b, sclip.b),
               std::min(out.clip.r, sclip.r), std::min(out.clip.t, sclip.t)};
    } else {
      out.clip = sclip;
      out.has_clip = true;
    }
  }
  // Stacks draw their windows bottom to top, and the root draws its
  // overlay stack last, so the last top-level window drawn is topmost.
  if (toplevel) {
    out.toplevel = child;
    topmost_ = child;
  } else {
    out.toplevel = parent.toplevel;
  }
  transforms_.push_back(out);
}

void DebugRectWidget::PopChildTransform() {
  // (A push skipped for want of a frame skipped its pop too.)
  if (transforms_.size() > 1) {
    transforms_.pop_back();
  }
}

void DebugRectWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  if (!draw_transparent) {
    return;
  }
  if (has_selected_widget_) {
    Widget* sel{selected_widget_.get()};
    if (sel == nullptr || !sel->IsHierarchySelected()) {
      return;
    }
  }
  if (info_.exists() && info_width_ < 0.0f) {
    auto width = g_base->text_graphics->TryGetStringWidth(info_->text());
    if (width.has_value()) {
      info_width_ = *width;
    }
  }
  Shape_ shape;
  shape.color_r = color_r_;
  shape.color_g = color_g_;
  shape.color_b = color_b_;
  shape.opacity = opacity_;
  shape.edge_width = edge_width_;
  shape.fill_opacity = fill_opacity_;
  shape.info_anchor = info_anchor_;
  // (No label until it's measured.)
  if (info_width_ >= 0.0f) {
    shape.info = info_;
    shape.info_width = info_width_;
  }

  if (front_) {
    // Record where we are on screen; we draw with the front queue.
    if (transforms_.size() < 2) {
      // Not inside a tracked tree draw (we're never the root).
      return;
    }
    const Transform_& xf{transforms_.back()};
    shape.rect = Rect{xf.x, xf.y, xf.x + xf.s * width_, xf.y + xf.s * height_};
    shape.has_clip = xf.has_clip;
    shape.clip = xf.clip;
    shape.toplevel = xf.toplevel;
    front_queue_.push_back(std::move(shape));
    return;
  }

  // Drawing in place, in our own space (labels and edges then scale
  // with us).
  shape.rect = Rect{0.0f, 0.0f, width_, height_};
  DrawShape_(pass, shape, 0.5f);
}

void DebugRectWidget::DrawFrontQueue(base::RenderPass* pass) {
  assert(g_base->InLogicThread());
  transforms_.clear();
  if (front_queue_.empty()) {
    return;
  }
  // Root space is screen space; we draw at its front (a sliver each,
  // later ones in front). Only the topmost window's rects (and any
  // outside every window).
  float count{static_cast<float>(front_queue_.size())};
  float step{(kFrontDepthEnd - kFrontDepthStart) / count};
  for (size_t i = 0; i < front_queue_.size(); ++i) {
    const Shape_& shape{front_queue_[i]};
    if (shape.toplevel != nullptr && shape.toplevel != topmost_) {
      continue;
    }
    DrawShape_(pass, shape, kFrontDepthStart + step * static_cast<float>(i));
  }
  front_queue_.clear();
  topmost_ = nullptr;
}

void DebugRectWidget::DrawShape_(base::RenderPass* pass, const Shape_& shape,
                                 float z) {
  if (shape.has_clip
      && (shape.clip.l >= shape.clip.r || shape.clip.b >= shape.clip.t)) {
    return;
  }
  const Rect& r{shape.rect};
  float ew{shape.edge_width};
  base::TextureAsset* white{
      g_base->assets->SolidTexture(base::SolidTextureColor::kWhite)};

  // Premultiplied textures want rgb premultiplied by alpha (see
  // docs/design/premultiplied-alpha.md).
  auto set_color = [white](base::SimpleComponent* c, float red, float green,
                           float blue, float alpha) {
    float cmul{(white != nullptr && white->premultiplied()) ? alpha : 1.0f};
    c->SetColor(red * cmul, green * cmul, blue * cmul, alpha);
  };

  base::SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetTexture(white);
  if (shape.has_clip) {
    c.ScissorPush(shape.clip);
  }

  // Fill.
  if (shape.fill_opacity > 0.0f && r.width() > 0.0f && r.height() > 0.0f) {
    set_color(&c, shape.color_r, shape.color_g, shape.color_b,
              std::min(1.0f, shape.fill_opacity));
    auto xf = c.ScopedTransform();
    c.Translate(0.5f * (r.l + r.r), 0.5f * (r.b + r.t), z);
    c.Scale(r.width(), r.height(), 1.0f);
    c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
  }

  // Edges, inside our bounds (so their outer edge marks our exact
  // bounds, and rects sharing an edge each show theirs).
  if (ew > 0.0f && shape.opacity > 0.0f) {
    set_color(&c, shape.color_r, shape.color_g, shape.color_b, shape.opacity);
    auto mesh = Object::New<base::RectOutlineMesh>(r.l, r.b, z, r.width(),
                                                   r.height(), ew);
    c.DrawMesh(mesh.get());
  }

  // Label, on a dark backdrop, inside our edges at its anchor.
  if (shape.info.exists() && shape.opacity > 0.0f) {
    float tscale{kInfoTextScale};
    float pad{kInfoPad};
    float box_w{shape.info_width * tscale + 2.0f * pad};
    float box_h{base::kTextCapHeight * tscale + 2.0f * pad};
    float inset{ew};
    float cx{};
    float cy{};
    switch (shape.info_anchor) {
      case InfoAnchor::kTopLeft:
      case InfoAnchor::kLeft:
      case InfoAnchor::kBottomLeft:
        cx = r.l + inset + 0.5f * box_w;
        break;
      case InfoAnchor::kTop:
      case InfoAnchor::kCenter:
      case InfoAnchor::kBottom:
        cx = 0.5f * (r.l + r.r);
        break;
      case InfoAnchor::kTopRight:
      case InfoAnchor::kRight:
      case InfoAnchor::kBottomRight:
        cx = r.r - inset - 0.5f * box_w;
        break;
    }
    switch (shape.info_anchor) {
      case InfoAnchor::kTopLeft:
      case InfoAnchor::kTop:
      case InfoAnchor::kTopRight:
        cy = r.t - inset - 0.5f * box_h;
        break;
      case InfoAnchor::kLeft:
      case InfoAnchor::kCenter:
      case InfoAnchor::kRight:
        cy = 0.5f * (r.b + r.t);
        break;
      case InfoAnchor::kBottomLeft:
      case InfoAnchor::kBottom:
      case InfoAnchor::kBottomRight:
        cy = r.b + inset + 0.5f * box_h;
        break;
    }
    {
      set_color(&c, 0.0f, 0.0f, 0.0f, 0.6f * shape.opacity);
      auto xf = c.ScopedTransform();
      c.Translate(cx, cy, z);
      c.Scale(box_w, box_h, 1.0f);
      c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
    }
    base::TextGroup& tgrp{*shape.info};
    int elem_count{tgrp.GetElementCount()};
    {
      auto xf = c.ScopedTransform();
      c.Translate(cx, cy, z);
      c.Scale(tscale, tscale, 1.0f);
      c.SetFlatness(1.0f);
      for (int e = 0; e < elem_count; e++) {
        base::TextureAsset* tex{tgrp.GetElementTexture(e)};
        float cmul{tex->premultiplied() ? shape.opacity : 1.0f};
        c.SetColor(std::min(1.0f, 0.4f + shape.color_r) * cmul,
                   std::min(1.0f, 0.4f + shape.color_g) * cmul,
                   std::min(1.0f, 0.4f + shape.color_b) * cmul, shape.opacity);
        c.SetTexture(tex);
        c.DrawMesh(tgrp.GetElementMesh(e));
      }
    }
  }
  if (shape.has_clip) {
    c.ScissorPop();
  }
  c.Submit();
}

}  // namespace ballistica::ui_v1
