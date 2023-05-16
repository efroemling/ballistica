// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_SUPPORT_ROOT_UI_H_
#define BALLISTICA_UI_V1_SUPPORT_ROOT_UI_H_

#include "ballistica/base/graphics/support/frame_def.h"

namespace ballistica::ui_v1 {

/// Manages root level UI such as the menu button, party button, etc.
/// This is set to be replaced by RootWidget.
class RootUI {
 public:
  RootUI();
  virtual ~RootUI();
  void Draw(base::FrameDef* frame_def);

  auto HandleMouseButtonDown(float x, float y) -> bool;
  void HandleMouseButtonUp(float x, float y);
  void HandleMouseMotion(float x, float y);
  void set_party_window_open(bool val) { party_window_open_ = val; }
  auto party_window_open() const -> bool { return party_window_open_; }
  void set_always_draw_party_icon(bool val) { always_draw_party_icon_ = val; }
  auto always_draw_party_icon() const -> bool {
    return always_draw_party_icon_;
  }
  void TogglePartyWindowKeyPress();
  void ActivatePartyIcon() const;

 private:
  millisecs_t last_menu_button_press_time_{};
  millisecs_t menu_update_time_{};
  bool menu_button_pressed_{};
  float menu_button_size_{};
  bool menu_button_hover_{};
  float menu_fade_{};
  bool party_window_open_{};
  bool always_draw_party_icon_{};
  float connected_client_extra_offset_smoothed_{};
  Object::Ref<base::TextGroup> party_button_text_group_;
  Object::Ref<base::TextGroup> party_size_text_group_;
  int party_size_text_group_num_{-1};
  Object::Ref<base::TextGroup> start_a_game_text_group_;
  float start_a_game_text_scale_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_SUPPORT_ROOT_UI_H_
