// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection_to_host.h"

#include <Python.h>

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/scene_v1/support/client_session_net.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

// How long to go between sending out null packets for pings.
const int kPingSendInterval = 2000;

ConnectionToHost::ConnectionToHost()
    : protocol_version_{
          classic::ClassicAppMode::GetSingleton()->host_protocol_version()} {}

auto ConnectionToHost::GetAsUDP() -> ConnectionToHostUDP* { return nullptr; }

ConnectionToHost::~ConnectionToHost() {
  // If we were considered 'connected', announce that we're leaving.
  if (can_communicate()) {
    // If we've already printed a 'connected' message, print 'disconnected'.
    // Otherwise say the connection was rejected.
    if (printed_connect_message_) {
      // Use the party/game name if we've got it; otherwise say
      // '${PEER-NAME}'s party'.
      std::string s;
      if (!party_name_.empty()) {
        s = g_base->assets->GetResourceString("leftGameText");
        Utils::StringReplaceOne(&s, "${NAME}", party_name_);
      } else {
        s = g_base->assets->GetResourceString("leftPartyText");
        Utils::StringReplaceOne(&s, "${NAME}", peer_spec().GetDisplayString());
      }
      g_base->ScreenMessage(s, {1, 0.5f, 0.0f});
      g_base->audio->SafePlaySysSound(base::SysSoundID::kCorkPop);
    } else {
      g_base->ScreenMessage(
          g_base->assets->GetResourceString("connectionRejectedText"),
          {1, 0, 0});
    }
  }
}

void ConnectionToHost::Update() {
  millisecs_t real_time = g_core->AppTimeMillisecs();

  // Send out null messages occasionally for ping measurement purposes.
  // Note that we currently only do this from the client since we might not
  // be sending things otherwise. The server on the other hand should be
  // sending lots of messages to clients so no need to add to the load there.
  if (can_communicate()
      && real_time - last_ping_send_time_ > kPingSendInterval) {
    std::vector<uint8_t> data(1);
    data[0] = BA_MESSAGE_NULL;
    SendReliableMessage(data);
    last_ping_send_time_ = real_time;
  }

  Connection::Update();
}

// Seems we get a false alarm here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "LocalValueEscapesScope"

void ConnectionToHost::HandleGamePacket(const std::vector<uint8_t>& data) {
  // If we've errored, ignore everything; we're just a zombie.
  if (errored()) {
    // Hmmm; do we want to respond with disconnect packets here?
    // (not remembering why server side does that but we don't).
    return;
  }

  if (data.empty()) {
    return;
  }

  switch (data[0]) {
    case BA_SCENEPACKET_HANDSHAKE: {
      if (data.size() <= 3) {
        break;
      }

      auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

      // We expect a > 3 byte handshake packet with protocol version as the
      // second and third bytes and name/info beyond that.
      // (player-spec for protocol <= 32 and info json dict for 33+).

      // If we don't support their protocol, let them know..
      bool compatible = false;
      uint16_t their_protocol_version;
      memcpy(&their_protocol_version, data.data() + 1,
             sizeof(their_protocol_version));
      if (their_protocol_version >= kProtocolVersionClientMin
          && their_protocol_version <= kProtocolVersionMax) {
        compatible = true;

        // If we are compatible, set our protocol version to match
        // what they're dealing.
        protocol_version_ = their_protocol_version;
      }

      // Ok now we know if we can talk to them. Respond so they know
      // whether they can talk to us.

      // (packet-type, our protocol-version, our spec/info)
      // For server-protocol < 32 we provide our player-spec.
      // For server-protocol 33+ we provide json info dict.
      if (their_protocol_version >= 33) {
        // Construct a json dict with our player-spec-string as one element
        JsonDict dict;
        dict.AddString("s", PlayerSpec::GetAccountPlayerSpec().GetSpecString());

        // Also add our public device id. Servers can
        // use this to combat spammers.
        dict.AddString("d", g_base->platform->GetPublicDeviceUUID());

        std::string out = dict.PrintUnformatted();

        std::vector<uint8_t> data2(3 + out.size());
        data2[0] = BA_SCENEPACKET_HANDSHAKE_RESPONSE;
        auto val = static_cast<uint16_t>(protocol_version_);
        memcpy(data2.data() + 1, &val, sizeof(val));
        memcpy(data2.data() + 3, out.c_str(), out.size());
        SendGamePacket(data2);
      } else {
        // (KILL THIS WHEN kProtocolVersionClientMin >= 33)
        std::string our_spec_str =
            PlayerSpec::GetAccountPlayerSpec().GetSpecString();
        std::vector<uint8_t> response(3 + our_spec_str.size());
        response[0] = BA_SCENEPACKET_HANDSHAKE_RESPONSE;
        auto val = static_cast<uint16_t>(protocol_version_);
        memcpy(response.data() + 1, &val, sizeof(val));
        memcpy(response.data() + 3, our_spec_str.c_str(), our_spec_str.size());
        SendGamePacket(response);
      }

      if (!compatible) {
        if (their_protocol_version > protocol_version()) {
          Error(g_base->assets->GetResourceString(
              "incompatibleNewerVersionHostText"));
        } else {
          Error(
              g_base->assets->GetResourceString("incompatibleVersionHostText"));
        }
        return;
      }

      // If we're freshly establishing that we're able to talk to them
      // in a language they understand, go ahead and kick some stuff off.
      if (!can_communicate()) {
        if (their_protocol_version >= 33) {
          // In newer protocols, handshake contains a json dict
          // so we can evolve it going forward.
          std::vector<char> string_buffer(data.size() - 3 + 1);
          memcpy(&(string_buffer[0]), &(data[3]), data.size() - 3);
          string_buffer[string_buffer.size() - 1] = 0;
          if (cJSON* handshake = cJSON_Parse(string_buffer.data())) {
            if (cJSON_IsObject(handshake)) {
              // We hash this to prove that we're us; keep it around.
              peer_hash_input_ = "";
              cJSON* pspec = cJSON_GetObjectItem(handshake, "s");
              if (cJSON_IsString(pspec)) {
                peer_hash_input_ += pspec->valuestring;
                set_peer_spec(PlayerSpec(pspec->valuestring));
              }
              cJSON* salt = cJSON_GetObjectItem(handshake, "l");
              if (cJSON_IsString(salt)) {
                peer_hash_input_ += salt->valuestring;
              }
            }
            cJSON_Delete(handshake);
          }
        } else {
          // (KILL THIS WHEN kProtocolVersionClientMin >= 33)
          // In older protocols, handshake simply contained a
          // player-spec for the host.

          // Pull host's PlayerSpec from the handshake packet.
          std::vector<char> string_buffer(data.size() - 3 + 1);
          memcpy(&(string_buffer[0]), &(data[3]), data.size() - 3);
          string_buffer[string_buffer.size() - 1] = 0;

          // We hash this to prove that we're us; keep it around.
          peer_hash_input_ = string_buffer.data();
          set_peer_spec(PlayerSpec(string_buffer.data()));
        }

        peer_hash_ = g_base->Plus()->CalcV1PeerHash(peer_hash_input_);

        set_can_communicate(true);
        appmode->LaunchClientSession();

        // NOTE:
        // we don't actually print a 'connected' message until after
        // we get our first message (it may influence the message we print and
        // there's also a chance we could still get booted after sending our
        // info message)

        // Wire ourselves up to drive the client-session we're in.
        auto* cs =
            dynamic_cast<ClientSessionNet*>(appmode->GetForegroundSession());
        assert(cs);
        assert(!cs->connection_to_host());
        client_session_ = cs;
        cs->SetConnectionToHost(this);

        // The very first thing we send is our client-info
        // which is a json dict with arbitrary data.
        {
          JsonDict dict;
          dict.AddNumber("b", kEngineBuildNumber);

          g_base->Plus()->V1SetClientInfo(&dict);

          // Pass the hash we generated from their handshake; they can use
          // this to make sure we're who we say we are.
          dict.AddString("ph", peer_hash_);
          std::string info = dict.PrintUnformatted();
          std::vector<uint8_t> msg(info.size() + 1);
          msg[0] = BA_MESSAGE_CLIENT_INFO;
          memcpy(&(msg[1]), info.c_str(), info.size());
          SendReliableMessage(msg);
        }

        // Send them our player-profiles so we can use them on their end.
        // (the host generally will pull these from the master server
        // to prevent cheating, but in some cases these are used)

        // On newer hosts we send these as json.
        if (protocol_version_ >= 32) {
          // (This is a borrowed ref)
          PyObject* profiles =
              g_base->python->GetRawConfigValue("Player Profiles");
          PythonRef empty_dict;
          if (!profiles) {
            g_core->logging->Log(
                LogName::kBaNetworking, LogLevel::kError,
                "No profiles found; sending empty list to host");
            empty_dict.Steal(PyDict_New());
            profiles = empty_dict.get();
          }
          if (profiles != nullptr) {
            // Dump them to a json string.
            PythonRef args(Py_BuildValue("(O)", profiles), PythonRef::kSteal);
            PythonRef keywds(Py_BuildValue("{s(ss)}", "separators", ",", ":"),
                             PythonRef::kSteal);
            PythonRef results =
                g_core->python->objs()
                    .Get(core::CorePython::ObjID::kJsonDumpsCall)
                    .Call(args, keywds);
            if (!results.exists()) {
              g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                                   "Error getting json dump of local profiles");
            } else {
              try {
                // Pull the string as utf8 and send.
                std::string s = results.ValueAsLString();
                std::vector<uint8_t> msg(s.size() + 1);
                msg[0] = BA_MESSAGE_CLIENT_PLAYER_PROFILES_JSON;
                memcpy(&(msg[1]), &s[0], s.size());
                SendReliableMessage(msg);
              } catch (const std::exception& e) {
                g_core->logging->Log(
                    LogName::kBaNetworking, LogLevel::kError,
                    std::string("Error sending player profiles to host: ")
                        + e.what());
              }
            }
          }
        } else {
          g_core->logging->Log(
              LogName::kBaNetworking, LogLevel::kError,
              "Connected to old protocol; can't send player profiles");
        }
      }
      break;
    }

    case BA_SCENEPACKET_DISCONNECT: {
      // They told us to leave, so lets do so :-(
      ErrorSilent();
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

#pragma clang diagnostic pop

void ConnectionToHost::HandleMessagePacket(const std::vector<uint8_t>& buffer) {
  assert(g_base->InLogicThread());

  if (buffer.empty()) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "Got invalid HandleMessagePacket");
    return;
  }

  // If the first message we get is not host-info, it means we're talking to
  // an older host that won't be sending us info.
  if (!got_host_info_ && buffer[0] != BA_MESSAGE_HOST_INFO) {
    build_number_ = 0;
    got_host_info_ = true;
  }

  switch (buffer[0]) {
    case BA_MESSAGE_HOST_INFO: {
      if (buffer.size() > 1) {
        std::vector<char> str_buffer(buffer.size());
        std::copy(buffer.begin() + 1, buffer.end(), str_buffer.begin());
        str_buffer.back() = 0;  // Ensure null termination
        if (cJSON* info = cJSON_Parse(str_buffer.data())) {
          if (cJSON_IsObject(info)) {
            // Build number.
            cJSON* b = cJSON_GetObjectItem(info, "b");
            if (cJSON_IsNumber(b)) {
              build_number_ = b->valueint;
            } else {
              BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                          "No buildnumber in hostinfo msg.");
            }
            // Party name.
            cJSON* n = cJSON_GetObjectItem(info, "n");
            if (cJSON_IsString(n)) {
              party_name_ = Utils::GetValidUTF8(n->valuestring, "bsmhi");
            }
          }
          cJSON_Delete(info);
        } else {
          BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                      "Got invalid json in hostinfo message: "
                          + std::string(str_buffer.data()) + ".");
        }
      }
      got_host_info_ = true;
      break;
    }

    case BA_MESSAGE_PARTY_ROSTER: {
      if (buffer.size() >= 3 && buffer[buffer.size() - 1] == 0) {
        // Expand this into a json object; if it's valid, replace the game's
        // current roster with it.
        cJSON* new_roster =
            cJSON_Parse(reinterpret_cast<const char*>(buffer.data()) + 1);

        // Watch for invalid data.
        if (new_roster && !cJSON_IsArray(new_roster)) {
          cJSON_Delete(new_roster);
          new_roster = nullptr;
          BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                      "Got invalid json in hostinfo message.");
        }

        if (new_roster) {
          if (auto* appmode = classic::ClassicAppMode::GetActive()) {
            appmode->SetGameRoster(new_roster);
          }
        }
      }
      break;
    }

    case BA_MESSAGE_JMESSAGE: {
      // High level json messages (nice and easy to expand on but not
      // especially efficient).
      if (buffer.size() >= 3 && buffer[buffer.size() - 1] == 0) {
        if (cJSON* msg =
                cJSON_Parse(reinterpret_cast<const char*>(buffer.data() + 1))) {
          if (cJSON_IsObject(msg)) {
            cJSON* type = cJSON_GetObjectItem(msg, "t");
            if (cJSON_IsNumber(type)) {
              switch (type->valueint) {
                case BA_JMESSAGE_SCREEN_MESSAGE: {
                  std::string m;
                  float r{1.0f};
                  float g{1.0f};
                  float b{1.0f};
                  cJSON* r_obj = cJSON_GetObjectItem(msg, "r");
                  cJSON* g_obj = cJSON_GetObjectItem(msg, "g");
                  cJSON* b_obj = cJSON_GetObjectItem(msg, "b");
                  cJSON* m_obj = cJSON_GetObjectItem(msg, "m");
                  if (cJSON_IsNumber(r_obj)) {
                    r = static_cast<float>(r_obj->valuedouble);
                  }
                  if (cJSON_IsNumber(g_obj)) {
                    g = static_cast<float>(g_obj->valuedouble);
                  }
                  if (cJSON_IsNumber(b_obj)) {
                    b = static_cast<float>(b_obj->valuedouble);
                  }
                  if (cJSON_IsString(m_obj)) {
                    m = m_obj->valuestring;
                    g_base->ScreenMessage(m, {r, g, b});
                  }
                  break;
                }
                default:
                  break;
              }
            }
          }
          cJSON_Delete(msg);
        }
      }
      break;
    }

    case BA_MESSAGE_PARTY_MEMBER_JOINED: {
      if (buffer.size() > 1) {
        std::vector<char> str_buffer(buffer.size());
        memcpy(&(str_buffer[0]), &(buffer[1]), buffer.size() - 1);
        str_buffer[str_buffer.size() - 1] = 0;
        std::string s =
            g_base->assets->GetResourceString("playerJoinedPartyText");
        Utils::StringReplaceOne(
            &s, "${NAME}", PlayerSpec(str_buffer.data()).GetDisplayString());
        g_base->ScreenMessage(s, {0.5f, 1.0f, 0.5f});
        g_base->audio->SafePlaySysSound(base::SysSoundID::kGunCock);
      }
      break;
    }

    case BA_MESSAGE_PARTY_MEMBER_LEFT: {
      // Host is informing us that someone in the party left.
      if (buffer.size() > 1) {
        std::vector<char> str_buffer(buffer.size());
        memcpy(&(str_buffer[0]), &(buffer[1]), buffer.size() - 1);
        str_buffer[str_buffer.size() - 1] = 0;
        std::string s =
            g_base->assets->GetResourceString("playerLeftPartyText");
        Utils::StringReplaceOne(
            &s, "${NAME}", PlayerSpec(&(str_buffer[0])).GetDisplayString());
        g_base->ScreenMessage(s, {1, 0.5f, 0.0f});
        g_base->audio->SafePlaySysSound(base::SysSoundID::kCorkPop);
      }
      break;
    }

    case BA_MESSAGE_ATTACH_REMOTE_PLAYER_2: {
      // New-style packet which includes a 32-bit player_id.
      if (buffer.size() != 6) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Invalid attach-remote-player-2 msg");
        break;
      }

      // Grab this local input-device and tell it its controlling something on
      // the host.
      base::InputDevice* input_device =
          g_base->input->GetInputDevice(buffer[1]);
      if (input_device) {
        // We expect this device to be rocking our delegate type.
        if (auto* delegate = dynamic_cast<SceneV1InputDeviceDelegate*>(
                &input_device->delegate())) {
          uint32_t player_id;
          memcpy(&player_id, &(buffer[2]), sizeof(player_id));
          delegate->AttachToRemotePlayer(this,
                                         static_cast_check_fit<int>(player_id));
        } else {
          g_core->logging->Log(
              LogName::kBaNetworking, LogLevel::kError,
              "InputDevice does not have a SceneV1 delegate as expected "
              "(loc1).");
        }
      }

      // Once we've gotten one of these we know to ignore the old style.
      ignore_old_attach_remote_player_packets_ = true;
      break;
    }

    case BA_MESSAGE_ATTACH_REMOTE_PLAYER: {
      // If our server uses the newer ones, we should ignore these.
      if (!ignore_old_attach_remote_player_packets_) {
        // This message was used in older versions but is flawed in that
        // player-id is an 8 bit value which isn't enough for longstanding
        // public servers.
        // TODO(ericf): can remove this once back-compat-protocol > 29.
        if (buffer.size() != 3) {
          g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                               "Invalid attach-remote-player msg.");
          break;
        }

        // Grab this local input-device and tell it its controlling something
        // on the host.
        base::InputDevice* input_device =
            g_base->input->GetInputDevice(buffer[1]);
        if (input_device) {
          // We expect this device to be rocking our delegate type.
          if (auto* delegate = dynamic_cast<SceneV1InputDeviceDelegate*>(
                  &input_device->delegate())) {
            delegate->AttachToRemotePlayer(this, buffer[2]);
          } else {
            g_core->logging->Log(
                LogName::kBaNetworking, LogLevel::kError,
                "InputDevice does not have a SceneV1 delegate as expected "
                "(loc2).");
          }
        }
      }
      break;
    }

    case BA_MESSAGE_CHAT: {
      if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
        appmode->LocalDisplayChatMessage(buffer);
      }
      break;
    }

    case BA_MESSAGE_DETACH_REMOTE_PLAYER: {
      if (buffer.size() != 2) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Invalid detach-remote-player msg");
        break;
      }
      // Server is telling us that our local input device is no longer
      // controlling a player.
      base::InputDevice* input_device =
          g_base->input->GetInputDevice(buffer[1]);
      if (input_device) {
        // We expect this device to be rocking our delegate type.
        if (auto* delegate = dynamic_cast<SceneV1InputDeviceDelegate*>(
                &input_device->delegate())) {
          auto* connection_to_host = delegate->GetRemotePlayer();
          if (connection_to_host == this) {
            // Normally detaching triggers a message to the server,
            // but that would be redundant. This will prevent that.
            delegate->InvalidateConnectionToHost();

            delegate->DetachFromPlayer();

          } else {
            // If we detached from our end, connection-to-host will already
            // be cleared out at this point. Just complain if that's not
            // the case.
            if (connection_to_host != nullptr) {
              g_core->logging->Log(
                  LogName::kBaNetworking, LogLevel::kError,
                  "InputDevice does not have a SceneV1 delegate as expected "
                  "(loc3).");
            }
          }
        }
      }
      break;
    }

    case BA_MESSAGE_SESSION_COMMANDS:
    case BA_MESSAGE_SESSION_RESET:
    case BA_MESSAGE_SESSION_DYNAMICS_CORRECTION: {
      // These commands are consumed directly by the session.
      if (client_session_.exists()) {
        client_session_->HandleSessionMessage(buffer);
      }
      break;
    }

    default: {
      Connection::HandleMessagePacket(buffer);
    }
  }

  // After we get our first message from the server is when we print our
  // 'connected to XXX' message.
  if (!printed_connect_message_) {
    std::string s;

    // If we've got a name for their party, use it; otherwise call it
    // '${NAME}'s party'.
    if (!party_name_.empty()) {
      s = g_base->assets->GetResourceString("connectedToGameText");
      Utils::StringReplaceOne(&s, "${NAME}", party_name_);
    } else {
      s = g_base->assets->GetResourceString("connectedToPartyText");
      Utils::StringReplaceOne(&s, "${NAME}", peer_spec().GetDisplayString());
    }
    g_base->ScreenMessage(s, {0.5f, 1, 0.5f});
    g_base->audio->SafePlaySysSound(base::SysSoundID::kGunCock);

    printed_connect_message_ = true;
  }
}

}  // namespace ballistica::scene_v1
