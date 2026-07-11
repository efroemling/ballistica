// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection_to_host.h"

#include <Python.h>

#include <algorithm>
#include <string>
#include <string_view>
#include <vector>

#include "ballistica/base/app_platform/app_platform.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/scene_v1/support/client_session_net.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/shared/generic/json_facade.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

// How long to go between sending out null packets for pings.
const int kPingSendInterval = 2000;

static auto MakeServerResponseJson_(const std::string& passed_str)
    -> std::string {
  // A {"t": ["serverResponses", <passed_str>]} object.
  JsonBuilder builder;
  builder.root_object().AddArray("t").Add("serverResponses").Add(passed_str);
  std::string result = builder.Write();

  return result;
}

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
      g_base->audio->SafePlayBuiltinSound(base::BuiltinSoundID::kAudioCorkPop);
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
      // second and third bytes and name/info beyond that. (player-spec for
      // protocol <= 32 and info json dict for 33+).

      // If we don't support their protocol, let them know.
      bool compatible = false;
      uint16_t their_protocol_version;
      memcpy(&their_protocol_version, data.data() + 1,
             sizeof(their_protocol_version));
      g_core->logging->Log(
          LogName::kBaNetworking, LogLevel::kDebug, [their_protocol_version] {
            return "ConnectionToHost: received HANDSHAKE (host protocol "
                   + std::to_string(their_protocol_version) + ").";
          });
      if (their_protocol_version >= kProtocolVersionClientMin
          && their_protocol_version <= kProtocolVersionMax) {
        compatible = true;

        // If we are compatible, set our protocol version to match what
        // they're dealing.
        protocol_version_ = their_protocol_version;
      }

      // See if the server uses v2 auth.
      if (!got_v2_auth_usage_) {
        // If server requires v2 auth, it will have a 'v2a' value in its
        // handshake which is its global-app-instance-uuid. We'll ask the
        // cloud to send our account info to that app-instance and give us a
        // token we can use to identify ourself as that account to them.
        if (their_protocol_version >= 33) {
          if (auto doc = JsonDoc::Parse(std::string_view(
                  reinterpret_cast<const char*>(data.data() + 3),
                  data.size() - 3))) {
            if (auto v2a = doc->root()["v2a"].as_string()) {
              v2_auth_global_app_instance_id_ = std::string(*v2a);
            }
          }
        }
        got_v2_auth_usage_ = true;
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [this] {
          return v2_auth_global_app_instance_id_.has_value()
                     ? ("ConnectionToHost: host uses v2-auth "
                        "(global-app-instance="
                        + *v2_auth_global_app_instance_id_ + ").")
                     : std::string(
                           "ConnectionToHost: host does not use v2-auth.");
        });
      }

      std::optional<std::string> v2_auth_token;

      // If the server does use v2 auth, process v2-auth requests as needed
      // and hold off on handshake-responses until something goes through.
      assert(got_v2_auth_usage_);
      if (v2_auth_global_app_instance_id_.has_value()) {
        auto args = PythonRef::Stolen(
            Py_BuildValue("(s)", v2_auth_global_app_instance_id_->c_str()));
        auto result = g_base->python->objs()
                          .Get(base::BasePython::ObjID::kV2AuthRequestCall)
                          .Call(args);
        if (!result.exists()) {
          g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                               "Error running v2_auth_request.");
        } else {
          if (result.ValueIsNone()) {
            // Still waiting...
          } else {
            auto valid_format{false};
            if (result.ValueIsSequence()) {
              auto vals{result.ValueAsSequence()};
              if (vals.size() == 2 && PyBool_Check(*vals[0])
                  && vals[1].ValueIsString()) {
                // Success!!!
                auto success{vals[0].ValueAsBool()};
                auto sval{vals[1].ValueAsString()};
                valid_format = true;

                if (!success) {
                  // If auth rejected us, show auth error message and fail.
                  Error(MakeServerResponseJson_(sval));
                  return;
                } else {
                  // Auth accepted us! Pass along this token in our
                  // handshake-response.
                  v2_auth_token = sval;
                }
              }
            }

            if (!valid_format) {
              g_core->logging->Log(
                  LogName::kBaNetworking, LogLevel::kError,
                  "Invalid type returned from v2_auth_request.");
            }
          }
        }
        // If we're still waiting on a token, go no further.
        if (!v2_auth_token.has_value()) {
          return;
        }
      }

      // Ok now we know if we can talk to them. Respond so they know whether
      // they can talk to us.

      // (packet-type, our protocol-version, our spec/info)
      // For server-protocol < 32 we provide our player-spec.
      // For server-protocol 33+ we provide json info dict.
      if (their_protocol_version >= 33) {
        // Construct a json dict with our player-spec-string as one element
        JsonBuilder builder;
        JsonObjBuilder dict = builder.root_object();
        dict.Add("s", PlayerSpec::GetAccountPlayerSpec().GetSpecString());

        // Also add our public device id. Servers can use this to combat
        // spammers.
        dict.Add("d", g_base->platform->GetPublicDeviceUUID());

        // Add v2 auth token.
        if (v2_auth_token.has_value()) {
          dict.Add("v2at", *v2_auth_token);
        }

        std::string out = builder.Write();

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

      // If we're freshly establishing that we're able to talk to them in a
      // language they understand, go ahead and kick some stuff off.
      if (!can_communicate()) {
        if (their_protocol_version >= 33) {
          // In newer protocols, handshake contains a json dict so we can
          // evolve it going forward.
          if (auto doc = JsonDoc::Parse(std::string_view(
                  reinterpret_cast<const char*>(data.data() + 3),
                  data.size() - 3))) {
            JsonRef root = doc->root();
            if (root.is_object()) {
              // We hash this to prove that we're us; keep it around.
              peer_hash_input_ = "";
              if (auto pspec = root["s"].as_string()) {
                peer_hash_input_ += *pspec;
                set_peer_spec(PlayerSpec(std::string(*pspec)));
              }
              if (auto salt = root["l"].as_string()) {
                peer_hash_input_ += *salt;
              }
            }
          }
        } else {
          // (KILL THIS WHEN kProtocolVersionClientMin >= 33)
          //
          // In older protocols, handshake simply contained a player-spec
          // for the host.

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
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [this] {
          return "ConnectionToHost: can_communicate=true "
                 "(protocol="
                 + std::to_string(protocol_version_)
                 + ", peer_spec=" + peer_spec().GetDisplayString() + ").";
        });
        appmode->LaunchClientSession();

        // NOTE:
        //
        // we don't actually print a 'connected' message until after we get
        // our first message (it may influence the message we print and
        // there's also a chance we could still get booted after sending our
        // info message)

        // Wire ourselves up to drive the client-session we're in.
        auto* cs =
            dynamic_cast<ClientSessionNet*>(appmode->GetForegroundSession());
        assert(cs);
        assert(!cs->connection_to_host());
        client_session_ = cs;
        cs->SetConnectionToHost(this);

        // The very first thing we send is our client-info which is a json
        // dict with arbitrary data.
        {
          JsonBuilder builder;
          JsonObjBuilder dict = builder.root_object();
          dict.Add("b", kEngineBuildNumber);

          g_base->Plus()->V1SetClientInfo(&dict);

          // Pass the hash we generated from their handshake; they can use
          // this for v1 client auth.
          dict.Add("ph", peer_hash_);
          std::string info = builder.Write();
          std::vector<uint8_t> msg(info.size() + 1);
          msg[0] = BA_MESSAGE_CLIENT_INFO;
          memcpy(&(msg[1]), info.c_str(), info.size());
          SendReliableMessage(msg);
        }

        // Send them our player-profiles so we can use them on their end.
        // (the host generally will pull these from the master server to
        // prevent cheating, but in some cases these are used).

        if (v2_auth_global_app_instance_id_.has_value()) {
          // Host has enabled v2-auth. Don't bother sending our profiles
          // directly as they will be ignored anyway (host gets profiles
          // from cloud in this case).
        } else if (protocol_version_ >= 32) {
          // On newer hosts we send profiles as json.
          //
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
        // Payload is the bytes after the message-type byte (no trailing null).
        std::string_view info_str(
            reinterpret_cast<const char*>(buffer.data() + 1),
            buffer.size() - 1);
        if (auto doc = JsonDoc::Parse(info_str)) {
          JsonRef root = doc->root();
          // Build number.
          if (auto b = root["b"].as_double()) {
            build_number_ = static_cast<int>(*b);
          } else {
            BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                        "No buildnumber in hostinfo msg.");
          }
          // Party name.
          if (auto n = root["n"].as_string()) {
            party_name_ = Utils::GetValidUTF8(std::string(*n).c_str(), "bsmhi");
          }
        } else {
          BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                      "Got invalid json in hostinfo message: "
                          + std::string(info_str) + ".");
        }
      }
      got_host_info_ = true;
      break;
    }

    case BA_MESSAGE_PARTY_ROSTER: {
      if (buffer.size() >= 3 && buffer[buffer.size() - 1] == 0) {
        // Parse the (untrusted) roster json; if it's a valid array, replace
        // the game's current roster with it. The payload is the bytes between
        // the message-type byte and the trailing null terminator.
        auto doc = JsonDoc::Parse(
            std::string_view(reinterpret_cast<const char*>(buffer.data() + 1),
                             buffer.size() - 2));
        if (doc.has_value() && doc->root().is_array()) {
          if (auto* appmode = classic::ClassicAppMode::GetActive()) {
            appmode->SetGameRoster(doc->root());
          }
        } else {
          BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                      "Got invalid json in party-roster message.");
        }
      }
      break;
    }

    case BA_MESSAGE_JMESSAGE: {
      // High level json screen-messages (nice and easy to expand on but not
      // especially efficient).
      if (buffer.size() >= 3 && buffer[buffer.size() - 1] == 0) {
        // Payload is the bytes between the type byte and the trailing null.
        if (auto doc = JsonDoc::Parse(std::string_view(
                reinterpret_cast<const char*>(buffer.data() + 1),
                buffer.size() - 2))) {
          JsonRef root = doc->root();
          if (auto type = root["t"].as_double()) {
            switch (static_cast<int>(*type)) {
              case BA_JMESSAGE_SCREEN_MESSAGE: {
                if (auto m = root["m"].as_string()) {
                  auto r = static_cast<float>(root["r"].double_or(1.0));
                  auto g = static_cast<float>(root["g"].double_or(1.0));
                  auto b = static_cast<float>(root["b"].double_or(1.0));
                  g_base->ScreenMessage(std::string(*m), {r, g, b});
                }
                break;
              }
              case BA_JMESSAGE_RUMBLE: {
                // The host addresses us by the local device-index we
                // originally claimed a remote player with (see
                // SceneV1InputDeviceDelegate::RequestPlayer()), so we can
                // look it up directly and rumble it ourselves.
                auto device_index = root["d"].as_int();
                if (device_index) {
                  if (base::InputDevice* input_device =
                          g_base->input->GetInputDevice(
                              static_cast<int>(*device_index))) {
                    auto low = static_cast<float>(root["lo"].double_or(1.0));
                    auto high = static_cast<float>(root["hi"].double_or(1.0));
                    auto duration =
                        static_cast<int>(root["ms"].int_or(150));
                    input_device->Rumble(low, high, duration);
                  }
                }
                break;
              }
              default:
                break;
            }
          }
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
        g_base->audio->SafePlayBuiltinSound(
            base::BuiltinSoundID::kAudioGunCocking);
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
        g_base->audio->SafePlayBuiltinSound(
            base::BuiltinSoundID::kAudioCorkPop);
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
      // Disabling this check for now - looks like there are legit multipart
      // messages of that size coming through.
      //
      // if (buffer[0] == BA_MESSAGE_MULTIPART
      //     && multipart_buffer_size() > 50000) {
      //   g_core->logging->Log(
      //       LogName::kBaNetworking, LogLevel::kError,
      //       "Multipart message from host exceeded size limit;
      //       disconnecting.");
      //   Error("");
      //   return;
      // }
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
    g_base->audio->SafePlayBuiltinSound(base::BuiltinSoundID::kAudioGunCocking);

    printed_connect_message_ = true;
  }
}

}  // namespace ballistica::scene_v1
