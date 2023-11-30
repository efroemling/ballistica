// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_TEXT_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_TEXT_WIDGET_H_

#include <string>

#include "ballistica/base/graphics/mesh/text_mesh.h"
#include "ballistica/shared/python/python_ref.h"
#include "ballistica/ui_v1/widget/widget.h"

namespace ballistica::ui_v1 {

// widget for drawing static text as well as text input
class TextWidget : public Widget {
 public:
  TextWidget();
  ~TextWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  void SetWidth(float widthIn);
  void SetHeight(float heightIn);
  auto GetWidth() -> float override;
  auto GetHeight() -> float override;
  enum class HAlign : uint8_t { kLeft, kCenter, kRight };
  enum class VAlign : uint8_t { kTop, kCenter, kBottom };
  enum class GlowType : uint8_t { kGradient, kUniform };
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto IsSelectable() -> bool override {
    return (enabled_ && (editable_ || selectable_));
  }
  void set_halign(HAlign a) {
    if (alignment_h_ != a) {
      text_group_dirty_ = true;
    }
    alignment_h_ = a;
  }
  void set_valign(VAlign a) {
    if (alignment_v_ != a) {
      text_group_dirty_ = true;
    }
    alignment_v_ = a;
  }
  void set_max_width(float m) { max_width_ = m; }
  void set_max_height(float m) { max_height_ = m; }
  void set_rotate(float val) { rotate_ = val; }
  void SetText(const std::string& text_in);
  void set_color(float rIn, float gIn, float bIn, float aIn) {
    color_r_ = rIn;
    color_g_ = gIn;
    color_b_ = bIn;
    color_a_ = aIn;
  }
  auto text_raw() const -> const std::string& { return text_raw_; }
  void SetEditable(bool e);
  void set_selectable(bool s) { selectable_ = s; }
  void SetEnabled(bool val);
  void set_padding(float padding_in) { padding_ = padding_in; }
  void set_max_chars(int max_chars_in) { max_chars_ = max_chars_in; }
  auto max_chars() const -> int { return max_chars_; }
  auto always_show_carat() const -> bool { return always_show_carat_; }
  void set_always_show_carat(bool val) { always_show_carat_ = val; }
  void set_click_activate(bool enabled) { click_activate_ = enabled; }
  void set_on_return_press_call(PyObject* call_tuple);
  void set_on_activate_call(PyObject* call_tuple);
  void set_center_scale(float val) { center_scale_ = val; }
  auto editable() const -> bool { return editable_; }
  void Activate() override;
  auto GetWidgetTypeName() -> std::string override { return "text"; }
  void set_always_highlight(bool val) { always_highlight_ = val; }
  void set_description(const std::string& d) { description_ = d; }
  auto description() const -> std::string { return description_; }
  void set_transition_delay(float val) { transition_delay_ = val; }
  void set_flatness(float flatness) { flatness_ = flatness; }
  void set_shadow(float shadow) { shadow_ = shadow; }
  void set_res_scale(float res_scale);
  auto GetTextWidth() -> float;
  void OnLanguageChange() override;
  void AdapterFinished();

  static TextWidget* GetAndroidStringEditWidget();

  void set_force_internal_editing(bool val) { force_internal_editing_ = val; }
  auto force_internal_editing() const -> bool {
    return force_internal_editing_;
  }
  // Set whether to attempt to use big font (if possible).
  void SetBig(bool big);
  void set_extra_touch_border_scale(float scale) {
    extra_touch_border_scale_ = scale;
  }
  void set_glow_type(GlowType glow_type) {
    if (glow_type == glow_type_) {
      return;
    }
    glow_type_ = glow_type;
    highlight_dirty_ = true;
  }

 private:
  auto ScaleAdjustedX_(float x) -> float;
  auto ScaleAdjustedY_(float y) -> float;
  void AddCharsToText_(const std::string& addchars);
  auto ShouldUseStringEditor_() const -> bool;
  void InvokeStringEditor_();
  void UpdateTranslation_();
  void DoDrawCarat_(base::RenderPass* pass, base::TextMesh::HAlign align_h,
                    base::TextMesh::VAlign align_v, float x_offset,
                    float y_offset, float max_width_scale,
                    float max_height_scale);
  void DoDrawText_(base::RenderPass* pass, float x_offset, float y_offset,
                   float max_width_scale, float max_height_scale);

  HAlign alignment_h_{HAlign::kLeft};
  VAlign alignment_v_{VAlign::kTop};
  GlowType glow_type_{GlowType::kGradient};
  bool enabled_{true};
  bool big_{};
  bool force_internal_editing_{};
  bool always_show_carat_{};
  bool highlight_dirty_{true};
  bool text_translation_dirty_{true};
  bool text_group_dirty_{true};
  bool outline_dirty_{true};
  bool click_activate_{};
  bool mouse_over_{};
  bool pressed_{};
  bool pressed_activate_{};
  bool always_highlight_{};
  bool editable_{};
  bool selectable_{};
  bool clear_pressed_{};
  bool clear_mouse_over_{};
  bool do_clear_button_{true};
  int carat_position_{9999};
  int max_chars_{99999};
  float res_scale_{1.0f};
  float transition_delay_{};
  float max_width_{-1.0f};
  float max_height_{-1.0f};
  float extra_touch_border_scale_{1.0f};
  float highlight_width_{};
  float highlight_height_{};
  float highlight_center_x_{};
  float highlight_center_y_{};
  float outline_width_{};
  float outline_height_{};
  float outline_center_x_{};
  float outline_center_y_{};
  float text_width_{};
  float text_height_{};
  float rotate_{};
  float color_r_{1.0f};
  float color_g_{1.0f};
  float color_b_{1.0f};
  float color_a_{1.0f};
  float flatness_{};
  float shadow_{0.5f};
  float padding_{};
  float width_{50.0f};
  float height_{30.0f};
  float center_scale_{1.0f};
  std::string text_raw_;
  std::string text_translated_;
  millisecs_t birth_time_millisecs_{};
  millisecs_t last_activate_time_millisecs_{};
  millisecs_t last_carat_change_time_millisecs_{};
  std::string description_{"Text"};
  Object::Ref<base::TextGroup> text_group_;

  // We keep these at the bottom so they're torn down first.
  Object::Ref<base::PythonContextCall> on_return_press_call_;
  Object::Ref<base::PythonContextCall> on_activate_call_;
  Object::Ref<base::NinePatchMesh> highlight_mesh_;
  PythonRef string_edit_adapter_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_TEXT_WIDGET_H_
