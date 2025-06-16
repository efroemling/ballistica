// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_H_
#define BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_H_

#include <string>

namespace ballistica {

class FatalErrorHandling {
 public:
  /// Complete high level level fatal error call; does both reporting and
  /// handling. ballistica::FatalError() simply calls this.
  static void DoFatalError(const std::string& message);

  /// Report a fatal error to the master-server/user/etc. Note that
  /// reporting only happens for the first invocation of this call;
  /// additional calls are no-ops. This is because the process of tearing
  /// down the app may trigger additional errors which are likely red
  /// herrings.
  static void ReportFatalError(const std::string& message,
                               bool in_top_level_exception_handler);

  /// Handle a fatal error. This can involve calling exit(), abort(),
  /// setting up an asynchronous quit, etc. Returns true if the fatal-error
  /// has been handled; otherwise it is up to the caller (this should only
  /// be the case when in_top_level_exception_handler is true).
  ///
  /// Unlike ReportFatalError, the logic in this call can be invoked
  /// repeatedly and should be prepared for that possibility in the case of
  /// recursive fatal errors/etc.
  static auto HandleFatalError(bool clean_exit,
                               bool in_top_level_exception_handler) -> bool;

 private:
  static void DoBlockingFatalErrorDialog(const std::string& message);
  static bool reported_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_H_
