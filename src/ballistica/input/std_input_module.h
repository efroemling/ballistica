// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_INPUT_STD_INPUT_MODULE_H_
#define BALLISTICA_INPUT_STD_INPUT_MODULE_H_

#include "ballistica/core/module.h"

namespace ballistica {

class StdInputModule : public Module {
 public:
  explicit StdInputModule(Thread* thread);
  ~StdInputModule() override;
  void PushBeginReadCall();

 private:
  std::string pending_input_;
};

}  // namespace ballistica

#endif  // BALLISTICA_INPUT_STD_INPUT_MODULE_H_
