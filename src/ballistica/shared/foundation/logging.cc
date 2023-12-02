// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/logging.h"

#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"

namespace ballistica {

// Note: we implicitly use core functionality. Our behavior is undefined
// if nobody has imported core yet.
using core::g_base_soft;
using core::g_core;

int g_early_v1_cloud_log_writes{10};

void Logging::Log(LogLevel level, const std::string& msg) {
  BA_PRECONDITION(g_core);
  g_core->python->LoggingCall(level, msg);
}

void Logging::EmitLog(const std::string& name, LogLevel level,
                      const std::string& msg) {
  // Print to the dev console.
  if (g_base_soft) {
    g_base_soft->PushDevConsolePrintCall(msg + "\n");
  }

  // Ship to platform-specific display mechanisms (android log, etc).
  if (g_core) {
    g_core->platform->EmitPlatformLog(name, level, msg);
  }
}

void Logging::V1CloudLog(const std::string& msg) {
  // Route through platform-specific loggers if present.

  if (g_core) {
    // (ship to things like Crashlytics crash-logging)
    g_core->platform->LowLevelDebugLog(msg);

    // Add to our complete v1-cloud-log.
    std::scoped_lock lock(g_core->v1_cloud_log_mutex);
    if (!g_core->v1_cloud_log_full) {
      (g_core->v1_cloud_log) += (msg + "\n");
      if ((g_core->v1_cloud_log).size() > 25000) {
        // Allow some reasonable overflow for last statement.
        if ((g_core->v1_cloud_log).size() > 250000) {
          // FIXME: This could potentially chop up utf-8 chars.
          (g_core->v1_cloud_log).resize(250000);
        }
        g_core->v1_cloud_log += "\n<max log size reached>\n";
        g_core->v1_cloud_log_full = true;
      }
    }
  }

  // If the base feature-set is up, ship it off there for further handling.
  if (g_base_soft) {
    g_base_soft->DoV1CloudLog(msg);
  }
}

}  // namespace ballistica
