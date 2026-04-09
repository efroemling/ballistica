// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SCENE_V1_INPUT_DEVICE_DELEGATE_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SCENE_V1_INPUT_DEVICE_DELEGATE_H_

#include <string>
#include <vector>

#include "ballistica/base/input/device/input_device_delegate.h"
#include "ballistica/scene_v1/support/player.h"

namespace ballistica::scene_v1 {

class SceneV1InputDeviceDelegate : public base::InputDeviceDelegate {
 public:
  SceneV1InputDeviceDelegate();
  ~SceneV1InputDeviceDelegate() override;

  void RequestPlayer() override;
  void InputCommand(InputType type, float value) override;
  auto GetPlayerPosition() -> std::optional<Vector3f> override;
  auto AttachedToPlayer() const -> bool override;

  virtual void AttachToLocalPlayer(Player* player);
  virtual void AttachToRemotePlayer(ConnectionToHost* connection_to_host,
                                    int remote_player_id);
  void DetachFromPlayer() override;

  void Update() override;
  auto GetPlayer() const -> Player* { return player_.get(); }
  auto GetRemotePlayer() const -> ConnectionToHost*;
  auto remote_player_id() const -> int { return remote_player_id_; }

  auto DescribeAttachedTo() const -> std::string override;

  auto NewPyRef() -> PyObject* { return GetPyInputDevice(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyInputDevice(false); }
  auto HasPyRef() -> bool { return (py_ref_ != nullptr); }

  void InvalidateConnectionToHost();

  /// Return client id or -1 if local.
  virtual auto GetClientID() const -> int;

  /// Return the name of the signed-in account associated with this device
  /// (for remote players, returns their account).
  virtual auto GetAccountName(bool full) const -> std::string;

  /// Return the account ID of the signed-in account associated
  /// with this device, or an empty string if not available.
  virtual auto GetAccountID() const -> std::string;

  /// Returns player-profiles dict if available; otherwise nullptr.
  virtual auto GetPlayerProfiles() const -> PyObject*;

  /// Returns the classic-inventory purchase legacy-ids list
  /// provided by the master server for the account using this
  /// device, or ``nullptr`` / ``Py_None`` when unknown (non-v2-auth
  /// connection, older master-server version, or no classic
  /// inventory record). Python callers should treat all "absent"
  /// cases as ``None`` — see the ``get_classic_purchases()``
  /// binding.
  virtual auto GetClassicPurchases() const -> PyObject*;

  // FIXME: redundant.
  virtual auto IsRemoteClient() const -> bool;

  static void ResetRandomNames();

  /// Return the default base player name for players using this input device.
  virtual auto GetDefaultPlayerName() -> std::string;

 private:
  auto GetPyInputDevice(bool new_ref) -> PyObject*;
  void ShipBufferIfFull();

  PyObject* py_ref_{};

  // We're attached to *one* of these two.
  Object::WeakRef<Player> player_;
  Object::WeakRef<ConnectionToHost> remote_player_;

  millisecs_t last_remote_input_commands_send_time_{};
  std::vector<uint8_t> remote_input_commands_buffer_;
  int remote_player_id_{-1};

  BA_DISALLOW_CLASS_COPIES(SceneV1InputDeviceDelegate);
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SCENE_V1_INPUT_DEVICE_DELEGATE_H_
