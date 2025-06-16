// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_input_device_delegate.h"

#include <string>
#include <vector>

#include "ballistica/base/networking/networking.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/connection/connection_to_client.h"
#include "ballistica/scene_v1/support/client_input_device.h"

namespace ballistica::scene_v1 {

void ClientInputDeviceDelegate::StoreClientDeviceInfo(
    ClientInputDevice* device) {
  assert(!connection_to_client_.exists());
  connection_to_client_ = device->connection_to_client();
  remote_device_id_ = device->remote_device_id();
}

void ClientInputDeviceDelegate::AttachToLocalPlayer(Player* player) {
  if (ConnectionToClient* c = connection_to_client_.get()) {
    // Send a new-style message with a 32 bit player-id.
    // (added during protocol 29; not always present)
    {
      std::vector<uint8_t> data(6);
      data[0] = BA_MESSAGE_ATTACH_REMOTE_PLAYER_2;
      data[1] = static_cast_check_fit<uint8_t>(remote_device_id_);
      int val = player->id();
      memcpy(&(data[2]), &val, sizeof(val));
      c->SendReliableMessage(data);
    }

    // We also need to send an old-style message as a fallback.
    //
    // FIXME: Can remove this once backwards-compat-protocol is > 29.
    //
    // UPDATE: Only send this if player id fits. This could cause problems
    //   for older clients in very rare cases, but the only alternative is
    //   to not support those clients. I doubt there are many such old
    //   clients out there anyway.
    if (player->id() < 256) {
      std::vector<uint8_t> data(3);
      data[0] = BA_MESSAGE_ATTACH_REMOTE_PLAYER;
      data[1] = static_cast_check_fit<uint8_t>(remote_device_id_);
      data[2] = static_cast_check_fit<uint8_t>(player->id());
      c->SendReliableMessage(data);
    }
  }
  SceneV1InputDeviceDelegate::AttachToLocalPlayer(player);
}

void ClientInputDeviceDelegate::DetachFromPlayer() {
  // Tell the client that their device is no longer attached to a player.
  if (ConnectionToClient* c = connection_to_client_.get()) {
    std::vector<uint8_t> data(2);
    data[0] = BA_MESSAGE_DETACH_REMOTE_PLAYER;
    data[1] = static_cast_check_fit<unsigned char>(remote_device_id_);
    c->SendReliableMessage(data);
  }
  SceneV1InputDeviceDelegate::DetachFromPlayer();
}

auto ClientInputDeviceDelegate::GetClientID() const -> int {
  if (ConnectionToClient* c = connection_to_client_.get()) {
    return c->id();
  } else {
    g_core->logging->Log(
        LogName::kBaNetworking, LogLevel::kError,
        "ClientInputDevice::get_client_id(): connection_to_client no longer "
        "exists; returning -1..");
    return -1;
  }
}

auto ClientInputDeviceDelegate::GetPublicV1AccountID() const -> std::string {
  assert(g_base->InLogicThread());
  if (connection_to_client_.exists()) {
    return connection_to_client_->peer_public_account_id();
  }
  return "";
}

auto ClientInputDeviceDelegate::GetAccountName(bool full) const -> std::string {
  assert(g_base->InLogicThread());
  if (connection_to_client_.exists()) {
    if (full) {
      return connection_to_client_->peer_spec().GetDisplayString();
    } else {
      return connection_to_client_->peer_spec().GetShortName();
    }
  }
  return "???";
}

auto ClientInputDeviceDelegate::GetPlayerProfiles() const -> PyObject* {
  if (connection_to_client_.exists()) {
    return connection_to_client_->GetPlayerProfiles();
  }
  return nullptr;
}

auto ClientInputDeviceDelegate::IsRemoteClient() const -> bool { return true; }

}  // namespace ballistica::scene_v1
