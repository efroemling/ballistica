// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_LOGGING_LOGGING_H_
#define BALLISTICA_CORE_LOGGING_LOGGING_H_

#include <mutex>
#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

// Slightly hacky, but don't want to store this with any of our normal
// global classes because it might be needed before they are allocated.
extern int g_early_v1_cloud_log_writes;

class Logging {
 public:
  Logging() = default;

  void Log(LogName name, LogLevel level, const std::string& msg);
  void Log(LogName name, LogLevel level, const char* msg);
  void Log(LogName name, LogLevel level, char* msg);

  void ApplyBaEnvConfig();

  /// Log call variant taking a call returning a string instead of a string
  /// directly. This can be useful for log strings requiring significant
  /// effort to construct, as the call will be skipped if the log level is
  /// not currently visible.
  template <typename C>
  void Log(LogName name, LogLevel level, C getmsgcall) {
    if (!LogLevelEnabled(name, level)) {
      return;
    }
    Log(name, level, getmsgcall());
  }

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
  void Log_(LogName name, LogLevel level, const std::string& msg);

  /// Send a log message to the in-app console, platform-specific logs, etc.
  /// This generally should not be called directly but instead wired up to
  /// log messages coming through the Python logging system.
  void EmitLog(const std::string& name, LogLevel level, double timestamp,
               const std::string& msg);

  /// Write a message to the v1 cloud log. This is considered legacy and
  /// will be phased out eventually.
  void V1CloudLog(const std::string& msg);

  auto v1_cloud_log_mutex() -> std::mutex& { return v1_cloud_log_mutex_; }
  auto v1_cloud_log() const { return v1_cloud_log_; }
  auto did_put_v1_cloud_log() const { return did_put_v1_cloud_log_; }
  void set_did_put_v1_cloud_log(bool val) { did_put_v1_cloud_log_ = val; }
  auto v1_cloud_log_full() const { return v1_cloud_log_full_; }

 private:
  LogLevel log_levels_[static_cast<int>(LogName::kLast)]{};
  bool did_put_v1_cloud_log_{};
  bool v1_cloud_log_full_{};
  std::mutex v1_cloud_log_mutex_;
  std::string v1_cloud_log_;
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_LOGGING_LOGGING_H_
