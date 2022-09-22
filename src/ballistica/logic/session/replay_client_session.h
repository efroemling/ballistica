// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_LOGIC_SESSION_REPLAY_CLIENT_SESSION_H_
#define BALLISTICA_LOGIC_SESSION_REPLAY_CLIENT_SESSION_H_

#include <string>
#include <vector>

#include "ballistica/logic/client_controller_interface.h"
#include "ballistica/logic/session/client_session.h"

namespace ballistica {

// A client-session fed by a connection to a host.
class ReplayClientSession : public ClientSession,
                            public ClientControllerInterface {
 public:
  explicit ReplayClientSession(std::string filename);
  ~ReplayClientSession() override;
  auto OnReset(bool rewind) -> void override;

  // Our ClientControllerInterface implementation.
  auto GetActualTimeAdvance(int advance_in) -> int override;
  auto OnClientConnected(ConnectionToClient* c) -> void override;
  auto OnClientDisconnected(ConnectionToClient* c) -> void override;
  auto OnCommandBufferUnderrun() -> void override;

  auto Error(const std::string& description) -> void override;
  auto FetchMessages() -> void override;

 private:
  uint32_t message_fetch_num_{};
  bool have_sent_client_message_{};
  std::vector<ConnectionToClient*> connections_to_clients_;
  std::vector<ConnectionToClient*> connections_to_clients_ignored_;
  std::string file_name_;
  FILE* file_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_LOGIC_SESSION_REPLAY_CLIENT_SESSION_H_
