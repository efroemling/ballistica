// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_LOGGING_LOGGING_H_
#define BALLISTICA_CORE_LOGGING_LOGGING_H_

#include <mutex>
#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

// Slightly hacky, but don't want to store this with any of our normal
// global classes because it might be needed before they are allocated.

class Logging {
 public:
  Logging() = default;

  /// Log a message to the engine's log system.
  ///
  /// IMPORTANT: This direct-string overload should only be used when the
  /// message is a fixed string literal or already-built std::string that
  /// requires no runtime construction at the call site. If the message
  /// involves *any* runtime construction (concatenation, std::to_string,
  /// formatting, etc.), use the lambda overload below instead — this
  /// overload always evaluates its argument before the level check, so
  /// the construction work happens even when the log level is disabled.
  ///
  /// This is especially important for DEBUG-level calls, which are
  /// usually disabled in shipped builds; eager construction there pays a
  /// real cost for nothing.
  void Log(LogName name, LogLevel level, const std::string& msg) {
    // Checking log-level here is more efficient than letting it happen in
    // Python land.
    if (LogLevelEnabled(name, level)) {
      Log_(name, level, msg.c_str());
    }
  }

  /// C-string convenience overload. Same rules as the std::string version
  /// above: use the lambda overload for any runtime construction.
  void Log(LogName name, LogLevel level, const char* msg) {
    // Checking log-level here is more efficient than letting it happen in
    // Python land.
    if (LogLevelEnabled(name, level)) {
      Log_(name, level, msg);
    }
  }

  /// C-string convenience overload. Same rules as the std::string version
  /// above: use the lambda overload for any runtime construction.
  void Log(LogName name, LogLevel level, char* msg) {
    // Checking log-level here is more efficient than letting it happen in
    // Python land.
    if (LogLevelEnabled(name, level)) {
      Log_(name, level, msg);
    }
  }

  /// Lambda overload: takes a callable returning std::string instead of a
  /// string directly. The callable is invoked only when the log level is
  /// enabled, so any construction work inside it is skipped otherwise.
  ///
  /// USE THIS for *any* dynamically-constructed log message — concatenation,
  /// std::to_string, std::format, building a value from members, etc. —
  /// not just for messages that feel "expensive" to build. Even a single
  /// `"foo: " + std::to_string(x)` allocates and copies; routing it through
  /// a lambda costs nothing extra at the call site and saves the work
  /// whenever the level is off.
  ///
  /// DEBUG-level calls especially should default to this form: DEBUG is
  /// usually off, so any string-building done at a direct-overload call
  /// site is wasted work in the common case.
  ///
  /// Example:
  ///   g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug,
  ///                        [&] { return "Got " + std::to_string(n)
  ///                                     + " bytes from " + addr; });
  template <typename C>
  void Log(LogName name, LogLevel level, C getmsgcall) {
    // Make sure provided lambdas return std::string; otherwise it would be
    // an easy mistake to return a char* to invalid function-local memory.
    // static_assert(std::is_same<std::string, decltype(getmsgcall())>::value,
    //               "Lambda must return std::string");
    if (LogLevelEnabled(name, level)) {
      Log_(name, level, getmsgcall().c_str());
    }
  }

  void ApplyBaEnvConfig();

  /// Grab current Python logging levels for all logs we use internally. If
  /// any changes are made at runtime to Python logging levels that we use,
  /// this should be called after.
  void UpdateInternalLoggerLevels();

  /// Check whether a certain log name/level combo will be shown. It is much
  /// more efficient to gate log calls using this (especially frequent or
  /// debug ones) rather than letting the Python layer do the gating. Be
  /// aware, however, that UpdateInternalLoggerLevels() must be called after
  /// making any changes to Python logger levels to keep this internal
  /// system up to date.
  auto LogLevelEnabled(LogName name, LogLevel level) -> bool {
    return log_levels_[static_cast<int>(name)] <= level;
  }
  auto GetLogLevel(LogName name) -> int {
    return static_cast<int>(log_levels_[static_cast<int>(name)]);
  }

  /// Send a log message to the in-app console, platform-specific logs, etc.
  /// This generally should not be called directly but instead wired up to
  /// log messages coming through the Python logging system.
  void EmitLog(std::string_view name, LogLevel level, double timestamp,
               std::string_view msg);

 private:
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
  void Log_(LogName name, LogLevel level, const char* msg);

  LogLevel log_levels_[static_cast<int>(LogName::kLast)]{};
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_LOGGING_LOGGING_H_
