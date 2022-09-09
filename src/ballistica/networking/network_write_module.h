// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_NETWORKING_NETWORK_WRITE_MODULE_H_
#define BALLISTICA_NETWORKING_NETWORK_WRITE_MODULE_H_

#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

// this thread handles network output and whatnot
class NetworkWriteModule {
 public:
  void PushSendToCall(const std::vector<uint8_t>& msg, const SockAddr& addr);
  explicit NetworkWriteModule(Thread* thread);
  auto thread() const -> Thread* { return thread_; }

 private:
  Thread* thread_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_NETWORKING_NETWORK_WRITE_MODULE_H_
