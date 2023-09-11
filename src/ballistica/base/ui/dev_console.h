// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_DEV_CONSOLE_H_
#define BALLISTICA_BASE_UI_DEV_CONSOLE_H_

#include <list>
#include <string>
#include <utility>

#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

class DevConsole {
 public:
  DevConsole();
  ~DevConsole();
  auto IsActive() const -> bool { return (state_ != State_::kInactive); }
  auto HandleTextEditing(const std::string& text) -> bool;
  auto HandleKeyPress(const SDL_Keysym* keysym) -> bool;
  auto HandleKeyRelease(const SDL_Keysym* keysym) -> bool;
  auto transition_start() const -> millisecs_t { return transition_start_; }

  /// Toggle between mini, fullscreen, and inactive.
  void ToggleState();

  /// Tell the console to quietly go away no matter what state it is in.
  void Dismiss();

  /// Print text to the console.
  void Print(const std::string& s_in);
  void Draw(RenderPass* pass);

  /// Called when the console should start accepting Python command input.
  void EnableInput();

  auto input_string() const {
    assert(g_base->InLogicThread());
    return input_string_;
  }
  void set_input_string(const std::string& val);

  void InputAdapterFinish();

  auto HandleMouseDown(int button, float x, float y) -> bool;
  void HandleMouseUp(int button, float x, float y);
  void Exec();

 private:
  class Button_;
  class Line_;
  enum class State_ { kInactive, kMini, kFull };
  auto Bottom_() const -> float;
  auto PythonConsoleBaseScale_() const -> float;
  void SubmitCommand_(const std::string& command);
  void InvokeStringEditor_();
  ImageMesh bg_mesh_;
  ImageMesh stripe_mesh_;
  ImageMesh shadow_mesh_;
  TextGroup built_text_group_;
  TextGroup title_text_group_;
  TextGroup prompt_text_group_;
  TextGroup input_text_group_;
  millisecs_t last_input_text_change_time_{};
  bool input_text_dirty_{true};
  double transition_start_{};
  State_ state_{State_::kInactive};
  State_ state_prev_{State_::kInactive};
  bool input_enabled_{};
  std::string input_string_;
  std::list<std::string> input_history_;
  int input_history_position_{};
  std::list<Line_> lines_;
  std::string last_line_;
  Object::Ref<TextGroup> last_line_mesh_group_;
  bool last_line_mesh_dirty_{true};
  bool python_console_pressed_{};
  PythonRef string_edit_adapter_;
  std::list<Button_> buttons_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_DEV_CONSOLE_H_
