// Released under the MIT License. See LICENSE for details.

#include "ballistica/game/connection/connection_to_client.h"

#include "ballistica/audio/audio.h"
#include "ballistica/game/client_controller_interface.h"
#include "ballistica/game/connection/connection_set.h"
#include "ballistica/game/game.h"
#include "ballistica/game/player.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/generic/json.h"
#include "ballistica/input/device/client_input_device.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/media/media.h"
#include "ballistica/networking/networking.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

// How long new clients have to wait before starting a kick vote.
const int kNewClientKickVoteDelay = 60000;

ConnectionToClient::ConnectionToClient(int id) : id_(id) {
  // We calc this once just in case it changes on our end
  // (the client uses it for their verification hash so we need to
  // ensure it stays consistent).
  our_handshake_player_spec_str_ =
      PlayerSpec::GetAccountPlayerSpec().GetSpecString();

  // On newer protocols we include an extra salt value
  // to ensure the hash the client generates can't be recycled.
  if (explicit_bool(kProtocolVersion >= 33)) {
    our_handshake_salt_ = std::to_string(rand());  // NOLINT
  }
}

auto ConnectionToClient::ShouldPrintIncompatibleClientErrors() const -> bool {
  return false;
}

void ConnectionToClient::SetController(ClientControllerInterface* c) {
  // If we had an old client-controller, inform it we're leaving it.
  if (controller_) {
    controller_->OnClientDisconnected(this);
    controller_ = nullptr;
  }

  // If we've got a new one, connect it.
  if (c) {
    controller_ = c;
    // We automatically push a session reset command before turning
    // a client connection over to a new controller.
    // The previous client may not have cleaned up after itself
    // in cases such as truncated replays, etc.
    SendReliableMessage(std::vector<uint8_t>(1, BA_MESSAGE_SESSION_RESET));
    controller_->OnClientConnected(this);
  }
}

ConnectionToClient::~ConnectionToClient() {
  // If we've got a controller, disconnect from it.
  SetController(nullptr);

  // If we had made any input-devices, they're just pointers that
  // we have to pass along to g_input to delete for us.
  for (auto&& i : client_input_devices_) {
    g_input->RemoveInputDevice(i.second, false);
  }

  // If they had been announced as connected, announce their departure.
  if (can_communicate() && g_game->ShouldAnnouncePartyJoinsAndLeaves()) {
    std::string s = g_game->GetResourceString("playerLeftPartyText");
    Utils::StringReplaceOne(&s, "${NAME}", peer_spec().GetDisplayString());
    ScreenMessage(s, {1, 0.5f, 0.0f});
    g_audio->PlaySound(g_media->GetSound(SystemSoundID::kCorkPop));
  }
}

void ConnectionToClient::Update() {
  Connection::Update();  // Handles common stuff.

  millisecs_t real_time = GetRealTime();

  // If we're waiting for handshake response still, keep sending out handshake
  // attempts.
  if (!can_communicate() && real_time - last_hand_shake_send_time_ > 1000) {
    // In newer protocols we embed a json dict as the second part of the
    // handshake packet; this way we can evolve the protocol more
    // easily in the future.
    if (explicit_bool(kProtocolVersion >= 33)) {
      // Construct a json dict with our player-spec-string as one element.
      JsonDict dict;
      dict.AddString("s", our_handshake_player_spec_str_);

      // We also add our random salt for hashing.
      dict.AddString("l", our_handshake_salt_);

      std::string out = dict.PrintUnformatted();
      std::vector<uint8_t> data(3 + out.size());
      data[0] = BA_GAMEPACKET_HANDSHAKE;
      uint16_t val = kProtocolVersion;
      memcpy(data.data() + 1, &val, sizeof(val));
      memcpy(data.data() + 3, out.c_str(), out.size());
      SendGamePacket(data);
    } else {
      // (KILL THIS WHEN kProtocolVersionMin >= 33)
      // on older protocols, we simply embedded our spec-string as the second
      // part of the handshake packet
      std::vector<uint8_t> data(3 + our_handshake_player_spec_str_.size());
      data[0] = BA_GAMEPACKET_HANDSHAKE;
      uint16_t val = kProtocolVersion;
      memcpy(data.data() + 1, &val, sizeof(val));
      memcpy(data.data() + 3, our_handshake_player_spec_str_.c_str(),
             our_handshake_player_spec_str_.size());
      SendGamePacket(data);
    }
    last_hand_shake_send_time_ = real_time;
  }
}

void ConnectionToClient::HandleGamePacket(const std::vector<uint8_t>& data) {
  // If we've errored, just respond to everything with 'GO AWAY!'.
  if (errored()) {
    std::vector<uint8_t> data2(1);
    data2[0] = BA_GAMEPACKET_DISCONNECT;
    SendGamePacket(data2);
    return;
  }

  if (data.empty()) {
    Log("Error: ConnectionToClient got data size 0.");
    return;
  }
  switch (data[0]) {
    case BA_GAMEPACKET_HANDSHAKE_RESPONSE: {
      // We sent the client a handshake and they're responding.
      if (data.size() < 3) {
        Log("got invalid BA_GAMEPACKET_HANDSHAKE_RESPONSE");
        return;
      }

      // In newer builds we expect to be sent a json dict here;
      // pull client's spec from that.
      if (explicit_bool(kProtocolVersion >= 33)) {
        std::vector<char> string_buffer(data.size() - 3 + 1);
        memcpy(&(string_buffer[0]), &(data[3]), data.size() - 3);
        string_buffer[string_buffer.size() - 1] = 0;
        cJSON* handshake = cJSON_Parse(string_buffer.data());
        if (handshake) {
          if (cJSON* pspec = cJSON_GetObjectItem(handshake, "s")) {
            set_peer_spec(PlayerSpec(pspec->valuestring));
          }

          // Newer builds also send their public-device-id; servers
          // can use this to combat simple spam attacks.
          if (cJSON* pubdeviceid = cJSON_GetObjectItem(handshake, "d")) {
            public_device_id_ = pubdeviceid->valuestring;
          }
          cJSON_Delete(handshake);
        }
      } else {
        // (KILL THIS WHEN kProtocolVersionMin >= 33)
        // older versions only contained the client spec
        // pull client's spec from the handshake packet..
        std::vector<char> string_buffer(data.size() - 3 + 1);
        memcpy(&(string_buffer[0]), &(data[3]), data.size() - 3);
        string_buffer[string_buffer.size() - 1] = 0;
        set_peer_spec(PlayerSpec(&(string_buffer[0])));
      }
      // FIXME: We should maybe set some sort of 'pending' peer-spec
      //  and fetch their actual info from the master-server.
      //  (or at least make that an option for internet servers)

      // Compare this against our blocked specs.. if there's a match, reject
      // them.
      if (g_game->IsPlayerBanned(peer_spec())) {
        Error("");
        return;
      }

      // Bytes 2 and 3 are their protocol version.
      uint16_t val;
      memcpy(&val, data.data() + 1, sizeof(val));
      if (val != kProtocolVersion) {
        // Depending on the connection type we may print the connection
        // failure or not. (If we invited them it'd be good to know about the
        // failure).
        std::string s;
        if (ShouldPrintIncompatibleClientErrors()) {
          // If they get here, announce on the host that the client is
          // incompatible. UDP connections will get rejected during the
          // connection attempt so this will only apply to things like Google
          // Play invites where we probably want to be more verbose as
          // to why the game just died.
          s = g_game->GetResourceString("incompatibleVersionPlayerText");
          Utils::StringReplaceOne(&s, "${NAME}",
                                  peer_spec().GetDisplayString());
        }
        Error(s);
        return;
      }

      // At this point we know we speak their language so we can send
      // them things beyond handshake packets.
      if (!can_communicate()) {
        set_can_communicate(true);

        // Don't allow fresh clients to start kick votes for a while.
        next_kick_vote_allow_time_ = GetRealTime() + kNewClientKickVoteDelay;

        // At this point we have their name, so lets announce their arrival.
        if (g_game->ShouldAnnouncePartyJoinsAndLeaves()) {
          std::string s = g_game->GetResourceString("playerJoinedPartyText");
          Utils::StringReplaceOne(&s, "${NAME}",
                                  peer_spec().GetDisplayString());
          ScreenMessage(s, {0.5f, 1, 0.5f});
          g_audio->PlaySound(g_media->GetSound(SystemSoundID::kGunCock));
        }

        // Also mark the time for flashing the 'someone just joined your
        // party' message in the corner.
        g_game->set_last_connection_to_client_join_time(GetRealTime());

        // Added midway through protocol 29:
        // We now send a json dict of info about ourself first thing. This
        // gives us a nice open-ended way to expand functionality/etc. going
        // forward. The other end will expect that this is the first reliable
        // message they get; if something else shows up first they'll assume
        // we're an old build and not sending this.
        {
          cJSON* info_dict = cJSON_CreateObject();
          cJSON_AddItemToObject(info_dict, "b",
                                cJSON_CreateNumber(kAppBuildNumber));

          // Add a name entry if we've got a public party name set.
          if (!g_game->public_party_name().empty()) {
            cJSON_AddItemToObject(
                info_dict, "n",
                cJSON_CreateString(g_game->public_party_name().c_str()));
          }
          std::string info = cJSON_PrintUnformatted(info_dict);
          cJSON_Delete(info_dict);

          std::vector<uint8_t> info_msg(info.size() + 1);
          info_msg[0] = BA_MESSAGE_HOST_INFO;
          memcpy(&(info_msg[1]), info.c_str(), info.size());
          SendReliableMessage(info_msg);
        }

        std::string joiner_spec = peer_spec().GetSpecString();
        std::vector<uint8_t> join_msg(joiner_spec.size() + 1);
        join_msg[0] = BA_MESSAGE_PARTY_MEMBER_JOINED;
        memcpy(&(join_msg[1]), joiner_spec.c_str(), joiner_spec.size());

        for (auto&& i : g_game->connections()->connections_to_clients()) {
          // Also send a 'party-member-joined' notification to all clients
          // *except* the new one.
          if (i.second.exists() && i.second.get() != this
              && g_game->ShouldAnnouncePartyJoinsAndLeaves()) {
            i.second->SendReliableMessage(join_msg);
          }
        }

        // Update the game party roster and send it to all clients (including
        // this new one).
        g_game->UpdateGameRoster();

        // Lastly, we hand this connection over to whoever is currently
        // feeding client connections.
        if (g_game->connections()->client_controller()) {
          SetController(g_game->connections()->client_controller());
        }
      }
      break;
    }

    default:
      // Let our base class handle common stuff *if* we're connected.
      if (can_communicate()) {
        Connection::HandleGamePacket(data);
      }
      break;
  }
}
void ConnectionToClient::Error(const std::string& msg) {
  // Take no further action at this time aside from printing it.
  // If we receive any more messages from the client we'll respond
  // with a disconnect message in HandleGamePacket().
  Connection::Error(msg);  // Common stuff.
}

void ConnectionToClient::SendScreenMessage(const std::string& s, float r,
                                           float g, float b) {
  // Older clients don't support the screen-message message, so in that case
  // we just send it as a chat-message from <HOST>.
  if (build_number() < 14248) {
    std::string value = g_game->CompileResourceString(s, "sendScreenMessage");
    std::string our_spec_string =
        PlayerSpec::GetDummyPlayerSpec("<HOST>").GetSpecString();
    std::vector<uint8_t> msg_out(1 + 1 + our_spec_string.size() + value.size());
    msg_out[0] = BA_MESSAGE_CHAT;
    size_t spec_size = our_spec_string.size();
    assert(spec_size < 256);
    msg_out[1] = static_cast<uint8_t>(spec_size);
    memcpy(&(msg_out[2]), our_spec_string.c_str(),
           static_cast<size_t>(spec_size));
    memcpy(&(msg_out[2 + spec_size]), value.c_str(), value.size());
    SendReliableMessage(msg_out);
  } else {
    cJSON* msg = cJSON_CreateObject();
    cJSON_AddNumberToObject(msg, "t", BA_JMESSAGE_SCREEN_MESSAGE);
    cJSON_AddStringToObject(msg, "m", s.c_str());
    cJSON_AddNumberToObject(msg, "r", r);
    cJSON_AddNumberToObject(msg, "g", g);
    cJSON_AddNumberToObject(msg, "b", b);
    SendJMessage(msg);
    cJSON_Delete(msg);
  }
}

void ConnectionToClient::HandleMessagePacket(
    const std::vector<uint8_t>& buffer) {
  if (buffer.empty()) {
    Log("Error: Got invalid HandleMessagePacket.");
    return;
  }

  // If the first message we get is not client-info, it means we're talking to
  // an older client that won't be sending us info.
  if (!got_client_info_ && buffer[0] != BA_MESSAGE_CLIENT_INFO) {
    build_number_ = 0;
    got_client_info_ = true;
  }

  switch (buffer[0]) {
    case BA_MESSAGE_JMESSAGE: {
      if (buffer.size() >= 3 && buffer[buffer.size() - 1] == 0) {
        cJSON* msg =
            cJSON_Parse(reinterpret_cast<const char*>(buffer.data() + 1));
        if (msg) {
          cJSON_Delete(msg);
        }
      }
      break;
    }

    case BA_MESSAGE_KICK_VOTE: {
      if (buffer.size() == 2) {
        for (auto&& i : g_game->connections()->connections_to_clients()) {
          ConnectionToClient* client = i.second.get();
          if (client->id() == static_cast<int>(buffer[1])) {
            g_game->StartKickVote(this, client);
            break;
          }
        }
      }
      break;
    }

    case BA_MESSAGE_CLIENT_INFO: {
      if (buffer.size() > 1) {
        std::vector<char> str_buffer(buffer.size());
        memcpy(&(str_buffer[0]), &(buffer[1]), buffer.size() - 1);
        str_buffer[str_buffer.size() - 1] = 0;
        cJSON* info = cJSON_Parse(reinterpret_cast<const char*>(&(buffer[1])));
        if (info) {
          cJSON* b = cJSON_GetObjectItem(info, "b");
          if (b) {
            build_number_ = b->valueint;
          } else {
            Log("no buildnumber in clientinfo msg");
          }

          // Grab their token (we use this to ask the
          // server for their v1 account info).
          cJSON* t = cJSON_GetObjectItem(info, "tk");
          if (t) {
            token_ = t->valuestring;
          } else {
            Log("no token in clientinfo msg");
          }

          // Newer clients also pass a peer-hash, which
          // we can include with the token to allow the
          // v1 server to better verify the client's identity.
          cJSON* ph = cJSON_GetObjectItem(info, "ph");
          if (ph) {
            peer_hash_ = ph->valuestring;
          }
          if (!token_.empty()) {
            // Kick off a query to the master-server for this client's info.
            // FIXME: we need to add retries for this in case of failure.
            g_app_internal->ClientInfoQuery(
                token_, our_handshake_player_spec_str_ + our_handshake_salt_,
                peer_hash_, build_number_);
          }
          cJSON_Delete(info);
        } else {
          Log("got invalid json in clientinfo message: '"
              + std::string(reinterpret_cast<const char*>(&(buffer[1]))) + "'");
        }
      }
      got_client_info_ = true;
      break;
    }

    case BA_MESSAGE_CLIENT_PLAYER_PROFILES_JSON: {
      // Newer type using json.
      // Only accept peer info if we've not gotten official info from
      // the master server (and if we're allowing it in general).
      if (!g_game->require_client_authentication()
          && !got_info_from_master_server_) {
        std::vector<char> b2(buffer.size());
        memcpy(&(b2[0]), &(buffer[1]), buffer.size() - 1);
        b2[buffer.size() - 1] = 0;
        PythonRef args(Py_BuildValue("(s)", b2.data()), PythonRef::kSteal);
        PythonRef results =
            g_python->obj(Python::ObjID::kJsonLoadsCall).Call(args);
        if (results.exists()) {
          player_profiles_ = results;
        }
      }
      break;
    }

    case BA_MESSAGE_CLIENT_PLAYER_PROFILES: {
      // Ok at this point we shouldn't attempt to eval these;
      // they would have been sent in python 2 and we're python 3
      // so they likely will fail in subtle ways.
      // ('u' prefixes before unicode and this and that)
      // Just gonna hope everyone is updated to a recent-ish version so
      // we don't get these.
      // This might be a good argument to separate out the protocol versions
      // we support for game streams vs client-connections.  We could disallow
      // connections to/from these older peers while still allowing old replays
      // to play back.
      BA_LOG_ONCE("Received old pre-json player profiles msg; ignoring.");
      break;
    }

    case BA_MESSAGE_CHAT: {
      // We got a chat message from a client.
      millisecs_t now = GetRealTime();

      // Ignore this if they're chat blocked.
      if (now >= chat_block_time_) {
        // We keep track of their recent chat times.
        // If they exceed a certain amount in the last several seconds,
        // Institute a chat block.
        last_chat_times_.push_back(now);
        uint32_t timeSample = 5000;
        if (now >= timeSample) {
          while (!last_chat_times_.empty()
                 && last_chat_times_[0] < now - timeSample) {
            last_chat_times_.erase(last_chat_times_.begin());
          }
        }

        // If we require client-info and don't have it from this guy yet,
        // ignore their chat messages (prevent bots from jumping in and
        // spamming before we can verify their identities)
        if (g_game->require_client_authentication()
            && !got_info_from_master_server_) {
          Log("Ignoring chat message from peer with no client info.");
          SendScreenMessage(R"({"r":"loadingTryAgainText"})", 1, 0, 0);
        } else if (last_chat_times_.size() >= 5) {
          chat_block_time_ = now + next_chat_block_seconds_ * 1000;
          g_game->connections()->SendScreenMessageToAll(
              R"({"r":"internal.chatBlockedText","s":[["${NAME}",)"
                  + Utils::GetJSONString(
                      GetCombinedSpec().GetDisplayString().c_str())
                  + R"(],["${TIME}",")"
                  + std::to_string(next_chat_block_seconds_) + "\"]]}",
              1, 1, 0);
          next_chat_block_seconds_ *= 2;  // make it worse next time

        } else {
          // Send this along to all clients.
          // *however* we want to ignore the player-spec that was included in
          // the chat message and replace it with our own for this
          // client-connection.
          if (buffer.size() > 3) {
            int spec_len = buffer[1];
            auto msg_len = static_cast<int>(buffer.size() - spec_len - 2);
            if (spec_len > 0 && msg_len >= 0) {
              std::vector<char> b2(static_cast<size_t>(msg_len) + 1);
              if (msg_len > 0) {
                memcpy(&(b2[0]), &(buffer[2 + spec_len]),
                       static_cast<size_t>(msg_len));
              }
              b2[msg_len] = 0;

              // Clamp messages at a reasonable size
              // (yes, people used this to try and crash machines).
              if (b2.size() > 100) {
                SendScreenMessage(
                    "{\"t\":[\"serverResponses\","
                    "\"Message is too long.\"]}",
                    1, 0, 0);
              } else if (g_game->kick_vote_in_progress()
                         && (!strcmp(b2.data(), "1")
                             || !strcmp(b2.data(), "2"))) {
                // Special case - if there's a kick vote going on, take '1' or
                // '2' to be votes.
                // TODO(ericf): Disable this based on build-numbers once we've
                //  got GUI voting working.
                if (!kick_voted_) {
                  kick_voted_ = true;
                  kick_vote_choice_ = !strcmp(b2.data(), "1");
                } else {
                  SendScreenMessage(R"({"r":"votedAlreadyText"})", 1, 0, 0);
                }
              } else {
                // Pass the message through any custom filtering we've got.
                // If the filter tells us to ignore it, we're done.
                std::string message = b2.data();
                bool allow_message =
                    g_python->FilterChatMessage(&message, id());
                if (!allow_message) {
                  break;
                }

                std::string spec_string = GetCombinedSpec().GetSpecString();
                std::vector<uint8_t> msg_out(1 + 1 + spec_string.size()
                                             + message.size());
                msg_out[0] = BA_MESSAGE_CHAT;
                size_t spec_size = spec_string.size();
                assert(spec_size < 256);
                msg_out[1] = static_cast<unsigned char>(spec_size);
                memcpy(&(msg_out[2]), spec_string.c_str(),
                       static_cast<size_t>(spec_size));
                memcpy(&(msg_out[2 + spec_size]), message.c_str(),
                       message.size());

                // Send it out to all clients.
                for (auto&& i :
                     g_game->connections()->connections_to_clients()) {
                  if (i.second->can_communicate()) {
                    i.second->SendReliableMessage(msg_out);
                  }
                }

                // Display it locally.
                g_game->LocalDisplayChatMessage(msg_out);
              }
            }
          }
        }
      }
      break;
    }

    case BA_MESSAGE_REMOTE_PLAYER_INPUT_COMMANDS: {
      if (ClientInputDevice* client_input_device =
              GetClientInputDevice(buffer[1])) {
        int count = static_cast<int>((buffer.size() - 2) / 5);
        if ((buffer.size() - 2) % 5 != 0) {
          Log("Error: invalid player-input-commands packet");
          break;
        }
        int index = 2;
        for (int i = 0; i < count; i++) {
          auto type = (InputType)buffer[index++];
          float val;
          memcpy(&val, &(buffer[index]), 4);
          index += 4;
          client_input_device->PassInputCommand(type, val);
        }
      }
      break;
    }

    case BA_MESSAGE_REMOVE_REMOTE_PLAYER: {
      last_remove_player_time_ = GetRealTime();
      if (buffer.size() != 2) {
        Log("Error: invalid remove-remote-player packet");
        break;
      }
      if (ClientInputDevice* cid = GetClientInputDevice(buffer[1])) {
        if (Player* player = cid->GetPlayer()) {
          HostSession* host_session = player->GetHostSession();
          if (!host_session) throw Exception("Player's host-session not found");
          host_session->RemovePlayer(player);
        }
      }
      break;
    }

    case BA_MESSAGE_REQUEST_REMOTE_PLAYER: {
      if (buffer.size() != 2) {
        Log("Error: invalid remote-player-request packet");
        break;
      }

      // Create/fetch our client-input that represents this guy
      // and submit a player-request on it's behalf.
      ClientInputDevice* cid = GetClientInputDevice(buffer[1]);

      if (auto* hs =
              dynamic_cast<HostSession*>(g_game->GetForegroundSession())) {
        if (!cid->attached_to_player()) {
          millisecs_t seconds_since_last_left =
              (GetRealTime() - last_remove_player_time_) / 1000;
          int min_seconds_since_left = 10;

          // If someone on this connection left less than 10 seconds ago,
          // prevent them from immediately jumping back in.
          if (seconds_since_last_left < min_seconds_since_left) {
            SendScreenMessage(
                "{\"t\":[\"serverResponses\",\"You can join in ${COUNT} "
                "seconds.\"],\"s\":[[\"${COUNT}\",\""
                    + std::to_string(min_seconds_since_left
                                     - seconds_since_last_left)
                    + "\"]]}",
                1, 1, 0);
          } else {
            bool still_waiting = (g_game->require_client_authentication()
                                  && !got_info_from_master_server_);
            // If we're not allowing peer client-info and have yet to get
            // master-server info for this client, delay their join (we'll
            // eventually give up and just give them a blank slate).
            if (still_waiting && (GetRealTime() - creation_time() < 10000)) {
              SendScreenMessage(
                  "{\"v\":\"${A}...\",\"s\":[[\"${A}\",{\"r\":"
                  "\"loadingTryAgainText\",\"f\":\"loadingText\"}]]}",
                  1, 1, 0);
            } else {
              // Either timed out or have info; let the request go through.
              if (still_waiting) {
                Log("Allowing player-request without client\'s master-server "
                    "info (build "
                    + std::to_string(build_number_) + ")");
              }
              hs->RequestPlayer(cid);
            }
          }
        }
      } else {
        Log("Error: ConnectionToClient got remote player"
            " request but have no host session");
      }
      break;
    }
    default: {
      // Hackers have attempted to mess with servers by sending huge amounts of
      // data through chat messages/etc. Let's watch out for mutli-part messages
      // growing too large and kick/ban the client if they do.
      if (buffer[0] == BA_MESSAGE_MULTIPART) {
        if (multipart_buffer_size() > 50000) {
          // Its not actually unknown but shhh don't tell the hackers...
          SendScreenMessage(R"({"r":"errorUnknownText"})", 1, 0, 0);
          Log("Client data limit exceeded by '" + peer_spec().GetShortName()
              + "'; kicking.");
          g_game->BanPlayer(peer_spec(), 1000 * 60);
          Error("");
          return;
        }
      }

      Connection::HandleMessagePacket(buffer);
    }
  }
}

auto ConnectionToClient::GetCombinedSpec() -> PlayerSpec {
  // Look for players coming from this client-connection.
  // If we find any, make a spec out of their name(s).
  if (auto* hs = dynamic_cast<HostSession*>(g_game->GetForegroundSession())) {
    std::string p_name_combined;
    for (auto&& p : hs->players()) {
      InputDevice* input_device = p->GetInputDevice();
      if (!p->GetName().empty() && p->name_is_real() && p->accepted()
          && input_device != nullptr && input_device->IsRemoteClient()) {
        auto* cid = static_cast<ClientInputDevice*>(input_device);
        ConnectionToClient* ctc = cid->connection_to_client();

        // Add some basic info for each remote player.
        if (ctc != nullptr && ctc == this) {
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
      return PlayerSpec::GetDummyPlayerSpec(p_name_combined);
    }
  }

  // Welp, that didn't work.
  // As a fallback, just use the peer spec (account name, etc.)
  return peer_spec();
}

auto ConnectionToClient::GetClientInputDevice(int remote_id)
    -> ClientInputDevice* {
  auto i = client_input_devices_.find(remote_id);
  if (i == client_input_devices_.end()) {
    // InputDevices need to be manually allocated and passed to g_input to
    // store.
    auto cid = Object::NewDeferred<ClientInputDevice>(remote_id, this);
    client_input_devices_[remote_id] = cid;
    g_input->AddInputDevice(cid, false);
    return cid;
  }
  return i->second;
}

auto ConnectionToClient::GetAsUDP() -> ConnectionToClientUDP* {
  return nullptr;
}

void ConnectionToClient::HandleMasterServerClientInfo(PyObject* info_obj) {
  PyObject* profiles_obj = PyDict_GetItemString(info_obj, "p");
  if (profiles_obj != nullptr) {
    player_profiles_.Acquire(profiles_obj);
  }

  // This will also contain a public account-id (if the query was valid).
  // Store it away for whoever wants it.
  PyObject* public_id_obj = PyDict_GetItemString(info_obj, "u");
  if (public_id_obj != nullptr && Python::IsPyString(public_id_obj)) {
    peer_public_account_id_ = Python::GetPyString(public_id_obj);
  } else {
    peer_public_account_id_ = "";

    // If the server returned no valid account info for them
    // and we're not trusting peers, kick this fella right out
    // and ban him for a short bit (to hopefully limit rejoin spam).
    if (g_game->require_client_authentication()) {
      SendScreenMessage(
          "{\"t\":[\"serverResponses\","
          "\"Your account was rejected. Are you signed in?\"]}",
          1, 0, 0);
      Log("Master server found no valid account for '"
          + peer_spec().GetShortName() + "'; kicking.");

      // Not benning anymore. People were exploiting this by impersonating
      // other players using their public ids to get them banned from
      // their own servers/etc.
      // g_game->BanPlayer(peer_spec(), 1000 * 60);
      Error("");
    }
  }
  got_info_from_master_server_ = true;
}

auto ConnectionToClient::IsAdmin() const -> bool {
  if (peer_public_account_id_.empty()) {
    return false;
  }
  return (g_game->admin_public_ids().find(peer_public_account_id_)
          != g_game->admin_public_ids().end());
}

}  // namespace ballistica
