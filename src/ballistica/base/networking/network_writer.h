// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_NETWORKING_NETWORK_WRITER_H_
#define BALLISTICA_BASE_NETWORKING_NETWORK_WRITER_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

// A subsystem handling outbound network traffic.
class NetworkWriter {
 public:
  NetworkWriter();
  void OnMainThreadStartApp();

  void PushSendToCall(const std::vector<uint8_t>& msg, const SockAddr& addr);
  auto event_loop() const -> EventLoop* { return event_loop_; }

 private:
  EventLoop* event_loop_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_NETWORKING_NETWORK_WRITER_H_
