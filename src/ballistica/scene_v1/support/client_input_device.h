// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_INPUT_DEVICE_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_INPUT_DEVICE_H_

#include <string>

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/scene_v1/scene_v1.h"

namespace ballistica::scene_v1 {

/// Represents a remote player on a client connected to us.
class ClientInputDevice : public base::InputDevice {
 public:
  ClientInputDevice(int remote_device_id,
                    ConnectionToClient* connection_to_client);
  ~ClientInputDevice() override;

  auto DoGetDeviceName() -> std::string override;
  auto IsLocal() -> bool override { return false; }

  void PassInputCommand(InputType type, float value) {
    InputCommand(type, value);
  }
  auto connection_to_client() const -> ConnectionToClient* {
    return connection_to_client_.get();
  }
  auto remote_device_id() const { return remote_device_id_; }

 private:
  Object::WeakRef<ConnectionToClient> connection_to_client_;
  int remote_device_id_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_INPUT_DEVICE_H_
