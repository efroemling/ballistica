// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_H_
#define BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_H_

#include <string>
#include <vector>

#include "ballistica/base/input/device/input_device_delegate.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// Base class for game input devices (keyboard, gamepads, etc).
/// InputDevices can be allocated in any thread (generally on the main
/// thread in response to some system event). An AddInputDevice() call
/// should then be pushed to the logic thread to inform it of the new
/// device. Deletion of the input-device is then handled by the logic
/// thread and can be triggered by pushing a RemoveInputDevice() call
/// to it.
class InputDevice : public Object {
 public:
  InputDevice();
  ~InputDevice() override;

  /// Request a player in the local game for this device.
  void RequestPlayer();

  auto AttachedToPlayer() const -> bool;
  void DetachFromPlayer();

  /// Pass some input command on to whatever we're controlling
  /// (player or remote-player).
  void InputCommand(InputType type, float value = 0.0f);

  /// Return the (not necessarily unique) name of the input device.
  auto GetDeviceName() -> std::string;

  /// Called during the game loop - for manual button repeats, etc.
  virtual void Update();

  virtual void ResetHeldStates();

  /// Return the name of the button used to evoke the party menu from UIs.
  virtual auto GetPartyButtonName() const -> std::string;

  /// Returns a number specific to this device type (saying this is the Nth
  /// device of this type).
  auto device_number() const -> int { return number_; }
  auto GetPersistentIdentifier() const -> std::string;

  /// Return the overall device index; unique among all devices.
  auto index() const -> int { return index_; }
  void set_index(int index_in) { index_ = index_in; }

  /// Our number specific to our type.
  auto number() const { return number_; }
  void set_number(int n) { number_ = n; }

  /// Read and apply new control values from config.
  virtual void UpdateMapping() {}

#if BA_SDL_BUILD || BA_MINSDL_BUILD
  virtual void HandleSDLEvent(const SDL_Event* e) {}
#endif
  virtual auto GetAllowsConfiguring() -> bool { return true; }

  virtual auto IsController() -> bool { return false; }
  virtual auto IsSDLController() -> bool { return false; }
  virtual auto IsTouchScreen() -> bool { return false; }
  virtual auto IsRemoteControl() -> bool { return false; }
  virtual auto IsTestInput() -> bool { return false; }
  virtual auto IsKeyboard() -> bool { return false; }
  virtual auto IsMFiController() -> bool { return false; }
  virtual auto IsLocal() -> bool { return true; }
  virtual auto IsUIOnly() -> bool { return false; }
  virtual auto IsRemoteApp() -> bool { return false; }

  /// Return a human-readable name for a button/key.
  virtual auto GetButtonName(int index) -> std::string;

  /// Return a human-readable name for an axis.
  virtual auto GetAxisName(int index) -> std::string;

  /// Return whether button-names returned by GetButtonName() for this
  /// device are identifiable to the user on the input-device itself.
  /// For example, if a gamepad returns 'A', 'B', 'X', 'Y', etc. as names,
  /// this should return true, but if it returns 'button 123', 'button 124',
  /// etc. then it should return false.
  virtual auto HasMeaningfulButtonNames() -> bool;

  /// Should return true if the input device has a start button and
  /// that button activates default widgets (will cause a start icon to show up
  /// on them).
  virtual auto start_button_activates_default_widget() -> bool { return false; }
  auto last_input_time_millisecs() const -> millisecs_t {
    return last_input_time_millisecs_;
  }
  virtual auto ShouldBeHiddenFromUser() -> bool;

  /// Return a human-readable name for the device's type.
  /// This is used for display and also for storing configs/etc.
  virtual auto GetRawDeviceName() -> std::string { return "Input Device"; }

  /// Return any extra description for the device.
  /// This portion is only used for display and not for storing configs.
  /// An example is Mac PS3 controllers; they return "(bluetooth)" or "(usb)"
  /// here depending on how they are connected.
  virtual auto GetDeviceExtraDescription() -> std::string { return ""; }

  /// Devices that have a way of identifying uniquely against other devices of
  /// the same type (a serial number, usb-port, etc) should return that here as
  /// a string.
  virtual auto GetDeviceIdentifier() -> std::string { return ""; }

  /// Called for all devices in the logic thread when they've successfully
  /// been added to the input-device list, have a valid ID, name, etc.
  virtual void OnAdded() {}

  void UpdateLastInputTime();

  auto delegate() -> InputDeviceDelegate& {
    // TEMP - Tracking down a crash in the wild.
    // Delegate should always exist any time we're accessing it.
    if (!delegate_.Exists()) {
      FatalError("Input-device delegate unexpectedly invalid.");
    }
    return *delegate_;
  }
  auto set_delegate(const Object::Ref<InputDeviceDelegate>& delegate) {
    delegate_ = delegate;
  }

  /// Provide a custom player-name that the game can choose to honor.
  /// This is used by the remote app.
  auto custom_default_player_name() const -> std::string {
    return custom_default_player_name_;
  }
  void set_custom_default_player_name(const std::string& val) {
    custom_default_player_name_ = val;
  }

 private:
  Object::Ref<InputDeviceDelegate> delegate_;

  // note: this is in base-net-time
  millisecs_t last_input_time_millisecs_{};

  int index_{-1};   // Our overall device index.
  int number_{-1};  // Our type-specific number.

  std::string custom_default_player_name_;

  BA_DISALLOW_CLASS_COPIES(InputDevice);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_H_
