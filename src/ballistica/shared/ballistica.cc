// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/ballistica.h"

#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/fatal_error.h"
#include "ballistica/shared/foundation/logging.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"

// Make sure min_sdl.h stays in here even though this file compile fine
// without it. On some platforms it does a bit of magic to redefine main as
// SDL_main which leads us to a tricky-to-diagnose linker error if it
// removed from here.
#ifndef BALLISTICA_CORE_PLATFORM_SUPPORT_MIN_SDL_H_
#error Please include min_sdl.h here.
#endif

// If desired, define main() in the global namespace.
#if BA_DEFINE_MAIN
auto main(int argc, char** argv) -> int {
  auto core_config =
      ballistica::core::CoreConfig::FromCommandLineAndEnv(argc, argv);

  // Arg-parsing may have yielded an error or printed simple output for
  // things such as '--help', in which case we're done.
  if (core_config.immediate_return_code.has_value()) {
    return *core_config.immediate_return_code;
  }
  return ballistica::MonolithicMain(core_config);
}
#endif

namespace ballistica {

// These are set automatically via script; don't modify them here.
const int kEngineBuildNumber = 21171;
const char* kEngineVersion = "1.7.23";

auto MonolithicMain(const core::CoreConfig& core_config) -> int {
  // This code is meant to be run standalone so won't inherit any
  // feature-set's globals; we'll need to collect anything we need
  // explicitly.
  core::CoreFeatureSet* l_core{};
  core::BaseSoftInterface* l_base{};

  try {
    // Even at the absolute start of execution we should be able to
    // reasonably log errors. Set env var BA_CRASH_TEST=1 to test this.
    if (const char* crashenv = getenv("BA_CRASH_TEST")) {
      if (!strcmp(crashenv, "1")) {
        FatalError("Fatal-Error-Test");
      }
    }

    // No matter what we're doing, we need the core feature set. Some
    // ballistica functionality implicitly uses core, so we should always
    // import it first thing even if we don't explicitly use it.
    l_core = core::CoreFeatureSet::Import(&core_config);

    // TEMP - bug hunting.
    l_core->platform->DebugLog("mm1");

    // If a command was passed, simply run it and exit. We want to act
    // simply as a Python interpreter in that case; we don't do any
    // environment setup (aside from the bits core does automatically such
    // as making our built in binary modules available).
    if (l_core->core_config().call_command.has_value()) {
      auto gil{Python::ScopedInterpreterLock()};
      bool success = PythonCommand(*l_core->core_config().call_command,
                                   "<ballistica app 'command' arg>")
                         .Exec(true, nullptr, nullptr);
      exit(success ? 0 : 1);
    }

    // TEMP - bug hunting.
    l_core->platform->DebugLog("mm2");

    // Ok, looks like we're doing a standard monolithic-mode app run.

    // -------------------------------------------------------------------------
    // Phase 1: "The board is set."
    // -------------------------------------------------------------------------

    // First, set up our environment using our internal paths and whatnot
    // (essentially the baenv.configure() call). This needs to be done
    // before any other ba* modules are imported since it may affect where
    // those modules get loaded from in the first place.
    l_core->python->MonolithicModeBaEnvConfigure();

    // TEMP - bug hunting.
    l_core->platform->DebugLog("mm3");

    // We need the base feature-set to run a full app but we don't have a hard
    // dependency to it. Let's see if it's available.
    l_base = l_core->SoftImportBase();
    if (!l_base) {
      FatalError("Base module unavailable; can't run app.");
    }

    // -------------------------------------------------------------------------
    // Phase 2: "The pieces are moving."
    // -------------------------------------------------------------------------

    // TEMP - bug hunting.
    l_core->platform->DebugLog("mm4");

    // Spin up all app machinery such as threads and subsystems. This gets
    // things ready to rock, but there's no actual rocking quite yet.
    l_base->StartApp();

    // -------------------------------------------------------------------------
    // Phase 3: "We come to it at last; the great battle of our time."
    // -------------------------------------------------------------------------

    // TEMP - bug hunting.
    l_core->platform->DebugLog("mm5");

    // At this point we unleash the beast and then simply process events
    // until the app exits (or we return from this function and let the
    // environment do that part).

    if (l_base->AppManagesEventLoop()) {
      // In environments where we control the event loop... do that.
      l_base->RunAppToCompletion();
    } else {
      // Under managed environments we now simply return and let the
      // environment feed us events until the app exits. However, we may
      // need to first 'prime the pump' here for our main thread event loop.
      // For instance, if our event loop is driven by frame draws, we may
      // need to manually pump events until we receive the 'create-screen'
      // message from the logic thread which gets our frame draws going.
      l_base->PrimeAppMainThreadEventPump();
    }
  } catch (const std::exception& exc) {
    std::string error_msg =
        std::string("Unhandled exception in MonolithicMain(): ") + exc.what();

    // Let the user and/or master-server know we're dying.
    FatalError::ReportFatalError(error_msg, true);

    // Exiting the app via an exception leads to crash reports on various
    // platforms. If it seems we're not on an official live build then we'd
    // rather just exit cleanly with an error code and avoid polluting crash
    // report logs with reports from dev builds.
    bool try_to_exit_cleanly = !(l_base && l_base->IsUnmodifiedBlessedBuild());

    // If this is true it means the app is handling things (showing a fatal
    // error dialog, etc.) and it's out of our hands.
    bool handled = FatalError::HandleFatalError(try_to_exit_cleanly, true);

    // Do the default thing if it's not been handled.
    if (!handled) {
      if (try_to_exit_cleanly) {
        exit(1);
      } else {
        throw;  // Crash report here we come!
      }
    }
  }

  if (l_core) {
    l_core->platform->WillExitMain(false);
    return l_core->return_value;
  }
  return -1;  // Didn't even get core; something clearly wrong.
}

void FatalError(const std::string& message) {
  // Let the user and/or master-server know we're dying.
  FatalError::ReportFatalError(message, false);

  // Exiting the app via an exception leads to crash reports on various
  // platforms. If it seems we're not on an official live build then we'd
  // rather just exit cleanly with an error code and avoid polluting crash
  // report logs with reports from dev builds.
  bool try_to_exit_cleanly =
      !(core::g_base_soft && core::g_base_soft->IsUnmodifiedBlessedBuild());
  bool handled = FatalError::HandleFatalError(try_to_exit_cleanly, false);
  if (!handled) {
    throw Exception("A fatal error occurred.");
  }
}

void Log(LogLevel level, const std::string& msg) { Logging::Log(level, msg); }

void ScreenMessage(const std::string& s, const Vector3f& color) {
  if (core::g_base_soft) {
    core::g_base_soft->ScreenMessage(s, color);
  } else {
    Log(LogLevel::kError,
        "ScreenMessage called without base feature-set loaded (will be lost): '"
            + s + "'");
  }
}

void ScreenMessage(const std::string& msg) {
  ScreenMessage(msg, {1.0f, 1.0f, 1.0f});
}

auto CurrentThreadName() -> std::string {
  // Currently just ask event-loop for this but perhaps should be talking
  // more directly to the OS/etc. to cover more cases.
  return EventLoop::CurrentThreadName();
}

}  // namespace ballistica
