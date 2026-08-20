// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/logging/logging.h"

#include <cstdio>
#include <string>

#include "ballistica/core/platform/platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/math/vector4f.h"

namespace ballistica::core {

void Logging::EmitLog(std::string_view name, LogLevel level, double timestamp,
                      std::string_view msg) {
  // Dev-console printing is only possible once base is up. Callers from
  // early startup (e.g. fatal-error reporting during
  // CoreFeatureSet::Import) will skip this branch and fall through to
  // platform-log routing below.
  if (g_base_soft) {
    if (name == "stdout" || name == "stderr") {
      // Print stdout/stderr entries with no extra info.
      g_base_soft->PushDevConsolePrintCall(
          {{std::string(msg), 1.0f, kVector4f1}});
    } else {
      auto elt{g_core->ba_env_launch_timestamp()};

      // Show -1 for time if we don't have a launch timestamp yet.
      auto rel_time{elt > 0.0 ? (timestamp - elt) : -1.0};

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

      snprintf(prestr, sizeof(prestr), "%.3f  %.*s", rel_time,
               static_cast<int>(name.size()), name.data());
      // Ship the whole entry (spacer + prefix + message) as ONE batched
      // call: a single logic-thread message instead of three. Per-line
      // calls let a verbose-logging burst flood that queue (the >1000
      // ThreadMessage ERROR / >10000 FatalError guards).
      g_base_soft->PushDevConsolePrintCall(
          {{"", 0.3f, kVector4f1},
           {prestr, 0.75f,
            Vector4f(logcolor.x * 0.4f + 0.6f, logcolor.y * 0.4f + 0.6f,
                     logcolor.z * 0.4f + 0.6f, 0.75)},
           {std::string(msg), 1.0f, logcolor}});
    }
  }

  // Ship to platform-specific display mechanisms (android log, etc).
  if (g_core) {
    g_core->platform->EmitPlatformLog(name, level, msg);
  }
}

void Logging::Log_(LogName name, LogLevel level, const char* msg) {
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
