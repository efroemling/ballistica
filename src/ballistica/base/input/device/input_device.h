// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_H_
#define BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_H_

#include <memory>
#include <string>

#include "ballistica/base/input/device/feedback_event.h"
#include "ballistica/base/input/device/input_device_delegate.h"
#include "ballistica/base/support/lang_str.h"
#include "ballistica/shared/foundation/input_types.h"

namespace ballistica::base {

/// Base class for game input devices (keyboard, gamepads, etc).
/// InputDevices can be allocated in any thread (generally on the main
/// thread in response to some system event). An AddInputDevice() call
/// should then be pushed to the logic thread to inform it of the new
/// device. Deletion of the input-device is then handled by the logic thread
/// and can be triggered by pushing a RemoveInputDevice() call to it.
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

  /// Return the name of the input device. Generally devices of the same
  /// type will have the same name. This value is not translated so is
  /// suitable for storing configs/etc.
  auto GetDeviceName() -> std::string;

  /// Return the name of the input device incorporating persistent
  /// identifier. This value is not translated so it suitable for storing
  /// configs/etc.
  auto GetDeviceNameUnique() -> std::string;

  /// Return a (possibly translated) device name which *may* incorporate
  /// persistent identifier. Be aware that this may change over time - for
  /// example, a single connected game controller might return
  /// "FooController" here but if a second is connected it will then return
  /// "FooController #1". Use this when identifying the device to the user
  /// but never for storing configs/etc.
  auto GetDeviceNamePretty() -> std::string;

  /// A string unique among devices with the same name. Generally just a
  /// number symbol followed by its number() value, but do not make this
  /// assumption.
  auto GetPersistentIdentifier() const -> std::string;

  /// Request physical feedback (rumble/haptics) on this device.
  ///
  /// Haptic hardware has no notion of mixing: issuing a new effect
  /// *replaces* whatever is playing rather than layering onto it. So
  /// exactly one event owns the device at a time, and this arbitrates by
  /// the requesting types' priorities before handing anything to a
  /// backend.
  ///
  /// Deciding *which* device should feel something -- anything involving
  /// players, sessions, or the network -- belongs to the layer above.
  /// Call in the logic thread.
  void ApplyFeedback(const FeedbackEvent& event);

  /// Immediately stop any feedback in progress and forget arbiter state.
  /// Used when we might otherwise strand a motor running (app suspend,
  /// etc).
  void StopFeedback();

  /// Render a feedback event that has already won arbitration, and
  /// return how many milliseconds that render will take (0 if nothing
  /// was rendered or the platform gives no control over the length).
  ///
  /// Default does nothing, which is correct both for devices with no
  /// haptic hardware (keyboards, test inputs) and for proxies standing
  /// in for someone else's hardware.
  ///
  /// Treat each call as "play this now, replacing anything current"; the
  /// arbiter has already decided this event should be heard, so a
  /// backend needs no history of its own. How strong and how long are
  /// entirely the backend's decisions -- the returned length simply lets
  /// the arbiter avoid cutting the render short, so a backend needing
  /// longer than a type's hold_millisecs is free to take it rather than
  /// being truncated into imperceptibility.
  ///
  /// Called in the logic thread. A backend needing main-thread-only
  /// platform state must hop there itself, capturing an id rather than a
  /// pointer -- the device can be removed before the call runs.
  virtual auto DoApplyFeedback(const FeedbackEvent& event) -> int;

  /// Stop any in-progress feedback. Default does nothing.
  virtual void DoStopFeedback();

  /// Called during the game loop - for manual button repeats, etc.
  virtual void Update();

  virtual void ResetHeldStates();

  /// Return the name of the button used to evoke the party menu from UIs.
  virtual auto GetPartyButtonName() const -> std::string;

  /// Overall device index; unique among all devices.
  auto index() const -> int { return index_; }
  void set_index(int index_in) { index_ = index_in; }

  /// Our number among devices with the same name.
  auto number() const { return number_; }
  void set_number(int n) { number_ = n; }

  /// Read and apply new control values from config.
  virtual void ApplyAppConfig();

#if BA_SDL_BUILD || BA_MINSDL_BUILD
  virtual void HandleSDLEvent(const BAEvent* e);
#endif

  virtual auto GetAllowsConfiguring() -> bool;
  virtual auto IsController() -> bool;
  virtual auto IsSDLController() -> bool;
  virtual auto IsTouchScreen() -> bool;
  virtual auto IsRemoteControl() -> bool;
  virtual auto IsTestInput() -> bool;
  virtual auto IsKeyboard() -> bool;
  virtual auto IsMFiController() -> bool;
  virtual auto IsLocal() -> bool;
  virtual auto IsUIOnly() -> bool;
  virtual auto IsRemoteApp() -> bool;

  /// Return a human-readable name for a button/key.
  ///
  /// Returns a language-string rather than baked text so the name stays
  /// live across locale switches: the generic fallback ('Button 5') is a
  /// resource form, while device-supplied glyph names ('A', 'Space') are
  /// literal value forms shown as-is in every locale.
  virtual auto GetButtonName(int index) -> std::shared_ptr<const LangStr>;

  /// Return a human-readable name for an axis.
  virtual auto GetAxisName(int index) -> std::string;

  /// Return whether button-names returned by GetButtonName() for this
  /// device are identifiable to the user on the input-device itself. For
  /// example, if a gamepad returns 'A', 'B', 'X', 'Y', etc. as names, this
  /// should return true, but if it returns 'button 123', 'button 124', etc.
  /// then it should return false.
  virtual auto HasMeaningfulButtonNames() -> bool;

  /// Should return true if the input device has a start button and that
  /// button activates default widgets (will cause a start icon to show up
  /// on them).
  virtual auto start_button_activates_default_widget() -> bool;

  auto last_active_time_millisecs() const -> millisecs_t {
    return last_active_time_millisecs_;
  }
  virtual auto ShouldBeHiddenFromUser() -> bool;

  /// Return a human-readable name for the device's type. This is used for
  /// display and also for storing configs/etc. so should not be translated.
  virtual auto DoGetDeviceName() -> std::string;

  /// Called for all devices in the logic thread when they've successfully
  /// been added to the input-device list, have a valid ID, name, etc.
  virtual void OnAdded();

  void UpdateLastActiveTime();

  auto delegate() -> InputDeviceDelegate& {
    assert(delegate_.exists());
    return *delegate_;
  }
  auto set_delegate(const Object::Ref<InputDeviceDelegate>& delegate) {
    delegate_ = delegate;
  }

  /// Provide a custom player-name that the game can choose to honor. This
  /// is used by the remote app.
  auto custom_default_player_name() const -> std::string {
    return custom_default_player_name_;
  }

  void set_custom_default_player_name(const std::string& val) {
    custom_default_player_name_ = val;
  }

  auto allow_input_in_attract_mode() const {
    return allow_input_in_attract_mode_;
  }

  void set_allow_input_in_attract_mode(bool allow) {
    allow_input_in_attract_mode_ = allow;
  }

 private:
  Object::Ref<InputDeviceDelegate> delegate_;

  millisecs_t last_active_time_millisecs_{};

  // Feedback arbiter state (see ApplyFeedback).
  millisecs_t feedback_hold_until_{};
  millisecs_t feedback_window_start_{};
  int feedback_window_count_{};
  int feedback_priority_{};

  int index_{-1};   // Our overall device index.
  int number_{-1};  // Our type-specific number.
  bool allow_input_in_attract_mode_{};

  std::string custom_default_player_name_;

  BA_DISALLOW_CLASS_COPIES(InputDevice);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_H_
