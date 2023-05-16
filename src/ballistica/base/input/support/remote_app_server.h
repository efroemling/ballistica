// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_SUPPORT_REMOTE_APP_SERVER_H_
#define BALLISTICA_BASE_INPUT_SUPPORT_REMOTE_APP_SERVER_H_

#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/shared/networking/networking_sys.h"

namespace ballistica::base {

constexpr int kRemoteAppProtocolVersion = 121;
constexpr int kMaxRemoteAppClients = 24;

enum class RemoteError {
  kVersionMismatch,
  kGameShuttingDown,
  kNotAcceptingConnections,
  kNotConnected
};

enum RemoteState {
  kRemoteStateMenu = 1u << 0u,
  kRemoteStateJump = 1u << 1u,
  kRemoteStatePunch = 1u << 2u,
  kRemoteStateThrow = 1u << 3u,
  kRemoteStateBomb = 1u << 4u,
  kRemoteStateRun = 1u << 5u,
  kRemoteStateFly = 1u << 6u,
  kRemoteStateHoldPosition = 1u << 7u,
  // Second byte is d-pad h-value and third byte is d-pad v-value.
};

class RemoteAppServer {
 public:
  RemoteAppServer();
  ~RemoteAppServer();

  // Feed the remote-server with data coming in to a listening udp socket.
  void HandleData(int sd, uint8_t* data, size_t data_size,
                  struct sockaddr* from, size_t from_size);

 private:
  auto GetClient(int request_id, struct sockaddr* addr, size_t addr_len,
                 const char* name, bool using_v2) -> int;
  struct RemoteAppClient {
    bool in_use{};
    int request_id{};
    char name[101]{};
    char display_name[101]{};
    sockaddr_storage address{};
    size_t address_size{};
    millisecs_t last_contact_time{};
    uint8_t next_state_id{};
    uint32_t state{};
    JoystickInput* joystick_{};
  };
  RemoteAppClient clients_[kMaxRemoteAppClients]{};
  enum class RemoteEventType;
  void HandleRemoteEvent(RemoteAppClient* client, RemoteEventType msg);
  void HandleRemoteFloatEvent(RemoteAppClient* client, RemoteEventType msg,
                              float val);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_SUPPORT_REMOTE_APP_SERVER_H_
