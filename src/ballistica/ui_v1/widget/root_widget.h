// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_

#include <list>
#include <string>

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

  /// Called when UIScale or screen dimensions change.
  void OnUIScaleChange();

  void UpdateLayout() override;

 private:
  struct ButtonDef;
  struct Button;
  struct TextDef;
  struct ImageDef;
  struct Text;
  struct Image;
  enum class MeterType { kLevel, kTrophy, kTickets, kTokens };
  enum class VAlign { kTop, kCenter, kBottom };
  void UpdateForFocusedWindow_(Widget* widget);
  auto AddButton_(const ButtonDef& def) -> Button*;
  auto AddText_(const TextDef& def) -> Text*;
  auto AddImage_(const ImageDef& def) -> Image*;
  void StepPositions_(float dt);
  void AddMeter_(MeterType type, float h_align, float r, float g, float b,
                 bool plus, const std::string& s);
  auto AddCover_(float h_align, VAlign v_align, float x, float y, float w,
                 float h, float o) -> Button*;
  ToolbarVisibility toolbar_visibility_{ToolbarVisibility::kInGame};
  StackWidget* screen_stack_widget_{};
  StackWidget* overlay_stack_widget_{};
  float base_scale_{1.0f};
  millisecs_t update_time_{};
  std::list<Button> buttons_;
  std::list<Text> texts_;
  std::list<Image> images_;
  std::vector<Button*> top_left_buttons_;
  std::vector<Button*> top_right_buttons_;
  std::vector<Button*> bottom_left_buttons_;
  std::vector<Button*> bottom_right_buttons_;
  bool positions_dirty_{true};
  bool in_main_menu_{};
  Button* back_button_{};
  Button* account_button_{};
  Button* achievements_button_{};
  Button* inbox_button_{};
  Button* tickets_meter_button_{};
  Button* tokens_meter_button_{};
  Button* trophy_meter_button_{};
  Button* settings_button_{};
  Button* store_button_{};
  Button* get_tokens_button_{};
  Button* inventory_button_{};
  Button* menu_button_{};
  Button* squad_button_{};
  Button* level_icon_{};
  Button* level_meter_button_{};
  Button* trophy_icon_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
