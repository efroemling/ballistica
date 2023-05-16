// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/text_widget.h"

#include "ballistica/base/app/app.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

const float kClearMargin{13.0f};

bool TextWidget::always_use_internal_keyboard_{false};

// FIXME: Move this to g_ui or something; not a global.
Object::WeakRef<TextWidget> TextWidget::android_string_edit_widget_;
TextWidget* TextWidget::GetAndroidStringEditWidget() {
  assert(g_base->InLogicThread());
  return android_string_edit_widget_.Get();
}

TextWidget::TextWidget() {
  // We always show our clear button except for in android when we don't
  // have a touchscreen (android-tv type situations).
  // FIXME - should generalize this to any controller-only situation.
  if (g_buildconfig.ostype_android()) {
    if (g_base->input->touch_input() == nullptr) {
      do_clear_button_ = false;
    }
  }

  birth_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
}

TextWidget::~TextWidget() = default;

void TextWidget::set_on_return_press_call(PyObject* call_tuple) {
  on_return_press_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void TextWidget::set_on_activate_call(PyObject* call_tuple) {
  on_activate_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void TextWidget::SetWidth(float width_in) {
  highlight_dirty_ = outline_dirty_ = true;
  width_ = width_in;
}

void TextWidget::SetHeight(float height_in) {
  highlight_dirty_ = outline_dirty_ = true;
  height_ = height_in;
}

void TextWidget::SetEditable(bool e) {
  if (e == editable_) {
    return;
  }

  // We don't translate when editable=true; need to refresh it.
  text_translation_dirty_ = true;
  editable_ = e;

  // Deselect us if we're selected.... update: why do we do this?
  if (!editable_ && !selectable_ && selected() && parent_widget())
    parent_widget()->SelectWidget(nullptr);
}

void TextWidget::SetEnabled(bool val) {
  enabled_ = val;

  // Deselect us if we're selected.
  if (!enabled_ && selected() && parent_widget()) {
    parent_widget()->SelectWidget(nullptr);
  }
}

void TextWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  millisecs_t current_time = pass->frame_def()->base_time();

  // All our stuff currently happens in the transparent pass.
  if (!draw_transparent) {
    return;
  }

  float l = padding_;
  float r = l + width_ - padding_;
  float b = padding_;
  float t = b + height_ - padding_;

  // If we're on a button or something, add tilt.
  {
    float tilt_scale = draw_control_parent() ? 0.04f : 0.01f;
    Vector3f tilt = tilt_scale * g_base->graphics->tilt();
    l -= tilt.y;
    r -= tilt.y;
    b += tilt.x;
    t += tilt.x;
  }

  // Center-scale.
  {
    // We should really be scaling our bounds and things,
    // but for now lets just do a hacky overall scale.
    base::EmptyComponent c(pass);
    c.SetTransparent(true);
    c.PushTransform();

    // Move to middle, scale down, move back.
    float offs_x = (r + l) / 2;
    float offs_y = (t + b) / 2;
    c.Translate(offs_x, offs_y, 0);
    c.Scale(center_scale_, center_scale_, 1.0f);
    c.Translate(-offs_x, -offs_y, 0);
    c.Submit();
  }

  if (editable() || IsSelectable()) {
    float bound_l = l - padding_;
    float bound_r = r + padding_;
    float bound_t = t + padding_;
    float bound_b = b - padding_;
    float border_width = -2;
    float border_height = -2;

    // Draw highlight.
    if ((IsSelectable()
         && ((selected() && always_highlight_) || IsHierarchySelected())
         && (always_highlight_ || g_base->ui->ShouldHighlightWidgets()))
        || ((pressed_ && mouse_over_)
            || (current_time - last_activate_time_millisecs_ < 200))) {
      float m;

      // Only pulsate if regular widget highlighting is on.
      if (g_base->ui->ShouldHighlightWidgets()) {
        if (IsHierarchySelected()) {
          m = 0.5f
              + std::abs(sinf(static_cast<float>(current_time) * 0.006467f)
                         * 0.4f);
        } else if (always_highlight_) {
          m = 0.7f;
        } else {
          m = 0.25f;
        }
      } else {
        m = 0.7f;
      }

      if (highlight_dirty_) {
        float l_border, r_border, b_border, t_border;
        float l2 = bound_l;
        float r2 = bound_r;
        float t2 = bound_t;
        float b2 = bound_b;
        l_border = std::max(10.0f, (r2 - l2) * 0.05f);
        r_border = 0;
        b_border = std::max(16.0f, (t2 - b2) * 0.16f);
        t_border = std::max(14.0f, (t2 - b2) * 0.14f);
        highlight_width_ = r2 - l2 + l_border + r_border;
        highlight_height_ = t2 - b2 + b_border + t_border;
        highlight_center_x_ = l2 - l_border + highlight_width_ * 0.5f;
        highlight_center_y_ = b2 - b_border + highlight_height_ * 0.5f;
        highlight_dirty_ = false;
      }

      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetPremultiplied(true);
      c.SetColor(0.25f * m, 0.3f * m, 0, 0.3f * m);
      c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kGlow));
      c.PushTransform();
      c.Translate(highlight_center_x_, highlight_center_y_, 0.1f);
      c.Scale(highlight_width_, highlight_height_);
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage4x1));
      c.PopTransform();
      c.Submit();
    }

    // Outline.
    if (editable()) {
      if (outline_dirty_) {
        float l_border = (r - l) * 0.04f;
        float r_border = (r - l) * 0.02f;
        float b_border = (t - b) * 0.07f;
        float t_border = (t - b) * 0.16f;
        outline_width_ = r - l + l_border + r_border;
        outline_height_ = t - b + b_border + t_border;
        outline_center_x_ = l - l_border + outline_width_ * 0.5f;
        outline_center_y_ = b - b_border + outline_height_ * 0.5f;
        outline_dirty_ = false;
      }
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, 1);
      c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kUIAtlas));
      c.PushTransform();
      c.Translate(outline_center_x_, outline_center_y_, 0.1f);
      c.Scale(outline_width_, outline_height_);
      c.DrawMeshAsset(
          g_base->assets->SysMesh(base::SysMeshID::kTextBoxTransparent));
      c.PopTransform();
      c.Submit();
    }

    // Clear button.
    if (editable() && (IsHierarchySelected() || always_show_carat_)
        && !text_raw_.empty() && do_clear_button_) {
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      if (clear_pressed_ && clear_mouse_over_) {
        c.SetColor(0.3f, 0.3f, 0.3f, 1);
      } else {
        c.SetColor(0.5f, 0.5f, 0.5f, 1);
      }
      c.SetTexture(
          g_base->assets->SysTexture(base::SysTextureID::kTextClearButton));
      c.PushTransform();
      c.Translate(r - 20, b * 0.5f + t * 0.5f, 0.1f);
      if (g_base->ui->scale() == UIScale::kSmall) {
        c.Scale(30, 30);
      } else {
        c.Scale(25, 25);
      }
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
      c.PopTransform();
      c.Submit();
    }

    // Constrain drawing to our bounds.
    if (editable()) {
      base::EmptyComponent c(pass);
      c.SetTransparent(true);
      c.ScissorPush(Rect(l + border_width, b + border_height, r - border_width,
                         t - border_height));
      c.Submit();
    }
  }

  float x_offset, y_offset;

  base::TextMesh::HAlign align_h;
  base::TextMesh::VAlign align_v;

  switch (alignment_h_) {
    case HAlign::kLeft:
      x_offset = l;
      align_h = base::TextMesh::HAlign::kLeft;
      break;
    case HAlign::kCenter:
      x_offset = (l + r) * 0.5f;
      align_h = base::TextMesh::HAlign::kCenter;
      break;
    case HAlign::kRight:
      x_offset = r;
      align_h = base::TextMesh::HAlign::kRight;
      break;
    default:
      throw Exception("Invalid HAlign");
  }
  switch (alignment_v_) {
    case VAlign::kTop:
      y_offset = t;
      align_v = base::TextMesh::VAlign::kTop;
      break;
    case VAlign::kCenter:
      y_offset = (b + t) * 0.5f;
      align_v = base::TextMesh::VAlign::kCenter;
      break;
    case VAlign::kBottom:
      y_offset = b;
      align_v = base::TextMesh::VAlign::kBottom;
      break;
    default:
      throw Exception("Invalid VAlign");
  }

  float transition =
      (static_cast<float>(birth_time_millisecs_) + transition_delay_)
      - static_cast<float>(current_time);
  if (transition > 0) {
    x_offset -= transition * 4.0f / (std::max(0.001f, center_scale_));
  }

  // Apply subs/resources to get our actual text if need be.
  UpdateTranslation();

  if (!text_group_.Exists()) {
    text_group_ = Object::New<base::TextGroup>();
  }
  if (text_group_dirty_) {
    text_group_->SetText(text_translated_, align_h, align_v, big_, res_scale_);
    text_width_ = g_base->text_graphics->GetStringWidth(text_translated_, big_);

    // FIXME: doesnt support big.
    text_height_ = g_base->text_graphics->GetStringHeight(text_translated_);
    text_group_dirty_ = false;
  }

  float max_width_scale = 1.0f;
  float max_height_scale = 1.0f;
  {
    // Calc draw-brightness (for us and our children).
    float color_mult = 1.0f;
    if (Widget* draw_controller = draw_control_parent()) {
      color_mult *= draw_controller->GetDrawBrightness(current_time);
    }

    float fin_a = enabled_ ? color_a_ : 0.4f * color_a_;

    base::SimpleComponent c(pass);
    c.SetTransparent(true);

    if ((pressed_ && mouse_over_)
        || (current_time - last_activate_time_millisecs_ < 200)) {
      color_mult *= 2.0f;
    } else if (always_highlight_ && selected()) {
      color_mult *= 1.4f;
    }
    float fin_color_r = color_r_ * color_mult;
    float fin_color_g = color_g_ * color_mult;
    float fin_color_b = color_b_ * color_mult;

    int elem_count = text_group_->GetElementCount();
    for (int e = 0; e < elem_count; e++) {
      // Gracefully skip unloaded textures..
      base::TextureAsset* t2 = text_group_->GetElementTexture(e);
      if (!t2->preloaded()) {
        continue;
      }
      c.SetTexture(t2);
      c.SetMaskUV2Texture(text_group_->GetElementMaskUV2Texture(e));
      c.SetShadow(-0.004f * text_group_->GetElementUScale(e),
                  -0.004f * text_group_->GetElementVScale(e), 0.0f,
                  shadow_ * color_a_);
      if (text_group_->GetElementCanColor(e)) {
        c.SetColor(fin_color_r, fin_color_g, fin_color_b, fin_a);
      } else {
        c.SetColor(1, 1, 1, fin_a);
      }

      if (g_core->IsVRMode()) {
        c.SetFlatness(text_group_->GetElementMaxFlatness(e));
      } else {
        c.SetFlatness(
            std::min(text_group_->GetElementMaxFlatness(e), flatness_));
      }
      c.PushTransform();
      c.Translate(x_offset, y_offset, 0.1f);
      if (rotate_ != 0.0f) {
        c.Rotate(rotate_, 0, 0, 1);
      }
      if (max_width_ > 0.0f && text_width_ > 0.0
          && ((text_width_ * center_scale_) > max_width_)) {
        max_width_scale = max_width_ / (text_width_ * center_scale_);
        c.Scale(max_width_scale, max_width_scale);
      }
      // Currently cant do max-height with big.
      assert(max_height_ <= 0.0 || !big_);
      if (max_height_ > 0.0f && text_height_ > 0.0
          && ((text_height_ * center_scale_ * max_width_scale) > max_height_)) {
        max_height_scale =
            max_height_ / (text_height_ * center_scale_ * max_width_scale);
        c.Scale(max_height_scale, max_height_scale);
      }
      c.DrawMesh(text_group_->GetElementMesh(e));
      c.PopTransform();
    }
    c.Submit();
  }

  if (editable()) {
    // Draw the carat.
    if (IsHierarchySelected() || always_show_carat_) {
      bool show_cursor = true;
      if (ShouldUseStringEditDialog()) {
        show_cursor = false;
      }
      if (show_cursor
          && ((current_time / 100) % 2 == 0
              || (current_time - last_carat_change_time_millisecs_ < 250))) {
        int str_size = Utils::UTF8StringLength(text_raw_.c_str());
        if (carat_position_ > str_size) {
          carat_position_ = str_size;
        }
        float h, v;
        text_group_->GetCaratPts(text_raw_, align_h, align_v, carat_position_,
                                 &h, &v);
        base::SimpleComponent c(pass);
        c.SetPremultiplied(true);
        c.SetTransparent(true);
        c.PushTransform();
        c.SetColor(0.17f, 0.12f, 0, 0);
        c.Translate(x_offset, y_offset);
        float max_width_height_scale = max_width_scale * max_height_scale;
        c.Scale(max_width_height_scale, max_width_height_scale);
        c.Translate(h + 4, v + 17.0f);
        c.Scale(6, 27);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        c.SetColor(1, 1, 1, 0);
        c.Scale(0.3f, 0.8f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        c.PopTransform();
        c.Submit();
      }
    }
    base::EmptyComponent c(pass);
    c.SetTransparent(true);
    c.ScissorPop();
    c.Submit();
  }

  // Pop initial positioning.
  {
    base::EmptyComponent c(pass);
    c.SetTransparent(true);
    c.PopTransform();
    c.Submit();
  }
}

void TextWidget::set_res_scale(float res_scale) {
  if (res_scale != res_scale_) {
    text_group_dirty_ = true;
  }
  res_scale_ = res_scale;
}

void TextWidget::SetText(const std::string& text_in_raw) {
  std::string text_in = Utils::GetValidUTF8(text_in_raw.c_str(), "twst1");

  // In some cases we want to make sure this is a valid resource-string
  // since catching the error here is much more useful than if we catch
  // it at draw-time.  However this is expensive so we only do it for debug
  // mode or if the string looks suspicious.
  bool do_format_check{};
  bool print_false_positives{};

  // Only non-editable text support resource-strings.
  if (!editable_) {
    if (g_buildconfig.debug_build()) {
      do_format_check = explicit_bool(true);
    } else {
      if (text_in_raw.size() > 1 && text_in_raw[0] == '{'
          && text_in_raw[text_in_raw.size() - 1] == '}') {
        // Ok, its got bounds like json; now if its either missing quotes or a
        // colon then let's check it.
        if (!strstr(text_in_raw.c_str(), "\"")
            || !strstr(text_in_raw.c_str(), ":")) {
          do_format_check = true;

          // We wanna avoid doing this check when we don't have to.
          // so lets print if we get a false positive
          print_false_positives = true;
        }
      }
    }
  }

  if (do_format_check) {
    bool valid;
    g_base->assets->CompileResourceString(
        text_in_raw, "TextWidget::set_text format check", &valid);
    if (!valid) {
      BA_LOG_ONCE(LogLevel::kError,
                  "Invalid resource string: '" + text_in_raw + "'");
      Python::PrintStackTrace();
    } else if (explicit_bool(print_false_positives)) {
      BA_LOG_ONCE(LogLevel::kError,
                  "Got false positive for json check on '" + text_in_raw + "'");
      Python::PrintStackTrace();
    }
  }
  if (text_in != text_raw_) {
    text_translation_dirty_ = true;
  }
  text_raw_ = text_in;

  // Do our clamping in unicode-space.
  if (Utils::UTF8StringLength(text_raw_.c_str()) > max_chars_) {
    std::vector<uint32_t> uni = Utils::UnicodeFromUTF8(text_raw_, "fjcoiwef");
    assert(max_chars_ >= 0);
    uni.resize(static_cast<size_t>(max_chars_));
    text_raw_ = Utils::UTF8FromUnicode(uni);
  }
  carat_position_ = 9999;
}

void TextWidget::SetBig(bool big) {
  if (big != big_) {
    text_group_dirty_ = true;
  }
  big_ = big;
}

// FIXME: Unify this with the drawing code.
auto TextWidget::GetWidth() -> float {
  // Changing this to just return set width.
  // What benefit would we get by returning adaptive vals?
  return width_;
}

// FIXME: Unify this with the drawing code.
auto TextWidget::GetHeight() -> float {
  // Changing this to just return set height.
  // What benefit would we get by returning adaptive vals?
  return height_;
}

auto TextWidget::ShouldUseStringEditDialog() const -> bool {
  if (g_core->HeadlessMode()) {
    return false;
  }
  if (force_internal_editing_) {
    return false;
  }
  if (always_use_internal_keyboard_) {
    return true;
  }

  // On most platforms we always want to do this.
  // on mac/pc, however, we use inline editing if the current UI input-device
  // is the mouse or keyboard
  if (g_buildconfig.ostype_macos() || g_buildconfig.ostype_windows()
      || g_buildconfig.ostype_linux()) {
    base::InputDevice* ui_input_device = g_base->ui->GetUIInputDevice();
    return !(ui_input_device == nullptr
             || ui_input_device == g_base->input->keyboard_input());
  } else {
    return true;
  }
}

void TextWidget::BringUpEditDialog() {
  bool use_internal_dialog = true;

  // in vr we always use our own dialog..
  if (g_core->IsVRMode()) {
    use_internal_dialog = true;
  } else {
    // on android, use the android keyboard unless the user want to use ours..
    if (!always_use_internal_keyboard_) {
      // on android we pull up a native dialog

      // (FIXME - abstract this to platform so we can use it elsewhere)
      if (g_buildconfig.ostype_android()) {
        use_internal_dialog = false;
        // store ourself as the current text-widget and kick off an edit
        android_string_edit_widget_ = this;
        g_base->app->PushStringEditCall(description_, text_raw_, max_chars_);
      }
    }
  }
  if (explicit_bool(use_internal_dialog)) {
    g_ui_v1->python->LaunchStringEdit(this);
  }
}

void TextWidget::Activate() {
  last_activate_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  if (auto* call = on_activate_call_.Get()) {
    // Call this in the next cycle (don't wanna risk mucking with UI from within
    // a UI loop).
    call->ScheduleWeak();
  }

  // If we're on ouya and this is editable, it brings up our string-editor.
  if (editable_ && ShouldUseStringEditDialog()) {
    BringUpEditDialog();
  }
}

auto TextWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  if (g_core->HeadlessMode()) {
    return false;
  }

  // How far outside our bounds touches register.
  float left_overlap, top_overlap, right_overlap, bottom_overlap;
  if (g_core->platform->IsRunningOnDesktop()) {
    left_overlap = 0.0f;
    top_overlap = 0.0f;
    right_overlap = 0.0f;
    bottom_overlap = 0.0f;
  } else {
    left_overlap = 3.0f * extra_touch_border_scale_;
    top_overlap = 3.0f * extra_touch_border_scale_;
    right_overlap = 3.0f * extra_touch_border_scale_;
    bottom_overlap = 3.0f * extra_touch_border_scale_;
  }

  // If we're doing inline editing, handle clipboard paste.
  if (editable() && !ShouldUseStringEditDialog()
      && m.type == base::WidgetMessage::Type::kPaste) {
    if (g_core->platform->ClipboardIsSupported()) {
      if (g_core->platform->ClipboardHasText()) {
        // Just enter it char by char as if we had typed it...
        AddCharsToText(g_core->platform->ClipboardGetText());
      }
    }
  }
  // If we're doing inline editing, handle some key events.
  if (m.has_keysym && !ShouldUseStringEditDialog()) {
    last_carat_change_time_millisecs_ =
        static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

    text_group_dirty_ = true;
    bool claimed = false;
    switch (m.keysym.sym) {
      case SDLK_UP:
      case SDLK_DOWN:
      case SDLK_TAB:
        // never claim up/down/tab
        return false;
      case SDLK_RETURN:
      case SDLK_KP_ENTER:
        if (g_buildconfig.ostype_ios_tvos() || g_buildconfig.ostype_android()) {
          // On mobile, return currently just deselects us.
          g_base->audio->PlaySound(
              g_base->assets->SysSound(base::SysSoundID::kSwish));
          parent_widget()->SelectWidget(nullptr);
          return true;
        } else {
          if (auto* call = on_return_press_call_.Get()) {
            claimed = true;
            // Call this in the next cycle (don't wanna risk mucking with UI
            // from within a UI loop)
            call->ScheduleWeak();
          }
        }
        break;
      case SDLK_LEFT:
        if (editable()) {
          claimed = true;
          if (carat_position_ > 0) {
            carat_position_--;
          }
        }
        break;
      case SDLK_RIGHT:
        if (editable()) {
          claimed = true;
          carat_position_++;
        }
        break;
      case SDLK_BACKSPACE:
      case SDLK_DELETE:
        if (editable()) {
          claimed = true;
          std::vector<uint32_t> unichars =
              Utils::UnicodeFromUTF8(text_raw_, "c94j8f");
          auto len = static_cast<int>(unichars.size());
          if (len > 0) {
            if (carat_position_ > 0) {
              int pos = carat_position_ - 1;
              if (pos > len - 1) {
                pos = len - 1;
              }
              unichars.erase(unichars.begin() + pos);
              text_raw_ = Utils::UTF8FromUnicode(unichars);
              text_translation_dirty_ = true;
              carat_position_--;
            }
          }
        }
        break;
      default:
        break;
    }
    if (!claimed) {
      // Pop in a char.
      if (editable()) {
        claimed = true;

#if BA_SDL2_BUILD || BA_MINSDL_BUILD
        // On SDL2, chars come through as TEXT_INPUT messages;
        // can ignore this.
#else
        std::vector<uint32_t> unichars =
            Utils::UnicodeFromUTF8(text_raw_, "2jf987");
        int len = static_cast<int>(unichars.size());

        if (len < max_chars_) {
          if ((m.keysym.unicode >= 32) && (m.keysym.sym != SDLK_TAB)) {
            claimed = true;
            int pos = carat_position_;
            if (pos > len) pos = len;
            unichars.insert(unichars.begin() + pos, m.keysym.unicode);
            text_raw_ = Utils::UTF8FromUnicode(unichars);
            text_translation_dirty_ = true;
            carat_position_++;
          } else {
            // These don't seem to come through cleanly as unicode:
            // FIXME - should re-check this on SDL2 builds

            claimed = true;
            std::string s;
            uint32_t pos = carat_position_;
            if (pos > len) pos = len;
            switch (m.keysym.sym) {
              case SDLK_KP0:
                s = '0';
                break;
              case SDLK_KP1:
                s = '1';
                break;
              case SDLK_KP2:
                s = '2';
                break;
              case SDLK_KP3:
                s = '3';
                break;
              case SDLK_KP4:
                s = '4';
                break;
              case SDLK_KP5:
                s = '5';
                break;
              case SDLK_KP6:
                s = '6';
                break;
              case SDLK_KP7:
                s = '7';
                break;
              case SDLK_KP8:
                s = '8';
                break;
              case SDLK_KP9:
                s = '9';
                break;
              case SDLK_KP_PERIOD:
                s = '.';
                break;
              case SDLK_KP_DIVIDE:
                s = '/';
                break;
              case SDLK_KP_MULTIPLY:
                s = '*';
                break;
              case SDLK_KP_MINUS:
                s = '-';
                break;
              case SDLK_KP_PLUS:
                s = '+';
                break;
              case SDLK_KP_EQUALS:
                s = '=';
                break;
              default:
                break;
            }
            if (s.size() > 0) {
              unichars.insert(unichars.begin() + pos, s[0]);
              text_raw_ = Utils::UTF8FromUnicode(unichars);
              text_translation_dirty_ = true;
              carat_position_++;
            }
          }
        }
#endif  // BA_SDL2_BUILD
      }
    }
    return claimed;
  }
  switch (m.type) {
    case base::WidgetMessage::Type::kTextInput: {
      // If we're using an edit dialog, any attempted text input just kicks us
      // over to that.
      if (editable() && ShouldUseStringEditDialog()) {
        BringUpEditDialog();
      } else {
        // Otherwise apply the text directly.
        if (editable() && m.sval != nullptr) {
          AddCharsToText(*m.sval);
          return true;
        }
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseMove: {
      if (!IsSelectable()) {
        return false;
      }
      float x{ScaleAdjustedX(m.fval1)};
      float y{ScaleAdjustedY(m.fval2)};
      bool claimed = (m.fval3 > 0.0f);
      if (claimed) {
        mouse_over_ = clear_mouse_over_ = false;
      } else {
        mouse_over_ =
            ((x >= (-left_overlap)) && (x < (width_ + right_overlap))
             && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap)));
        clear_mouse_over_ =
            ((x >= width_ - 35 - kClearMargin) && (x < width_ + kClearMargin)
             && (y > -kClearMargin) && (y < height_ + kClearMargin));
      }
      return mouse_over_;
    }
    case base::WidgetMessage::Type::kMouseDown: {
      if (!IsSelectable()) {
        return false;
      }
      float x{ScaleAdjustedX(m.fval1)};
      float y{ScaleAdjustedY(m.fval2)};

      auto click_count = static_cast<int>(m.fval3);

      // See if a click is in our clear button.
      if (editable() && (IsHierarchySelected() || always_show_carat_)
          && !text_raw_.empty() && (x >= width_ - 35)
          && (x < width_ + kClearMargin) && (y > -kClearMargin)
          && (y < height_ + kClearMargin) && do_clear_button_) {
        clear_pressed_ = clear_mouse_over_ = true;
        return true;
      }
      if ((x >= (-left_overlap)) && (x < (width_ + right_overlap))
          && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))) {
        ContainerWidget* c = parent_widget();
        if (c && IsSelectable()) {
          // In cases where we have a keyboard, this also sets that as
          // the ui input device. If we don't, an on-screen keyboard will
          // likely pop up for the current input-device.
          // FIXME: may need to test/tweak this behavior for cases where
          //  we pop up a UI dialog for text input..
          if (editable()) {
            if (auto* kb = g_base->input->keyboard_input()) {
              g_base->ui->SetUIInputDevice(kb);
            }
          }
          GlobalSelect();
          pressed_ = true;

          // Second click (or first if we want) puts us in
          // potentially-activating-mode.
          pressed_activate_ =
              (click_count == 2 || click_activate_) && !editable_;
          if (click_count == 1) {
            g_base->audio->PlaySound(
                g_base->assets->SysSound(base::SysSoundID::kTap));
          }
        }
        return true;
      } else {
        return false;
      }
    }
    case base::WidgetMessage::Type::kMouseUp: {
      float x{ScaleAdjustedX(m.fval1)};
      float y{ScaleAdjustedY(m.fval2)};
      bool claimed = (m.fval3 > 0.0f);

      if (clear_pressed_ && !claimed && editable()
          && (IsHierarchySelected() || always_show_carat_)
          && (!text_raw_.empty()) && (x >= width_ - 35 - kClearMargin)
          && (x < width_ + kClearMargin) && (y >= 0 - kClearMargin)
          && (y < height_ + kClearMargin)) {
        text_raw_ = "";
        text_translation_dirty_ = true;
        carat_position_ = 0;
        text_group_dirty_ = true;
        clear_pressed_ = false;
        g_base->audio->PlaySound(
            g_base->assets->SysSound(base::SysSoundID::kTap));
        return true;
      }
      clear_pressed_ = false;
      if (pressed_) {
        pressed_ = false;

        // for non-editable text, mouse-ups within our region trigger an
        // activate
        if (pressed_activate_ && (x >= (-left_overlap))
            && (x < (width_ + right_overlap)) && (y >= (-bottom_overlap))
            && (y < (height_ + top_overlap)) && !claimed) {
          Activate();
          pressed_activate_ = false;
        } else if (editable_ && ShouldUseStringEditDialog()
                   && (x >= (-left_overlap)) && (x < (width_ + right_overlap))
                   && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))
                   && !claimed) {
          // With dialog-editing, a click/tap brings up our editor.
          BringUpEditDialog();
        }

        // Pressed buttons always claim mouse-ups presented to them.
        return true;
      }
      break;
    }
    default:
      break;
  }
  return false;
}

auto TextWidget::ScaleAdjustedX(float x) -> float {
  // Account for our center_scale_ value.
  float offsx = x - width_ * 0.5f;
  return width_ * 0.5f + offsx / center_scale_;
}

auto TextWidget::ScaleAdjustedY(float y) -> float {
  // Account for our center_scale_ value.
  float offsy = y - height_ * 0.5f;
  return height_ * 0.5f + offsy / center_scale_;
}

void TextWidget::AddCharsToText(const std::string& addchars) {
  assert(editable());
  std::vector<uint32_t> unichars = Utils::UnicodeFromUTF8(text_raw_, "jcjwf8f");
  int len = static_cast<int>(unichars.size());
  std::vector<uint32_t> sval = Utils::UnicodeFromUTF8(addchars, "j4958fbv");
  for (unsigned int i : sval) {
    if (len < max_chars_) {
      text_group_dirty_ = true;
      if (carat_position_ > len) {
        carat_position_ = len;
      }
      unichars.insert(unichars.begin() + carat_position_, i);
      len++;
      carat_position_++;
    }
  }
  text_raw_ = Utils::UTF8FromUnicode(unichars);
  text_translation_dirty_ = true;
}

void TextWidget::UpdateTranslation() {
  // Apply subs/resources to get our actual text if need be.
  if (text_translation_dirty_) {
    // We don't run translations on user-editable text.
    if (editable()) {
      text_translated_ = text_raw_;
    } else {
      text_translated_ = g_base->assets->CompileResourceString(
          text_raw_, "TextWidget::UpdateTranslation");
    }
    text_translation_dirty_ = false;
    text_group_dirty_ = true;
  }
}

auto TextWidget::GetTextWidth() -> float {
  UpdateTranslation();

  // Should we cache this?
  return g_base->text_graphics->GetStringWidth(text_translated_, big_);
}

void TextWidget::OnLanguageChange() { text_translation_dirty_ = true; }

}  // namespace ballistica::ui_v1
