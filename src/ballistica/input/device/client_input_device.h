// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INPUT_DEVICE_CLIENT_INPUT_DEVICE_H_
#define BALLISTICA_INPUT_DEVICE_CLIENT_INPUT_DEVICE_H_

#include <string>

#include "ballistica/input/device/input_device.h"

namespace ballistica {

/// Represents a remote player on a client connected to us.
class ClientInputDevice : public InputDevice {
 public:
  ClientInputDevice(int remote_device_id,
                    ConnectionToClient* connection_to_client);
  ~ClientInputDevice() override;

  auto GetRawDeviceName() -> std::string override;
  auto IsRemoteClient() const -> bool override { return true; }
  auto GetClientID() const -> int override;
  auto IsLocal() -> bool override { return false; }

  // Return player-profiles dict if available; otherwise nullptr.
  auto GetPlayerProfiles() const -> PyObject* override;
  auto GetAccountName(bool full) const -> std::string override;
  auto GetPublicV1AccountID() const -> std::string override;
  void AttachToLocalPlayer(Player* player) override;
  void DetachFromPlayer() override;
  void PassInputCommand(InputType type, float value) {
    InputCommand(type, value);
  }
  auto connection_to_client() const -> ConnectionToClient* {
    return connection_to_client_.get();
  }

 private:
  Object::WeakRef<ConnectionToClient> connection_to_client_;
  int remote_device_id_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_INPUT_DEVICE_CLIENT_INPUT_DEVICE_H_
