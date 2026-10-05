// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/check_box_widget.h"

#include <Python.h>

#include <algorithm>
#include <string>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::ui_v1 {

// A brief flash after a toggle, so presses too quick to show the held
// glow (taps, controller/keyboard activations) still get some visual
// kick. Over kToggleFlashMs, box/check/label brightness gets a boost
// fading out from kToggleFlashBoxAmt, and the backing glow starts out
// as strong as the click-hold glow and fades from there (never dimming
// a glow that's already stronger).
static constexpr millisecs_t kToggleFlashMs{200};
static constexpr float kToggleFlashBoxAmt{0.6f};

/// A disabled check box's box and check go grey at this multiple of
/// their color's luminance (as disabled ButtonWidgets' bodies do).
static constexpr float kDisabledGreyScale{0.85f};

static auto DisabledGrey_(float r, float g, float b) -> float {
  return kDisabledGreyScale * (0.3f * r + 0.59f * g + 0.11f * b);
}

CheckBoxWidget::CheckBoxWidget() {
  SetText("CheckBox");
  text_.set_owner_widget(this);
  text_.SetVAlign(TextWidget::VAlign::kCenter);
  text_.SetHAlign(TextWidget::HAlign::kLeft);
  birth_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
}

CheckBoxWidget::~CheckBoxWidget() = default;

void CheckBoxWidget::set_transition_delay(millisecs_t val) {
  transition_delay_ = val;
  // Our text runs its own copy of the transition (about its own
  // center); it was born alongside us so the timing lines up.
  text_.set_transition_delay(static_cast<float>(val));
}

void CheckBoxWidget::set_transition_type(TransitionType val) {
  transition_type_ = val;
  text_.set_transition_type(val == TransitionType::kScale
                                ? TextWidget::TransitionType::kScale
                                : TextWidget::TransitionType::kInLeft);
}

auto CheckBoxWidget::TransitionScale_(millisecs_t current_time) const -> float {
  if (transition_type_ != TransitionType::kScale) {
    return 1.0f;
  }
  float in_progress = static_cast<float>(birth_time_millisecs_
                                         + transition_delay_ - current_time);
  if (in_progress <= 0.0f) {
    return 1.0f;
  }
  // Fixed 150ms scale-up at the tail of the transition window
  // (quadratic ease-out), the same curve TextWidget/ButtonWidget use.
  constexpr float kScaleDurationMs = 150.0f;
  float t = std::max(0.0f, 1.0f - in_progress / kScaleDurationMs);
  return 1.0f - (1.0f - t) * (1.0f - t);
}

void CheckBoxWidget::SetOnValueChangeCall(PyObject* call_tuple) {
  on_value_change_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void CheckBoxWidget::SetText(const std::string& text) {
  text_.SetText(text);
  have_text_ = (!text.empty());
}

void CheckBoxWidget::SetLangStr(std::shared_ptr<const base::LangStr> val) {
  // A set language-string always counts as text present.
  have_text_ = (val != nullptr);
  text_.SetLangStr(std::move(val));
}

void CheckBoxWidget::SetWidth(float width_in) {
  highlight_dirty_ = box_dirty_ = check_dirty_ = true;
  width_ = width_in;
  text_.SetWidth(width_in - (2 * box_padding_ + box_size_ + 4));
  UpdateTextMaxWidth_();
}

void CheckBoxWidget::SetMaxWidth(float w) {
  max_width_ = w;
  UpdateTextMaxWidth_();
}

void CheckBoxWidget::UpdateTextMaxWidth_() {
  float val = max_width_;
  if (style_ == Style::kRight) {
    // Text runs from our left bounds to the box; always fit it to that
    // (leaving a bit of breathing room before the box art).
    float available =
        std::max(1.0f, width_ - (2 * box_padding_ + box_size_ + 12.0f));
    val = val > 0.0f ? std::min(val, available) : available;
  }
  text_.set_max_width(val);
}

void CheckBoxWidget::SetHeight(float height_in) {
  highlight_dirty_ = box_dirty_ = check_dirty_ = true;
  height_ = height_in;
  text_.SetHeight(height_in);
}

void CheckBoxWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  millisecs_t real_time = g_core->AppTimeMillisecs();

  have_drawn_ = true;
  float l = 0.0f;
  float r = l + width_;
  float b = 0.0f;
  float t = b + height_;

  Vector3f tilt = 0.01f * g_base->input->tilt();
  if (draw_control_parent()) {
    tilt += 0.02f * g_base->input->tilt();
  }
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  float glow_amt = 1.0f;

  // Post-toggle flash strength: 1 right at a toggle, fading to 0.
  float toggle_flash{};
  {
    millisecs_t since = real_time - last_activate_time_;
    if (since >= 0 && since < kToggleFlashMs) {
      toggle_flash =
          1.0f - static_cast<float>(since) / static_cast<float>(kToggleFlashMs);
    }
  }

  // Scale-in transition: the box group (glow, box, check) scales about
  // the box's center. Our text scales itself, about its own center (see
  // set_transition_delay()), so this transform must end before it draws.
  base::EmptyComponent transition_c(pass);
  transition_c.SetTransparent(draw_transparent);
  {
    auto transition_xf = transition_c.ScopedTransform();
    float transition_scale =
        TransitionScale_(pass->frame_def()->display_time_millisecs());
    if (transition_scale != 1.0f) {
      float box_cx = (style_ == Style::kRight ? r - box_padding_ - box_size_
                                              : l + box_padding_)
                     + box_size_ * 0.5f;
      float box_cy = b + (t - b) * 0.5f;
      transition_c.Translate(box_cx, box_cy, 0.0f);
      transition_c.Scale(transition_scale, transition_scale, 1.0f);
      transition_c.Translate(-box_cx, -box_cy, 0.0f);
    }
    transition_c.Submit();

    bool highlighted = selected() && g_base->ui->ShouldHighlightWidgets();
    if (have_text_ && draw_transparent
        && (highlighted || (pressed_ && mouse_over_) || toggle_flash > 0.0f)) {
      // Draw glow (at depth 0.9f).
      // The uniform glow reads much stronger than the gradient one at
      // the same factor (and its brightness goes as m squared -- m
      // scales both rgb and the premultiplying alpha), so it gets a
      // smaller one when pressed: 0.9 is ~20% of the brightness 2.0
      // would give.
      float pressed_m = style_ == Style::kRight ? 0.9f : 2.0f;
      float m;
      if (pressed_ && mouse_over_) {
        m = pressed_m;
      } else if (highlighted) {
        if (IsHierarchySelected()) {
          m = 0.5f
              + std::abs(sinf(static_cast<float>(real_time) * 0.006467f)
                         * 0.4f);
        } else {
          m = 0.25f;
        }
      } else {
        // Showing only for a toggle flash.
        m = 0.0f;
      }
      m = std::max(m, pressed_m * toggle_flash);

      if (highlight_dirty_) {
        if (style_ == Style::kDefault) {
          float l_border, r_border, b_border, t_border;
          l_border = 10.0f;
          r_border = 0.0f;
          b_border = 11.0f;
          t_border = 11.0f;
          highlight_width_ = r - l + l_border + r_border;
          highlight_height_ = t - b + b_border + t_border;
          highlight_center_x_ = l - l_border + highlight_width_ * 0.5f;
          highlight_center_y_ = b - b_border + highlight_height_ * 0.5f;
          highlight_mesh_.Clear();
        } else {
          assert(style_ == Style::kRight);
          // Uniform glow; same look as TextWidget's GlowType::kUniform.
          float corner_radius{30.0f};
          // Horizontally our bounds are flush with the text and box
          // while vertically they have some slack, and the side fades
          // run wider than the top/bottom ones (those are capped by our
          // height); extend further sideways so the glow reads as
          // reaching out equally all around.
          float x_extend{24.0f};
          float y_extend{6.0f};
          float width_fin = (r - l) + x_extend * 2.0f;
          float height_fin = (t - b) + y_extend * 2.0f;
          float x_border = base::NinePatchMesh::BorderForRadius(
              corner_radius, width_fin, height_fin);
          float y_border = base::NinePatchMesh::BorderForRadius(
              corner_radius, height_fin, width_fin);
          highlight_mesh_ = Object::New<base::NinePatchMesh>(
              -x_extend, -y_extend, 0.0f, width_fin, height_fin, x_border,
              y_border, x_border, y_border);
        }
        highlight_dirty_ = false;
      }
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      if (style_ == Style::kDefault) {
        c.SetPremultiplied(true);
        c.SetColor(0.25f * m, 0.3f * m, 0, 0.3f * m);
        c.SetTexture(g_ui_v1->assets().glow.get());
        {
          auto xf = c.ScopedTransform();
          c.Translate(highlight_center_x_, highlight_center_y_);
          c.Scale(highlight_width_, highlight_height_);
          c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
        }
      } else {
        auto* tex = g_ui_v1->assets().shadow_sharp.get();
        // Premultiply rgb by alpha for premultiplied textures so the
        // highlight composites 'over' under premult blend instead of adding
        // full-brightness rgb.
        float a = 0.3f * m;
        float cmul = tex->premultiplied() ? a : 1.0f;
        c.SetColor(0.9f * m * cmul, 1.0f * m * cmul, 0, a);
        c.SetTexture(tex);
        {
          auto xf = c.ScopedTransform();
          c.Translate(l, b);
          c.DrawMesh(highlight_mesh_.get());
        }
      }
      c.Submit();
    }

    {
      float box_l = style_ == Style::kRight ? r - box_padding_ - box_size_
                                            : l + box_padding_;
      float box_r = box_l + box_size_;
      float box_b = b + (t - b) / 2 - box_size_ / 2;
      float box_t = box_b + box_size_;

      if (pressed_ && mouse_over_) {
        glow_amt = 2.0f;
      } else if (IsHierarchySelected()
                 && g_base->ui->ShouldHighlightWidgets()) {
        // A wide swing so the box's own pulse still reads against the
        // selection glow pulsing behind it.
        glow_amt =
            0.9f
            + std::abs(sinf(static_cast<float>(real_time) * 0.006467f) * 0.7f);
      }

      glow_amt += kToggleFlashBoxAmt * toggle_flash;

      // Button portion (depth 0.1f-0.5f).
      {
        if (box_dirty_) {
          float l_border, r_border, b_border, t_border;
          l_border = 8;
          r_border = 12;
          b_border = 6;
          t_border = 6;
          box_width_ = box_r - box_l + l_border + r_border;
          box_height_ = box_t - box_b + b_border + t_border;
          box_center_x_ = box_l - l_border + box_width_ * 0.5f;
          box_center_y_ = box_b - b_border + box_height_ * 0.5f;
          box_dirty_ = false;
        }

        base::SimpleComponent c(pass);
        c.SetTransparent(draw_transparent);
        if (enabled_) {
          c.SetColor(glow_amt * color_r_, glow_amt * color_g_,
                     glow_amt * color_b_, 1);
        } else {
          float grey = glow_amt * DisabledGrey_(color_r_, color_g_, color_b_);
          c.SetColor(grey, grey, grey, 1);
        }
        c.SetTexture(g_ui_v1->assets().ui_atlas.get());
        {
          auto xf = c.ScopedTransform();
          c.Translate(box_center_x_ + extra_offs_x,
                      box_center_y_ + extra_offs_y, 0.1f);
          c.Scale(box_width_, box_height_, 0.4f);
          c.DrawMeshAsset((draw_transparent
                               ? g_ui_v1->assets().button_small_transparent
                               : g_ui_v1->assets().button_small_opaque)
                              .get());
        }
        c.Submit();
      }

      // Check portion.
      if (draw_transparent) {
        if (check_dirty_) {
          float s = 1;
          if (real_time - last_change_time_ < 100) {
            s = static_cast<float>(real_time - last_change_time_) / 100;
          }
          if (!checked_) s = 1.0f - s;

          float check_offset_h = -2;
          float check_offset_v = -2;

          check_width_ = 45 * s;
          check_height_ = 45 * s;
          check_center_x_ =
              box_l + 11 - 18 * s + check_offset_h + check_width_ * 0.5f;
          check_center_y_ =
              box_b + 10 - 18 * s + check_offset_v + check_height_ * 0.5f;

          // Only set clean once our transition is over.
          if (real_time - last_change_time_ > 100) check_dirty_ = false;
        }

        // Draw check in z depth from 0.5f to 1.
        base::SimpleComponent c(pass);
        c.SetTransparent(draw_transparent);
        if (is_radio_button_) {
          c.SetTexture(g_ui_v1->assets().nub.get());
        } else {
          c.SetTexture(g_ui_v1->assets().ui_atlas.get());
        }

        if (!enabled_) {
          float grey = glow_amt * DisabledGrey_(1.0f, 0.6f, 0.0f);
          c.SetColor(grey, grey, grey, 1);
        } else if (mouse_over_ && g_core->platform->IsRunningOnDesktop()) {
          c.SetColor(1.0f * glow_amt, 0.7f * glow_amt, 0, 1);
        } else {
          c.SetColor(1.0f * glow_amt, 0.6f * glow_amt, 0, 1);
        }
        {
          auto xf = c.ScopedTransform();
          if (is_radio_button_) {
            c.Translate(check_center_x_ + 1 + 3.0f * extra_offs_x,
                        check_center_y_ + 2 + 3.0f * extra_offs_y, 0.5f);
            c.Scale(check_width_ * 0.45f, check_height_ * 0.45f, 0.5f);
            c.Translate(-0.17f, -0.17f, 0.5f);
            c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
          } else {
            c.Translate(check_center_x_ + 3.0f * extra_offs_x,
                        check_center_y_ + 3.0f * extra_offs_y, 0.5f);
            c.Scale(check_width_, check_height_, 0.5f);
            c.DrawMeshAsset(g_ui_v1->assets().check_transparent.get());
          }
        }
        c.Submit();
      }
    }
  }  // End of the transition transform's scope.
  transition_c.Submit();

  // Draw our text in z depth 0.5f to 1.
  base::EmptyComponent c(pass);
  c.SetTransparent(draw_transparent);
  {
    auto xf = c.ScopedTransform();
    c.Translate(
        style_ == Style::kRight ? 0.0f : 2 * box_padding_ + box_size_ + 10, 0,
        0.5f);
    c.Scale(1, 1, 0.5f);
    c.Submit();
    float cs = glow_amt;
    text_.set_color(cs * text_color_r_, cs * text_color_g_, cs * text_color_b_,
                    text_color_a_);
    // (Disabled: TextWidget's own disabled look.)
    text_.SetEnabled(enabled_);
    text_.Draw(pass, draw_transparent);
  }
  c.Submit();
}

// for our center we return something near center of the checkbox; not our text
void CheckBoxWidget::GetCenter(float* x, float* y) {
  *x = tx() + scale() * GetWidth() * (style_ == Style::kRight ? 0.8f : 0.2f);
  *y = ty() + scale() * GetHeight() * 0.5f;
}

void CheckBoxWidget::SetStyle(Style style) {
  if (style == style_) {
    return;
  }
  style_ = style;
  highlight_dirty_ = box_dirty_ = check_dirty_ = true;
  UpdateTextMaxWidth_();
}

void CheckBoxWidget::SetValue(bool value) {
  if (value == checked_) {
    return;
  }
  check_dirty_ = true;

  // Don't animate if we're setting initial values.
  if (checked_ != value && have_drawn_) {
    last_change_time_ = g_core->AppTimeMillisecs();
  }
  checked_ = value;
}

void CheckBoxWidget::SetEnabled(bool val) {
  enabled_ = val;
  if (!enabled_) {
    mouse_over_ = false;
  }
}

void CheckBoxWidget::Activate() {
  // Disabled: selectable, but not toggleable; say no audibly.
  if (!enabled_) {
    g_base->audio->SafePlayBuiltinSound(base::BuiltinSoundID::kAudioError);
    return;
  }
  g_base->audio->PlaySound(g_ui_v1->assets().swish3.get());
  checked_ = !checked_;
  check_dirty_ = true;
  last_change_time_ = g_core->AppTimeMillisecs();
  last_activate_time_ = last_change_time_;
  if (auto* call = on_value_change_call_.get()) {
    PythonRef args(Py_BuildValue("(O)", checked_ ? Py_True : Py_False),
                   PythonRef::kSteal);

    // Schedule this to run immediately after any current UI traversal.
    call->ScheduleInUIOperation(args);
  }
}

auto CheckBoxWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  // How far outside button touches register.
  float left_overlap, top_overlap, right_overlap, bottom_overlap;
  if (g_core->platform->IsRunningOnDesktop()) {
    left_overlap = 3.0f;
    top_overlap = 1.0f;
    right_overlap = 0.0f;
    bottom_overlap = 0.0f;
  } else {
    left_overlap = 12.0f;
    top_overlap = 10.0f;
    right_overlap = 13.0f;
    bottom_overlap = 15.0f;
  }

  switch (m.type) {
    case base::WidgetMessage::Type::kMouseMove: {
      float x = m.fval1;
      float y = m.fval2;
      bool claimed = (m.fval3 > 0.0f);
      // (No hover while disabled, as with ButtonWidget.)
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
      if ((x >= (-left_overlap)) && (x < (width_ + right_overlap))
          && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))) {
        GlobalSelect();
        pressed_ = true;

        // A press lands where the pointer is, so it is over us now. Without
        // this, the held glow (pressed && mouse-over) only shows if a
        // mouse-move happened to reach us since our hover state was last
        // cleared -- so a second click without moving could show none.
        // Matches ButtonWidget. Dragging off while held still clears it
        // via kMouseMove. (Disabled: no held glow; the press just selects
        // us, and its release answers with an error sound via
        // Activate().)
        mouse_over_ = enabled_;
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

      // Radio-style boxes can't be un-checked.
      if (pressed_) {
        pressed_ = false;

        if (m.type == base::WidgetMessage::Type::kMouseUp) {
          // If they're still over us and unclaimed, toggle.
          if ((x >= (-left_overlap)) && (x < (width_ + right_overlap))
              && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))
              && !claimed) {
            // Radio-style buttons don't allow unchecking.
            if (!is_radio_button_ || !checked_) {
              Activate();
            }
          }
        }
        // If we're pressed, claim any mouse-ups/cancels presented to us.
        return true;
      }
      break;
    }
    default:
      break;
  }
  return false;
}

void CheckBoxWidget::OnLanguageChange() { text_.OnLanguageChange(); }

}  // namespace ballistica::ui_v1
