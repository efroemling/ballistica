// Released under the MIT License. See LICENSE for details.

#include "ballistica/ballistica.h"

#include <map>

#include "ballistica/app/app_flavor.h"
#include "ballistica/assets/assets.h"
#include "ballistica/assets/assets_server.h"
#include "ballistica/audio/audio_server.h"
#include "ballistica/core/fatal_error.h"
#include "ballistica/core/logging.h"
#include "ballistica/core/thread.h"
#include "ballistica/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/game/v1_account.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/networking/network_writer.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

// These are set automatically via script; don't modify them here.
const int kAppBuildNumber = 20806;
const char* kAppVersion = "1.7.7";

// Our standalone globals.
// These are separated out for easy access.
// Everything else should go into App (or more ideally into a class).
int g_early_log_writes{10};

V1Account* g_v1_account{};
AppConfig* g_app_config{};
App* g_app{};
AppInternal* g_app_internal{};
AppFlavor* g_app_flavor{};
Audio* g_audio{};
AudioServer* g_audio_server{};
BGDynamics* g_bg_dynamics{};
BGDynamicsServer* g_bg_dynamics_server{};
Game* g_game{};
Graphics* g_graphics{};
GraphicsServer* g_graphics_server{};
Input* g_input{};
Thread* g_main_thread{};
Assets* g_assets{};
AssetsServer* g_assets_server{};
NetworkReader* g_network_reader{};
Networking* g_networking{};
NetworkWriteModule* g_network_writer{};
Platform* g_platform{};
Python* g_python{};
StdInputModule* g_std_input_module{};
TextGraphics* g_text_graphics{};
UI* g_ui{};
Utils* g_utils{};

// Basic overview of our bootstrapping process:
// 1: All threads and globals are created and provisioned. Everything above
//    should exist at the end of this step (if it is going to exist).
//    Threads should not be talking to each other yet at this point.
// 2: The system is set in motion. Game thread is told to load/apply the config.
//    This event kicks off an initial-screen-creation message sent to the
//    graphics-server thread. Other systems are informed that bootstrapping
//    is complete and that they are free to talk to each other. Initial
//    input-devices are added, asset loads can begin (at least ones not
//    dependent on the screen/renderer), etc.
// 3: The initial screen is created on the graphics-server thread in response
//    to the message sent from the game thread. A completion notice is sent
//    back to the game thread when done.
// 4: Back on the game thread, any renderer-dependent asset-loads/etc. can begin
//    and lastly the initial game session is kicked off.

auto BallisticaMain(int argc, char** argv) -> int {
  try {
    // Even at the absolute start of execution we should be able to
    // phone home on errors. Set env var BA_CRASH_TEST=1 to test this.
    if (const char* crashenv = getenv("BA_CRASH_TEST")) {
      if (!strcmp(crashenv, "1")) {
        FatalError("Fatal-Error-Test");
      }
    }

    // -------------------------------------------------------------------------
    // Phase 1: Create and provision all globals.
    // -------------------------------------------------------------------------

    // Absolute bare-bones basics.
    g_app = new App(argc, argv);
    g_platform = Platform::Create();

    // Bootstrap our Python environment as early as we can (depends on
    // g_platform for locating OS-specific paths).
    assert(g_python == nullptr);
    g_python = new Python();

    // Create a Thread wrapper around the current (main) thread.
    g_main_thread = new Thread(ThreadIdentifier::kMain, ThreadType::kMain);
    Thread::UpdateMainThreadID();

    // Spin up our specific app variation (VR, headless, regular, etc.)
    g_app_flavor = g_platform->CreateAppFlavor();
    g_app_flavor->PostInit();

    // Various other subsystems.
    g_v1_account = new V1Account();
    g_utils = new Utils();
    g_assets = new Assets();
    Scene::Init();

    // Spin up our other standard threads.
    auto* assets_thread{new Thread(ThreadIdentifier::kAssets)};
    g_app->pausable_threads.push_back(assets_thread);
    auto* audio_thread{new Thread(ThreadIdentifier::kAudio)};
    g_app->pausable_threads.push_back(audio_thread);
    auto* logic_thread{new Thread(ThreadIdentifier::kLogic)};
    g_app->pausable_threads.push_back(logic_thread);
    auto* network_write_thread{new Thread(ThreadIdentifier::kNetworkWrite)};
    g_app->pausable_threads.push_back(network_write_thread);

    // Spin up our subsystems in those threads.
    logic_thread->PushCallSynchronous(
        [logic_thread] { new Game(logic_thread); });
    network_write_thread->PushCallSynchronous([network_write_thread] {
      new NetworkWriteModule(network_write_thread);
    });
    assets_thread->PushCallSynchronous(
        [assets_thread] { new AssetsServer(assets_thread); });
    new GraphicsServer(g_main_thread);
    audio_thread->PushCallSynchronous(
        [audio_thread] { new AudioServer(audio_thread); });

    // Now let the platform spin up any other threads/modules it uses.
    // (bg-dynamics in non-headless builds, stdin/stdout where applicable,
    // etc.)
    g_platform->CreateAuxiliaryModules();

    // Ok at this point we can be considered up-and-running.
    g_app->is_bootstrapped = true;

    // -------------------------------------------------------------------------
    // Phase 2: Set things in motion.
    // -------------------------------------------------------------------------

    // Let the app and platform do whatever else it wants here such as adding
    // initial input devices/etc.
    g_app_flavor->OnBootstrapComplete();
    g_platform->OnBootstrapComplete();

    // Ok; now that we're bootstrapped, tell the game thread to read and apply
    // the config which should kick off the real action.
    g_game->PushApplyConfigCall();

    // -------------------------------------------------------------------------
    // Phase 3/4: Create a screen and/or kick off game (in other threads).
    // -------------------------------------------------------------------------

    if (g_app_flavor->ManagesEventLoop()) {
      // On our event-loop-managing platforms we now simply sit in our event
      // loop until the app is quit.
      g_main_thread->RunEventLoop(false);
    } else {
      // In this case we'll now simply return and let the OS feed us events
      // until the app quits.
      // However, we may need to 'prime the pump' first. For instance,
      // if the main thread event loop is driven by frame draws, it may need
      // to manually pump events until drawing begins (otherwise it will never
      // process the 'create-screen' event and wind up deadlocked).
      g_app_flavor->PrimeEventPump();
    }
  } catch (const std::exception& exc) {
    std::string error_msg =
        std::string("Unhandled exception in BallisticaMain(): ") + exc.what();

    // Exiting the app via an exception tends to trigger crash reports
    // on various platforms. If it seems we're not on an official live
    // build then we'd rather just exit cleanly with an error code and avoid
    // polluting crash report logs from dev builds.
    FatalError::ReportFatalError(error_msg, true);
    bool exit_cleanly = !IsUnmodifiedBlessedBuild();
    bool handled = FatalError::HandleFatalError(exit_cleanly, true);

    // Do the default thing if it's not been handled.
    if (!handled) {
      if (exit_cleanly) {
        exit(1);
      } else {
        throw;
      }
    }
  }

  g_platform->WillExitMain(false);
  return g_app->return_value;
}

auto GetRealTime() -> millisecs_t {
  millisecs_t t = g_platform->GetTicks();

  // If we're at a different time than our last query, do our funky math.
  if (t != g_app->last_real_time_ticks) {
    std::scoped_lock lock(g_app->real_time_mutex);
    millisecs_t passed = t - g_app->last_real_time_ticks;

    // GetTicks() is supposed to be monotonic, but I've seen 'passed'
    // equal -1 even when it is using std::chrono::steady_clock. Let's do
    // our own filtering here to make 100% sure we don't go backwards.
    if (passed < 0) {
      passed = 0;
    } else {
      // Very large times-passed probably means we went to sleep or something;
      // clamp to a reasonable value.
      if (passed > 250) {
        passed = 250;
      }
    }
    g_app->real_time += passed;
    g_app->last_real_time_ticks = t;
  }
  return g_app->real_time;
}

auto FatalError(const std::string& message) -> void {
  FatalError::ReportFatalError(message, false);
  bool exit_cleanly = !IsUnmodifiedBlessedBuild();
  bool handled = FatalError::HandleFatalError(exit_cleanly, false);
  assert(handled);
}

auto GetAppInstanceUUID() -> const std::string& {
  static std::string session_id;
  static bool have_session_id = false;

  if (!have_session_id) {
    if (g_python) {
      Python::ScopedInterpreterLock gil;
      auto uuid = g_python->obj(Python::ObjID::kUUIDStrCall).Call();
      if (uuid.exists()) {
        session_id = uuid.ValueAsString().c_str();
        have_session_id = true;
      }
    }
    if (!have_session_id) {
      // As an emergency fallback simply use a single random number.
      Log("WARNING: GetSessionUUID() using rand fallback.");
      srand(static_cast<unsigned int>(
          Platform::GetCurrentMilliseconds()));                    // NOLINT
      session_id = std::to_string(static_cast<uint32_t>(rand()));  // NOLINT
      have_session_id = true;
    }
    if (session_id.size() >= 100) {
      Log("WARNING: session id longer than it should be.");
    }
  }
  return session_id;
}

auto InLogicThread() -> bool {
  return (g_game && g_game->thread()->IsCurrent());
}

auto InMainThread() -> bool {
  return (g_app && std::this_thread::get_id() == g_app->main_thread_id);
}

auto InGraphicsThread() -> bool {
  return (g_graphics_server && g_graphics_server->thread()->IsCurrent());
}

auto InAudioThread() -> bool {
  return (g_audio_server && g_audio_server->thread()->IsCurrent());
}

auto InBGDynamicsThread() -> bool {
  return (g_bg_dynamics_server && g_bg_dynamics_server->thread()->IsCurrent());
}

auto InAssetsThread() -> bool {
  return (g_assets_server && g_assets_server->thread()->IsCurrent());
}

auto InNetworkWriteThread() -> bool {
  return (g_network_writer && g_network_writer->thread()->IsCurrent());
}

auto Log(const std::string& msg, bool to_stdout, bool to_server) -> void {
  Logging::Log(msg, to_stdout, to_server);
}

auto IsVRMode() -> bool { return g_app->vr_mode; }

void ScreenMessage(const std::string& s, const Vector3f& color) {
  if (g_game) {
    g_game->PushScreenMessage(s, color);
  } else {
    Log("ScreenMessage before g_game init (will be lost): '" + s + "'");
  }
}

auto ScreenMessage(const std::string& msg) -> void {
  ScreenMessage(msg, {1.0f, 1.0f, 1.0f});
}

auto GetCurrentThreadName() -> std::string {
  return Thread::GetCurrentThreadName();
}

auto IsBootstrapped() -> bool { return g_app->is_bootstrapped; }

}  // namespace ballistica

// If desired, define main() in the global namespace.
#if BA_DEFINE_MAIN
auto main(int argc, char** argv) -> int {
  return ballistica::BallisticaMain(argc, argv);
}
#endif
