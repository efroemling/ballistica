// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/networking/network_writer.h"

#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/core/core.h"
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
  //
  // UPDATE: Disabling this for now. Am getting reports of servers
  // effectively dying after showing this message
  // (https://github.com/efroemling/ballistica/issues/862), so I'm wondering
  // if it's a pathological situation where once we hit this threshold then
  // we start to get a bunch of message re-sends which makes only the
  // situation worse. So perhaps its better to stick with the standard
  // behavior of logging warnings when the list gets too big and dying if it
  // gets out of control big. We could also try blocking in this call, but I
  // would want to know that it would not lead to things effectively
  // breaking also.
  //
  // if (!event_loop()->CheckPushSafety()) {
  //   BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
  //               "Network-writer buffer is full;"
  //               " dropping outbound messages.");
  //   return;
  // }
  event_loop()->PushCall([msg, addr] {
    assert(g_base->network_reader);
    Networking::SendTo(msg, addr);
  });
}

}  // namespace ballistica::base
