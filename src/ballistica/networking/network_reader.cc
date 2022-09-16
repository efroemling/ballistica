// Released under the MIT License. See LICENSE for details.

#include "ballistica/networking/network_reader.h"

#include "ballistica/generic/json.h"
#include "ballistica/input/remote_app.h"
#include "ballistica/logic/connection/connection_set.h"
#include "ballistica/logic/logic.h"
#include "ballistica/logic/player_spec.h"
#include "ballistica/math/vector3f.h"
#include "ballistica/networking/network_writer.h"
#include "ballistica/networking/sockaddr.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

NetworkReader::NetworkReader() {
  // We're a singleton; make sure we don't exist.
  assert(g_network_reader == nullptr);
}

auto NetworkReader::SetPort(int port) -> void {
  assert(InMainThread());
  // Currently can't switch once this is set.
  if (port4_ != -1) {
    return;
  }
  port4_ = port6_ = port;
  thread_ = new std::thread(RunThreadStatic, this);
}

auto NetworkReader::Pause() -> void {
  assert(InMainThread());
  assert(!paused_);
  {
    std::unique_lock<std::mutex> lock(paused_mutex_);
    paused_ = true;
  }

  // Ok now attempt to send a quick ping to ourself to wake us up so we can kill
  // our socket.
  if (port4_ != -1) {
    PokeSelf();
  } else {
    Log(LogLevel::kError, "NetworkReader port is -1 on pause");
  }
}

void NetworkReader::Resume() {
  assert(InMainThread());
  assert(paused_);

  {
    std::unique_lock<std::mutex> lock(paused_mutex_);
    paused_ = false;
  }

  // Poke our thread so it can go on its way.
  paused_cv_.notify_all();
}

void NetworkReader::PokeSelf() {
  int sd = socket(AF_INET, SOCK_DGRAM, 0);
  if (sd < 0) {
    Log(LogLevel::kError, "Unable to create sleep ping socket; errno "
                              + g_platform->GetSocketErrorString());
  } else {
    struct sockaddr_in serv_addr {};
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);  // NOLINT
    serv_addr.sin_port = 0;                         // any
    int bresult = ::bind(sd, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (bresult == 1) {
      Log(LogLevel::kError,
          "Unable to bind sleep socket: " + g_platform->GetSocketErrorString());
    } else {
      struct sockaddr_in t_addr {};
      memset(&t_addr, 0, sizeof(t_addr));
      t_addr.sin_family = AF_INET;
      t_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);  // NOLINT
      t_addr.sin_port = htons(port4_);                  // NOLINT
      char b[1] = {BA_PACKET_POKE};
      ssize_t sresult =
          sendto(sd, b, 1, 0, (struct sockaddr*)(&t_addr), sizeof(t_addr));
      if (sresult == -1) {
        Log(LogLevel::kError, "Error on sleep self-sendto: "
                                  + g_platform->GetSocketErrorString());
      }
    }
    g_platform->CloseSocket(sd);
  }
}

static auto HandleJSONPing(const std::string& data_str) -> std::string {
  cJSON* data = cJSON_Parse(data_str.c_str());
  if (data == nullptr) {
    return "";
  }
  cJSON_Delete(data);

  // Ok lets include some basic info that might be pertinent to someone pinging
  // us. Currently that includes our current/max connection count.
  char buffer[256];
  int party_size = 0;
  int party_size_max = 10;
  if (g_python != nullptr) {
    party_size = g_logic->public_party_size();
    party_size_max = g_logic->public_party_max_size();
  }
  snprintf(buffer, sizeof(buffer), R"({"b":%d,"ps":%d,"psmx":%d})",
           kAppBuildNumber, party_size, party_size_max);
  return buffer;
}

static auto HandleGameQuery(const char* buffer, size_t size,
                            struct sockaddr_storage* from) -> void {
  if (size == 5) {
    // If we're already in a party, don't advertise since they
    // wouldn't be able to join us anyway.
    if (g_logic->connections()->has_connection_to_host()) {
      return;
    }

    // Pull the query id from the packet.
    uint32_t query_id;
    memcpy(&query_id, buffer + 1, 4);

    // Ship them a response packet containing the query id,
    // our protocol version, our unique-app-instance-id, and our
    // player_spec.
    char msg[400];

    std::string usid = GetAppInstanceUUID();
    std::string player_spec_string;

    // If we're signed in, send our account spec.
    // Otherwise just send a dummy made with our device name.
    player_spec_string = PlayerSpec::GetAccountPlayerSpec().GetSpecString();

    // This should always be the case (len needs to be 1 byte)
    BA_PRECONDITION_FATAL(player_spec_string.size() < 256);

    BA_PRECONDITION_FATAL(!usid.empty());
    if (usid.size() > 100) {
      Log(LogLevel::kError, "had to truncate session-id; shouldn't happen");
      usid.resize(100);
    }
    if (usid.empty()) {
      usid = "error";
    }

    msg[0] = BA_PACKET_GAME_QUERY_RESPONSE;
    memcpy(msg + 1, &query_id, 4);
    uint32_t protocol_version = kProtocolVersion;
    memcpy(msg + 5, &protocol_version, 4);
    msg[9] = static_cast<char>(usid.size());
    msg[10] = static_cast<char>(player_spec_string.size());

    memcpy(msg + 11, usid.c_str(), usid.size());
    memcpy(msg + 11 + usid.size(), player_spec_string.c_str(),
           player_spec_string.size());
    size_t msg_len = 11 + player_spec_string.size() + usid.size();
    BA_PRECONDITION_FATAL(msg_len <= sizeof(msg));

    std::vector<uint8_t> msg_buffer(msg_len);
    memcpy(msg_buffer.data(), msg, msg_len);

    g_network_writer->PushSendToCall(msg_buffer, SockAddr(*from));

  } else {
    Log(LogLevel::kError, "Got invalid game-query packet of len "
                              + std::to_string(size) + "; expected 5.");
  }
}

auto NetworkReader::RunThread() -> int {
  if (!HeadlessMode()) {
    remote_server_ = std::make_unique<RemoteAppServer>();
  }

  // Do this whole thing in a loop. If we get put to sleep we just start over.
  while (true) {
    // Sleep until we're unpaused.
    if (paused_) {
      std::unique_lock<std::mutex> lock(paused_mutex_);
      paused_cv_.wait(lock, [this] { return (!paused_); });
    }

    OpenSockets();

    // Now just listen and forward messages along.
    char buffer[10000];
    while (true) {
      struct sockaddr_storage from {};
      socklen_t from_size = sizeof(from);
      fd_set readset;
      FD_ZERO(&readset);
      if (sd4_ != -1) {
        if (!g_buildconfig.ostype_windows()) {
          // Try to get a clean error instead of a crash if we exceed our
          // open file descriptor limit (except on windows where FD_SETSIZE
          // is apparently a dummy value).
          if (sd4_ < 0 || sd4_ >= FD_SETSIZE) {
            FatalError("Socket/File Descriptor Overflow (sd4="
                       + std::to_string(sd4_) + ", FD_SETSIZE="
                       + std::to_string(FD_SETSIZE) + "). Please report this.");
          }
        }

        FD_SET(sd4_, &readset);  // NOLINT
      }
      if (sd6_ != -1) {
        if (!g_buildconfig.ostype_windows()) {
          // Try to get a clean error instead of a crash if we exceed our
          // open file descriptor limit (except on windows where FD_SETSIZE
          // is apparently a dummy value).
          if (sd6_ < 0 || sd6_ >= FD_SETSIZE) {
            FatalError("Socket/File Descriptor Overflow (sd6="
                       + std::to_string(sd6_) + ", FD_SETSIZE="
                       + std::to_string(FD_SETSIZE) + "). Please report this.");
          }
        }
        FD_SET(sd6_, &readset);  // NOLINT
      }
      int maxfd = std::max(sd4_, sd6_);
      int sresult = select(maxfd + 1, &readset, nullptr, nullptr, nullptr);
      if (sresult == -1) {
        // No big deal if we get interrupted occasionally.
        if (g_platform->GetSocketError() == EINTR) {
          // Aint no thang.
        } else {
          // Let's complain for anything else though.
          Log(LogLevel::kError,
              "Error on select: " + g_platform->GetSocketErrorString());
        }
      } else {
        // Wait for any data on either of our sockets.
        for (int sd : {sd4_, sd6_}) {
          if (sd == -1 || !(FD_ISSET(sd, &readset))) {
            continue;
          }
          ssize_t rresult =
              recvfrom(sd, buffer, sizeof(buffer), 0,
                       reinterpret_cast<sockaddr*>(&from), &from_size);
          if (rresult == 0) {
            Log(LogLevel::kError,
                "NetworkReader Recv got length 0; this shouldn't "
                "happen");
          } else if (rresult == -1) {
            // This needs to be locked during any sd changes/writes.
            std::scoped_lock lock(sd_mutex_);

            // If either of our sockets goes down lets close *both* of
            // them.
            if (sd4_ != -1) {
              g_platform->CloseSocket(sd4_);
              sd4_ = -1;
            }
            if (sd6_ != -1) {
              g_platform->CloseSocket(sd6_);
              sd6_ = -1;
            }
          } else {
            assert(from_size >= 0);
            auto rresult2{static_cast<size_t>(rresult)};
            // If we get *any* data while paused, kill both our
            // sockets (we ping ourself for this purpose).
            if (paused_) {
              // This needs to be locked during any sd changes/writes.
              std::scoped_lock lock(sd_mutex_);
              if (sd4_ != -1) {
                g_platform->CloseSocket(sd4_);
                sd4_ = -1;
              }
              if (sd6_ != -1) {
                g_platform->CloseSocket(sd6_);
                sd6_ = -1;
              }
              break;
            }
            switch (buffer[0]) {
              case BA_PACKET_POKE:
                break;
              case BA_PACKET_SIMPLE_PING: {
                // This needs to be locked during any sd changes/writes.
                std::scoped_lock lock(sd_mutex_);
                char msg[1] = {BA_PACKET_SIMPLE_PONG};
                sendto(sd, msg, 1, 0, reinterpret_cast<sockaddr*>(&from),
                       from_size);
                break;
              }
              case BA_PACKET_JSON_PING: {
                if (rresult2 > 1) {
                  std::vector<char> s_buffer(rresult2);
                  memcpy(s_buffer.data(), buffer + 1, rresult2 - 1);
                  s_buffer[rresult2 - 1] = 0;  // terminate string
                  std::string response = HandleJSONPing(s_buffer.data());
                  if (!response.empty()) {
                    std::vector<char> msg(1 + response.size());
                    msg[0] = BA_PACKET_JSON_PONG;
                    memcpy(msg.data() + 1, response.c_str(), response.size());
                    std::scoped_lock lock(sd_mutex_);
                    sendto(
                        sd, msg.data(),
                        static_cast_check_fit<socket_send_length_t>(msg.size()),
                        0, reinterpret_cast<sockaddr*>(&from), from_size);
                  }
                }
                break;
              }
              case BA_PACKET_JSON_PONG: {
                if (rresult2 > 1) {
                  std::vector<char> s_buffer(rresult2);
                  memcpy(s_buffer.data(), buffer + 1, rresult2 - 1);
                  s_buffer[rresult2 - 1] = 0;  // terminate string
                  cJSON* data = cJSON_Parse(s_buffer.data());
                  if (data != nullptr) {
                    cJSON_Delete(data);
                  }
                }
                break;
              }
              case BA_PACKET_REMOTE_PING:
              case BA_PACKET_REMOTE_PONG:
              case BA_PACKET_REMOTE_ID_REQUEST:
              case BA_PACKET_REMOTE_ID_RESPONSE:
              case BA_PACKET_REMOTE_DISCONNECT:
              case BA_PACKET_REMOTE_STATE:
              case BA_PACKET_REMOTE_STATE2:
              case BA_PACKET_REMOTE_STATE_ACK:
              case BA_PACKET_REMOTE_DISCONNECT_ACK:
              case BA_PACKET_REMOTE_GAME_QUERY:
              case BA_PACKET_REMOTE_GAME_RESPONSE:
                // These packets are associated with the remote app; let the
                // remote server handle them.
                if (remote_server_) {
                  remote_server_->HandleData(
                      sd, reinterpret_cast<uint8_t*>(buffer), rresult2,
                      reinterpret_cast<sockaddr*>(&from),
                      static_cast<size_t>(from_size));
                }
                break;

              case BA_PACKET_CLIENT_REQUEST:
              case BA_PACKET_CLIENT_ACCEPT:
              case BA_PACKET_CLIENT_DENY:
              case BA_PACKET_CLIENT_DENY_ALREADY_IN_PARTY:
              case BA_PACKET_CLIENT_DENY_VERSION_MISMATCH:
              case BA_PACKET_CLIENT_DENY_PARTY_FULL:
              case BA_PACKET_DISCONNECT_FROM_CLIENT_REQUEST:
              case BA_PACKET_DISCONNECT_FROM_CLIENT_ACK:
              case BA_PACKET_DISCONNECT_FROM_HOST_REQUEST:
              case BA_PACKET_DISCONNECT_FROM_HOST_ACK:
              case BA_PACKET_CLIENT_GAMEPACKET_COMPRESSED:
              case BA_PACKET_HOST_GAMEPACKET_COMPRESSED: {
                // These messages are associated with udp host/client
                // connections.. pass them to the logic thread to wrangle.
                std::vector<uint8_t> msg_buffer(rresult2);
                memcpy(&(msg_buffer[0]), buffer, rresult2);
                g_logic->connections()->PushUDPConnectionPacketCall(
                    msg_buffer, SockAddr(from));
                break;
              }

              case BA_PACKET_GAME_QUERY: {
                HandleGameQuery(buffer, rresult2, &from);
                break;
              }

              default:
                break;
            }
          }
        }
      }

      // If *both* of our sockets are dead, break out.
      if (sd4_ == -1 && sd6_ == -1) {
        break;
      }
    }

    // Sleep for a moment to keep us from running wild if we're unable to block.
    Platform::SleepMS(1000);
  }
}

auto NetworkReader::OpenSockets() -> void {
  // This needs to be locked during any socket-descriptor changes/writes.
  std::scoped_lock lock(sd_mutex_);

  int result;
  int print_port_unavailable = false;
  int initial_requested_port = port4_;

  sd4_ = socket(AF_INET, SOCK_DGRAM, 0);
  if (sd4_ < 0) {
    Log(LogLevel::kError, "Unable to open host socket; errno "
                              + g_platform->GetSocketErrorString());
  } else {
    g_platform->SetSocketNonBlocking(sd4_);

    // Bind to local server port.
    struct sockaddr_in serv_addr {};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);  // NOLINT

    // Try our requested port for v4, then go with any available if that
    // doesn't work.
    serv_addr.sin_port = htons(port4_);  // NOLINT
    result = ::bind(sd4_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (result != 0) {
      // If we're headless then we abort here; we're useless if we don't get
      // the port we wanted.
      if (HeadlessMode()) {
        FatalError("Unable to bind to requested udp port "
                   + std::to_string(port4_) + " (ipv4)");
      }

      // Primary ipv4 bind failed; try on any port as a backup.
      print_port_unavailable = true;
      serv_addr.sin_port = htons(0);  // NOLINT
      result = ::bind(sd4_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));

      // Wuh oh; no ipv6 for us i guess.
      if (result != 0) {
        g_platform->CloseSocket(sd4_);
        sd4_ = -1;
      }
    }
  }

  // See what v4 port we actually wound up with.
  if (sd4_ != -1) {
    struct sockaddr_in sa {};
    socklen_t sa_len = sizeof(sa);
    if (getsockname(sd4_, reinterpret_cast<sockaddr*>(&sa), &sa_len) == 0) {
      port4_ = ntohs(sa.sin_port);  // NOLINT

      // Aim for a v6 port to match whatever we wound up with on the v4
      // side.
      port6_ = port4_;
    }
  }

  // Ok now lets try to create an ipv6 socket on the same port.
  // (its actually possible to just create a v6 socket and let the OSs
  // dual-stack support provide v4 connectivity too, but that's not
  // available everywhere (win XP, etc) so let's do this for now.
  sd6_ = socket(AF_INET6, SOCK_DGRAM, 0);
  if (sd6_ < 0) {
    Log(LogLevel::kError,
        "Unable to open ipv6 socket: " + g_platform->GetSocketErrorString());
  } else {
    // Since we're explicitly creating both a v4 and v6 socket, tell the v6
    // to *not* do both itself (not sure if this is necessary; on mac it
    // still seems to come up.. but apparently that's not always the case).
    int on = 1;
    if (setsockopt(sd6_, IPPROTO_IPV6, IPV6_V6ONLY,
                   reinterpret_cast<char*>(&on), sizeof(on))
        == -1) {
      Log(LogLevel::kError, "Error setting socket as ipv6-only");
    }

    g_platform->SetSocketNonBlocking(sd6_);
    struct sockaddr_in6 serv_addr {};
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin6_family = AF_INET6;
    serv_addr.sin6_port = htons(port6_);  // NOLINT
    serv_addr.sin6_addr = in6addr_any;
    result = ::bind(sd6_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));

    if (result != 0) {
      if (HeadlessMode()) {
        FatalError("Unable to bind to requested udp port "
                   + std::to_string(port6_) + " (ipv6)");
      }
      // Primary ipv6 bind failed; try backup.

      // We don't care if our random backup ports don't match; only if our
      // target port failed.
      if (port6_ == initial_requested_port) {
        print_port_unavailable = true;
      }
      serv_addr.sin6_port = htons(0);  // NOLINT
      result = ::bind(sd6_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
      if (result != 0) {
        // Wuh oh; no ipv6 for us i guess.
        g_platform->CloseSocket(sd6_);
        sd6_ = -1;
      }
    }
  }

  // See what v6 port we actually wound up with.
  if (sd6_ != -1) {
    struct sockaddr_in sa {};
    socklen_t sa_len = sizeof(sa);
    if (getsockname(sd6_, reinterpret_cast<sockaddr*>(&sa), &sa_len) == 0) {
      port6_ = ntohs(sa.sin_port);  // NOLINT
    }
  }
  if (print_port_unavailable) {
    // FIXME - use translations here
    ScreenMessage("Unable to bind udp port "
                      + std::to_string(initial_requested_port)
                      + "; some network functionality may fail.",
                  {1, 0.5f, 0});
    Log(LogLevel::kWarning, "Unable to bind udp port "
                                + std::to_string(initial_requested_port)
                                + "; some network functionality may fail.");
  }
}

}  // namespace ballistica
