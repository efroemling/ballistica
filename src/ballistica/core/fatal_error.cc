// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/fatal_error.h"

#include "ballistica/app/app_flavor.h"
#include "ballistica/core/logging.h"
#include "ballistica/core/thread.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/platform/platform.h"

namespace ballistica {
auto FatalError::ReportFatalError(const std::string& message,
                                  bool in_top_level_exception_handler) -> void {
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

  // Give the platform the opportunity to completely override our handling.
  if (g_platform) {
    auto handled =
        g_platform->ReportFatalError(message, in_top_level_exception_handler);
    if (handled) {
      return;
    }
  }

  std::string dialog_msg = message;
  if (!dialog_msg.empty()) {
    dialog_msg += "\n";
  }

  auto starttime = time(nullptr);

  // Launch a thread and give it a chance to directly send our logs to the
  // master-server. The standard mechanism probably won't get the job done
  // since it relies on the logic thread loop and we're likely blocking that.
  // But generally we want to stay in this function and call abort() or whatnot
  // from here so that our stack trace makes it into platform logs.
  int result{};

  std::string logmsg =
      std::string("FATAL ERROR:") + (!message.empty() ? " " : "") + message;

  // Try to include a stack trace if we're being called from outside of a
  // top-level exception handler. Otherwise the trace isn't really useful
  // since we know where those are anyway.
  if (!in_top_level_exception_handler) {
    if (g_platform) {
      PlatformStackTrace* trace{g_platform->GetStackTrace()};
      if (trace) {
        std::string tracestr = trace->GetDescription();
        if (!tracestr.empty()) {
          logmsg += ("\nSTACK-TRACE-BEGIN:\n" + tracestr + "\nSTACK-TRACE-END");
        }
        delete trace;
      }
    }
  }

  // Prevent the early-log insta-send mechanism from firing since we do
  // basically the same thing ourself here (avoid sending the same logs twice).
  g_early_log_writes = 0;

  Logging::Log(logmsg);

  std::string prefix = "FATAL-ERROR-LOG:";
  std::string suffix;

  // If we have no globals yet, include this message explicitly
  // since it won't be part of the standard log.
  if (g_app == nullptr) {
    suffix = logmsg;
  }
  g_app_internal->DirectSendLogs(prefix, suffix, true, &result);

  // If we're able to show a fatal-error dialog synchronously, do so.
  if (g_platform && g_platform->CanShowBlockingFatalErrorDialog()) {
    DoBlockingFatalErrorDialog(dialog_msg);
  }

  // Wait until the log submit has finished or a bit of time has passed..
  while (time(nullptr) - starttime < 10) {
    if (result != 0) {
      break;
    }
    Platform::SleepMS(100);
  }
}

auto FatalError::DoBlockingFatalErrorDialog(const std::string& message)
    -> void {
  // If we're in the main thread; just fire off the dialog directly.
  // Otherwise tell the main thread to do it and wait around until it's done.
  if (InMainThread()) {
    g_platform->BlockingFatalErrorDialog(message);
  } else {
    bool started{};
    bool finished{};
    bool* startedptr{&started};
    bool* finishedptr{&finished};
    g_app_flavor->thread()->PushCall([message, startedptr, finishedptr] {
      *startedptr = true;
      g_platform->BlockingFatalErrorDialog(message);
      *finishedptr = true;
    });

    // Wait a short amount of time for the main thread to take action.
    // There's a chance that it can't (if threads are paused, if it is
    // blocked on a synchronous call to another thread, etc.) so if we don't
    // see something happening soon, just give up on showing a dialog.
    auto starttime = Platform::GetCurrentMilliseconds();
    while (!started) {
      if (Platform::GetCurrentMilliseconds() - starttime > 1000) {
        return;
      }
      Platform::SleepMS(10);
    }
    while (!finished) {
      Platform::SleepMS(10);
    }
  }
}

auto FatalError::HandleFatalError(bool exit_cleanly,
                                  bool in_top_level_exception_handler) -> bool {
  // Give the platform the opportunity to completely override our handling.
  if (g_platform) {
    auto handled = g_platform->HandleFatalError(exit_cleanly,
                                                in_top_level_exception_handler);
    if (handled) {
      return true;
    }
  }

  // If we're not being called as part of a top-level exception handler,
  // bring the app down ourself.
  if (!in_top_level_exception_handler) {
    if (exit_cleanly) {
      Log("Calling exit(1)...");
      exit(1);
    } else {
      Log("Calling abort()...");
      abort();
    }
  }

  // Otherwise its up to who called us
  // (they might let the caught exception bubble up)
  return false;
}

}  // namespace ballistica
