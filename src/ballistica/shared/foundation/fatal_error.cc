// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/fatal_error.h"

#include <cstdio>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/generic/lambda_runnable.h"
#include "ballistica/shared/generic/native_stack_trace.h"
#include "ballistica/shared/python/python.h"

namespace ballistica {

// Note: implicitly using core's internal globals here, but we should try to
// behave reasonably if they're not inited since fatal errors can happen any
// time.
using core::g_base_soft;
using core::g_core;

bool FatalErrorHandling::reported_{};

void FatalErrorHandling::DoFatalError(const std::string& message) {
  // Let the user and/or master-server know we're dying.
  ReportFatalError(message, false);

  // In some cases we prefer to cleanly exit the app with an error code in a
  // way that won't wind up as a crash report; this avoids polluting our
  // crash reports list with stuff from dev builds.
  bool try_to_exit_cleanly =
      !(core::g_base_soft && core::g_base_soft->IsUnmodifiedBlessedBuild());
  bool handled = HandleFatalError(try_to_exit_cleanly, false);
  if (!handled) {
    abort();
  }
}

void FatalErrorHandling::ReportFatalError(const std::string& message,
                                          bool in_top_level_exception_handler) {
  // We want to report only the first fatal error that happens; if further
  // ones happen they are likely red herrings triggered by the first.
  if (reported_) {
    return;
  }
  reported_ = true;

  // Our main goal here varies based off whether we are an unmodified
  // blessed build. If we are, our main goal is to communicate as much info
  // about the error to the master server, and communicating to the user is
  // a stretch goal.

  // If we are unblessed or modified, the main goals are communicating the
  // error to the user and exiting the app cleanly (so we don't pollute our
  // crash records with results of user tinkering).

  // Special case: if we've got a debugger attached we simply abort()
  // immediately in order to get the debugger's attention.
  if (g_core && g_core->core_config().debugger_attached) {
    if (!message.empty()) {
      printf("FATAL ERROR (debugger mode): %s\n", message.c_str());
      fflush(stdout);
    }
    abort();
  }

  // Give the platform the opportunity to augment or override our handling.
  if (g_core) {
    auto handled = g_core->platform->ReportFatalError(
        message, in_top_level_exception_handler);
    if (handled) {
      return;
    }
  }

  auto starttime = time(nullptr);

  // Launch a thread and give it a chance to directly send our logs to the
  // master-server. The standard mechanism probably won't get the job done
  // since it relies on the logic thread loop and we're likely blocking
  // that. But generally we want to stay in this function and call abort()
  // or whatnot from here so that our stack trace makes it into platform
  // logs.
  int result{};

  std::string logmsg =
      std::string("FATAL ERROR:") + (!message.empty() ? " " : "") + message;

  // Try to include a stack trace if we're being called from outside of a
  // top-level exception handler. Otherwise the trace isn't really useful
  // since we know where those are anyway.
  if (!in_top_level_exception_handler) {
    if (g_core && g_core->platform) {
      NativeStackTrace* trace{g_core->platform->GetNativeStackTrace()};
      if (trace) {
        std::string tracestr = trace->FormatForDisplay();
        if (!tracestr.empty()) {
          logmsg +=
              (("\n----------------------- BALLISTICA-NATIVE-STACK-TRACE-BEGIN "
                "--------------------\n")
               + tracestr
               + ("\n----------------------- BALLISTICA-NATIVE-STACK-TRACE-END "
                  "----------------------"));
        }
        delete trace;
      } else {
        logmsg += "\n(BALLISTICA-NATIVE-STACK-TRACE-UNAVAILABLE)";
      }
    }
  }

  // Prevent the early-v1-cloud-log insta-send mechanism from firing since
  // we do basically the same thing ourself here (avoid sending the same
  // logs twice).
  core::g_early_v1_cloud_log_writes = 0;

  // Add this to our V1CloudLog which we'll be attempting to send
  // momentarily, and also go to platform-specific logging and good ol'
  // stderr.

  if (g_core) {
    g_core->logging->V1CloudLog(logmsg);
    g_core->logging->EmitLog("root", LogLevel::kCritical,
                             core::CorePlatform::TimeSinceEpochSeconds(),
                             logmsg);
  }

  fprintf(stderr, "%s\n", logmsg.c_str());
  std::string prefix = "FATAL-ERROR-LOG:";
  std::string suffix;

  // If we have no core state yet, include this message explicitly since it
  // won't be part of the standard log.
  if (g_core == nullptr) {
    suffix = logmsg;
  }

  if (g_base_soft) {
    g_base_soft->PlusDirectSendV1CloudLogs(prefix, suffix, true, &result);
  }

  // If we're able to show a fatal-error dialog synchronously, do so.
  if (g_core && g_core->platform
      && g_core->platform->CanShowBlockingFatalErrorDialog()) {
    DoBlockingFatalErrorDialog(message);
  }

  // Wait until the log submit has finished or a bit of time has passed.
  while (time(nullptr) - starttime < 10) {
    if (result != 0) {
      break;
    }
    core::CorePlatform::SleepMillisecs(100);
  }
}

void FatalErrorHandling::DoBlockingFatalErrorDialog(
    const std::string& message) {
  // Should not be possible to get here without this intact.
  assert(g_core);
  // If we're in the main thread; just fire off the dialog directly.
  // Otherwise tell the main thread to do it and wait around until it's
  // done.
  if (g_core->InMainThread()) {
    g_core->platform->BlockingFatalErrorDialog(message);
  } else if (g_base_soft) {
    bool started{};
    bool finished{};
    bool* startedptr{&started};
    bool* finishedptr{&finished};

    // If our thread is holding the GIL, release it while we spin; otherwise
    // we can wind up in deadlock if the main thread wants it.
    Python::ScopedInterpreterLockRelease gil_release;

    g_base_soft->PushMainThreadRunnable(
        NewLambdaRunnableUnmanaged([message, startedptr, finishedptr] {
          *startedptr = true;
          g_core->platform->BlockingFatalErrorDialog(message);
          *finishedptr = true;
        }));

    // Wait a short amount of time for the main thread to take action.
    // There's a chance that it can't (if threads are suspended, if it is
    // blocked on a synchronous call to another thread, etc.) so if we don't
    // see something happening soon, just give up on showing a dialog.
    auto starttime = core::CorePlatform::TimeMonotonicMillisecs();
    while (!started) {
      if (core::CorePlatform::TimeMonotonicMillisecs() - starttime > 3000) {
        return;
      }
      core::CorePlatform::SleepMillisecs(10);
    }
    while (!finished) {
      core::CorePlatform::SleepMillisecs(10);
    }
  }
}

auto FatalErrorHandling::HandleFatalError(bool exit_cleanly,
                                          bool in_top_level_exception_handler)
    -> bool {
  // Give the platform the opportunity to completely override our handling.
  if (g_core) {
    auto handled = g_core->platform->HandleFatalError(
        exit_cleanly, in_top_level_exception_handler);
    if (handled) {
      return true;
    }
  }

  // If we're not being called as part of a top-level exception handler,
  // bring the app down ourself.
  if (!in_top_level_exception_handler) {
    if (exit_cleanly) {
      if (g_core) {
        g_core->logging->EmitLog("root", LogLevel::kCritical,
                                 core::CorePlatform::TimeSinceEpochSeconds(),
                                 "Calling exit(1)...");

        // Inform anyone who cares that the engine is going down NOW.
        // This value can be polled by threads that may otherwise block us
        // from exiting cleanly. As an example, I've seen recent linux builds
        // hang on exit because a bg thread is blocked in a read of stdin.
        g_core->set_engine_done();
      }

      // Note: We DO NOT call FinalizePython() in this case; we're already
      // going down in flames so that might just make things worse.

      exit(1);
    } else {
      if (g_core) {
        g_core->logging->EmitLog("root", LogLevel::kCritical,
                                 core::CorePlatform::TimeSinceEpochSeconds(),
                                 "Calling abort()...");
      }
      abort();
    }
  }

  // Otherwise its up to who called us (they might let the caught exception
  // bubble up).
  return false;
}

}  // namespace ballistica
