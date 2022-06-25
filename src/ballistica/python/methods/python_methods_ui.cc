// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_ui.h"

#include "ballistica/app/app.h"
#include "ballistica/app/app_globals.h"
#include "ballistica/game/account.h"
#include "ballistica/game/connection/connection_set.h"
#include "ballistica/game/game.h"
#include "ballistica/input/input.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/ui/root_ui.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/button_widget.h"
#include "ballistica/ui/widget/check_box_widget.h"
#include "ballistica/ui/widget/column_widget.h"
#include "ballistica/ui/widget/h_scroll_widget.h"
#include "ballistica/ui/widget/image_widget.h"
#include "ballistica/ui/widget/root_widget.h"
#include "ballistica/ui/widget/row_widget.h"
#include "ballistica/ui/widget/scroll_widget.h"

#if !BA_HEADLESS_BUILD && !BA_XCODE_NEW_PROJECT
extern "C" void SDL_ericf_focus(void);
#endif

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyButtonWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("buttonwidget");
  PyObject* size_obj = Py_None;
  PyObject* pos_obj = Py_None;
  PyObject* label_obj = Py_None;
  PyObject* parent_obj = Py_None;
  PyObject* edit_obj = Py_None;
  ContainerWidget* parent_widget = nullptr;
  PyObject* on_activate_call_obj = Py_None;
  PyObject* color_obj = Py_None;
  PyObject* down_widget_obj = Py_None;
  Widget* down_widget = nullptr;
  PyObject* up_widget_obj = Py_None;
  Widget* up_widget = nullptr;
  PyObject* left_widget_obj = Py_None;
  Widget* left_widget = nullptr;
  PyObject* right_widget_obj = Py_None;
  Widget* right_widget = nullptr;
  PyObject* texture_obj = Py_None;
  PyObject* tint_texture_obj = Py_None;
  PyObject* text_scale_obj = Py_None;
  PyObject* textcolor_obj = Py_None;
  PyObject* enable_sound_obj = Py_None;
  PyObject* model_transparent_obj = Py_None;
  PyObject* model_opaque_obj = Py_None;
  PyObject* repeat_obj = Py_None;
  PyObject* scale_obj = Py_None;
  PyObject* transition_delay_obj = Py_None;
  PyObject* on_select_call_obj = Py_None;
  PyObject* button_type_obj = Py_None;
  PyObject* extra_touch_border_scale_obj = Py_None;
  PyObject* selectable_obj = Py_None;
  PyObject* show_buffer_top_obj = Py_None;
  PyObject* icon_obj = Py_None;
  PyObject* iconscale_obj = Py_None;
  PyObject* icon_tint_obj = Py_None;
  PyObject* icon_color_obj = Py_None;
  PyObject* autoselect_obj = Py_None;
  PyObject* mask_texture_obj = Py_None;
  PyObject* tint_color_obj = Py_None;
  PyObject* tint2_color_obj = Py_None;
  PyObject* text_flatness_obj = Py_None;
  PyObject* text_res_scale_obj = Py_None;
  PyObject* enabled_obj = Py_None;
  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "on_activate_call",
                                 "label",
                                 "color",
                                 "down_widget",
                                 "up_widget",
                                 "left_widget",
                                 "right_widget",
                                 "texture",
                                 "text_scale",
                                 "textcolor",
                                 "enable_sound",
                                 "model_transparent",
                                 "model_opaque",
                                 "repeat",
                                 "scale",
                                 "transition_delay",
                                 "on_select_call",
                                 "button_type",
                                 "extra_touch_border_scale",
                                 "selectable",
                                 "show_buffer_top",
                                 "icon",
                                 "iconscale",
                                 "icon_tint",
                                 "icon_color",
                                 "autoselect",
                                 "mask_texture",
                                 "tint_texture",
                                 "tint_color",
                                 "tint2_color",
                                 "text_flatness",
                                 "text_res_scale",
                                 "enabled",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &size_obj,
          &pos_obj, &on_activate_call_obj, &label_obj, &color_obj,
          &down_widget_obj, &up_widget_obj, &left_widget_obj, &right_widget_obj,
          &texture_obj, &text_scale_obj, &textcolor_obj, &enable_sound_obj,
          &model_transparent_obj, &model_opaque_obj, &repeat_obj, &scale_obj,
          &transition_delay_obj, &on_select_call_obj, &button_type_obj,
          &extra_touch_border_scale_obj, &selectable_obj, &show_buffer_top_obj,
          &icon_obj, &iconscale_obj, &icon_tint_obj, &icon_color_obj,
          &autoselect_obj, &mask_texture_obj, &tint_texture_obj,
          &tint_color_obj, &tint2_color_obj, &text_flatness_obj,
          &text_res_scale_obj, &enabled_obj))
    return nullptr;

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context docs)",
        PyExcType::kContext);
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<ButtonWidget> b;
  if (edit_obj != Py_None) {
    b = dynamic_cast<ButtonWidget*>(Python::GetPyWidget(edit_obj));
    if (!b.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    b = Object::New<ButtonWidget>();
  }

  // set applicable values  ----------------------------
  if (label_obj != Py_None) {
    b->SetText(Python::GetPyString(label_obj));
  }
  if (on_activate_call_obj != Py_None) {
    b->set_on_activate_call(on_activate_call_obj);
  }

  if (down_widget_obj != Py_None) {
    down_widget = Python::GetPyWidget(down_widget_obj);
    if (!down_widget) {
      throw Exception("Invalid down widget.", PyExcType::kWidgetNotFound);
    }
    b->set_down_widget(down_widget);
  }
  if (up_widget_obj != Py_None) {
    up_widget = Python::GetPyWidget(up_widget_obj);
    if (!up_widget) {
      throw Exception("Invalid up widget.", PyExcType::kWidgetNotFound);
    }
    b->set_up_widget(up_widget);
  }
  if (autoselect_obj != Py_None) {
    b->set_auto_select(Python::GetPyBool(autoselect_obj));
  }
  if (left_widget_obj != Py_None) {
    left_widget = Python::GetPyWidget(left_widget_obj);
    if (!left_widget) {
      throw Exception("Invalid left widget.", PyExcType::kWidgetNotFound);
    }
    b->set_left_widget(left_widget);
  }
  if (right_widget_obj != Py_None) {
    right_widget = Python::GetPyWidget(right_widget_obj);
    if (!right_widget) {
      throw Exception("Invalid right widget.", PyExcType::kWidgetNotFound);
    }
    b->set_right_widget(right_widget);
  }
  if (model_transparent_obj != Py_None) {
    b->SetModelTransparent(Python::GetPyModel(model_transparent_obj));
  }
  if (show_buffer_top_obj != Py_None) {
    b->set_show_buffer_top(Python::GetPyFloat(show_buffer_top_obj));
  }
  if (model_opaque_obj != Py_None) {
    b->SetModelOpaque(Python::GetPyModel(model_opaque_obj));
  }
  if (on_select_call_obj != Py_None) {
    b->SetOnSelectCall(on_select_call_obj);
  }
  if (selectable_obj != Py_None) {
    b->set_selectable(Python::GetPyBool(selectable_obj));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    b->set_width(p.x);
    b->set_height(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    b->set_translate(p.x, p.y);
  }
  if (scale_obj != Py_None) {
    b->set_scale(Python::GetPyFloat(scale_obj));
  }
  if (iconscale_obj != Py_None) {
    b->set_icon_scale(Python::GetPyFloat(iconscale_obj));
  }
  if (icon_tint_obj != Py_None) {
    b->set_icon_tint(Python::GetPyFloat(icon_tint_obj));
  }
  if (icon_color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(icon_color_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or 4 floats for icon_color.",
                      PyExcType::kValue);
    }
    b->set_icon_color(c[0], c[1], c[2], (c.size() > 3) ? c[3] : 1.0f);
  }
  if (extra_touch_border_scale_obj != Py_None) {
    b->set_extra_touch_border_scale(
        Python::GetPyFloat(extra_touch_border_scale_obj));
  }
  if (texture_obj != Py_None) {
    b->SetTexture(Python::GetPyTexture(texture_obj));
  }
  if (mask_texture_obj != Py_None) {
    b->SetMaskTexture(Python::GetPyTexture(mask_texture_obj));
  }
  if (tint_texture_obj != Py_None) {
    b->SetTintTexture(Python::GetPyTexture(tint_texture_obj));
  }
  if (icon_obj != Py_None) {
    b->SetIcon(Python::GetPyTexture(icon_obj));
  }
  if (button_type_obj != Py_None) {
    std::string button_type = Python::GetPyString(button_type_obj);
    if (button_type == "back") {
      b->set_style(ButtonWidget::Style::kBack);
    } else if (button_type == "backSmall") {
      b->set_style(ButtonWidget::Style::kBackSmall);
    } else if (button_type == "regular") {
      b->set_style(ButtonWidget::Style::kRegular);
    } else if (button_type == "square") {
      b->set_style(ButtonWidget::Style::kSquare);
    } else if (button_type == "tab") {
      b->set_style(ButtonWidget::Style::kTab);
    } else {
      throw Exception("Invalid button type: " + button_type + ".",
                      PyExcType::kValue);
    }
  }
  if (repeat_obj != Py_None) {
    b->set_repeat(Python::GetPyBool(repeat_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    b->SetColor(c[0], c[1], c[2]);
  }
  if (textcolor_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(textcolor_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or 4 floats for textcolor.",
                      PyExcType::kValue);
    }
    b->set_text_color(c[0], c[1], c[2], (c.size() > 3) ? c[3] : 1.0f);
  }
  if (tint_color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(tint_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint_color.", PyExcType::kValue);
    }
    b->set_tint_color(c[0], c[1], c[2]);
  }
  if (tint2_color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(tint2_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint2_color.", PyExcType::kValue);
    }
    b->set_tint2_color(c[0], c[1], c[2]);
  }
  if (text_flatness_obj != Py_None) {
    b->set_text_flatness(Python::GetPyFloat(text_flatness_obj));
  }
  if (text_scale_obj != Py_None) {
    b->set_text_scale(Python::GetPyFloat(text_scale_obj));
  }
  if (enable_sound_obj != Py_None) {
    b->set_enable_sound(Python::GetPyBool(enable_sound_obj));
  }
  if (transition_delay_obj != Py_None) {
    // We accept this as seconds; widget takes milliseconds.
#if BA_TEST_BUILD
    g_python->TimeFormatCheck(TimeFormat::kSeconds, transition_delay_obj);
#endif
    b->set_transition_delay(static_cast<millisecs_t>(
        1000.0f * Python::GetPyFloat(transition_delay_obj)));
  }
  if (text_res_scale_obj != Py_None) {
    b->SetTextResScale(Python::GetPyFloat(text_res_scale_obj));
  }
  if (enabled_obj != Py_None) {
    b->set_enabled(Python::GetPyBool(selectable_obj));
  }

  // If making a new widget add it at the end.
  if (edit_obj == Py_None) {
    g_ui->AddWidget(b.get(), parent_widget);
  }

  return b->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyCheckBoxWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("checkboxwidget");
  PyObject* size_obj = Py_None;
  PyObject* pos_obj = Py_None;
  PyObject* text_obj = Py_None;
  PyObject* value_obj = Py_None;
  PyObject* on_value_change_call_obj = Py_None;
  PyObject* on_select_call_obj = Py_None;
  PyObject* scale_obj = Py_None;
  PyObject* is_radio_button_obj = Py_None;
  PyObject* maxwidth_obj = Py_None;
  PyObject* parent_obj = Py_None;
  PyObject* edit_obj = Py_None;
  ContainerWidget* parent_widget = nullptr;
  PyObject* text_scale_obj = Py_None;
  PyObject* textcolor_obj = Py_None;
  PyObject* autoselect_obj = Py_None;
  PyObject* color_obj = Py_None;

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "text",
                                 "value",
                                 "on_value_change_call",
                                 "on_select_call",
                                 "text_scale",
                                 "textcolor",
                                 "scale",
                                 "is_radio_button",
                                 "maxwidth",
                                 "autoselect",
                                 "color",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &size_obj, &pos_obj, &text_obj, &value_obj,
          &on_value_change_call_obj, &on_select_call_obj, &text_scale_obj,
          &textcolor_obj, &scale_obj, &is_radio_button_obj, &maxwidth_obj,
          &autoselect_obj, &color_obj)) {
    return nullptr;
  }

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<CheckBoxWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<CheckBoxWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<CheckBoxWidget>();
  }

  // set applicable values ----------------------------
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetPyBool(autoselect_obj));
  }
  if (text_obj != Py_None) {
    widget->SetText(Python::GetPyString(text_obj));
  }
  if (value_obj != Py_None) {
    widget->SetValue(Python::GetPyBool(value_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() != 3)
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    widget->set_color(c[0], c[1], c[2]);
  }
  if (maxwidth_obj != Py_None) {
    widget->SetMaxWidth(Python::GetPyFloat(maxwidth_obj));
  }
  if (is_radio_button_obj != Py_None) {
    widget->SetIsRadioButton(Python::GetPyBool(is_radio_button_obj));
  }
  if (scale_obj != Py_None) {
    widget->set_scale(Python::GetPyFloat(scale_obj));
  }
  if (on_value_change_call_obj != Py_None) {
    widget->SetOnValueChangeCall(on_value_change_call_obj);
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (text_scale_obj != Py_None) {
    widget->SetTextScale(Python::GetPyFloat(text_scale_obj));
  }
  if (textcolor_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(textcolor_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or 4 float values for textcolor.",
                      PyExcType::kValue);
    }
    if (c.size() == 3) {
      widget->set_text_color(c[0], c[1], c[2], 1.0f);
    } else {
      widget->set_text_color(c[0], c[1], c[2], c[3]);
    }
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui->AddWidget(widget.get(), parent_widget);
  }

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyImageWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("imagewidget");
  PyObject* size_obj = Py_None;
  PyObject* pos_obj = Py_None;
  PyObject* texture_obj = Py_None;
  PyObject* tint_texture_obj = Py_None;
  ContainerWidget* parent_widget = nullptr;
  PyObject* parent_obj = Py_None;
  PyObject* edit_obj = Py_None;
  PyObject* color_obj = Py_None;
  PyObject* tint_color_obj = Py_None;
  PyObject* tint2_color_obj = Py_None;
  PyObject* opacity_obj = Py_None;
  PyObject* model_transparent_obj = Py_None;
  PyObject* model_opaque_obj = Py_None;
  PyObject* has_alpha_channel_obj = Py_None;
  PyObject* transition_delay_obj = Py_None;
  PyObject* draw_controller_obj = Py_None;
  PyObject* tilt_scale_obj = Py_None;
  PyObject* mask_texture_obj = Py_None;
  PyObject* radial_amount_obj = Py_None;

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "color",
                                 "texture",
                                 "opacity",
                                 "model_transparent",
                                 "model_opaque",
                                 "has_alpha_channel",
                                 "tint_texture",
                                 "tint_color",
                                 "transition_delay",
                                 "draw_controller",
                                 "tint2_color",
                                 "tilt_scale",
                                 "mask_texture",
                                 "radial_amount",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &size_obj, &pos_obj, &color_obj, &texture_obj,
          &opacity_obj, &model_transparent_obj, &model_opaque_obj,
          &has_alpha_channel_obj, &tint_texture_obj, &tint_color_obj,
          &transition_delay_obj, &draw_controller_obj, &tint2_color_obj,
          &tilt_scale_obj, &mask_texture_obj, &radial_amount_obj))
    return nullptr;

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<ImageWidget> b;
  if (edit_obj != Py_None) {
    b = dynamic_cast<ImageWidget*>(Python::GetPyWidget(edit_obj));
    if (!b.exists())
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (parent_widget == nullptr) {
      throw Exception("Parent widget nonexistent or not a container.",
                      PyExcType::kWidgetNotFound);
    }
    b = Object::New<ImageWidget>();
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    b->set_width(p.x);
    b->set_height(p.y);
  }
  if (texture_obj != Py_None) {
    b->SetTexture(Python::GetPyTexture(texture_obj));
  }
  if (tint_texture_obj != Py_None) {
    b->SetTintTexture(Python::GetPyTexture(tint_texture_obj));
  }
  if (mask_texture_obj != Py_None) {
    b->SetMaskTexture(Python::GetPyTexture(mask_texture_obj));
  }
  if (model_opaque_obj != Py_None) {
    b->SetModelOpaque(Python::GetPyModel(model_opaque_obj));
  }
  if (model_transparent_obj != Py_None) {
    b->SetModelTransparent(Python::GetPyModel(model_transparent_obj));
  }
  if (draw_controller_obj != Py_None) {
    auto* dcw = Python::GetPyWidget(draw_controller_obj);
    if (!dcw) {
      throw Exception("Invalid or nonexistent draw-controller widget.",
                      PyExcType::kWidgetNotFound);
    }
    b->set_draw_control_parent(dcw);
  }
  if (has_alpha_channel_obj != Py_None) {
    b->set_has_alpha_channel(Python::GetPyBool(has_alpha_channel_obj));
  }
  if (opacity_obj != Py_None) {
    b->set_opacity(Python::GetPyFloat(opacity_obj));
  }
  if (radial_amount_obj != Py_None) {
    b->set_radial_amount(Python::GetPyFloat(radial_amount_obj));
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    b->set_translate(p.x, p.y);
  }
  if (transition_delay_obj != Py_None) {
    // We accept this as seconds; widget takes milliseconds.
#if BA_TEST_BUILD
    g_python->TimeFormatCheck(TimeFormat::kSeconds, transition_delay_obj);
#endif
    b->set_transition_delay(1000.0f * Python::GetPyFloat(transition_delay_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    b->set_color(c[0], c[1], c[2]);
  }
  if (tint_color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(tint_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint_color.", PyExcType::kValue);
    }
    b->set_tint_color(c[0], c[1], c[2]);
  }
  if (tint2_color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(tint2_color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for tint2_color.", PyExcType::kValue);
    }
    b->set_tint2_color(c[0], c[1], c[2]);
  }
  if (tilt_scale_obj != Py_None) {
    b->set_tilt_scale(Python::GetPyFloat(tilt_scale_obj));
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui->AddWidget(b.get(), parent_widget);
  }

  return b->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyColumnWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("columnwidget");

  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* visible_child_obj{Py_None};
  PyObject* single_depth_obj{Py_None};
  PyObject* print_list_exit_instructions_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* left_border_obj{Py_None};
  PyObject* top_border_obj{Py_None};
  PyObject* bottom_border_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};
  PyObject* border_obj{Py_None};
  PyObject* margin_obj{Py_None};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* claims_tab_obj{Py_None};
  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "visible_child",
                                 "single_depth",
                                 "print_list_exit_instructions",
                                 "left_border",
                                 "top_border",
                                 "bottom_border",
                                 "selection_loops_to_parent",
                                 "border",
                                 "margin",
                                 "claims_left_right",
                                 "claims_tab",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &visible_child_obj, &single_depth_obj,
          &print_list_exit_instructions_obj, &left_border_obj, &top_border_obj,
          &bottom_border_obj, &selection_loops_to_parent_obj, &border_obj,
          &margin_obj, &claims_left_right_obj, &claims_tab_obj))
    return nullptr;

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context "
        "docs).",
        PyExcType::kContext);
  }
  // if (!g_game->IsInUIContext()) { BA_LOG_PYTHON_TRACE("ERROR: This should be
  // called within the UI context (see ba.Context docs)");}
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<ColumnWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<ColumnWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<ColumnWidget>();
  }

  // Set applicable values ----------------------------
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (single_depth_obj != Py_None) {
    widget->set_single_depth(Python::GetPyBool(single_depth_obj));
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (left_border_obj != Py_None) {
    widget->set_left_border(Python::GetPyFloat(left_border_obj));
  }
  if (top_border_obj != Py_None) {
    widget->set_top_border(Python::GetPyFloat(top_border_obj));
  }
  if (border_obj != Py_None) {
    widget->set_border(Python::GetPyFloat(border_obj));
  }
  if (margin_obj != Py_None) {
    widget->set_margin(Python::GetPyFloat(margin_obj));
  }
  if (bottom_border_obj != Py_None) {
    widget->set_bottom_border(Python::GetPyFloat(bottom_border_obj));
  }
  if (print_list_exit_instructions_obj != Py_None) {
    widget->set_should_print_list_exit_instructions(
        Python::GetPyBool(print_list_exit_instructions_obj));
  }
  if (background_obj != Py_None) {
    widget->set_background(Python::GetPyBool(background_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(Python::GetPyWidget(selected_child_obj));
  }
  if (visible_child_obj != Py_None) {
    widget->ShowWidget(Python::GetPyWidget(visible_child_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetPyBool(selection_loops_to_parent_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetPyBool(claims_left_right_obj));
  }
  if (claims_tab_obj != Py_None) {
    widget->set_claims_tab(Python::GetPyBool(claims_tab_obj));
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui->AddWidget(widget.get(), parent_widget);
  }

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyContainerWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("containerwidget");
  PyObject* size_obj = Py_None;
  PyObject* pos_obj = Py_None;
  PyObject* background_obj = Py_None;
  PyObject* selected_child_obj = Py_None;
  PyObject* transition_obj = Py_None;
  PyObject* cancel_button_obj = Py_None;
  PyObject* start_button_obj = Py_None;
  PyObject* root_selectable_obj = Py_None;
  PyObject* on_activate_call_obj = Py_None;
  PyObject* claims_left_right_obj = Py_None;
  PyObject* claims_up_down_obj = Py_None;
  PyObject* claims_tab_obj = Py_None;
  PyObject* selection_loops_obj = Py_None;
  PyObject* selection_loops_to_parent_obj = Py_None;
  PyObject* scale_obj = Py_None;
  PyObject* on_outside_click_call_obj = Py_None;
  PyObject* print_list_exit_instructions_obj = Py_None;
  PyObject* single_depth_obj = Py_None;
  PyObject* visible_child_obj = Py_None;
  PyObject* stack_offset_obj = Py_None;
  PyObject* scale_origin_stack_offset_obj = Py_None;
  PyObject* color_obj = Py_None;
  PyObject* on_cancel_call_obj = Py_None;
  PyObject* click_activate_obj = Py_None;
  PyObject* always_highlight_obj = Py_None;
  PyObject* parent_obj = Py_None;
  ContainerWidget* parent_widget;
  PyObject* edit_obj = Py_None;
  PyObject* selectable_obj = Py_None;
  PyObject* toolbar_visibility_obj = Py_None;
  PyObject* on_select_call_obj = Py_None;
  PyObject* claim_outside_clicks_obj = Py_None;

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "transition",
                                 "cancel_button",
                                 "start_button",
                                 "root_selectable",
                                 "on_activate_call",
                                 "claims_left_right",
                                 "claims_tab",
                                 "selection_loops",
                                 "selection_loops_to_parent",
                                 "scale",
                                 "on_outside_click_call",
                                 "single_depth",
                                 "visible_child",
                                 "stack_offset",
                                 "color",
                                 "on_cancel_call",
                                 "print_list_exit_instructions",
                                 "click_activate",
                                 "always_highlight",
                                 "selectable",
                                 "scale_origin_stack_offset",
                                 "toolbar_visibility",
                                 "on_select_call",
                                 "claim_outside_clicks",
                                 "claims_up_down",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &size_obj,
          &pos_obj, &background_obj, &selected_child_obj, &transition_obj,
          &cancel_button_obj, &start_button_obj, &root_selectable_obj,
          &on_activate_call_obj, &claims_left_right_obj, &claims_tab_obj,
          &selection_loops_obj, &selection_loops_to_parent_obj, &scale_obj,
          &on_outside_click_call_obj, &single_depth_obj, &visible_child_obj,
          &stack_offset_obj, &color_obj, &on_cancel_call_obj,
          &print_list_exit_instructions_obj, &click_activate_obj,
          &always_highlight_obj, &selectable_obj,
          &scale_origin_stack_offset_obj, &toolbar_visibility_obj,
          &on_select_call_obj, &claim_outside_clicks_obj,
          &claims_up_down_obj)) {
    return nullptr;
  }

  if (!g_game->IsInUIContext())
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<ContainerWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<ContainerWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    if (parent_obj == Py_None) {
      BA_PRECONDITION(g_ui && g_ui->screen_root_widget() != nullptr);
    }
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<ContainerWidget>();
    g_ui->AddWidget(widget.get(), parent_widget);
  }

  // Set applicable values.
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (on_cancel_call_obj != Py_None) {
    widget->SetOnCancelCall(on_cancel_call_obj);
  }
  if (scale_obj != Py_None) {
    widget->set_scale(Python::GetPyFloat(scale_obj));
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (selectable_obj != Py_None) {
    widget->set_selectable(Python::GetPyBool(selectable_obj));
  }
  if (single_depth_obj != Py_None) {
    widget->set_single_depth(Python::GetPyBool(single_depth_obj));
  }
  if (stack_offset_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(stack_offset_obj);
    widget->set_stack_offset(p.x, p.y);
  }
  if (scale_origin_stack_offset_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(scale_origin_stack_offset_obj);
    widget->SetScaleOriginStackOffset(p.x, p.y);
  }
  if (visible_child_obj != Py_None) {
    widget->ShowWidget(Python::GetPyWidget(visible_child_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() != 3 && c.size() != 4) {
      throw Exception("Expected 3 or floats for color.", PyExcType::kValue);
    }
    if (c.size() == 3) {
      widget->set_color(c[0], c[1], c[2], 1.0f);
    } else {
      widget->set_color(c[0], c[1], c[2], c[3]);
    }
  }

  if (on_activate_call_obj != Py_None) {
    widget->SetOnActivateCall(on_activate_call_obj);
  }

  if (on_outside_click_call_obj != Py_None) {
    widget->SetOnOutsideClickCall(on_outside_click_call_obj);
  }

  if (background_obj != Py_None) {
    widget->set_background(Python::GetPyBool(background_obj));
  }
  if (root_selectable_obj != Py_None) {
    widget->SetRootSelectable(Python::GetPyBool(root_selectable_obj));
  }
  if (selected_child_obj != Py_None) {
    // special case: passing 0 implies deselect
    if (PyLong_Check(selected_child_obj)
        && (PyLong_AsLong(selected_child_obj) == 0)) {
      widget->SelectWidget(nullptr);
    } else {
      widget->SelectWidget(Python::GetPyWidget(selected_child_obj));
    }
  }

  if (transition_obj != Py_None) {
    std::string t = Python::GetPyString(transition_obj);
    if (t == "in_left")
      widget->SetTransition(ContainerWidget::TRANSITION_IN_LEFT);
    else if (t == "in_right")
      widget->SetTransition(ContainerWidget::TRANSITION_IN_RIGHT);
    else if (t == "out_left")
      widget->SetTransition(ContainerWidget::TRANSITION_OUT_LEFT);
    else if (t == "out_right")
      widget->SetTransition(ContainerWidget::TRANSITION_OUT_RIGHT);
    else if (t == "in_scale")
      widget->SetTransition(ContainerWidget::TRANSITION_IN_SCALE);
    else if (t == "out_scale")
      widget->SetTransition(ContainerWidget::TRANSITION_OUT_SCALE);
  }

  if (cancel_button_obj != Py_None) {
    auto* button_widget =
        dynamic_cast<ButtonWidget*>(Python::GetPyWidget(cancel_button_obj));
    if (!button_widget) {
      throw Exception("Invalid cancel_button.", PyExcType::kWidgetNotFound);
    }
    widget->SetCancelButton(button_widget);
  }
  if (start_button_obj != Py_None) {
    auto* button_widget =
        dynamic_cast<ButtonWidget*>(Python::GetPyWidget(start_button_obj));
    if (!button_widget) {
      throw Exception("Invalid start_button.", PyExcType::kWidgetNotFound);
    }
    widget->SetStartButton(button_widget);
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetPyBool(claims_left_right_obj));
  }
  if (claims_up_down_obj != Py_None) {
    widget->set_claims_up_down(Python::GetPyBool(claims_up_down_obj));
  }
  if (claims_tab_obj != Py_None) {
    widget->set_claims_tab(Python::GetPyBool(claims_tab_obj));
  }
  if (selection_loops_obj != Py_None) {
    widget->set_selection_loops(Python::GetPyBool(selection_loops_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetPyBool(selection_loops_to_parent_obj));
  }
  if (print_list_exit_instructions_obj != Py_None) {
    widget->set_should_print_list_exit_instructions(
        Python::GetPyBool(print_list_exit_instructions_obj));
  }
  if (click_activate_obj != Py_None) {
    widget->set_click_activate(Python::GetPyBool(click_activate_obj));
  }
  if (always_highlight_obj != Py_None) {
    widget->set_always_highlight(Python::GetPyBool(always_highlight_obj));
  }
  if (toolbar_visibility_obj != Py_None) {
    Widget::ToolbarVisibility val;
    std::string sval = Python::GetPyString(toolbar_visibility_obj);
    if (sval == "menu_minimal") {
      val = Widget::ToolbarVisibility::kMenuMinimal;
    } else if (sval == "menu_minimal_no_back") {
      val = Widget::ToolbarVisibility::kMenuMinimalNoBack;
    } else if (sval == "menu_full") {
      val = Widget::ToolbarVisibility::kMenuFull;
    } else if (sval == "menu_currency") {
      val = Widget::ToolbarVisibility::kMenuCurrency;
    } else if (sval == "menu_full_root") {
      val = Widget::ToolbarVisibility::kMenuFullRoot;
    } else if (sval == "in_game") {
      val = Widget::ToolbarVisibility::kInGame;
    } else if (sval == "inherit") {
      val = Widget::ToolbarVisibility::kInherit;
    } else {
      throw Exception("Invalid toolbar_visibility: '" + sval + "'.",
                      PyExcType::kValue);
    }
    widget->SetToolbarVisibility(val);
  }
  if (claim_outside_clicks_obj != Py_None) {
    widget->set_claims_outside_clicks(
        Python::GetPyBool(claim_outside_clicks_obj));
  }
  return widget->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyRowWidget(PyObject* /* self */, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("rowwidget");

  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* visible_child_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* claims_tab_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};

  static const char* kwlist[] = {"edit",          "parent",
                                 "size",          "position",
                                 "background",    "selected_child",
                                 "visible_child", "claims_left_right",
                                 "claims_tab",    "selection_loops_to_parent",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOO", const_cast<char**>(kwlist), &edit_obj,
          &parent_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &visible_child_obj, &claims_left_right_obj,
          &claims_tab_obj, &selection_loops_to_parent_obj))
    return nullptr;

  if (!g_game->IsInUIContext())
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);

  // Called within the UI context (see ba.Context docs)");}
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // Grab the edited widget or create a new one.
  Object::Ref<RowWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<RowWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<RowWidget>();
  }

  // Set applicable values.
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }

  if (background_obj != Py_None) {
    widget->set_background(Python::GetPyBool(background_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(Python::GetPyWidget(selected_child_obj));
  }
  if (visible_child_obj != Py_None) {
    widget->ShowWidget(Python::GetPyWidget(visible_child_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetPyBool(claims_left_right_obj));
  }
  if (claims_tab_obj != Py_None) {
    widget->set_claims_tab(Python::GetPyBool(claims_tab_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetPyBool(selection_loops_to_parent_obj));
  }

  // If making a new widget, add it to the parent.
  if (edit_obj == Py_None) {
    g_ui->AddWidget(widget.get(), parent_widget);
  }

  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyScrollWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("scrollwidget");
  PyObject* size_obj{Py_None};
  PyObject* pos_obj{Py_None};
  PyObject* background_obj{Py_None};
  PyObject* selected_child_obj{Py_None};
  PyObject* capture_arrows_obj{Py_None};
  PyObject* on_select_call_obj{Py_None};
  PyObject* parent_obj{Py_None};
  PyObject* edit_obj{Py_None};
  PyObject* center_small_content_obj{Py_None};
  ContainerWidget* parent_widget{};
  PyObject* color_obj{Py_None};
  PyObject* highlight_obj{Py_None};
  PyObject* border_opacity_obj{Py_None};
  PyObject* simple_culling_v_obj{Py_None};
  PyObject* selection_loops_to_parent_obj{Py_None};
  PyObject* claims_left_right_obj{Py_None};
  PyObject* claims_up_down_obj{Py_None};
  PyObject* claims_tab_obj{Py_None};
  PyObject* autoselect_obj{Py_None};

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "capture_arrows",
                                 "on_select_call",
                                 "center_small_content",
                                 "color",
                                 "highlight",
                                 "border_opacity",
                                 "simple_culling_v",
                                 "selection_loops_to_parent",
                                 "claims_left_right",
                                 "claims_up_down",
                                 "claims_tab",
                                 "autoselect",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &capture_arrows_obj, &on_select_call_obj,
          &center_small_content_obj, &color_obj, &highlight_obj,
          &border_opacity_obj, &simple_culling_v_obj,
          &selection_loops_to_parent_obj, &claims_left_right_obj,
          &claims_up_down_obj, &claims_tab_obj, &autoselect_obj))
    return nullptr;

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // Grab the edited widget or create a new one. ---------------------
  Object::Ref<ScrollWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<ScrollWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent edit widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<ScrollWidget>();
  }

  // Set applicable values. ----------------------------
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (highlight_obj != Py_None) {
    widget->set_highlight(Python::GetPyBool(highlight_obj));
  }
  if (border_opacity_obj != Py_None) {
    widget->set_border_opacity(Python::GetPyFloat(border_opacity_obj));
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (center_small_content_obj != Py_None) {
    widget->set_center_small_content(
        Python::GetPyBool(center_small_content_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    widget->set_color(c[0], c[1], c[2]);
  }
  if (capture_arrows_obj != Py_None) {
    widget->set_capture_arrows(Python::GetPyBool(capture_arrows_obj));
  }
  if (background_obj != Py_None) {
    widget->set_background(Python::GetPyBool(background_obj));
  }
  if (simple_culling_v_obj != Py_None) {
    widget->set_simple_culling_v(Python::GetPyFloat(simple_culling_v_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(Python::GetPyWidget(selected_child_obj));
  }
  if (selection_loops_to_parent_obj != Py_None) {
    widget->set_selection_loops_to_parent(
        Python::GetPyBool(selection_loops_to_parent_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetPyBool(claims_left_right_obj));
  }
  if (claims_up_down_obj != Py_None) {
    widget->set_claims_up_down(Python::GetPyBool(claims_up_down_obj));
  }
  if (claims_tab_obj != Py_None) {
    widget->set_claims_tab(Python::GetPyBool(claims_tab_obj));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetPyBool(autoselect_obj));
  }

  // If making a new widget add it at the end.
  if (edit_obj == Py_None) {
    g_ui->AddWidget(widget.get(), parent_widget);
  }
  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyHScrollWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("hscrollwidget");

  PyObject* size_obj = Py_None;
  PyObject* pos_obj = Py_None;
  PyObject* background_obj = Py_None;
  PyObject* selected_child_obj = Py_None;
  PyObject* capture_arrows_obj = Py_None;
  PyObject* on_select_call_obj = Py_None;
  PyObject* parent_obj = Py_None;
  PyObject* edit_obj = Py_None;
  PyObject* center_small_content_obj = Py_None;
  ContainerWidget* parent_widget = nullptr;
  PyObject* color_obj = Py_None;
  PyObject* highlight_obj = Py_None;
  PyObject* border_opacity_obj = Py_None;
  PyObject* simple_culling_h_obj = Py_None;
  PyObject* claims_left_right_obj = Py_None;
  PyObject* claims_up_down_obj = Py_None;
  PyObject* claims_tab_obj = Py_None;
  PyObject* autoselect_obj = Py_None;

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "background",
                                 "selected_child",
                                 "capture_arrows",
                                 "on_select_call",
                                 "center_small_content",
                                 "color",
                                 "highlight",
                                 "border_opacity",
                                 "simple_culling_h",
                                 "claims_left_right",
                                 "claims_up_down",
                                 "claims_tab",
                                 "autoselect",
                                 nullptr};

  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOO", const_cast<char**>(kwlist),
          &edit_obj, &parent_obj, &size_obj, &pos_obj, &background_obj,
          &selected_child_obj, &capture_arrows_obj, &on_select_call_obj,
          &center_small_content_obj, &color_obj, &highlight_obj,
          &border_opacity_obj, &simple_culling_h_obj, &claims_left_right_obj,
          &claims_up_down_obj, &claims_tab_obj, &autoselect_obj))
    return nullptr;

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<HScrollWidget> widget;
  if (edit_obj != Py_None) {
    widget = dynamic_cast<HScrollWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent edit widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<HScrollWidget>();
  }

  // set applicable values ----------------------------
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (highlight_obj != Py_None) {
    widget->set_highlight(Python::GetPyBool(highlight_obj));
  }
  if (border_opacity_obj != Py_None) {
    widget->setBorderOpacity(Python::GetPyFloat(border_opacity_obj));
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (center_small_content_obj != Py_None) {
    widget->SetCenterSmallContent(Python::GetPyBool(center_small_content_obj));
  }
  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() != 3) {
      throw Exception("Expected 3 floats for color.", PyExcType::kValue);
    }
    widget->setColor(c[0], c[1], c[2]);
  }
  if (capture_arrows_obj != Py_None) {
    widget->set_capture_arrows(Python::GetPyBool(capture_arrows_obj));
  }
  if (background_obj != Py_None) {
    widget->set_background(Python::GetPyBool(background_obj));
  }
  if (simple_culling_h_obj != Py_None) {
    widget->set_simple_culling_h(Python::GetPyFloat(simple_culling_h_obj));
  }
  if (selected_child_obj != Py_None) {
    widget->SelectWidget(Python::GetPyWidget(selected_child_obj));
  }
  if (claims_left_right_obj != Py_None) {
    widget->set_claims_left_right(Python::GetPyBool(claims_left_right_obj));
  }
  if (claims_up_down_obj != Py_None) {
    widget->set_claims_up_down(Python::GetPyBool(claims_up_down_obj));
  }
  if (claims_tab_obj != Py_None) {
    widget->set_claims_tab(Python::GetPyBool(claims_tab_obj));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetPyBool(autoselect_obj));
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui->AddWidget(widget.get(), parent_widget);
  }
  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyTextWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("textwidget");
  PyObject* size_obj = Py_None;
  PyObject* pos_obj = Py_None;
  PyObject* text_obj = Py_None;
  PyObject* v_align_obj = Py_None;
  PyObject* h_align_obj = Py_None;
  PyObject* editable_obj = Py_None;
  PyObject* padding_obj = Py_None;
  PyObject* on_return_press_call_obj = Py_None;
  PyObject* on_activate_call_obj = Py_None;
  PyObject* selectable_obj = Py_None;
  PyObject* max_chars_obj = Py_None;
  PyObject* color_obj = Py_None;
  PyObject* click_activate_obj = Py_None;
  PyObject* on_select_call_obj = Py_None;
  PyObject* maxwidth_obj = Py_None;
  PyObject* max_height_obj = Py_None;
  PyObject* scale_obj = Py_None;
  PyObject* corner_scale_obj = Py_None;
  PyObject* always_highlight_obj = Py_None;
  PyObject* draw_controller_obj = Py_None;
  PyObject* description_obj = Py_None;
  PyObject* transition_delay_obj = Py_None;
  PyObject* flatness_obj = Py_None;
  PyObject* shadow_obj = Py_None;
  PyObject* big_obj = Py_None;
  PyObject* parent_obj = Py_None;
  ContainerWidget* parent_widget = nullptr;
  PyObject* edit_obj = Py_None;
  PyObject* query_obj = Py_None;
  PyObject* autoselect_obj = Py_None;
  PyObject* rotate_obj = Py_None;
  PyObject* enabled_obj = Py_None;
  PyObject* force_internal_editing_obj = Py_None;
  PyObject* always_show_carat_obj = Py_None;
  PyObject* extra_touch_border_scale_obj = Py_None;
  PyObject* res_scale_obj = Py_None;

  static const char* kwlist[] = {"edit",
                                 "parent",
                                 "size",
                                 "position",
                                 "text",
                                 "v_align",
                                 "h_align",
                                 "editable",
                                 "padding",
                                 "on_return_press_call",
                                 "on_activate_call",
                                 "selectable",
                                 "query",
                                 "max_chars",
                                 "color",
                                 "click_activate",
                                 "on_select_call",
                                 "always_highlight",
                                 "draw_controller",
                                 "scale",
                                 "corner_scale",
                                 "description",
                                 "transition_delay",
                                 "maxwidth",
                                 "max_height",
                                 "flatness",
                                 "shadow",
                                 "autoselect",
                                 "rotate",
                                 "enabled",
                                 "force_internal_editing",
                                 "always_show_carat",
                                 "big",
                                 "extra_touch_border_scale",
                                 "res_scale",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "|OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
          const_cast<char**>(kwlist), &edit_obj, &parent_obj, &size_obj,
          &pos_obj, &text_obj, &v_align_obj, &h_align_obj, &editable_obj,
          &padding_obj, &on_return_press_call_obj, &on_activate_call_obj,
          &selectable_obj, &query_obj, &max_chars_obj, &color_obj,
          &click_activate_obj, &on_select_call_obj, &always_highlight_obj,
          &draw_controller_obj, &scale_obj, &corner_scale_obj, &description_obj,
          &transition_delay_obj, &maxwidth_obj, &max_height_obj, &flatness_obj,
          &shadow_obj, &autoselect_obj, &rotate_obj, &enabled_obj,
          &force_internal_editing_obj, &always_show_carat_obj, &big_obj,
          &extra_touch_border_scale_obj, &res_scale_obj))
    return nullptr;

  if (!g_game->IsInUIContext())
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  // if (!g_game->IsInUIContext()) { BA_LOG_PYTHON_TRACE("ERROR: This should be
  // called within the UI context (see ba.Context docs)");}
  ScopedSetContext cp(g_game->GetUIContextTarget());

  // grab the edited widget or create a new one ---------------------
  Object::Ref<TextWidget> widget;
  if (query_obj != Py_None) {
    widget = dynamic_cast<TextWidget*>(Python::GetPyWidget(query_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
    return PyUnicode_FromString(widget->text_raw().c_str());
  }
  if (edit_obj != Py_None) {
    widget = dynamic_cast<TextWidget*>(Python::GetPyWidget(edit_obj));
    if (!widget.exists()) {
      throw Exception("Invalid or nonexistent widget.",
                      PyExcType::kWidgetNotFound);
    }
  } else {
    parent_widget =
        parent_obj == Py_None
            ? g_ui->screen_root_widget()
            : dynamic_cast<ContainerWidget*>(Python::GetPyWidget(parent_obj));
    if (!parent_widget) {
      throw Exception("Invalid or nonexistent parent widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget = Object::New<TextWidget>();
  }

  // Set applicable values ----------------------------
  if (max_chars_obj != Py_None) {
    widget->set_max_chars(
        static_cast_check_fit<int>(Python::GetPyInt64(max_chars_obj)));
  }
  if (size_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(size_obj);
    widget->SetWidth(p.x);
    widget->SetHeight(p.y);
  }
  if (description_obj != Py_None) {
    // FIXME - compiling Lstr values to flat strings before passing them in;
    // we should probably extend TextWidget to handle this internally, but
    // punting on that for now..
    widget->set_description(g_game->CompileResourceString(
        Python::GetPyString(description_obj), "textwidget set desc"));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetPyBool(autoselect_obj));
  }
  if (transition_delay_obj != Py_None) {
    // we accept this as seconds; widget takes milliseconds
#if BA_TEST_BUILD
    g_python->TimeFormatCheck(TimeFormat::kSeconds, transition_delay_obj);
#endif
    widget->set_transition_delay(1000.0f
                                 * Python::GetPyFloat(transition_delay_obj));
  }
  if (enabled_obj != Py_None) {
    widget->SetEnabled(Python::GetPyBool(enabled_obj));
  }
  if (always_show_carat_obj != Py_None) {
    widget->set_always_show_carat(Python::GetPyBool(always_show_carat_obj));
  }
  if (big_obj != Py_None) {
    widget->SetBig(Python::GetPyBool(big_obj));
  }
  if (force_internal_editing_obj != Py_None) {
    widget->set_force_internal_editing(
        Python::GetPyBool(force_internal_editing_obj));
  }
  if (pos_obj != Py_None) {
    Point2D p = Python::GetPyPoint2D(pos_obj);
    widget->set_translate(p.x, p.y);
  }
  if (flatness_obj != Py_None) {
    widget->set_flatness(Python::GetPyFloat(flatness_obj));
  }
  if (rotate_obj != Py_None) {
    widget->set_rotate(Python::GetPyFloat(rotate_obj));
  }
  if (shadow_obj != Py_None) {
    widget->set_shadow(Python::GetPyFloat(shadow_obj));
  }
  if (maxwidth_obj != Py_None) {
    widget->set_max_width(Python::GetPyFloat(maxwidth_obj));
  }
  if (max_height_obj != Py_None) {
    widget->set_max_height(Python::GetPyFloat(max_height_obj));
  }
  // note: need to make sure to set this before settings text
  // (influences whether we look for json strings or not)
  if (editable_obj != Py_None) {
    widget->SetEditable(Python::GetPyBool(editable_obj));
  }

  if (text_obj != Py_None) {
    widget->SetText(Python::GetPyString(text_obj));
  }
  if (h_align_obj != Py_None) {
    std::string halign = Python::GetPyString(h_align_obj);
    if (halign == "left") {
      widget->set_halign(TextWidget::HAlign::kLeft);
    } else if (halign == "center") {
      widget->set_halign(TextWidget::HAlign::kCenter);
    } else if (halign == "right") {
      widget->set_halign(TextWidget::HAlign::kRight);
    } else {
      throw Exception("Invalid halign.", PyExcType::kValue);
    }
  }
  if (v_align_obj != Py_None) {
    std::string valign = Python::GetPyString(v_align_obj);
    if (valign == "top") {
      widget->set_valign(TextWidget::VAlign::kTop);
    } else if (valign == "center") {
      widget->set_valign(TextWidget::VAlign::kCenter);
    } else if (valign == "bottom") {
      widget->set_valign(TextWidget::VAlign::kBottom);
    } else {
      throw Exception("Invalid valign.", PyExcType::kValue);
    }
  }
  if (always_highlight_obj != Py_None) {
    widget->set_always_highlight(Python::GetPyBool(always_highlight_obj));
  }
  if (padding_obj != Py_None) {
    widget->set_padding(Python::GetPyFloat(padding_obj));
  }
  if (scale_obj != Py_None) {
    widget->set_center_scale(Python::GetPyFloat(scale_obj));
  }
  // *normal* widget scale.. we currently plug 'scale' into 'centerScale'.  ew.
  if (corner_scale_obj != Py_None) {
    widget->set_scale(Python::GetPyFloat(corner_scale_obj));
  }
  if (draw_controller_obj != Py_None) {
    auto* dcw = Python::GetPyWidget(draw_controller_obj);
    if (!dcw) {
      throw Exception("Invalid or nonexistent draw-controller widget.",
                      PyExcType::kWidgetNotFound);
    }
    widget->set_draw_control_parent(dcw);
  }
  if (on_return_press_call_obj != Py_None) {
    widget->set_on_return_press_call(on_return_press_call_obj);
  }
  if (on_select_call_obj != Py_None) {
    widget->SetOnSelectCall(on_select_call_obj);
  }
  if (on_activate_call_obj != Py_None) {
    widget->set_on_activate_call(on_activate_call_obj);
  }
  if (selectable_obj != Py_None)
    widget->set_selectable(Python::GetPyBool(selectable_obj));

  if (color_obj != Py_None) {
    std::vector<float> c = Python::GetPyFloats(color_obj);
    if (c.size() == 3) {
      widget->set_color(c[0], c[1], c[2], 1.0f);
    } else if (c.size() == 4) {
      widget->set_color(c[0], c[1], c[2], c[3]);
    } else {
      throw Exception("Expected 3 or 4 floats for color.", PyExcType::kValue);
    }
  }
  if (click_activate_obj != Py_None) {
    widget->set_click_activate(Python::GetPyBool(click_activate_obj));
  }
  if (extra_touch_border_scale_obj != Py_None) {
    widget->set_extra_touch_border_scale(
        Python::GetPyFloat(extra_touch_border_scale_obj));
  }
  if (res_scale_obj != Py_None) {
    widget->set_res_scale(Python::GetPyFloat(res_scale_obj));
  }

  // if making a new widget add it at the end
  if (edit_obj == Py_None) {
    g_ui->AddWidget(widget.get(), parent_widget);
  }
  return widget->NewPyRef();

  BA_PYTHON_CATCH;
}

auto PyWidgetCall(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("widget");

  PyObject* edit_obj = Py_None;
  PyObject* down_widget_obj = Py_None;
  PyObject* up_widget_obj = Py_None;
  PyObject* left_widget_obj = Py_None;
  PyObject* right_widget_obj = Py_None;
  PyObject* show_buffer_top_obj = Py_None;
  PyObject* show_buffer_bottom_obj = Py_None;
  PyObject* show_buffer_left_obj = Py_None;
  PyObject* show_buffer_right_obj = Py_None;
  PyObject* autoselect_obj = Py_None;

  static const char* kwlist[] = {"edit",
                                 "up_widget",
                                 "down_widget",
                                 "left_widget",
                                 "right_widget",
                                 "show_buffer_top",
                                 "show_buffer_bottom",
                                 "show_buffer_left",
                                 "show_buffer_right",
                                 "autoselect",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O|OOOOOOOOO", const_cast<char**>(kwlist), &edit_obj,
          &up_widget_obj, &down_widget_obj, &left_widget_obj, &right_widget_obj,
          &show_buffer_top_obj, &show_buffer_bottom_obj, &show_buffer_left_obj,
          &show_buffer_right_obj, &autoselect_obj))
    return nullptr;

  if (!g_game->IsInUIContext()) {
    throw Exception(
        "This must be called within the UI context (see ba.Context docs).",
        PyExcType::kContext);
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());

  Widget* widget = nullptr;
  if (edit_obj != Py_None) {
    widget = Python::GetPyWidget(edit_obj);
  }
  if (!widget)
    throw Exception("Invalid or nonexistent widget passed.",
                    PyExcType::kWidgetNotFound);

  if (down_widget_obj != Py_None) {
    Widget* down_widget = Python::GetPyWidget(down_widget_obj);
    if (!down_widget) {
      throw Exception("Invalid down widget.", PyExcType::kWidgetNotFound);
    }
    widget->set_down_widget(down_widget);
  }
  if (up_widget_obj != Py_None) {
    Widget* up_widget = Python::GetPyWidget(up_widget_obj);
    if (!up_widget) {
      throw Exception("Invalid up widget.", PyExcType::kWidgetNotFound);
    }
    widget->set_up_widget(up_widget);
  }
  if (left_widget_obj != Py_None) {
    Widget* left_widget = Python::GetPyWidget(left_widget_obj);
    if (!left_widget) {
      throw Exception("Invalid left widget.", PyExcType::kWidgetNotFound);
    }
    widget->set_left_widget(left_widget);
  }
  if (right_widget_obj != Py_None) {
    Widget* right_widget = Python::GetPyWidget(right_widget_obj);
    if (!right_widget) {
      throw Exception("Invalid right widget.", PyExcType::kWidgetNotFound);
    }
    widget->set_right_widget(right_widget);
  }
  if (show_buffer_top_obj != Py_None) {
    widget->set_show_buffer_top(Python::GetPyFloat(show_buffer_top_obj));
  }
  if (show_buffer_bottom_obj != Py_None) {
    widget->set_show_buffer_bottom(Python::GetPyFloat(show_buffer_bottom_obj));
  }
  if (show_buffer_left_obj != Py_None) {
    widget->set_show_buffer_left(Python::GetPyFloat(show_buffer_left_obj));
  }
  if (show_buffer_right_obj != Py_None) {
    widget->set_show_buffer_right(Python::GetPyFloat(show_buffer_right_obj));
  }
  if (autoselect_obj != Py_None) {
    widget->set_auto_select(Python::GetPyBool(autoselect_obj));
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyUIBounds(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("uibounds");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  assert(g_graphics);
  // note: to be safe, we return our min guaranteed screen bounds; not our
  // current (which can be bigger)
  float x = 0.5f * kBaseVirtualResX;
  float virtual_res_y = kBaseVirtualResY;
  float y = 0.5f * virtual_res_y;
  return Py_BuildValue("(ffff)", -x, x, -y, y);
  BA_PYTHON_CATCH;
}

auto PyFocusWindow(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("focuswindow");

  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  assert(InGameThread());
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && !BA_HEADLESS_BUILD \
    && !BA_XCODE_NEW_PROJECT
  SDL_ericf_focus();
#else
#endif
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyShowOnlineScoreUI(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("show_online_score_ui");
  const char* show = "general";
  PyObject* game_obj = Py_None;
  PyObject* game_version_obj = Py_None;
  static const char* kwlist[] = {"show", "game", "game_version", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|sOO",
                                   const_cast<char**>(kwlist), &show, &game_obj,
                                   &game_version_obj)) {
    return nullptr;
  }
  std::string game;
  if (game_obj != Py_None) {
    game = Python::GetPyString(game_obj);
  }
  std::string game_version;
  if (game_version_obj != Py_None) {
    game_version = Python::GetPyString(game_version_obj);
  }
  g_app->PushShowOnlineScoreUICall(show, game, game_version);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyFadeScreen(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("fade_screen");

  // This can only be called in the UI context.
  int fade = 0;
  float time = 0.25;
  PyObject* endcall = nullptr;
  static const char* kwlist[] = {"to", "time", "endcall", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|pfO",
                                   const_cast<char**>(kwlist), &fade, &time,
                                   &endcall)) {
    return nullptr;
  }
  g_graphics->FadeScreen(static_cast<bool>(fade),
                         static_cast<int>(1000.0f * time), endcall);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyShowAd(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("show_ad");
  BA_PRECONDITION(InGameThread());
  const char* purpose;
  PyObject* on_completion_call_obj = Py_None;
  int pass_actually_showed = false;
  static const char* kwlist[] = {"purpose", "on_completion_call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|O", const_cast<char**>(kwlist), &purpose,
          &on_completion_call_obj, &pass_actually_showed)) {
    return nullptr;
  }
  AppInternalSetAdCompletionCall(on_completion_call_obj,
                                 static_cast<bool>(pass_actually_showed));

  // In cases where we support ads, store our callback and kick one off.
  // We'll then fire our callback once its done.
  // If we *don't* support ads, just store our callback and then kick off
  // an ad-view-complete message ourself so the event flow is similar..
  if (g_platform->GetHasAds()) {
    g_platform->ShowAd(purpose);
  } else {
    AppInternalPushAdViewComplete(purpose, false);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

// (same as PyShowAd but passes actually_showed arg in callback)
auto PyShowAd2(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("show_ad_2");
  BA_PRECONDITION(InGameThread());
  const char* purpose;
  PyObject* on_completion_call_obj = Py_None;
  int pass_actually_showed = true;
  static const char* kwlist[] = {"purpose", "on_completion_call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|O", const_cast<char**>(kwlist), &purpose,
          &on_completion_call_obj, &pass_actually_showed)) {
    return nullptr;
  }
  AppInternalSetAdCompletionCall(on_completion_call_obj,
                                 static_cast<bool>(pass_actually_showed));

  // In cases where we support ads, store our callback and kick one off.
  // We'll then fire our callback once its done.
  // If we *don't* support ads, just store our callback and then kick off
  // an ad-view-complete message ourself so the event flow is similar..
  if (g_platform->GetHasAds()) {
    g_platform->ShowAd(purpose);
  } else {
    AppInternalPushAdViewComplete(purpose, false);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyShowAppInvite(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("show_app_invite");
  std::string title;
  std::string message;
  std::string code;
  PyObject* title_obj;
  PyObject* message_obj;
  PyObject* code_obj;
  static const char* kwlist[] = {"title", "message", "code", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOO",
                                   const_cast<char**>(kwlist), &title_obj,
                                   &message_obj, &code_obj)) {
    return nullptr;
  }
  title = Python::GetPyString(title_obj);
  message = Python::GetPyString(message_obj);
  code = Python::GetPyString(code_obj);
  g_platform->AndroidShowAppInvite(title, message, code);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyShowProgressBar(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("show_progress_bar");

  g_graphics->EnableProgressBar(false);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPartyIconAlwaysVisible(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("set_party_icon_always_visible");

  int value;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }
  assert(g_input);
  g_ui->root_ui()->set_always_draw_party_icon(static_cast<bool>(value));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyChatMessage(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("chat_message");
  std::string message;
  PyObject* message_obj;
  PyObject* clients_obj = Py_None;
  PyObject* sender_override_obj = Py_None;
  std::string sender_override;
  const std::string* sender_override_p{};
  std::vector<int> clients;
  std::vector<int>* clients_p{};

  static const char* kwlist[] = {"message", "clients", "sender_override",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|OO",
                                   const_cast<char**>(kwlist), &message_obj,
                                   &clients_obj, &sender_override_obj)) {
    return nullptr;
  }
  message = Python::GetPyString(message_obj);
  if (sender_override_obj != Py_None) {
    sender_override = Python::GetPyString(sender_override_obj);
    sender_override_p = &sender_override;
  }

  if (clients_obj != Py_None) {
    clients = Python::GetPyInts(clients_obj);
    clients_p = &clients;
  }
  g_game->connections()->SendChatMessage(message, clients_p, sender_override_p);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetChatMessages(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("get_chat_messages");

  BA_PRECONDITION(InGameThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  PyObject* py_list = PyList_New(0);
  for (auto&& i : g_game->chat_messages()) {
    PyList_Append(py_list, PyUnicode_FromString(i.c_str()));
  }
  return py_list;
  BA_PYTHON_CATCH;
}

auto PySetPartyWindowOpen(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_party_window_open");
  int value;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }
  assert(g_input);
  g_ui->root_ui()->set_party_window_open(static_cast<bool>(value));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetSpecialWidget(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("get_special_widget");

  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  RootWidget* root_widget = g_ui->root_widget();
  assert(root_widget);
  Widget* w = root_widget->GetSpecialWidget(name);
  if (w == nullptr) {
    throw Exception("Invalid special widget name '" + std::string(name) + "'.",
                    PyExcType::kValue);
  }
  return w->NewPyRef();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

// returns an extra hash value that can be incorporated into security checks;
// this contains things like whether console commands have been run, etc.
auto PyHaveIncentivizedAd(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("have_incentivized_ad");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (g_app_globals->have_incentivized_ad) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

// this returns whether it makes sense to show an currently
auto PyCanShowAd(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("can_show_ad");

  BA_PRECONDITION(InGameThread());
  // if we've got any network connections, no ads..
  // (don't want to make someone on the other end wait or risk disconnecting
  // them or whatnot) also disallow ads if remote apps are connected; at least
  // on android ads pause our activity which disconnects the remote app.. (could
  // potentially still allow on other platforms; should verify..)
  if (g_game->connections()->connection_to_host()
      || g_game->connections()->has_connection_to_clients()
      || g_input->HaveRemoteAppController()) {
    Py_RETURN_FALSE;
  }
  Py_RETURN_TRUE;  // all systems go..
  BA_PYTHON_CATCH;
}

auto PyHasVideoAds(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("has_video_ads");
  if (g_platform->GetHasVideoAds()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyBackPress(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("back_press");

  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_input->HandleBackPress(true);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyOpenURL(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("open_url");
  const char* address = nullptr;
  static const char* kwlist[] = {"address", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &address)) {
    return nullptr;
  }
  assert(g_app);
  g_app->PushOpenURLCall(address);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyOpenFileExternally(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("open_file_externally");

  char* path = nullptr;
  static const char* kwlist[] = {"path", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &path)) {
    return nullptr;
  }
  g_platform->OpenFileExternally(path);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyOpenDirExternally(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("open_dir_externally");
  char* path = nullptr;
  static const char* kwlist[] = {"path", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &path)) {
    return nullptr;
  }
  g_platform->OpenDirExternally(path);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyConsolePrint(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;

  Platform::SetLastPyCall("console_print");

#if !BA_HEADLESS_BUILD
  Py_ssize_t tuple_size = PyTuple_GET_SIZE(args);
  PyObject* obj;
  for (Py_ssize_t i = 0; i < tuple_size; i++) {
    obj = PyTuple_GET_ITEM(args, i);
    PyObject* str_obj = PyObject_Str(obj);
    if (!str_obj) {
      PyErr_Clear();  // In case this is caught without setting the py exc.
      throw Exception();
    }
    const char* c = PyUnicode_AsUTF8(str_obj);
    g_game->PushConsolePrintCall(c);
    Py_DECREF(str_obj);
  }
#endif  // !BA_HEADLESS_BUILD
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIsPartyIconVisible(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  Platform::SetLastPyCall("is_party_icon_visible");
  BA_PYTHON_TRY;
  bool party_button_active =
      (g_game->connections()->GetConnectedClientCount() > 0
       || g_game->connections()->connection_to_host()
       || g_ui->root_ui()->always_draw_party_icon());
  if (party_button_active) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonMethodsUI::GetMethods() -> std::vector<PyMethodDef> {
  return {
      {"is_party_icon_visible", (PyCFunction)PyIsPartyIconVisible,
       METH_VARARGS | METH_KEYWORDS,
       "is_party_icon_visible() -> bool\n"
       "\n"
       "(internal)"},

      {"console_print", PyConsolePrint, METH_VARARGS,
       "console_print(*args: Any) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Print the provided args to the game console (using str()).\n"
       "For most debugging/info purposes you should just use Python's "
       "standard\n"
       "print, which will show up in the game console as well."},

      {"open_dir_externally", (PyCFunction)PyOpenDirExternally,
       METH_VARARGS | METH_KEYWORDS,
       "open_dir_externally(path: str) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Open the provided dir in the default external app."},

      {"open_file_externally", (PyCFunction)PyOpenFileExternally,
       METH_VARARGS | METH_KEYWORDS,
       "open_file_externally(path: str) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Open the provided file in the default external app."},

      {"open_url", (PyCFunction)PyOpenURL, METH_VARARGS | METH_KEYWORDS,
       "open_url(address: str) -> None\n"
       "\n"
       "Open a provided URL.\n"
       "\n"
       "Category: **General Utility Functions**\n"
       "\n"
       "Open the provided url in a web-browser, or display the URL\n"
       "string in a window if that isn't possible.\n"},

      {"back_press", (PyCFunction)PyBackPress, METH_VARARGS | METH_KEYWORDS,
       "back_press() -> None\n"
       "\n"
       "(internal)"},

      {"has_video_ads", (PyCFunction)PyHasVideoAds,
       METH_VARARGS | METH_KEYWORDS,
       "has_video_ads() -> bool\n"
       "\n"
       "(internal)"},

      {"can_show_ad", (PyCFunction)PyCanShowAd, METH_VARARGS | METH_KEYWORDS,
       "can_show_ad() -> bool\n"
       "\n"
       "(internal)"},

      {"have_incentivized_ad", (PyCFunction)PyHaveIncentivizedAd,
       METH_VARARGS | METH_KEYWORDS,
       "have_incentivized_ad() -> bool\n"
       "\n"
       "(internal)"},

      {"get_special_widget", (PyCFunction)PyGetSpecialWidget,
       METH_VARARGS | METH_KEYWORDS,
       "get_special_widget(name: str) -> Widget\n"
       "\n"
       "(internal)"},

      {"set_party_window_open", (PyCFunction)PySetPartyWindowOpen,
       METH_VARARGS | METH_KEYWORDS,
       "set_party_window_open(value: bool) -> None\n"
       "\n"
       "(internal)"},

      {"get_chat_messages", (PyCFunction)PyGetChatMessages,
       METH_VARARGS | METH_KEYWORDS,
       "get_chat_messages() -> list[str]\n"
       "\n"
       "(internal)"},

      {"chatmessage", (PyCFunction)PyChatMessage, METH_VARARGS | METH_KEYWORDS,
       "chatmessage(message: str | ba.Lstr,\n"
       "  clients: Sequence[int] | None = None,\n"
       "  sender_override: str | None = None) -> None\n"
       "\n"
       "(internal)"},

      {"set_party_icon_always_visible",
       (PyCFunction)PySetPartyIconAlwaysVisible, METH_VARARGS | METH_KEYWORDS,
       "set_party_icon_always_visible(value: bool) -> None\n"
       "\n"
       "(internal)"},

      {"show_progress_bar", (PyCFunction)PyShowProgressBar,
       METH_VARARGS | METH_KEYWORDS,
       "show_progress_bar() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: **General Utility Functions**"},

      {"show_app_invite", (PyCFunction)PyShowAppInvite,
       METH_VARARGS | METH_KEYWORDS,
       "show_app_invite(title: str | ba.Lstr,\n"
       "  message: str | ba.Lstr,\n"
       "  code: str) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: **General Utility Functions**"},

      {"show_ad", (PyCFunction)PyShowAd, METH_VARARGS | METH_KEYWORDS,
       "show_ad(purpose: str,\n"
       "  on_completion_call: Callable[[], None] | None = None)\n"
       " -> None\n"
       "\n"
       "(internal)"},

      {"show_ad_2", (PyCFunction)PyShowAd2, METH_VARARGS | METH_KEYWORDS,
       "show_ad_2(purpose: str,\n"
       " on_completion_call: Callable[[bool], None] | None = None)\n"
       " -> None\n"
       "\n"
       "(internal)"},

      {"fade_screen", (PyCFunction)PyFadeScreen, METH_VARARGS | METH_KEYWORDS,
       "fade_screen(to: int = 0, time: float = 0.25,\n"
       "  endcall: Callable[[], None] | None = None) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Fade the local game screen in our out from black over a duration of\n"
       "time. if \"to\" is 0, the screen will fade out to black.  Otherwise "
       "it\n"
       "will fade in from black. If endcall is provided, it will be run after "
       "a\n"
       "completely faded frame is drawn."},

      {"show_online_score_ui", (PyCFunction)PyShowOnlineScoreUI,
       METH_VARARGS | METH_KEYWORDS,
       "show_online_score_ui(show: str = 'general', game: str | None = None,\n"
       "  game_version: str | None = None) -> None\n"
       "\n"
       "(internal)"},

      {"focus_window", (PyCFunction)PyFocusWindow, METH_VARARGS | METH_KEYWORDS,
       "focus_window() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "A workaround for some unintentional backgrounding that occurs on mac"},

      {"uibounds", (PyCFunction)PyUIBounds, METH_VARARGS | METH_KEYWORDS,
       "uibounds() -> tuple[float, float, float, float]\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns a tuple of 4 values: (x-min, x-max, y-min, y-max) "
       "representing\n"
       "the range of values that can be plugged into a root level\n"
       "ba.ContainerWidget's stack_offset value while guaranteeing that its\n"
       "center remains onscreen.\n"},

      {"buttonwidget", (PyCFunction)PyButtonWidget,
       METH_VARARGS | METH_KEYWORDS,
       "buttonwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  on_activate_call: Callable | None = None,\n"
       "  label: str | ba.Lstr | None = None,\n"
       "  color: Sequence[float] | None = None,\n"
       "  down_widget: ba.Widget | None = None,\n"
       "  up_widget: ba.Widget | None = None,\n"
       "  left_widget: ba.Widget | None = None,\n"
       "  right_widget: ba.Widget | None = None,\n"
       "  texture: ba.Texture | None = None,\n"
       "  text_scale: float | None = None,\n"
       "  textcolor: Sequence[float] | None = None,\n"
       "  enable_sound: bool | None = None,\n"
       "  model_transparent: ba.Model | None = None,\n"
       "  model_opaque: ba.Model | None = None,\n"
       "  repeat: bool | None = None,\n"
       "  scale: float | None = None,\n"
       "  transition_delay: float | None = None,\n"
       "  on_select_call: Callable | None = None,\n"
       "  button_type: str | None = None,\n"
       "  extra_touch_border_scale: float | None = None,\n"
       "  selectable: bool | None = None,\n"
       "  show_buffer_top: float | None = None,\n"
       "  icon: ba.Texture | None = None,\n"
       "  iconscale: float | None = None,\n"
       "  icon_tint: float | None = None,\n"
       "  icon_color: Sequence[float] | None = None,\n"
       "  autoselect: bool | None = None,\n"
       "  mask_texture: ba.Texture | None = None,\n"
       "  tint_texture: ba.Texture | None = None,\n"
       "  tint_color: Sequence[float] | None = None,\n"
       "  tint2_color: Sequence[float] | None = None,\n"
       "  text_flatness: float | None = None,\n"
       "  text_res_scale: float | None = None,\n"
       "  enabled: bool | None = None) -> ba.Widget\n"
       "\n"
       "Create or edit a button widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"checkboxwidget", (PyCFunction)PyCheckBoxWidget,
       METH_VARARGS | METH_KEYWORDS,
       "checkboxwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  text: str | ba.Lstr | None = None,\n"
       "  value: bool | None = None,\n"
       "  on_value_change_call: Callable[[bool], None] | None = None,\n"
       "  on_select_call: Callable[[], None] | None = None,\n"
       "  text_scale: float | None = None,\n"
       "  textcolor: Sequence[float] | None = None,\n"
       "  scale: float | None = None,\n"
       "  is_radio_button: bool | None = None,\n"
       "  maxwidth: float | None = None,\n"
       "  autoselect: bool | None = None,\n"
       "  color: Sequence[float] | None = None) -> ba.Widget\n"
       "\n"
       "Create or edit a check-box widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"imagewidget", (PyCFunction)PyImageWidget, METH_VARARGS | METH_KEYWORDS,
       "imagewidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  color: Sequence[float] | None = None,\n"
       "  texture: ba.Texture | None = None,\n"
       "  opacity: float | None = None,\n"
       "  model_transparent: ba.Model | None = None,\n"
       "  model_opaque: ba.Model | None = None,\n"
       "  has_alpha_channel: bool = True,\n"
       "  tint_texture: ba.Texture | None = None,\n"
       "  tint_color: Sequence[float] | None = None,\n"
       "  transition_delay: float | None = None,\n"
       "  draw_controller: ba.Widget | None = None,\n"
       "  tint2_color: Sequence[float] | None = None,\n"
       "  tilt_scale: float | None = None,\n"
       "  mask_texture: ba.Texture | None = None,\n"
       "  radial_amount: float | None = None)\n"
       "  -> ba.Widget\n"
       "\n"
       "Create or edit an image widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"columnwidget", (PyCFunction)PyColumnWidget,
       METH_VARARGS | METH_KEYWORDS,
       "columnwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  background: bool | None = None,\n"
       "  selected_child: ba.Widget | None = None,\n"
       "  visible_child: ba.Widget | None = None,\n"
       "  single_depth: bool | None = None,\n"
       "  print_list_exit_instructions: bool | None = None,\n"
       "  left_border: float | None = None,\n"
       "  top_border: float | None = None,\n"
       "  bottom_border: float | None = None,\n"
       "  selection_loops_to_parent: bool | None = None,\n"
       "  border: float | None = None,\n"
       "  margin: float | None = None,\n"
       "  claims_left_right: bool | None = None,\n"
       "  claims_tab: bool | None = None) -> ba.Widget\n"
       "\n"
       "Create or edit a column widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"containerwidget", (PyCFunction)PyContainerWidget,
       METH_VARARGS | METH_KEYWORDS,
       "containerwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  background: bool | None = None,\n"
       "  selected_child: ba.Widget | None = None,\n"
       "  transition: str | None = None,\n"
       "  cancel_button: ba.Widget | None = None,\n"
       "  start_button: ba.Widget | None = None,\n"
       "  root_selectable: bool | None = None,\n"
       "  on_activate_call: Callable[[], None] | None = None,\n"
       "  claims_left_right: bool | None = None,\n"
       "  claims_tab: bool | None = None,\n"
       "  selection_loops: bool | None = None,\n"
       "  selection_loops_to_parent: bool | None = None,\n"
       "  scale: float | None = None,\n"
       "  on_outside_click_call: Callable[[], None] | None = None,\n"
       "  single_depth: bool | None = None,\n"
       "  visible_child: ba.Widget | None = None,\n"
       "  stack_offset: Sequence[float] | None = None,\n"
       "  color: Sequence[float] | None = None,\n"
       "  on_cancel_call: Callable[[], None] | None = None,\n"
       "  print_list_exit_instructions: bool | None = None,\n"
       "  click_activate: bool | None = None,\n"
       "  always_highlight: bool | None = None,\n"
       "  selectable: bool | None = None,\n"
       "  scale_origin_stack_offset: Sequence[float] | None = None,\n"
       "  toolbar_visibility: str | None = None,\n"
       "  on_select_call: Callable[[], None] | None = None,\n"
       "  claim_outside_clicks: bool | None = None,\n"
       "  claims_up_down: bool | None = None) -> ba.Widget\n"
       "\n"
       "Create or edit a container widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"rowwidget", (PyCFunction)PyRowWidget, METH_VARARGS | METH_KEYWORDS,
       "rowwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  background: bool | None = None,\n"
       "  selected_child: ba.Widget | None = None,\n"
       "  visible_child: ba.Widget | None = None,\n"
       "  claims_left_right: bool | None = None,\n"
       "  claims_tab: bool | None = None,\n"
       "  selection_loops_to_parent: bool | None = None) -> ba.Widget\n"
       "\n"
       "Create or edit a row widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"scrollwidget", (PyCFunction)PyScrollWidget,
       METH_VARARGS | METH_KEYWORDS,
       "scrollwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  background: bool | None = None,\n"
       "  selected_child: ba.Widget | None = None,\n"
       "  capture_arrows: bool = False,\n"
       "  on_select_call: Callable | None = None,\n"
       "  center_small_content: bool | None = None,\n"
       "  color: Sequence[float] | None = None,\n"
       "  highlight: bool | None = None,\n"
       "  border_opacity: float | None = None,\n"
       "  simple_culling_v: float | None = None,\n"
       "  selection_loops_to_parent: bool | None = None,\n"
       "  claims_left_right: bool | None = None,\n"
       "  claims_up_down: bool | None = None,\n"
       "  claims_tab: bool | None = None,\n"
       "  autoselect: bool | None = None) -> ba.Widget\n"
       "\n"
       "Create or edit a scroll widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"hscrollwidget", (PyCFunction)PyHScrollWidget,
       METH_VARARGS | METH_KEYWORDS,
       "hscrollwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  background: bool | None = None,\n"
       "  selected_child: ba.Widget | None = None,\n"
       "  capture_arrows: bool | None = None,\n"
       "  on_select_call: Callable[[], None] | None = None,\n"
       "  center_small_content: bool | None = None,\n"
       "  color: Sequence[float] | None = None,\n"
       "  highlight: bool | None = None,\n"
       "  border_opacity: float | None = None,\n"
       "  simple_culling_h: float | None = None,\n"
       "  claims_left_right: bool | None = None,\n"
       "  claims_up_down: bool | None = None,\n"
       "  claims_tab: bool | None = None)  -> ba.Widget\n"
       "\n"
       "Create or edit a horizontal scroll widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"textwidget", (PyCFunction)PyTextWidget, METH_VARARGS | METH_KEYWORDS,
       "textwidget(edit: ba.Widget | None = None,\n"
       "  parent: ba.Widget | None = None,\n"
       "  size: Sequence[float] | None = None,\n"
       "  position: Sequence[float] | None = None,\n"
       "  text: str | ba.Lstr | None = None,\n"
       "  v_align: str | None = None,\n"
       "  h_align: str | None = None,\n"
       "  editable: bool | None = None,\n"
       "  padding: float | None = None,\n"
       "  on_return_press_call: Callable[[], None] | None = None,\n"
       "  on_activate_call: Callable[[], None] | None = None,\n"
       "  selectable: bool | None = None,\n"
       "  query: ba.Widget | None = None,\n"
       "  max_chars: int | None = None,\n"
       "  color: Sequence[float] | None = None,\n"
       "  click_activate: bool | None = None,\n"
       "  on_select_call: Callable[[], None] | None = None,\n"
       "  always_highlight: bool | None = None,\n"
       "  draw_controller: ba.Widget | None = None,\n"
       "  scale: float | None = None,\n"
       "  corner_scale: float | None = None,\n"
       "  description: str | ba.Lstr | None = None,\n"
       "  transition_delay: float | None = None,\n"
       "  maxwidth: float | None = None,\n"
       "  max_height: float | None = None,\n"
       "  flatness: float | None = None,\n"
       "  shadow: float | None = None,\n"
       "  autoselect: bool | None = None,\n"
       "  rotate: float | None = None,\n"
       "  enabled: bool | None = None,\n"
       "  force_internal_editing: bool | None = None,\n"
       "  always_show_carat: bool | None = None,\n"
       "  big: bool | None = None,\n"
       "  extra_touch_border_scale: float | None = None,\n"
       "  res_scale: float | None = None)\n"
       "  -> Widget\n"
       "\n"
       "Create or edit a text widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Pass a valid existing ba.Widget as 'edit' to modify it; otherwise\n"
       "a new one is created and returned. Arguments that are not set to None\n"
       "are applied to the Widget."},

      {"widget", (PyCFunction)PyWidgetCall, METH_VARARGS | METH_KEYWORDS,
       "widget(edit: ba.Widget | None = None,\n"
       "  up_widget: ba.Widget | None = None,\n"
       "  down_widget: ba.Widget | None = None,\n"
       "  left_widget: ba.Widget | None = None,\n"
       "  right_widget: ba.Widget | None = None,\n"
       "  show_buffer_top: float | None = None,\n"
       "  show_buffer_bottom: float | None = None,\n"
       "  show_buffer_left: float | None = None,\n"
       "  show_buffer_right: float | None = None,\n"
       "  autoselect: bool | None = None) -> None\n"
       "\n"
       "Edit common attributes of any widget.\n"
       "\n"
       "Category: **User Interface Functions**\n"
       "\n"
       "Unlike other UI calls, this can only be used to edit, not to "
       "create.\n"},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
