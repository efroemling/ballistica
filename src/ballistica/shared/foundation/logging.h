// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_LOGGING_H_
#define BALLISTICA_SHARED_FOUNDATION_LOGGING_H_

#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica {

// Slightly hacky, but don't want to store this with any of our normal
// global classes because it might be needed before they are allocated.
extern int g_early_v1_cloud_log_writes;

class Logging {
 public:
  /// Write a message to the log. Intended for logging use in C++ code. This
  /// is safe to call by any thread at any time as long as core has been
  /// inited. In general it simply passes through to the equivalent Python
  /// logging call: logging.info, logging.warning, etc.
  ///
  /// Be aware that Log() calls made before babase is imported will be
  /// stored and submitted all at once to Python once babase is imported
  /// (with a [HELD] prefix). Ballistica's log/print redirection gets
  /// finalized at that point and this system ensures all C++ Log() calls
  /// ever made will be routed through the app, visible in in-app consoles,
  /// etc. Note that direct Python logging calls or prints occurring before
  /// babase is imported may not be visible in the app for that same reason.
  static void Log(LogLevel level, const std::string& msg);

  /// Send a log message to the in-app console, platform-specific logs, etc.
  /// This generally should not be called directly but instead wired up to
  /// log messages coming through the Python logging system.
  static void EmitLog(const std::string& name, LogLevel level,
                      const std::string& msg);

  /// Write a message to the v1 cloud log. This is considered legacy and
  /// will be phased out eventually.
  static void V1CloudLog(const std::string& msg);
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_LOGGING_H_
