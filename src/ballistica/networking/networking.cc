// Released under the MIT License. See LICENSE for details.

#include "ballistica/networking/networking.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/game/player_spec.h"
#include "ballistica/networking/network_reader.h"
#include "ballistica/networking/sockaddr.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

struct Networking::ScanResultsEntryPriv {
  PlayerSpec player_spec;
  std::string address;
  uint32_t last_query_id{};
  millisecs_t last_contact_time{};
};

Networking::Networking() {
  assert(InLogicThread());
  Resume();
}

Networking::~Networking() = default;

// Note: for now we're making our host-scan network calls directly from the game
// thread. This is generally not a good idea since it appears that even in
// non-blocking mode they're still blocking for 3-4ms sometimes. But for now
// since this is only used minimally and only while in the UI i guess it's ok.
void Networking::HostScanCycle() {
  assert(InLogicThread());

  // We need to create a scanner socket - an ipv4 socket we can send out
  // broadcast messages from.
  if (scan_socket_ == -1) {
    scan_socket_ = socket(AF_INET, SOCK_DGRAM, 0);

    if (scan_socket_ == -1) {
      Log("Error opening scan socket: " + g_platform->GetSocketErrorString()
          + ".");
      return;
    }

    // Since this guy lives in the game-thread we need it to not block.
    if (!g_platform->SetSocketNonBlocking(scan_socket_)) {
      Log("Error setting socket non-blocking.");
      g_platform->CloseSocket(scan_socket_);
      scan_socket_ = -1;
      return;
    }

    // Bind to whatever.
    struct sockaddr_in serv_addr {};
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);  // NOLINT
    serv_addr.sin_port = 0;                         // any
    int result =
        ::bind(scan_socket_, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
    if (result == 1) {
      Log("Error binding socket: " + g_platform->GetSocketErrorString() + ".");
      g_platform->CloseSocket(scan_socket_);
      scan_socket_ = -1;
      return;
    }

    // Enable broadcast on the socket.
    BA_SOCKET_SETSOCKOPT_VAL_TYPE op_val{1};
    result = setsockopt(scan_socket_, SOL_SOCKET, SO_BROADCAST, &op_val,
                        sizeof(op_val));

    if (result != 0) {
      Log("Error enabling broadcast for scan-socket: "
          + g_platform->GetSocketErrorString() + ".");
      g_platform->CloseSocket(scan_socket_);
      scan_socket_ = -1;
      return;
    }
  }

  // Ok we've got a valid scanner socket. Now lets send out broadcast pings on
  // all available networks.
  std::vector<uint32_t> addrs = g_platform->GetBroadcastAddrs();
  for (auto&& i : addrs) {
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(kDefaultPort);  // NOLINT
    addr.sin_addr.s_addr = htonl(i);      // NOLINT

    // Include our query id (so we can sort out which responses come back
    // quickest).
    uint8_t data[5];
    data[0] = BA_PACKET_GAME_QUERY;
    memcpy(data + 1, &next_scan_query_id_, 4);
    BA_DEBUG_TIME_CHECK_BEGIN(sendto);
    ssize_t result = sendto(
        scan_socket_, reinterpret_cast<socket_send_data_t*>(data), sizeof(data),
        0, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    BA_DEBUG_TIME_CHECK_END(sendto, 10);
    if (result == -1) {
      int err = g_platform->GetSocketError();
      switch (err) {  // NOLINT(hicpp-multiway-paths-covered)
        case ENETUNREACH:
          break;
        default:
          Log("Error on scanSocket sendto: "
              + g_platform->GetSocketErrorString());
      }
    }
  }
  next_scan_query_id_++;

  // ..and see if any responses came in from previous sends.
  char buffer[256];
  struct sockaddr_storage from {};
  socklen_t from_size = sizeof(from);
  while (true) {
    BA_DEBUG_TIME_CHECK_BEGIN(recvfrom);
    ssize_t result = recvfrom(scan_socket_, buffer, sizeof(buffer), 0,
                              reinterpret_cast<sockaddr*>(&from), &from_size);
    BA_DEBUG_TIME_CHECK_END(recvfrom, 10);

    if (result == -1) {
      int err = g_platform->GetSocketError();
      switch (err) {  // NOLINT(hicpp-multiway-paths-covered)
        case EWOULDBLOCK:
          break;
        default:
          Log("Error: recvfrom error: " + g_platform->GetSocketErrorString());
          break;
      }
      break;
    }

    if (result > 2 && buffer[0] == BA_PACKET_GAME_QUERY_RESPONSE) {
      // Size should be between 13 and 366 (1 byte type, 4 byte query_id, 4
      // byte protocol_id, 1 byte id_len, 1 byte player_spec_len, 1-100 byte
      // id, 1-255 byte player-spec).
      if (result >= 14 && result <= 366) {
        uint32_t protocol_version;
        uint32_t query_id;

        memcpy(&query_id, buffer + 1, 4);
        memcpy(&protocol_version, buffer + 5, 4);
        auto id_len = static_cast<uint32_t>(buffer[9]);
        auto player_spec_len = static_cast<uint32_t>(buffer[10]);

        if (id_len > 0 && id_len <= 100 && player_spec_len > 0
            && player_spec_len <= 255
            && (11 + id_len + player_spec_len == result)) {
          char id[101];
          char player_spec_str[256];
          memcpy(id, buffer + 11, id_len);
          memcpy(player_spec_str, buffer + 11 + id_len, player_spec_len);

          id[id_len] = 0;
          player_spec_str[player_spec_len] = 0;

          // Add or modify an entry for this.
          {
            std::scoped_lock lock(scan_results_mutex_);

            // Ignore if it looks like its us.
            if (id != GetAppInstanceUUID()) {
              std::string key = id;
              auto i = scan_results_.find(key);

              // Make a new entry if its not there.
              bool do_update_entry = (i == scan_results_.end()
                                      || i->second.last_query_id != query_id);
              if (do_update_entry) {
                ScanResultsEntryPriv& entry(scan_results_[key]);
                entry.player_spec = PlayerSpec(player_spec_str);
                char buffer2[256];
                entry.address = inet_ntop(
                    AF_INET,
                    &((reinterpret_cast<sockaddr_in*>(&from))->sin_addr),
                    buffer2, sizeof(buffer2));
                entry.last_query_id = query_id;
                entry.last_contact_time = GetRealTime();
              }
            }
            PruneScanResults();
          }
        } else {
          Log("Error: Got invalid BA_PACKET_GAME_QUERY_RESPONSE packet");
        }
      } else {
        Log("Error: Got invalid BA_PACKET_GAME_QUERY_RESPONSE packet");
      }
    }
  }
}

auto Networking::GetScanResults() -> std::vector<Networking::ScanResultsEntry> {
  std::vector<ScanResultsEntry> results;
  results.resize(scan_results_.size());
  {
    std::scoped_lock lock(scan_results_mutex_);
    int out_num = 0;
    for (auto&& i : scan_results_) {
      ScanResultsEntryPriv& in(i.second);
      ScanResultsEntry& out(results[out_num]);
      out.display_string = in.player_spec.GetDisplayString();
      out.address = in.address;
      out_num++;
    }
    PruneScanResults();
  }
  return results;
}

void Networking::PruneScanResults() {
  millisecs_t t = GetRealTime();
  auto i = scan_results_.begin();
  while (i != scan_results_.end()) {
    auto i_next = i;
    i_next++;
    if (t - i->second.last_contact_time > 3000) {
      scan_results_.erase(i);
    }
    i = i_next;
  }
}

void Networking::EndHostScanning() {
  if (scan_socket_ != -1) {
    g_platform->CloseSocket(scan_socket_);
    scan_socket_ = -1;
  }
}

void Networking::Pause() {
  if (!running_) Log("Networking::pause() called with running_ already false");
  running_ = false;

  // Game is going into background or whatnot. Kill any sockets/etc.
  EndHostScanning();
}

void Networking::Resume() {
  if (running_) {
    Log("Networking::resume() called with running_ already true");
  }
  running_ = true;
}

void Networking::SendTo(const std::vector<uint8_t>& buffer,
                        const SockAddr& addr) {
  assert(g_network_reader);
  assert(!buffer.empty());

  // This needs to be locked during any sd changes/writes.
  std::scoped_lock lock(g_network_reader->sd_mutex());

  // Only send if the relevant socket is currently up.. silently ignore
  // otherwise.
  int sd = addr.IsV6() ? g_network_reader->sd6() : g_network_reader->sd4();
  if (sd != -1) {
    sendto(sd, (const char*)&buffer[0],
           static_cast_check_fit<socket_send_length_t>(buffer.size()), 0,
           addr.GetSockAddr(), addr.GetSockAddrLen());
  }
}

}  // namespace ballistica
