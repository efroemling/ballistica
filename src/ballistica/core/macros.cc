// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/core/macros.h"

#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

// Snippets of compiled functionality used by our evil macros.

namespace ballistica {

void MacroFunctionTimerEnd(millisecs_t starttime, millisecs_t time,
                           const char* funcname) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.test_build()) {
    return;
  }
  millisecs_t endtime = g_platform->GetTicks();
  if (endtime - starttime > time) {
    Log("Warning: " + std::to_string(endtime - starttime)
        + " milliseconds spent in " + funcname);
  }
}

void MacroFunctionTimerEndThread(millisecs_t starttime, millisecs_t time,
                                 const char* funcname) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.test_build()) {
    return;
  }
  millisecs_t endtime = g_platform->GetTicks();
  if (endtime - starttime > time) {
    Log("Warning: " + std::to_string(endtime - starttime)
        + " milliseconds spent by " + ballistica::GetCurrentThreadName()
        + " thread in " + funcname);
  }
}

void MacroFunctionTimerEndEx(millisecs_t starttime, millisecs_t time,
                             const char* funcname, const std::string& what) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.test_build()) {
    return;
  }
  millisecs_t endtime = g_platform->GetTicks();
  if (endtime - starttime > time) {
    Log("Warning: " + std::to_string(endtime - starttime)
        + " milliseconds spent in " + funcname + " for " + what);
  }
}

void MacroFunctionTimerEndThreadEx(millisecs_t starttime, millisecs_t time,
                                   const char* funcname,
                                   const std::string& what) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.test_build()) {
    return;
  }
  millisecs_t endtime = g_platform->GetTicks();
  if (endtime - starttime > time) {
    Log("Warning: " + std::to_string(endtime - starttime)
        + " milliseconds spent by " + ballistica::GetCurrentThreadName()
        + " thread in " + funcname + " for " + what);
  }
}

void MacroTimeCheckEnd(millisecs_t starttime, millisecs_t time,
                       const char* name, const char* file, int line) {
  // Currently disabling this for test builds; not really useful for
  // the general public.
  if (g_buildconfig.test_build()) {
    return;
  }
  millisecs_t e = g_platform->GetTicks();
  if (e - starttime > time) {
    Log(std::string("Warning: ") + name + " took "
        + std::to_string(e - starttime) + " milliseconds; " + file + " line "
        + std::to_string(line));
  }
}

void MacroLogErrorTrace(const std::string& msg, const char* fname, int line) {
  char buffer[2048];
  snprintf(buffer, sizeof(buffer), "%s:%d:", fname, line);
  buffer[sizeof(buffer) - 1] = 0;
  Python::PrintStackTrace();
  Log(std::string(buffer) + " error: " + msg);
}

void MacroLogError(const std::string& msg, const char* fname, int line) {
  char e_buffer[2048];
  snprintf(e_buffer, sizeof(e_buffer), "%s:%d:", fname, line);
  e_buffer[sizeof(e_buffer) - 1] = 0;
  ballistica::Log(std::string(e_buffer) + " error: " + msg);
}

void MacroLogPythonTrace(const std::string& msg) {
  Python::PrintStackTrace();
  Log(msg);
}

}  // namespace ballistica
