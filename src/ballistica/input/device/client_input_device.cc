// Released under the MIT License. See LICENSE for details.

#include "ballistica/input/device/client_input_device.h"

#include "ballistica/logic/connection/connection_to_client.h"
#include "ballistica/logic/player.h"
#include "ballistica/networking/networking.h"

namespace ballistica {

ClientInputDevice::ClientInputDevice(int remote_device_id,
                                     ConnectionToClient* connection_to_client)
    : remote_device_id_(remote_device_id),
      connection_to_client_(connection_to_client) {}

// Hmm; do we need to send a remote-detach in this case?
// I don't think so; if we're dying it means the connection is dying
// which means we probably couldn't communicate anyway and
// the other end will free the input-device up
ClientInputDevice::~ClientInputDevice() = default;

auto ClientInputDevice::GetRawDeviceName() -> std::string {
  return "Client Input Device";
}

auto ClientInputDevice::GetClientID() const -> int {
  if (ConnectionToClient* c = connection_to_client_.get()) {
    return c->id();
  } else {
    Log(LogLevel::kError,
        "ClientInputDevice::get_client_id(): connection_to_client no longer "
        "exists; returning -1..");
    return -1;
  }
}

auto ClientInputDevice::GetPlayerProfiles() const -> PyObject* {
  if (connection_to_client_.exists()) {
    return connection_to_client_->GetPlayerProfiles();
  }
  return nullptr;
}

auto ClientInputDevice::GetAccountName(bool full) const -> std::string {
  assert(InLogicThread());
  if (connection_to_client_.exists()) {
    if (full) {
      return connection_to_client_->peer_spec().GetDisplayString();
    } else {
      return connection_to_client_->peer_spec().GetShortName();
    }
  }
  return "???";
}

auto ClientInputDevice::GetPublicV1AccountID() const -> std::string {
  assert(InLogicThread());
  if (connection_to_client_.exists()) {
    return connection_to_client_->peer_public_account_id();
  }
  return "";
}

void ClientInputDevice::AttachToLocalPlayer(Player* player) {
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
    // FIXME: Can remove this once backwards-compat-protocol is > 29.
    {
      std::vector<uint8_t> data(3);
      data[0] = BA_MESSAGE_ATTACH_REMOTE_PLAYER;
      data[1] = static_cast_check_fit<uint8_t>(remote_device_id_);
      data[2] = static_cast_check_fit<uint8_t>(player->id());
      c->SendReliableMessage(data);
    }
  }
  InputDevice::AttachToLocalPlayer(player);
}

void ClientInputDevice::DetachFromPlayer() {
  if (ConnectionToClient* c = connection_to_client_.get()) {
    std::vector<uint8_t> data(2);
    data[0] = BA_MESSAGE_DETACH_REMOTE_PLAYER;
    data[1] = static_cast_check_fit<unsigned char>(remote_device_id_);
    c->SendReliableMessage(data);
  }
  InputDevice::DetachFromPlayer();
}

}  // namespace ballistica
