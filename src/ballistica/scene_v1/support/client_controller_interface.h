// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_CONTROLLER_INTERFACE_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_CONTROLLER_INTERFACE_H_

#include "ballistica/scene_v1/scene_v1.h"

namespace ballistica::scene_v1 {

/// An interface for something that can control client-connections
/// (such as an output-stream or a replay-client-session).
/// Objects can register themselves as the current client-connection-controller
/// and then they will get control of all existing (and forthcoming) clients.
class ClientControllerInterface {
 public:
  virtual void OnClientConnected(ConnectionToClient* c) = 0;
  virtual void OnClientDisconnected(ConnectionToClient* c) = 0;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_CONTROLLER_INTERFACE_H_
