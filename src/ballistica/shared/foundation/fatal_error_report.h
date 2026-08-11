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

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_FATAL_ERROR_REPORT_H_
