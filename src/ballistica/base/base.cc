// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/base.h"

#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/empty_app_mode.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/assets_server.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/discord/discord.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/base/networking/network_writer.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_feature_set_data.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/support/base_build_switches.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/base/support/stdio_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/base/ui/ui_delegate.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/vector4f.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica::base {

core::CoreFeatureSet* g_core{};
BaseFeatureSet* g_base{};

BaseFeatureSet::BaseFeatureSet()
    : app_adapter{BaseBuildSwitches::CreateAppAdapter()},
      app_config{new AppConfig()},
      app_mode_{EmptyAppMode::GetSingleton()},
      assets{new Assets()},
      assets_server{new AssetsServer()},
      audio{new Audio()},
      audio_server{new AudioServer()},
      basn_log_behavior_{g_core->platform->GetEnv("BASNLOG") == "1"},
      bg_dynamics{g_core->HeadlessMode() ? nullptr : new BGDynamics},
      bg_dynamics_server{g_core->HeadlessMode() ? nullptr
                                                : new BGDynamicsServer},
      context_ref{new ContextRef(nullptr)},
      graphics{BaseBuildSwitches::CreateGraphics()},
      graphics_server{new GraphicsServer()},
      input{new Input()},
      logic{new Logic()},
      network_reader{new NetworkReader()},
      network_writer{new NetworkWriter()},
      networking{new Networking()},
      platform{BaseBuildSwitches::CreatePlatform()},
      python{new BasePython()},
      stdio_console{g_buildconfig.enable_stdio_console() ? new StdioConsole()
                                                         : nullptr},
      text_graphics{new TextGraphics()},
      ui{new UI()},
      utils{new Utils()},
      discord{g_buildconfig.enable_discord() ? new Discord() : nullptr} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_base == nullptr);

  // We modify some app behavior when run under the server manager.
  auto* envval = getenv("BA_SERVER_WRAPPER_MANAGED");
  server_wrapper_managed_ = (envval && strcmp(envval, "1") == 0);
}

void BaseFeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported. Just like a
  // pure Python module would, we take this opportunity to import/create the
  // stuff we use.

  // Importing core should always be the first thing we do. Various
  // Ballistica functionality will fail if this has not been done.
  assert(g_core == nullptr);
  g_core = core::CoreFeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_babase exec begin");

  // This locks in a baenv configuration.
  g_core->ApplyBaEnvConfig();

  // Create our feature-set's C++ front-end.
  assert(g_base == nullptr);
  g_base = new BaseFeatureSet();

  // Core uses some of our functionality when we're present. Let them know
  // we're now present.
  core::g_base_soft = g_base;

  // Define our native Python classes.
  //
  // NOTE: Normally we'd define our classes *after* we import stuff (like a
  // regular Python module generally would) but we need FeatureSetData to
  // exist *before* we call StoreOnPythonModule, so we have to do this
  // early.
  g_base->python->AddPythonClasses(module);

  // Store our C++ front-end with our Python module. This is what allows
  // other C++ code to 'import' our C++ front end and talk to us directly.
  g_base->StoreOnPythonModule(module);

  // Import all the Python stuff we use.
  g_base->python->ImportPythonObjs();

  // Run some sanity checks, wire up our log handler, etc.
  bool success = g_base->python->objs()
                     .Get(BasePython::ObjID::kEnvOnNativeModuleImportCall)
                     .Call()
                     .exists();
  if (!success) {
    FatalError("babase._env.on_native_module_import() call failed.");
  }

  // A marker we pop down at the very end so other modules can run sanity
  // checks to make sure we aren't importing them reciprocally when they
  // import us.
  Python::MarkReachedEndOfModule(module);
  assert(!g_base->base_native_import_completed_);
  g_base->base_native_import_completed_ = true;

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_babase exec end");
}

void BaseFeatureSet::OnReachedEndOfBaBaseImport() {
  assert(!base_import_completed_);
  g_base->python->ImportPythonAppObjs();
  base_import_completed_ = true;
}

auto BaseFeatureSet::Import() -> BaseFeatureSet* {
  return ImportThroughPythonModule<BaseFeatureSet>("_babase");
}

auto BaseFeatureSet::IsBaseCompletelyImported() -> bool {
  return base_import_completed_ && base_native_import_completed_;
}

void BaseFeatureSet::SuccessScreenMessage() {
  if (auto* event_loop = logic->event_loop()) {
    event_loop->PushCall([this] {
      python->objs().Get(BasePython::ObjID::kSuccessMessageCall).Call();
    });
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "SuccessScreenMessage called without logic event_loop in place.");
  }
}

void BaseFeatureSet::ErrorScreenMessage() {
  if (auto* event_loop = logic->event_loop()) {
    event_loop->PushCall([this] {
      python->objs().Get(BasePython::ObjID::kErrorMessageCall).Call();
    });
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "ErrorScreenMessage called without logic event_loop in place.");
  }
}

auto BaseFeatureSet::GetV2AccountID() -> std::optional<std::string> {
  // Guard against this getting called early.
  if (!IsAppStarted()) {
    return {};
  }

  auto gil = Python::ScopedInterpreterLock();
  auto result =
      python->objs().Get(BasePython::ObjID::kGetV2AccountIdCall).Call();
  if (result.exists()) {
    if (result.ValueIsNone()) {
      return {};
    }
    return result.ValueAsString();
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "GetV2AccountID() py call errored.");
    return {};
  }
}

void BaseFeatureSet::OnAssetsAvailable() {
  assert(InLogicThread());

  ui->OnAssetsAvailable();
}

void BaseFeatureSet::StartApp() {
  BA_PRECONDITION(g_core->InMainThread());
  BA_PRECONDITION(g_base);

  auto start_time = g_core->AppTimeSeconds();

  // Currently limiting this to once per process.
  BA_PRECONDITION(!called_start_app_);
  called_start_app_ = true;
  assert(!app_started_);  // Shouldn't be possible.

  LogStartupMessage_();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "start-app begin (main thread)");

  // The logic thread (or maybe other things) need to run Python as
  // we're bringing them up, so let it go for the duration of this call.
  // We'll explicitly grab it if/when we need it.
  Python::ScopedInterpreterLockRelease gil_release;

  // Allow our subsystems to start doing work in their own threads and
  // communicating with other subsystems. Note that we may still want to run
  // some things serially here and ordering may be important (for instance
  // we want to give our main thread a chance to register all initial input
  // devices with the logic thread before the logic thread applies the
  // current config to them).

  python->OnMainThreadStartApp();
  logic->OnMainThreadStartApp();
  graphics_server->OnMainThreadStartApp();
  if (bg_dynamics_server) {
    bg_dynamics_server->OnMainThreadStartApp();
  }
  network_writer->OnMainThreadStartApp();
  audio_server->OnMainThreadStartApp();
  assets_server->OnMainThreadStartApp();
  app_adapter->OnMainThreadStartApp();

  // Ok; we're now official 'started'. Various code such as anything that
  // pushes messages to threads can watch for this state (via IsAppStarted()
  // to avoid crashing if called early.
  app_started_ = true;

  // As the last step of this phase, tell the logic thread to apply the app
  // config which will kick off screen creation or otherwise to get the
  // ball rolling.
  {
    Python::ScopedInterpreterLock gil;
    python->objs().Get(BasePython::ObjID::kAppPushApplyAppConfigCall).Call();
  }

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "start-app end (main thread)");

  // Make some noise if this takes more than a few seconds. If we pass 5
  // seconds or so we start to trigger App-Not-Responding reports which
  // isn't good.
  auto duration = g_core->AppTimeSeconds() - start_time;
  if (duration > 3.0) {
    char buffer[128];
    snprintf(buffer, sizeof(buffer),
             "StartApp() took too long (%.2lf seconds).", duration);
    g_core->logging->Log(LogName::kBa, LogLevel::kWarning, buffer);
  }
}

void BaseFeatureSet::SuspendApp() {
  assert(g_core);
  assert(g_core->InMainThread());

  if (app_suspended_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "AppAdapter::SuspendApp() called with app already suspended.");
    return;
  }

  millisecs_t start_time{core::CorePlatform::TimeMonotonicMillisecs()};

  // Apple mentioned 5 seconds to run stuff once backgrounded or they bring
  // down the hammer. Let's aim to stay under 4.
  millisecs_t max_duration{4000};

  g_core->platform->LowLevelDebugLog(
      "SuspendApp@"
      + std::to_string(core::CorePlatform::TimeMonotonicMillisecs()));
  app_suspended_ = true;

  // IMPORTANT: Any pause related stuff that event-loop-threads need to do
  // should be done from their registered pause-callbacks. If we instead
  // push runnables to them from here they may or may not be called before
  // their event-loop is actually paused (event-loops don't exhaust queued
  // runnables before pausing since those could block on other
  // already-paused threads).

  // Currently the only Python level call related to this is
  // AppMode.on_app_active_changed(), but that runs in the logic thread and,
  // as mentioned above, we don't have any strict guarantees that it gets
  // run before this suspend goes through. So let's wait for up to a
  // fraction of our total max-duration here to make sure it has been called
  // and make some noise if it hasn't been.
  millisecs_t max_duration_part{max_duration / 2};
  while (true) {
    if (g_base->logic->app_active_applied() == false) {
      break;
    }
    if (std::abs(core::CorePlatform::TimeMonotonicMillisecs() - start_time)
        >= max_duration_part) {
      BA_LOG_ONCE(
          LogName::kBa, LogLevel::kError,
          "SuspendApp timed out waiting for app-active callback to complete.");
      break;
    }
    core::CorePlatform::SleepMillisecs(1);
  }

  EventLoop::SetEventLoopsSuspended(true);

  if (g_base->network_reader) {
    g_base->network_reader->OnAppSuspend();
  }
  g_base->networking->OnAppSuspend();

  // We assume that the OS will completely suspend our process the moment we
  // return from this call (though this is not technically true on all
  // platforms). So we want to spin here and give our various event loop
  // threads time to park themselves.
  std::vector<EventLoop*> running_loops;
  do {
    // If/when we get to a point with no threads waiting to be paused, we're
    // good to go.
    running_loops = EventLoop::GetStillSuspendingEventLoops();
    if (running_loops.empty()) {
      if (g_buildconfig.debug_build()) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kDebug,
            "SuspendApp() completed in "
                + std::to_string(core::CorePlatform::TimeMonotonicMillisecs()
                                 - start_time)
                + "ms.");
      }
      return;
    }
  } while (std::abs(core::CorePlatform::TimeMonotonicMillisecs() - start_time)
           < max_duration);

  // If we made it here, we timed out. Complain.
  std::string msg =
      std::string("SuspendApp() took too long; ")
      + std::to_string(running_loops.size())
      + " event-loops not yet suspended after "
      + std::to_string(core::CorePlatform::TimeMonotonicMillisecs()
                       - start_time)
      + " ms: (";
  bool first = true;
  for (auto* loop : running_loops) {
    if (!first) {
      msg += ", ";
    }
    // Note: not adding a default here so the compiler complains if we
    // add/change something.
    switch (loop->identifier()) {
      case EventLoopID::kInvalid:
        msg += "invalid";
        break;
      case EventLoopID::kLogic:
        msg += "logic";
        break;
      case EventLoopID::kAssets:
        msg += "assets";
        break;
      case EventLoopID::kFileOut:
        msg += "fileout";
        break;
      case EventLoopID::kMain:
        msg += "main";
        break;
      case EventLoopID::kAudio:
        msg += "audio";
        break;
      case EventLoopID::kNetworkWrite:
        msg += "networkwrite";
        break;
      case EventLoopID::kSuicide:
        msg += "suicide";
        break;
      case EventLoopID::kStdin:
        msg += "stdin";
        break;
      case EventLoopID::kBGDynamics:
        msg += "bgdynamics";
        break;
    }
    first = false;
  }
  msg += ").";

  g_core->logging->Log(LogName::kBa, LogLevel::kError, msg);
}

void BaseFeatureSet::UnsuspendApp() {
  assert(g_core);
  assert(g_core->InMainThread());

  if (!app_suspended_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "AppAdapter::UnsuspendApp() called with app not in suspendedstate.");
    return;
  }
  millisecs_t start_time{core::CorePlatform::TimeMonotonicMillisecs()};
  g_core->platform->LowLevelDebugLog(
      "UnsuspendApp@"
      + std::to_string(core::CorePlatform::TimeMonotonicMillisecs()));
  app_suspended_ = false;

  // Spin all event-loops back up.
  EventLoop::SetEventLoopsSuspended(false);

  // Run resumes that expect to happen in the main thread.
  g_base->network_reader->OnAppUnsuspend();
  g_base->networking->OnAppUnsuspend();

  if (g_buildconfig.debug_build()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kDebug,
        "UnsuspendApp() completed in "
            + std::to_string(core::CorePlatform::TimeMonotonicMillisecs()
                             - start_time)
            + "ms.");
  }
}

void BaseFeatureSet::OnAppShutdownComplete() {
  assert(g_core->InMainThread());
  assert(g_core);
  assert(g_base);

  // Flag our own event loop to exit (or ask the OS to if they're managing).
  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "app exiting (main thread)");
  if (app_adapter->ManagesMainThreadEventLoop()) {
    app_adapter->DoExitMainThreadEventLoop();
  } else {
    app_adapter->TerminateApp();
  }
}

void BaseFeatureSet::LogStartupMessage_() {
  char buffer[256];
  if (g_buildconfig.headless_build()) {
    snprintf(buffer, sizeof(buffer),
             "BallisticaKit Headless %s build %d starting...", kEngineVersion,
             kEngineBuildNumber);
  } else {
    snprintf(buffer, sizeof(buffer), "BallisticaKit %s build %d starting...",
             kEngineVersion, kEngineBuildNumber);
  }
  g_core->logging->Log(LogName::kBaApp, LogLevel::kInfo, buffer);
}

void BaseFeatureSet::set_app_mode(AppMode* mode) {
  assert(InLogicThread());

  // Redundant sets should not happen (make an exception here for empty mode
  // since that's in place before any app mode is officially set).
  if (mode == app_mode_ && mode != EmptyAppMode::GetSingleton()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "set_app_mode called with already-current app-mode; unexpected.");
  }

  try {
    // Tear down previous mode (if any).
    if (app_mode_) {
      app_mode_->OnDeactivate();
    }

    // Set and build up new one.
    app_mode_ = mode;

    // App modes each provide their own input-device delegate types.
    input->RebuildInputDeviceDelegates();

    app_mode_->OnActivate();

    // Let some stuff know.
    logic->OnAppModeChanged();
  } catch (const Exception& exc) {
    // Anything going wrong while switching app-modes leaves us in an
    // undefined state; don't try to continue.
    FatalError(std::string("Error setting native layer app-mode: ")
               + exc.what());
  }
}

auto BaseFeatureSet::AppManagesMainThreadEventLoop() -> bool {
  return app_adapter->ManagesMainThreadEventLoop();
}

void BaseFeatureSet::RunAppToCompletion() {
  BA_PRECONDITION(g_core->InMainThread());
  BA_PRECONDITION(g_base);
  BA_PRECONDITION(g_base->app_adapter->ManagesMainThreadEventLoop());
  BA_PRECONDITION(!called_run_app_to_completion_);
  called_run_app_to_completion_ = true;

  if (!called_start_app_) {
    StartApp();
  }

  // Let go of the GIL while we're running.
  Python::ScopedInterpreterLockRelease gil_release;

  g_base->app_adapter->RunMainThreadEventLoopToCompletion();
}

auto BaseFeatureSet::HavePlus() -> bool {
  if (!plus_soft_ && !tried_importing_plus_) {
    python->SoftImportPlus();
    // Important to set this *after* import attempt, or a second import
    // attempt while first is ongoing can insta-fail. Multiple import
    // attempts shouldn't hurt anything.
    tried_importing_plus_ = true;
  }
  return plus_soft_ != nullptr;
}

void BaseFeatureSet::SetPlus(PlusSoftInterface* plus) {
  assert(plus_soft_ == nullptr);
  plus_soft_ = plus;
}

/// Access the plus feature-set. Will throw an exception if not present.
auto BaseFeatureSet::Plus() -> PlusSoftInterface* {
  if (!plus_soft_ && !tried_importing_plus_) {
    python->SoftImportPlus();
    // Important to set this *after* import attempt, or a second import
    // attempt while first is ongoing can insta-fail. Multiple import
    // attempts shouldn't hurt anything.
    tried_importing_plus_ = true;
  }
  if (!plus_soft_) {
    throw Exception("plus feature-set not present.");
  }
  return plus_soft_;
}

auto BaseFeatureSet::HaveClassic() -> bool {
  if (!classic_soft_ && !tried_importing_classic_) {
    python->SoftImportClassic();
    // Important to set this *after* import attempt, or a second import
    // attempt while first is ongoing can insta-fail. Multiple import
    // attempts shouldn't hurt anything.
    tried_importing_classic_ = true;
  }
  return classic_soft_ != nullptr;
}

/// Access the plus feature-set. Will throw an exception if not present.
auto BaseFeatureSet::classic() -> ClassicSoftInterface* {
  if (!classic_soft_ && !tried_importing_classic_) {
    python->SoftImportClassic();
    // Important to set this *after* import attempt, or a second import
    // attempt while first is ongoing can insta-fail. Multiple import
    // attempts shouldn't hurt anything.
    tried_importing_classic_ = true;
  }
  if (!classic_soft_) {
    throw Exception("classic feature-set not present.");
  }
  return classic_soft_;
}

void BaseFeatureSet::set_classic(ClassicSoftInterface* classic) {
  assert(classic_soft_ == nullptr);
  classic_soft_ = classic;
}

auto BaseFeatureSet::GetAppInstanceUUID() -> const std::string& {
  static std::string app_instance_uuid;
  static bool have_app_instance_uuid = false;

  if (!have_app_instance_uuid) {
    if (g_base) {
      Python::ScopedInterpreterLock gil;
      auto uuid = g_core->python->objs()
                      .Get(core::CorePython::ObjID::kUUIDStrCall)
                      .Call();
      if (uuid.exists()) {
        app_instance_uuid = uuid.ValueAsString();
        have_app_instance_uuid = true;
      }
    }
    if (!have_app_instance_uuid) {
      // As an emergency fallback simply use a single random number. We
      // should probably simply disallow this before Python is up.
      g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                           "GetSessionUUID() using rand fallback.");
      srand(static_cast<unsigned int>(
          core::CorePlatform::TimeMonotonicMillisecs()));  // NOLINT
      app_instance_uuid =
          std::to_string(static_cast<uint32_t>(rand()));  // NOLINT
      have_app_instance_uuid = true;
    }
    if (app_instance_uuid.size() >= 100) {
      g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                           "session id longer than it should be.");
    }
  }
  return app_instance_uuid;
}

void BaseFeatureSet::PlusDirectSendV1CloudLogs(const std::string& prefix,
                                               const std::string& suffix,
                                               bool instant, int* result) {
  if (plus_soft_ != nullptr) {
    plus_soft_->DirectSendV1CloudLogs(prefix, suffix, instant, result);
  }
}

auto BaseFeatureSet::CreateFeatureSetData(FeatureSetNativeComponent* featureset)
    -> PyObject* {
  return PythonClassFeatureSetData::Create(featureset);
}

auto BaseFeatureSet::FeatureSetFromData(PyObject* obj)
    -> FeatureSetNativeComponent* {
  if (!PythonClassFeatureSetData::Check(obj)) {
    FatalError("Module FeatureSetData attr is an incorrect type.");
  }
  return PythonClassFeatureSetData::FromPyObj(obj).feature_set();
}

auto BaseFeatureSet::IsUnmodifiedBlessedBuild() -> bool {
  // If we've got plus present, ask them. Otherwise assume no.
  if (HavePlus()) {
    return Plus()->IsUnmodifiedBlessedBuild();
  }
  return false;
}

auto BaseFeatureSet::InMainThread() const -> bool {
  return g_core->InMainThread();
}

auto BaseFeatureSet::InAssetsThread() const -> bool {
  if (auto* loop = assets_server->event_loop()) {
    return loop->ThreadIsCurrent();
  }
  return false;
}

auto BaseFeatureSet::InLogicThread() const -> bool {
  if (auto* loop = logic->event_loop()) {
    return loop->ThreadIsCurrent();
  }
  return false;
}

auto BaseFeatureSet::InAudioThread() const -> bool {
  if (auto* loop = audio_server->event_loop()) {
    return loop->ThreadIsCurrent();
  }
  return false;
}

auto BaseFeatureSet::InBGDynamicsThread() const -> bool {
  if (auto* loop = bg_dynamics_server->event_loop()) {
    return loop->ThreadIsCurrent();
  }
  return false;
}

auto BaseFeatureSet::InNetworkWriteThread() const -> bool {
  if (auto* loop = network_writer->event_loop()) {
    return loop->ThreadIsCurrent();
  }
  return false;
}

auto BaseFeatureSet::InGraphicsContext() const -> bool {
  return app_adapter->InGraphicsContext();
}

void BaseFeatureSet::ScreenMessage(const std::string& s,
                                   const Vector3f& color) {
  logic->event_loop()->PushCall([this, s, color] {
    graphics->screenmessages->AddScreenMessage(s, color);
  });
}

void BaseFeatureSet::DoV1CloudLog(const std::string& msg) {
  // We may attempt to import stuff and that should *never* happen before
  // base is fully imported.
  if (!IsBaseCompletelyImported()) {
    static bool warned = false;
    if (!warned) {
      warned = true;
      printf(
          "WARNING: V1CloudLog called before babase fully imported; "
          "ignoring.\n");
    }
    return;
  }

  // Even though this part lives here in 'base', this is considered 'classic'
  // functionality, so silently no-op if classic isn't present.
  if (!HaveClassic()) {
    return;
  }

  // Let the Python layer handle this if possible. PushCall functionality
  // requires the app to be running, and the call itself requires plus.
  if (app_started_ && HavePlus()) {
    python->objs().PushCall(BasePython::ObjID::kHandleV1CloudLogCall);
    return;
  }

  // Ok; Python path not available. We might be able to do a direct send.

  // Hack: Currently disabling direct sends for basn to avoid shipping early
  // logs not containing errors or warnings. Need to clean this system up;
  // this shouldn't be necessary.
  if (basn_log_behavior_) {
    return;
  }

  // Need plus for direct sends.
  if (!HavePlus()) {
    static bool did_warn = false;
    if (!did_warn) {
      did_warn = true;
      printf("WARNING: V1CloudLog direct-sends not available; ignoring.\n");
    }
    return;
  }

  // Only attempt direct sends a few times.
  if (core::g_early_v1_cloud_log_writes <= 0) {
    return;
  }

  // Ok; going ahead with the direct send.
  core::g_early_v1_cloud_log_writes -= 1;
  std::string logprefix = "EARLY-LOG:";
  std::string logsuffix;

  // If we're an early enough error, our global log isn't even available,
  // so include this whole message as a suffix instead.
  if (g_core == nullptr) {
    logsuffix = msg;
  }
  Plus()->DirectSendV1CloudLogs(logprefix, logsuffix, false, nullptr);
}

void BaseFeatureSet::PushDevConsolePrintCall(const std::string& msg,
                                             float scale, Vector4f color) {
  ui->PushDevConsolePrintCall(msg, scale, color);
}

PyObject* BaseFeatureSet::GetPyExceptionType(PyExcType exctype) {
  switch (exctype) {
    case PyExcType::kContext:
      return python->objs().Get(BasePython::ObjID::kContextError).get();
    case PyExcType::kNotFound:
      return python->objs().Get(BasePython::ObjID::kNotFoundError).get();
    case PyExcType::kNodeNotFound:
      return python->objs().Get(BasePython::ObjID::kNodeNotFoundError).get();
    case PyExcType::kSessionPlayerNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kSessionPlayerNotFoundError)
          .get();
    case PyExcType::kInputDeviceNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kInputDeviceNotFoundError)
          .get();
    case PyExcType::kDelegateNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kDelegateNotFoundError)
          .get();
    case PyExcType::kWidgetNotFound:
      return python->objs().Get(BasePython::ObjID::kWidgetNotFoundError).get();
    case PyExcType::kActivityNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kActivityNotFoundError)
          .get();
    case PyExcType::kSessionNotFound:
      return python->objs().Get(BasePython::ObjID::kSessionNotFoundError).get();
    default:
      return nullptr;
  }
}

void BaseFeatureSet::SetCurrentContext(const ContextRef& context) {
  assert(InLogicThread());  // Up to caller to ensure this.
  context_ref->SetTarget(context.Get());
}

auto BaseFeatureSet::PrintPythonStackTrace() -> bool {
  Python::ScopedInterpreterLock lock;
  auto objid{BasePython::ObjID::kPrintTraceCall};
  if (python->objs().Exists(objid)) {
    python->objs().Get(objid).Call();
    return true;  // available!
  }
  return false;  // not available.
}

auto BaseFeatureSet::GetPyLString(PyObject* obj) -> std::string {
  return python->GetPyLString(obj);
}

std::string BaseFeatureSet::DoGetContextBaseString() {
  if (!InLogicThread()) {
    return "  context_ref: <not in logic thread>";
  }
  return "  context_ref: " + g_base->CurrentContext().GetDescription();
}
void BaseFeatureSet::DoPrintContextAuto() {
  if (!InLogicThread()) {
    PrintContextNonLogicThread_();
  } else if (const char* label = Python::ScopedCallLabel::current_label()) {
    PrintContextForCallableLabel_(label);
  } else if (PythonCommand* cmd = PythonCommand::current_command()) {
    cmd->PrintContext();
  } else if (PythonContextCall* call = PythonContextCall::current_call()) {
    call->PrintContext();
  } else {
    PrintContextUnavailable_();
  }
}
void BaseFeatureSet::PrintContextNonLogicThread_() {
  std::string s = std::string(
      "  root call: <not in logic thread; context_ref unavailable>");
  PySys_WriteStderr("%s\n", s.c_str());
}

void BaseFeatureSet::PrintContextForCallableLabel_(const char* label) {
  assert(InLogicThread());
  assert(label);
  std::string s = std::string("  root call: ") + label + "\n";
  s += Python::GetContextBaseString();
  PySys_WriteStderr("%s\n", s.c_str());
}

void BaseFeatureSet::PrintContextUnavailable_() {
  // (no logic-thread-check here; can be called early or from other threads)
  std::string s = std::string("  root call: <unavailable>\n");
  s += Python::GetContextBaseString();
  PySys_WriteStderr("%s\n", s.c_str());
}

void BaseFeatureSet::DoPushObjCall(const PythonObjectSetBase* objset, int id) {
  // Watch for uses before we've created our event loop;
  // should fix them at the source.
  assert(IsAppStarted());

  if (auto* loop = logic->event_loop()) {
    logic->event_loop()->PushCall([objset, id] {
      ScopedSetContext ssc(nullptr);
      objset->Obj(id).Call();
    });
  } else {
    BA_LOG_ONCE(
        LogName::kBa, LogLevel::kError,
        "BaseFeatureSet::DoPushObjCall called before event loop created.");
  }
}

void BaseFeatureSet::DoPushObjCall(const PythonObjectSetBase* objset, int id,
                                   const std::string& arg) {
  // Watch for uses before we've created our event loop;
  // should fix them at the source.
  assert(IsAppStarted());

  logic->event_loop()->PushCall([objset, id, arg] {
    ScopedSetContext ssc(nullptr);
    PythonRef args(Py_BuildValue("(s)", arg.c_str()),
                   ballistica::PythonRef::kSteal);
    objset->Obj(id).Call(args);
  });
}

auto BaseFeatureSet::IsAppStarted() const -> bool { return app_started_; }

auto BaseFeatureSet::IsAppBootstrapped() const -> bool {
  return logic->app_bootstrapping_complete();
}

auto BaseFeatureSet::ShutdownSuppressBegin() -> bool {
  std::scoped_lock lock(shutdown_suppress_lock_);

  // Once shutdown has begun, we no longer allow things that would
  // suppress it. Tell the caller to abort what they're trying to do.
  if (shutdown_suppress_disallowed_) {
    return false;
  }
  shutdown_suppress_count_++;
  return true;
}

void BaseFeatureSet::ShutdownSuppressEnd() {
  std::scoped_lock lock(shutdown_suppress_lock_);
  shutdown_suppress_count_--;
  assert(shutdown_suppress_count_ >= 0);
}

auto BaseFeatureSet::ShutdownSuppressGetCount() -> int {
  std::scoped_lock lock(shutdown_suppress_lock_);
  return shutdown_suppress_count_;
}

void BaseFeatureSet::ShutdownSuppressDisallow() {
  std::scoped_lock lock(shutdown_suppress_lock_);
  assert(!shutdown_suppress_disallowed_);
  shutdown_suppress_disallowed_ = true;
}

void BaseFeatureSet::QuitApp(bool confirm, QuitType quit_type) {
  // If they want a confirm dialog and we're able to present one, do that.
  if (confirm && !g_core->HeadlessMode() && !g_base->input->IsInputLocked()
      && g_base->ui->delegate()
      && g_base->ui->delegate()->HasQuitConfirmDialog()) {
    logic->event_loop()->PushCall(
        [this, quit_type] { g_base->ui->delegate()->ConfirmQuit(quit_type); });
    return;
  }
  // Ok looks like we're quitting immediately.
  //
  // If they ask for 'back' and we support that, do it. Otherwise if they
  // want 'back' or 'soft' and we support soft, do it. Otherwise go with a
  // regular app shutdown.
  if (quit_type == QuitType::kBack && app_adapter->CanBackQuit()) {
    logic->event_loop()->PushCall([this] { app_adapter->DoBackQuit(); });
  } else if ((quit_type == QuitType::kBack || quit_type == QuitType::kSoft)
             && app_adapter->CanSoftQuit()) {
    logic->event_loop()->PushCall([this] { app_adapter->DoSoftQuit(); });
  } else {
    logic->event_loop()->PushCall([this] { logic->Shutdown(); });
  }
}

void BaseFeatureSet::PushMainThreadRunnable(Runnable* runnable) {
  app_adapter->DoPushMainThreadRunnable(runnable);
}

auto BaseFeatureSet::ClipboardIsSupported() -> bool {
  // We only call our actual virtual function once.
  if (!have_clipboard_is_supported_) {
    clipboard_is_supported_ = app_adapter->DoClipboardIsSupported();
    have_clipboard_is_supported_ = true;
  }
  return clipboard_is_supported_;
}

auto BaseFeatureSet::ClipboardHasText() -> bool {
  // If subplatform says they don't support clipboards, don't even ask.
  if (!ClipboardIsSupported()) {
    return false;
  }
  return app_adapter->DoClipboardHasText();
}

void BaseFeatureSet::ClipboardSetText(const std::string& text) {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardSetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  app_adapter->DoClipboardSetText(text);
}

auto BaseFeatureSet::ClipboardGetText() -> std::string {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardGetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  return app_adapter->DoClipboardGetText();
}

void BaseFeatureSet::SetAppActive(bool active) {
  assert(InMainThread());

  // Note: in some cases I'm seeing repeat active/inactive sets. For example
  // on Mac SDL if I hide the app and then click on it in the dock I get a
  // 'inactive' for the hide followed by a 'active', 'inactive', 'active' on
  // the dock click. So our strategy here to filter that out is just to tell
  // the logic thread that the value has changed but have them directly read
  // the shared atomic value, so they should generally skip over flip-flops
  // like that and instead just read the final value a few times in a row.

  g_core->platform->LowLevelDebugLog(
      "SetAppActive(" + std::to_string(active) + ")@"
      + std::to_string(core::CorePlatform::TimeMonotonicMillisecs()));

  // Issue a gentle warning if they are feeding us the same state twice in a
  // row; might imply faulty logic on an app-adapter or whatnot.
  if (app_active_set_ && app_active_ == active) {
    g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                         "SetAppActive called with state "
                             + std::to_string(active) + " twice in a row.");
  }
  app_active_set_ = true;
  app_active_ = active;

  g_base->logic->event_loop()->PushCall(
      [] { g_base->logic->OnAppActiveChanged(); });
}

void BaseFeatureSet::Reset() {
  ui->Reset();
  input->Reset();
  graphics->Reset();
  python->Reset();
  audio->Reset();
}

auto BaseFeatureSet::TimeSinceEpochCloudSeconds() -> seconds_t {
  // TODO(ericf): wire this up. Just using local time for now. And make sure
  // that this and utc_now_cloud() in the Python layer are synced up.
  return core::CorePlatform::TimeSinceEpochSeconds();
}

void BaseFeatureSet::SetUIScale(UIScale scale) {
  assert(InLogicThread());

  // Store the canonical value in UI.
  ui->SetUIScale(scale);

  // Let interested parties know that it has changed.
  graphics->OnUIScaleChange();
}

}  // namespace ballistica::base
