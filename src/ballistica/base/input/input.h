// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_INPUT_H_
#define BALLISTICA_BASE_INPUT_INPUT_H_

#include <list>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/foundation/types.h"

namespace ballistica::base {

/// Input subsystem. Mostly operates in the logic thread.
class Input {
 public:
  Input();

  void OnAppStart();
  void OnAppSuspend();
  void OnAppUnsuspend();
  void OnAppShutdown();
  void OnAppShutdownComplete();
  void StepDisplayTime();

  void DoApplyAppConfig();

  void OnScreenSizeChange();

  // Add an input device. Must be called from the logic thread; otherwise use
  // PushAddInputDeviceCall.
  void AddInputDevice(InputDevice* device, bool standard_message);

  // Removes a previously-added input-device. Must be called from the
  // logic thread; otherwise use PushRemoveInputDeviceCall.
  void RemoveInputDevice(InputDevice* input, bool standard_message);

  // Given a device name and persistent identifier for it, returns a device or
  // nullptr. Note that this can return hidden devices (ones the user has
  // flagged as totally-ignored, etc).
  auto GetInputDevice(const std::string& name, const std::string& persistent_id)
      -> InputDevice*;

  // Return a device by id, or nullptr for an invalid id. Note that this can
  // return hidden devices (ones the user has flagged as totally-ignored, etc).
  auto GetInputDevice(int id) -> InputDevice*;

  // Return all input devices with this name.
  auto GetInputDevicesWithName(const std::string& name)
      -> std::vector<InputDevice*>;

  /// Release all held buttons/keys/etc. For use when directing input
  /// to a new target (from in-game to UI, etc.) so that old targets
  /// don't get stuck moving/etc. Should come up with a more elegant
  /// way to handle this situation.
  void ResetHoldStates();

  void Reset();
  void LockAllInput(bool permanent, const std::string& label);
  void UnlockAllInput(bool permanent, const std::string& label);
  auto IsInputLocked() const -> bool {
    return input_lock_count_temp_ > 0 || input_lock_count_permanent_ > 0;
  }
  auto cursor_pos_x() const -> float { return cursor_pos_x_; }
  auto cursor_pos_y() const -> float { return cursor_pos_y_; }

  auto IsCursorVisible() const -> bool;

  // Return list of gamepads that are user-visible and able to be configured.
  auto GetConfigurableGamePads() -> std::vector<InputDevice*>;

  // Reset all keyboard keys to a non-held state and deal out associated
  // messages - used before switching keyboard focus to a new context
  // so that the old one is not stuck with a held key forever.
  void ResetKeyboardHeldKeys();

  // Same idea but for joysticks.
  void ResetJoyStickHeldButtons();
  auto ShouldCompletelyIgnoreInputDevice(InputDevice* input_device) -> bool;

  auto touch_input() const -> TouchInput* { return touch_input_; }
  auto have_non_touch_inputs() const -> bool { return have_non_touch_inputs_; }
  auto have_button_using_inputs() const -> bool {
    return have_button_using_inputs_;
  }
  auto have_start_activated_default_button_inputs() const -> bool {
    return have_start_activated_default_button_inputs_;
  }
  void Draw(FrameDef* frame_def);

  // Get the total idle time for the system.
  // FIXME - should better coordinate this with InputDevice::getLastUsedTime().
  // auto GetIdleTime() const -> millisecs_t;

  // Should be called whenever user-input of some form comes through.
  // void ResetIdleTime() { last_input_time_ = GetAppTimeMillisecs(); }
  auto MarkInputActive() { input_active_ = true; }

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
  auto keyboard_input() const -> KeyboardInput* { return keyboard_input_; }
  auto keyboard_input_2() const -> KeyboardInput* { return keyboard_input_2_; }
  // void CreateTouchInput();

  void PushTextInputEvent(const std::string& text);
  void PushKeyPressEventSimple(int keycode);
  void PushKeyReleaseEventSimple(int keycode);
  void PushKeyPressEvent(const SDL_Keysym& keysym);
  void PushKeyReleaseEvent(const SDL_Keysym& keysym);
  void PushMouseDownEvent(int button, const Vector2f& position);
  void PushMouseUpEvent(int button, const Vector2f& position);
  void PushMouseMotionEvent(const Vector2f& position);
  void PushSmoothMouseScrollEvent(const Vector2f& velocity, bool momentum);
  void PushMouseScrollEvent(const Vector2f& amount);
  void PushJoystickEvent(const SDL_Event& event, InputDevice* input_device);
  void PushAddInputDeviceCall(InputDevice* input_device, bool standard_message);
  void PushRemoveInputDeviceCall(InputDevice* input_device,
                                 bool standard_message);
  void PushTouchEvent(const TouchEvent& touch_event);
  void PushDestroyKeyboardInputDevices();
  void PushCreateKeyboardInputDevices();
  void LsInputDevices();

  /// Roughly how long in milliseconds have all input devices been idle.
  auto input_idle_time() const { return input_idle_time_; }

  typedef bool(HandleJoystickEventCall)(const SDL_Event& event,
                                        InputDevice* input_device);
  typedef bool(HandleKeyPressCall)(const SDL_Keysym& keysym);
  typedef bool(HandleKeyReleaseCall)(const SDL_Keysym& keysym);

  void CaptureKeyboardInput(HandleKeyPressCall* press_call,
                            HandleKeyReleaseCall* release_call);
  void ReleaseKeyboardInput();

  void CaptureJoystickInput(HandleJoystickEventCall* call);
  void ReleaseJoystickInput();
  void RebuildInputDeviceDelegates();

 private:
  void UpdateInputDeviceCounts_();
  auto GetNewNumberedIdentifier_(const std::string& name,
                                 const std::string& identifier) -> int;
  void AnnounceConnects_();
  void AnnounceDisconnects_();
  void HandleKeyPressSimple_(int keycode);
  void HandleKeyReleaseSimple_(int keycode);
  void HandleKeyPress_(const SDL_Keysym& keysym);
  void HandleKeyRelease_(const SDL_Keysym& keysym);
  void HandleMouseMotion_(const Vector2f& position);
  void HandleMouseDown_(int button, const Vector2f& position);
  void HandleMouseUp_(int button, const Vector2f& position);
  void HandleMouseScroll_(const Vector2f& amount);
  void HandleSmoothMouseScroll_(const Vector2f& velocity, bool momentum);
  void HandleJoystickEvent_(const SDL_Event& event, InputDevice* input_device);
  void HandleTouchEvent_(const TouchEvent& e);
  void ShowStandardInputDeviceConnectedMessage_(InputDevice* j);
  void ShowStandardInputDeviceDisconnectedMessage_(InputDevice* j);
  void PrintLockLabels_();
  void UpdateModKeyStates_(const SDL_Keysym* keysym, bool press);
  void CreateKeyboardInputDevices_();
  void DestroyKeyboardInputDevices_();
  void AddFakeMods_(SDL_Keysym* sym);

  int connect_print_timer_id_{};
  int disconnect_print_timer_id_{};
  int max_controller_count_so_far_{};
  int local_active_input_device_count_{};
  int mouse_move_count_{};
  int input_lock_count_temp_{};
  int input_lock_count_permanent_{};
  bool input_active_{};
  bool have_button_using_inputs_{};
  bool have_start_activated_default_button_inputs_{};
  bool have_non_touch_inputs_{};
  millisecs_t input_idle_time_{};
  millisecs_t last_get_local_active_input_device_count_check_time_{};
  float cursor_pos_x_{};
  float cursor_pos_y_{};
  millisecs_t last_click_time_{};
  millisecs_t double_click_time_{200};
  seconds_t last_mouse_move_time_{};
  std::list<std::string> input_lock_temp_labels_;
  std::list<std::string> input_unlock_temp_labels_;
  std::list<std::string> input_lock_permanent_labels_;
  std::list<std::string> input_unlock_permanent_labels_;
  std::list<std::string> recent_input_locks_unlocks_;
  std::list<std::string> newly_connected_controllers_;
  std::list<std::string> newly_disconnected_controllers_;
  std::unordered_map<std::string, std::unordered_map<std::string, int> >
      reserved_identifiers_;
  std::vector<Object::Ref<InputDevice> > input_devices_;
  std::set<int> keys_held_;
  millisecs_t last_input_device_count_update_time_{};
  millisecs_t last_input_temp_lock_time_{};
  void* single_touch_{};
  KeyboardInput* keyboard_input_{};
  KeyboardInput* keyboard_input_2_{};
  TouchInput* touch_input_{};
  HandleKeyPressCall* keyboard_input_capture_press_{};
  HandleKeyReleaseCall* keyboard_input_capture_release_{};
  HandleJoystickEventCall* joystick_input_capture_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_INPUT_H_
