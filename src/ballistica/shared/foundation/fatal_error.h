// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_H_
#define BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_H_

#include <atomic>
#include <ctime>
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

  /// Report a shutdown that could not complete cleanly, then exit.
  ///
  /// For when the app is not dying of an error but still can't shut
  /// down cleanly (a thread that won't stop, for instance) and must get
  /// out without finalizing. The report goes out like a fatal error's --
  /// live, or saved for the next launch if that fails -- with the
  /// message prefixed ``UNCLEAN-SHUTDOWN:``, but no dialog is shown.
  /// Then, like fatal errors, unmodified blessed builds abort() (so the
  /// platform files a crash report, which on most platforms includes
  /// every thread's stack -- the stuck thread's included) and other
  /// builds exit with code 1. Exits via _Exit()/abort() rather than
  /// exit() since other threads may still be running. Never returns.
  [[noreturn]] static void DoUncleanShutdown(const std::string& message);

 private:
  static void DoBlockingFatalErrorDialog(const std::string& message);

  /// Wait (up to wait_seconds after start_time) for a report started
  /// with SendFatalErrorReport() to finish; if it did not succeed, save
  /// it for the next launch to send.
  static void FinishReportOrSaveForLater_(const std::atomic<int>& result,
                                          time_t start_time, int wait_seconds,
                                          const std::string& message,
                                          const std::string& stack_trace);
  static bool reported_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_H_
