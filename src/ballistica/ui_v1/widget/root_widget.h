// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_

#include <list>
#include <string>
#include <vector>

#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// Root-level widget; contains a top-bar, screen-stack, bottom-bar,
// menu-button, etc. This is intended to replace RootUI.
class RootWidget : public ContainerWidget {
 public:
  RootWidget();
  ~RootWidget() override;
  auto GetWidgetTypeName() -> std::string override { return "root"; }
  void SetScreenWidget(StackWidget* w);
  void SetOverlayWidget(StackWidget* w);
  void UpdateForFocusedWindow();
  void Setup();
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  void BackPress();
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto GetSpecialWidget(const std::string& s) const -> Widget*;
  auto base_scale() const -> float { return base_scale_; }
  auto overlay_window_stack() const -> StackWidget* {
    return overlay_stack_widget_;
  }
  void SquadPress();

  /// Called when UIScale or screen dimensions change.
  void OnUIScaleChange();

  void OnLanguageChange() override;
  void UpdateLayout() override;
  void SetSquadSizeLabel(int val);
  void SetAccountState(bool signed_in, const std::string& name);

  void SetTicketsMeterValue(int val);
  void SetTokensMeterValue(int val, bool gold_pass);
  void SetLeagueRankValues(const std::string& league_type, int league_number,
                           int league_rank);
  void SetAchievementPercentText(const std::string& val);
  void SetLevelText(const std::string& val);
  void SetXPText(const std::string& val);
  void SetInboxCountText(const std::string& val);
  void SetChests(const std::string& chest_0_appearance,
                 const std::string& chest_1_appearance,
                 const std::string& chest_2_appearance,
                 const std::string& chest_3_appearance,
                 seconds_t chest_0_unlock_time, seconds_t chest_1_unlock_time,
                 seconds_t chest_2_unlock_time, seconds_t chest_3_unlock_time,
                 seconds_t chest_0_ad_allow_time,
                 seconds_t chest_1_ad_allow_time,
                 seconds_t chest_2_ad_allow_time,
                 seconds_t chest_3_ad_allow_time);
  void SetHaveLiveValues(bool have_live_values);

  auto bottom_left_height() const { return bottom_left_height_; }

  /// Temporarily pause updates to things such as
  /// ticket/token meters so they can be applied at a
  /// set time or animated.
  void PauseUpdates();

  /// Resume updates to things such as ticket/token
  /// meters. Snaps to the latest values.
  void ResumeUpdates();

  auto league_type_vis_value() const { return league_type_vis_value_; }
  auto league_number_vis_value() const { return league_number_vis_value_; }
  auto league_rank_vis_value() const { return league_rank_vis_value_; }
  void RestoreLeagueRankDisplayVisValues(const std::string& league_type,
                                         int league_num, int league_rank);

 private:
  struct ButtonDef_;
  struct Button_;
  struct TextDef_;
  struct ImageDef_;
  struct Text_;
  struct Image_;
  enum class MeterType_ { kLevel, kTrophy, kTickets, kTokens };
  enum class VAlign_ { kTop, kCenter, kBottom };

  auto GetTimeStr_(seconds_t diff) -> std::string;
  void UpdateChests_();
  void UpdateTokensMeterText_();
  void UpdateForFocusedWindow_(Widget* widget);
  auto AddButton_(const ButtonDef_& def) -> Button_*;
  auto AddText_(const TextDef_& def) -> Text_*;
  auto AddImage_(const ImageDef_& def) -> Image_*;
  void StepChildWidgets_(seconds_t dt);
  void StepChests_();
  void StepLeagueRankAnim_(base::RenderPass* pass, seconds_t dt);
  void AddMeter_(MeterType_ type, float h_align, float r, float g, float b,
                 bool plus, const std::string& s);
  void UpdateTokensMeterTextColor_();
  void ShowTrophyMeterAnnotation_(const std::string& val);
  void HideTrophyMeterAnnotation_();
  void UpdateLeagueRankDisplayValue_();
  auto ColorForLeagueValue_(const std::string& value) -> Vector3f;

  Object::Ref<base::AppTimer> trophy_meter_annotation_timer_;
  Object::Ref<base::AppTimer> trophy_meter_display_timer_;
  std::string chest_0_appearance_;
  std::string chest_1_appearance_;
  std::string chest_2_appearance_;
  std::string chest_3_appearance_;
  std::string time_suffix_hours_;
  std::string time_suffix_minutes_;
  std::string time_suffix_seconds_;
  std::string league_type_vis_value_;
  std::string league_type_value_;
  std::list<Button_> buttons_;
  std::list<Text_> texts_;
  std::list<Image_> images_;
  std::vector<Button_*> top_left_buttons_;
  std::vector<Button_*> top_right_buttons_;
  std::vector<Button_*> bottom_left_buttons_;
  std::vector<Button_*> bottom_right_buttons_;
  StackWidget* screen_stack_widget_{};
  StackWidget* overlay_stack_widget_{};
  Button_* back_button_{};
  Button_* account_button_{};
  Button_* achievements_button_{};
  Button_* inbox_button_{};
  Button_* tickets_meter_button_{};
  Button_* tokens_meter_button_{};
  Button_* trophy_meter_button_{};
  Button_* settings_button_{};
  Button_* store_button_{};
  Button_* get_tokens_button_{};
  Button_* inventory_button_{};
  Button_* menu_button_{};
  Button_* squad_button_{};
  Button_* level_meter_button_{};
  Button_* chest_0_button_{};
  Button_* chest_1_button_{};
  Button_* chest_2_button_{};
  Button_* chest_3_button_{};
  Button_* chest_backing_{};
  Image_* trophy_icon_{};
  Image_* tickets_meter_icon_{};
  Image_* tokens_meter_icon_{};
  Image_* inbox_count_backing_{};
  Image_* chest_0_lock_icon_{};
  Image_* chest_1_lock_icon_{};
  Image_* chest_2_lock_icon_{};
  Image_* chest_3_lock_icon_{};
  Image_* chest_0_tv_icon_{};
  Image_* chest_1_tv_icon_{};
  Image_* chest_2_tv_icon_{};
  Image_* chest_3_tv_icon_{};
  Text_* squad_size_text_{};
  Text_* account_name_text_{};
  Text_* tickets_meter_text_{};
  Text_* tokens_meter_text_{};
  Text_* league_rank_text_{};
  Text_* achievement_percent_text_{};
  Text_* level_text_{};
  Text_* xp_text_{};
  Text_* inbox_count_text_{};
  Text_* chest_0_time_text_{};
  Text_* chest_1_time_text_{};
  Text_* chest_2_time_text_{};
  Text_* chest_3_time_text_{};
  Text_* trophy_meter_annotation_text_{};
  seconds_t chest_0_unlock_time_{-1.0};
  seconds_t chest_1_unlock_time_{-1.0};
  seconds_t chest_2_unlock_time_{-1.0};
  seconds_t chest_3_unlock_time_{-1.0};
  seconds_t chest_0_ad_allow_time_{-1.0};
  seconds_t chest_1_ad_allow_time_{-1.0};
  seconds_t chest_2_ad_allow_time_{-1.0};
  seconds_t chest_3_ad_allow_time_{-1.0};
  seconds_t last_chests_step_time_{-1.0f};
  seconds_t update_pause_time_{};
  seconds_t update_time_{};
  seconds_t league_rank_anim_start_time_{};
  float base_scale_{1.0f};
  float bottom_left_height_{};
  float league_rank_anim_val_{};
  int update_pause_count_{};
  int league_rank_vis_value_{-1};
  int league_rank_value_{-1};
  int league_rank_anim_start_val_{};
  int league_number_vis_value_{-1};
  int league_number_value_{-1};
  std::optional<uint32_t> league_rank_anim_sound_play_id_{};
  ToolbarVisibility toolbar_visibility_{ToolbarVisibility::kInGame};
  bool child_widgets_dirty_{true};
  bool in_main_menu_{};
  bool gold_pass_{};
  bool have_live_values_{};
  bool translations_dirty_{true};
  bool league_rank_animating_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
