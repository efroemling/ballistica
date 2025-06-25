// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_DEV_CONSOLE_H_
#define BALLISTICA_BASE_UI_DEV_CONSOLE_H_

#include <list>
#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/graphics/mesh/image_mesh.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector4f.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

/// Where on the overlay-front-pass we draw.
const float kDevConsoleZDepth = 0.0f;

class DevConsole {
 public:
  DevConsole();
  auto IsActive() const -> bool { return (state_ != State_::kInactive); }
  auto HandleTextEditing(const std::string& text) -> bool;
  auto HandleKeyPress(const SDL_Keysym* keysym) -> bool;
  auto HandleKeyRelease(const SDL_Keysym* keysym) -> bool;
  auto transition_start() const -> millisecs_t { return transition_start_; }

  /// Toggle between mini, fullscreen, and inactive.
  void CycleState(bool backwards = false);

  /// Tell the console to quietly go away no matter what state it is in.
  void Dismiss();

  /// Attempt to Paste. Returns true if it happened.
  auto PasteFromClipboard() -> bool;

  /// Print text to the console.
  void Print(const std::string& s_in, float scale, Vector4f color);
  void Draw(FrameDef* frame_def);

  void ApplyAppConfig();
  void StepDisplayTime();

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
  void HandleMouseCancel(int button, float x, float y);
  void Exec();
  void CopyHistory();

  void AddButton(const char* label, float x, float y, float width, float height,
                 PyObject* call, const char* h_anchor_str, float label_scale,
                 float corner_radius, const char* style_str, bool disabled);
  void AddText(const char* text, float x, float y, const char* h_anchor_str,
               const char* h_align_str, const char* v_align_str, float scale,
               const char* style_str);
  void AddPythonTerminal();

  auto Width() -> float;
  auto Height() -> float;
  auto BaseScale() const -> float;
  void RequestRefresh();

  void OnUIScaleChanged();

 private:
  class ScopedUILock_;
  class Widget_;
  class Button_;
  class Text_;
  class ToggleButton_;
  class TabButton_;
  class OutputLine_;
  enum class State_ : uint8_t { kInactive, kMini, kFull };

  auto CaratCharValid_() -> bool;
  auto GetCaratX_() -> float;
  void UpdateCarat_();
  auto Bottom_() const -> float;
  void SubmitPythonCommand_(const std::string& command);
  void InvokeStringEditor_();
  void RefreshCloseButton_();
  void RefreshTabButtons_();
  void RefreshTabContents_();
  void SaveActiveTab_();

  int input_history_position_{};
  int ui_lock_count_{};
  int carat_char_{};
  State_ state_{State_::kInactive};
  State_ state_prev_{State_::kInactive};
  bool input_text_dirty_{true};
  bool input_enabled_{};
  bool python_terminal_visible_{};
  bool python_terminal_pressed_{};
  bool refresh_pending_{};
  bool carat_dirty_{true};
  float carat_x_{};
  float last_virtual_res_x_{-1.0f};
  float last_virtual_res_y_{-1.0f};
  seconds_t last_virtual_res_change_time_{};
  seconds_t transition_start_{};
  millisecs_t last_carat_x_change_time_{};
  ImageMesh bg_mesh_;
  ImageMesh stripe_mesh_;
  ImageMesh border_mesh_;
  TextGroup built_text_group_;
  TextGroup title_text_group_;
  TextGroup prompt_text_group_;
  TextGroup input_text_group_;
  std::string input_string_;
  std::vector<std::string> tabs_;
  std::string active_tab_;
  PythonRef string_edit_adapter_;
  std::list<std::string> input_history_;
  std::list<OutputLine_> output_lines_;
  std::unique_ptr<Widget_> close_button_;
  std::vector<std::unique_ptr<Widget_> > widgets_;
  std::vector<std::unique_ptr<Widget_> > tab_buttons_;
  Object::Ref<Repeater> key_repeater_;
  Object::Ref<NinePatchMesh> carat_mesh_;
  Object::Ref<NinePatchMesh> carat_glow_mesh_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_DEV_CONSOLE_H_
