// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_CONNECTION_CONNECTION_TO_HOST_H_
#define BALLISTICA_GAME_CONNECTION_CONNECTION_TO_HOST_H_

#include <string>
#include <vector>

#include "ballistica/game/connection/connection.h"

namespace ballistica {

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
  bool printed_connect_message_ = false;
  int protocol_version_ = kProtocolVersion;
  int build_number_ = 0;
  bool got_host_info_ = false;
  // can remove once back-compat protocol is > 29
  bool ignore_old_attach_remote_player_packets_ = false;
  // the client-session that we're driving
  Object::WeakRef<ClientSession> client_session_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_CONNECTION_CONNECTION_TO_HOST_H_
