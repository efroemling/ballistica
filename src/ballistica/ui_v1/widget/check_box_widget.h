// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_CHECK_BOX_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_CHECK_BOX_WIDGET_H_

#include <string>

#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::ui_v1 {

// Check box interface widget.
class CheckBoxWidget : public Widget {
 public:
  CheckBoxWidget();
  ~CheckBoxWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  void SetWidth(float widthIn);
  void SetHeight(float heightIn);
  auto GetWidth() -> float override { return width_; }
  auto GetHeight() -> float override { return height_; }
  void SetText(const std::string& text);
  void SetValue(bool value);
  void SetMaxWidth(float w) { text_.set_max_width(w); }
  void SetTextScale(float val) { text_.set_center_scale(val); }
  void set_text_color(float r, float g, float b, float a) {
    text_color_r_ = r;
    text_color_g_ = g;
    text_color_b_ = b;
    text_color_a_ = a;
  }
  void set_color(float r, float g, float b) {
    color_r_ = r;
    color_g_ = g;
    color_b_ = b;
  }
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  void Activate() override;
  auto IsSelectable() -> bool override { return true; }
  auto GetWidgetTypeName() -> std::string override { return "checkbox"; }
  void SetOnValueChangeCall(PyObject* call_tuple);
  void SetIsRadioButton(bool enabled) { is_radio_button_ = enabled; }
  void GetCenter(float* x, float* y) override;
  void OnLanguageChange() override;

 private:
  bool have_text_{true};
  float text_color_r_{0.75f};
  float text_color_g_{1.0f};
  float text_color_b_{0.7f};
  float text_color_a_{1.0f};
  float color_r_{0.4f};
  float color_g_{0.6f};
  float color_b_{0.2f};
  base::ImageMesh box_image_mesh_;
  float check_width_{};
  float check_height_{};
  float check_center_x_{};
  float check_center_y_{};
  float box_width_{};
  float box_height_{};
  float box_center_x_{};
  float box_center_y_{};
  float highlight_width_{};
  float highlight_height_{};
  float highlight_center_x_{};
  float highlight_center_y_{};
  bool highlight_dirty_{true};
  bool box_dirty_{true};
  bool check_dirty_{true};
  bool click_select_{};
  bool mouse_over_{};
  bool checked_{true};
  bool have_drawn_{};
  millisecs_t last_change_time_{};
  float box_size_{20.0f};
  float box_padding_{6.0f};
  float width_{400.0f};
  float height_{24.0f};
  TextWidget text_;
  std::string command_;
  bool pressed_{};
  bool is_radio_button_{};

  // Keep these at the bottom, so they'll be torn down first.
  Object::Ref<base::PythonContextCall> on_value_change_call_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_CHECK_BOX_WIDGET_H_
