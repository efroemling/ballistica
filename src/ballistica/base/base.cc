// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/base.h"

#include "ballistica/base/app/app.h"
#include "ballistica/base/app/app_config.h"
#include "ballistica/base/app/app_mode_empty.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/assets_server.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/base/networking/network_writer.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_feature_set_data.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/huffman.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/base/support/stdio_console.h"
#include "ballistica/base/ui/console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/logging.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica::base {

core::CoreFeatureSet* g_core{};
BaseFeatureSet* g_base{};

BaseFeatureSet::BaseFeatureSet()
    : python{new BasePython()},
      platform{BasePlatform::CreatePlatform()},
      audio{new Audio()},
      utils{new Utils()},
      logic{new Logic()},
      huffman{new Huffman()},
      ui{new UI()},
      networking{new Networking()},
      app{BasePlatform::CreateApp()},
      context_ref{new ContextRef(nullptr)},
      network_reader{new NetworkReader()},
      network_writer{new NetworkWriter()},
      assets_server{new AssetsServer()},
      bg_dynamics{g_core->HeadlessMode() ? nullptr : new BGDynamics},
      bg_dynamics_server{g_core->HeadlessMode() ? nullptr
                                                : new BGDynamicsServer},
      app_config{new AppConfig()},
      graphics{BasePlatform::CreateGraphics()},
      graphics_server{new GraphicsServer()},
      input{new Input()},
      text_graphics{new TextGraphics()},
      audio_server{new AudioServer()},
      assets{new Assets()},
      app_mode_{AppModeEmpty::GetSingleton()},
      basn_log_behavior_{g_core->platform->GetEnv("BASNLOG") == "1"},
      stdio_console{g_buildconfig.enable_stdio_console() ? new StdioConsole()
                                                         : nullptr} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_base == nullptr);
}

void BaseFeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported. Like any
  // normal Python module, we take this opportunity to import/create the
  // stuff we use.

  // Importing core should always be the first thing we do. Various
  // ballistica functionality will fail if this has not been done.
  assert(g_core == nullptr);
  g_core = core::CoreFeatureSet::Import();

  g_core->LifecycleLog("_babase exec begin");

  // Want to run this at the last possible moment before spinning up our
  // BaseFeatureSet. This locks in baenv customizations.
  g_core->python->ApplyBaEnvConfig();

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
  // others to 'import' our C++ front end.
  g_base->StoreOnPythonModule(module);

  // Import all the Python stuff we use.
  g_base->python->ImportPythonObjs();

  // Run some sanity checks, wire up our log handler, etc.
  auto result = g_base->python->objs()
                    .Get(BasePython::ObjID::kOnNativeModuleImportCall)
                    .Call();
  if (!result.Exists()) {
    FatalError("babase._env.on_native_module_import() call failed.");
  }

  // ..and because Python is now feeding us logs, we can push any logs
  // through that we've been holding on to and start forwarding log calls as
  // they happen.
  g_core->python->EnablePythonLoggingCalls();

  // Marker we pop down at the very end so other modules can run sanity
  // checks to make sure we aren't importing them reciprocally when they
  // import us.
  Python::MarkReachedEndOfModule(module);
  assert(!g_base->base_native_import_completed_);
  g_base->base_native_import_completed_ = true;

  g_core->LifecycleLog("_babase exec end");
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

void BaseFeatureSet::OnAssetsAvailable() {
  assert(InLogicThread());
  assert(console_ == nullptr);

  // Spin up the in-app console.
  if (!g_core->HeadlessMode()) {
    console_ = new Console();

    // Print any messages that have built up.
    if (!console_startup_messages_.empty()) {
      console_->Print(console_startup_messages_);
      console_startup_messages_.clear();
    }
  }
}

void BaseFeatureSet::StartApp() {
  BA_PRECONDITION(g_core->InMainThread());
  BA_PRECONDITION(g_base);

  // Currently limiting this to once per process.
  BA_PRECONDITION(!called_start_app_);
  called_start_app_ = true;
  assert(!app_started_);  // Shouldn't be possible.

  g_core->LifecycleLog("start-app begin (main thread)");

  LogVersionInfo();

  // Read in ba.app.config for anyone who wants to start looking at it
  // (though we don't explicitly ask anyone to apply it until later).
  python->ReadConfig();

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
  app->OnMainThreadStartApp();

  // Take note that we're now 'running'. Various code such as anything that
  // pushes messages to threads can watch for this state to avoid crashing
  // if called early.
  app_started_ = true;

  // Inform anyone who wants to know that we're done starting.
  platform->OnMainThreadStartAppComplete();

  // As the last step of this phase, tell the logic thread to apply the app
  // config which will kick off screen creation and otherwise get the ball
  // rolling.
  {
    Python::ScopedInterpreterLock gil;
    python->objs().Get(BasePython::ObjID::kPushApplyAppConfigCall).Call();
  }

  g_core->LifecycleLog("start-app end (main thread)");
}

void BaseFeatureSet::LogVersionInfo() {
  char buffer[256];
  if (g_buildconfig.headless_build()) {
    snprintf(buffer, sizeof(buffer), "BallisticaKit Headless %s build %d.",
             kEngineVersion, kEngineBuildNumber);
  } else {
    snprintf(buffer, sizeof(buffer), "BallisticaKit %s build %d.",
             kEngineVersion, kEngineBuildNumber);
  }
  Log(LogLevel::kInfo, buffer);
}

void BaseFeatureSet::set_app_mode(AppMode* mode) {
  assert(InLogicThread());

  // Make an exception here for empty mode since that's in place before an
  // app mode is officially set.
  if (mode == app_mode_ && mode != AppModeEmpty::GetSingleton()) {
    Log(LogLevel::kWarning,
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

auto BaseFeatureSet::AppManagesEventLoop() -> bool {
  return app->ManagesEventLoop();
}

void BaseFeatureSet::RunAppToCompletion() {
  BA_PRECONDITION(g_core->InMainThread());
  BA_PRECONDITION(g_base);
  BA_PRECONDITION(g_base->app->ManagesEventLoop());
  BA_PRECONDITION(!called_run_app_to_completion_);
  called_run_app_to_completion_ = true;

  // Start things moving if not done yet.
  if (!called_start_app_) {
    StartApp();
  }

  // On our event-loop-managing platforms we now simply sit in our event
  // loop until the app is quit.
  g_core->main_event_loop()->RunEventLoop(false);
}

void BaseFeatureSet::PrimeAppMainThreadEventPump() {
  app->PrimeMainThreadEventPump();
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

void BaseFeatureSet::set_plus(PlusSoftInterface* plus) {
  assert(plus_soft_ == nullptr);
  plus_soft_ = plus;
}

/// Access the plus feature-set. Will throw an exception if not present.
auto BaseFeatureSet::plus() -> PlusSoftInterface* {
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

auto BaseFeatureSet::HaveUIV1() -> bool {
  if (!ui_v1_soft_ && !tried_importing_ui_v1_) {
    python->SoftImportUIV1();
    // Important to set this *after* import attempt, or a second import
    // attempt while first is ongoing can insta-fail. Multiple import
    // attempts shouldn't hurt anything.
    tried_importing_ui_v1_ = true;
  }
  return ui_v1_soft_ != nullptr;
}

/// Access the plus feature-set. Will throw an exception if not present.
auto BaseFeatureSet::ui_v1() -> UIV1SoftInterface* {
  if (!ui_v1_soft_ && !tried_importing_ui_v1_) {
    python->SoftImportUIV1();
    // Important to set this *after* import attempt, or a second import
    // attempt while first is ongoing can insta-fail. Multiple import
    // attempts shouldn't hurt anything.
    tried_importing_ui_v1_ = true;
  }
  if (!ui_v1_soft_) {
    throw Exception("ui_v1 feature-set not present.");
  }
  return ui_v1_soft_;
}

void BaseFeatureSet::set_ui_v1(UIV1SoftInterface* ui_v1) {
  assert(ui_v1_soft_ == nullptr);
  ui_v1_soft_ = ui_v1;
}

auto BaseFeatureSet::GetAppInstanceUUID() -> const std::string& {
  static std::string app_instance_uuid;
  static bool have_app_instance_uuid = false;

  if (!have_app_instance_uuid) {
    if (g_base) {
      Python::ScopedInterpreterLock gil;
      auto uuid =
          g_base->python->objs().Get(BasePython::ObjID::kUUIDStrCall).Call();
      if (uuid.Exists()) {
        app_instance_uuid = uuid.ValueAsString();
        have_app_instance_uuid = true;
      }
    }
    if (!have_app_instance_uuid) {
      // As an emergency fallback simply use a single random number. We
      // should probably simply disallow this before Python is up.
      Log(LogLevel::kWarning, "GetSessionUUID() using rand fallback.");
      srand(static_cast<unsigned int>(
          core::CorePlatform::GetCurrentMillisecs()));  // NOLINT
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
    return plus()->IsUnmodifiedBlessedBuild();
  }
  return false;
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

auto BaseFeatureSet::InGraphicsThread() const -> bool {
  if (auto* loop = graphics_server->event_loop()) {
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

void BaseFeatureSet::ScreenMessage(const std::string& s,
                                   const Vector3f& color) {
  logic->event_loop()->PushCall(
      [this, s, color] { graphics->AddScreenMessage(s, color); });
}

void BaseFeatureSet::DoV1CloudLog(const std::string& msg) {
  // We may attempt to import stuff and that should *never* happen before
  // base is fully imported.
  if (!IsBaseCompletelyImported()) {
    printf(
        "WARNING: V1CloudLog called before babase fully imported; ignoring.\n");
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
    printf("WARNING: V1CloudLog direct-sends not available; ignoring.\n");
    return;
  }

  // Only attempt direct sends a few times.
  if (g_early_v1_cloud_log_writes <= 0) {
    return;
  }

  // Ok; going ahead with the direct send.
  g_early_v1_cloud_log_writes -= 1;
  std::string logprefix = "EARLY-LOG:";
  std::string logsuffix;

  // If we're an early enough error, our global log isn't even available,
  // so include this whole message as a suffix instead.
  if (g_core == nullptr) {
    logsuffix = msg;
  }
  plus()->DirectSendV1CloudLogs(logprefix, logsuffix, false, nullptr);
}

void BaseFeatureSet::PushConsolePrintCall(const std::string& msg) {
  // Completely ignore this stuff in headless mode.
  if (g_core->HeadlessMode()) {
    return;
  }
  // If our event loop AND console are up and running, ship it off to
  // be printed. Otherwise store it for the console to grab when it's ready.
  if (auto* event_loop = logic->event_loop()) {
    if (console_ != nullptr) {
      event_loop->PushCall([this, msg] { console_->Print(msg); });
      return;
    }
  }
  // Didn't send a print; store for later.
  console_startup_messages_ += msg;
}

PyObject* BaseFeatureSet::GetPyExceptionType(PyExcType exctype) {
  switch (exctype) {
    case PyExcType::kContext:
      return python->objs().Get(BasePython::ObjID::kContextError).Get();
    case PyExcType::kNotFound:
      return python->objs().Get(BasePython::ObjID::kNotFoundError).Get();
    case PyExcType::kNodeNotFound:
      return python->objs().Get(BasePython::ObjID::kNodeNotFoundError).Get();
    case PyExcType::kSessionPlayerNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kSessionPlayerNotFoundError)
          .Get();
    case PyExcType::kInputDeviceNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kInputDeviceNotFoundError)
          .Get();
    case PyExcType::kDelegateNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kDelegateNotFoundError)
          .Get();
    case PyExcType::kWidgetNotFound:
      return python->objs().Get(BasePython::ObjID::kWidgetNotFoundError).Get();
    case PyExcType::kActivityNotFound:
      return python->objs()
          .Get(BasePython::ObjID::kActivityNotFoundError)
          .Get();
    case PyExcType::kSessionNotFound:
      return python->objs().Get(BasePython::ObjID::kSessionNotFoundError).Get();
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
    PrintContextNonLogicThread();
  } else if (const char* label = Python::ScopedCallLabel::current_label()) {
    PrintContextForCallableLabel(label);
  } else if (PythonCommand* cmd = PythonCommand::current_command()) {
    cmd->PrintContext();
  } else if (PythonContextCall* call = PythonContextCall::current_call()) {
    call->PrintContext();
  } else {
    PrintContextUnavailable();
  }
}
void BaseFeatureSet::PrintContextNonLogicThread() {
  std::string s = std::string(
      "  root call: <not in logic thread; context_ref unavailable>");
  PySys_WriteStderr("%s\n", s.c_str());
}

void BaseFeatureSet::PrintContextForCallableLabel(const char* label) {
  assert(InLogicThread());
  assert(label);
  std::string s = std::string("  root call: ") + label + "\n";
  s += Python::GetContextBaseString();
  PySys_WriteStderr("%s\n", s.c_str());
}

void BaseFeatureSet::PrintContextUnavailable() {
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
        LogLevel::kError,
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

}  // namespace ballistica::base
