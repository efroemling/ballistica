// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_CONNECTION_CONNECTION_SET_H_
#define BALLISTICA_GAME_CONNECTION_CONNECTION_SET_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

class ConnectionSet {
 public:
  ConnectionSet();

  // Whoever wants to wrangle current client connections should call this
  // to register itself. Note that it must explicitly call unregister when
  // unregistering itself.
  auto RegisterClientController(ClientControllerInterface* c) -> void;
  auto UnregisterClientController(ClientControllerInterface* c) -> void;

  // Quick test as to whether there are clients. Does not check if they are
  // fully connected.
  auto has_connection_to_clients() const -> bool {
    assert(InGameThread());
    return (!connections_to_clients_.empty());
  }

  // Returns our host-connection or nullptr if there is none.
  auto connection_to_host() -> ConnectionToHost* {
    return connection_to_host_.get();
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

  auto Update() -> void;
  auto Shutdown() -> void;
  auto PrepareForLaunchHostSession() -> void;
  auto HandleClientDisconnected(int id) -> void;
  // Returns true if disconnect attempts are supported.
  auto DisconnectClient(int client_id, int ban_seconds) -> bool;
  auto ForceDisconnectClients() -> void;
  auto PushHostConnectedUDPCall(const SockAddr& addr,
                                bool print_connect_progress) -> void;
  auto PushDisconnectFromHostCall() -> void;
  auto PushDisconnectedFromHostCall() -> void;
  auto GetPrintUDPConnectProgress() const -> bool {
    return print_udp_connect_progress_;
  }
  auto PushUDPConnectionPacketCall(const std::vector<uint8_t>& data,
                                   const SockAddr& addr) -> void;
  // Return our client connections (if any).
  // FIXME: this prunes invalid connections, but it is necessary?
  //  Can we just use connections_to_clients() for direct access?
  auto GetConnectionsToClients() -> std::vector<ConnectionToClient*>;

  // Return the number of connections-to-client with "connected" status true.
  auto GetConnectedClientCount() const -> int;

  // For applying player-profiles data from the master-server.
  auto SetClientInfoFromMasterServer(const std::string& client_token,
                                     PyObject* info) -> void;

  auto SendChatMessage(const std::string& message,
                       const std::vector<int>* clients = nullptr,
                       const std::string* sender_override = nullptr) -> void;

  // Send a screen message to all connected clients AND print it on the host.
  auto SendScreenMessageToAll(const std::string& s, float r, float g, float b)
      -> void;

  // send a screen message to all connected clients
  auto SendScreenMessageToClients(const std::string& s, float r, float g,
                                  float b) -> void;

  // Send a screen message to specific connected clients (those matching the IDs
  // specified) the id -1 can be used to specify the host.
  auto SendScreenMessageToSpecificClients(const std::string& s, float r,
                                          float g, float b,
                                          const std::vector<int>& clients)
      -> void;

#if BA_GOOGLE_BUILD
  auto PushClientDisconnectedGooglePlayCall(int id) -> void;
  int GetGooglePlayClientCount() const;
  auto PushHostConnectedGooglePlayCall() -> void;
  auto PushClientConnectedGooglePlayCall(int id) -> void;
  auto PushCompressedGamePacketFromHostGooglePlayCall(
      const std::vector<uint8_t>& data) -> void;
  auto PushCompressedGamePacketFromClientGooglePlayCall(
      int google_client_id, const std::vector<uint8_t>& data) -> void;
  auto ClientIDFromGooglePlayClientID(int google_id) -> int;
  auto GooglePlayClientIDFromClientID(int client_id) -> int;
#endif

  auto UDPConnectionPacket(const std::vector<uint8_t>& data,
                           const SockAddr& addr) -> void;
  auto PushClientDisconnectedCall(int id) -> void;

 private:
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

#if BA_GOOGLE_BUILD
  std::unordered_map<int, int> google_play_id_to_client_id_map_;
  std::unordered_map<int, int> client_id_to_google_play_id_map_;
#endif
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_CONNECTION_CONNECTION_SET_H_
