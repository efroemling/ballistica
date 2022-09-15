// Released under the MIT License. See LICENSE for details.

#include "ballistica/networking/network_writer.h"

#include "ballistica/core/thread.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/sockaddr.h"

namespace ballistica {

NetworkWriter::NetworkWriter() {
  // We're a singleton; make sure we don't already exist.
  assert(g_network_writer == nullptr);

  // Spin up our thread.
  thread_ = new Thread(ThreadTag::kNetworkWrite);
  g_app->pausable_threads.push_back(thread_);
}

void NetworkWriter::PushSendToCall(const std::vector<uint8_t>& msg,
                                   const SockAddr& addr) {
  // Avoid buffer-full errors if something is causing us to write too often;
  // these are unreliable messages so its ok to just drop them.
  if (!thread()->CheckPushSafety()) {
    BA_LOG_ONCE(LogLevel::kError,
                "Excessive send-to calls in net-write-module.");
    return;
  }
  thread()->PushCall([this, msg, addr] {
    assert(g_network_reader);
    Networking::SendTo(msg, addr);
  });
}

}  // namespace ballistica
