// Copyright (c) 2011-2020 Eric Froemling

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
        DirectSendLogs(logprefix, logsuffix, false);
      }
    }
  }
}

auto Logging::DirectSendLogs(const std::string& prefix,
                             const std::string& suffix, bool instant,
                             int* result) -> void {
  // Use a rough mechanism to restrict log uploads to 1 send per second.
  static time_t last_non_instant_send_time{-1};
  if (!instant) {
    auto curtime = Platform::GetCurrentSeconds();
    if (curtime == last_non_instant_send_time) {
      return;
    }
    last_non_instant_send_time = curtime;
  }

  std::thread t([prefix, suffix, instant, result]() {
    // For non-instant sends, sleep for 2 seconds before sending logs;
    // this should capture the just-added log as well as any more that
    // got added in the subsequent second when we were not launching new
    // send threads.
    if (!instant) {
      Platform::SleepMS(2000);
    }
    std::string log;

    // Send our blessing hash only after we've calculated it; don't use our
    // internal one. This means that we'll get false-negatives on whether
    // direct-sent logs are blessed, but I think that's better than false
    // positives.
    std::string calced_blessing_hash;
    if (g_app_globals) {
      std::lock_guard<std::mutex> lock(g_app_globals->log_mutex);
      log = g_app_globals->log;
      calced_blessing_hash = g_app_globals->calced_blessing_hash;
    } else {
      log = "(g_app_globals not yet inited; no global log available)";
    }
    if (!prefix.empty()) {
      log = prefix + "\n" + log;
    }
    if (!suffix.empty()) {
      log = log + "\n" + suffix;
    }

    // Also send our blessing-calculation state; we may want to distinguish
    // between blessing not being calced yet and being confirmed as un-blessed.
    // FIXME: should probably do this in python layer log submits too.
    std::string bless_calc_state;
    if (kBlessingHash == nullptr) {
      bless_calc_state = "nointhash";
    } else if (g_app_globals == nullptr) {
      bless_calc_state = "noglobs";
    } else if (g_app_globals->calced_blessing_hash.empty()) {
      // Mention we're calculating, but also mention if it is likely that
      // the user is mucking with stuff.
      if (g_app_globals->user_ran_commands
          || g_platform->using_custom_app_python_dir()) {
        bless_calc_state = "calcing_likely_modded";
      } else {
        bless_calc_state = "calcing_not_modded";
      }
    } else {
      bless_calc_state = "done";
    }

    std::string path{"/bsLog"};
    std::map<std::string, std::string> params{
        {"log", log},
        {"time", "-1"},
        {"userAgentString", g_app_globals ? g_app_globals->user_agent_string
                                          : "(no g_app_globals)"},
        {"newsShow", calced_blessing_hash.c_str()},
        {"bcs", bless_calc_state.c_str()},
        {"build", std::to_string(kAppBuildNumber)}};
    try {
      Networking::MasterServerPost(path, params);
      if (result) {
        *result = 1;  // SUCCESS!
      }
    } catch (const std::exception&) {
      // Try our fallback master-server address if that didn't work.
      try {
        params["log"] = prefix + "(FALLBACK-ADDR):\n" + log;
        Networking::MasterServerPost(path, params, true);
        if (result) {
          *result = 1;  // SUCCESS!
        }
      } catch (const std::exception& exc) {
        // Well, we tried; make a note to platform log if available
        // that we failed.
        if (g_platform != nullptr) {
          g_platform->HandleLog(std::string("Early log-to-server failed: ")
                                + exc.what());
        }
        if (result) {
          *result = -1;  // FAIL!!
        }
      }
    }
  });
  t.detach();
}

}  // namespace ballistica
