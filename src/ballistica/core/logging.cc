// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/logging.h"

#include <map>

#include "ballistica/app/app_globals.h"
#include "ballistica/ballistica.h"
#include "ballistica/game/game.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

static void PrintCommon(const std::string& s) {
  // Print to in-game console.
  {
    if (g_game != nullptr) {
      g_game->PushConsolePrintCall(s);
    } else {
      if (g_platform != nullptr) {
        g_platform->HandleLog(
            "Warning: Log() called before game-thread setup; "
            "will not appear on in-game console.\n");
      }
    }
  }
  // Print to any telnet clients.
  if (g_app_globals && g_app_globals->telnet_server) {
    g_app_globals->telnet_server->PushPrint(s);
  }
}

void Logging::PrintStdout(const std::string& s, bool flush) {
  fprintf(stdout, "%s", s.c_str());
  if (flush) {
    fflush(stdout);
  }
  PrintCommon(s);
}

void Logging::PrintStderr(const std::string& s, bool flush) {
  fprintf(stderr, "%s", s.c_str());
  if (flush) {
    fflush(stderr);
  }
  PrintCommon(s);
}

void Logging::Log(const std::string& msg, bool to_stdout, bool to_server) {
  if (to_stdout) {
    PrintStdout(msg + "\n", true);
  }

  // Ship to the platform logging mechanism (android-log, stderr, etc.)
  // if that's available yet.
  if (g_platform != nullptr) {
    g_platform->HandleLog(msg);
  }

  // Ship to master-server/etc.
  if (to_server) {
    // Route through platform-specific loggers if present.
    // (things like Crashlytics crash-logging)
    if (g_platform) {
      Platform::DebugLog(msg);
    }

    // Add to our complete log.
    if (g_app_globals != nullptr) {
      std::lock_guard<std::mutex> lock(g_app_globals->log_mutex);
      if (!g_app_globals->log_full) {
        (g_app_globals->log) += (msg + "\n");
        if ((g_app_globals->log).size() > 10000) {
          // Allow some reasonable overflow for last statement.
          if ((g_app_globals->log).size() > 100000) {
            // FIXME: This could potentially chop up utf-8 chars.
            (g_app_globals->log).resize(100000);
          }
          g_app_globals->log += "\n<max log size reached>\n";
          g_app_globals->log_full = true;
        }
      }
    }

    // If the game is fully bootstrapped, let the Python layer handle logs.
    // It will group log messages intelligently  and ship them to the
    // master server with various other context info included.
    if (g_app_globals && g_app_globals->is_bootstrapped) {
      assert(g_python != nullptr);
      g_python->PushObjCall(Python::ObjID::kHandleLogCall);
    } else {
      // For log messages during bootstrapping we ship them immediately since
      // we don't know if the Python layer is (or will be) able to.
      if (g_early_log_writes > 0) {
        g_early_log_writes -= 1;
        std::string logprefix = "EARLY-LOG:";
        std::string logsuffix;

        // If we're an early enough error, our global log isn't even available,
        // so include this specific message as a suffix instead.
        if (g_app_globals == nullptr) {
          logsuffix = msg;
        }
        AppInternalDirectSendLogs(logprefix, logsuffix, false);
      }
    }
  }
}

}  // namespace ballistica
