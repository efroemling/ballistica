// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INPUT_INPUT_H_
#define BALLISTICA_INPUT_INPUT_H_

#include <list>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

/// Class for managing input.
/// Should only be used in the logic thread unless otherwise specified.
class Input {
 public:
  Input();

  // Add an input device. Must be called from the logic thread; otherwise use
  // PushAddInputDeviceCall.
  auto AddInputDevice(InputDevice* input, bool standard_message) -> void;

  // Removes a previously-added input-device. Must be called from the
  // logic thread; otherwise use PushRemoveInputDeviceCall.
  auto RemoveInputDevice(InputDevice* input, bool standard_message) -> void;

  // Given a device name and persistent identifier for it, returns a device or
  // nullptr note that this can return hidden devices (ones the user has flagged
  // as totally-ignored, etc).
  auto GetInputDevice(const std::string& name, const std::string& persistent_id)
      -> InputDevice*;

  // Return a device by id.
  // Note that this can return hidden devices (ones the user has flagged as
  // totally-ignored, etc).
  auto GetInputDevice(int id) -> InputDevice*;

  // Return all input devices with this name.
  auto GetInputDevicesWithName(const std::string& name)
      -> std::vector<InputDevice*>;

  auto Reset() -> void;
  auto LockAllInput(bool permanent, const std::string& label) -> void;
  auto UnlockAllInput(bool permanent, const std::string& label) -> void;
  auto IsInputLocked() const -> bool {
    return ((input_lock_count_temp_ > 0) || (input_lock_count_permanent_ > 0));
  }
  auto cursor_pos_x() const -> float { return cursor_pos_x_; }
  auto cursor_pos_y() const -> float { return cursor_pos_y_; }

  auto IsCursorVisible() const -> bool;

  // Return list of gamepads that are user-visible and able to be configured.
  auto GetConfigurableGamePads() -> std::vector<InputDevice*>;

  // Reset all keyboard keys to a non-held state and deal out associated
  // messages - used before switching keyboard focus to a new context
  // so that the old one is not stuck with a held key forever.
  auto ResetKeyboardHeldKeys() -> void;

  auto GetKeyName(int keycode) -> std::string;

  // Same idea but for joysticks.
  auto ResetJoyStickHeldButtons() -> void;
  auto ShouldCompletelyIgnoreInputDevice(InputDevice* input_device) -> bool;
  auto ApplyAppConfig() -> void;

  auto touch_input() const -> TouchInput* { return touch_input_; }
  auto have_non_touch_inputs() const -> bool { return have_non_touch_inputs_; }
  auto have_button_using_inputs() const -> bool {
    return have_button_using_inputs_;
  }
  auto have_start_activated_default_button_inputs() const -> bool {
    return have_start_activated_default_button_inputs_;
  }
  auto Draw(FrameDef* frame_def) -> void;

  // Get the total idle time for the system.
  // FIXME - should better coordinate this with InputDevice::getLastUsedTime().
  // auto GetIdleTime() const -> millisecs_t;

  // Should be called whenever user-input of some form comes through.
  // auto ResetIdleTime() -> void { last_input_time_ = GetRealTime(); }
  auto mark_input_active() { input_active_ = true; }

  // Should be called regularly to update button repeats, etc.
  auto Update() -> void;

  // returns true if more than one non-keyboard device has been active recently
  // ..this is used to determine whether we need to have strict menu ownership
  // (otherwise menu use would be chaotic with 8 players connected)
  auto HaveManyLocalActiveInputDevices() -> bool {
    return GetLocalActiveInputDeviceCount() > 1;
  }
  auto GetLocalActiveInputDeviceCount() -> int;

  // Return true if there are any joysticks with players attached.
  // The touch-input uses this to warn the user if it looks like they
  // may have accidentally joined the game using a controller touchpad or
  // something.
  auto HaveControllerWithPlayer() -> bool;
  auto HaveRemoteAppController() -> bool;
  auto HandleBackPress(bool from_toolbar) -> void;
  auto ProcessStressTesting(int player_count) -> void;
  auto keyboard_input() const -> KeyboardInput* { return keyboard_input_; }
  auto keyboard_input_2() const -> KeyboardInput* { return keyboard_input_2_; }
  auto CreateTouchInput() -> void;

  auto PushTextInputEvent(const std::string& text) -> void;
  auto PushKeyPressEvent(const SDL_Keysym& keysym) -> void;
  auto PushKeyReleaseEvent(const SDL_Keysym& keysym) -> void;
  auto PushMouseDownEvent(int button, const Vector2f& position) -> void;
  auto PushMouseUpEvent(int button, const Vector2f& position) -> void;
  auto PushMouseMotionEvent(const Vector2f& position) -> void;
  auto PushSmoothMouseScrollEvent(const Vector2f& velocity, bool momentum)
      -> void;
  auto PushMouseScrollEvent(const Vector2f& amount) -> void;
  auto PushJoystickEvent(const SDL_Event& event, InputDevice* input_device)
      -> void;
  auto PushAddInputDeviceCall(InputDevice* input_device, bool standard_message)
      -> void;
  auto PushRemoveInputDeviceCall(InputDevice* input_device,
                                 bool standard_message) -> void;
  auto PushTouchEvent(const TouchEvent& touch_event) -> void;
  auto PushDestroyKeyboardInputDevices() -> void;
  auto PushCreateKeyboardInputDevices() -> void;

  /// Roughly how long in milliseconds have all input devices been idle.
  auto input_idle_time() const { return input_idle_time_; }

 private:
  auto UpdateInputDeviceCounts() -> void;
  auto GetNewNumberedIdentifier(const std::string& name,
                                const std::string& identifier) -> int;
  auto UpdateEnabledControllerSubsystems() -> void;
  auto AnnounceConnects() -> void;
  auto AnnounceDisconnects() -> void;
  auto HandleKeyPress(const SDL_Keysym* keysym) -> void;
  auto HandleKeyRelease(const SDL_Keysym* keysym) -> void;
  auto HandleMouseMotion(const Vector2f& position) -> void;
  auto HandleMouseDown(int button, const Vector2f& position) -> void;
  auto HandleMouseUp(int button, const Vector2f& position) -> void;
  auto HandleMouseScroll(const Vector2f& amount) -> void;
  auto HandleSmoothMouseScroll(const Vector2f& velocity, bool momentum) -> void;
  auto HandleJoystickEvent(const SDL_Event& event, InputDevice* input_device)
      -> void;
  auto HandleTouchEvent(const TouchEvent& e) -> void;
  auto ShowStandardInputDeviceConnectedMessage(InputDevice* j) -> void;
  auto ShowStandardInputDeviceDisconnectedMessage(InputDevice* j) -> void;
  auto PrintLockLabels() -> void;
  auto UpdateModKeyStates(const SDL_Keysym* keysym, bool press) -> void;
  auto CreateKeyboardInputDevices() -> void;
  auto DestroyKeyboardInputDevices() -> void;

  bool input_active_{};
  millisecs_t input_idle_time_{};
  int local_active_input_device_count_{};
  millisecs_t last_get_local_active_input_device_count_check_time_{};
  std::unordered_map<std::string, std::unordered_map<std::string, int> >
      reserved_identifiers_;
  int max_controller_count_so_far_{};
  std::list<std::string> newly_connected_controllers_;
  std::list<std::string> newly_disconnected_controllers_;
  int connect_print_timer_id_{};
  int disconnect_print_timer_id_{};
  bool have_button_using_inputs_{};
  bool have_start_activated_default_button_inputs_{};
  bool have_non_touch_inputs_{};
  float cursor_pos_x_{};
  float cursor_pos_y_{};
  // millisecs_t last_input_time_{};
  millisecs_t last_click_time_{};
  millisecs_t double_click_time_{200};
  millisecs_t last_mouse_move_time_{};
  int mouse_move_count_{};
  std::vector<Object::Ref<InputDevice> > input_devices_;
  KeyboardInput* keyboard_input_{};
  KeyboardInput* keyboard_input_2_{};
  TouchInput* touch_input_{};
  int input_lock_count_temp_{};
  int input_lock_count_permanent_{};
  std::list<std::string> input_lock_temp_labels_;
  std::list<std::string> input_unlock_temp_labels_;
  std::list<std::string> input_lock_permanent_labels_;
  std::list<std::string> input_unlock_permanent_labels_;
  std::list<std::string> recent_input_locks_unlocks_;
  std::set<int> keys_held_;
  millisecs_t last_input_device_count_update_time_{};
  millisecs_t last_input_temp_lock_time_{};
  bool ignore_mfi_controllers_{};
  bool ignore_sdl_controllers_{};
  std::list<TestInput*> test_inputs_;
  millisecs_t stress_test_time_{};
  millisecs_t stress_test_last_leave_time_{};
  void* single_touch_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_INPUT_INPUT_H_
