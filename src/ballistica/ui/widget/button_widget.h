// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_WIDGET_BUTTON_WIDGET_H_
#define BALLISTICA_UI_WIDGET_BUTTON_WIDGET_H_

#include <string>

#include "ballistica/ui/widget/text_widget.h"

namespace ballistica {

class ButtonWidget : public Widget {
 public:
  ButtonWidget();
  ~ButtonWidget() override;
  void Draw(RenderPass* pass, bool transparent) override;
  auto HandleMessage(const WidgetMessage& m) -> bool override;
  void set_width(float width) { width_ = width; }
  void set_height(float height) { height_ = height; }
  auto GetWidth() -> float override;
  auto GetHeight() -> float override;
  void SetColor(float r, float g, float b) {
    color_set_ = true;
    color_red_ = r;
    color_green_ = g;
    color_blue_ = b;
  }
  void set_tint_color(float r, float g, float b) {
    tint_color_red_ = r;
    tint_color_green_ = g;
    tint_color_blue_ = b;
  }
  void set_tint2_color(float r, float g, float b) {
    tint2_color_red_ = r;
    tint2_color_green_ = g;
    tint2_color_blue_ = b;
  }
  void set_text_color(float r, float g, float b, float a) {
    text_color_r_ = r;
    text_color_g_ = g;
    text_color_b_ = b;
    text_color_a_ = a;
  }
  void set_icon_color(float r, float g, float b, float a) {
    icon_color_red_ = r;
    icon_color_green_ = g;
    icon_color_blue_ = b;
    icon_color_alpha_ = a;
  }
  void set_text_flatness(float f) { text_flatness_ = f; }
  enum class Style { kRegular, kBack, kBackSmall, kTab, kSquare };
  void set_style(Style s) { style_ = s; }
  enum class IconType { kNone, kCancel, kStart };
  void SetText(const std::string& text);
  auto text() const -> std::string { return text_->text_raw(); }
  void set_icon_type(IconType i) { icon_type_ = i; }
  void set_repeat(bool repeat) { repeat_ = repeat; }
  void set_text_scale(float val) { text_scale_ = val; }
  void SetTexture(Texture* t);
  void SetMaskTexture(Texture* t);
  void SetTintTexture(Texture* val);
  void SetIcon(Texture* t);
  auto icon() const -> Texture* { return icon_.get(); }
  void set_on_activate_call(PyObject* call_obj);
  void Activate() override;
  auto IsSelectable() -> bool override { return selectable_; }
  auto GetWidgetTypeName() -> std::string override { return "button"; }
  void set_enable_sound(bool enable) { sound_enabled_ = enable; }
  void SetModelTransparent(Model* val);
  void SetModelOpaque(Model* val);
  void set_transition_delay(millisecs_t val) { transition_delay_ = val; }
  void HandleRealTimerExpired(RealTimer<ButtonWidget>* t);
  void set_extra_touch_border_scale(float scale) {
    extra_touch_border_scale_ = scale;
  }
  void set_selectable(bool s) { selectable_ = s; }
  void set_icon_scale(float s) { icon_scale_ = s; }
  void set_icon_tint(float tint) { icon_tint_ = tint; }
  void SetTextResScale(float val);

  // Disabled buttons can't be clicked or otherwise activated.
  void set_enabled(bool val) { enabled_ = val; }
  auto enabled() const -> bool { return enabled_; }
  void set_opacity(float val) { opacity_ = val; }
  auto GetDrawBrightness(millisecs_t time) const -> float override;
  auto is_color_set() const -> bool { return color_set_; }
  void OnLanguageChange() override;

 private:
  bool text_width_dirty_ = true;
  bool color_set_ = false;
  void DoActivate(bool isRepeat = false);
  auto GetMult(millisecs_t current_time) const -> float;
  IconType icon_type_ = IconType::kNone;
  bool enabled_ = true;
  bool selectable_ = true;
  float icon_tint_ = 0.0f;
  Style style_ = Style::kRegular;
  bool sound_enabled_ = true;
  bool mouse_over_ = false;
  bool repeat_ = false;
  bool pressed_ = false;
  float extra_touch_border_scale_ = 1.0f;
  float width_ = 50.0f;
  float height_ = 30.0f;
  float text_scale_ = 1.0f;
  float text_width_ = 0.0f;
  float color_red_ = 0.5f;
  float color_green_ = 0.7f;
  float color_blue_ = 0.2f;
  float icon_color_red_ = 1.0f;
  float icon_color_green_ = 1.0f;
  float icon_color_blue_ = 1.0f;
  float icon_color_alpha_ = 1.0f;
  Object::Ref<Texture> texture_;
  Object::Ref<Texture> icon_;
  Object::Ref<Texture> tint_texture_;
  Object::Ref<Texture> mask_texture_;
  Object::Ref<Model> model_transparent_;
  Object::Ref<Model> model_opaque_;
  float icon_scale_{1.0f};
  millisecs_t last_activate_time_{};
  millisecs_t birth_time_{};
  millisecs_t transition_delay_{};
  float opacity_{1.0f};
  float text_flatness_{0.5f};
  float text_color_r_{0.75f};
  float text_color_g_{1.0f};
  float text_color_b_{0.7f};
  float text_color_a_{1.0f};
  float tint_color_red_{1.0f};
  float tint_color_green_{1.0f};
  float tint_color_blue_{1.0f};
  float tint2_color_red_{1.0f};
  float tint2_color_green_{1.0f};
  float tint2_color_blue_{1.0f};

  // Keep these at the bottom, so they're torn down first.
  Object::Ref<TextWidget> text_;
  Object::Ref<PythonContextCall> on_activate_call_;
  Object::Ref<RealTimer<ButtonWidget> > repeat_timer_;
};

}  // namespace ballistica

#endif  // BALLISTICA_UI_WIDGET_BUTTON_WIDGET_H_
