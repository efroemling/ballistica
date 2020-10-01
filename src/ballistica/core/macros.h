// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_MACROS_H_
#define BALLISTICA_CORE_MACROS_H_

#ifdef __cplusplus
#include <cassert>
#include <string>
#endif

#include "ballistica/core/types.h"

// Various utility macros and related support calls.
// Trying to contain the evil in this one place.

// Trailing-semicolon note:
// Some macros contain a ((void*) at the end. This is so the macro can be
// followed by a semicolon without triggering an 'empty statement' warning.
// I find standalone function-style macro invocations without semicolons
// tends to confuse code formatters.

#define BA_STRINGIFY(x) #x

#define BA_BUILD_COMMAND_FILENAME \
  "<string: " __FILE__ " line " BA_STRINGIFY(__LINE__) ">"
#define BA_BCFN BA_BUILD_COMMAND_FILENAME

#if BA_OSTYPE_WINDOWS
#define BA_DIRSLASH "\\"
#else
#define BA_DIRSLASH "/"
#endif

#if BA_DEBUG_BUILD
#define BA_IFDEBUG(a) a
#else
#define BA_IFDEBUG(a) ((void)0)
#endif

// Useful for finding hitches.
// Call begin, followed at some point by any of the end versions.
// FIXME: Turn these into C++ classes.
#if BA_DEBUG_BUILD
#define BA_DEBUG_FUNCTION_TIMER_BEGIN() \
  millisecs_t _dfts = g_platform->GetTicks()
#define BA_DEBUG_FUNCTION_TIMER_END(time) \
  ballistica::MacroFunctionTimerEnd(_dfts, time, __PRETTY_FUNCTION__)
#define BA_DEBUG_FUNCTION_TIMER_END_THREAD(time) \
  ballistica::MacroFunctionTimerEndThread(_dfts, time, __PRETTY_FUNCTION__)
#define BA_DEBUG_FUNCTION_TIMER_END_EX(time, what) \
  MacroFunctionTimerEndEx(_dfts, time, __PRETTY_FUNCTION__, what)
#define BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(time, what)                     \
  ballistica::MacroFunctionTimerEndThreadEx(_dfts, time, __PRETTY_FUNCTION__, \
                                            what)
#define BA_DEBUG_TIME_CHECK_BEGIN(name) \
  millisecs_t name##_ts = g_platform->GetTicks()
#define BA_DEBUG_TIME_CHECK_END(name, time) \
  ballistica::MacroTimeCheckEnd(name##_ts, time, #name, __FILE__, __LINE__)
#else
#define BA_DEBUG_FUNCTION_TIMER_BEGIN() ((void)0)
#define BA_DEBUG_FUNCTION_TIMER_END(time) ((void)0)
#define BA_DEBUG_FUNCTION_TIMER_END_THREAD(time) ((void)0)
#define BA_DEBUG_FUNCTION_TIMER_END_EX(time, what) ((void)0)
#define BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(time, what) ((void)0)
#define BA_DEBUG_TIME_CHECK_BEGIN(name) ((void)0)
#define BA_DEBUG_TIME_CHECK_END(name, time) ((void)0)
#endif

// Disallow copying for a class.
#define BA_DISALLOW_CLASS_COPIES(type) \
  type(const type& foo) = delete;      \
  type& operator=(const type& src) = delete; /* NOLINT (macro parens) */

// Call this for errors which are non-fatal but should be noted so they can be
// fixed.
#define BA_LOG_ERROR_TRACE(msg) \
  ballistica::MacroLogErrorTrace(msg, __FILE__, __LINE__)

#define BA_LOG_ERROR_TRACE_ONCE(msg)                           \
  {                                                            \
    static bool did_log_error_trace_here = false;              \
    if (!did_log_error_trace_here) {                           \
      ballistica::MacroLogErrorTrace(msg, __FILE__, __LINE__); \
      did_log_error_trace_here = true;                         \
    }                                                          \
  }                                                            \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#define BA_LOG_ONCE(msg)              \
  {                                   \
    static bool did_log_here = false; \
    if (!did_log_here) {              \
      ballistica::Log(msg);           \
      did_log_here = true;            \
    }                                 \
  }                                   \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#define BA_LOG_PYTHON_TRACE(msg) ballistica::MacroLogPythonTrace(msg)

#define BA_LOG_PYTHON_TRACE_ONCE(msg)              \
  {                                                \
    static bool did_log_python_trace_here = false; \
    if (!did_log_python_trace_here) {              \
      ballistica::MacroLogPythonTrace(msg);        \
      did_log_python_trace_here = true;            \
    }                                              \
  }                                                \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

/// Test a condition and throw an exception if it fails (on both debug and
/// release builds)
#define BA_PRECONDITION(b)                                     \
  {                                                            \
    if (!(b)) {                                                \
      throw ballistica::Exception("Precondition failed: " #b); \
    }                                                          \
  }                                                            \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

/// Test a condition and simply print a log message if it fails (on both debug
/// and release builds)
#define BA_PRECONDITION_LOG(b)         \
  {                                    \
    if (!(b)) {                        \
      Log("Precondition failed: " #b); \
    }                                  \
  }                                    \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

/// Test a condition and abort the program if it fails (on both debug
/// and release builds)
#define BA_PRECONDITION_FATAL(b)              \
  {                                           \
    if (!(b)) {                               \
      FatalError("Precondition failed: " #b); \
    }                                         \
  }                                           \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#ifdef __cplusplus

namespace ballistica {

// Support functions used by some of our macros; not intended to be used
// directly.
void MacroFunctionTimerEnd(millisecs_t starttime, millisecs_t time,
                           const char* funcname);
void MacroFunctionTimerEndThread(millisecs_t starttime, millisecs_t time,
                                 const char* funcname);
void MacroFunctionTimerEndEx(millisecs_t starttime, millisecs_t time,
                             const char* funcname, const std::string& what);
void MacroFunctionTimerEndThreadEx(millisecs_t starttime, millisecs_t time,
                                   const char* funcname,
                                   const std::string& what);
void MacroTimeCheckEnd(millisecs_t starttime, millisecs_t time,
                       const char* name, const char* file, int line);
void MacroLogErrorTrace(const std::string& msg, const char* fname, int line);
void MacroLogError(const std::string& msg, const char* fname, int line);
void MacroLogPythonTrace(const std::string& msg);

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_CORE_MACROS_H_
