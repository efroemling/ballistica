// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_STDIO_CONSOLE_H_
#define BALLISTICA_BASE_SUPPORT_STDIO_CONSOLE_H_

#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

class StdioConsole {
 public:
  StdioConsole();
  void Start();
  auto event_loop() const -> EventLoop* { return event_loop_; }

 private:
  void StartInMainThread_();
  void PushCommand_(const std::string& command);
  void Clear_();
  EventLoop* event_loop_{};
  std::string pending_input_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_STDIO_CONSOLE_H_
