// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_LOGGING_H_
#define BALLISTICA_CORE_LOGGING_H_

#include <string>

namespace ballistica {

class Logging {
 public:
  /// Print a string directly to stdout as well as the in-game console
  /// and any connected telnet consoles.
  static auto PrintStdout(const std::string& s, bool flush = false) -> void;

  /// Print a string directly to stderr as well as the in-game console
  /// and any connected telnet consoles.
  static auto PrintStderr(const std::string& s, bool flush = false) -> void;

  /// Write a string to the debug log.
  /// This will go to stdout, windows debug log, android log, etc. depending
  /// on the platform.
  static auto Log(const std::string& msg, bool to_stdout = true,
                  bool to_server = true) -> void;

  /// Ship logs to the master-server in a bg thread. If result is passed,
  /// it will be set to 1 on success and -1 on error.
  static auto DirectSendLogs(const std::string& prefix,
                             const std::string& suffix, bool instant,
                             int* result = nullptr) -> void;
};

}  // namespace ballistica

#endif  // BALLISTICA_CORE_LOGGING_H_
