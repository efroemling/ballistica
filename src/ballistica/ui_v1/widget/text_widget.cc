// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/text_widget.h"

#include <Python.h>

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

const float kClearMargin{13.0f};

TextWidget::TextWidget() {
  // We always show our clear button except for in android when we don't
  // have a touchscreen (android-tv type situations).
  //
  // FIXME - should generalize this to any controller-only situation.
  if (g_buildconfig.platform_android()) {
    if (g_base->input->touch_input() == nullptr) {
      implicit_clear_button_ = false;
    }
  }
  birth_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
}

TextWidget::~TextWidget() = default;

void TextWidget::SetOnReturnPressCall(PyObject* call_tuple) {
  on_return_press_call_ = Object::New<base::PythonContextCall>(call_tuple);
}

void TextWidget::SetOnActivateCall(PyObject* call_tuple) {
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
  // All our stuff currently happens in the transparent pass.
  if (!draw_transparent) {
    return;
  }

  millisecs_t current_time = pass->frame_def()->display_time_millisecs();

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
    // We should really be scaling our bounds and things, but for now lets
    // just do a hacky overall scale.
    base::EmptyComponent c(pass);
    c.SetTransparent(true);

    // FIXME(ericf): This component has an unmatched push and we have
    // another component at the end with the matching pop. This only works
    // because the components in the middle wind up writing to the same draw
    // list, but there is nothing checking or enforcing that so it would be
    // easy to break. Should improve this somehow. (perhaps by using a
    // single component and enforcing list uniformity between push/pop
    // blocks?)
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
        if (glow_type_ == GlowType::kGradient) {
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
          highlight_mesh_.Clear();
        } else {
          assert(glow_type_ == GlowType::kUniform);
          float corner_radius{30.0f};
          float width{bound_r - bound_l};
          float height{bound_t - bound_b};
          float x_extend{12.0f};
          float y_extend{6.0f};
          float x_offset{0.0f};
          float width_fin = width + x_extend * 2.0f;
          float height_fin = height + y_extend * 2.0f;
          float x_border = base::NinePatchMesh::BorderForRadius(
              corner_radius, width_fin, height_fin);
          float y_border = base::NinePatchMesh::BorderForRadius(
              corner_radius, height_fin, width_fin);

          highlight_mesh_ = Object::New<base::NinePatchMesh>(
              -x_extend + x_offset, -y_extend, 0.0f, width_fin, height_fin,
              x_border, y_border, x_border, y_border);
        }
        highlight_dirty_ = false;
      }

      if (glow_type_ == GlowType::kGradient) {
        base::SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetPremultiplied(true);
        c.SetColor(0.25f * m, 0.3f * m, 0, 0.3f * m);
        c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kGlow));
        {
          auto xf = c.ScopedTransform();
          c.Translate(highlight_center_x_, highlight_center_y_, 0.1f);
          c.Scale(highlight_width_, highlight_height_);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage4x1));
        }
      } else {
        assert(glow_type_ == GlowType::kUniform);
        base::SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetColor(0.9 * m, 1.0f * m, 0, 0.3f * m);
        c.SetTexture(
            g_base->assets->SysTexture(base::SysTextureID::kShadowSharp));
        {
          auto xf = c.ScopedTransform();
          c.Translate(bound_l, bound_b, 0.1f);
          c.DrawMesh(highlight_mesh_.get());
        }
      }
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
      {
        auto xf = c.ScopedTransform();
        c.Translate(outline_center_x_, outline_center_y_, 0.1f);
        c.Scale(outline_width_, outline_height_);
        c.DrawMeshAsset(
            g_base->assets->SysMesh(base::SysMeshID::kTextBoxTransparent));
      }
      c.Submit();
    }

    // Clear button.
    if (editable() && (IsHierarchySelected() || always_show_carat_)
        && !text_raw_.empty() && implicit_clear_button_
        && allow_clear_button_) {
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      if (clear_pressed_ && clear_mouse_over_) {
        c.SetColor(0.3f, 0.3f, 0.3f, 1);
      } else {
        c.SetColor(0.5f, 0.5f, 0.5f, 1);
      }
      c.SetTexture(
          g_base->assets->SysTexture(base::SysTextureID::kTextClearButton));
      {
        auto xf = c.ScopedTransform();
        c.Translate(r - 20, b * 0.5f + t * 0.5f, 0.1f);
        if (g_base->ui->uiscale() == UIScale::kSmall) {
          c.Scale(30, 30);
        } else {
          c.Scale(25, 25);
        }
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
      }
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
  UpdateTranslation_();

  if (!text_group_.exists()) {
    text_group_ = Object::New<base::TextGroup>();
  }
  if (text_group_dirty_) {
    text_group_->SetText(text_translated_, align_h, align_v, big_, res_scale_);
    text_width_ = g_base->text_graphics->GetStringWidth(text_translated_, big_);

    // FIXME: doesnt support big.
    text_height_ = g_base->text_graphics->GetStringHeight(text_translated_);
    text_group_dirty_ = false;
  }

  // Calc scaling factors due to max width/height restrictions.
  float max_width_scale = 1.0f;
  float max_height_scale = 1.0f;
  if (max_width_ > 0.0f && text_width_ > 0.0
      && ((text_width_ * center_scale_) > max_width_)) {
    max_width_scale = max_width_ / (text_width_ * center_scale_);
  }
  // Currently cant do max-height with big.
  assert(max_height_ <= 0.0 || !big_);
  if (max_height_ > 0.0f && text_height_ > 0.0
      && ((text_height_ * center_scale_ * max_width_scale) > max_height_)) {
    max_height_scale =
        max_height_ / (text_height_ * center_scale_ * max_width_scale);
  }

  DoDrawText_(pass, x_offset, y_offset, max_width_scale, max_height_scale);

  if (editable()) {
    // Draw the carat.
    DoDrawCarat_(pass, align_h, align_v, x_offset, y_offset, max_width_scale,
                 max_height_scale);

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

void TextWidget::DoDrawText_(base::RenderPass* pass, float x_offset,
                             float y_offset, float max_width_scale,
                             float max_height_scale) {
  millisecs_t current_time{pass->frame_def()->display_time_millisecs()};

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
    // Gracefully skip unloaded textures.
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

    // In VR, draw everything flat because it's generally harder to read.
    if (g_core->vr_mode()) {
      c.SetFlatness(text_group_->GetElementMaxFlatness(e));
    } else {
      c.SetFlatness(std::min(text_group_->GetElementMaxFlatness(e), flatness_));
    }
    {
      auto xf = c.ScopedTransform();
      c.Translate(x_offset, y_offset, 0.1f);
      if (rotate_ != 0.0f) {
        c.Rotate(rotate_, 0, 0, 1);
      }
      if (max_width_scale != 1.0f) {
        c.Scale(max_width_scale, max_width_scale);
      }
      if (max_height_scale != 1.0f) {
        c.Scale(max_height_scale, max_height_scale);
      }
      c.DrawMesh(text_group_->GetElementMesh(e));
    }
  }
  c.Submit();
}

void TextWidget::DoDrawCarat_(base::RenderPass* pass,
                              base::TextMesh::HAlign align_h,
                              base::TextMesh::VAlign align_v, float x_offset,
                              float y_offset, float max_width_scale,
                              float max_height_scale) {
  millisecs_t current_time{pass->frame_def()->display_time_millisecs()};
  if (IsHierarchySelected() || always_show_carat_) {
    bool show_cursor = true;
    if (ShouldUseStringEditor_()) {
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
      text_group_->GetCaratPts(text_raw_, align_h, align_v, carat_position_, &h,
                               &v);
      base::SimpleComponent c(pass);
      c.SetPremultiplied(true);
      c.SetTransparent(true);
      {
        auto xf = c.ScopedTransform();
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
      }
      c.Submit();
    }
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

  // Ignore redundant sets.
  if (text_in == text_raw_) {
    return;
  }

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
    g_base->assets->CompileResourceString(text_in_raw, &valid);
    if (!valid) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Invalid resource string: '" + text_in_raw + "'");
      Python::PrintStackTrace();
    } else if (explicit_bool(print_false_positives)) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Got false positive for json check on '" + text_in_raw + "'");
      Python::PrintStackTrace();
    }
  }

  // Do our clamping in unicode-space.
  if (Utils::UTF8StringLength(text_raw_.c_str()) > max_chars_) {
    std::vector<uint32_t> uni = Utils::UnicodeFromUTF8(text_raw_, "fjcoiwef");
    assert(max_chars_ >= 0);
    uni.resize(static_cast<size_t>(max_chars_));
    text_raw_ = Utils::UTF8FromUnicode(uni);
  }
  text_translation_dirty_ = true;
  text_raw_ = text_in;
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

void TextWidget::Activate() {
  last_activate_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  if (auto* call = on_activate_call_.get()) {
    // Schedule this to run immediately after any current UI traversal.
    call->ScheduleInUIOperation();
  }

  // Bring up an editor if applicable.
  if (editable_ && ShouldUseStringEditor_()) {
    InvokeStringEditor_();
  }
}

auto TextWidget::ShouldUseStringEditor_() const -> bool {
  assert(!g_core->HeadlessMode());  // Should not get called here.

  // Obscure cases such as the text-widget *on* our built-in on-screen
  // editor (obviously it should itself not pop up an editor).
  if (force_internal_editing_) {
    return false;
  }

  // If the user wants to use our widget-based keyboard, always say yes
  // here.
  if (g_ui_v1->always_use_internal_on_screen_keyboard()) {
    return true;
  }

  // If the UI is getting fed actual keyboard events, no string-editor needed.
  return !g_base->ui->UIHasDirectKeyboardInput();
}

void TextWidget::InvokeStringEditor_() {
  assert(g_base->InLogicThread());

  // If there's already a valid edit attached to us, do nothing.
  if (string_edit_adapter_.exists()
      && !g_base->python->CanPyStringEditAdapterBeReplaced(
          string_edit_adapter_.get())) {
    return;
  }

  // Create a Python StringEditAdapter for this widget, passing ourself as
  // the sole arg.
  auto args = PythonRef::Stolen(Py_BuildValue("(O)", BorrowPyRef()));
  auto result = g_ui_v1->python->objs()
                    .Get(UIV1Python::ObjID::kTextWidgetStringEditAdapterClass)
                    .Call(args);
  if (!result.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error invoking string edit dialog.");
    return;
  }

  // If this new one is already marked replacable, it means it wasn't able
  // to register as the active one, so we can ignore it.
  if (g_base->python->CanPyStringEditAdapterBeReplaced(result.get())) {
    return;
  }

  // Ok looks like we're good; store the adapter and hand it over
  // to whoever will be driving it.
  string_edit_adapter_ = result;

  // Use the platform string-editor if we have one unless the user
  // explicitly wants us to use our own.
  if (g_base->platform->HaveStringEditor()
      && !g_ui_v1->always_use_internal_on_screen_keyboard()) {
    g_base->platform->InvokeStringEditor(string_edit_adapter_.get());
  } else {
    g_ui_v1->python->InvokeStringEditor(string_edit_adapter_.get());
  }
}

void TextWidget::AdapterFinished() {
  BA_PRECONDITION(g_base->InLogicThread());
  string_edit_adapter_.Release();
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
  if (editable() && !ShouldUseStringEditor_()
      && m.type == base::WidgetMessage::Type::kPaste) {
    if (g_base->ClipboardIsSupported()) {
      if (g_base->ClipboardHasText()) {
        // Just enter it char by char as if we had typed it...
        AddCharsToText_(g_base->ClipboardGetText());
      }
    }
  }

  // If we're doing inline editing, handle some key events.
  if (editable() && m.has_keysym && !ShouldUseStringEditor_()) {
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
        if (g_buildconfig.platform_ios_tvos()
            || g_buildconfig.platform_android()) {
          // On mobile, return currently just deselects us.
          g_base->audio->SafePlaySysSound(base::SysSoundID::kSwish);
          parent_widget()->SelectWidget(nullptr);
          return true;
        } else {
          if (auto* call = on_return_press_call_.get()) {
            claimed = true;
            // Schedule this to run immediately after any current UI traversal.
            call->ScheduleInUIOperation();
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
      // Direct text edits come through as seperate events, but we still
      // want to claim key down events here; otherwise they'll do weird
      // stuff like navigate to other widgets.
      claimed = true;
    }
    return claimed;
  }
  switch (m.type) {
    case base::WidgetMessage::Type::kTextInput: {
      if (editable()) {
        if (ShouldUseStringEditor_()) {
          // Normally we shouldn't be getting direct text input events in
          // situations where we're using string editors, but it still might
          // be possible; for instance if a game controller is driving the
          // ui when a key is typed. We simply ignore the event in that case
          // because otherwise the text input would be fighting with the
          // string-editor.
        } else {
          // Apply text directly.
          if (m.sval != nullptr) {
            AddCharsToText_(*m.sval);
            return true;
          }
        }
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseMove: {
      if (!IsSelectable()) {
        return false;
      }
      float x{ScaleAdjustedX_(m.fval1)};
      float y{ScaleAdjustedY_(m.fval2)};
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
      float x{ScaleAdjustedX_(m.fval1)};
      float y{ScaleAdjustedY_(m.fval2)};

      auto click_count = static_cast<int>(m.fval3);

      // See if a click is in our clear button.
      if (editable() && (IsHierarchySelected() || always_show_carat_)
          && !text_raw_.empty() && (x >= width_ - 35)
          && (x < width_ + kClearMargin) && (y > -kClearMargin)
          && (y < height_ + kClearMargin) && implicit_clear_button_
          && allow_clear_button_) {
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
            if (base::KeyboardInput* kb = g_base->input->keyboard_input()) {
              g_base->ui->SetMainUIInputDevice(kb);
            }
          }
          GlobalSelect();
          pressed_ = true;

          // Second click (or first if we want) puts us in
          // potentially-activating-mode.
          pressed_activate_ =
              (click_count == 2 || click_activate_) && !editable_;
          if (click_count == 1) {
            g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
          }
        }
        return true;
      } else {
        return false;
      }
    }
    case base::WidgetMessage::Type::kMouseUp:
    case base::WidgetMessage::Type::kMouseCancel: {
      float x{ScaleAdjustedX_(m.fval1)};
      float y{ScaleAdjustedY_(m.fval2)};
      bool claimed = (m.fval3 > 0.0f);

      if (clear_pressed_ && !claimed && editable()
          && (IsHierarchySelected() || always_show_carat_)
          && (!text_raw_.empty()) && (x >= width_ - 35 - kClearMargin)
          && (x < width_ + kClearMargin) && (y >= 0 - kClearMargin)
          && (y < height_ + kClearMargin)) {
        clear_pressed_ = false;

        if (m.type == base::WidgetMessage::Type::kMouseUp) {
          text_raw_ = "";
          text_translation_dirty_ = true;
          carat_position_ = 0;
          text_group_dirty_ = true;
          g_base->audio->SafePlaySysSound(base::SysSoundID::kTap);
        }

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
          pressed_activate_ = false;
          if (m.type == base::WidgetMessage::Type::kMouseUp) {
            Activate();
          }
        } else if (editable_ && ShouldUseStringEditor_()
                   && (x >= (-left_overlap)) && (x < (width_ + right_overlap))
                   && (y >= (-bottom_overlap)) && (y < (height_ + top_overlap))
                   && !claimed) {
          if (m.type == base::WidgetMessage::Type::kMouseUp) {
            // With dialog-editing, a click/tap brings up our editor.
            InvokeStringEditor_();
          }
        }

        // Pressed buttons always claim mouse-ups/cancels presented to them.
        return true;
      }
      break;
    }
    default:
      break;
  }
  return false;
}

auto TextWidget::ScaleAdjustedX_(float x) -> float {
  // Account for our center_scale_ value.
  float offsx = x - width_ * 0.5f;
  return width_ * 0.5f + offsx / center_scale_;
}

auto TextWidget::ScaleAdjustedY_(float y) -> float {
  // Account for our center_scale_ value.
  float offsy = y - height_ * 0.5f;
  return height_ * 0.5f + offsy / center_scale_;
}

void TextWidget::AddCharsToText_(const std::string& addchars) {
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

void TextWidget::UpdateTranslation_() {
  // Apply subs/resources to get our actual text if need be.
  if (text_translation_dirty_) {
    // We don't run translations on user-editable text.
    if (editable()) {
      text_translated_ = text_raw_;
    } else {
      text_translated_ = g_base->assets->CompileResourceString(text_raw_);
    }
    text_translation_dirty_ = false;
    text_group_dirty_ = true;
  }
}

auto TextWidget::GetTextWidth() -> float {
  UpdateTranslation_();

  // Should we cache this?
  return g_base->text_graphics->GetStringWidth(text_translated_, big_);
}

void TextWidget::OnLanguageChange() { text_translation_dirty_ = true; }

void TextWidget::SetHAlign(HAlign a) {
  if (alignment_h_ != a) {
    text_group_dirty_ = true;
  }
  alignment_h_ = a;
}
void TextWidget::SetVAlign(VAlign a) {
  if (alignment_v_ != a) {
    text_group_dirty_ = true;
  }
  alignment_v_ = a;
}

void TextWidget::SetGlowType(GlowType glow_type) {
  if (glow_type == glow_type_) {
    return;
  }
  glow_type_ = glow_type;
  highlight_dirty_ = true;
}

}  // namespace ballistica::ui_v1
