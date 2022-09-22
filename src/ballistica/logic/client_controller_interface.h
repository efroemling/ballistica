// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_LOGIC_CLIENT_CONTROLLER_INTERFACE_H_
#define BALLISTICA_LOGIC_CLIENT_CONTROLLER_INTERFACE_H_

#include "ballistica/ballistica.h"

namespace ballistica {

/// An interface for something that can control client-connections
/// (such as an output-stream or a replay-client-session).
/// Objects can register themselves as the current client-connection-controller
/// and then they will get control of all existing (and forthcoming) clients.
class ClientControllerInterface {
 public:
  virtual auto OnClientConnected(ConnectionToClient* c) -> void = 0;
  virtual auto OnClientDisconnected(ConnectionToClient* c) -> void = 0;
};

}  // namespace ballistica

#endif  // BALLISTICA_LOGIC_CLIENT_CONTROLLER_INTERFACE_H_
