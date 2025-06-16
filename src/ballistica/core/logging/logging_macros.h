// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_LOGGING_LOGGING_MACROS_H_
#define BALLISTICA_CORE_LOGGING_LOGGING_MACROS_H_

// Compiler claims these are unused but they are indeed used in these
// macros.

#include "ballistica/core/core.h"             // IWYU pragma: keep.
#include "ballistica/core/logging/logging.h"  // IWYU pragma: keep.

// Call this for errors which are non-fatal but should be noted so they can
// be fixed.
#define BA_LOG_ERROR_NATIVE_TRACE(msg) \
  ::ballistica::MacroLogErrorNativeTrace(g_core, msg, __FILE__, __LINE__)

#define BA_LOG_ERROR_NATIVE_TRACE_ONCE(msg)                                    \
  {                                                                            \
    static bool did_log_error_trace_here = false;                              \
    if (!did_log_error_trace_here) {                                           \
      ::ballistica::MacroLogErrorNativeTrace(g_core, msg, __FILE__, __LINE__); \
      did_log_error_trace_here = true;                                         \
    }                                                                          \
  }                                                                            \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

// Call this for errors which are non-fatal but should be noted so they can
// be fixed.
#define BA_LOG_ERROR_PYTHON_TRACE(msg) \
  ::ballistica::MacroLogErrorPythonTrace(g_core, msg, __FILE__, __LINE__)

#define BA_LOG_ERROR_PYTHON_TRACE_ONCE(msg)                                    \
  {                                                                            \
    static bool did_log_error_trace_here = false;                              \
    if (!did_log_error_trace_here) {                                           \
      ::ballistica::MacroLogErrorPythonTrace(g_core, msg, __FILE__, __LINE__); \
      did_log_error_trace_here = true;                                         \
    }                                                                          \
  }                                                                            \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#define BA_LOG_ONCE(nm, lvl, msg)         \
  {                                       \
    static bool did_log_here{};           \
    if (!did_log_here) {                  \
      g_core->logging->Log(nm, lvl, msg); \
      did_log_here = true;                \
    }                                     \
  }                                       \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#define BA_LOG_PYTHON_TRACE(msg) ::ballistica::MacroLogPythonTrace(g_core, msg)

#define BA_LOG_PYTHON_TRACE_ONCE(msg)                 \
  {                                                   \
    static bool did_log_python_trace_here = false;    \
    if (!did_log_python_trace_here) {                 \
      ::ballistica::MacroLogPythonTrace(g_core, msg); \
      did_log_python_trace_here = true;               \
    }                                                 \
  }                                                   \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#endif  // BALLISTICA_CORE_LOGGING_LOGGING_MACROS_H_
