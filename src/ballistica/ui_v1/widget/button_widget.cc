// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/button_widget.h"

#include <algorithm>
#include <memory>
#include <string>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/support/lang_str.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/ui_v1/widget/depiction_slot.h"

namespace ballistica::ui_v1 {

/// Label margin at each side for a centered label (and at the far side of
/// a left/right-aligned one when there is no accessory).
/// A standard-disabled button's body grey, as a multiple of its color's
/// luminance.
constexpr float kDisabledBodyGreyScale{0.85f};

/// A standard-disabled button's icon alpha, as a multiple of its own.
constexpr float kDisabledIconAlphaScale{0.4f};

constexpr float kTextSideMargin{15.0f};

/// Room kept above and below a label; a label taller than what's left
/// (a wrapped multi-line one, typically) shrinks to fit, as an over-wide
/// one does sideways. Height is plain row spacing (32 per line), not
/// glyph extents.
constexpr float kTextVertMargin{4.0f};

/// Distance from our edge to a left/right-aligned label.
constexpr float kAlignedTextInset{20.0f};

/// Gap between our right edge and an accessory glyph's area.
constexpr float kAccessoryEdgeInset{8.0f};

/// Width of the area an accessory glyph is centered in.
constexpr float kAccessoryWidth{36.0f};

/// Everything at our right end given over to an accessory; the label
/// stops here.
constexpr float kAccessoryRegion{kAccessoryEdgeInset + kAccessoryWidth};

/// Scale an accessory glyph draws at.
constexpr float kAccessoryScale{0.69f};

ButtonWidget::ButtonWidget()
    : birth_time_millisecs_{
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)} {
  text_ = Object::New<TextWidget>();
  SetText("Button");
  text_->SetVAlign(TextWidget::VAlign::kCenter);
  text_->SetHAlign(TextWidget::HAlign::kCenter);
  text_->SetWidth(0.0f);
  text_->SetHeight(0.0f);
}

ButtonWidget::~ButtonWidget() = default;

auto ButtonWidget::GetDepictionSlot() -> DepictionSlot& {
  if (!depiction_slot_) {
    depiction_slot_ = std::make_unique<DepictionSlot>();
  }
  return *depiction_slot_;
}

void ButtonWidget::SetTextResScale(float val) { text_->set_res_scale(val); }

void ButtonWidget::SetOnActivateCall(PyObject* call_obj) {
  on_activate_call_ = Object::New<base::PythonContextCall>(call_obj);
}

void ButtonWidget::SetTextLiteral(bool val) { text_->SetLiteral(val); }

void ButtonWidget::SetText(const std::string& text_in) {
  std::string text = Utils::GetValidUTF8(text_in.c_str(), "bwst");
  text_->SetText(text);

  // Also cache our current text width; don't want to calc this with each draw
  // (especially now that we may have to ask the OS to do it).
  text_width_dirty_ = true;
}

void ButtonWidget::SetLangStr(std::shared_ptr<const base::LangStr> val) {
  text_->SetLangStr(std::move(val));
  text_width_dirty_ = true;
}

void ButtonWidget::SetAccessory(Accessory val) {
  accessory_ = val;
  switch (val) {
    case Accessory::kNone:
      accessory_text_.Clear();
      break;
    case Accessory::kPopup:
      accessory_text_ = Object::New<TextWidget>();
      accessory_text_->SetLiteral(true);
      accessory_text_->SetVAlign(TextWidget::VAlign::kCenter);
      accessory_text_->SetHAlign(TextWidget::HAlign::kCenter);
      accessory_text_->SetWidth(0.0f);
      accessory_text_->SetHeight(0.0f);

      accessory_text_->SetText(
          g_base->assets->CharStr(SpecialChar::kPopupIcon));
      break;
  }
}

void ButtonWidget::SetTextHAlign(TextWidget::HAlign val) {
  text_h_align_ = val;
  text_->SetHAlign(val);
}

void ButtonWidget::SetTexture(base::TextureAsset* val) { texture_ = val; }

void ButtonWidget::SetMaskTexture(base::TextureAsset* val) {
  mask_texture_ = val;
}

void ButtonWidget::SetTintTexture(base::TextureAsset* val) {
  tint_texture_ = val;
}

void ButtonWidget::SetIcon(base::TextureAsset* val) { icon_ = val; }

void ButtonWidget::OnRepeatTimerExpired() {
  // Repeat our action unless we somehow lost focus but didn't get a mouse-up.
  if (IsHierarchySelected() && pressed_) {
    // Gather up any user code triggered by this stuff and run it at the end
    // before we return.
    base::UI::OperationContext ui_op_context;

    DoActivate(true);

    // Speed up repeats after the first.
    repeat_timer_->SetLength(0.150);

    // Run any calls built up by UI callbacks.
    ui_op_context.Finish();

  } else {
    repeat_timer_.Clear();
  }
}

void ButtonWidget::SetMeshOpaque(base::MeshAsset* val) { mesh_opaque_ = val; }

void ButtonWidget::SetMeshTransparent(base::MeshAsset* val) {
  mesh_transparent_ = val;
}

auto ButtonWidget::GetWidth() -> float { return width_; }
auto ButtonWidget::GetHeight() -> float { return height_; }

auto ButtonWidget::GetMult(millisecs_t current_time) const -> float {
  float mult = 1.0f;

  if ((pressed_ && hover_)
      || (current_time - last_activate_time_millisecs_ < 200)) {
    if (pressed_ && hover_) {
      mult = 3.0f;
    } else {
      float x = static_cast<float>(current_time - last_activate_time_millisecs_)
                / 200.0f;
      mult = 1.0f + 3.0f * (1.0f - x * x);
    }
  } else if ((IsHierarchySelected() && g_base->ui->ShouldHighlightWidgets())) {
    mult =
        0.8f
        + std::abs(sinf(static_cast<float>(current_time) * 0.006467f)) * 0.2f;

    if (!texture_.exists()) {
      mult *= 1.7f;
    } else {
      // Let's make custom textures pulsate brighter since they can be dark/etc.
      mult *= 2.0f;
    }
  } else {
    // Slightly highlighting all buttons for idle hovering (but ONLY with a
    // mouse; not touchscreen).
    if (hover_ && !g_base->ui->touch_mode()) {
      // if (mouse_over_) {
      mult = 1.2f;
    }
  }
  return mult;
}

auto ButtonWidget::GetDrawBrightness(millisecs_t time) const -> float {
  return GetMult(time);
}

void ButtonWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  millisecs_t current_time = pass->frame_def()->display_time_millisecs();

  Vector3f tilt = 0.02f * g_base->input->tilt();
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  assert(g_base->input);
  bool show_icons = false;

  auto* device = g_base->ui->GetMainUIInputDevice();

  // If there's an explicit user-set icon we always show.
  if (icon_.exists()) {
    show_icons = true;
  }

  bool remote_icons = false;

  if (icon_type_ == IconType::kCancel && device != nullptr
      && device->IsRemoteControl()) {
    remote_icons = true;
  }

  // Simple transition.
  millisecs_t transition =
      (birth_time_millisecs_ + transition_delay_) - current_time;
  float transition_scale = 1.0f;
  bool apply_scale_transform = false;
  if (transition > 0) {
    if (transition_type_ == TransitionType::kScale) {
      // Fixed 150ms scale-up at the tail of the transition window
      // (quadratic ease-out; decelerates as it settles at 1.0).
      constexpr float kScaleDurationMs = 150.0f;
      float t = std::max(
          0.0f, 1.0f - static_cast<float>(transition) / kScaleDurationMs);
      transition_scale = 1.0f - (1.0f - t) * (1.0f - t);
      apply_scale_transform = true;
    } else {
      extra_offs_x -= static_cast<float>(transition) * 4.0f / scale();
    }
  }

  // Push a scaled-around-center transform if we're mid scale-in.
  if (apply_scale_transform) {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    c.PushTransform();
    float cx = width_ * 0.5f;
    float cy = height_ * 0.5f;
    c.Translate(cx, cy, 0.0f);
    c.Scale(transition_scale, transition_scale, 1.0f);
    c.Translate(-cx, -cy, 0.0f);
    c.Submit();
  }

  bool apply_rotate_transform = (rotate_ != 0.0f);
  if (apply_rotate_transform) {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    c.PushTransform();
    float cx = width_ * 0.5f;
    float cy = height_ * 0.5f;
    c.Translate(cx, cy, 0.0f);
    c.Rotate(rotate_, 0, 0, 1);
    c.Translate(-cx, -cy, 0.0f);
    c.Submit();
  }

  // A time-varying label (a live countdown) changes width as it ticks.
  if (text_->IsTimeVarying()) {
    text_width_dirty_ = true;
  }
  if (text_width_dirty_) {
    // Empty while OS-span measures warm in the background; stay dirty
    // and keep using our previous width until the value lands (the
    // label's own drawing defers in that state too).
    if (auto text_width = text_->TryGetTextWidth()) {
      text_width_ = *text_width;
      text_width_dirty_ = false;
    }
    // (Height needs no measuring, so it's simply current whenever we
    // get here.)
    text_height_ = text_->GetTextHeight();
  }

  float string_scale = text_scale_;

  bool string_too_small_to_draw = false;

  // The horizontal span our label (plus any icon) lives in. A centered
  // label keeps its traditional margins; an aligned one hugs its edge;
  // an accessory takes over the right end.
  bool text_centered = text_h_align_ == TextWidget::HAlign::kCenter;
  float text_span_l = text_centered ? kTextSideMargin : kAlignedTextInset;
  float text_span_r =
      width_
      - (accessory_ != Accessory::kNone
             ? kAccessoryRegion
             : (text_centered ? kTextSideMargin : kAlignedTextInset));
  float icon_width = show_icons ? 34.0f * icon_scale_ : 0.0f;

  // We should only need this in our transparent pass.
  float string_width;
  if (draw_transparent) {
    string_width = std::max(0.0001f, text_width_);

    // Shrink the label to fit an available extent. Whatever the
    // caller's numbers (a tiny button, an oversized icon), the
    // available space is held positive so the scale never goes to
    // zero or negative; a label squished past readability just
    // stops drawing.
    auto fit = [&string_scale, &string_too_small_to_draw](float extent,
                                                          float available) {
      available = std::max(1.0f, available);
      if (extent > 0.0f && (extent * string_scale) > available) {
        float squish_scale = available / (extent * string_scale);
        if (squish_scale < 0.2f) {
          string_too_small_to_draw = true;
        }
        string_scale *= squish_scale;
      }
    };

    // Account for our icon if we have it.
    fit(string_width, std::max(30.0f, text_span_r - text_span_l) - icon_width);

    // Then the same vertically.
    fit(text_height_, height_ - 2.0f * kTextVertMargin);
  } else {
    string_width = 0.0f;  // Shouldn't be used.
  }

  float mult = GetMult(current_time);

  // Standard-disabled buttons draw greyed: our body goes grey at roughly
  // its own brightness (so the default green lands near the (0.5, 0.5,
  // 0.5) hand-rolled disabled buttons have long used), icons fade, and
  // our label takes TextWidget's disabled look (set further down).
  bool disabled_look = StandardDisabled_();
  float color_r{color_red_};
  float color_g{color_green_};
  float color_b{color_blue_};
  float icon_alpha{icon_color_alpha_};
  if (disabled_look) {
    float grey =
        kDisabledBodyGreyScale
        * (0.3f * color_red_ + 0.59f * color_green_ + 0.11f * color_blue_);
    color_r = color_g = color_b = grey;
    icon_alpha *= kDisabledIconAlphaScale;
  }

  {
    float l = 0;
    float r = l + width_;
    float b = 0;
    float t = b + height_;

    // Use these to pick styles so style doesn't
    // change during mouse-over, etc.
    float l_orig = l;
    float r_orig = r;
    float b_orig = b;
    float t_orig = t;

    // For normal buttons we draw both transparent and opaque.
    // With custom ones we only draw what we're given.
    Object::Ref<base::MeshAsset> custom_mesh;
    bool do_draw_mesh;

    // Normal buttons draw in both transparent and opaque passes.
    if (!texture_.exists()) {
      do_draw_mesh = true;
    } else {
      // If we're supplying any custom meshes, draw whichever is provided.
      if (mesh_opaque_.exists() || mesh_transparent_.exists()) {
        if (draw_transparent && mesh_transparent_.exists()) {
          do_draw_mesh = true;
          custom_mesh = mesh_transparent_;
        } else if ((!draw_transparent) && mesh_opaque_.exists()) {
          do_draw_mesh = true;
          custom_mesh = mesh_opaque_;
        } else {
          do_draw_mesh = false;  // Skip this pass.
        }
      } else {
        // With no custom meshes we just draw a plain square in the
        // transparent pass.
        do_draw_mesh = draw_transparent;
      }
    }

    // A depiction stands in for our body (texture or standard art); our
    // label and icon still draw over it. Our transforms are already
    // pushed, and our own look (brightness, disabled) is its host state.
    bool draw_depiction = depiction_slot_ && depiction_slot_->active();
    if (draw_depiction) {
      DepictionSlot::DrawArgs args;
      args.owner = this;
      args.pass = pass;
      args.transparent = draw_transparent;
      // Standing in for a custom texture, we take the box that texture
      // draws to: without better-bg-fit that overhangs our bounds by 4%
      // a side (see below), and art authored for it (the toolbar
      // chests) should come out the same size either way.
      float dep_border_x{};
      float dep_border_y{};
      if (texture_.exists() && !better_bg_fit_) {
        dep_border_x = 0.04f * width_;
        dep_border_y = 0.04f * height_;
      }
      args.width = width_ + 2.0f * dep_border_x;
      args.height = height_ + 2.0f * dep_border_y;
      args.offset_x = extra_offs_x - dep_border_x;
      args.offset_y = extra_offs_y - dep_border_y;
      args.brightness = mult;
      args.opacity = opacity_;
      args.disabled = disabled_look;
      args.mask_texture = mask_texture_.get();
      depiction_slot_->Draw(args);
    }

    if (do_draw_mesh) {
      base::SimpleComponent c(pass);
      c.SetTransparent(draw_transparent);

      // We currently only support non-1.0 opacity values when using custom
      // textures with no custom opaque mesh.
      float opacity;
      if (opacity_ == 1.0f || (texture_.exists() && !mesh_opaque_.exists())) {
        opacity = opacity_;
      } else {
        BA_LOG_ONCE(LogName::kBaUI, LogLevel::kWarning,
                    "Button opacity < 1.0 only works with custom textures and "
                    "no opaque meshes.");
        opacity = 1.0f;
      }
      // Premultiply rgb by opacity for premultiplied textures so faded/
      // transparent buttons composite 'over' under premult blend instead of
      // staying full-brightness (premult blend adds rgb directly rather than
      // weighting it by alpha). Straight-alpha textures (and untextured
      // buttons, which force opacity to 1.0 above) keep raw rgb and fade via
      // alpha as before.
      float omul =
          (texture_.exists() && texture_->premultiplied()) ? opacity : 1.0f;
      c.SetColor(mult * color_r * omul, mult * color_g * omul,
                 mult * color_b * omul, opacity);
      if (flatness_ != 0.0f) {
        c.SetFlatness(flatness_);
      }

      float l_border{}, r_border{}, b_border{}, t_border{};
      float bg_scale_center_x{}, bg_scale_center_y{};
      float bg_scale_x{}, bg_scale_y{};

      bool do_draw{true};
      bool do_draw_better_fit{};

      base::MeshAsset* mesh;

      // Custom button texture.
      if (texture_.exists()) {
        if (!custom_mesh.exists()) {
          mesh = g_ui_v1->assets().image1x1.get();
        } else {
          mesh = custom_mesh.get();
        }
        if (texture_->loaded() && mesh->loaded()
            && (!mask_texture_.exists() || mask_texture_->loaded())
            && (!tint_texture_.exists() || tint_texture_->loaded())) {
          c.SetTexture(texture_);
          if (tint_texture_.exists()) {
            c.SetColorizeTexture(tint_texture_.get());
            c.SetColorizeColor(tint_color_red_, tint_color_green_,
                               tint_color_blue_);
            c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                                tint2_color_blue_);
            c.SetColorizeColor3(tint3_color_red_, tint3_color_green_,
                                tint3_color_blue_);
          }
          c.SetMaskTexture(mask_texture_.get());
        } else {
          do_draw = false;
        }
        l_border = r_border = 0.04f * width_;
        b_border = t_border = 0.04f * height_;

        if (better_bg_fit_) {
          // Just fit exactly to the widget bounds. If we need adjustments
          // we can expose args.
          bg_scale_center_x = 0.5f;
          bg_scale_center_y = 0.5f;
          bg_scale_x = 1.0f;
          bg_scale_y = 1.0f;
          do_draw_better_fit = true;
        }

      } else {
        // Standard button texture.
        base::MeshAsset* mesh_asset;
        base::TextureAsset* tex_asset;

        // Regular style means pick based on our aspect ratio.
        if (style_ == Style::kRegular) {
          if ((r_orig - l_orig) / (t_orig - b_orig) < 50.0f / 30.0f) {
            style_ = Style::kSmall;
          } else if ((r_orig - l_orig) / (t_orig - b_orig) < 200.0f / 35.0f) {
            style_ = Style::kMedium;
          } else if ((r_orig - l_orig) / (t_orig - b_orig) < 300.0f / 35.0f) {
            style_ = Style::kLarge;
          } else {
            style_ = Style::kLarger;
          }
        }

        switch (style_) {
          case Style::kBack: {
            tex_asset = g_ui_v1->assets().ui_atlas.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_back_transparent.get()
                             : g_ui_v1->assets().button_back_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.523f;
              bg_scale_center_y = 0.46f;
              bg_scale_x = 1.01f;
              bg_scale_y = 1.2f;
              do_draw_better_fit = true;
            } else {
              l_border = 10;
              r_border = 6;
              b_border = 6;
              t_border = -1;
            }
            break;
          }
          case Style::kBackSmall: {
            tex_asset = g_ui_v1->assets().ui_atlas.get();
            mesh_asset =
                draw_transparent
                    ? g_ui_v1->assets().button_back_small_transparent.get()
                    : g_ui_v1->assets().button_back_small_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.624f;
              bg_scale_center_y = 0.488f;
              bg_scale_x = 1.35f;
              bg_scale_y = 1.28f;
              do_draw_better_fit = true;
            } else {
              l_border = 10;
              r_border = 14;
              b_border = 9;
              t_border = 5;
            }
            break;
          }
          case Style::kTab: {
            tex_asset = g_ui_v1->assets().ui_atlas2.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_tab_transparent.get()
                             : g_ui_v1->assets().button_tab_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.5f;
              bg_scale_center_y = 0.5f;
              bg_scale_x = 1.04f;
              bg_scale_y = 1.1f;
              do_draw_better_fit = true;
            } else {
              l_border = 6;
              r_border = 10;
              b_border = 5;
              t_border = 2;
            }
            break;
          }
          case Style::kSquare: {
            tex_asset = g_ui_v1->assets().button_square.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_square_transparent.get()
                             : g_ui_v1->assets().button_square_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.521f;
              bg_scale_center_y = 0.495f;
              bg_scale_x = 1.155f;
              bg_scale_y = 1.169f;
              do_draw_better_fit = true;
            } else {
              l_border = 6;
              r_border = 9;
              b_border = 6;
              t_border = 6;
            }

            break;
          }
          case Style::kSquareWide: {
            tex_asset = g_ui_v1->assets().button_square_wide.get();
            mesh_asset = g_ui_v1->assets().image1x1.get();
            do_draw = draw_transparent;

            bg_scale_center_x = 0.505f;
            bg_scale_center_y = 0.49f;
            bg_scale_x = 1.06f;
            bg_scale_y = 1.17f;
            do_draw_better_fit = true;

            break;
          }
          case Style::kLarger: {
            tex_asset = g_ui_v1->assets().ui_atlas.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_larger_transparent.get()
                             : g_ui_v1->assets().button_larger_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.506f;
              bg_scale_center_y = 0.47f;
              bg_scale_x = 1.055f;
              bg_scale_y = 1.27f;
              do_draw_better_fit = true;
            } else {
              l_border = 7;
              r_border = 11;
              b_border = 10;
              t_border = 4;
            }
            break;
          }
          case Style::kLarge: {
            tex_asset = g_ui_v1->assets().ui_atlas.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_large_transparent.get()
                             : g_ui_v1->assets().button_large_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.503f;
              bg_scale_center_y = 0.452f;
              bg_scale_x = 1.06f;
              bg_scale_y = 1.22f;
              do_draw_better_fit = true;
            } else {
              l_border = 7;
              r_border = 10;
              b_border = 10;
              t_border = 5;
            }
            break;
          }
          case Style::kMedium: {
            tex_asset = g_ui_v1->assets().ui_atlas.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_medium_transparent.get()
                             : g_ui_v1->assets().button_medium_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.5f;
              bg_scale_center_y = 0.48f;
              bg_scale_x = 1.05f;
              bg_scale_y = 1.16f;
              do_draw_better_fit = true;
            } else {
              l_border = 6;
              r_border = 10;
              b_border = 5;
              t_border = 2;
            }

            break;
          }

          default: {
            assert(style_ == Style::kSmall);
            tex_asset = g_ui_v1->assets().ui_atlas.get();
            mesh_asset = draw_transparent
                             ? g_ui_v1->assets().button_small_transparent.get()
                             : g_ui_v1->assets().button_small_opaque.get();
            if (better_bg_fit_) {
              bg_scale_center_x = 0.5f;
              bg_scale_center_y = 0.49f;
              bg_scale_x = 1.158f;
              bg_scale_y = 1.16f;
              do_draw_better_fit = true;
            } else {
              l_border = 10;
              r_border = 14;
              b_border = 9;
              t_border = 5;
            }
            break;
          }
        }
        c.SetTexture(tex_asset);
        mesh = mesh_asset;
      }
      if (do_draw && !draw_depiction) {
        if (do_draw_better_fit) {
          // This math scales properly with widget size.
          auto xf = c.ScopedTransform();
          c.Translate(l + bg_scale_center_x * (r - l) + extra_offs_x,
                      b + bg_scale_center_y * (t - b) + extra_offs_y, 0);
          c.Scale((r - l) * bg_scale_x, (t - b) * bg_scale_y, 1.0f);
          c.DrawMeshAsset(mesh);
        } else {
          // This math is old and dumb and scales wonky, meaning bigger
          // widgets need different spacing. Ew. Leaving it for backwards
          // compat though.
          auto xf = c.ScopedTransform();
          c.Translate((l - l_border + r + r_border) * 0.5f + extra_offs_x,
                      (b - b_border + t + t_border) * 0.5f + extra_offs_y, 0);
          c.Scale(r - l + l_border + r_border, t - b + b_border + t_border,
                  1.0f);
          c.DrawMeshAsset(mesh);
        }
      }

      // Draw icon.
      if ((show_icons) && draw_transparent) {
        bool do_draw_icon = true;
        if (icon_type_ == IconType::kStart) {
          c.SetColor(1.4f * mult * color_r, 1.4f * mult * color_g,
                     1.4f * mult * color_b, 1.0f);
          c.SetTexture(g_ui_v1->assets().start_button.get());
        } else if (icon_type_ == IconType::kCancel) {
          if (remote_icons) {
            c.SetColor(1.0f * mult * (1.0f), 1.0f * mult * (1.0f),
                       1.0f * mult * (1.0f), 1.0f);
            c.SetTexture(g_ui_v1->assets().back_icon.get());
          } else {
            c.SetColor(1.5f * mult * color_r, 1.5f * mult * color_g,
                       1.5f * mult * color_b, 1.0f);
            c.SetTexture(g_ui_v1->assets().bomb_button.get());
          }
        } else if (icon_.exists()) {
          // Premultiply rgb by alpha for a premultiplied icon texture so a
          // faded icon (icon_color_alpha_ < 1) composites 'over' correctly
          // (see docs/design/premultiplied-alpha.md).
          float imul = icon_->premultiplied() ? icon_alpha : 1.0f;
          c.SetColor(icon_color_red_ * imul
                         * (icon_tint_ * (1.7f * mult * color_r)
                            + (1.0f - icon_tint_) * mult),
                     icon_color_green_ * imul
                         * (icon_tint_ * (1.7f * mult * color_g)
                            + (1.0f - icon_tint_) * mult),
                     icon_color_blue_ * imul
                         * (icon_tint_ * (1.7f * mult * color_b)
                            + (1.0f - icon_tint_) * mult),
                     icon_alpha);
          if (!icon_->loaded()) {
            do_draw_icon = false;
          } else {
            c.SetTexture(icon_);
          }
        } else {
          c.SetColor(1, 1, 1);
          c.SetTexture(g_ui_v1->assets().circle.get());
        }
        if (do_draw_icon) {
          // The icon sits just before the label's left edge.
          float drawn_width = string_width * string_scale;
          float text_left;
          switch (text_h_align_) {
            case TextWidget::HAlign::kLeft:
              text_left = l + text_span_l + icon_width;
              break;
            case TextWidget::HAlign::kRight:
              text_left = l + text_span_r - drawn_width;
              break;
            default:
              text_left = l + (text_span_l + text_span_r) * 0.5f
                          + icon_width * 0.5f - drawn_width * 0.5f;
              break;
          }
          auto xf = c.ScopedTransform();
          c.Translate(text_left - icon_width * 0.5f - 5.0f + extra_offs_x,
                      (b + t) * 0.5f + extra_offs_y, 0.001f);
          c.Scale(34.0f * icon_scale_, 34.f * icon_scale_, 1.0f);
          c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
        }
      }
      c.Submit();
    }
  }

  // Draw our text at z depth 0.5-1.
  if (!string_too_small_to_draw) {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    {
      auto xf = c.ScopedTransform();

      c.Translate(1.0f * extra_offs_x, 1.0f * extra_offs_y, 0.5f);
      c.Scale(1, 1, 0.5f);

      // Special case - fudge text centering for small back buttons.
      if (style_ == Style::kBackSmall && text_centered) {
        if (better_bg_fit_) {
          c.Translate(width_ * 0.55, height_ * 0.5f);
        } else {
          c.Translate(width_ * 0.4f, height_ * 0.48f);
        }
        // Shift over for our icon if we have it.
        c.Translate(icon_width * 0.5f, 0, 0);
      } else {
        // Anchor per our label's alignment; an icon precedes the label.
        float anchor_x;
        switch (text_h_align_) {
          case TextWidget::HAlign::kLeft:
            anchor_x = text_span_l + icon_width;
            break;
          case TextWidget::HAlign::kRight:
            anchor_x = text_span_r;
            break;
          default:
            anchor_x = (text_span_l + text_span_r + icon_width) * 0.5f;
            break;
        }
        c.Translate(anchor_x, height_ * 0.5f);
      }
      if (string_scale != 1.0f) {
        c.Scale(string_scale, string_scale);
      }
      c.Submit();

      text_->set_color(mult * text_color_r_, mult * text_color_g_,
                       mult * text_color_b_, text_color_a_);
      text_->set_flatness(text_flatness_);
      text_->SetEnabled(!disabled_look);
      text_->Draw(pass, draw_transparent);
    }
    c.Submit();
  }

  // Draw our accessory glyph centered in its region at our right end.
  if (accessory_text_.exists()) {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    {
      auto xf = c.ScopedTransform();
      c.Translate(
          width_ - kAccessoryEdgeInset - kAccessoryWidth * 0.5f + extra_offs_x,
          height_ * 0.5f + extra_offs_y, 0.5f);
      c.Scale(kAccessoryScale, kAccessoryScale, 0.5f);
      c.Submit();
      accessory_text_->set_color(mult * text_color_r_, mult * text_color_g_,
                                 mult * text_color_b_, text_color_a_);
      accessory_text_->set_flatness(text_flatness_);
      accessory_text_->SetEnabled(!disabled_look);
      accessory_text_->Draw(pass, draw_transparent);
    }
    c.Submit();
  }

  if (apply_rotate_transform) {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    c.PopTransform();
    c.Submit();
  }

  // Pop scale-in transform we pushed at the top.
  if (apply_scale_transform) {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    c.PopTransform();
    c.Submit();
  }
}

auto ButtonWidget::RotatePointToLocal(float x, float y) const
    -> std::pair<float, float> {
  if (rotate_ == 0.0f) {
    return {x, y};
  }
  constexpr float kDegToRad = 3.14159265358979323846f / 180.0f;
  float theta = rotate_ * kDegToRad;
  float cx = width_ * 0.5f;
  float cy = height_ * 0.5f;
  float dx = x - cx;
  float dy = y - cy;
  float ct = cosf(theta);
  float st = sinf(theta);
  float nx = cx + dx * ct + dy * st;
  float ny = cy - dx * st + dy * ct;
  return {nx, ny};
}

auto ButtonWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  // How far outside button touches register.
  float left_overlap, top_overlap, right_overlap, bottom_overlap;
  // if (g_core->platform->IsRunningOnDesktop()) {

  // UPDATE - removing touch-specific boundary adjustments. If it is
  // necessary to reenable these, should do it on a per-event basis so need
  // to differentiate between touches and clicks. It is probably sufficient
  // to simply expose manual boundary tweaks that apply everywhere though.
  left_overlap = 3.0f;
  top_overlap = 1.0f;
  right_overlap = 0.0f;
  bottom_overlap = 0.0f;
  // } else {
  //   left_overlap = 3.0f + 9.0f * extra_touch_border_scale_;
  //   top_overlap = 1.0f + 5.0f * extra_touch_border_scale_;
  //   right_overlap = 7.0f * extra_touch_border_scale_;
  //   bottom_overlap = 7.0f * extra_touch_border_scale_;
  // }

  // Extra overlap that always applies.
  right_overlap += target_extra_right_;
  left_overlap += target_extra_left_;

  // Our whole box (plus those overlaps), or with depiction_hit_area
  // set, just what our depiction covers (grown to a minimum size and
  // kept within that box).
  float hit_l{-left_overlap};
  float hit_r{width_ + right_overlap};
  float hit_b{-bottom_overlap};
  float hit_t{height_ + top_overlap};
  if (depiction_hit_area_ && depiction_slot_) {
    if (auto content = depiction_slot_->GetContentBox(width_, height_)) {
      float cx = content->x + content->width * 0.5f;
      float cy = content->y + content->height * 0.5f;
      float half_w = 0.5f * std::max(content->width, kMinDepictionHitSize);
      float half_h = 0.5f * std::max(content->height, kMinDepictionHitSize);
      hit_l = std::max(hit_l, cx - half_w);
      hit_r = std::min(hit_r, cx + half_w);
      hit_b = std::max(hit_b, cy - half_h);
      hit_t = std::min(hit_t, cy + half_h);
    }
  }
  auto in_target = [hit_l, hit_r, hit_b, hit_t](float x, float y) {
    return x >= hit_l && x < hit_r && y >= hit_b && y < hit_t;
  };

  switch (m.type) {
    case base::WidgetMessage::Type::kMouseMove: {
      auto [x, y] = RotatePointToLocal(m.fval1, m.fval2);
      bool claimed = (m.fval3 > 0.0f);
      [[maybe_unused]] auto old_hover{hover_};

      if (claimed || !enabled_) {
        hover_ = false;
      } else {
        if (pressed_) {
          claimed = true;
        }
        hover_ = in_target(x, y);
      }
      if (hover_) {
        claimed = true;
      }

      return claimed;
    }
    case base::WidgetMessage::Type::kMouseDown: {
      auto [x, y] = RotatePointToLocal(m.fval1, m.fval2);

      // Standard-disabled: a press still selects us (we stay selectable,
      // so a tap should do what navigating to us does) but never lights
      // or activates us. We claim it, and so its release, which answers
      // with an error sound. (Toolbar-behavior disabled buttons fall
      // through below and ignore the press entirely.)
      if (StandardDisabled_()) {
        if (in_target(x, y)) {
          disabled_pressed_ = true;
          if (selectable_) {
            GlobalSelect();
          }
          return true;
        }
        return false;
      }
      if (enabled_ && in_target(x, y)) {
        hover_ = true;
        pressed_ = true;

        if (repeat_) {
          repeat_timer_ = base::AppTimer::New(
              0.3, true, [this] { OnRepeatTimerExpired(); });

          // If we're a repeat button we trigger immediately.
          // (waiting till mouse up sort of defeats the purpose here)
          // Not via Activate(): our actions-complete waits for the
          // release, after any repeats.
          DoActivate();
        }
        if (selectable_) {
          GlobalSelect();
        }
        return true;
      } else {
        return false;
      }
    }
    case base::WidgetMessage::Type::kMouseUp:
    case base::WidgetMessage::Type::kMouseCancel: {
      auto [x, y] = RotatePointToLocal(m.fval1, m.fval2);
      bool claimed = (m.fval3 > 0.0f);

      if (claim_release_silently_) {
        claim_release_silently_ = false;
        return true;
      }
      if (disabled_pressed_) {
        disabled_pressed_ = false;
        if (m.type == base::WidgetMessage::Type::kMouseUp && !claimed
            && in_target(x, y)) {
          g_base->audio->SafePlayBuiltinSound(
              base::BuiltinSoundID::kAudioError);
        }
        return true;
      }

      if (pressed_) {
        pressed_ = false;

        // Stop any repeats.
        repeat_timer_.Clear();

        // For non-repeat buttons, non-claimed mouse-ups within the
        // button region trigger the action (Activate() reports
        // actions-complete itself).
        if (!repeat_) {
          if (enabled_ && in_target(x, y) && !claimed) {
            if (m.type == base::WidgetMessage::Type::kMouseUp) {
              Activate();
            }
          }
        } else {
          // A repeat button activated on the press and possibly since;
          // the release is when its actions are complete.
          RunActionsComplete_();
        }
        return true;  // Pressed buttons always claim mouse-ups.
      }
      break;
    }
    default:
      break;
  }
  return false;
}

void ButtonWidget::SetEnabled(bool val) {
  // (The toolbar calls this every update, so keep the no-change case
  // cheap.)
  if (val == enabled_) {
    return;
  }
  enabled_ = val;

  // A standard-disabled button being disabled mid-press ends the press
  // here: otherwise a held repeat-button would sound an error on every
  // remaining repeat tick. Its actions are complete (a row may commit on
  // that), and the release still comes to us, silently.
  if (!enabled_ && !disabled_toolbar_button_behavior_ && pressed_) {
    pressed_ = false;
    hover_ = false;
    repeat_timer_.Clear();
    claim_release_silently_ = true;
    base::UI::OperationContext ui_op_context;
    RunActionsComplete_();
    ui_op_context.Finish();
  }
}

void ButtonWidget::Activate() {
  // A direct activation (key/controller press, Python call) has no
  // press sequence to wait out; its actions are complete at once.
  DoActivate();
  RunActionsComplete_();
}

void ButtonWidget::SetOnActionsCompleteCall(PyObject* call_obj) {
  on_actions_complete_call_ = Object::New<base::PythonContextCall>(call_obj);
}

void ButtonWidget::RunActionsComplete_() {
  if (!activated_since_complete_) {
    return;
  }
  activated_since_complete_ = false;
  if (auto* call = on_actions_complete_call_.get()) {
    // Same dispatch as on_activate_call, so the two run in order.
    if (g_base->ui->InUIOperation()) {
      call->ScheduleInUIOperation();
    } else {
      call->Run();
    }
  }
}

void ButtonWidget::DoActivate(bool is_repeat) {
  if (!enabled_) {
    // Standard-disabled buttons get activated like any other selectable
    // widget (a key/controller press on one, say); say no audibly. Only
    // toolbar-behavior ones should never be reached here.
    if (!disabled_toolbar_button_behavior_) {
      g_base->audio->SafePlayBuiltinSound(base::BuiltinSoundID::kAudioError);
    } else {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kWarning,
          "ButtonWidget::DoActivate() called on disabled button");
    }
    return;
  }
  activated_since_complete_ = true;

  // We don't want holding down a repeat-button to keep flashing it.
  if (!is_repeat) {
    last_activate_time_millisecs_ =
        static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  }
  if (sound_enabled_) {
    g_ui_v1->PlaySwish();
  }
  if (auto* call = on_activate_call_.get()) {
    // If we're being activated as part of a ui-operation (a click or other
    // such event) then run at the end of that operation to avoid mucking
    // with volatile UI.
    if (g_base->ui->InUIOperation()) {
      call->ScheduleInUIOperation();
    } else {
      // Ok, we're *not* in a ui-operation. This generally means we're
      // being activated explicitly via a Python call or whatnot. Just
      // run immediately in this case.
      call->Run();
    }
    return;
  }
}

void ButtonWidget::OnLanguageChange() {
  text_->OnLanguageChange();
  text_width_dirty_ = true;
}

}  // namespace ballistica::ui_v1
