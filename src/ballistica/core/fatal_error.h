// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_FATAL_ERROR_H_
#define BALLISTICA_CORE_FATAL_ERROR_H_

#include <string>

namespace ballistica {

class FatalError {
 public:
  /// Report a fatal error to the master-server/user/etc. Note that reporting
  /// only happens for the first invocation of this call; additional calls
  /// are no-ops.
  static auto ReportFatalError(const std::string& message,
                               bool in_top_level_exception_handler) -> void;

  /// Handle a fatal error. This can involve calling exit(), abort(), setting
  /// up an asynchronous quit, etc. Returns true if the fatal-error has been
  /// handled; otherwise it is up to the caller (this should only be the case
  /// when in_top_level_exception_handler is true).
  /// Unlike ReportFatalError, the logic in this call can be invoked repeatedly
  /// and should be prepared for that possibility in the case of recursive
  /// fatal errors/etc.
  static auto HandleFatalError(bool clean_exit,
                               bool in_top_level_exception_handler) -> bool;

 private:
  static auto DoBlockingFatalErrorDialog(const std::string& message) -> void;
};

}  // namespace ballistica
#endif  // BALLISTICA_CORE_FATAL_ERROR_H_
