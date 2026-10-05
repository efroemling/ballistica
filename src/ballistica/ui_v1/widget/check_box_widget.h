// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_CHECK_BOX_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_CHECK_BOX_WIDGET_H_

#include <string>

#include "ballistica/base/graphics/mesh/image_mesh.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::ui_v1 {

// Check box interface widget.
class CheckBoxWidget : public Widget {
 public:
  /// Overall layout/look. kDefault has the box at the left with text
  /// following it and a gradient selection glow; kRight has text at the
  /// left bounds, the box at the right bounds, and a uniform selection
  /// glow (the gradient glow fades out toward the right, which reads wrong
  /// with the box sitting there).
  enum class Style : uint8_t { kDefault, kRight };

  CheckBoxWidget();
  ~CheckBoxWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  void SetWidth(float widthIn);
  void SetHeight(float heightIn);
  auto GetWidth() -> float override { return width_; }
  auto GetHeight() -> float override { return height_; }
  void SetText(const std::string& text);
  /// Set a native language-string as our text (retained; re-evaluated on
  /// language changes; see TextWidget::SetLangStr).
  void SetLangStr(std::shared_ptr<const base::LangStr> val);
  void SetValue(bool value);
  /// Max width for our text. In the kRight style the text is always fit
  /// to the space left of the box; a value here can only shrink it further.
  void SetMaxWidth(float w);
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

  /// A disabled check box draws greyed and can't be toggled, but stays
  /// selectable (as disabled ButtonWidgets do) so navigation around it
  /// never changes: a tap selects it, and a tap or activation that would
  /// have toggled it plays an error sound instead.
  void SetEnabled(bool val);
  auto enabled() const -> bool { return enabled_; }
  void SetStyle(Style style);
  void GetCenter(float* x, float* y) override;
  void OnLanguageChange() override;

  /// Scale-in transition, as on ButtonWidget/TextWidget: after
  /// `transition_delay` ms past creation the box scales up about its
  /// own center and the text about its own, so a wide widget's parts
  /// each pop in place rather than sweeping in from the middle.
  enum class TransitionType : uint8_t { kInLeft, kScale };
  void set_transition_delay(millisecs_t val);
  void set_transition_type(TransitionType val);

 private:
  void UpdateTextMaxWidth_();
  /// Current scale-in factor (1.0 once the transition is over).
  auto TransitionScale_(millisecs_t current_time) const -> float;
  bool have_text_{true};
  TransitionType transition_type_{TransitionType::kInLeft};
  millisecs_t transition_delay_{};
  millisecs_t birth_time_millisecs_{};
  float max_width_{-1.0f};
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
  // Last user toggle (for the post-toggle flash); far enough in the
  // past to start that no flash shows before one.
  millisecs_t last_activate_time_{-10000};
  float box_size_{20.0f};
  float box_padding_{6.0f};
  float width_{400.0f};
  float height_{24.0f};
  TextWidget text_;
  std::string command_;
  bool pressed_{};
  bool enabled_{true};
  bool is_radio_button_{};
  Style style_{Style::kDefault};
  Object::Ref<base::NinePatchMesh> highlight_mesh_;

  // Keep these at the bottom, so they'll be torn down first.
  Object::Ref<base::PythonContextCall> on_value_change_call_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_CHECK_BOX_WIDGET_H_
