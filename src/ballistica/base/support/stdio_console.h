// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_STDIO_CONSOLE_H_
#define BALLISTICA_BASE_SUPPORT_STDIO_CONSOLE_H_

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

class StdioConsole {
 public:
  StdioConsole();
  void Start();
  auto event_loop() const -> EventLoop* { return event_loop_; }

 private:
  void StartInMainThread();
  void PushCommand(const std::string& command);
  EventLoop* event_loop_{};
  std::string pending_input_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_STDIO_CONSOLE_H_
