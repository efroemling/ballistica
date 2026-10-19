// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_REPORT_H_
#define BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_REPORT_H_

#include <atomic>
#include <string>

namespace ballistica {

/// Fire off a one-shot fatal-error report to the master-server.
///
/// This is deliberately the lowest-level reporting path we have. It runs
/// with whatever state happens to be intact -- it must stay functional
/// when g_core is null (BA_CRASH_TEST=1 fires before core is even
/// imported) and when the Python layer never came up at all. Everything
/// it sends is either passed in or a compile-time constant, with
/// g_core-derived extras added only opportunistically.
///
/// Note that this intentionally does NOT send logs. Log history is the
/// Python logging layer's job; at fatal-error time we cannot know that
/// touching that state is safe, so we send only what is immediately at
/// hand: the message and a stack trace.
///
/// Spawns a detached thread and returns immediately. `result` (if
/// non-null) is set to 1 on success or -1 on failure, so the caller can
/// spin-wait on it briefly before aborting. It is atomic since the spawned
/// thread writes it while the caller polls it.
void SendFatalErrorReport(const std::string& message,
                          const std::string& stack_trace,
                          std::atomic<int>* result);

/// Submit any crash record left behind by a previous run, then remove
/// it.
///
/// A native crash cannot report itself: the process is dying and its
/// state is untrusted, so the handler only writes a record. This picks
/// that record up on the next launch and sends it through the same
/// reporting path a fatal error uses, in the same payload shape --
/// with the *recorded* build/variant/renderer values, not this
/// process's, since the two can differ if the user updated in between.
///
/// Safe to call when no record exists (the common case); does nothing
/// and returns. Sending is fire-and-forget on a detached thread, so
/// this does not hold up startup.
void SubmitPendingCrashReport();

/// Tell the fatal-error reporter where deferred reports live.
///
/// Called once, as soon as the app's config dir is known. Stored in
/// plain static storage so a dying process never has to call into core
/// or platform code to find it. Until this is called (a fatal error very
/// early in startup) nothing can be deferred.
void SetPendingFatalReportDir(const std::string& dir);

/// Save a fatal-error report that could not be delivered live.
///
/// Called by the fatal-error handler when the live send failed or had
/// not finished by the time the process must go down -- most often
/// because the network was not reachable yet (a fatal error right after
/// the app resumes from the background, for example). Writes the
/// report, message prefixed ``DEFERRED:``, for SubmitPendingFatalReports
/// to send on the next launch. Best-effort and never throws; a no-op if
/// no pending-report dir has been set.
void SavePendingFatalReport(const std::string& message,
                            const std::string& stack_trace);

/// Send the newest deferred fatal-error report left by a previous run.
///
/// Same lifecycle as native crash records: the newest report wins,
/// every pending report is deleted *before* sending (so a crash-looping
/// app can't report the same failure forever), and a failed send is not
/// retried. Logs a line about it locally too -- at WARNING in developer
/// builds, so it shows up in test and automation output. Sending is
/// fire-and-forget on a detached thread.
void SubmitPendingFatalReports();

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_REPORT_H_
