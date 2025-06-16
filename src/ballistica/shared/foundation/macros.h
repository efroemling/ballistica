// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_MACROS_H_
#define BALLISTICA_SHARED_FOUNDATION_MACROS_H_

#ifdef __cplusplus
#include <string>
#endif

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/exception.h"  // IWYU pragma: keep.

// Various utility macros and related support calls.
// Trying to contain the evil to this one place.

// Trailing-semicolon note:
// Some macros contain a ((void*) at the end. This is so the macro can be
// followed by a semicolon without triggering an 'empty statement' warning.
// I find standalone function-style macro invocations without semicolons
// tend to confuse code formatters.

#define BA_STRINGIFY(x) #x
// Looks redundant at first but strangely necessary.
// See https://www.decompile.com/cpp/faq/file_and_line_error_string.htm
#define BA_TOSTRING(x) BA_STRINGIFY(x)

#define BA_BUILD_COMMAND_FILENAME \
  "<string: " __FILE__ " line " BA_TOSTRING(__LINE__) ">"

#if BA_PLATFORM_WINDOWS
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
  millisecs_t _dfts = ::ballistica::MacroFunctionTimerStartTime()
#define BA_DEBUG_FUNCTION_TIMER_END(time) \
  ::ballistica::MacroFunctionTimerEnd(g_core, _dfts, time, __PRETTY_FUNCTION__)
#define BA_DEBUG_FUNCTION_TIMER_END_THREAD(time)                 \
  ::ballistica::MacroFunctionTimerEndThread(g_core, _dfts, time, \
                                            __PRETTY_FUNCTION__)
#define BA_DEBUG_FUNCTION_TIMER_END_EX(time, what) \
  MacroFunctionTimerEndEx(g_core, _dfts, time, __PRETTY_FUNCTION__, what)
#define BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(time, what)          \
  ::ballistica::MacroFunctionTimerEndThreadEx(g_core, _dfts, time, \
                                              __PRETTY_FUNCTION__, what)
#define BA_DEBUG_TIME_CHECK_BEGIN(name) \
  millisecs_t name##_ts = ::ballistica::MacroFunctionTimerStartTime()
#define BA_DEBUG_TIME_CHECK_END(name, time)                                 \
  ::ballistica::MacroTimeCheckEnd(g_core, name##_ts, time, #name, __FILE__, \
                                  __LINE__)
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

/// Test a condition and throw an exception if it fails (on both debug and
/// release builds)
#define BA_PRECONDITION(b)                                                \
  {                                                                       \
    if (!(b)) {                                                           \
      throw ::ballistica::Exception(std::string("Precondition failed @ ") \
                                    + cxpr_base_name(__FILE__)            \
                                    + ":" BA_TOSTRING(__LINE__) ": " #b); \
    }                                                                     \
  }                                                                       \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

/// Test a condition and simply print a log message if it fails (on both debug
/// and release builds)
#define BA_PRECONDITION_LOG(b)                                        \
  {                                                                   \
    if (!(b)) {                                                       \
      Log(LogLevel::kError, std::string("Precondition failed @ ")     \
                                + cxpr_base_name(__FILE__)            \
                                + ":" BA_TOSTRING(__LINE__) ": " #b); \
    }                                                                 \
  }                                                                   \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

/// Test a condition and abort the program if it fails (on both debug
/// and release builds)
#define BA_PRECONDITION_FATAL(b)                       \
  {                                                    \
    if (!(b)) {                                        \
      FatalError(std::string("Precondition failed @ ") \
                 + cxpr_base_name(__FILE__)            \
                 + ":" BA_TOSTRING(__LINE__) ": " #b); \
    }                                                  \
  }                                                    \
  ((void)0)  // (see 'Trailing-semicolon note' at top)

#ifdef __cplusplus

namespace ballistica::core {
class CoreFeatureSet;
}

namespace ballistica {

// Support functions used by some of our macros; not intended to be used
// directly.
auto MacroPathFilter(core::CoreFeatureSet* corefs, const char* filename)
    -> const char*;
auto MacroFunctionTimerStartTime() -> millisecs_t;
void MacroFunctionTimerEnd(core::CoreFeatureSet* corefs, millisecs_t starttime,
                           millisecs_t time, const char* funcname);
void MacroFunctionTimerEndThread(core::CoreFeatureSet* corefs,
                                 millisecs_t starttime, millisecs_t time,
                                 const char* funcname);
void MacroFunctionTimerEndEx(core::CoreFeatureSet* corefs,
                             millisecs_t starttime, millisecs_t time,
                             const char* funcname, const std::string& what);
void MacroFunctionTimerEndThreadEx(core::CoreFeatureSet* corefs,
                                   millisecs_t starttime, millisecs_t time,
                                   const char* funcname,
                                   const std::string& what);
void MacroTimeCheckEnd(core::CoreFeatureSet* corefs, millisecs_t starttime,
                       millisecs_t time, const char* name, const char* file,
                       int line);
void MacroLogErrorNativeTrace(core::CoreFeatureSet* corefs,
                              const std::string& msg, const char* fname,
                              int line);
void MacroLogErrorPythonTrace(core::CoreFeatureSet* corefs,
                              const std::string& msg, const char* fname,
                              int line);
void MacroLogError(core::CoreFeatureSet* corefs, const std::string& msg,
                   const char* fname, int line);
void MacroLogPythonTrace(core::CoreFeatureSet* corefs, const std::string& msg);

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_SHARED_FOUNDATION_MACROS_H_
