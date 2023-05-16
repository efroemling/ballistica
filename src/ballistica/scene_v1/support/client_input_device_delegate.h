// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_INPUT_DEVICE_DELEGATE_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_INPUT_DEVICE_DELEGATE_H_

#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"

namespace ballistica::scene_v1 {

class ClientInputDeviceDelegate : public SceneV1InputDeviceDelegate {
 public:
  void AttachToLocalPlayer(Player* player) override;
  void DetachFromPlayer() override;
  auto connection_to_client() const -> ConnectionToClient* {
    return connection_to_client_.Get();
  }

  void StoreClientDeviceInfo(ClientInputDevice* device);
  auto GetClientID() const -> int override;
  auto GetPublicV1AccountID() const -> std::string override;
  auto GetAccountName(bool full) const -> std::string override;
  // Return player-profiles dict if available; otherwise nullptr.
  auto GetPlayerProfiles() const -> PyObject* override;
  auto IsRemoteClient() const -> bool override;

 private:
  Object::WeakRef<ConnectionToClient> connection_to_client_;
  int remote_device_id_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_INPUT_DEVICE_DELEGATE_H_
