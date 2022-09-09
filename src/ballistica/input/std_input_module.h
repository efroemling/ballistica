// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INPUT_STD_INPUT_MODULE_H_
#define BALLISTICA_INPUT_STD_INPUT_MODULE_H_

#include "ballistica/ballistica.h"

namespace ballistica {

class StdInputModule {
 public:
  explicit StdInputModule(Thread* thread);
  void PushBeginReadCall();
  auto thread() const -> Thread* { return thread_; }

 private:
  Thread* thread_{};
  std::string pending_input_;
};

}  // namespace ballistica

#endif  // BALLISTICA_INPUT_STD_INPUT_MODULE_H_
