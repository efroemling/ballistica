// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_BUTTON_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_BUTTON_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::ui_v1 {

class ButtonWidget : public Widget {
 public:
  ButtonWidget();
  ~ButtonWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
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
  auto set_text_flatness(float f) { text_flatness_ = f; }
  enum class Style : uint8_t { kRegular, kBack, kBackSmall, kTab, kSquare };
  auto set_style(Style s) { style_ = s; }
  enum class IconType : uint8_t { kNone, kCancel, kStart };
  void set_text(const std::string& text);
  auto text() const -> std::string { return text_->text_raw(); }
  auto set_icon_type(IconType i) { icon_type_ = i; }
  auto set_repeat(bool repeat) { repeat_ = repeat; }
  auto set_text_scale(float val) { text_scale_ = val; }
  void SetTexture(base::TextureAsset* t);
  void SetMaskTexture(base::TextureAsset* t);
  void SetTintTexture(base::TextureAsset* val);
  void SetIcon(base::TextureAsset* t);
  auto icon() const -> base::TextureAsset* { return icon_.Get(); }
  void set_on_activate_call(PyObject* call_obj);
  void Activate() override;
  auto IsSelectable() -> bool override { return selectable_; }
  auto GetWidgetTypeName() -> std::string override { return "button"; }
  auto set_enable_sound(bool enable) { sound_enabled_ = enable; }
  void SetMeshTransparent(base::MeshAsset* val);
  void SetMeshOpaque(base::MeshAsset* val);
  auto set_transition_delay(millisecs_t val) { transition_delay_ = val; }
  void OnRepeatTimerExpired();
  auto set_extra_touch_border_scale(float scale) {
    extra_touch_border_scale_ = scale;
  }
  auto set_selectable(bool s) { selectable_ = s; }
  auto set_icon_scale(float s) { icon_scale_ = s; }
  auto set_icon_tint(float tint) { icon_tint_ = tint; }
  void SetTextResScale(float val);

  // Disabled buttons can't be clicked or otherwise activated.
  auto set_enabled(bool val) { enabled_ = val; }
  auto enabled() const -> bool { return enabled_; }
  auto set_opacity(float val) { opacity_ = val; }
  auto GetDrawBrightness(millisecs_t time) const -> float override;
  auto is_color_set() const -> bool { return color_set_; }
  void OnLanguageChange() override;

 private:
  bool text_width_dirty_ = true;
  bool color_set_ = false;
  void DoActivate(bool is_repeat = false);
  auto GetMult(millisecs_t current_time) const -> float;

  IconType icon_type_{};
  Style style_{};
  bool enabled_{true};
  bool selectable_{true};
  bool sound_enabled_{true};
  bool mouse_over_{};
  bool repeat_{};
  bool pressed_{};
  millisecs_t last_activate_time_millisecs_{};
  millisecs_t birth_time_millisecs_{};
  millisecs_t transition_delay_{};
  float icon_tint_{};
  float extra_touch_border_scale_{1.0f};
  float width_{50.0f};
  float height_{30.0f};
  float text_scale_{1.0f};
  float text_width_{0.0f};
  float color_red_{0.5f};
  float color_green_{0.7f};
  float color_blue_{0.2f};
  float icon_color_red_{1.0f};
  float icon_color_green_{1.0f};
  float icon_color_blue_{1.0f};
  float icon_color_alpha_{1.0f};
  float icon_scale_{1.0f};
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
  Object::Ref<base::TextureAsset> texture_;
  Object::Ref<base::TextureAsset> icon_;
  Object::Ref<base::TextureAsset> tint_texture_;
  Object::Ref<base::TextureAsset> mask_texture_;
  Object::Ref<base::MeshAsset> mesh_transparent_;
  Object::Ref<base::MeshAsset> mesh_opaque_;

  // Keep these at the bottom so they're torn down first (this was a problem
  // at some point though I don't remember details).
  Object::Ref<TextWidget> text_;
  Object::Ref<base::PythonContextCall> on_activate_call_;
  Object::Ref<base::AppTimer> repeat_timer_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_BUTTON_WIDGET_H_
