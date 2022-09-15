// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_LOGGING_H_
#define BALLISTICA_CORE_LOGGING_H_

#include <string>

#include "ballistica/ballistica.h"

namespace ballistica {

class Logging {
 public:
  /// Write a message to the log. Intended for logging use in C++ code.
  /// This is safe to call by any thread at any time. In general it simply
  /// passes through to the equivalent Python log calls: logging.info,
  /// logging.warning, etc.
  /// Note that log messages often must go through some background
  /// processing before being seen by the user, meaning they may not
  /// always work well for tight debugging purposes. In cases such as these,
  /// printf() type calls or calling DisplayLog() directly may work better.
  /// (though both of these should be avoided in permanent code).
  static auto Log(LogLevel level, const std::string& msg) -> void;

  /// Immediately display a log message in the in-game console,
  /// platform-specific logs, etc. This generally should not be called
  /// directly but instead wired up to display messages coming from the
  /// Python logging system.
  static auto DisplayLog(const std::string& name, LogLevel level,
                         const std::string& msg) -> void;

  /// Write a message to the v1 cloud log. This is considered legacy
  /// and will be phased out eventually.
  static auto V1CloudLog(const std::string& msg) -> void;
};

}  // namespace ballistica

#endif  // BALLISTICA_CORE_LOGGING_H_
