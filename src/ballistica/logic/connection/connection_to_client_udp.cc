// Released under the MIT License. See LICENSE for details.

#include "ballistica/logic/connection/connection_to_client_udp.h"

#include "ballistica/logic/connection/connection_set.h"
#include "ballistica/logic/logic.h"
#include "ballistica/networking/network_writer.h"
#include "ballistica/networking/sockaddr.h"

namespace ballistica {

ConnectionToClientUDP::ConnectionToClientUDP(const SockAddr& addr,
                                             std::string client_name,
                                             uint8_t request_id, int client_id)
    : ConnectionToClient(client_id),
      request_id_(request_id),
      addr_(new SockAddr(addr)),
      client_instance_uuid_(std::move(client_name)),
      last_client_response_time_(g_logic->master_time()),
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
  assert(g_network_writer);
  g_network_writer->PushSendToCall(data_full, *addr_);
}

void ConnectionToClientUDP::Update() {
  ConnectionToClient::Update();

  millisecs_t current_time = g_logic->master_time();

  // if its been long enough since we've heard anything from the host, error.
  if (current_time - last_client_response_time_
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
  last_client_response_time_ = g_logic->master_time();
  ConnectionToClient::HandleGamePacket(buffer);
}

void ConnectionToClientUDP::Die() {
  if (did_die_) {
    Log(LogLevel::kError, "Posting multiple die messages; probably not good.");
    return;
  }
  // this will actually clear the object..
  g_logic->connections()->PushClientDisconnectedCall(id());
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
  g_network_writer->PushSendToCall(data, *addr_);
}

}  // namespace ballistica
