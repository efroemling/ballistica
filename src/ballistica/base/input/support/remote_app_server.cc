// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/support/remote_app_server.h"

#include <cstdio>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

// Just used privately by the remote-server machinery.
enum class RemoteAppServer::RemoteEventType {
  kDPadH,
  kDPadV,
  kPunchPress,
  kPunchRelease,
  kJumpPress,
  kJumpRelease,
  kThrowPress,
  kThrowRelease,
  kBombPress,
  kBombRelease,
  kMenu,  // Old.
  kMenuPress,
  kMenuRelease,
  kHoldPositionPress,
  kHoldPositionRelease,
  kRunPress,
  kRunRelease
};

RemoteAppServer::RemoteAppServer() = default;

RemoteAppServer::~RemoteAppServer() = default;

void RemoteAppServer::HandleData(int socket, uint8_t* buffer, size_t amt,
                                 struct sockaddr* addr, size_t addr_len) {
  if (amt == 0) {
    return;
  }
  switch (buffer[0]) {
    case BA_PACKET_REMOTE_GAME_QUERY: {
      // Ship them a response packet with our name.
      char msg[256];
      std::string name = g_core->platform->GetDeviceName();
      msg[0] = BA_PACKET_REMOTE_GAME_RESPONSE;
      strncpy(msg + 1, name.c_str(), sizeof(msg) - 1);
      msg[255] = 0;
      size_t msg_len = 1 + strlen(msg + 1);

      // This needs to be locked during any sd changes/writes.
      std::scoped_lock lock(g_base->network_reader->sd_mutex());
      sendto(socket, msg, static_cast_check_fit<socket_send_length_t>(msg_len),
             0, addr, static_cast<socklen_t>(addr_len));

      // if (result != msg_len) {
      // Hmm; ive seen errno 64 (network down) and 65 (package not installed)
      // here, but I don't know what we could do in response. Just gonna ignore
      // them.
      // }
      break;
    }
    case BA_PACKET_REMOTE_ID_REQUEST: {
      if (amt < 5 || amt > 127) {
        BA_LOG_ONCE(LogName::kBaInput, LogLevel::kError,
                    "Received invalid BA_PACKET_REMOTE_ID_REQUEST of length "
                        + std::to_string(amt));
        break;
      }

      // Second byte is protocol version.
      int protocol_version = buffer[1];

      // Make sure we speak the same language.
      if (protocol_version != kRemoteAppProtocolVersion) {
        uint8_t data[2] = {
            BA_PACKET_REMOTE_DISCONNECT,
            static_cast_check_fit<uint8_t>(RemoteError::kVersionMismatch)};

        // This needs to be locked during any sd changes/writes.
        std::scoped_lock lock(g_base->network_reader->sd_mutex());
        sendto(socket, reinterpret_cast<char*>(data), sizeof(data), 0, addr,
               static_cast<socklen_t>(addr_len));
        break;
      }

      // Third and fourth bytes are request id.
      int16_t request_id;
      memcpy(&request_id, buffer + 2, sizeof(request_id));

      // This is now a protocol-version-request. It used to be an address index
      // from the other end so probably will be a value between 1 and 5 or so on
      // older builds.
      int protocol_request = buffer[4];
      int protocol_response =
          protocol_request;  // Old default was to return same value.

      // If they sent 50, it means they want protocol v2 (24 bit states).
      // In that case we return 100 to say 'ok, we support that version'.
      // Note to self (years later): please explain to me why I did this.
      bool using_v2 = (protocol_request == 50);
      if (using_v2) {
        protocol_response = 100;
      }

      // Remaining bytes are name (up to 100 bytes).
      char name[101];
      assert(amt >= 5);
      size_t name_len = amt - 5;
      if (name_len > 100) {
        name_len = 100;
      }
      strncpy(name, reinterpret_cast<char*>(buffer) + 5, name_len);
      name[name_len] = 0;
      int client_id = GetClient(request_id, addr, static_cast<int>(addr_len),
                                name, using_v2);

      // If we've got a slot for this client, tell them what their id is.
      if (client_id != -1) {
        uint8_t data[3] = {BA_PACKET_REMOTE_ID_RESPONSE,
                           static_cast<uint8_t>(client_id),
                           static_cast<uint8_t>(protocol_response)};

        // This needs to be locked during any sd changes/writes.
        std::scoped_lock lock(g_base->network_reader->sd_mutex());
        sendto(socket, reinterpret_cast<char*>(data), sizeof(data), 0, addr,
               static_cast<socklen_t>(addr_len));
      } else {
        // No room.
        uint8_t data[2] = {BA_PACKET_REMOTE_DISCONNECT,
                           static_cast_check_fit<uint8_t>(
                               RemoteError::kNotAcceptingConnections)};

        // This needs to be locked during any sd changes/writes.
        std::scoped_lock lock(g_base->network_reader->sd_mutex());
        sendto(socket, reinterpret_cast<char*>(data), sizeof(data), 0, addr,
               static_cast<socklen_t>(addr_len));
      }
      break;
    }
    case BA_PACKET_REMOTE_DISCONNECT: {
      // They told us they're leaving.. free up their slot.
      if (amt == 2 && buffer[1] < kMaxRemoteAppClients) {
        int joystickID = buffer[1];

        // Tell our delegate to kill its local joystick.
        RemoteAppClient* client = clients_ + joystickID;
        if (clients_[joystickID].in_use) {
          // Print 'Billy Bob's iPhone Disconnected'.
          char m[256];
          snprintf(m, sizeof(m), "%s", client->display_name);

          // Replace ${CONTROLLER} with it in our message.
          std::string s =
              g_base->assets->GetResourceString("controllerDisconnectedText");
          Utils::StringReplaceOne(&s, "${CONTROLLER}", m);
          g_base->logic->event_loop()->PushCall([s] {
            g_base->graphics->screenmessages->AddScreenMessage(
                s, Vector3f(1, 1, 1));
          });
          g_base->logic->event_loop()->PushCall(
              [] { g_base->audio->SafePlaySysSound(SysSoundID::kCorkPop); });
          g_base->input->PushRemoveInputDeviceCall(client->joystick_, false);
          client->joystick_ = nullptr;
          client->in_use = false;
          client->name[0] = 0;
        }

        // Send an ack.
        uint8_t data[1] = {BA_PACKET_REMOTE_DISCONNECT_ACK};

        // This needs to be locked during any sd changes/writes.
        std::scoped_lock lock(g_base->network_reader->sd_mutex());
        sendto(socket, reinterpret_cast<char*>(data), 1, 0, addr,
               static_cast<socklen_t>(addr_len));
      }
      break;
    }
    case BA_PACKET_REMOTE_STATE2: {
      // Has to be at least 4 bytes.
      // (msg-type, joystick-id, state-count, starting-state-id)
      if (amt < 4) {
        break;
      }

      uint8_t joystick_id = buffer[1];
      uint8_t state_count = buffer[2];
      uint8_t state_id = buffer[3];

      // If its not an active joystick, let them know they're not playing
      // (this can happen if they time-out but still try to keep talking to us).
      if (!clients_[joystick_id].in_use) {
        uint8_t data[2] = {
            BA_PACKET_REMOTE_DISCONNECT,
            static_cast_check_fit<uint8_t>(RemoteError::kNotConnected)};

        // This needs to be locked during any sd changes/writes.
        std::scoped_lock lock(g_base->network_reader->sd_mutex());
        sendto(socket, reinterpret_cast<char*>(data), sizeof(data), 0, addr,
               static_cast<socklen_t>(addr_len));
        break;
      }

      // Each state is 2 bytes. So make sure our length adds up.
      if (amt != 4 + state_count * 3) {
        BA_LOG_ONCE(LogName::kBaInput, LogLevel::kError,
                    "Invalid state packet");
        return;
      }
      RemoteAppClient* client = clients_ + joystick_id;

      // Take note that we heard from them.
      client->last_contact_time = g_core->AppTimeMillisecs();

      // Ok now iterate.
      uint8_t* val = buffer + 4;
      for (int i = 0; i < state_count; i++) {
        // If we're behind enough, just skip ahead to here
        uint8_t diff = state_id - client->next_state_id;

        // Diffs close to 255 are probably just retransmitted states we just
        // looked at.
        if (diff > 10 && diff < 200) {
          client->next_state_id = state_id;
        }

        // If this is the next state we're looking for, apply it.
        if (client->next_state_id == state_id) {
          uint32_t last_state = client->state;
          uint32_t state = val[0] + (val[1] << 8u) + (val[2] << 16u);
          uint32_t h_raw = (state >> 8u) & 0xFFu;
          uint32_t v_raw = (state >> 16u) & 0xFFu;
          uint32_t h_raw_last = (last_state >> 8u) & 0xFFu;
          uint32_t v_raw_last = (last_state >> 16u) & 0xFFu;
          float dpad_h, dpad_v;
          dpad_h = -1.0f + 2.0f * (static_cast<float>(h_raw) / 255.0f);
          dpad_v = -1.0f + 2.0f * (static_cast<float>(v_raw) / 255.0f);
          float last_dpad_h, last_dpad_v;
          last_dpad_h =
              -1.0f + 2.0f * (static_cast<float>(h_raw_last) / 255.0f);
          last_dpad_v =
              -1.0f + 2.0f * (static_cast<float>(v_raw_last) / 255.0f);

          // Process this first since it can affect how other events are
          // handled.
          if ((last_state & kRemoteStateHoldPosition)
              && !(state & kRemoteStateHoldPosition)) {
            HandleRemoteEvent(client, RemoteEventType::kHoldPositionRelease);
          } else if (!(last_state & kRemoteStateHoldPosition)
                     && (state & kRemoteStateHoldPosition)) {
            HandleRemoteEvent(client, RemoteEventType::kHoldPositionPress);
          }
          if (dpad_h != last_dpad_h) {
            HandleRemoteFloatEvent(client, RemoteEventType::kDPadH, dpad_h);
          }
          if (dpad_v != last_dpad_v) {
            HandleRemoteFloatEvent(client, RemoteEventType::kDPadV, dpad_v);
          }
          if ((last_state & kRemoteStateBomb) && !(state & kRemoteStateBomb)) {
            HandleRemoteEvent(client, RemoteEventType::kBombRelease);
          } else if (!(last_state & kRemoteStateBomb)
                     && (state & kRemoteStateBomb)) {
            HandleRemoteEvent(client, RemoteEventType::kBombPress);
          }
          if ((last_state & kRemoteStateJump) && !(state & kRemoteStateJump)) {
            HandleRemoteEvent(client, RemoteEventType::kJumpRelease);
          } else if (!(last_state & kRemoteStateJump)
                     && (state & kRemoteStateJump)) {
            HandleRemoteEvent(client, RemoteEventType::kJumpPress);
          }
          if ((last_state & kRemoteStatePunch)
              && !(state & kRemoteStatePunch)) {
            HandleRemoteEvent(client, RemoteEventType::kPunchRelease);
          } else if (!(last_state & kRemoteStatePunch)
                     && (state & kRemoteStatePunch)) {
            HandleRemoteEvent(client, RemoteEventType::kPunchPress);
          }
          if ((last_state & kRemoteStateThrow)
              && !(state & kRemoteStateThrow)) {
            HandleRemoteEvent(client, RemoteEventType::kThrowRelease);
          } else if (!(last_state & kRemoteStateThrow)
                     && (state & kRemoteStateThrow)) {
            HandleRemoteEvent(client, RemoteEventType::kThrowPress);
          }
          if ((last_state & kRemoteStateMenu) && !(state & kRemoteStateMenu)) {
            HandleRemoteEvent(client, RemoteEventType::kMenuRelease);
          } else if (!(last_state & kRemoteStateMenu)
                     && (state & kRemoteStateMenu)) {
            HandleRemoteEvent(client, RemoteEventType::kMenuPress);
          }
          if ((last_state & kRemoteStateRun) && !(state & kRemoteStateRun)) {
            HandleRemoteEvent(client, RemoteEventType::kRunRelease);
          } else if (!(last_state & kRemoteStateRun)
                     && (state & kRemoteStateRun)) {
            HandleRemoteEvent(client, RemoteEventType::kRunPress);
          }
          client->state = state;
          client->next_state_id++;
        }
        state_id++;
        val += 3;
      }

      // Ok now send an ack with the state ID we're looking for next.
      uint8_t data[2] = {BA_PACKET_REMOTE_STATE_ACK, client->next_state_id};

      // This needs to be locked during any sd changes/writes.
      std::scoped_lock lock(g_base->network_reader->sd_mutex());
      sendto(socket, reinterpret_cast<char*>(data), 2, 0, addr,
             static_cast<socklen_t>(addr_len));

      break;
    }
    case BA_PACKET_REMOTE_STATE: {
      // Has to be at least 4 bytes.
      // (msg-type, joystick-id, state-count, starting-state-id)
      if (amt < 4) break;

      // This was used on older versions of the remote app; no longer supported.
      {
        uint8_t data[2] = {
            BA_PACKET_REMOTE_DISCONNECT,
            static_cast_check_fit<uint8_t>(RemoteError::kVersionMismatch)};

        // This needs to be locked during any sd changes/writes.
        std::scoped_lock lock(g_base->network_reader->sd_mutex());
        sendto(socket, reinterpret_cast<char*>(data), sizeof(data), 0, addr,
               static_cast<socklen_t>(addr_len));
        break;
      }
    }
    default:
      break;
  }
}

auto RemoteAppServer::GetClient(int request_id, struct sockaddr* addr,
                                size_t addr_len, const char* name,
                                bool using_v2) -> int {
  // If we're not accepting connections at all, reject 'em.
  if (!g_base->networking->remote_server_accepting_connections()) {
    return -1;
  }

  // First see if we have an id for this name. (we no longer care about
  // request-id).
  for (int i = 0; i < kMaxRemoteAppClients; i++) {
    // We now have clients include unique IDs in their name so we simply compare
    // to name.
    // This allows re-establishing connections and whatnot.
    if (strcmp(name, "") != 0 && !strcmp(name, clients_[i].name)) {
      // If the request id has changed it means that they rebooted their remote
      // or something; lets take note of that.
      if (clients_[i].request_id != request_id) {
        clients_[i].request_id = request_id;

        // Print 'Billy Bob's iPhone Reconnected'.
        char m[256];
        snprintf(m, sizeof(m), "%s", clients_[i].display_name);

        // Replace ${CONTROLLER} with it in our message.
        std::string s =
            g_base->assets->GetResourceString("controllerReconnectedText");
        Utils::StringReplaceOne(&s, "${CONTROLLER}", m);
        g_base->logic->event_loop()->PushCall([s] {
          g_base->graphics->screenmessages->AddScreenMessage(s,
                                                             Vector3f(1, 1, 1));
        });
        g_base->logic->event_loop()->PushCall([] {
          if (g_base->assets->asset_loads_allowed()) {
            g_base->audio->SafePlaySysSound(SysSoundID::kGunCock);
          }
        });
      }
      clients_[i].in_use = true;
      return i;
    }
  }

  // Don't reuse a slot for 5 seconds (if its been heard from since this time).
  millisecs_t cooldown_time = g_core->AppTimeMillisecs() - 5000;

  // Ok, not there already.. now look for a non-taken one and return that.
  for (int i = 0; i < kMaxRemoteAppClients; i++) {
    if (!clients_[i].in_use
        && (clients_[i].last_contact_time == 0
            || clients_[i].last_contact_time < cooldown_time)) {
      // Ok lets fill out the client.
      clients_[i].in_use = true;
      clients_[i].next_state_id = 0;
      clients_[i].state = 0;
      BA_PRECONDITION(addr_len <= sizeof(clients_[i].address));
      memcpy(&clients_[i].address, addr, addr_len);
      clients_[i].address_size = addr_len;
      strncpy(clients_[i].name, name, sizeof(clients_[i].name));
      clients_[i].name[sizeof(clients_[i].name) - 1] =
          0;  // in case we overflowed

      // Display-name is simply name with everything after '#' removed (which is
      // only used as a unique ID).
      strcpy(clients_[i].display_name, clients_[i].name);  // NOLINT
      char* c = strchr(clients_[i].display_name, '#');
      if (c) *c = 0;
      clients_[i].last_contact_time = g_core->AppTimeMillisecs();
      clients_[i].request_id = request_id;
      char m[256];

      // Print 'Billy Bob's iPhone Connected'
      snprintf(m, sizeof(m), "%s", clients_[i].display_name);

      // Replace ${CONTROLLER} with it in our message.
      std::string s =
          g_base->assets->GetResourceString("controllerConnectedText");
      Utils::StringReplaceOne(&s, "${CONTROLLER}", m);
      g_base->logic->event_loop()->PushCall([s] {
        g_base->graphics->screenmessages->AddScreenMessage(s,
                                                           Vector3f(1, 1, 1));
      });

      g_base->logic->event_loop()->PushCall([] {
        if (g_base->assets->asset_loads_allowed()) {
          g_base->audio->SafePlaySysSound(SysSoundID::kGunCock);
        }
      });

      std::string utf8 = Utils::GetValidUTF8(clients_[i].display_name, "rsgc1");
      clients_[i].joystick_ = Object::NewDeferred<JoystickInput>(
          -1,  // not an sdl joystick
          "RemoteApp: "
              + utf8,  // device name (we now incorporate the name they send us)
          false,       // don't allow configuring
          using_v2);   // calibrate in v2; not v1
      clients_[i].joystick_->set_is_remote_app(true);

      // If they name they supplied was <= 10 characters, use it as our default
      // player name.
      if (Utils::UTF8StringLength(utf8.c_str()) <= 10) {
        clients_[i].joystick_->set_custom_default_player_name(utf8);
      }
      assert(g_base->logic);
      g_base->input->PushAddInputDeviceCall(clients_[i].joystick_, false);
      return i;
    }
  }
  // Sorry no room.
  return -1;
}

void RemoteAppServer::HandleRemoteEvent(RemoteAppClient* client,
                                        RemoteEventType b) {
  bool send{true};

  // Ok we got some data from the remote.
  // All we have to do is translate it into an SDL event and feed it to our
  // manual joystick we made.
  SDL_Event e{};
  switch (b) {
    case RemoteEventType::kBombPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 2;
      break;
    case RemoteEventType::kBombRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 2;
      break;

      // Could actually call the menu func directly,
      // but it should be fine to just emulate it via the button-press.
    case RemoteEventType::kMenu:
    case RemoteEventType::kMenuPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 5;
      break;
    case RemoteEventType::kMenuRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 5;
      break;
    case RemoteEventType::kJumpPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 0;
      break;
    case RemoteEventType::kJumpRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 0;
      break;
    case RemoteEventType::kThrowPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 3;
      break;
    case RemoteEventType::kThrowRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 3;
      break;
    case RemoteEventType::kPunchPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 1;
      break;
    case RemoteEventType::kPunchRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 1;
      break;
    case RemoteEventType::kHoldPositionPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 25;
      break;
    case RemoteEventType::kHoldPositionRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 25;
      break;
    case RemoteEventType::kRunPress:
      e.type = SDL_JOYBUTTONDOWN;
      e.jbutton.button = 64;
      break;
    case RemoteEventType::kRunRelease:
      e.type = SDL_JOYBUTTONUP;
      e.jbutton.button = 64;
      break;

#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
    default:
      send = false;
      break;
  }
  if (send) {
    assert(g_base->logic);
    g_base->input->PushJoystickEvent(e, client->joystick_);
  }
#pragma clang diagnostic pop
}

void RemoteAppServer::HandleRemoteFloatEvent(RemoteAppClient* client,
                                             RemoteEventType b, float val) {
  SDL_Event e{};
  bool send = true;
  switch (b) {
    case RemoteEventType::kDPadH:
      e.type = SDL_JOYAXISMOTION;
      e.jaxis.axis = 0;
      e.jaxis.value = static_cast<int16_t>(32767 * val);
      break;
    case RemoteEventType::kDPadV:
      e.type = SDL_JOYAXISMOTION;
      e.jaxis.axis = 1;
      e.jaxis.value = static_cast<int16_t>(32767 * val);
      break;

#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
    default:
      send = false;
      break;
  }
  if (send) {
    assert(g_base->logic);
    g_base->input->PushJoystickEvent(e, client->joystick_);
  }
#pragma clang diagnostic pop
}

}  // namespace ballistica::base
