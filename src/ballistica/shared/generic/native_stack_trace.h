// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_NATIVE_STACK_TRACE_H_
#define BALLISTICA_SHARED_GENERIC_NATIVE_STACK_TRACE_H_

#include <string>

namespace ballistica {

/// For capturing and printing stack-traces and related errors. Platforms
/// should subclass this and return instances in GetNativeStackTrace(). Stack
/// trace classes should capture the stack state immediately upon
/// construction but should do the bare minimum amount of work to store it.
/// Any expensive operations such as symbolification should be deferred
/// until FormatForDisplay().
class NativeStackTrace {
 public:
  virtual ~NativeStackTrace() = default;

  // Return a human readable version of the trace (with symbolification if
  // available).
  virtual auto FormatForDisplay() noexcept -> std::string = 0;

  // Should return a copy of itself allocated via new() (or nullptr if not
  // possible).
  virtual auto Copy() const noexcept -> NativeStackTrace* = 0;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_NATIVE_STACK_TRACE_H_
