// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/networking/network_reader.h"

#include <algorithm>
#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/input/support/remote_app_server.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/networking/sockaddr.h"

namespace ballistica::base {

NetworkReader::NetworkReader() = default;

void NetworkReader::SetPort(int port) {
  assert(g_core->InMainThread());
  // Currently can't switch once this is set.
  if (port4_ != -1) {
    return;
  }
  port4_ = port6_ = port;
  thread_ = new std::thread(RunThreadStatic_, this);
}

void NetworkReader::OnAppSuspend() {
  assert(g_core->InMainThread());
  assert(!paused_);
  {
    std::scoped_lock<std::mutex> lock(paused_mutex_);
    paused_ = true;
  }

  // It's possible that we get suspended before port is set, so this could
  // still be -1.
  if (port4_ != -1) {
    PokeSelf_();
  }
}

void NetworkReader::OnAppUnsuspend() {
  assert(g_core->InMainThread());
  assert(paused_);

  {
    std::scoped_lock<std::mutex> lock(paused_mutex_);
    paused_ = false;
  }

  // Poke our thread so it can go on its way.
  paused_cv_.notify_all();
}

void NetworkReader::PokeSelf_() {
  int sd = socket(AF_INET, SOCK_DGRAM, 0);
  if (sd < 0) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "Error creating poke socket: "
                             + g_core->platform->GetSocketErrorString());
  } else {
    struct sockaddr_in serv_addr{};
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    serv_addr.sin_port = 0;  // any
    int bresult = ::bind(sd, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (bresult != 0) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Error binding poke socket: "
                               + g_core->platform->GetSocketErrorString());
    } else {
      struct sockaddr_in t_addr{};
      memset(&t_addr, 0, sizeof(t_addr));
      t_addr.sin_family = AF_INET;
      t_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
      t_addr.sin_port = htons(port4_);
      char b[1] = {BA_PACKET_POKE};
      ssize_t sresult =
          sendto(sd, b, 1, 0, (struct sockaddr*)(&t_addr), sizeof(t_addr));
      if (sresult == -1) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Error on poke socket send: "
                                 + g_core->platform->GetSocketErrorString());
      }
    }
    g_core->platform->CloseSocket(sd);
  }
}

void NetworkReader::DoPoll_(bool* can_read_4, bool* can_read_6) {
  struct pollfd fds[2]{};
  int i{};
  int index_4{-1};
  int index_6{-1};

  if (sd4_ != -1) {
    fds[i].fd = sd4_;
    fds[i].events = POLLIN;
    index_4 = i++;
  }
  if (sd6_ != -1) {
    fds[i].fd = sd6_;
    fds[i].events = POLLIN;
    index_6 = i++;
  }
  if (i > 0) {
    int result = BA_SOCKET_POLL(fds, i, -1);
    if (result == BA_SOCKET_ERROR_RETURN) {
      // No big deal if we get interrupted occasionally.
      if (g_core->platform->GetSocketError() == EINTR) {
        // Aint no thang.
      } else {
        // Let's complain for anything else though.
        g_core->logging->Log(
            LogName::kBaNetworking, LogLevel::kError,
            "Error on select: " + g_core->platform->GetSocketErrorString());
      }
    } else {
      *can_read_4 = index_4 != -1 && fds[index_4].revents & POLLIN;
      *can_read_6 = index_6 != -1 && fds[index_6].revents & POLLIN;
    }
  } else {
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                "DoPoll called with neither sd4 or sd6 set.");
  }
}

void NetworkReader::DoSelect_(bool* can_read_4, bool* can_read_6) {
  fd_set readset;
  FD_ZERO(&readset);

  if (sd4_ != -1) {
    if (!g_buildconfig.platform_windows()) {
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
    if (!g_buildconfig.platform_windows()) {
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
  if (sresult == BA_SOCKET_ERROR_RETURN) {
    // No big deal if we get interrupted occasionally.
    if (g_core->platform->GetSocketError() == EINTR) {
      // Aint no thang.
    } else {
      // Let's complain for anything else though.
      g_core->logging->Log(
          LogName::kBaNetworking, LogLevel::kError,
          "Error on select: " + g_core->platform->GetSocketErrorString());
    }
  } else {
    *can_read_4 = sd4_ != -1 && FD_ISSET(sd4_, &readset);
    *can_read_6 = sd6_ != -1 && FD_ISSET(sd6_, &readset);
  }
}

auto NetworkReader::RunThread_() -> int {
  g_core->platform->SetCurrentThreadName("ballistica network-read");

  if (!g_core->HeadlessMode()) {
    remote_server_ = std::make_unique<RemoteAppServer>();
  }

  // Do this whole thing in a loop. If we get put to sleep we just start
  // over.
  while (true) {
    // Sleep until we're unpaused.
    if (paused_) {
      std::unique_lock<std::mutex> lock(paused_mutex_);
      paused_cv_.wait(lock, [this] { return (!paused_); });
    }

    OpenSockets_();

    // Now just listen and forward messages along.
    char buffer[10000];
    while (true) {
      sockaddr_storage from{};
      socklen_t from_size = sizeof(from);

      bool can_read_4{};
      bool can_read_6{};

      // A bit of history here: Had been using select() to wait for input
      // here, but recently I've started seeing newer versions of android
      // crashing due to file descriptor counts going over the standard set
      // limit size of ~1000 or whatnot. So switching to poll() instead
      // which should not have such limitations.
      if (explicit_bool(true)) {
        DoPoll_(&can_read_4, &can_read_6);
      } else {
        DoSelect_(&can_read_4, &can_read_6);
      }

      for (int s_index : {0, 1}) {
        int sd;
        bool can_read;
        if (s_index == 0) {
          sd = sd4_;
          can_read = can_read_4;
        } else if (s_index == 1) {
          sd = sd6_;
          can_read = can_read_6;
        } else {
          FatalError("Should not get here; s_index=" + std::to_string(s_index)
                     + ".");
          sd = -1;
          can_read = false;
        }
        if (!can_read) {
          continue;
        }
        ssize_t rresult =
            recvfrom(sd, buffer, sizeof(buffer), 0,
                     reinterpret_cast<sockaddr*>(&from), &from_size);
        if (rresult == 0) {
          // Note: have gotten reports of server attacks with this log
          // message repeating. So now only logging this once to eliminate
          // repeated log overhead and hopefully make the attack less
          // effective.
          BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                      "NetworkReader Recv got length 0; this shouldn't "
                      "happen");
        } else if (rresult == -1) {
          // This needs to be locked during any sd changes/writes.
          std::scoped_lock lock(sd_mutex_);

          // If either of our sockets goes down lets close *both* of them.
          if (sd4_ != -1) {
            g_core->platform->CloseSocket(sd4_);
            sd4_ = -1;
          }
          if (sd6_ != -1) {
            g_core->platform->CloseSocket(sd6_);
            sd6_ = -1;
          }
        } else {
          assert(from_size >= 0);
          auto rresult2{static_cast<size_t>(rresult)};
          // If we get *any* data while paused, kill both our sockets (we
          // ping ourself for this purpose).
          if (paused_) {
            // This needs to be locked during any sd changes/writes.
            std::scoped_lock lock(sd_mutex_);
            if (sd4_ != -1) {
              g_core->platform->CloseSocket(sd4_);
              sd4_ = -1;
            }
            if (sd6_ != -1) {
              g_core->platform->CloseSocket(sd6_);
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
                std::string response =
                    g_base->app_mode()->HandleJSONPing(s_buffer.data());
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
              // remote-server handle them.
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
              // connections; pass them to the logic thread to wrangle.
              std::vector<uint8_t> msg_buffer(rresult2);
              memcpy(msg_buffer.data(), buffer, rresult2);
              PushIncomingUDPPacketCall_(msg_buffer, SockAddr(from));
              break;
            }

            case BA_PACKET_HOST_QUERY: {
              g_base->app_mode()->HandleGameQuery(buffer, rresult2, &from);
              break;
            }

            default:
              break;
          }
        }
      }

      // If *both* of our sockets are dead, break out.
      if (sd4_ == -1 && sd6_ == -1) {
        break;
      }
    }

    // Sleep for a moment to keep us from running wild if we're unable to block.
    core::CorePlatform::SleepMillisecs(1000);
  }
}

void NetworkReader::PushIncomingUDPPacketCall_(const std::vector<uint8_t>& data,
                                               const SockAddr& addr) {
  // Avoid buffer-full errors if something is causing us to write too often;
  // these are unreliable messages so its ok to just drop them.
  if (!g_base->logic->event_loop()->CheckPushSafety()) {
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                "Ignoring excessive incoming udp packets.");
    return;
  }

  g_base->logic->event_loop()->PushCall([data, addr] {
    g_base->app_mode()->HandleIncomingUDPPacket(data, addr);
  });
}

void NetworkReader::OpenSockets_() {
  // This needs to be locked during any socket-descriptor changes/writes.
  std::scoped_lock lock(sd_mutex_);

  int result;
  int print_port_unavailable = false;
  int initial_requested_port = port4_;

  // If we're headless then we die if our requested port(s) are unavailable;
  // we're useless otherwise. But we now allow overriding this behavior via
  // env var for cases where we use headless builds for data crunching.
  auto suppress_env_var =
      g_core->platform->GetEnv("BA_SUPPRESS_HEADLESS_PORT_IN_USE_ERROR");
  auto suppress_headless_port_in_use_error =
      (suppress_env_var && *suppress_env_var == "1");

  sd4_ = socket(AF_INET, SOCK_DGRAM, 0);
  if (sd4_ < 0) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "Unable to open host socket; errno "
                             + g_core->platform->GetSocketErrorString());
  } else {
    g_core->platform->SetSocketNonBlocking(sd4_);

    // Bind to local server port.
    struct sockaddr_in serv_addr{};
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    // Try our requested port for v4, then go with any available if that
    // doesn't work.
    serv_addr.sin_port = htons(port4_);  // NOLINT
    result = ::bind(sd4_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (result != 0) {
      if (g_core->HeadlessMode() && !suppress_headless_port_in_use_error) {
        FatalError("Unable to bind to requested udp port "
                   + std::to_string(port4_) + " (ipv4)");
      }

      // Primary ipv4 bind failed; try on any port as a backup.
      print_port_unavailable = true;
      serv_addr.sin_port = htons(0);  // NOLINT
      result = ::bind(sd4_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));

      // Wuh oh; no ipv6 for us i guess.
      if (result != 0) {
        g_core->platform->CloseSocket(sd4_);
        sd4_ = -1;
      }
    }
  }

  // See what v4 port we actually wound up with.
  if (sd4_ != -1) {
    struct sockaddr_in sa{};
    socklen_t sa_len = sizeof(sa);
    if (getsockname(sd4_, reinterpret_cast<sockaddr*>(&sa), &sa_len) == 0) {
      port4_ = ntohs(sa.sin_port);  // NOLINT

      // Aim for a v6 port to match whatever we wound up with on the v4
      // side.
      port6_ = port4_;
    }
  }

  // Ok now lets try to create an ipv6 socket on the same port. Its actually
  // possible to just create a v6 socket and let the OS's dual-stack support
  // provide v4 connectivity too, but not sure that's available everywhere;
  // should look into it.
  sd6_ = socket(AF_INET6, SOCK_DGRAM, 0);
  if (sd6_ < 0) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "Unable to open ipv6 socket: "
                             + g_core->platform->GetSocketErrorString());
  } else {
    // Since we're explicitly creating both a v4 and v6 socket, tell the v6
    // to *not* do both itself (not sure if this is necessary; on mac it
    // still seems to come up.. but apparently that's not always the case).
    int on = 1;
    if (setsockopt(sd6_, IPPROTO_IPV6, IPV6_V6ONLY,
                   reinterpret_cast<char*>(&on), sizeof(on))
        == -1) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                           "Error setting socket as ipv6-only");
    }

    g_core->platform->SetSocketNonBlocking(sd6_);
    struct sockaddr_in6 serv_addr{};
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin6_family = AF_INET6;
    serv_addr.sin6_port = htons(port6_);  // NOLINT
    serv_addr.sin6_addr = in6addr_any;
    result = ::bind(sd6_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));

    if (result != 0) {
      if (g_core->HeadlessMode() && !suppress_headless_port_in_use_error) {
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
        g_core->platform->CloseSocket(sd6_);
        sd6_ = -1;
      }
    }
  }

  // See what v6 port we actually wound up with.
  if (sd6_ != -1) {
    struct sockaddr_in sa{};
    socklen_t sa_len = sizeof(sa);
    if (getsockname(sd6_, reinterpret_cast<sockaddr*>(&sa), &sa_len) == 0) {
      port6_ = ntohs(sa.sin_port);  // NOLINT
    }
  }
  if (print_port_unavailable) {
    // FIXME - use translations here
    g_base->ScreenMessage("Unable to bind udp port "
                              + std::to_string(initial_requested_port)
                              + "; some network functionality may fail.",
                          {1, 0.5f, 0});
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kWarning,
                         "Unable to bind udp port "
                             + std::to_string(initial_requested_port)
                             + "; some network functionality may fail.");
  }
}

}  // namespace ballistica::base
