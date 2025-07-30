// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/ballistica.h"

#include <string>

#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/fatal_error.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"

// Make sure min_sdl.h stays in here even though this file compiles fine
// without it. On some platforms it does a bit of magic to redefine main as
// SDL_main which leads us to a tricky-to-diagnose linker error if it
// removed from here.
#ifndef BALLISTICA_CORE_PLATFORM_SUPPORT_MIN_SDL_H_
#error Please include min_sdl.h here.
#endif

// If desired, define main() in the global namespace.
#if BA_MONOLITHIC_BUILD && BA_DEFINE_MAIN
auto main(int argc, char** argv) -> int {
  auto core_config =
      ballistica::core::CoreConfig::ForArgsAndEnvVars(argc, argv);

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
const int kEngineBuildNumber = 22467;
const char* kEngineVersion = "1.7.46";
const int kEngineApiVersion = 9;

#if BA_MONOLITHIC_BUILD

auto MonolithicMain(const core::CoreConfig& core_config) -> int {
  // This code is meant to be run standalone so won't inherit any
  // feature-set's globals; we'll need to collect anything we need
  // explicitly.
  core::CoreFeatureSet* l_core{};
  core::BaseSoftInterface* l_base{};

  try {
    auto time1 = core::CorePlatform::TimeMonotonicMillisecs();

    // Even at the absolute start of execution we should be able to
    // reasonably log errors. Set env var BA_CRASH_TEST=1 to test this.
    if (const char* crashenv = getenv("BA_CRASH_TEST")) {
      if (!strcmp(crashenv, "1")) {
        FatalError("Fatal-Error-Test");
      }
    }

    // No matter what we're doing, we need the core feature set. Some
    // Ballistica functionality implicitly uses core, so we should always
    // import it first thing even if we don't explicitly use it.
    l_core = core::CoreFeatureSet::Import(&core_config);

    auto time2 = core::CorePlatform::TimeMonotonicMillisecs();

    // If a command was passed, simply run it and exit. We want to act
    // simply as a Python interpreter in that case; we don't do any
    // environment setup (aside from the bits core does automatically such
    // as making our built-in binary modules available).
    if (l_core->core_config().call_command.has_value()) {
      auto gil{Python::ScopedInterpreterLock()};
      bool success = PythonCommand(*l_core->core_config().call_command,
                                   "<ballistica app 'command' arg>")
                         .Exec(true, nullptr, nullptr);

      // Let anyone interested know we're trying to go down NOW.
      l_core->set_engine_done();

      // Take the Python interpreter down gracefully. This will block for
      // any outstanding threads/etc.
      l_core->python->FinalizePython();

      // Laterz.
      exit(success ? 0 : 1);
    }

    // Ok, looks like we're doing a standard monolithic-mode app run.

    // -------------------------------------------------------------------------
    // Phase 1: "The board is set."
    // -------------------------------------------------------------------------

    // First, set up our environment using our internal paths and whatnot
    // (essentially the baenv.configure() call). This needs to be done
    // before any other ba* modules are imported since it may affect where
    // those modules get loaded from in the first place.
    l_core->python->MonolithicModeBaEnvConfigure();

    auto time3 = core::CorePlatform::TimeMonotonicMillisecs();

    // We need the base feature-set to run a full app but we don't have a hard
    // dependency to it. Let's see if it's available.
    l_base = l_core->SoftImportBase();
    if (!l_base) {
      FatalError("Base module unavailable; can't run app.");
    }

    auto time4 = core::CorePlatform::TimeMonotonicMillisecs();

    // -------------------------------------------------------------------------
    // Phase 2: "The pieces are moving."
    // -------------------------------------------------------------------------

    // Spin up all app machinery such as threads and subsystems. This gets
    // things ready to rock, but there's no actual rocking quite yet.
    l_base->StartApp();

    // -------------------------------------------------------------------------
    // Phase 3: "We come to it at last; the great battle of our time."
    // -------------------------------------------------------------------------

    // At this point we unleash the beast and then simply process events
    // until the app exits (or we return from this function and let the
    // environment do that part).

    // Make noise if it takes us too long to get to this point.
    auto time5 = core::CorePlatform::TimeMonotonicMillisecs();
    auto total_duration = time5 - time1;
    if (total_duration > 5000) {
      auto core_import_duration = time2 - time1;
      auto env_config_duration = time3 - time2;
      auto base_import_duration = time4 - time3;
      auto start_app_duration = time5 - time4;
      core::g_core->logging->Log(LogName::kBa, LogLevel::kWarning, [=] {
        return "MonolithicMain took too long (" + std::to_string(total_duration)
               + " ms; " + std::to_string(core_import_duration)
               + " core-import, " + std::to_string(env_config_duration)
               + " env-config, " + std::to_string(base_import_duration)
               + " base-import, " + std::to_string(start_app_duration)
               + " start-app).";
      });
    }

    if (l_base->AppManagesMainThreadEventLoop()) {
      // In environments where we control the event loop, do that.
      l_base->RunAppToCompletion();

      // Let anyone interested know we're trying to go down NOW.
      l_core->set_engine_done();

      // Take the Python interpreter down gracefully. This will block for
      // any outstanding threads/etc.
      l_core->python->FinalizePython();

    } else {
      // If the environment is managing events, we now simply return and let
      // it feed us those events.

      // IMPORTANT - We're still holding the GIL at this point, so we need
      // to permanently release it to avoid starving the app. From this
      // point on, any code outside of the logic thread will need to
      // explicitly acquire it.
      Python::PermanentlyReleaseGIL();
    }
  } catch (const std::exception& exc) {
    std::string error_msg =
        std::string("Unhandled exception in MonolithicMain(): ") + exc.what();

    // Let the user and/or master-server know what killed us.
    FatalErrorHandling::ReportFatalError(error_msg, true);

    // Exiting the app via an exception tends to lead to crash reports. If
    // it seems we're not on an official live build then we'd rather just
    // exit cleanly with an error code and avoid polluting crash report logs
    // with reports from dev builds.
    bool try_to_exit_cleanly = !(l_base && l_base->IsUnmodifiedBlessedBuild());

    // If this returns true, it means the platform/app-adapter is handling
    // things (showing a fatal error dialog, etc.) and it's out of our
    // hands.
    bool handled =
        FatalErrorHandling::HandleFatalError(try_to_exit_cleanly, true);

    // If it's not been handled, take the app down ourself.
    if (!handled) {
      // Let anyone interested know we're trying to go down NOW.
      if (l_core) {
        l_core->set_engine_done();
        // Note: We DO NOT call FinalizePython() in this case; we're already
        // going down in flames so that might just make things worse.
      }
      if (try_to_exit_cleanly) {
        exit(1);
      } else {
        throw;  // Crash report here we come!
      }
    }
  }
  return 0;
}

// A way to do the same as above except in an incremental manner. This can
// be used to avoid app-not-responding reports on slow devices by
// interleaving engine init steps with other event processing.
class IncrementalInitRunner_ {
 public:
  explicit IncrementalInitRunner_(const core::CoreConfig* config)
      : config_(*config) {}
  auto Process() -> bool {
    if (zombie_) {
      return false;
    }
    try {
      switch (step_) {
        case 0:
          core_ = core::CoreFeatureSet::Import(&config_);
          step_++;
          return false;
        case 1:
          core_->python->MonolithicModeBaEnvConfigure();
          step_++;
          return false;
        case 2:
          base_ = core_->SoftImportBase();
          if (!base_) {
            FatalError("Base module unavailable; can't run app.");
          }
          step_++;
          return false;
        case 3:
          base_->StartApp();
          Python::PermanentlyReleaseGIL();
          step_++;
          return false;
        default:
          return true;
      }
    } catch (const std::exception& exc) {
      std::string error_msg =
          std::string("Unhandled exception in MonolithicMain(): ") + exc.what();

      // Let the user and/or master-server know what killed us.
      FatalErrorHandling::ReportFatalError(error_msg, true);

      // Exiting the app via an exception tends to lead to crash reports. If
      // it seems we're not on an official live build then we'd rather just
      // exit cleanly with an error code and avoid polluting crash report logs
      // with reports from dev builds.
      bool try_to_exit_cleanly = !(base_ && base_->IsUnmodifiedBlessedBuild());

      // If this returns true, it means the platform/app-adapter is handling
      // things (showing a fatal error dialog, etc.) and it's out of our
      // hands.
      bool handled =
          FatalErrorHandling::HandleFatalError(try_to_exit_cleanly, true);

      // If it's not been handled, take the app down ourself.
      if (!handled) {
        if (try_to_exit_cleanly) {
          exit(1);
        } else {
          throw;  // Crash report here we come!
        }
      }
      // Just go into vegetable mode so hopefully the handler can do its
      // thing.
      zombie_ = true;
      return false;
    }
  }

 private:
  int step_{};
  bool zombie_{};
  core::CoreConfig config_;
  core::CoreFeatureSet* core_{};
  core::BaseSoftInterface* base_{};
};

static IncrementalInitRunner_* g_incremental_init_runner_{};

auto MonolithicMainIncremental(const core::CoreConfig* config) -> bool {
  if (g_incremental_init_runner_ == nullptr) {
    g_incremental_init_runner_ = new IncrementalInitRunner_(config);
  }
  return g_incremental_init_runner_->Process();
}

#endif  // BA_MONOLITHIC_BUILD

void FatalError(const std::string& message) {
  FatalErrorHandling::DoFatalError(message);
}

}  // namespace ballistica
