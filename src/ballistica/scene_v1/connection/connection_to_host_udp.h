// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_UDP_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_UDP_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/networking/networking.h"
#include "ballistica/scene_v1/connection/connection_to_host.h"

namespace ballistica::scene_v1 {

class ConnectionToHostUDP : public ConnectionToHost {
 public:
  explicit ConnectionToHostUDP(const SockAddr& addr);
  ~ConnectionToHostUDP() override;
  void Update() override;
  void HandleGamePacket(const std::vector<uint8_t>& buffer) override;
  auto GetAsUDP() -> ConnectionToHostUDP* override;
  auto request_id() const -> uint8_t { return request_id_; }
  void set_client_id(int val) { client_id_ = val; }
  auto client_id() const -> int { return client_id_; }

  /// Attempt connecting via a different protocol. If none are left to try,
  /// returns false.
  auto SwitchProtocol() -> bool;
  void RequestDisconnect() override;

  void SendGamePacketCompressed(const std::vector<uint8_t>& data) override;
  void Error(const std::string& error_msg) override;
  void Die();
  void SendDisconnectRequest();
  const auto& addr() const { return *addr_; }

  /// How long it has been (display-time millisecs) since we last heard
  /// from the host.
  auto HostSilentMillisecs() const -> millisecs_t;

  /// Note a host game packet we dropped because it carried a request id
  /// other than ours (diagnostics for joins that never complete).
  void NoteMismatchedRequestIdPacket(uint8_t packet_request_id);

 private:
  int mismatched_request_id_packets_{};
  uint8_t last_mismatched_request_id_{};
  void GetRequestID_();

  bool did_die_{};
  uint8_t request_id_{};
  int client_id_{};
  millisecs_t last_client_id_request_time_{};
  millisecs_t last_disconnect_request_time_{};
  /// When we started disconnecting (0 while not disconnecting).
  millisecs_t disconnect_start_time_millisecs_{};
  millisecs_t last_host_response_time_millisecs_{};
  bool got_host_game_packet_{};
  std::unique_ptr<SockAddr> addr_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_TO_HOST_UDP_H_
