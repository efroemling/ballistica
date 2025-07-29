// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_

#include <list>
#include <map>
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
  void SetAccountSignInState(bool signed_in, const std::string& name);

  void SetTicketsMeterValue(int val);
  void SetTokensMeterValue(int val, bool gold_pass);
  void SetLeagueRankValues(const std::string& league_type, int league_number,
                           int league_rank);
  void SetAchievementPercentText(const std::string& val);
  void SetLevelText(const std::string& val);
  void SetXPText(const std::string& val);
  void SetInboxState(int val, bool is_max, const std::string& announce_text);
  void SetChests(const std::string& chest_0_appearance,
                 const std::string& chest_1_appearance,
                 const std::string& chest_2_appearance,
                 const std::string& chest_3_appearance,
                 seconds_t chest_0_create_time, seconds_t chest_1_create_time,
                 seconds_t chest_2_create_time, seconds_t chest_3_create_time,
                 seconds_t chest_0_unlock_time, seconds_t chest_1_unlock_time,
                 seconds_t chest_2_unlock_time, seconds_t chest_3_unlock_time,
                 int chest_0_unlock_tokens, int chest_1_unlock_tokens,
                 int chest_2_unlock_tokens, int chest_3_unlock_tokens,
                 seconds_t chest_0_ad_allow_time,
                 seconds_t chest_1_ad_allow_time,
                 seconds_t chest_2_ad_allow_time,
                 seconds_t chest_3_ad_allow_time);
  void SetHaveLiveValues(bool have_live_values);

  auto bottom_left_height() const { return bottom_left_height_; }

  /// Temporarily pause automatic updates to allow explicit animation. Make
  /// sure each call to this is matched by a call to ResumeUpdates. Note
  /// that this is a static function to avoid the possibility of
  /// accidentally calling pause and resume on different instances.
  static void PauseUpdates();

  /// Resume updates to things such as ticket/token meters. Note that this
  /// is a static function to avoid the possibility of accidentally calling
  /// pause and resume on different instances.
  static void ResumeUpdates();

  auto league_type_vis_value() const { return league_type_vis_value_; }
  auto league_number_vis_value() const { return league_number_vis_value_; }
  auto league_rank_vis_value() const { return league_rank_vis_value_; }
  auto inbox_count_vis_value() const { return inbox_count_vis_value_; }
  auto inbox_count_is_max_vis_value() const {
    return inbox_count_is_max_vis_value_;
  }
  void SetAccountState(const std::string& league_type, int league_num,
                       int league_rank, int inbox_count,
                       bool inbox_count_is_max);
  void AnimateChestUnlockTime(const std::string& chestid, seconds_t duration,
                              seconds_t startvalue, seconds_t endvalue);
  void AnimateTickets(seconds_t duration, int startvalue, int endvalue);
  void AnimateTokens(seconds_t duration, int startvalue, int endvalue);

  void set_highlight_potential_token_purchases(bool val) {
    highlight_potential_token_purchases_ = val;
  }

 private:
  struct ButtonDef_;
  struct Button_;
  struct TextDef_;
  struct ImageDef_;
  struct Text_;
  struct Image_;
  struct ChestSlot_;
  enum class MeterType_ { kLevel, kTrophy, kTickets, kTokens };
  enum class VAlign_ { kTop, kCenter, kBottom };

  auto GetTimeStr_(seconds_t diff, bool animating) -> std::string;
  void UpdateChests_();
  void UpdateTokensMeterText_();
  void UpdateForFocusedWindow_(Widget* widget);
  auto AddButton_(const ButtonDef_& def) -> Button_*;
  auto AddText_(const TextDef_& def) -> Text_*;
  auto AddImage_(const ImageDef_& def) -> Image_*;
  void StepChildWidgets_(seconds_t dt);
  void StepChests_(base::RenderPass* renderpass, seconds_t dt);
  void StepLeagueRank_(base::RenderPass* renderpass, seconds_t dt);
  void StepInbox_(base::RenderPass* renderpass, seconds_t dt);
  void StepTicketsMeter_(base::RenderPass* renderpass, seconds_t dt);
  void StepTokensMeter_(base::RenderPass* renderpass, seconds_t dt);
  void AddMeter_(MeterType_ type, float h_align, float r, float g, float b,
                 bool plus, const std::string& s);
  void UpdateTokensMeterTextColor_();
  void ShowTrophyMeterAnnotation_(const std::string& val,
                                  const Vector3f& color);
  void HideTrophyMeterAnnotation_();
  void UpdateLeagueRankDisplay_();
  void UpdateInboxDisplay_();
  auto ColorForLeagueValue_(const std::string& value) -> Vector3f;
  void SetInboxCountValue_(int count, bool is_max);
  void Update_(base::RenderPass* pass);
  void UpdateTicketsMeterTextColor_();

  std::map<std::string, ChestSlot_> chest_slots_;
  Object::Ref<base::AppTimer> trophy_meter_annotation_timer_;
  Object::Ref<base::AppTimer> trophy_meter_display_timer_;
  Object::Ref<base::AppTimer> inbox_display_timer_;
  std::string time_suffix_hours_;
  std::string time_suffix_minutes_;
  std::string time_suffix_seconds_;
  std::string league_type_vis_value_;
  std::string league_type_value_;
  std::string inbox_announce_text_str_;
  std::string open_me_text_;
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
  Button_* chest_backing_{};
  Image_* trophy_icon_{};
  Image_* tickets_meter_icon_{};
  Image_* tokens_meter_icon_{};
  Image_* inbox_count_backing_{};
  Text_* squad_size_text_{};
  Text_* account_name_text_{};
  Text_* tickets_meter_text_{};
  Text_* tokens_meter_text_{};
  Text_* league_rank_text_{};
  Text_* achievement_percent_text_{};
  Text_* level_text_{};
  Text_* xp_text_{};
  Text_* inbox_count_text_{};
  Text_* inbox_announce_text_{};
  Text_* trophy_meter_annotation_text_{};
  seconds_t update_pause_total_time_{};
  seconds_t last_chests_step_time_{-1.0f};
  seconds_t update_time_{};
  seconds_t league_rank_anim_start_time_{};
  seconds_t inbox_anim_flash_time_{};
  seconds_t tickets_anim_start_time_{};
  seconds_t tickets_anim_end_time_{};
  seconds_t tokens_anim_start_time_{};
  seconds_t tokens_anim_end_time_{};
  seconds_t last_draw_display_time_{};
  float base_scale_{1.0f};
  float bottom_left_height_{};
  float league_rank_anim_val_{};
  int league_rank_vis_value_{-1};
  int league_rank_value_{-1};
  int league_rank_anim_start_val_{};
  int league_number_vis_value_{-1};
  int league_number_value_{-1};
  int inbox_count_vis_value_{-1};
  int inbox_count_value_{-1};
  int tickets_meter_value_{-1};
  int tickets_meter_vis_value_{-1};
  int tokens_meter_value_{-1};
  int tokens_meter_vis_value_{-1};
  int tickets_anim_start_value_{};
  int tickets_anim_end_value_{};
  int tokens_anim_start_value_{};
  int tokens_anim_end_value_{};
  std::optional<uint32_t> league_rank_anim_sound_play_id_{};
  std::optional<uint32_t> chest_unlock_time_anim_sound_play_id_{};
  std::optional<uint32_t> tickets_anim_sound_play_id_{};
  std::optional<uint32_t> tokens_anim_sound_play_id_{};
  ToolbarVisibility toolbar_visibility_{ToolbarVisibility::kInGame};
  bool child_widgets_dirty_{true};
  bool in_main_menu_{};
  bool gold_pass_{};
  bool have_live_values_{};
  bool translations_dirty_{true};
  bool league_rank_animating_{};
  bool inbox_animating_{};
  bool inbox_count_is_max_vis_value_{};
  bool inbox_count_is_max_value_{};
  bool tickets_meter_live_display_dirty_{};
  bool tokens_meter_live_display_dirty_{};
  bool tickets_meter_animating_{};
  bool tokens_meter_animating_{};
  bool highlight_potential_token_purchases_{};

  static int update_pause_count_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
