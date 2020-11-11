// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INPUT_DEVICE_INPUT_DEVICE_H_
#define BALLISTICA_INPUT_DEVICE_INPUT_DEVICE_H_

#include <string>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

/// Base class for game input devices (keyboard, joystick, etc).
/// InputDevices can be allocated in any thread (generally on the main
/// thread in response to some system event).  An AddInputDevice() call
/// should then be pushed to the game thread to inform it of the new device.
/// Deletion of the input-device is then handled by the game thread
/// and can be triggered by pushing a RemoveInputDevice() call to it.
class InputDevice : public Object {
 public:
  InputDevice();
  ~InputDevice() override;

  /// Called when the device is attached/detached to a local player.
  virtual void AttachToLocalPlayer(Player* player);
  virtual void AttachToRemotePlayer(ConnectionToHost* connection_to_host,
                                    int remote_player_id);
  virtual void DetachFromPlayer();

  /// Issues a command to the remote game to remove the player we're attached
  /// to.
  void RemoveRemotePlayerFromGame();

  /// Return the (not necessarily unique) name of the input device.
  auto GetDeviceName() -> std::string;
  virtual void ResetHeldStates();

  /// Return the default base player name for players using this input device.
  virtual auto GetDefaultPlayerName() -> std::string;

  /// Return the name of the signed-in account associated with this device
  /// (for remote players, returns their account).
  virtual auto GetAccountName(bool full) const -> std::string;

  /// Return the public Account ID of the signed-in account associated
  /// with this device, or an empty string if not (yet) available.
  /// Note that in some cases there may be a delay before this value
  /// is available. (remote player account IDs are verified with the
  /// master server before becoming available, etc)
  virtual auto GetPublicAccountID() const -> std::string;

  /// Returns player-profiles dict if available; otherwise nullptr.
  virtual auto GetPlayerProfiles() const -> PyObject*;

  /// Return the name of the button used to evoke the party menu.
  virtual auto GetPartyButtonName() const -> std::string;

  /// Returns a number specific to this device type (saying this is the Nth
  /// device of this type).
  auto device_number() const -> int { return number_; }
  auto GetPersistentIdentifier() const -> std::string;
  auto attached_to_player() const -> bool {
    return player_.exists() || remote_player_.exists();
  }
  auto GetRemotePlayer() const -> ConnectionToHost*;
  auto GetPlayer() const -> Player* { return player_.get(); }

  /// Return the overall device index; unique to all devices.
  auto index() const -> int { return index_; }

  /// Read new control values from config.
  virtual void UpdateMapping() {}

  /// Called during the game loop - for manual button repeats, etc.
  virtual void Update();

  /// Return client id or -1 if local.
  virtual auto GetClientID() const -> int;

  // FIXME: redundant.
  virtual auto IsRemoteClient() const -> bool;

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

  /// Override this to return true if you implement get_button_name().
  // virtual auto HasButtonNames() -> bool { return false; }

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
  auto NewPyRef() -> PyObject* { return GetPyInputDevice(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyInputDevice(false); }
  auto has_py_ref() -> bool { return (py_ref_ != nullptr); }
  auto last_input_time() const -> millisecs_t { return last_input_time_; }
  virtual auto ShouldBeHiddenFromUser() -> bool;
  static void ResetRandomNames();

 protected:
  void ShipBufferIfFull();

  /// Pass some input command on to whatever we're connected to
  /// (player or remote-player).
  void InputCommand(InputType type, float value = 0.0f);

  /// Called for all devices when they've successfully been added
  /// to the input-device list, have a valid ID, name, etc.
  virtual void ConnectionComplete() {}

  /// Subclasses should call this to request a player in the local game.
  void RequestPlayer();

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

  auto remote_player_id() const -> int { return remote_player_id_; }
  void UpdateLastInputTime();

 private:
  millisecs_t last_remote_input_commands_send_time_ = 0;
  std::vector<uint8_t> remote_input_commands_buffer_;

  // note: this is in base-net-time
  millisecs_t last_input_time_ = 0;

  // We're attached to *one* of these two.
  Object::WeakRef<Player> player_;
  Object::WeakRef<ConnectionToHost> remote_player_;

  int remote_player_id_ = -1;
  PyObject* py_ref_ = nullptr;
  auto GetPyInputDevice(bool new_ref) -> PyObject*;
  void set_index(int index_in) { index_ = index_in; }
  void set_numbered_identifier(int n) { number_ = n; }
  int index_ = -1;   // Our overall device index.
  int number_ = -1;  // Our type-specific number.
  friend class Input;
  BA_DISALLOW_CLASS_COPIES(InputDevice);
};

}  // namespace ballistica

#endif  // BALLISTICA_INPUT_DEVICE_INPUT_DEVICE_H_
