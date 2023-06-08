// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/fatal_error.h"

#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/logging.h"

namespace ballistica {

// Note: implicitly using core's internal globals here, so our behavior is
// undefined if core has not been imported by *someone*.
using core::g_base_soft;
using core::g_core;

void FatalError::ReportFatalError(const std::string& message,
                                  bool in_top_level_exception_handler) {
  // We want to report the first fatal error that happens; if further ones
  // happen they are probably red herrings.
  static bool ran = false;
  if (ran) {
    return;
  }
  ran = true;

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
      core::PlatformStackTrace* trace{g_core->platform->GetStackTrace()};
      if (trace) {
        std::string tracestr = trace->GetDescription();
        if (!tracestr.empty()) {
          logmsg += ("\nCPP-STACK-TRACE-BEGIN:\n" + tracestr
                     + "\nCPP-STACK-TRACE-END");
        }
        delete trace;
      } else {
        logmsg += "\n(CPP-STACK-TRACE-UNAVAILABLE)";
      }
    }
  }

  // Prevent the early-v1-cloud-log insta-send mechanism from firing since
  // we do basically the same thing ourself here (avoid sending the same
  // logs twice).
  g_early_v1_cloud_log_writes = 0;

  // Add this to our V1CloudLog which we'll be attempting to send
  // momentarily, and also go to platform-specific logging and good ol'
  // stderr.
  Logging::V1CloudLog(logmsg);
  Logging::DisplayLog("root", LogLevel::kCritical, logmsg);
  fprintf(stderr, "%s\n", logmsg.c_str());

  std::string prefix = "FATAL-ERROR-LOG:";
  std::string suffix;

  // If we have no core state yet, include this message explicitly
  // since it won't be part of the standard log.
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

  // Wait until the log submit has finished or a bit of time has passed..
  while (time(nullptr) - starttime < 10) {
    if (result != 0) {
      break;
    }
    core::CorePlatform::SleepMillisecs(100);
  }
}

void FatalError::DoBlockingFatalErrorDialog(const std::string& message) {
  // We should not get here without this intact.
  assert(g_core);
  // If we're in the main thread; just fire off the dialog directly.
  // Otherwise tell the main thread to do it and wait around until it's
  // done.
  if (g_core->InMainThread()) {
    g_core->platform->BlockingFatalErrorDialog(message);
  } else {
    bool started{};
    bool finished{};
    bool* startedptr{&started};
    bool* finishedptr{&finished};
    g_core->main_event_loop()->PushCall([message, startedptr, finishedptr] {
      *startedptr = true;
      g_core->platform->BlockingFatalErrorDialog(message);
      *finishedptr = true;
    });

    // Wait a short amount of time for the main thread to take action.
    // There's a chance that it can't (if threads are paused, if it is
    // blocked on a synchronous call to another thread, etc.) so if we don't
    // see something happening soon, just give up on showing a dialog.
    auto starttime = core::CorePlatform::GetCurrentMillisecs();
    while (!started) {
      if (core::CorePlatform::GetCurrentMillisecs() - starttime > 1000) {
        return;
      }
      core::CorePlatform::SleepMillisecs(10);
    }
    while (!finished) {
      core::CorePlatform::SleepMillisecs(10);
    }
  }
}

auto FatalError::HandleFatalError(bool exit_cleanly,
                                  bool in_top_level_exception_handler) -> bool {
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
      Logging::DisplayLog("root", LogLevel::kCritical, "Calling exit(1)...");
      exit(1);
    } else {
      Logging::DisplayLog("root", LogLevel::kCritical, "Calling abort()...");
      abort();
    }
  }

  // Otherwise its up to who called us (they might let the caught exception
  // bubble up)
  return false;
}

}  // namespace ballistica
