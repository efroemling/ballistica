// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_CONNECTION_CONNECTION_TO_CLIENT_UDP_H_
#define BALLISTICA_GAME_CONNECTION_CONNECTION_TO_CLIENT_UDP_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/game/connection/connection_to_client.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/sockaddr.h"

namespace ballistica {

// Connection to a party client if we're the host.
class ConnectionToClientUDP : public ConnectionToClient {
 public:
  ConnectionToClientUDP(const SockAddr& addr, std::string client_name,
                        uint8_t request_id, int client_id);
  ~ConnectionToClientUDP() override;
  void Update() override;
  void HandleGamePacket(const std::vector<uint8_t>& buffer) override;
  auto client_instance_uuid() const { return client_instance_uuid_; }
  auto GetAsUDP() -> ConnectionToClientUDP* override;
  void RequestDisconnect() override;
  void Die();
  void SendDisconnectRequest();
  auto SendGamePacketCompressed(const std::vector<uint8_t>& data)
      -> void override;
  auto addr() { return *addr_; }

 private:
  uint8_t request_id_;
  std::unique_ptr<SockAddr> addr_;
  std::string client_instance_uuid_;
  bool did_die_;
  millisecs_t last_client_response_time_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_CONNECTION_CONNECTION_TO_CLIENT_UDP_H_
