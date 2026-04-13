// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_input_device.h"

#include <string>

#include "ballistica/scene_v1/connection/connection_to_client.h"

namespace ballistica::scene_v1 {

ClientInputDevice::ClientInputDevice(int remote_device_id,
                                     ConnectionToClient* connection_to_client)
    : remote_device_id_(remote_device_id),
      connection_to_client_(connection_to_client) {}

// Hmm; do we need to send a remote-detach in this case?
// I don't think so; if we're dying it means the connection is dying
// which means we probably couldn't communicate anyway and
// the other end will free the input-device up
ClientInputDevice::~ClientInputDevice() = default;

auto ClientInputDevice::DoGetDeviceName() -> std::string {
  return "Client Input Device";
}

}  // namespace ballistica::scene_v1
