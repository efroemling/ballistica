// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_

#include <list>
#include <string>

#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// Root-level widget; contains a top-bar, screen-stack, bottom-bar, menu-button,
// etc. This is intended to replace RootUI.
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
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto GetSpecialWidget(const std::string& s) const -> Widget*;
  auto base_scale() const -> float { return base_scale_; }
  auto overlay_window_stack() const -> StackWidget* {
    return overlay_stack_widget_;
  }

 private:
  struct ButtonDef;
  struct Button;
  struct TextDef;
  struct Text;
  enum class VAlign { kTop, kCenter, kBottom };
  void UpdateForFocusedWindow(Widget* widget);
  void OnCancelCustom() override;
  void UpdateLayout() override;
  auto AddButton(const ButtonDef& def) -> Button*;
  auto AddText(const TextDef& def) -> Text*;
  void StepPositions(float dt);
  void AddMeter(float h_align, float x, int type, float r, float g, float b,
                bool plus, const std::string& s);
  auto AddCover(float h_align, VAlign v_align, float x, float y, float w,
                float h, float o) -> Button*;
  StackWidget* screen_stack_widget_{};
  StackWidget* overlay_stack_widget_{};
  float base_scale_{1.0f};
  std::list<Button> buttons_;
  std::list<Text> texts_;
  bool positions_dirty_{true};
  millisecs_t update_time_{};
  bool in_main_menu_{};
  Button* back_button_{};
  Button* account_button_{};
  Button* tickets_plus_button_{};
  Button* tickets_info_button_{};
  Button* settings_button_{};
  Button* menu_button_{};
  Button* party_button_{};
  ToolbarVisibility toolbar_visibility_{ToolbarVisibility::kInGame};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_ROOT_WIDGET_H_
