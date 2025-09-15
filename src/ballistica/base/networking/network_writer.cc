// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/networking/network_writer.h"

#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/networking/sockaddr.h"

namespace ballistica::base {

NetworkWriter::NetworkWriter() {}

void NetworkWriter::OnMainThreadStartApp() {
  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kNetworkWrite);
  g_core->suspendable_event_loops.push_back(event_loop_);
}

void NetworkWriter::PushSendToCall(const std::vector<uint8_t>& msg,
                                   const SockAddr& addr) {
  // These are unreliable sends so its ok to drop stuff instead of possibly
  // dying due to event loop hitting its limit.
  if (!event_loop()->CheckPushSafety()) {
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                "Network-writer buffer is full;"
                " dropping outbound messages.");
    return;
  }
  event_loop()->PushCall([msg, addr] {
    assert(g_base->network_reader);
    Networking::SendTo(msg, addr);
  });
}

}  // namespace ballistica::base
