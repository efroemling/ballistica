// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_EXCEPTION_H_
#define BALLISTICA_SHARED_FOUNDATION_EXCEPTION_H_
#ifdef __cplusplus

#include <string>

#include "ballistica/shared/ballistica.h"

namespace ballistica {

// Notes on our C++ exception handling:
//
// std::exception in broken into two subclass categories, logic_error and
// runtime_error. It is my understanding that logic_error should be used as
// a sort of non-fatal assert() for things that the program is doing
// incorrectly, while runtime_error applies to external things such as user
// input (a user entering a name containing invalid characters, etc).
//
// In practice, we currently handle both sides identically, so the
// distinction is not really important to us. We also translate C++
// exceptions to and from Python exceptions as their respective stacks
// unwind, so the distinction tends to get lost anyway.
//
// So for the time being we have a simple single ballistica::Exception type
// inheriting directly from std::exception that we use for pretty much
// anything going wrong. It contains useful tidbits such as a stack trace to
// help diagnose issues. We can expand on this or branch off into more
// particular types if/when the need arises.
//
// Note that any sites *catching* exception should catch std::exception
// (unless they have a particular need to catch a more specific type). This
// preserves our freedom to add variants under std::logic_error or
// std::runtime_error at a later time and also catches exceptions coming
// from std itself.

/// Get a short description for an exception.
///
/// By default, our Exception classes provide what() values that may include
/// backtraces of the throw location or other extended info that can be
/// useful to have printed in crash reports/etc. In some cases this extended
/// info is not desired, however, such as when converting a C++ exception to
/// a Python one (which will have its own backtrace and other context_ref).
/// This function will return the raw message only if passed one of our
/// Exceptions, and simply what() in other cases.
auto GetShortExceptionDescription(const std::exception& exc) -> const char*;

class Exception : public std::exception {
 public:
  explicit Exception(std::string message = "",
                     PyExcType python_type = PyExcType::kRuntime);
  explicit Exception(PyExcType python_type);
  Exception(const Exception& other) noexcept;
  ~Exception() override;

  /// Return the full description for this exception which may include
  /// backtraces/etc.
  auto what() const noexcept -> const char* override;

  /// Return only the raw message passed to this exception on creation.
  auto message() const noexcept -> const char* { return message_.c_str(); }

  void SetPyError() const noexcept;

  auto python_type() const { return python_type_; }

 private:
  std::string thread_name_;
  std::string message_;
  std::string full_description_;
  PyExcType python_type_;
  NativeStackTrace* stack_trace_{};
};

}  // namespace ballistica

#endif  // __cplusplus
#endif  // BALLISTICA_SHARED_FOUNDATION_EXCEPTION_H_
