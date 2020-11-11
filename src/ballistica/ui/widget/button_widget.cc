// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui/widget/button_widget.h"

#include <algorithm>
#include <string>

#include "ballistica/audio/audio.h"
#include "ballistica/generic/real_timer.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/component/empty_component.h"
#include "ballistica/graphics/component/simple_component.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/input/input.h"
#include "ballistica/media/component/model.h"
#include "ballistica/python/python_context_call.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

ButtonWidget::ButtonWidget() {
  text_ = Object::New<TextWidget>();
  SetText("Button");
  text_->set_valign(TextWidget::VAlign::kCenter);
  text_->set_halign(TextWidget::HAlign::kCenter);
  text_->SetWidth(0.0f);
  text_->SetHeight(0.0f);
  birth_time_ = g_game->master_time();
}

ButtonWidget::~ButtonWidget() = default;

void ButtonWidget::SetTextResScale(float val) { text_->set_res_scale(val); }

void ButtonWidget::set_on_activate_call(PyObject* call_obj) {
  on_activate_call_ = Object::New<PythonContextCall>(call_obj);
}

void ButtonWidget::SetText(const std::string& text_in) {
  std::string text = Utils::GetValidUTF8(text_in.c_str(), "bwst");
  text_->SetText(text);

  // Also cache our current text width; don't want to calc this with each draw
  // (especially now that we may have to ask the OS to do it).
  text_width_dirty_ = true;
}

void ButtonWidget::SetTexture(Texture* val) {
  if (val && !val->IsFromUIContext()) {
    throw Exception("texture is not from the UI context: " + ObjToString(val));
  }
  texture_ = val;
}

void ButtonWidget::SetMaskTexture(Texture* val) {
  if (val && !val->IsFromUIContext()) {
    throw Exception("texture is not from the UI context: " + ObjToString(val));
  }
  mask_texture_ = val;
}

void ButtonWidget::SetTintTexture(Texture* val) {
  if (val && !val->IsFromUIContext()) {
    throw Exception("texture is not from the UI context: " + ObjToString(val));
  }
  tint_texture_ = val;
}

void ButtonWidget::SetIcon(Texture* val) {
  if (val && !val->IsFromUIContext()) {
    throw Exception("icon texture is not from the UI context: "
                    + val->GetObjectDescription());
  }
  icon_ = val;
}

void ButtonWidget::HandleRealTimerExpired(RealTimer<ButtonWidget>* t) {
  // Repeat our action unless we somehow lost focus but didn't get a mouse-up.
  if (IsHierarchySelected() && pressed_) {
    DoActivate(true);

    // Speed up repeats after the first.
    t->SetLength(150);
  } else {
    repeat_timer_.Clear();
  }
}

void ButtonWidget::SetModelOpaque(Model* val) {
  if (val && !val->IsFromUIContext()) {
    throw Exception("model_opaque is not from the UI context");
  }
  model_opaque_ = val;
}

void ButtonWidget::SetModelTransparent(Model* val) {
  if (val && !val->IsFromUIContext()) {
    throw Exception("model_transparent is not from the UI context");
  }
  model_transparent_ = val;
}

auto ButtonWidget::GetWidth() -> float { return width_; }
auto ButtonWidget::GetHeight() -> float { return height_; }

auto ButtonWidget::GetMult(millisecs_t current_time) const -> float {
  float mult = 1.0f;
  if ((pressed_ && mouse_over_) || (current_time - last_activate_time_ < 200)) {
    if (pressed_ && mouse_over_) {
      mult = 3.0f;
    } else {
      float x = static_cast<float>(current_time - last_activate_time_) / 200.0f;
      mult = 1.0f + 3.0f * (1.0f - x * x);
    }
  } else if ((IsHierarchySelected() && g_ui->ShouldHighlightWidgets())) {
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
    if (!texture_.exists()) {
    } else {
      // In desktop mode we want image buttons to light up when we
      // mouse over them.
      if (!g_platform->IsRunningOnDesktop()) {
        if (mouse_over_) {
          mult = 1.4f;
        }
      }
    }
  }
  return mult;
}

auto ButtonWidget::GetDrawBrightness(millisecs_t time) const -> float {
  return GetMult(time);
}

void ButtonWidget::Draw(RenderPass* pass, bool draw_transparent) {
  millisecs_t current_time = pass->frame_def()->base_time();

  Vector3f tilt = 0.02f * g_graphics->tilt();
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  assert(g_input);
  bool show_icons = false;

  InputDevice* device = g_ui->GetUIInputDevice();

  // If there's an explicit user-set icon we always show.
  if (icon_.exists()) {
    show_icons = true;
  }

  bool ouya_icons = false;
  bool remote_icons = false;

  // Phasing out ouya stuff.
  if (explicit_bool(false)) {
    ouya_icons = true;
  }
  if (icon_type_ == IconType::kCancel && device != nullptr
      && device->IsRemoteControl()) {
    remote_icons = true;
  }

  // Simple transition.
  float transition = (birth_time_ + transition_delay_) - current_time;
  if (transition > 0) {
    extra_offs_x -= transition * 4.0f;
  }

  if (text_width_dirty_) {
    text_width_ = text_->GetTextWidth();
    text_width_dirty_ = false;
  }

  float string_scale = text_scale_;

  bool string_too_small_to_draw = false;

  // We should only need this in our transparent pass.
  float string_width;
  if (draw_transparent) {
    string_width = std::max(0.0001f, text_width_);

    // Account for our icon if we have it.
    float s_width_available = std::max(30.0f, width_ - 30);
    if (show_icons) s_width_available -= (34.0f * icon_scale_);

    if ((string_width * string_scale) > s_width_available) {
      float squish_scale = s_width_available / (string_width * string_scale);
      if (squish_scale < 0.2f) string_too_small_to_draw = true;
      string_scale *= squish_scale;
    }
  } else {
    string_width = 0.0f;  // Shouldn't be used.
  }

  float mult = GetMult(current_time);

  {
    float l = 0;
    float r = l + width_;
    float b = 0;
    float t = b + height_;

    // Use these to pick styles so style doesnt
    // change during mouse-over, etc.
    float l_orig = l;
    float r_orig = r;
    float b_orig = b;
    float t_orig = t;

    // For normal buttons we draw both transparent and opaque.
    // With custom ones we only draw what we're given.
    Object::Ref<Model> custom_model;
    bool do_draw_model;

    // Normal buttons draw in both transparent and opaque passes.
    if (!texture_.exists()) {
      do_draw_model = true;
    } else {
      // If we're supplying any custom models, draw whichever is provided.
      if (model_opaque_.exists() || model_transparent_.exists()) {
        if (draw_transparent && model_transparent_.exists()) {
          do_draw_model = true;
          custom_model = model_transparent_;
        } else if ((!draw_transparent) && model_opaque_.exists()) {
          do_draw_model = true;
          custom_model = model_opaque_;
        } else {
          do_draw_model = false;  // Skip this pass.
        }
      } else {
        // With no custom models we just draw a plain square in the
        // transparent pass.
        do_draw_model = draw_transparent;
      }
    }

    if (do_draw_model) {
      SimpleComponent c(pass);
      c.SetTransparent(draw_transparent);

      // We currently only support non-1.0 opacity values when using
      // custom textures and no custom opaque model.
      assert(opacity_ == 1.0f
             || (texture_.exists() && !model_opaque_.exists()));

      c.SetColor(mult * color_red_, mult * color_green_, mult * color_blue_,
                 opacity_);

      float l_border, r_border, b_border, t_border;

      bool doDraw = true;

      ModelData* model;

      // Custom button texture.
      if (texture_.exists()) {
        if (!custom_model.exists()) {
          model = g_media->GetModel(SystemModelID::kImage1x1);
        } else {
          model = custom_model->model_data();
        }
        if (texture_->texture_data()->loaded() && model->loaded()
            && (!mask_texture_.exists()
                || mask_texture_->texture_data()->loaded())
            && (!tint_texture_.exists()
                || tint_texture_->texture_data()->loaded())) {
          c.SetTexture(texture_);
          if (tint_texture_.exists()) {
            c.SetColorizeTexture(tint_texture_);
            c.SetColorizeColor(tint_color_red_, tint_color_green_,
                               tint_color_blue_);
            c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                                tint2_color_blue_);
          }
          c.SetMaskTexture(mask_texture_);
        } else {
          doDraw = false;
        }
        l_border = r_border = 0.04f * width_;
        b_border = t_border = 0.04f * height_;
      } else {
        // Standard button texture.
        SystemModelID model_id;
        SystemTextureID tex_id;

        switch (style_) {
          case Style::kBack: {
            tex_id = SystemTextureID::kUIAtlas;
            model_id = draw_transparent ? SystemModelID::kButtonBackTransparent
                                        : SystemModelID::kButtonBackOpaque;
            l_border = 10;
            r_border = 6;
            b_border = 6;
            t_border = -1;
            break;
          }
          case Style::kBackSmall: {
            tex_id = SystemTextureID::kUIAtlas;
            model_id = draw_transparent
                           ? SystemModelID::kButtonBackSmallTransparent
                           : SystemModelID::kButtonBackSmallOpaque;
            l_border = 10;
            r_border = 14;
            b_border = 9;
            t_border = 5;
            break;
          }
          case Style::kTab: {
            tex_id = SystemTextureID::kUIAtlas2;
            model_id = draw_transparent ? SystemModelID::kButtonTabTransparent
                                        : SystemModelID::kButtonTabOpaque;
            l_border = 6;
            r_border = 10;
            b_border = 5;
            t_border = 2;
            break;
          }
          case Style::kSquare: {
            tex_id = SystemTextureID::kButtonSquare;
            model_id = draw_transparent
                           ? SystemModelID::kButtonSquareTransparent
                           : SystemModelID::kButtonSquareOpaque;
            l_border = 6;
            r_border = 9;
            b_border = 6;
            t_border = 6;
            break;
          }
          default: {
            if ((r_orig - l_orig) / (t_orig - b_orig) < 50.0f / 30.0f) {
              tex_id = SystemTextureID::kUIAtlas;
              model_id = draw_transparent
                             ? SystemModelID::kButtonSmallTransparent
                             : SystemModelID::kButtonSmallOpaque;
              l_border = 10;
              r_border = 14;
              b_border = 9;
              t_border = 5;
            } else if ((r_orig - l_orig) / (t_orig - b_orig) < 200.0f / 35.0f) {
              tex_id = SystemTextureID::kUIAtlas;
              model_id = draw_transparent
                             ? SystemModelID::kButtonMediumTransparent
                             : SystemModelID::kButtonMediumOpaque;
              l_border = 6;
              r_border = 10;
              b_border = 5;
              t_border = 2;
            } else if ((r_orig - l_orig) / (t_orig - b_orig) < 300.0f / 35.0f) {
              tex_id = SystemTextureID::kUIAtlas;
              model_id = draw_transparent
                             ? SystemModelID::kButtonLargeTransparent
                             : SystemModelID::kButtonLargeOpaque;
              l_border = 7;
              r_border = 10;
              b_border = 10;
              t_border = 5;
            } else {
              tex_id = SystemTextureID::kUIAtlas;
              model_id = draw_transparent
                             ? SystemModelID::kButtonLargerTransparent
                             : SystemModelID::kButtonLargerOpaque;
              l_border = 7;
              r_border = 11;
              b_border = 10;
              t_border = 4;
            }
            break;
          }
        }
        c.SetTexture(g_media->GetTexture(tex_id));
        model = g_media->GetModel(model_id);
      }
      if (doDraw) {
        c.PushTransform();
        c.Translate((l - l_border + r + r_border) * 0.5f + extra_offs_x,
                    (b - b_border + t + t_border) * 0.5f + extra_offs_y, 0);
        c.Scale(r - l + l_border + r_border, t - b + b_border + t_border, 1.0f);
        c.DrawModel(model);
        c.PopTransform();
      }

      // Draw icon.
      if ((show_icons) && draw_transparent) {
        bool doDrawIcon = true;
        if (icon_type_ == IconType::kStart) {
          c.SetColor(1.4f * mult * (color_red_), 1.4f * mult * (color_green_),
                     1.4f * mult * (color_blue_), 1.0f);
          c.SetTexture(g_media->GetTexture(SystemTextureID::kStartButton));
        } else if (icon_type_ == IconType::kCancel) {
          if (remote_icons) {
            c.SetColor(1.0f * mult * (1.0f), 1.0f * mult * (1.0f),
                       1.0f * mult * (1.0f), 1.0f);
            c.SetTexture(g_media->GetTexture(SystemTextureID::kBackIcon));
          } else if (ouya_icons) {
            c.SetColor(1.0f * mult * (1.0f), 1.0f * mult * (1.0f),
                       1.0f * mult * (1.0f), 1.0f);
            c.SetTexture(g_media->GetTexture(SystemTextureID::kOuyaAButton));
          } else {
            c.SetColor(1.5f * mult * (color_red_), 1.5f * mult * (color_green_),
                       1.5f * mult * (color_blue_), 1.0f);
            c.SetTexture(g_media->GetTexture(SystemTextureID::kBombButton));
          }
        } else if (icon_.exists()) {
          c.SetColor(icon_color_red_
                         * (icon_tint_ * (1.7f * mult * (color_red_))
                            + (1.0f - icon_tint_) * mult),
                     icon_color_green_
                         * (icon_tint_ * (1.7f * mult * (color_green_))
                            + (1.0f - icon_tint_) * mult),
                     icon_color_blue_
                         * (icon_tint_ * (1.7f * mult * (color_blue_))
                            + (1.0f - icon_tint_) * mult),
                     icon_color_alpha_);
          if (!icon_->texture_data()->loaded()) {
            doDrawIcon = false;
          } else {
            c.SetTexture(icon_);
          }
        } else {
          c.SetColor(1, 1, 1);
          c.SetTexture(g_media->GetTexture(SystemTextureID::kCircle));
        }
        if (doDrawIcon) {
          c.PushTransform();
          c.Translate((l + r) * 0.5f + extra_offs_x
                          - (string_width * string_scale) * 0.5f - 5.0f,
                      (b + t) * 0.5f + extra_offs_y, 0.001f);
          c.Scale(34.0f * icon_scale_, 34.f * icon_scale_, 1.0f);
          c.DrawModel(g_media->GetModel(SystemModelID::kImage1x1));
          c.PopTransform();
        }
      }
      c.Submit();
    }
  }

  // Draw our text at z depth 0.5-1.
  if (!string_too_small_to_draw) {
    EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    c.PushTransform();
    c.Translate(1.0f * extra_offs_x, 1.0f * extra_offs_y, 0.5f);
    c.Scale(1, 1, 0.5f);
    c.Translate(width_ * 0.5f, height_ * 0.5f);

    // Shift over for our icon if we have it.
    if (show_icons) {
      c.Translate(17.0f * icon_scale_, 0, 0);
    }
    if (string_scale != 1.0f) {
      c.Scale(string_scale, string_scale);
    }
    c.Submit();

    text_->set_color(mult * text_color_r_, mult * text_color_g_,
                     mult * text_color_b_, text_color_a_);
    text_->set_flatness(text_flatness_);
    text_->Draw(pass, draw_transparent);
    c.PopTransform();
    c.Submit();
  }
}

auto ButtonWidget::HandleMessage(const WidgetMessage& m) -> bool {
  // How far outside button touches register.
  float left_overlap, top_overlap, right_overlap, bottom_overlap;
  if (g_platform->IsRunningOnDesktop()) {
    left_overlap = 3.0f;
    top_overlap = 1.0f;
    right_overlap = 0.0f;
    bottom_overlap = 0.0f;
  } else {
    left_overlap = 3.0f + 9.0f * extra_touch_border_scale_;
    top_overlap = 1.0f + 5.0f * extra_touch_border_scale_;
    right_overlap = 7.0f * extra_touch_border_scale_;
    bottom_overlap = 7.0f * extra_touch_border_scale_;
  }

  switch (m.type) {
    case WidgetMessage::Type::kMouseMove: {
      float x = m.fval1;
      float y = m.fval2;
      bool claimed = (m.fval3 > 0.0f);
      if (claimed || !enabled_) {
        mouse_over_ = false;
      } else {
        mouse_over_ =
            ((x >= (-left_overlap)) && (x < (width_ + right_overlap))
             && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap)));
      }

      return mouse_over_;
    }
    case WidgetMessage::Type::kMouseDown: {
      float x = m.fval1;
      float y = m.fval2;
      if (enabled_ && (x >= (-left_overlap)) && (x < (width_ + right_overlap))
          && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))) {
        mouse_over_ = true;
        pressed_ = true;

        if (repeat_) {
          repeat_timer_ = Object::New<RealTimer<ButtonWidget>>(300, true, this);
          // If we're a repeat button we trigger immediately.
          // (waiting till mouse up sort of defeats the purpose here)
          Activate();
        }
        if (selectable_) {
          GlobalSelect();
        }
        return true;
      } else {
        return false;
      }
    }
    case WidgetMessage::Type::kMouseUp: {
      float x = m.fval1;
      float y = m.fval2;
      bool claimed = (m.fval3 > 0.0f);
      if (pressed_) {
        pressed_ = false;

        // Stop any repeats.
        repeat_timer_.Clear();

        // For non-repeat buttons, non-claimed mouse-ups within the
        // button region trigger the action.
        if (!repeat_) {
          if (enabled_ && (x >= (0 - left_overlap))
              && (x < (0 + width_ + right_overlap))
              && (y >= (0 - bottom_overlap))
              && (y < (0 + height_ + top_overlap)) && !claimed) {
            Activate();
          }
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

void ButtonWidget::Activate() { DoActivate(); }

void ButtonWidget::DoActivate(bool isRepeat) {
  if (!enabled_) {
    Log("WARNING: ButtonWidget::DoActivate() called on disabled button");
    return;
  }

  // We dont want holding down a repeat-button to keep flashing it.
  if (!isRepeat) {
    last_activate_time_ = g_game->master_time();
  }
  if (sound_enabled_) {
    int r = rand() % 3;  // NOLINT
    if (r == 0) {
      g_audio->PlaySound(g_media->GetSound(SystemSoundID::kSwish));
    } else if (r == 1) {
      g_audio->PlaySound(g_media->GetSound(SystemSoundID::kSwish2));
    } else {
      g_audio->PlaySound(g_media->GetSound(SystemSoundID::kSwish3));
    }
  }
  if (on_activate_call_.exists()) {
    // Call this in the next cycle (don't wanna risk mucking with UI from
    // within a UI loop.
    g_game->PushPythonWeakCall(
        Object::WeakRef<PythonContextCall>(on_activate_call_));
    return;
  }
}

void ButtonWidget::OnLanguageChange() {
  text_->OnLanguageChange();
  text_width_dirty_ = true;
}

}  // namespace ballistica
