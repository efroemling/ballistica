// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_SET_H_
#define BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_SET_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

class ConnectionSet {
 public:
  ConnectionSet();

  // Whoever wants to wrangle current client connections should call this
  // to register itself. Note that it must explicitly call unregister when
  // unregistering itself.
  void RegisterClientController(ClientControllerInterface* c);
  void UnregisterClientController(ClientControllerInterface* c);

  // Quick test as to whether there are clients. Does not check if they are
  // fully connected.
  auto HasConnectionToClients() const -> bool {
    assert(g_base->InLogicThread());
    return (!connections_to_clients_.empty());
  }

  // Returns our host-connection or nullptr if there is none.
  auto connection_to_host() -> ConnectionToHost* {
    return connection_to_host_.Get();
  }
  auto GetConnectionToHostUDP() -> ConnectionToHostUDP*;

  auto connections_to_clients()
      -> const std::unordered_map<int, Object::Ref<ConnectionToClient> >& {
    return connections_to_clients_;
  }
  auto client_controller() -> ClientControllerInterface* {
    return client_controller_;
  }

  // Simple thread safe query.
  auto has_connection_to_host() const -> bool {
    return has_connection_to_host_;
  }

  void Update();
  void Shutdown();
  void PrepareForLaunchHostSession();
  void HandleClientDisconnected(int id);
  // Returns true if disconnect attempts are supported.
  auto DisconnectClient(int client_id, int ban_seconds) -> bool;
  void ForceDisconnectClients();
  void PushHostConnectedUDPCall(const SockAddr& addr,
                                bool print_connect_progress);
  void PushDisconnectFromHostCall();
  void PushDisconnectedFromHostCall();
  auto GetPrintUDPConnectProgress() const -> bool {
    return print_udp_connect_progress_;
  }
  void PushIncomingUDPPacketCall(const std::vector<uint8_t>& data,
                                 const SockAddr& addr);
  // Return our client connections (if any).
  // FIXME: this prunes invalid connections, but it is necessary?
  //  Can we just use connections_to_clients() for direct access?
  auto GetConnectionsToClients() -> std::vector<ConnectionToClient*>;

  // Return the number of connections-to-client with "connected" status true.
  auto GetConnectedClientCount() const -> int;

  // For applying player-profiles data from the master-server.
  void SetClientInfoFromMasterServer(const std::string& client_token,
                                     PyObject* info);

  void SendChatMessage(const std::string& message,
                       const std::vector<int>* clients = nullptr,
                       const std::string* sender_override = nullptr);

  // Send a screen message to all connected clients AND print it on the host.
  void SendScreenMessageToAll(const std::string& s, float r, float g, float b);

  // send a screen message to all connected clients
  void SendScreenMessageToClients(const std::string& s, float r, float g,
                                  float b);

  // Send a screen message to specific connected clients (those matching the IDs
  // specified) the id -1 can be used to specify the host.
  void SendScreenMessageToSpecificClients(const std::string& s, float r,
                                          float g, float b,
                                          const std::vector<int>& clients);

  void HandleIncomingUDPPacket(const std::vector<uint8_t>& data_in,
                               const SockAddr& addr);
  void PushClientDisconnectedCall(int id);

 private:
  auto VerifyClientAddr(uint8_t client_id, const SockAddr& addr) -> bool;

  // Try to minimize the chance a garbage packet will have this id.
  int next_connection_to_client_id_{113};
  std::unordered_map<int, Object::Ref<ConnectionToClient> >
      connections_to_clients_;
  Object::Ref<ConnectionToHost> connection_to_host_;
  ClientControllerInterface* client_controller_{};

  // Simple flag for thread-safe access.
  bool has_connection_to_host_{};
  bool print_udp_connect_progress_{true};

  // Prevents us from printing multiple 'you got disconnected' messages.
  bool printed_host_disconnect_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_CONNECTION_CONNECTION_SET_H_
