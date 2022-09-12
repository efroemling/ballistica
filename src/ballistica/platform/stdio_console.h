// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PLATFORM_STDIO_CONSOLE_H_
#define BALLISTICA_PLATFORM_STDIO_CONSOLE_H_

#include "ballistica/ballistica.h"

namespace ballistica {

class StdioConsole {
 public:
  StdioConsole();
  void OnAppStart();
  auto thread() const -> Thread* { return thread_; }

 private:
  Thread* thread_{};
  std::string pending_input_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PLATFORM_STDIO_CONSOLE_H_
