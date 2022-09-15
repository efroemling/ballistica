// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/logging.h"

#include <map>

#include "ballistica/app/app.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/logic/logic.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

auto Logging::Log(LogLevel level, const std::string& msg) -> void {
  // This is basically up to Python to handle, but its up to us
  // if Python's not up yet.
  if (!g_python) {
    // Make an attempt to get it at least seen (and note the fact
    // that its super-early).
    const char* errmsg{"Logging::Log() called before g_python exists."};
    if (g_platform) {
      g_platform->DisplayLog("root", LogLevel::kError, errmsg);
      g_platform->DisplayLog("root", level, msg);
    }
    fprintf(stderr, "%s\n%s\n", errmsg, msg.c_str());
    return;
  }

  // All we want to do is call Python logging.XXX. That's on Python.
  g_python->LoggingCall(level, msg);
}

auto Logging::DisplayLog(const std::string& name, LogLevel level,
                         const std::string& msg) -> void {
  auto msgnewline{msg + "\n"};

  // Print to in-game console.
  {
    if (g_logic != nullptr) {
      g_logic->PushConsolePrintCall(msgnewline);
    } else {
      if (g_platform != nullptr) {
        g_platform->DisplayLog("root", LogLevel::kWarning,
                               "DisplayLog() called before logic-thread setup; "
                               "will not appear on in-game console.");
      }
    }
  }

  // Print to any telnet clients.
  if (g_app && g_app->telnet_server) {
    g_app->telnet_server->PushPrint(msgnewline);
  }

  // Ship to platform-specific display mechanisms (android log, etc).
  g_platform->DisplayLog(name, level, msg);
}

auto Logging::V1CloudLog(const std::string& msg) -> void {
  // Route through platform-specific loggers if present.
  // (things like Crashlytics crash-logging)
  if (g_platform) {
    Platform::DebugLog(msg);
  }

  // Add to our complete v1-cloud-log.
  if (g_app != nullptr) {
    std::scoped_lock lock(g_app->v1_cloud_log_mutex);
    if (!g_app->v1_cloud_log_full) {
      (g_app->v1_cloud_log) += (msg + "\n");
      if ((g_app->v1_cloud_log).size() > 10000) {
        // Allow some reasonable overflow for last statement.
        if ((g_app->v1_cloud_log).size() > 100000) {
          // FIXME: This could potentially chop up utf-8 chars.
          (g_app->v1_cloud_log).resize(100000);
        }
        g_app->v1_cloud_log += "\n<max log size reached>\n";
        g_app->v1_cloud_log_full = true;
      }
    }
  }

  // If the game is fully bootstrapped, let the Python layer handle logs.
  // It will group log messages intelligently  and ship them to the
  // master server with various other context info included.
  if (g_app && g_app->is_bootstrapped) {
    assert(g_python != nullptr);
    g_python->PushObjCall(Python::ObjID::kHandleV1CloudLogCall);
  } else {
    // For log messages during bootstrapping we ship them immediately since
    // we don't know if the Python layer is (or will be) able to.
    if (g_early_v1_cloud_log_writes > 0) {
      g_early_v1_cloud_log_writes -= 1;
      std::string logprefix = "EARLY-LOG:";
      std::string logsuffix;

      // If we're an early enough error, our global log isn't even available,
      // so include this specific message as a suffix instead.
      if (g_app == nullptr) {
        logsuffix = msg;
      }
      g_app_internal->DirectSendV1CloudLogs(logprefix, logsuffix, false);
    }
  }
}

}  // namespace ballistica
