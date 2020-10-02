// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SESSION_REPLAY_CLIENT_SESSION_H_
#define BALLISTICA_GAME_SESSION_REPLAY_CLIENT_SESSION_H_

#include <string>
#include <vector>

#include "ballistica/game/client_controller_interface.h"
#include "ballistica/game/session/client_session.h"

namespace ballistica {

// A client-session fed by a connection to a host.
class ReplayClientSession : public ClientSession,
                            public ClientControllerInterface {
 public:
  explicit ReplayClientSession(std::string filename);
  ~ReplayClientSession() override;
  void OnReset(bool rewind) override;

  // Our ClientControllerInterface implementation.
  auto GetActualTimeAdvance(int advance_in) -> int override;
  void OnClientConnected(ConnectionToClient* c) override;
  void OnClientDisconnected(ConnectionToClient* c) override;
  void DumpFullState(GameStream* out) override;

 protected:
  void Error(const std::string& description) override;
  void FetchMessages() override;

 private:
  uint32_t message_fetch_num_;
  bool have_sent_client_message_;
  std::vector<ConnectionToClient*> connections_to_clients_;
  std::vector<ConnectionToClient*> connections_to_clients_ignored_;
  std::string file_name_;
  FILE* file_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SESSION_REPLAY_CLIENT_SESSION_H_
