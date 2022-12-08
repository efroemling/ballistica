// Released under the MIT License. See LICENSE for details.

#include "ballistica/ballistica.h"

#include <map>

#include "ballistica/app/app_config.h"
#include "ballistica/app/app_flavor.h"
#include "ballistica/assets/assets.h"
#include "ballistica/assets/assets_server.h"
#include "ballistica/audio/audio.h"
#include "ballistica/audio/audio_server.h"
#include "ballistica/core/fatal_error.h"
#include "ballistica/core/logging.h"
#include "ballistica/core/thread.h"
#include "ballistica/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/text/text_graphics.h"
#include "ballistica/input/input.h"
#include "ballistica/internal/app_internal.h"
#include "ballistica/logic/v1_account.h"
#include "ballistica/networking/network_reader.h"
#include "ballistica/networking/network_writer.h"
#include "ballistica/networking/networking.h"
#include "ballistica/platform/platform.h"
#include "ballistica/platform/stdio_console.h"
#include "ballistica/python/python.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/v1/scene_v1.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

// These are set automatically via script; don't modify them here.
const int kAppBuildNumber = 20961;
const char* kAppVersion = "1.7.16";

// Our standalone globals.
// These are separated out for easy access.
// Everything else should go into App (or more ideally into a class).
int g_early_v1_cloud_log_writes{10};

App* g_app{};
AppConfig* g_app_config{};
AppInternal* g_app_internal{};
AppFlavor* g_app_flavor{};
Assets* g_assets{};
AssetsServer* g_assets_server{};
Audio* g_audio{};
AudioServer* g_audio_server{};
BGDynamics* g_bg_dynamics{};
BGDynamicsServer* g_bg_dynamics_server{};
Context* g_context{};
Graphics* g_graphics{};
GraphicsServer* g_graphics_server{};
Input* g_input{};
Logic* g_logic{};
Thread* g_main_thread{};
Networking* g_networking{};
NetworkReader* g_network_reader{};
NetworkWriter* g_network_writer{};
Platform* g_platform{};
Python* g_python{};
SceneV1* g_scene_v1{};
StdioConsole* g_stdio_console{};
TextGraphics* g_text_graphics{};
UI* g_ui{};
Utils* g_utils{};
V1Account* g_v1_account{};

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
    // Phase 1: "The board is set."
    // -------------------------------------------------------------------------

    // Here we instantiate all of our globals. Code here should
    // avoid any logic that accesses other globals since they may
    // not yet exist.

    // Minimal globals we must assign immediately as they ARE needed
    // for construction of the others (would be great to eliminate this need).
    g_platform = Platform::Create();
    g_app = new App(argc, argv);
    g_app_internal = CreateAppInternal();
    g_main_thread = new Thread(ThreadTag::kMain, ThreadSource::kWrapMain);

    // For everything else, we hold off until the end to actually assign
    // them to their globals. This keeps us honest and catches any stray
    // inter-global access that we might accidentally include in a
    // constructor.
    auto* app_flavor = g_platform->CreateAppFlavor();
    auto* python = Python::Create();
    auto* graphics = g_platform->CreateGraphics();
    auto* graphics_server = new GraphicsServer();
    auto* audio = new Audio();
    auto* audio_server = new AudioServer();
    auto* context = new Context(nullptr);
    auto* text_graphics = new TextGraphics();
    auto* app_config = new AppConfig();
    auto* v1_account = new V1Account();
    auto* utils = new Utils();
    auto* assets = new Assets();
    auto* assets_server = new AssetsServer();
    auto* ui = Object::NewUnmanaged<UI>();
    auto* networking = new Networking();
    auto* network_reader = new NetworkReader();
    auto* network_writer = new NetworkWriter();
    auto* input = new Input();
    auto* logic = new Logic();
    auto* scene_v1 = new SceneV1();
    auto* bg_dynamics = HeadlessMode() ? nullptr : new BGDynamics;
    auto* bg_dynamics_server = HeadlessMode() ? nullptr : new BGDynamicsServer;
    auto* stdio_console =
        g_buildconfig.enable_stdio_console() ? new StdioConsole() : nullptr;

    g_app_flavor = app_flavor;
    g_python = python;
    g_graphics = graphics;
    g_graphics_server = graphics_server;
    g_audio = audio;
    g_audio_server = audio_server;
    g_context = context;
    g_text_graphics = text_graphics;
    g_app_config = app_config;
    g_v1_account = v1_account;
    g_utils = utils;
    g_assets = assets;
    g_assets_server = assets_server;
    g_ui = ui;
    g_networking = networking;
    g_network_reader = network_reader;
    g_network_writer = network_writer;
    g_input = input;
    g_logic = logic;
    g_scene_v1 = scene_v1;
    g_bg_dynamics = bg_dynamics;
    g_bg_dynamics_server = bg_dynamics_server;
    g_stdio_console = stdio_console;

    g_app->is_bootstrapped = true;

    // -------------------------------------------------------------------------
    // Phase 2: "The pieces are moving."
    // -------------------------------------------------------------------------

    // Allow our subsystems to start doing work in their own threads
    // and communicating with other subsystems. Note that we may still
    // want to run some things serially here and ordering may be important
    // (for instance we want to give our main thread a chance to register
    // all initial input devices with the logic thread before the logic
    // thread applies the current config to them).

    g_logic->OnAppStart();
    g_audio_server->OnAppStart();
    g_assets_server->OnAppStart();
    g_platform->OnAppStart();
    g_app_flavor->OnAppStart();
    if (g_stdio_console) {
      g_stdio_console->OnAppStart();
    }

    // As the last step of this phase, tell the logic thread to apply
    // the app config which will kick off screen creation and otherwise
    // get the ball rolling.
    g_logic->PushApplyConfigCall();

    // -------------------------------------------------------------------------
    // Phase 3: "We come to it at last; the great battle of our time."
    // -------------------------------------------------------------------------

    // At this point all threads are off and running and we simply
    // feed events until things end (or return and let the OS do that).

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
  BA_PRECONDITION(handled);
}

// FIXME: move this to g_app or whatnot.
auto GetAppInstanceUUID() -> const std::string& {
  static std::string app_instance_uuid;
  static bool have_app_instance_uuid = false;

  if (!have_app_instance_uuid) {
    if (g_python) {
      Python::ScopedInterpreterLock gil;
      auto uuid = g_python->obj(Python::ObjID::kUUIDStrCall).Call();
      if (uuid.exists()) {
        app_instance_uuid = uuid.ValueAsString().c_str();
        have_app_instance_uuid = true;
      }
    }
    if (!have_app_instance_uuid) {
      // As an emergency fallback simply use a single random number.
      // We should probably simply disallow this before Python is up.
      Log(LogLevel::kWarning, "GetSessionUUID() using rand fallback.");
      srand(static_cast<unsigned int>(
          Platform::GetCurrentMilliseconds()));  // NOLINT
      app_instance_uuid =
          std::to_string(static_cast<uint32_t>(rand()));  // NOLINT
      have_app_instance_uuid = true;
    }
    if (app_instance_uuid.size() >= 100) {
      Log(LogLevel::kWarning, "session id longer than it should be.");
    }
  }
  return app_instance_uuid;
}

auto InMainThread() -> bool {
  assert(g_main_thread);  // Root out early use of this.
  return (g_main_thread->IsCurrent());
}

auto InLogicThread() -> bool {
  assert(g_app && g_app->is_bootstrapped);  // Root out early use of this.
  return (g_logic && g_logic->thread()->IsCurrent());
}

auto InGraphicsThread() -> bool {
  assert(g_app && g_app->is_bootstrapped);  // Root out early use of this.
  return (g_graphics_server && g_graphics_server->thread()->IsCurrent());
}

auto InAudioThread() -> bool {
  assert(g_app && g_app->is_bootstrapped);  // Root out early use of this.
  return (g_audio_server && g_audio_server->thread()->IsCurrent());
}

auto InBGDynamicsThread() -> bool {
  assert(g_app && g_app->is_bootstrapped);  // Root out early use of this.
  return (g_bg_dynamics_server && g_bg_dynamics_server->thread()->IsCurrent());
}

auto InAssetsThread() -> bool {
  assert(g_app && g_app->is_bootstrapped);  // Root out early use of this.
  return (g_assets_server && g_assets_server->thread()->IsCurrent());
}

auto InNetworkWriteThread() -> bool {
  assert(g_app && g_app->is_bootstrapped);  // Root out early use of this.
  return (g_network_writer && g_network_writer->thread()->IsCurrent());
}

auto Log(LogLevel level, const std::string& msg) -> void {
  Logging::Log(level, msg);
}

auto IsVRMode() -> bool { return g_app->vr_mode; }

void ScreenMessage(const std::string& s, const Vector3f& color) {
  if (g_logic) {
    g_logic->PushScreenMessage(s, color);
  } else {
    Log(LogLevel::kError,
        "ScreenMessage before g_logic init (will be lost): '" + s + "'");
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
