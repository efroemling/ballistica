// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/macros.h"

#include <cstdio>
#include <cstring>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/generic/native_stack_trace.h"
#include "ballistica/shared/python/python.h"

// Snippets of compiled functionality used by our evil macros.

namespace ballistica {

auto MacroFunctionTimerStartTime() -> millisecs_t {
  return core::CorePlatform::TimeMonotonicMillisecs();
}

void MacroFunctionTimerEnd(core::CoreFeatureSet* corefs, millisecs_t starttime,
                           millisecs_t time, const char* funcname) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.variant_test_build()) {
    return;
  }
  assert(corefs);
  millisecs_t endtime = core::CorePlatform::TimeMonotonicMillisecs();
  if (endtime - starttime > time) {
    core::g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                               std::to_string(endtime - starttime)
                                   + " milliseconds spent in " + funcname);
  }
}

void MacroFunctionTimerEndThread(core::CoreFeatureSet* corefs,
                                 millisecs_t starttime, millisecs_t time,
                                 const char* funcname) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.variant_test_build()) {
    return;
  }
  assert(corefs);
  millisecs_t endtime = core::CorePlatform::TimeMonotonicMillisecs();
  if (endtime - starttime > time) {
    corefs->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        std::to_string(endtime - starttime) + " milliseconds spent by "
            + corefs->CurrentThreadName() + " thread in " + funcname);
  }
}

void MacroFunctionTimerEndEx(core::CoreFeatureSet* corefs,
                             millisecs_t starttime, millisecs_t time,
                             const char* funcname, const std::string& what) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.variant_test_build()) {
    return;
  }
  assert(corefs);
  millisecs_t endtime = core::CorePlatform::TimeMonotonicMillisecs();
  if (endtime - starttime > time) {
    corefs->logging->Log(LogName::kBa, LogLevel::kWarning,
                         std::to_string(endtime - starttime)
                             + " milliseconds spent in " + funcname + " for "
                             + what);
  }
}

void MacroFunctionTimerEndThreadEx(core::CoreFeatureSet* corefs,
                                   millisecs_t starttime, millisecs_t time,
                                   const char* funcname,
                                   const std::string& what) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.variant_test_build()) {
    return;
  }
  assert(corefs);
  millisecs_t endtime = core::CorePlatform::TimeMonotonicMillisecs();
  if (endtime - starttime > time) {
    corefs->logging->Log(LogName::kBa, LogLevel::kWarning,
                         std::to_string(endtime - starttime)
                             + " milliseconds spent by "
                             + corefs->CurrentThreadName() + " thread in "
                             + funcname + " for " + what);
  }
}

void MacroTimeCheckEnd(core::CoreFeatureSet* corefs, millisecs_t starttime,
                       millisecs_t time, const char* name, const char* file,
                       int line) {
  assert(corefs);
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.variant_test_build()) {
    return;
  }
  millisecs_t e = core::CorePlatform::TimeMonotonicMillisecs();
  if (e - starttime > time) {
    corefs->logging->Log(LogName::kBa, LogLevel::kWarning,
                         std::string(name) + " took "
                             + std::to_string(e - starttime) + " milliseconds; "
                             + MacroPathFilter(corefs, file) + " line "
                             + std::to_string(line));
  }
}

void MacroLogErrorNativeTrace(core::CoreFeatureSet* corefs,
                              const std::string& msg, const char* fname,
                              int line) {
  assert(corefs);
  char buffer[2048];
  snprintf(buffer, sizeof(buffer), "%s:%d:", MacroPathFilter(corefs, fname),
           line);
  auto trace = corefs->platform->GetNativeStackTrace();
  auto trace_s =
      trace ? trace->FormatForDisplay() : "<native stack trace unavailable>";
  corefs->logging->Log(LogName::kBa, LogLevel::kError,
                       std::string(buffer) + " error: " + msg + "\n" + trace_s);
}

void MacroLogErrorPythonTrace(core::CoreFeatureSet* corefs,
                              const std::string& msg, const char* fname,
                              int line) {
  assert(corefs);
  char buffer[2048];
  snprintf(buffer, sizeof(buffer), "%s:%d:", MacroPathFilter(corefs, fname),
           line);
  // FIXME: Should have the trace be part of the log; not a separate print.
  //  Since our logging goes through Python anyway, we should just ask
  //  Python do include the trace in our log call.
  Python::PrintStackTrace();
  corefs->logging->Log(LogName::kBa, LogLevel::kError,
                       std::string(buffer) + " error: " + msg);
}

void MacroLogError(core::CoreFeatureSet* corefs, const std::string& msg,
                   const char* fname, int line) {
  assert(corefs);
  char e_buffer[2048];
  snprintf(e_buffer, sizeof(e_buffer), "%s:%d:", MacroPathFilter(corefs, fname),
           line);
  corefs->logging->Log(LogName::kBa, LogLevel::kError,
                       std::string(e_buffer) + " error: " + msg);
}

void MacroLogPythonTrace(core::CoreFeatureSet* corefs, const std::string& msg) {
  assert(corefs);
  Python::PrintStackTrace();
  corefs->logging->Log(LogName::kBa, LogLevel::kError, msg);
}

auto MacroPathFilter(core::CoreFeatureSet* corefs, const char* filename)
    -> const char* {
  assert(corefs);
  // If we've got a build_src_dir set and filename starts with it, skip past
  // it.
  if (corefs && !corefs->build_src_dir().empty()
      && strstr(filename, core::g_core->build_src_dir().c_str()) == filename) {
    return filename + core::g_core->build_src_dir().size();
  }
  return filename;
}

}  // namespace ballistica
