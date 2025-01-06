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

  void UpdateLayout() override;
  void SetSquadSizeLabel(int val);
  void SetAccountState(bool signed_in, const std::string& name);

  void SetTicketsMeterText(const std::string& val);
  void SetTokensMeterText(const std::string& val, bool gold_pass);
  void SetLeagueRankText(const std::string& val);
  void SetLeagueType(const std::string& val);
  void SetAchievementPercentText(const std::string& val);
  void SetLevelText(const std::string& val);
  void SetXPText(const std::string& val);
  void SetInboxCountText(const std::string& val);
  void SetChests(const std::string& chest_0_appearance,
                 const std::string& chest_1_appearance,
                 const std::string& chest_2_appearance,
                 const std::string& chest_3_appearance);
  void SetHaveLiveValues(bool have_live_values);

  auto bottom_left_height() const { return bottom_left_height_; }

 private:
  struct ButtonDef_;
  struct Button_;
  struct TextDef_;
  struct ImageDef_;
  struct Text_;
  struct Image_;
  enum class MeterType_ { kLevel, kTrophy, kTickets, kTokens };
  enum class VAlign_ { kTop, kCenter, kBottom };

  void UpdateChests_();
  void UpdateTokensMeterText_();
  void UpdateForFocusedWindow_(Widget* widget);
  auto AddButton_(const ButtonDef_& def) -> Button_*;
  auto AddText_(const TextDef_& def) -> Text_*;
  auto AddImage_(const ImageDef_& def) -> Image_*;
  void StepChildWidgets_(float dt);
  void AddMeter_(MeterType_ type, float h_align, float r, float g, float b,
                 bool plus, const std::string& s);
  void UpdateTokensMeterTextColor_();

  std::string chest_0_appearance_;
  std::string chest_1_appearance_;
  std::string chest_2_appearance_;
  std::string chest_3_appearance_;
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
  float base_scale_{1.0f};
  float bottom_left_height_{};
  millisecs_t update_time_{};
  ToolbarVisibility toolbar_visibility_{ToolbarVisibility::kInGame};
  bool child_widgets_dirty_{true};
  bool in_main_menu_{};
  bool gold_pass_{};
  bool have_live_values_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
