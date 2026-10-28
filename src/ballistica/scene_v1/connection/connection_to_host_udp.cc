// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection_to_host_udp.h"

#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/builtin_strings.h"
#include "ballistica/base/networking/network_writer.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/networking/sockaddr.h"

namespace ballistica::scene_v1 {

// Note: our timers here use real (monotonic) time, not app/display time.
// Those pause while we're suspended (backgrounded) but the host's clock
// doesn't, and these timers are guesses about what the host is doing.
static auto NowMillisecs_() -> millisecs_t {
  return core::Platform::TimeMonotonicMillisecs();
}

/// When disconnecting, the longest we wait for the host to ack.
constexpr millisecs_t kDisconnectAckWaitMillisecs{2000};

/// When disconnecting from a host that has already been silent this
/// long, don't wait for an ack at all.
constexpr millisecs_t kDisconnectHostSilentGiveUpMillisecs{1000};

auto ConnectionToHostUDP::SwitchProtocol() -> bool {
  if (protocol_version() > kProtocolVersionClientMin) {
    int next = protocol_version() - 1;
    while (next > kProtocolVersionClientMin && !IsJoinableHostProtocol(next)) {
      --next;
    }
    set_protocol_version(next);

    // Need a new request id so we ignore further responses to our previous
    // requests.
    GetRequestID_();
    return true;
  }
  return false;
}

ConnectionToHostUDP::ConnectionToHostUDP(const SockAddr& addr)
    : addr_(new SockAddr(addr)),
      client_id_(-1),
      last_client_id_request_time_(0),
      last_disconnect_request_time_(0),
      did_die_(false),
      last_host_response_time_millisecs_(NowMillisecs_()) {
  GetRequestID_();
  g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [this, &addr] {
    return "ConnectionToHostUDP: created for " + addr.AddressString() + ":"
           + std::to_string(addr.Port()) + " with request_id "
           + std::to_string(request_id_) + ".";
  });
  // Note: no "Connecting..." message here; bascenev1.connect_to_party
  // shows it as soon as the join is requested, before the pre-join
  // exchange that precedes us.
}

ConnectionToHostUDP::~ConnectionToHostUDP() {
  // This prevents anything from trying to send (and thus crashing in
  // pure-virtual SendGamePacketCompressed) as we die.
  set_connection_dying(true);
}

void ConnectionToHostUDP::GetRequestID_() {
  // We store a unique-ish request ID to minimize the chance that data for
  // previous connections/etc will muck with us. Try to start this value at
  // something that won't be common in packets to minimize chance of garbage
  // packets causing trouble.
  static auto next_request_id =
      static_cast<uint8_t>(71 + (rand() % 151));  // NOLINT
  request_id_ = next_request_id++;
}

void ConnectionToHostUDP::Update() {
  ConnectionToHost::Update();
  auto* appmode = classic::ClassicAppMode::GetActiveOrWarn();
  if (!appmode) {
    return;
  }

  // Already on our way out; nothing more to do.
  if (did_die_) {
    return;
  }

  auto current_time_millisecs = NowMillisecs_();

  // If we've not gotten a client_id from the host yet, keep pestering it.
  if (!errored()) {
    if (client_id_ == -1
        && current_time_millisecs - last_client_id_request_time_ > 500) {
      last_client_id_request_time_ = current_time_millisecs;

      // Client request packet: contains our protocol version (2 bytes), our
      // request id (1 byte), and our app-instance-uuid (remainder of the
      // message).
      const std::string& uuid{g_base->LocalAppInstanceUUID()};
      std::vector<uint8_t> msg(4 + uuid.size());
      msg[0] = BA_PACKET_CLIENT_REQUEST;
      auto p_version = static_cast<uint16_t>(protocol_version());
      memcpy(&(msg[1]), &p_version, 2);
      msg[3] = request_id_;
      memcpy(&(msg[4]), uuid.c_str(), uuid.size());
      g_base->network_writer->PushSendToCall(msg, *addr_);
      g_core->logging->Log(
          LogName::kBaNetworking, LogLevel::kDebug, [this, p_version] {
            return "ConnectionToHostUDP: sent CLIENT_REQUEST to "
                   + addr_->AddressString() + ":"
                   + std::to_string(addr_->Port()) + " (protocol "
                   + std::to_string(p_version) + ", request_id "
                   + std::to_string(request_id_) + ").";
          });
    }
  }

  // If its been long enough since we've heard anything from the host, error.
  if (current_time_millisecs - last_host_response_time_millisecs_
      > (can_communicate() ? 30000u : 10000u)) {
    auto silent_secs = std::to_string(
        (current_time_millisecs - last_host_response_time_millisecs_) / 1000);
    auto host = addr_->AddressString() + ":" + std::to_string(addr_->Port());
    if (can_communicate()) {
      // An established connection went quiet: the host or the network
      // between us dropped out; nothing to say about our engine.
      g_core->logging->Log(LogName::kBaUser, LogLevel::kWarning,
                           "Lost connection to host " + host
                               + "; heard nothing for " + silent_secs + "s.");
    } else if (client_id_ == -1 && !got_host_game_packet_) {
      // Nothing ever came back: unreachable host, wrong address, bad
      // network, etc.
      g_core->logging->Log(LogName::kBaUser, LogLevel::kWarning,
                           "Unable to connect to host " + host
                               + "; no response after " + silent_secs + "s.");
    } else {
      // The host answered but the handshake never finished. That's
      // not a plain network problem, so make it reportable.
      g_core->logging->Log(
          LogName::kBaNetworking, LogLevel::kWarning,
          "Connection to host " + host
              + " never completed (accepted=" + std::to_string(client_id_ != -1)
              + ", got_game_packets=" + std::to_string(got_host_game_packet_)
              + ", protocol " + std::to_string(protocol_version())
              + ", request_id " + std::to_string(request_id_) + ", dropped "
              + std::to_string(mismatched_request_id_packets_)
              + " host packet(s) with another request_id"
              + (mismatched_request_id_packets_
                     ? " (last " + std::to_string(last_mismatched_request_id_)
                           + ")"
                     : std::string())
              + "); host silent for " + silent_secs + "s.");
    }
    // If the connection never got established, announce it failed.
    if (!can_communicate()) {
      g_base->ScreenMessage(
          base::BuiltinStrings::Net::ConnectionFailed()->Evaluate(), {1, 0, 0});
    }

    // Die immediately in this case; no use trying to wait for a
    // disconnect-ack since we've already given up hope of hearing from
    // them.
    Die();
    return;
  } else if (errored()) {
    if (disconnect_start_time_millisecs_ == 0) {
      disconnect_start_time_millisecs_ = current_time_millisecs;
    }

    // Don't hold the user hostage waiting for an ack. If the host has
    // already gone quiet, it is likely gone entirely (quit, crashed,
    // dropped off the network) and will never answer; and even a live
    // host acks within a round trip. So give up quickly either way;
    // the host times us out on its own if our requests never reached
    // it.
    if (HostSilentMillisecs() > kDisconnectHostSilentGiveUpMillisecs
        || current_time_millisecs - disconnect_start_time_millisecs_
               > kDisconnectAckWaitMillisecs) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug,
                           "ConnectionToHostUDP: no disconnect ack from "
                           "host; dropping connection.");
      Die();
      return;
    }

    // Keep sending disconnect-requests periodically. Once we get a
    // response (or give up above) we'll die.
    if (current_time_millisecs - last_disconnect_request_time_ > 1000) {
      last_disconnect_request_time_ = current_time_millisecs;

      // If we haven't even got a client id yet, we can't send disconnect
      // requests; just die.
      if (client_id_ == -1) {
        Die();
        return;
      } else {
        SendDisconnectRequest();
      }
    }
  }
}

// Tells the game to actually kill us. We try to inform the server of our
// departure before doing this when possible.
void ConnectionToHostUDP::Die() {
  if (did_die_) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "Posting multiple die messages; probably not good.");
    return;
  }
  if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
    if (appmode->connections()->connection_to_host() == this) {
      appmode->connections()->PushDisconnectedFromHostCall();
      did_die_ = true;
    } else {
      g_core->logging->Log(
          LogName::kBaNetworking, LogLevel::kError,
          "Running update for non-current host-connection; shouldn't "
          "happen.");
    }
  }
}

void ConnectionToHostUDP::SendDisconnectRequest() {
  assert(client_id_ != -1);
  if (client_id_ != -1) {
    std::vector<uint8_t> data(2);
    data[0] = BA_PACKET_DISCONNECT_FROM_CLIENT_REQUEST;
    data[1] = static_cast_check_fit<uint8_t>(client_id_);
    g_base->network_writer->PushSendToCall(data, *addr_);
  }
}

void ConnectionToHostUDP::HandleGamePacket(const std::vector<uint8_t>& buffer) {
  // Keep track of when we last heard from the host for time-out purposes.
  last_host_response_time_millisecs_ = NowMillisecs_();
  got_host_game_packet_ = true;

  ConnectionToHost::HandleGamePacket(buffer);
}

void ConnectionToHostUDP::SendGamePacketCompressed(
    const std::vector<uint8_t>& data) {
  assert(!data.empty());

  // Ok, we've got a random chunk of (possibly) compressed data to send over
  // the wire. Lets stick a header on it and ship it out.
  std::vector<uint8_t> data_full(data.size() + 2);
  memcpy(&(data_full[2]), &data[0], data.size());
  data_full[0] = BA_PACKET_CLIENT_GAMEPACKET_COMPRESSED;
  data_full[1] = static_cast_check_fit<uint8_t>(client_id_);

  // Ship this off to the net-out thread to send; at this point we don't know
  // or care what happens to it.
  assert(g_base->network_writer);
  g_base->network_writer->PushSendToCall(data_full, *addr_);
}

void ConnectionToHostUDP::Error(const std::string& msg) {
  // On our initial erroring, send a disconnect request immediately if we've
  // got an ID otherwise just kill ourselves instantly.
  if (!errored()) {
    if (client_id_ != -1) {
      SendDisconnectRequest();
    } else {
      Die();
    }
  }

  // Common error stuff.
  ConnectionToHost::Error(msg);
}

auto ConnectionToHostUDP::GetAsUDP() -> ConnectionToHostUDP* { return this; }

void ConnectionToHostUDP::NoteMismatchedRequestIdPacket(
    uint8_t packet_request_id) {
  mismatched_request_id_packets_++;
  last_mismatched_request_id_ = packet_request_id;
  if (mismatched_request_id_packets_ == 1) {
    g_core->logging->Log(
        LogName::kBaNetworking, LogLevel::kDebug, [this, packet_request_id] {
          return "ConnectionToHostUDP: dropping host packets tagged"
                 " request_id "
                 + std::to_string(packet_request_id) + " (ours is "
                 + std::to_string(request_id_) + ").";
        });
  }
}

auto ConnectionToHostUDP::HostSilentMillisecs() const -> millisecs_t {
  return NowMillisecs_() - last_host_response_time_millisecs_;
}

void ConnectionToHostUDP::RequestDisconnect() {
  // Mark us as errored so all future communication results in more
  // disconnect requests.
  set_errored(true);
  if (client_id_ != -1) {
    SendDisconnectRequest();
  }

  // If the host has already gone quiet, it is likely gone entirely
  // (quit, crashed, dropped off the network) and will never ack, so
  // leave immediately. Our request above still goes out in case it is
  // just slow. Same if we never got far enough to have a client id.
  if (!did_die_
      && (client_id_ == -1
          || HostSilentMillisecs() > kDisconnectHostSilentGiveUpMillisecs)) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug,
                         "ConnectionToHostUDP: host already silent; "
                         "disconnecting without waiting for ack.");
    Die();
  }
}

}  // namespace ballistica::scene_v1
