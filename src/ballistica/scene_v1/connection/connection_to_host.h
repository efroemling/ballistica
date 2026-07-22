// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_H_

#include <optional>
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

  /// The password to present to the host (empty = none). Set at connect
  /// time; the client sends HMAC(password, host-salt) in its CLIENT_INFO
  /// so the host can verify without the raw password ever hitting the
  /// (plaintext) wire.
  void set_join_password(const std::string& val) { join_password_ = val; }

  /// Whether the pre-join requirements exchange completed for this
  /// connect. Set at connect time; the handshake hard-fails joins to
  /// lang-str-era hosts (protocol 39+) that weren't prepped (the
  /// no-mid-game-downloads design means such a join could only strand).
  void set_prepped(bool val) { prepped_ = val; }

 private:
  std::string party_name_;
  std::string peer_hash_input_;
  std::string peer_hash_;
  std::string join_password_;
  bool prepped_{};
  std::string handshake_salt_;
  std::optional<std::string> v2_auth_global_app_instance_id_;
  // The client-session that we're driving
  Object::WeakRef<ClientSession> client_session_;
  int protocol_version_{-1};
  int build_number_{};
  millisecs_t last_ping_send_time_{};
  // Can remove once back-compat protocol is > 29
  bool ignore_old_attach_remote_player_packets_{};
  bool printed_connect_message_{};
  bool got_host_info_{};
  bool got_v2_auth_usage_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_H_
