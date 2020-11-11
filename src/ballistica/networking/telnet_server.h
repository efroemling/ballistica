// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_NETWORKING_TELNET_SERVER_H_
#define BALLISTICA_NETWORKING_TELNET_SERVER_H_

#include <condition_variable>
#include <mutex>
#include <string>
#include <thread>

#include "ballistica/ballistica.h"

namespace ballistica {

class TelnetServer {
 public:
  explicit TelnetServer(int port);
  ~TelnetServer();
  auto Pause() -> void;
  auto Resume() -> void;
  auto PushTelnetScriptCommand(const std::string& command) -> void;
  auto PushPrint(const std::string& s) -> void;
  auto SetAccessEnabled(bool v) -> void;
  auto SetPassword(const char* password) -> void;  // nullptr == no password

 private:
  auto RunThread() -> int;
  auto Print(const std::string& s) -> void;
  static auto RunThreadStatic(void* self) -> int {
    return static_cast<TelnetServer*>(self)->RunThread();
  }
  int sd_{-1};
  int client_sd_{-1};
  int port_{};
  std::thread* thread_{};
  bool have_asked_user_for_access_{};
  bool user_has_granted_access_{};
  bool paused_{};
  bool reading_password_{};
  bool require_password_{};
  millisecs_t last_try_time_{};
  std::string password_;
  std::mutex paused_mutex_;
  std::condition_variable paused_cv_;
};

}  // namespace ballistica

#endif  // BALLISTICA_NETWORKING_TELNET_SERVER_H_
