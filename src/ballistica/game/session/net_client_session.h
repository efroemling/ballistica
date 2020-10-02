// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SESSION_NET_CLIENT_SESSION_H_
#define BALLISTICA_GAME_SESSION_NET_CLIENT_SESSION_H_

#include <vector>

#include "ballistica/game/session/client_session.h"

namespace ballistica {

// A client-session fed by a connection to a host.
class NetClientSession : public ClientSession {
 public:
  NetClientSession();
  ~NetClientSession() override;
  auto connection_to_host() const -> ConnectionToHost* {
    return connection_to_host_.get();
  }
  void SetConnectionToHost(ConnectionToHost* c);
  void HandleSessionMessage(const std::vector<uint8_t>& buffer) override;
  void OnCommandBufferUnderrun() override;

 protected:
  void Update(int time_advance) override;

 private:
  void UpdateBuffering();
  bool writing_replay_ = false;
  Object::WeakRef<ConnectionToHost> connection_to_host_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SESSION_NET_CLIENT_SESSION_H_
