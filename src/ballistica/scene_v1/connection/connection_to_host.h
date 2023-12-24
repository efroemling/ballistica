// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/connection/connection.h"
#include "ballistica/scene_v1/scene_v1.h"

namespace ballistica::scene_v1 {

// connection to the party host if we're a client
class ConnectionToHost : public Connection {
 public:
  ConnectionToHost();
  ~ConnectionToHost() override;
  void Update() override;
  void HandleMessagePacket(const std::vector<uint8_t>& buffer) override;
  void HandleGamePacket(const std::vector<uint8_t>& buffer) override;
  // more efficient than dynamic_cast?.. bad idea?..
  virtual auto GetAsUDP() -> ConnectionToHostUDP*;
  auto build_number() const -> int { return build_number_; }
  auto protocol_version() const -> int { return protocol_version_; }
  void set_protocol_version(int val) { protocol_version_ = val; }
  auto party_name() const -> std::string {
    // FIXME should we return peer name as fallback?..
    return party_name_;
  }

 private:
  std::string party_name_;
  std::string peer_hash_input_;
  std::string peer_hash_;
  // Can remove once back-compat protocol is > 29
  bool ignore_old_attach_remote_player_packets_{};
  bool printed_connect_message_{};
  bool got_host_info_{};
  int protocol_version_{-1};
  int build_number_{};
  millisecs_t last_ping_send_time_{};
  // the client-session that we're driving
  Object::WeakRef<ClientSession> client_session_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_H_
