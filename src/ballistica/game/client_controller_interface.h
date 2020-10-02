// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_CLIENT_CONTROLLER_INTERFACE_H_
#define BALLISTICA_GAME_CLIENT_CONTROLLER_INTERFACE_H_

#include "ballistica/ballistica.h"

namespace ballistica {

// An interface for something that can control client-connections.
// (such as an output-stream or a replay-client-session)
// objects can register themselves as the current client-connection-controller
// and then they will get control of all existing (and forthcoming) clients
class ClientControllerInterface {
 public:
  virtual void OnClientConnected(ConnectionToClient* c) = 0;
  virtual void OnClientDisconnected(ConnectionToClient* c) = 0;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_CLIENT_CONTROLLER_INTERFACE_H_
