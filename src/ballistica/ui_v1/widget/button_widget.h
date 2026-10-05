// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_BUTTON_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_BUTTON_WIDGET_H_

#include <memory>
#include <string>
#include <utility>

#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::ui_v1 {

class DepictionSlot;

class ButtonWidget : public Widget {
 public:
  /// Our default color. Exposed so other widgets can match buttons rather
  /// than duplicating the numbers and quietly drifting from them.
  static constexpr float kDefaultColorR{0.5f};
  static constexpr float kDefaultColorG{0.7f};
  static constexpr float kDefaultColorB{0.2f};

  ButtonWidget();
  ~ButtonWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  void set_width(float width) { width_ = width; }
  void set_height(float height) { height_ = height; }
  auto GetWidth() -> float override;
  auto GetHeight() -> float override;
  void set_color(float r, float g, float b) {
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
  void set_tint3_color(float r, float g, float b) {
    tint3_color_red_ = r;
    tint3_color_green_ = g;
    tint3_color_blue_ = b;
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
  void set_flatness(float val) { flatness_ = val; }

  auto set_text_flatness(float f) { text_flatness_ = f; }
  enum class Style : uint8_t {
    kRegular,
    kBack,
    kBackSmall,
    kTab,
    kSquare,
    kSmall,
    kMedium,
    kLarge,
    kLarger,
    kSquareWide,
  };
  void set_better_bg_fit(bool val) { better_bg_fit_ = val; }
  auto set_style(Style s) { style_ = s; }
  enum class IconType : uint8_t { kNone, kCancel, kStart };
  enum class TransitionType : uint8_t { kInLeft, kScale };

  /// A small built-in glyph drawn at our right edge, telling what a press
  /// does. The label's space shrinks to make room for it.
  enum class Accessory : uint8_t {
    kNone,
    /// Opens a popup menu of choices (an up/down indicator).
    kPopup,
  };
  void SetAccessory(Accessory val);

  /// Where the label sits horizontally. Center is the default; left and
  /// right hug our edges (inside the accessory, if any), with any icon
  /// staying just before the label.
  void SetTextHAlign(TextWidget::HAlign val);
  void SetTextLiteral(bool val);
  void SetText(const std::string& text);
  /// Native language-string label (retained + re-evaluated on
  /// language changes; see TextWidget::SetLangStr).
  void SetLangStr(std::shared_ptr<const base::LangStr> val);
  auto text() const -> std::string { return text_->text_raw(); }

  /// Label text as it is currently displayed -- the translated form
  /// when the label is a language-string, the raw string otherwise.
  /// Mirrors TextWidget::GetQueryText(); this is what `buttonwidget(
  /// query=...)` returns.
  auto GetQueryText() -> std::string { return text_->GetQueryText(); }
  auto set_icon_type(IconType i) { icon_type_ = i; }
  auto set_repeat(bool repeat) { repeat_ = repeat; }
  auto set_text_scale(float val) { text_scale_ = val; }
  void SetTexture(base::TextureAsset* t);
  void SetMaskTexture(base::TextureAsset* t);
  void SetTintTexture(base::TextureAsset* t);
  void SetIcon(base::TextureAsset* t);
  auto icon() const { return icon_.get(); }
  void SetOnActivateCall(PyObject* call_obj);

  /// Set a call to run once a press sequence that activated us is over:
  /// after the activation of a normal press or key/controller press,
  /// and after the *last* repeat of a held repeat-button. Lets a caller
  /// react to every activation locally and do something costly (a
  /// server round trip, say) only once at the end.
  void SetOnActionsCompleteCall(PyObject* call_obj);
  void Activate() override;
  auto IsSelectable() -> bool override { return selectable_; }
  auto GetWidgetTypeName() -> std::string override { return "button"; }
  auto set_enable_sound(bool enable) { sound_enabled_ = enable; }
  void SetMeshTransparent(base::MeshAsset* val);
  void SetMeshOpaque(base::MeshAsset* val);
  auto set_transition_delay(millisecs_t val) { transition_delay_ = val; }
  void set_transition_type(TransitionType val) { transition_type_ = val; }
  void OnRepeatTimerExpired();
  auto set_extra_touch_border_scale(float scale) {
    extra_touch_border_scale_ = scale;
  }
  auto set_selectable(bool s) { selectable_ = s; }
  auto set_icon_scale(float s) { icon_scale_ = s; }
  auto set_icon_tint(float tint) { icon_tint_ = tint; }
  void SetTextResScale(float val);

  /// Disabled buttons can't be activated. By default they also draw
  /// greyed out yet stay selectable (as disabled SliderWidgets and
  /// TextWidgets do): a tap selects one, and a tap or activation that
  /// would have fired it plays an error sound instead.
  ///
  /// Disabling mid-press (a held repeat-button reaching a limit, say)
  /// ends the press quietly: repeats stop, the actions-complete call
  /// fires, and the release is claimed without an error sound.
  void SetEnabled(bool val);
  auto enabled() const -> bool { return enabled_; }

  /// Have disabled mean what it does for the root widget's toolbar
  /// buttons, which hide by sliding offscreen and include purely
  /// decorative pieces: we draw exactly as when enabled (the caller owns
  /// that look), ignore presses entirely (they pass through to whatever
  /// is behind us), and never play error sounds. Not exposed to Python.
  auto set_disabled_toolbar_button_behavior(bool val) {
    disabled_toolbar_button_behavior_ = val;
  }
  void set_rotate(float val) { rotate_ = val; }
  auto set_opacity(float val) { opacity_ = val; }
  auto GetDrawBrightness(millisecs_t time) const -> float override;
  auto IsDrawDisabled() const -> bool override { return StandardDisabled_(); }
  auto is_color_set() const -> bool { return color_set_; }
  void OnLanguageChange() override;

  auto set_target_extra_left(float val) { target_extra_left_ = val; }
  auto set_target_extra_right(float val) { target_extra_right_ = val; }

  /// Our depiction slot, made on first use. While it has something to
  /// show it draws in place of our body (texture or standard art),
  /// filling our box; our label and icon draw over it, and our
  /// brightness (presses, focus, hover), disabled look, opacity and
  /// mask apply to it. Input stays ours: a depiction never takes a
  /// button's press.
  auto GetDepictionSlot() -> DepictionSlot&;

  /// Our depiction slot if we've made one.
  auto depiction_slot() const -> DepictionSlot* {
    return depiction_slot_.get();
  }

  /// With this set, mouse/touch only lands on us where our depiction
  /// actually draws (see base::Depiction::GetContentBox) -- an icon
  /// hugging one end of a wide button, a short name in a box sized for
  /// long ones -- rather than anywhere in our box. Grown to at least
  /// kMinDepictionHitSize each way (so a tiny depiction stays easy to
  /// tap) and kept within our box. No effect without a depiction, or
  /// on selection by keyboard/controller.
  void set_depiction_hit_area(bool val) { depiction_hit_area_ = val; }

  /// Smallest hit area depiction_hit_area shrinks us to, in our units.
  static constexpr float kMinDepictionHitSize{60.0f};

 private:
  bool depiction_hit_area_{};
  std::unique_ptr<DepictionSlot> depiction_slot_;
  bool text_width_dirty_ = true;
  bool color_set_ = false;
  void DoActivate(bool is_repeat = false);
  auto GetMult(millisecs_t current_time) const -> float;

  /// Whether we're disabled with the standard disabled behavior (greyed,
  /// still selectable, error sounds) rather than the toolbar's.
  auto StandardDisabled_() const -> bool {
    return !enabled_ && !disabled_toolbar_button_behavior_;
  }
  auto RotatePointToLocal(float x, float y) const -> std::pair<float, float>;

  /// Scale for our accessory glyph and its region: 1 except on short
  /// better-bg-fit buttons, which shrink it to keep room for the label.
  auto AccessoryScale_() const -> float;

  IconType icon_type_{};
  Accessory accessory_{};
  TextWidget::HAlign text_h_align_{TextWidget::HAlign::kCenter};
  Style style_{};
  TransitionType transition_type_{TransitionType::kInLeft};
  bool enabled_{true};
  bool disabled_toolbar_button_behavior_{};
  bool selectable_{true};
  bool sound_enabled_{true};
  bool hover_{};
  bool repeat_{};
  bool pressed_{};

  /// A press landed on us while standard-disabled; we claim its release
  /// (answering an in-bounds one with an error sound).
  bool disabled_pressed_{};

  /// We were disabled mid-press; claim the release silently.
  bool claim_release_silently_{};
  bool better_bg_fit_{};
  millisecs_t last_activate_time_millisecs_{};
  millisecs_t birth_time_millisecs_{};
  millisecs_t transition_delay_{};
  float icon_tint_{};
  float extra_touch_border_scale_{1.0f};
  float width_{50.0f};
  float height_{30.0f};
  float text_scale_{1.0f};
  float text_width_{0.0f};
  float text_height_{0.0f};
  float color_red_{kDefaultColorR};
  float color_green_{kDefaultColorG};
  float color_blue_{kDefaultColorB};
  float icon_color_red_{1.0f};
  float icon_color_green_{1.0f};
  float icon_color_blue_{1.0f};
  float icon_color_alpha_{1.0f};
  float icon_scale_{1.0f};
  float rotate_{0.0f};
  float opacity_{1.0f};
  float flatness_{0.0f};
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
  float tint3_color_red_{1.0f};
  float tint3_color_green_{1.0f};
  float tint3_color_blue_{1.0f};
  float target_extra_right_{0.0f};
  float target_extra_left_{0.0f};
  Object::Ref<base::TextureAsset> texture_;
  Object::Ref<base::TextureAsset> icon_;
  Object::Ref<base::TextureAsset> tint_texture_;
  Object::Ref<base::TextureAsset> mask_texture_;
  Object::Ref<base::MeshAsset> mesh_transparent_;
  Object::Ref<base::MeshAsset> mesh_opaque_;

  /// Run the actions-complete call if anything activated us since the
  /// last one (see SetOnActionsCompleteCall).
  void RunActionsComplete_();

  /// Has DoActivate() run since we last reported actions-complete?
  bool activated_since_complete_{};

  // Keep these at the bottom so they're torn down first (this was a problem
  // at some point though I don't remember details).
  Object::Ref<TextWidget> text_;

  /// Draws our accessory glyph; exists only while we have one.
  Object::Ref<TextWidget> accessory_text_;
  Object::Ref<base::PythonContextCall> on_activate_call_;
  Object::Ref<base::PythonContextCall> on_actions_complete_call_;
  Object::Ref<base::AppTimer> repeat_timer_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_BUTTON_WIDGET_H_
