// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_NETWORKING_NETWORK_WRITE_MODULE_H_
#define BALLISTICA_NETWORKING_NETWORK_WRITE_MODULE_H_

#include <vector>

#include "ballistica/core/module.h"

namespace ballistica {

// this thread handles network output and whatnot
class NetworkWriteModule : public Module {
 public:
  void PushSendToCall(const std::vector<uint8_t>& msg, const SockAddr& addr);
  explicit NetworkWriteModule(Thread* thread);
};

}  // namespace ballistica

#endif  // BALLISTICA_NETWORKING_NETWORK_WRITE_MODULE_H_
