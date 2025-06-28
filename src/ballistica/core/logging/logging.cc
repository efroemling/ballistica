// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/logging/logging.h"

#include <cstdio>
#include <string>

#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/math/vector4f.h"

namespace ballistica::core {

int g_early_v1_cloud_log_writes{10};

void Logging::EmitLog(const std::string& name, LogLevel level, double timestamp,
                      const std::string& msg) {
  assert(g_base_soft);
  // Print to the dev console.
  if (name == "stdout" || name == "stderr") {
    // Print stdout/stderr entries with no extra info.
    g_base_soft->PushDevConsolePrintCall(msg, 1.0f, kVector4f1);
  } else {
    auto elt{g_core->ba_env_launch_timestamp()};

    // Show -1 for time if we don't have a launch timestamp yet.
    auto rel_time{elt > 0.0 ? (timestamp - elt) : -1.0};

    if (g_base_soft) {
      Vector4f logcolor;
      switch (level) {
        case LogLevel::kDebug:
          logcolor = Vector4f(0.0f, 0.5f, 1.0f, 1.0f);
          break;
        case LogLevel::kInfo:
          logcolor = Vector4f(1.0f, 1.0f, 1.0f, 1.0f);
          break;
        case LogLevel::kWarning:
          logcolor = Vector4f(1.0f, 0.7f, 0.0f, 1.0f);
          break;
        case LogLevel::kError:
          logcolor = Vector4f(1.0f, 0.0, 0.0f, 1.0f);
          break;
        case LogLevel::kCritical:
          logcolor = Vector4f(0.6f, 0.0, 0.25f, 1.0f);
          break;
      }
      char prestr[256];

      snprintf(prestr, sizeof(prestr), "%.3f  %s", rel_time, name.c_str());
      g_base_soft->PushDevConsolePrintCall("", 0.3f, kVector4f1);
      g_base_soft->PushDevConsolePrintCall(
          prestr, 0.75f,
          Vector4f(logcolor.x * 0.4f + 0.6f, logcolor.y * 0.4f + 0.6f,
                   logcolor.z * 0.4f + 0.6f, 0.75));
      g_base_soft->PushDevConsolePrintCall(msg, 1.0f, logcolor);
    }
  }

  // Ship to platform-specific display mechanisms (android log, etc).
  if (g_core) {
    g_core->platform->EmitPlatformLog(name, level, msg);
  }
}

void Logging::V1CloudLog(const std::string& msg) {
  // Route through platform-specific loggers if present.

  assert(g_core);

  if (g_core) {
    // (ship to things like Crashlytics crash-logging)
    g_core->platform->LowLevelDebugLog(msg);

    // Add to our complete v1-cloud-log.
    std::scoped_lock lock(v1_cloud_log_mutex_);
    if (!v1_cloud_log_full_) {
      v1_cloud_log_ += (msg + "\n");
      if (v1_cloud_log_.size() > 25000) {
        // Allow some reasonable overflow for last statement.
        if (v1_cloud_log_.size() > 250000) {
          // FIXME: This could potentially chop up utf-8 chars.
          v1_cloud_log_.resize(250000);
        }
        v1_cloud_log_ += "\n<max log size reached>\n";
        v1_cloud_log_full_ = true;
      }
    }
  }

  // If the base feature-set is up, ship it off there for further handling.
  if (g_base_soft) {
    g_base_soft->DoV1CloudLog(msg);
  }
}

void Logging::Log_(LogName name, LogLevel level, const std::string& msg) {
  assert(g_core);
  // Wrappers calling us should be checking this.
  assert(LogLevelEnabled(name, level));

  g_core->python->LoggingCall(name, level, msg);
}

void Logging::ApplyBaEnvConfig() {
  // This is also a reasonable time to grab initial logger levels that baenv
  // likely mucked with. For any changes after this to make it to the native
  // layer, babase.update_internal_logger_levels() must be called.
  UpdateInternalLoggerLevels();
}

void Logging::UpdateInternalLoggerLevels() {
  g_core->python->UpdateInternalLoggerLevels(log_levels_);
}

}  // namespace ballistica::core
