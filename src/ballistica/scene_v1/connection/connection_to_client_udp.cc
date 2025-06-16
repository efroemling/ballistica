// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/connection/connection_to_client_udp.h"

#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_writer.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/connection/connection_set.h"

namespace ballistica::scene_v1 {

ConnectionToClientUDP::ConnectionToClientUDP(const SockAddr& addr,
                                             std::string client_name,
                                             uint8_t request_id, int client_id)
    : ConnectionToClient(client_id),
      request_id_(request_id),
      addr_(new SockAddr(addr)),
      client_instance_uuid_(std::move(client_name)),
      last_client_response_time_millisecs_(
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)),
      did_die_(false) {}

ConnectionToClientUDP::~ConnectionToClientUDP() {
  // This prevents anything from trying to send
  // (and thus crashing in pure-virtual SendGamePacketCompressed) as we die.
  set_connection_dying(true);
}

void ConnectionToClientUDP::SendGamePacketCompressed(
    const std::vector<uint8_t>& data) {
  // Ok, we've got a random chunk of (possibly) compressed data to send over
  // the wire.. lets stick a header on it and ship it out.
  std::vector<uint8_t> data_full(data.size() + 2);
  memcpy(&(data_full[2]), &data[0], data.size());
  data_full[0] = BA_PACKET_HOST_GAMEPACKET_COMPRESSED;

  // Go ahead and include their original request_id so they know we're talking
  // to them.
  data_full[1] = request_id_;

  // Ship this off to the net-out thread to send; at this point we don't know
  // or case what happens to it.
  assert(g_base->network_writer);
  g_base->network_writer->PushSendToCall(data_full, *addr_);
}

void ConnectionToClientUDP::Update() {
  ConnectionToClient::Update();
  auto current_time_millisecs =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  // if its been long enough since we've heard anything from the host, error.
  if (current_time_millisecs - last_client_response_time_millisecs_
      > (can_communicate() ? 10000u : 5000u)) {
    // die immediately in this case; no use trying to wait for a
    // disconnect-ack since we've already given up hope of hearing from them..
    Die();
    return;
  }
}
void ConnectionToClientUDP::HandleGamePacket(
    const std::vector<uint8_t>& buffer) {
  // keep track of when we last heard from the host for disconnect purposes
  last_client_response_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  ConnectionToClient::HandleGamePacket(buffer);
}

void ConnectionToClientUDP::Die() {
  if (did_die_) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                         "Posting multiple die messages; probably not good.");
    return;
  }
  // this will actually clear the object..
  if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
    appmode->connections()->PushClientDisconnectedCall(id());
  }
  did_die_ = true;
}

auto ConnectionToClientUDP::GetAsUDP() -> ConnectionToClientUDP* {
  return this;
}

void ConnectionToClientUDP::RequestDisconnect() {
  // mark us as errored so all future communication results in more disconnect
  // requests
  set_errored(true);
  SendDisconnectRequest();
}

void ConnectionToClientUDP::SendDisconnectRequest() {
  std::vector<uint8_t> data(2);
  data[0] = BA_PACKET_DISCONNECT_FROM_HOST_REQUEST;
  data[1] = static_cast<uint8_t>(id());
  g_base->network_writer->PushSendToCall(data, *addr_);
}

}  // namespace ballistica::scene_v1
