// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/depiction_slot.h"

#include <algorithm>
#include <cmath>
#include <string>

#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/ui/widget_message.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

DepictionSlot::DepictionSlot() {
  // A key unique to us unless we're given one. (A counter, not our
  // address: a reused address could pick up some dead widget's viewer.)
  static int64_t next_key{};
  key_ = "depictionslot:" + std::to_string(next_key++);
}

DepictionSlot::~DepictionSlot() = default;

void DepictionSlot::SetDepiction(const std::string& json) {
  assert(g_base->InLogicThread());
  if (json == json_ && (depiction_.exists() || json.empty())) {
    return;
  }
  if (pressed_) {
    Release_();
  }
  json_ = json;
  if (json.empty()) {
    depiction_.Clear();
    return;
  }
  depiction_ =
      base::DepictionRegistry::Create(json, base::DepictionHost::kUI, key_);
}

auto DepictionSlot::GetPythonControl() -> PyObject* {
  return depiction_.exists() ? depiction_->GetPythonControl() : nullptr;
}

auto DepictionSlot::GetTintControl() -> base::DepictionTintControl* {
  return depiction_.exists() ? depiction_->GetTintControl() : nullptr;
}

auto DepictionSlot::GetContentBox(float width, float height) const
    -> std::optional<base::DepictionBox> {
  if (!depiction_.exists()) {
    return std::nullopt;
  }
  return depiction_->GetContentBox(
      base::FitDepictionBox({0.0f, 0.0f, width, height}, *depiction_, h_align_,
                            v_align_, suffix_.GetTrailingAspect()));
}

/// Physical pixels per unit of a widget's own space, as settled on
/// screen: where its corners sit in the widget hierarchy, which knows
/// nothing of transitions being played at draw time.
static auto PixelsPerUnit(const Widget& owner, float width) -> float {
  if (width <= 0.0f) {
    return 1.0f;
  }
  float x0{0.0f};
  float y0{0.0f};
  float x1{width};
  float y1{0.0f};
  owner.WidgetPointToScreen(&x0, &y0);
  owner.WidgetPointToScreen(&x1, &y1);
  base::Graphics* graphics = g_base->graphics;
  float virtual_width = graphics->screen_virtual_width();
  if (virtual_width <= 0.0f) {
    return 1.0f;
  }
  float pixel_width = std::abs(x1 - x0)
                      * graphics->virtual_bounds_rect().width() / virtual_width;
  return pixel_width / width;
}

/// A box scaled about its center.
static auto ScaledBox(const base::DepictionBox& box, float scale)
    -> base::DepictionBox {
  if (scale == 1.0f) {
    return box;
  }
  base::DepictionBox out{box};
  float cx = box.x + box.width * 0.5f;
  float cy = box.y + box.height * 0.5f;
  out.width *= scale;
  out.height *= scale;
  out.x = cx - out.width * 0.5f;
  out.y = cy - out.height * 0.5f;
  return out;
}

void DepictionSlot::DrawBacking_(const DrawArgs& args,
                                 const base::DepictionBox& box) {
  // Solid, so unmasked it goes in the opaque pass; a mask cutting our
  // edges needs the transparent one.
  base::TextureAsset* mask = args.mask_texture;
  bool masked = mask != nullptr;
  if (args.transparent != masked || (masked && !mask->loaded())) {
    return;
  }
  base::TextureAsset* white = g_ui_v1->assets().white.get();
  if (!white || !white->loaded()) {
    return;
  }
  base::SimpleComponent c(args.pass);
  c.SetTransparent(masked);
  c.SetColor(backing_color_[0], backing_color_[1], backing_color_[2], 1.0f);
  c.SetTexture(white);
  if (masked) {
    c.SetMaskTexture(mask);
    c.SetColorizeColor(frame_color_[0], frame_color_[1], frame_color_[2]);
  }
  {
    auto xf = c.ScopedTransform();
    c.Translate(box.x + box.width * 0.5f, box.y + box.height * 0.5f);
    c.Scale(box.width, box.height, 1.0f);
    c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
  }
  c.Submit();
}

void DepictionSlot::DrawDebugBox_(const DrawArgs& args,
                                  const base::DepictionBox& box) {
  base::TextureAsset* white = g_ui_v1->assets().white.get();
  if (!white || !white->loaded()) {
    return;
  }
  base::SimpleComponent c(args.pass);
  c.SetTransparent(true);
  c.SetColor(0.0f, 0.6f, 1.0f, 0.3f);
  c.SetTexture(white);
  {
    auto xf = c.ScopedTransform();
    c.Translate(box.x + box.width * 0.5f, box.y + box.height * 0.5f);
    c.Scale(box.width, box.height, 1.0f);
    c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
  }
  c.Submit();
}

void DepictionSlot::Draw(const DrawArgs& args) {
  assert(args.owner && args.pass);
  if (args.opacity < 0.001f) {
    return;
  }
  if (has_backing_) {
    DrawBacking_(
        args, ScaledBox({args.offset_x, args.offset_y, args.width, args.height},
                        args.scale));
  }
  if (!depiction_.exists()) {
    return;
  }

  // Once per frame (ui draws an opaque pass, then a transparent one).
  if (!args.transparent) {
    depiction_->MarkShown();
    depiction_->Update(args.pass->frame_def()->display_time_millisecs());
  }

  base::DepictionBox box = ScaledBox(
      base::FitDepictionBox(
          {args.offset_x, args.offset_y, args.width, args.height}, *depiction_,
          h_align_, v_align_, suffix_.GetTrailingAspect()),
      args.scale);
  const float* color_override = depiction_->EffectiveColorOverride(
      use_color_override_ ? color_override_ : nullptr);

  base::DepictionDrawContext context;
  context.pass = args.pass;
  context.transparent = args.transparent;
  context.box = box;
  context.brightness = args.brightness;
  context.opacity = args.opacity;
  context.disabled = args.disabled;
  context.pixels_per_unit = PixelsPerUnit(*args.owner, args.width);
  context.mask_texture = args.mask_texture;
  std::copy(std::begin(frame_color_), std::end(frame_color_),
            context.frame_color);
  context.color_override = color_override;
  // (No host switch for this here yet; a depiction's baked one counts.)
  context.team_coloring = depiction_->EffectiveTeamColoring(false);
  depiction_->Draw(context);
  suffix_.Draw(context, box, color_override);
  depiction_->DrawDebugBounds(context, ScaledBox({args.offset_x, args.offset_y,
                                                  args.width, args.height},
                                                 args.scale));
  if (debug_ && args.transparent) {
    DrawDebugBox_(args, depiction_->GetContentBox(box));
  }
}

auto DepictionSlot::HandleMessage(const base::WidgetMessage& m, float width,
                                  float height) -> bool {
  if (!take_input_ || !depiction_.exists()) {
    return false;
  }
  base::DepictionInput* input = depiction_->GetInput();
  if (input == nullptr) {
    return false;
  }
  switch (m.type) {
    case base::WidgetMessage::Type::kMouseDown: {
      const float x = m.fval1;
      const float y = m.fval2;
      if (x < 0.0f || x >= width || y < 0.0f || y >= height) {
        return false;
      }
      if (input->HandlePress(x / width, y / height)) {
        pressed_ = true;
        return true;
      }
      return false;
    }
    case base::WidgetMessage::Type::kMouseMove:
      // Drags of a press we took (not claimed, so hover etc. still
      // reach others).
      if (pressed_ && width > 0.0f && height > 0.0f) {
        input->HandleDrag(m.fval1 / width, m.fval2 / height);
      }
      return false;
    case base::WidgetMessage::Type::kMouseUp:
    case base::WidgetMessage::Type::kMouseCancel:
      // Only a press we took gets a release.
      if (pressed_) {
        Release_();
        return true;
      }
      return false;
    default:
      return false;
  }
}

void DepictionSlot::Release_() {
  pressed_ = false;
  if (depiction_.exists()) {
    if (base::DepictionInput* input = depiction_->GetInput()) {
      input->HandleRelease();
    }
  }
}

}  // namespace ballistica::ui_v1
