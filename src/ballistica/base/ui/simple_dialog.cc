// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/simple_dialog.h"

#include <algorithm>
#include <cmath>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/graphics/text/text_graphics.h"

namespace ballistica::base {

/// Fraction of the virtual safe area's width the dialog spans (at scale 1.0).
const float kDialogWidthFraction = 2.0f / 3.0f;

/// Master scale for the whole dialog. Every metric derives from the dialog
/// width, so scaling the width here uniformly scales the entire dialog
/// (panel, text, bar, button, margins).
const float kDialogScale = 0.8f;

/// Target height of one line of TITLE text, as a fraction of the dialog width.
/// The title is rendered at exactly this scale (shrinking only to fit the
/// bounds), and its area is sized to a single line of it. Tuned to reproduce
/// the previous look (the title filled a ~6%-of-width band).
const float kTitleLineHeightFraction = 0.06f;

/// Body (message) text is rendered at this fraction of the title's scale, so
/// it reads a touch smaller than the title rather than ballooning to fill its
/// area as it used to.
const float kMessageScaleFactor = 0.8f;

/// The message area is sized to hold this many lines of body text at the
/// target scale. A shorter message simply leaves empty space below it (the
/// text is top-aligned); a longer one is scaled down to fit.
const float kMessageAreaLines = 3.0f;

/// How long the button shows its pressed glow after a key/controller
/// activation (which is instantaneous, unlike a held mouse press).
const millisecs_t kButtonFlashMillisecs = 150;

/// Opaque backing color. A lightened version of the dev-console's dark purple
/// so the dialog reads clearly over the black of early boot (construct-mode),
/// where it would otherwise barely stand out.
const float kPanelColorR = 0.25f;
const float kPanelColorG = 0.21f;
const float kPanelColorB = 0.33f;

/// Button body color (and its brighter pressed/flash variant). Kept clearly
/// lighter than the panel so the button reads as a raised control against it.
const float kButtonColorR = 0.45f;
const float kButtonColorG = 0.38f;
const float kButtonColorB = 0.56f;
const float kButtonPressedColorR = 0.62f;
const float kButtonPressedColorG = 0.55f;
const float kButtonPressedColorB = 0.74f;

/// Debug aid: when true, draw faint rects behind the title, message, and
/// button-label regions so their layout bounds are visible while tuning. Must
/// stay false in committed code.
const bool kSimpleDialogShowBounds = false;

/// Draw a faint debug rect filling the given region (used for ShowBounds).
static void DrawBoundsRect_(FrameDef* frame_def, float cx, float cy, float w,
                            float h, float z) {
  SimpleComponent c(frame_def->overlay_front_pass());
  c.SetTransparent(true);
  c.SetColor(0.0f, 0.0f, 0.0f, 0.3f);
  {
    auto xf = c.ScopedTransform();
    c.Translate(cx, cy, z);
    c.Scale(w, h, 1.0f);
    c.DrawMeshAsset(
        g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
  }
  c.Submit();
}

/// Draw a prebuilt rounded-rect ninepatch mesh (opaque) centered at (cx, cy).
/// The mesh's local space spans [0,w] x [0,h]; we translate to its lower-left.
static void DrawRoundedRectMesh_(FrameDef* frame_def, NinePatchMesh* mesh,
                                 float cx, float cy, float w, float h, float z,
                                 float r, float g, float b) {
  SimpleComponent c(frame_def->overlay_front_pass());
  c.SetTransparent(true);
  c.SetColor(r, g, b, 1.0f);
  c.SetTexture(
      g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesCircle));
  {
    auto xf = c.ScopedTransform();
    c.Translate(cx - w * 0.5f, cy - h * 0.5f, z);
    c.DrawMesh(mesh);
  }
  c.Submit();
}

void SimpleDialog::EnsureRoundedMesh_(Object::Ref<NinePatchMesh>* mesh,
                                      float* cur_w, float* cur_h, float w,
                                      float h, float corner_radius) {
  // Ninepatch corners must not be scaled (it'd distort them), so we rebuild
  // the mesh at the exact size whenever it changes rather than scaling.
  if (mesh->exists() && *cur_w == w && *cur_h == h) {
    return;
  }
  *cur_w = w;
  *cur_h = h;
  *mesh = Object::New<NinePatchMesh>(
      0.0f, 0.0f, 0.0f, w, h,
      NinePatchMesh::BorderForRadius(corner_radius, w, h),
      NinePatchMesh::BorderForRadius(corner_radius, h, w),
      NinePatchMesh::BorderForRadius(corner_radius, w, h),
      NinePatchMesh::BorderForRadius(corner_radius, h, w));
}

SimpleDialog::SimpleDialog(int id) : id_{id} {}

void SimpleDialog::SetState(const std::string& title,
                            const std::string& message, float progress,
                            const std::string& button_label) {
  // Rebuild text-meshes only when the underlying string actually changes.
  if (title != title_) {
    title_ = title;
    title_text_group_.SetText(title_, TextMesh::HAlign::kCenter,
                              TextMesh::VAlign::kCenter);
  }
  if (message != message_) {
    message_ = message;
    message_text_group_.SetText(message_, TextMesh::HAlign::kCenter,
                                TextMesh::VAlign::kCenter);
  }
  if (button_label != button_label_) {
    button_label_ = button_label;
    if (!button_label_.empty()) {
      button_text_group_.SetText(button_label_, TextMesh::HAlign::kCenter,
                                 TextMesh::VAlign::kCenter);
    }
  }
  progress_ = progress;
}

void SimpleDialog::Draw(FrameDef* frame_def) {
  float vwidth = g_base->graphics->screen_virtual_width();
  float vheight = g_base->graphics->screen_virtual_height();

  // Width is a fixed fraction of the safe area; the dialog's HEIGHT is derived
  // from its stacked contents, so adding the bar/button makes the dialog
  // taller rather than shrinking the message area. Centered in the (full)
  // virtual screen.
  float safe_width, safe_height;
  Graphics::GetBaseVirtualRes(&safe_width, &safe_height);
  float width = safe_width * kDialogWidthFraction * kDialogScale;
  float cx = vwidth * 0.5f;
  float cy = vheight * 0.5f;

  // Resolve the progress value up front (demo_animate_ cycles it for
  // look-iteration) so we know whether a bar is present when sizing.
  float progress = progress_;
  if (demo_animate_ && progress_ >= 0.0f) {
    const float kCycleSeconds = 3.0f;
    progress = static_cast<float>(
        std::fmod(frame_def->display_time(), kCycleSeconds) / kCycleSeconds);
  }
  bool has_bar = progress >= 0.0f;
  bool has_button = !button_label_.empty();

  // When the bounds-debug flag is on, alternate once per second between the
  // real geometry and the layout-bounds boxes so the two can be compared.
  // (Off in committed code -> always real geometry.)
  bool draw_bounds_now = kSimpleDialogShowBounds
                         && std::fmod(frame_def->display_time(), 2.0) >= 1.0;

  // Fixed target text scales. Rather than scaling each text block to fill a
  // fixed area (which made a short message balloon), we fix the scales up front
  // and derive the text areas from them. The single-line height comes from a
  // one-char measurement -- GetStringHeight is line-count * row-height, so any
  // single-line string yields exactly one line's height. The per-string scales
  // computed at draw time below only ever shrink from these to fit.
  float line_height =
      std::max(0.0001f, g_base->text_graphics->GetStringHeight("X"));
  float title_scale = width * kTitleLineHeightFraction / line_height;
  float message_scale = title_scale * kMessageScaleFactor;

  // Vertical metrics, all absolute. Most derive from the fixed width; the two
  // text areas instead take their height from the scales above -- one line for
  // the title, kMessageAreaLines for the message.
  float margin = width * 0.025f;
  float gap = width * 0.02f;
  float title_h = line_height * title_scale;
  float bar_h = width * 0.04f;
  float message_h = line_height * message_scale * kMessageAreaLines;
  float button_h = width * 0.07f;
  float button_w = button_h * 3.0f;

  // Sum the stacked pieces (plus top/bottom margins) for the total height.
  float height = margin + title_h + gap + message_h + margin;
  if (has_bar) {
    height += gap + bar_h;
  }
  if (has_button) {
    height += gap + button_h;
  }

  // Background panel. Real geometry: an opaque dark-purple rounded rect (like
  // the dev-console backing). Bounds mode: the flat translucent placeholder.
  if (draw_bounds_now) {
    SimpleComponent c(frame_def->overlay_front_pass());
    c.SetTransparent(true);
    c.SetColor(0.0f, 0.0f, 1.0f, 0.5f);
    {
      auto xf = c.ScopedTransform();
      c.Translate(cx, cy, kSimpleDialogZDepth);
      c.Scale(width, height, 1.0f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
    }
    c.Submit();
  } else {
    EnsureRoundedMesh_(&panel_mesh_, &panel_mesh_w_, &panel_mesh_h_, width,
                       height, width * 0.06f);
    DrawRoundedRectMesh_(frame_def, panel_mesh_.get(), cx, cy, width, height,
                         kSimpleDialogZDepth, kPanelColorR, kPanelColorG,
                         kPanelColorB);
  }

  // Walk down from the top edge, placing each element in turn.
  float y = cy + height * 0.5f - margin;

  // Title.
  float title_area_width = width * 0.9f;
  float title_cy = y - title_h * 0.5f;
  y -= title_h;
  if (draw_bounds_now) {
    DrawBoundsRect_(frame_def, cx, title_cy, title_area_width, title_h,
                    kSimpleDialogZDepth + 0.002f);
  }
  // Title text: render at the fixed title scale, shrinking only to fit the
  // area's width (or its one-line height, for a multi-line title).
  if (!title_.empty()) {
    const std::string& title = title_text_group_.text();
    float string_width =
        std::max(0.0001f, g_base->text_graphics->GetStringWidth(title));
    float string_height =
        std::max(0.0001f, g_base->text_graphics->GetStringHeight(title));
    float text_scale = std::min({title_scale, title_area_width / string_width,
                                 title_h / string_height});
    SimpleComponent c(frame_def->overlay_front_pass());
    c.SetTransparent(true);
    c.SetFlatness(1.0f);
    c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
    int elem_count = title_text_group_.GetElementCount();
    for (int e = 0; e < elem_count; e++) {
      c.SetTexture(title_text_group_.GetElementTexture(e));
      {
        auto xf = c.ScopedTransform();
        c.Translate(cx, title_cy, kSimpleDialogZDepth + 0.005f);
        c.Scale(text_scale, text_scale, 1.0f);
        c.DrawMesh(title_text_group_.GetElementMesh(e));
      }
    }
    c.Submit();
  }

  // Progress bar (if any): a faint track plus a left-anchored fill scaled by
  // the progress value [0..1].
  if (has_bar) {
    y -= gap;
    float bar_width = width * 0.8f;
    float bar_cy = y - bar_h * 0.5f;
    y -= bar_h;
    progress = std::min(1.0f, std::max(0.0f, progress));

    // Track (faint background).
    {
      SimpleComponent c(frame_def->overlay_front_pass());
      c.SetTransparent(true);
      c.SetColor(0.0f, 0.0f, 0.0f, 0.4f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(cx, bar_cy, kSimpleDialogZDepth + 0.002f);
        c.Scale(bar_width, bar_h, 1.0f);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
      }
      c.Submit();
    }

    // Fill (left-anchored; width scaled by progress).
    {
      float fill_width = bar_width * progress;
      float fill_height = bar_h * 0.7f;
      float fill_left = cx - bar_width * 0.5f;
      float fill_cx = fill_left + fill_width * 0.5f;
      SimpleComponent c(frame_def->overlay_front_pass());
      c.SetTransparent(true);
      c.SetColor(0.3f, 0.7f, 1.0f, 1.0f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(fill_cx, bar_cy, kSimpleDialogZDepth + 0.003f);
        c.Scale(fill_width, fill_height, 1.0f);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
      }
      c.Submit();
    }
  }

  // Message text-area: top-aligned multi-line text rendered at the fixed
  // message scale, shrinking only to fit the area's width or height.
  y -= gap;
  float message_top = y;
  float message_cy = y - message_h * 0.5f;
  y -= message_h;
  float message_area_width = width * 0.9f;
  if (draw_bounds_now) {
    DrawBoundsRect_(frame_def, cx, message_cy, message_area_width, message_h,
                    kSimpleDialogZDepth + 0.002f);
  }
  if (!message_.empty()) {
    const std::string& message = message_text_group_.text();
    float string_width =
        std::max(0.0001f, g_base->text_graphics->GetStringWidth(message));
    float string_height =
        std::max(0.0001f, g_base->text_graphics->GetStringHeight(message));
    float text_scale =
        std::min({message_scale, message_area_width / string_width,
                  message_h / string_height});
    // Top-align: the text-group is centered on its draw point
    // (VAlign::kCenter), so drop the draw point by half the scaled block
    // height to pin the block's top to the area top.
    float block_height = string_height * text_scale;
    float text_y = message_top - block_height * 0.5f;
    SimpleComponent c(frame_def->overlay_front_pass());
    c.SetTransparent(true);
    c.SetFlatness(1.0f);
    c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
    int elem_count = message_text_group_.GetElementCount();
    for (int e = 0; e < elem_count; e++) {
      c.SetTexture(message_text_group_.GetElementTexture(e));
      {
        auto xf = c.ScopedTransform();
        c.Translate(cx, text_y, kSimpleDialogZDepth + 0.005f);
        c.Scale(text_scale, text_scale, 1.0f);
        c.DrawMesh(message_text_group_.GetElementMesh(e));
      }
    }
    c.Submit();
  }

  // The single (centered) button.
  if (has_button) {
    y -= gap;
    button_.width = button_w;
    button_.height = button_h;
    button_.center_x = cx;
    button_.center_y = y - button_h * 0.5f;
    y -= button_h;
    // Pressed look from a held mouse press, or from the brief post-activation
    // glow (key/controller).
    bool pressed = button_.pressed
                   || frame_def->app_time_millisecs() < button_flash_end_time_;
    DrawButton_(frame_def, button_, &button_text_group_, draw_bounds_now,
                pressed);
  }
}

void SimpleDialog::DrawButton_(FrameDef* frame_def, const Button_& b,
                               TextGroup* label, bool bounds_mode,
                               bool pressed) {
  // Button body. Real geometry: an opaque rounded rect in the dev-console
  // button color (brightened while pressed). Bounds mode: the flat placeholder
  // plus the label-bounds box.
  if (bounds_mode) {
    SimpleComponent c(frame_def->overlay_front_pass());
    c.SetTransparent(true);
    if (pressed) {
      c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
    } else {
      c.SetColor(0.5f, 0.5f, 0.6f, 0.9f);
    }
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.center_x, b.center_y, kSimpleDialogZDepth + 0.004f);
      c.Scale(b.width, b.height, 1.0f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
    }
    c.Submit();
  } else {
    EnsureRoundedMesh_(&button_mesh_, &button_mesh_w_, &button_mesh_h_, b.width,
                       b.height, b.height * 0.28f);
    if (pressed) {
      DrawRoundedRectMesh_(frame_def, button_mesh_.get(), b.center_x,
                           b.center_y, b.width, b.height,
                           kSimpleDialogZDepth + 0.004f, kButtonPressedColorR,
                           kButtonPressedColorG, kButtonPressedColorB);
    } else {
      DrawRoundedRectMesh_(frame_def, button_mesh_.get(), b.center_x,
                           b.center_y, b.width, b.height,
                           kSimpleDialogZDepth + 0.004f, kButtonColorR,
                           kButtonColorG, kButtonColorB);
    }
  }

  // Label text (always white for readability), scaled to fit a region inset
  // from the button edges.
  {
    float label_area_width = b.width * 0.85f;
    float label_area_height = b.height * 0.65f;
    if (bounds_mode) {
      DrawBoundsRect_(frame_def, b.center_x, b.center_y, label_area_width,
                      label_area_height, kSimpleDialogZDepth + 0.005f);
    }
    const std::string& text = label->text();
    float string_width =
        std::max(0.0001f, g_base->text_graphics->GetStringWidth(text));
    float string_height =
        std::max(0.0001f, g_base->text_graphics->GetStringHeight(text));
    float text_scale = std::min(label_area_width / string_width,
                                label_area_height / string_height);
    SimpleComponent c(frame_def->overlay_front_pass());
    c.SetTransparent(true);
    c.SetFlatness(1.0f);
    c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
    int elem_count = label->GetElementCount();
    for (int e = 0; e < elem_count; e++) {
      c.SetTexture(label->GetElementTexture(e));
      {
        auto xf = c.ScopedTransform();
        c.Translate(b.center_x, b.center_y, kSimpleDialogZDepth + 0.006f);
        c.Scale(text_scale, text_scale, 1.0f);
        c.DrawMesh(label->GetElementMesh(e));
      }
    }
    c.Submit();
  }
}

auto SimpleDialog::HandleMouseDown(int button, float x, float y) -> bool {
  if (button != 1 || !has_button()) {
    return false;
  }
  if (button_.Contains(x, y)) {
    button_.pressed = true;
    return true;
  }
  return false;
}

auto SimpleDialog::HandleMouseUp(int button, float x, float y) -> bool {
  // Fire on release only if still within the button that was pressed.
  bool fired{};
  if (button_.pressed) {
    button_.pressed = false;
    if (button_.Contains(x, y)) {
      fired = true;
    }
  }
  return fired;
}

void SimpleDialog::HandleMouseCancel(int button, float x, float y) {
  button_.pressed = false;
}

auto SimpleDialog::Activate() -> bool {
  // OK/confirm from a non-mouse device: fire the button regardless of
  // position, and glow it briefly (there's no held state to show like a mouse
  // press has).
  if (!has_button()) {
    return false;
  }
  button_flash_end_time_ = g_core->AppTimeMillisecs() + kButtonFlashMillisecs;
  return true;
}

}  // namespace ballistica::base
