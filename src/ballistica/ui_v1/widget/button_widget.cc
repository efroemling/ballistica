// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/button_widget.h"

#include <algorithm>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::ui_v1 {

ButtonWidget::ButtonWidget()
    : birth_time_millisecs_{
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)} {
  text_ = Object::New<TextWidget>();
  set_text("Button");
  text_->SetVAlign(TextWidget::VAlign::kCenter);
  text_->SetHAlign(TextWidget::HAlign::kCenter);
  text_->SetWidth(0.0f);
  text_->SetHeight(0.0f);
}

ButtonWidget::~ButtonWidget() = default;

void ButtonWidget::SetTextResScale(float val) { text_->set_res_scale(val); }

void ButtonWidget::SetOnActivateCall(PyObject* call_obj) {
  on_activate_call_ = Object::New<base::PythonContextCall>(call_obj);
}

void ButtonWidget::set_text(const std::string& text_in) {
  std::string text = Utils::GetValidUTF8(text_in.c_str(), "bwst");
  text_->SetText(text);

  // Also cache our current text width; don't want to calc this with each draw
  // (especially now that we may have to ask the OS to do it).
  text_width_dirty_ = true;
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
  if ((pressed_ && mouse_over_)
      || (current_time - last_activate_time_millisecs_ < 200)) {
    if (pressed_ && mouse_over_) {
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
    // Slightly highlighting all buttons for mouse-over. Once we can
    // differentiate between touch events and pointer events we should limit
    // this to pointer events.
    if (mouse_over_) {
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

  Vector3f tilt = 0.02f * g_base->graphics->tilt();
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
  if (transition > 0) {
    extra_offs_x -= static_cast<float>(transition) * 4.0f / scale();
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
    if (show_icons) {
      s_width_available -= (34.0f * icon_scale_);
    }

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

    if (do_draw_mesh) {
      base::SimpleComponent c(pass);
      c.SetTransparent(draw_transparent);

      // We currently only support non-1.0 opacity values when using
      // custom textures and no custom opaque mesh.
      assert(opacity_ == 1.0f || (texture_.exists() && !mesh_opaque_.exists()));

      c.SetColor(mult * color_red_, mult * color_green_, mult * color_blue_,
                 opacity_);

      float l_border, r_border, b_border, t_border;

      bool do_draw = true;

      base::MeshAsset* mesh;

      // Custom button texture.
      if (texture_.exists()) {
        if (!custom_mesh.exists()) {
          mesh = g_base->assets->SysMesh(base::SysMeshID::kImage1x1);
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
          }
          c.SetMaskTexture(mask_texture_.get());
        } else {
          do_draw = false;
        }
        l_border = r_border = 0.04f * width_;
        b_border = t_border = 0.04f * height_;
      } else {
        // Standard button texture.
        base::SysMeshID mesh_id;
        base::SysTextureID tex_id;

        switch (style_) {
          case Style::kBack: {
            tex_id = base::SysTextureID::kUIAtlas;
            mesh_id = draw_transparent ? base::SysMeshID::kButtonBackTransparent
                                       : base::SysMeshID::kButtonBackOpaque;
            l_border = 10;
            r_border = 6;
            b_border = 6;
            t_border = -1;
            break;
          }
          case Style::kBackSmall: {
            tex_id = base::SysTextureID::kUIAtlas;
            mesh_id = draw_transparent
                          ? base::SysMeshID::kButtonBackSmallTransparent
                          : base::SysMeshID::kButtonBackSmallOpaque;
            l_border = 10;
            r_border = 14;
            b_border = 9;
            t_border = 5;
            break;
          }
          case Style::kTab: {
            tex_id = base::SysTextureID::kUIAtlas2;
            mesh_id = draw_transparent ? base::SysMeshID::kButtonTabTransparent
                                       : base::SysMeshID::kButtonTabOpaque;
            l_border = 6;
            r_border = 10;
            b_border = 5;
            t_border = 2;
            break;
          }
          case Style::kSquare: {
            tex_id = base::SysTextureID::kButtonSquare;
            mesh_id = draw_transparent
                          ? base::SysMeshID::kButtonSquareTransparent
                          : base::SysMeshID::kButtonSquareOpaque;
            l_border = 6;
            r_border = 9;
            b_border = 6;
            t_border = 6;
            break;
          }
          default: {
            if ((r_orig - l_orig) / (t_orig - b_orig) < 50.0f / 30.0f) {
              tex_id = base::SysTextureID::kUIAtlas;
              mesh_id = draw_transparent
                            ? base::SysMeshID::kButtonSmallTransparent
                            : base::SysMeshID::kButtonSmallOpaque;
              l_border = 10;
              r_border = 14;
              b_border = 9;
              t_border = 5;
            } else if ((r_orig - l_orig) / (t_orig - b_orig) < 200.0f / 35.0f) {
              tex_id = base::SysTextureID::kUIAtlas;
              mesh_id = draw_transparent
                            ? base::SysMeshID::kButtonMediumTransparent
                            : base::SysMeshID::kButtonMediumOpaque;
              l_border = 6;
              r_border = 10;
              b_border = 5;
              t_border = 2;
            } else if ((r_orig - l_orig) / (t_orig - b_orig) < 300.0f / 35.0f) {
              tex_id = base::SysTextureID::kUIAtlas;
              mesh_id = draw_transparent
                            ? base::SysMeshID::kButtonLargeTransparent
                            : base::SysMeshID::kButtonLargeOpaque;
              l_border = 7;
              r_border = 10;
              b_border = 10;
              t_border = 5;
            } else {
              tex_id = base::SysTextureID::kUIAtlas;
              mesh_id = draw_transparent
                            ? base::SysMeshID::kButtonLargerTransparent
                            : base::SysMeshID::kButtonLargerOpaque;
              l_border = 7;
              r_border = 11;
              b_border = 10;
              t_border = 4;
            }
            break;
          }
        }
        c.SetTexture(g_base->assets->SysTexture(tex_id));
        mesh = g_base->assets->SysMesh(mesh_id);
      }
      if (do_draw) {
        auto xf = c.ScopedTransform();
        c.Translate((l - l_border + r + r_border) * 0.5f + extra_offs_x,
                    (b - b_border + t + t_border) * 0.5f + extra_offs_y, 0);
        c.Scale(r - l + l_border + r_border, t - b + b_border + t_border, 1.0f);
        c.DrawMeshAsset(mesh);
      }

      // Draw icon.
      if ((show_icons) && draw_transparent) {
        bool do_draw_icon = true;
        if (icon_type_ == IconType::kStart) {
          c.SetColor(1.4f * mult * (color_red_), 1.4f * mult * (color_green_),
                     1.4f * mult * (color_blue_), 1.0f);
          c.SetTexture(
              g_base->assets->SysTexture(base::SysTextureID::kStartButton));
        } else if (icon_type_ == IconType::kCancel) {
          if (remote_icons) {
            c.SetColor(1.0f * mult * (1.0f), 1.0f * mult * (1.0f),
                       1.0f * mult * (1.0f), 1.0f);
            c.SetTexture(
                g_base->assets->SysTexture(base::SysTextureID::kBackIcon));
          } else {
            c.SetColor(1.5f * mult * (color_red_), 1.5f * mult * (color_green_),
                       1.5f * mult * (color_blue_), 1.0f);
            c.SetTexture(
                g_base->assets->SysTexture(base::SysTextureID::kBombButton));
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
          if (!icon_->loaded()) {
            do_draw_icon = false;
          } else {
            c.SetTexture(icon_);
          }
        } else {
          c.SetColor(1, 1, 1);
          c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kCircle));
        }
        if (do_draw_icon) {
          auto xf = c.ScopedTransform();
          c.Translate((l + r) * 0.5f + extra_offs_x
                          - (string_width * string_scale) * 0.5f - 5.0f,
                      (b + t) * 0.5f + extra_offs_y, 0.001f);
          c.Scale(34.0f * icon_scale_, 34.f * icon_scale_, 1.0f);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
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
    }
    c.Submit();
  }
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

  switch (m.type) {
    case base::WidgetMessage::Type::kMouseMove: {
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
    case base::WidgetMessage::Type::kMouseDown: {
      float x = m.fval1;
      float y = m.fval2;
      if (enabled_ && (x >= (-left_overlap)) && (x < (width_ + right_overlap))
          && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))) {
        mouse_over_ = true;
        pressed_ = true;

        if (repeat_) {
          repeat_timer_ = base::AppTimer::New(
              0.3, true, [this] { OnRepeatTimerExpired(); });

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
    case base::WidgetMessage::Type::kMouseUp:
    case base::WidgetMessage::Type::kMouseCancel: {
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
            if (m.type == base::WidgetMessage::Type::kMouseUp) {
              Activate();
            }
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

void ButtonWidget::DoActivate(bool is_repeat) {
  if (!enabled_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "ButtonWidget::DoActivate() called on disabled button");
    return;
  }

  // We don't want holding down a repeat-button to keep flashing it.
  if (!is_repeat) {
    last_activate_time_millisecs_ =
        static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  }
  if (sound_enabled_) {
    int r = rand() % 3;  // NOLINT
    if (r == 0) {
      g_base->audio->SafePlaySysSound(base::SysSoundID::kSwish);
    } else if (r == 1) {
      g_base->audio->SafePlaySysSound(base::SysSoundID::kSwish2);
    } else {
      g_base->audio->SafePlaySysSound(base::SysSoundID::kSwish3);
    }
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
