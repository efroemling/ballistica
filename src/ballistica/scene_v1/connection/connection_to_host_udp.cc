// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection_to_host_udp.h"

#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_writer.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/networking/sockaddr.h"

namespace ballistica::scene_v1 {

auto ConnectionToHostUDP::SwitchProtocol() -> bool {
  if (protocol_version() > kProtocolVersionClientMin) {
    set_protocol_version(protocol_version() - 1);

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
      last_host_response_time_millisecs_(
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)) {
  GetRequestID_();
  if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
    if (appmode->connections()->GetPrintUDPConnectProgress()) {
      g_base->ScreenMessage(
          g_base->assets->GetResourceString("connectingToPartyText"));
    }
  }
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

  auto current_time_millisecs =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  // If we've not gotten a client_id from the host yet, keep pestering it.
  if (!errored()) {
    if (client_id_ == -1
        && current_time_millisecs - last_client_id_request_time_ > 500) {
      last_client_id_request_time_ = current_time_millisecs;

      // Client request packet: contains our protocol version (2 bytes), our
      // request id (1 byte), and our session-identifier (remainder of the
      // message).
      const std::string& uuid{g_base->GetAppInstanceUUID()};
      std::vector<uint8_t> msg(4 + uuid.size());
      msg[0] = BA_PACKET_CLIENT_REQUEST;
      auto p_version = static_cast<uint16_t>(protocol_version());
      memcpy(&(msg[1]), &p_version, 2);
      msg[3] = request_id_;
      memcpy(&(msg[4]), uuid.c_str(), uuid.size());
      g_base->network_writer->PushSendToCall(msg, *addr_);
    }
  }

  // If its been long enough since we've heard anything from the host, error.
  if (current_time_millisecs - last_host_response_time_millisecs_
      > (can_communicate() ? 10000u : 5000u)) {
    // If the connection never got established, announce it failed.
    if (!can_communicate()) {
      g_base->ScreenMessage(
          g_base->assets->GetResourceString("connectionFailedText"), {1, 0, 0});
    }

    // Die immediately in this case; no use trying to wait for a
    // disconnect-ack since we've already given up hope of hearing from
    // them.
    Die();
    return;
  } else if (errored()) {
    // If we've errored, keep sending disconnect-requests periodically. Once
    // we get a response (or time out in the above code) we'll die.
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
  last_host_response_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

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

void ConnectionToHostUDP::RequestDisconnect() {
  // Mark us as errored so all future communication results in more
  // disconnect requests.
  set_errored(true);
  if (client_id_ != -1) {
    SendDisconnectRequest();
  }
}

}  // namespace ballistica::scene_v1
