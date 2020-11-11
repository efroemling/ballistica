// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_CONNECTION_CONNECTION_TO_HOST_UDP_H_
#define BALLISTICA_GAME_CONNECTION_CONNECTION_TO_HOST_UDP_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/game/connection/connection_to_host.h"
#include "ballistica/networking/networking.h"

namespace ballistica {

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

  // Attempt connecting via a different protocol.  If none are left to try,
  // returns false.
  auto SwitchProtocol() -> bool;
  void RequestDisconnect() override;

 protected:
  uint8_t request_id_{};
  std::unique_ptr<SockAddr> addr_;
  bool did_die_{};
  void Die();
  void SendDisconnectRequest();
  millisecs_t last_client_id_request_time_{};
  millisecs_t last_disconnect_request_time_{};
  int client_id_{};
  millisecs_t last_host_response_time_{};
  void SendGamePacketCompressed(const std::vector<uint8_t>& data) override;
  void Error(const std::string& error_msg) override;

 private:
  void GetRequestID();
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_CONNECTION_CONNECTION_TO_HOST_UDP_H_
