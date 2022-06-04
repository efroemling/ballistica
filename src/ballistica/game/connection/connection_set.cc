// Released under the MIT License. See LICENSE for details.

#include "ballistica/game/connection/connection_set.h"

#include "ballistica/game/connection/connection_to_client_udp.h"
#include "ballistica/game/connection/connection_to_host_udp.h"
#include "ballistica/game/game.h"
#include "ballistica/game/player.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/networking/network_write_module.h"
#include "ballistica/networking/sockaddr.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {
ConnectionSet::ConnectionSet() = default;

auto ConnectionSet::GetConnectionToHostUDP() -> ConnectionToHostUDP* {
  ConnectionToHost* h = connection_to_host_.get();
  return h ? h->GetAsUDP() : nullptr;
}

void ConnectionSet::RegisterClientController(ClientControllerInterface* c) {
  // This shouldn't happen, but if there's already a controller registered,
  // detach all clients from it.
  if (client_controller_) {
    Log("RegisterClientController() called "
        "but already have a controller; bad.");
    for (auto&& i : connections_to_clients_) {
      assert(i.second.exists());
      i.second->SetController(nullptr);
    }
  }

  // Ok, now assign the new and attach all currently-connected clients to it.
  client_controller_ = c;
  if (client_controller_) {
    for (auto&& i : connections_to_clients_) {
      assert(i.second.exists());
      if (i.second->can_communicate()) {
        i.second->SetController(client_controller_);
      }
    }
  }
}

auto ConnectionSet::Update() -> void {
  // First do housekeeping on our client/host connections.
  for (auto&& i : connections_to_clients_) {
    BA_IFDEBUG(Object::WeakRef<ConnectionToClient> test_ref(i.second));
    i.second->Update();

    // Make sure the connection didn't kill itself in the update.
    assert(test_ref.exists());
  }

  if (connection_to_host_.exists()) {
    connection_to_host_->Update();
  }
}

auto ConnectionSet::GetConnectedClientCount() const -> int {
  assert(InGameThread());
  int count = 0;
  for (auto&& i : connections_to_clients_) {
    if (i.second.exists() && i.second->can_communicate()) {
      count++;
    }
  }
  return count;
}

void ConnectionSet::SendChatMessage(const std::string& message,
                                    const std::vector<int>& clients,
                                    const std::string* sender_override) {
  // Sending to particular clients is only applicable while hosting.
  if (!clients.empty() && connection_to_host() != nullptr) {
    throw Exception("Can't send chat message to specific clients as a client.");
  }

  // Same with overriding sender name
  if (sender_override != nullptr && connection_to_host() != nullptr) {
    throw Exception(
        "Can't send chat message with sender_override as a client.");
  }

  std::string our_spec_string;

  if (sender_override != nullptr) {
    std::string override_final = *sender_override;
    if (override_final.size() > kMaxPartyNameCombinedSize) {
      override_final.resize(kMaxPartyNameCombinedSize);
      override_final += "...";
    }
    our_spec_string =
        PlayerSpec::GetDummyPlayerSpec(override_final).GetSpecString();
  } else {
    if (connection_to_host() != nullptr) {
      // NOTE - we send our own spec string with the chat message whether we're
      // a client or server.. however on protocol version 30+ this is ignored
      // by the server and replaced with a spec string it generates for us.
      // so once we know we're connected to a 30+ server we can start sending
      // blank strings as a client.
      // (not that it really matters; chat messages are tiny overall)
      our_spec_string = PlayerSpec::GetAccountPlayerSpec().GetSpecString();
    } else {
      // As a host we want to do the equivalent of
      // ConnectionToClient::GetCombinedSpec() except for local connections (so
      // send our name as the combination of local players if possible). Look
      // for players coming from this client-connection; if we find any, make a
      // spec out of their name(s).
      std::string p_name_combined;
      if (auto* hs =
              dynamic_cast<HostSession*>(g_game->GetForegroundSession())) {
        for (auto&& p : hs->players()) {
          InputDevice* input_device = p->GetInputDevice();
          if (p->accepted() && p->name_is_real() && input_device != nullptr
              && !input_device->IsRemoteClient()) {
            if (!p_name_combined.empty()) {
              p_name_combined += "/";
            }
            p_name_combined += p->GetName();
          }
        }
      }
      if (p_name_combined.size() > kMaxPartyNameCombinedSize) {
        p_name_combined.resize(kMaxPartyNameCombinedSize);
        p_name_combined += "...";
      }
      if (!p_name_combined.empty()) {
        our_spec_string =
            PlayerSpec::GetDummyPlayerSpec(p_name_combined).GetSpecString();
      } else {
        our_spec_string = PlayerSpec::GetAccountPlayerSpec().GetSpecString();
      }
    }
  }

  // If we find a newline, only take the first line (prevent people from
  // covering the screen with obnoxious chat messages).
  std::string message2 = message;
  size_t nlpos = message2.find('\n');
  if (nlpos != std::string::npos) {
    message2 = message2.substr(0, nlpos);
  }

  // If we're the host, run filters before we send the message out.
  // If the filter kills the message, don't send.
  bool allow_message = g_python->FilterChatMessage(&message2, -1);
  if (!allow_message) {
    return;
  }

  // 1 byte type + 1 byte spec-string-length + message.
  std::vector<uint8_t> msg_out(1 + 1 + our_spec_string.size()
                               + message2.size());
  msg_out[0] = BA_MESSAGE_CHAT;
  size_t spec_size = our_spec_string.size();
  assert(spec_size < 256);
  msg_out[1] = static_cast<uint8_t>(spec_size);
  memcpy(&(msg_out[2]), our_spec_string.c_str(), spec_size);
  memcpy(&(msg_out[2 + spec_size]), message2.c_str(), message2.size());

  // If we're a client, send this to the host (it will make its way back to us
  // when they send to clients).
  if (ConnectionToHost* hc = connection_to_host()) {
    hc->SendReliableMessage(msg_out);
  } else {
    // Ok we're the host.

    // Send to all (or at least some) connected clients.
    for (auto&& i : connections_to_clients_) {
      // Skip if its going to specific ones and this one doesn't match.
      if (!clients.empty()) {
        auto found = false;
        for (auto c : clients) {
          if (c == i.second->id()) {
            found = true;
          }
        }
        if (!found) {
          continue;
        }
      }

      if (i.second->can_communicate()) {
        i.second->SendReliableMessage(msg_out);
      }
    }

    // And display locally if the message is addressed to all.
    if (clients.empty()) {
      g_game->LocalDisplayChatMessage(msg_out);
    }
  }
}

// Can probably kill this.
auto ConnectionSet::GetConnectionsToClients()
    -> std::vector<ConnectionToClient*> {
  std::vector<ConnectionToClient*> connections;
  connections.reserve(connections_to_clients_.size());
  for (auto& connections_to_client : connections_to_clients_) {
    if (connections_to_client.second.exists()) {
      connections.push_back(connections_to_client.second.get());
    } else {
      Log("HAVE NONEXISTENT CONNECTION_TO_CLIENT IN LIST; UNEXPECTED");
    }
  }
  return connections;
}

void ConnectionSet::PushUDPConnectionPacketCall(
    const std::vector<uint8_t>& data, const SockAddr& addr) {
  // Avoid buffer-full errors if something is causing us to write too often;
  // these are unreliable messages so its ok to just drop them.
  if (!g_game->CheckPushSafety()) {
    BA_LOG_ONCE(
        "Ignoring excessive udp-connection input packets; (could this be a "
        "flood attack?).");
    return;
  }

  g_game->PushCall([this, data, addr] { UDPConnectionPacket(data, addr); });
}

auto ConnectionSet::Shutdown() -> void {
  // If we have any client/host connections, give them
  // a chance to shoot off disconnect packets or whatnot.
  for (auto& connection : connections_to_clients_) {
    connection.second->RequestDisconnect();
  }
  if (connection_to_host_.exists()) {
    connection_to_host_->RequestDisconnect();
  }
}

void ConnectionSet::SendScreenMessageToClients(const std::string& s, float r,
                                               float g, float b) {
  for (auto&& i : connections_to_clients_) {
    if (i.second.exists() && i.second->can_communicate()) {
      i.second->SendScreenMessage(s, r, g, b);
    }
  }
}

void ConnectionSet::SendScreenMessageToSpecificClients(
    const std::string& s, float r, float g, float b,
    const std::vector<int>& clients) {
  for (auto&& i : connections_to_clients_) {
    if (i.second.exists() && i.second->can_communicate()) {
      // Only send if this client is in our list.
      for (auto c : clients) {
        if (c == i.second->id()) {
          i.second->SendScreenMessage(s, r, g, b);
          break;
        }
      }
    }
  }

  // Now print locally only if -1 is in our list.
  for (auto c : clients) {
    if (c == -1) {
      ScreenMessage(s, {r, g, b});
      break;
    }
  }
}

void ConnectionSet::SendScreenMessageToAll(const std::string& s, float r,
                                           float g, float b) {
  SendScreenMessageToClients(s, r, g, b);
  ScreenMessage(s, {r, g, b});
}

auto ConnectionSet::PrepareForLaunchHostSession() -> void {
  // If for some reason we're still attached to a host, kill the connection.
  if (connection_to_host_.exists()) {
    Log("Had host-connection during LaunchHostSession(); shouldn't happen.");
    connection_to_host_->RequestDisconnect();
    connection_to_host_.Clear();
    has_connection_to_host_ = false;
    g_game->UpdateGameRoster();
  }
}

auto ConnectionSet::HandleClientDisconnected(int id) -> void {
  auto i = connections_to_clients_.find(id);
  if (i != connections_to_clients_.end()) {
    bool was_connected = i->second->can_communicate();
    std::string leaver_spec = i->second->peer_spec().GetSpecString();
    std::vector<uint8_t> leave_msg(leaver_spec.size() + 1);
    leave_msg[0] = BA_MESSAGE_PARTY_MEMBER_LEFT;
    memcpy(&(leave_msg[1]), leaver_spec.c_str(), leaver_spec.size());
    connections_to_clients_.erase(i);

    // If the client was connected, they were on the roster.
    // We need to update it and send it to all remaining clients since they're
    // gone. Also inform everyone who just left so they can announce it
    // (technically could consolidate these messages but whatever...).
    if (was_connected) {
      g_game->UpdateGameRoster();
      for (auto&& connection : connections_to_clients_) {
        if (g_game->ShouldAnnouncePartyJoinsAndLeaves()) {
          connection.second->SendReliableMessage(leave_msg);
        }
      }
    }
  }
}

auto ConnectionSet::DisconnectClient(int client_id, int ban_seconds) -> bool {
  assert(InGameThread());

  if (connection_to_host_.exists()) {
    // Kick-votes first appeared in 14248
    if (connection_to_host_->build_number() < 14248) {
      return false;
    }
    if (client_id > 255) {
      Log("DisconnectClient got client_id > 255 (" + std::to_string(client_id)
          + ")");
    } else {
      std::vector<uint8_t> msg_out(2);
      msg_out[0] = BA_MESSAGE_KICK_VOTE;
      msg_out[1] = static_cast_check_fit<uint8_t>(client_id);
      connection_to_host_->SendReliableMessage(msg_out);
      return true;
    }
  } else {
    // No host connection - look for clients.
    auto i = connections_to_clients_.find(client_id);

    if (i != connections_to_clients_.end()) {
      // If this is considered a kick, add an entry to our banned list so we
      // know not to let them back in for a while.
      if (ban_seconds > 0) {
        g_game->BanPlayer(i->second->peer_spec(), 1000 * ban_seconds);
      }
      i->second->RequestDisconnect();

      // Do the official local disconnect immediately with the sounds and all
      // that.
      PushClientDisconnectedCall(client_id);

      return true;
    }
  }
  return false;
}

void ConnectionSet::PushClientDisconnectedCall(int id) {
  g_game->PushCall([this, id] { HandleClientDisconnected(id); });
}

void ConnectionSet::PushDisconnectedFromHostCall() {
  g_game->PushCall([this] {
    if (connection_to_host_.exists()) {
      bool was_connected = connection_to_host_->can_communicate();
      connection_to_host_.Clear();
      has_connection_to_host_ = false;

      // Clear out our party roster.
      g_game->UpdateGameRoster();

      // Go back to main menu *if* the connection was fully connected.
      // Otherwise we're still probably sitting at the main menu
      // so no need to reset it.
      if (was_connected) {
        g_game->RunMainMenu();
      }
    }
  });
}

void ConnectionSet::PushHostConnectedUDPCall(const SockAddr& addr,
                                             bool print_connect_progress) {
  g_game->PushCall([this, addr, print_connect_progress] {
    // Attempt to disconnect any clients we have, turn off public-party
    // advertising, etc.
    g_game->CleanUpBeforeConnectingToHost();
    print_udp_connect_progress_ = print_connect_progress;
    connection_to_host_ = Object::New<ConnectionToHostUDP>(addr);
    has_connection_to_host_ = true;
    printed_host_disconnect_ = false;
  });
}

void ConnectionSet::PushDisconnectFromHostCall() {
  g_game->PushCall([this] {
    if (connection_to_host_.exists()) {
      connection_to_host_->RequestDisconnect();
    }
  });
}

auto ConnectionSet::UnregisterClientController(ClientControllerInterface* c)
    -> void {
  assert(c);

  // This shouldn't happen.
  if (client_controller_ != c) {
    Log("UnregisterClientController() called with a non-registered "
        "controller");
    return;
  }

  // Ok, detach all our controllers from this guy.
  if (client_controller_) {
    for (auto&& i : connections_to_clients_) {
      i.second->SetController(nullptr);
    }
  }
  client_controller_ = nullptr;
}

void ConnectionSet::ForceDisconnectClients() {
  for (auto&& i : connections_to_clients_) {
    if (ConnectionToClient* client = i.second.get()) {
      client->RequestDisconnect();
    }
  }
  connections_to_clients_.clear();
}

// Called for low level packets coming in pertaining to udp
// host/client-connections.
auto ConnectionSet::UDPConnectionPacket(const std::vector<uint8_t>& data_in,
                                        const SockAddr& addr) -> void {
  assert(!data_in.empty());

  const uint8_t* data = &(data_in[0]);
  auto data_size = static_cast<size_t>(data_in.size());

  switch (data[0]) {
    case BA_PACKET_CLIENT_ACCEPT: {
      if (data_size == 3) {
        uint8_t request_id = data[2];

        // If we have a udp-host-connection and its request-id matches, we're
        // accepted; hooray!
        ConnectionToHostUDP* hc = GetConnectionToHostUDP();
        if (hc && hc->request_id() == request_id) {
          hc->set_client_id(data[1]);
        }
      }
      break;
    }
    case BA_PACKET_DISCONNECT_FROM_CLIENT_REQUEST: {
      if (data_size == 2) {
        // Client is telling us (host) that it wants to disconnect.
        uint8_t client_id = data[1];

        // Wipe that client out (if it still exists).
        PushClientDisconnectedCall(client_id);

        // Now send an ack so they know it's been taken care of.
        g_network_write_module->PushSendToCall(
            {BA_PACKET_DISCONNECT_FROM_CLIENT_ACK, client_id}, addr);
      }
      break;
    }
    case BA_PACKET_DISCONNECT_FROM_CLIENT_ACK: {
      if (data_size == 2) {
        // Host is telling us (client) that we've been disconnected.
        uint8_t client_id = data[1];
        ConnectionToHostUDP* hc = GetConnectionToHostUDP();
        if (hc && hc->client_id() == client_id) {
          PushDisconnectedFromHostCall();
        }
      }
      break;
    }
    case BA_PACKET_DISCONNECT_FROM_HOST_REQUEST: {
      if (data_size == 2) {
        uint8_t client_id = data[1];

        // Host is telling us (client) to disconnect.
        ConnectionToHostUDP* hc = GetConnectionToHostUDP();
        if (hc && hc->client_id() == client_id) {
          PushDisconnectedFromHostCall();
        }

        // Now send an ack so they know it's been taken care of.
        g_network_write_module->PushSendToCall(
            {BA_PACKET_DISCONNECT_FROM_HOST_ACK, client_id}, addr);
      }
      break;
    }
    case BA_PACKET_DISCONNECT_FROM_HOST_ACK: {
      break;
    }
    case BA_PACKET_CLIENT_GAMEPACKET_COMPRESSED: {
      if (data_size > 2) {
        uint8_t client_id = data[1];
        auto i = connections_to_clients_.find(client_id);
        if (i != connections_to_clients_.end()) {
          // FIXME: could change HandleGamePacketCompressed to avoid this
          //  copy.
          std::vector<uint8_t> data2(data_size - 2);
          memcpy(data2.data(), data + 2, data_size - 2);
          i->second->HandleGamePacketCompressed(data2);
          return;
        } else {
          // Send a disconnect request aimed at them.
          g_network_write_module->PushSendToCall(
              {BA_PACKET_DISCONNECT_FROM_HOST_REQUEST, client_id}, addr);
        }
      }
      break;
    }

    case BA_PACKET_HOST_GAMEPACKET_COMPRESSED: {
      if (data_size > 2) {
        uint8_t request_id = data[1];

        ConnectionToHostUDP* hc = GetConnectionToHostUDP();
        if (hc && hc->request_id() == request_id) {
          // FIXME: Should change HandleGamePacketCompressed to avoid this copy.
          std::vector<uint8_t> data2(data_size - 2);
          memcpy(data2.data(), data + 2, data_size - 2);
          hc->HandleGamePacketCompressed(data2);
        }
      }
      break;
    }

    case BA_PACKET_CLIENT_DENY:
    case BA_PACKET_CLIENT_DENY_PARTY_FULL:
    case BA_PACKET_CLIENT_DENY_ALREADY_IN_PARTY:
    case BA_PACKET_CLIENT_DENY_VERSION_MISMATCH: {
      if (data_size == 2) {
        uint8_t request_id = data[1];
        ConnectionToHostUDP* hc = GetConnectionToHostUDP();

        // If they're for-sure rejecting *this* connection, kill it.
        if (hc && hc->request_id() == request_id) {
          bool keep_trying = false;

          // OBSOLETE BUT HERE FOR BACKWARDS COMPAT WITH 1.4.98 servers.
          // Newer servers never deny us in this way and simply include
          // their protocol version in the handshake they send us, allowing us
          // to decide whether we support talking to them or not.
          if (data[0] == BA_PACKET_CLIENT_DENY_VERSION_MISMATCH) {
            // If we've got more protocols we can try, keep trying to connect
            // with our other protocols until one works or we run out.
            // FIXME: We should move this logic to the gamepacket or message
            //  level so it works for all connection types.
            keep_trying = hc->SwitchProtocol();
            if (!keep_trying) {
              if (!printed_host_disconnect_) {
                ScreenMessage(g_game->GetResourceString(
                                  "connectionFailedVersionMismatchText"),
                              {1, 0, 0});
                printed_host_disconnect_ = true;
              }
            }
          } else if (data[0] == BA_PACKET_CLIENT_DENY_PARTY_FULL) {
            if (!printed_host_disconnect_) {
              if (print_udp_connect_progress_) {
                ScreenMessage(
                    g_game->GetResourceString("connectionFailedPartyFullText"),
                    {1, 0, 0});
              }
              printed_host_disconnect_ = true;
            }
          } else if (data[0] == BA_PACKET_CLIENT_DENY_ALREADY_IN_PARTY) {
            if (!printed_host_disconnect_) {
              ScreenMessage(g_game->GetResourceString(
                                "connectionFailedHostAlreadyInPartyText"),
                            {1, 0, 0});
              printed_host_disconnect_ = true;
            }
          } else {
            if (!printed_host_disconnect_) {
              ScreenMessage(g_game->GetResourceString("connectionRejectedText"),
                            {1, 0, 0});
              printed_host_disconnect_ = true;
            }
          }
          if (!keep_trying) {
            PushDisconnectedFromHostCall();
          }
        }
      }
      break;
    }
    case BA_PACKET_CLIENT_REQUEST: {
      if (data_size > 4) {
        // Bytes 2 and 3 are their protocol ID, byte 4 is request ID, the rest
        // is session-id.
        uint16_t protocol_id;
        memcpy(&protocol_id, data + 1, 2);
        uint8_t request_id = data[3];

        // They also send us their session-ID which should
        // be completely unique to them; we can use this to lump client
        // requests together and such.
        std::vector<char> client_instance_buffer(data_size - 4 + 1);
        memcpy(&(client_instance_buffer[0]), data + 4, data_size - 4);
        client_instance_buffer[data_size - 4] = 0;  // terminate string
        std::string client_instance_uuid = &(client_instance_buffer[0]);

        if (static_cast<int>(connections_to_clients_.size() + 1)
            >= g_game->public_party_max_size()) {
          // If we've reached our party size limit (including ourself in that
          // count), reject.

          // Newer version have a specific party-full message; send that first
          // but also follow up with a generic deny message for older clients.
          g_network_write_module->PushSendToCall(
              {BA_PACKET_CLIENT_DENY_PARTY_FULL, request_id}, addr);

          g_network_write_module->PushSendToCall(
              {BA_PACKET_CLIENT_DENY, request_id}, addr);

        } else if (connection_to_host_.exists()) {
          // If we're connected to someone else, we can't have clients.
          g_network_write_module->PushSendToCall(
              {BA_PACKET_CLIENT_DENY_ALREADY_IN_PARTY, request_id}, addr);
        } else {
          // Otherwise go ahead and make them a new client connection.
          Object::Ref<ConnectionToClientUDP> connection_to_client;

          // Go through and see if we already have a client-connection for
          // this request-id.
          for (auto&& i : connections_to_clients_) {
            if (ConnectionToClientUDP* cc_udp = i.second->GetAsUDP()) {
              if (cc_udp->client_instance_uuid() == client_instance_uuid) {
                connection_to_client = cc_udp;
                break;
              }
            }
          }
          if (!connection_to_client.exists()) {
            // Create them a client object.
            // Try to find an unused client-id in the range 0-255.
            int client_id = 0;
            bool found = false;
            for (int i = 0; i < 256; i++) {
              int test_id = (next_connection_to_client_id_ + i) % 255;
              if (connections_to_clients_.find(test_id)
                  == connections_to_clients_.end()) {
                client_id = test_id;
                found = true;
                break;
              }
            }
            next_connection_to_client_id_++;

            // If all 255 slots are taken (whaaaaaaa?), reject them.
            if (!found) {
              std::vector<uint8_t> msg_out(2);
              msg_out[0] = BA_PACKET_CLIENT_DENY;
              msg_out[1] = request_id;
              g_network_write_module->PushSendToCall(msg_out, addr);
              Log("All client slots full; really?..");
              break;
            }
            connection_to_client = Object::New<ConnectionToClientUDP>(
                addr, client_instance_uuid, request_id, client_id);
            connections_to_clients_[client_id] = connection_to_client;
          }

          // If we got to this point, regardless of whether
          // we already had a connection or not, tell them
          // they're accepted.
          std::vector<uint8_t> msg_out(3);
          msg_out[0] = BA_PACKET_CLIENT_ACCEPT;
          assert(connection_to_client->id() < 256);
          msg_out[1] =
              static_cast_check_fit<uint8_t>(connection_to_client->id());
          msg_out[2] = request_id;
          g_network_write_module->PushSendToCall(msg_out, addr);
        }
      }
      break;
    }
    default:
      // Assuming we can get random other noise in here;
      // should just silently ignore.
      break;
  }
}

void ConnectionSet::SetClientInfoFromMasterServer(
    const std::string& client_token, PyObject* info_obj) {
  // NOLINTNEXTLINE  (python doing bitwise math on signed int)
  if (!PyDict_Check(info_obj)) {
    Log("got non-dict for master-server client info for token " + client_token
        + ": " + Python::ObjToString(info_obj));
    return;
  }
  for (ConnectionToClient* client : GetConnectionsToClients()) {
    if (client->token() == client_token) {
      client->HandleMasterServerClientInfo(info_obj);

      // Roster will now include account-id...
      g_game->mark_game_roster_dirty();
      break;
    }
  }
}

}  // namespace ballistica
