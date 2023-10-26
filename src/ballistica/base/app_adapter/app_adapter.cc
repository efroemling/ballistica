// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/app_adapter/app_adapter.h"

#if BA_OSTYPE_ANDROID  // Remove conditional once android sources are public.
#include "ballistica/base/app_adapter/app_adapter_android.h"
#endif
#include "ballistica/base/app_adapter/app_adapter_apple.h"
#include "ballistica/base/app_adapter/app_adapter_headless.h"
#include "ballistica/base/app_adapter/app_adapter_sdl.h"
#include "ballistica/base/app_adapter/app_adapter_vr.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/support/stress_test.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::base {

auto AppAdapter::Create() -> AppAdapter* {
  assert(g_core);

// TEMP - need to init sdl on our legacy mac build even though its not
// technically an SDL app. Kill this once the old mac build is gone.
#if BA_LEGACY_MACOS_BUILD
  AppAdapterSDL::InitSDL();
#endif

  AppAdapter* app_adapter{};

#if BA_HEADLESS_BUILD
  app_adapter = new AppAdapterHeadless();
#elif BA_OSTYPE_ANDROID
  app_adapter = new AppAdapterAndroid();
#elif BA_XCODE_BUILD
  app_adapter = new AppAdapterApple();
#elif BA_RIFT_BUILD
  // Rift build can spin up in either VR or regular mode.
  if (g_core->vr_mode) {
    app_adapter = new AppAdapterVR();
  } else {
    app_adapter = new AppAdapterSDL();
  }
#elif BA_CARDBOARD_BUILD
  app_adapter = new AppAdapterVR();
#elif BA_SDL_BUILD
  app_adapter = new AppAdapterSDL();
#else
#error No app adapter defined for this build.
#endif

  assert(app_adapter);
  return app_adapter;
}

AppAdapter::AppAdapter() = default;

AppAdapter::~AppAdapter() = default;

auto AppAdapter::ManagesMainThreadEventLoop() const -> bool { return true; }

void AppAdapter::OnMainThreadStartApp() {
  assert(g_base);
  assert(g_core);
  assert(g_core->InMainThread());

  // Add some common input devices where applicable. More specific ones (SDL
  // Joysticks, etc.) get added in subclasses.

  // FIXME: This stuff should probably go elsewhere.
  if (!g_core->HeadlessMode()) {
    // If we've got a nice themed hardware cursor, show it. Otherwise we'll
    // render it manually, which is laggier but gets the job done.
    // g_base->platform->SetHardwareCursorVisible(g_buildconfig.hardware_cursor());

    // On desktop systems we just assume keyboard input exists and add it
    // immediately.
    if (g_core->platform->IsRunningOnDesktop()) {
      g_base->input->PushCreateKeyboardInputDevices();
    }

    // On non-tv, non-desktop, non-vr systems, create a touchscreen input.
    if (!g_core->platform->IsRunningOnTV() && !g_core->IsVRMode()
        && !g_core->platform->IsRunningOnDesktop()) {
      g_base->input->CreateTouchInput();
    }
  }
}

void AppAdapter::OnAppStart() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppPause() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppResume() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppShutdown() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }
void AppAdapter::OnScreenSizeChange() { assert(g_base->InLogicThread()); }
void AppAdapter::DoApplyAppConfig() { assert(g_base->InLogicThread()); }

void AppAdapter::OnAppSuspend_() {
  assert(g_core->InMainThread());

  // IMPORTANT: Any pause related stuff that event-loop-threads need to do
  // should be done from their registered pause-callbacks. If we instead
  // push runnables to them from here they may or may not be called before
  // their event-loop is actually paused.

  // Pause all event loops.
  EventLoop::SetEventLoopsSuspended(true);

  if (g_base->network_reader) {
    g_base->network_reader->OnAppPause();
  }
  g_base->networking->OnAppPause();
}

void AppAdapter::OnAppUnsuspend_() {
  assert(g_core->InMainThread());

  // Spin all event-loops back up.
  EventLoop::SetEventLoopsSuspended(false);

  // Run resumes that expect to happen in the main thread.
  g_base->network_reader->OnAppResume();
  g_base->networking->OnAppResume();

  // When resuming from a suspended state, we may want to pause whatever
  // game was running when we last were active.
  //
  // TODO(efro): we should make this smarter so it doesn't happen if we're
  // in a network game or something that we can't pause; bringing up the
  // menu doesn't really accomplish anything there.
  //
  // In general this probably should be handled at a higher level.
  if (g_core->should_pause_active_game) {
    g_core->should_pause_active_game = false;

    // If we've been completely backgrounded, send a menu-press command to
    // the game; this will bring up a pause menu if we're in the game/etc.
    if (!g_base->ui->MainMenuVisible()) {
      g_base->ui->PushMainMenuPressCall(nullptr);
    }
  }
}

void AppAdapter::SuspendApp() {
  assert(g_core);
  assert(g_core->InMainThread());

  if (app_suspended_) {
    Log(LogLevel::kWarning,
        "AppAdapter::SuspendApp() called with app already suspended.");
    return;
  }

  millisecs_t start_time{core::CorePlatform::GetCurrentMillisecs()};

  // Apple mentioned 5 seconds to run stuff once backgrounded or they bring
  // down the hammer. Let's aim to stay under 2.
  millisecs_t max_duration{2000};

  g_core->platform->DebugLog(
      "SuspendApp@"
      + std::to_string(core::CorePlatform::GetCurrentMillisecs()));
  // assert(!app_pause_requested_);
  // app_pause_requested_ = true;
  app_suspended_ = true;
  OnAppSuspend_();
  // UpdatePauseResume_();

  // We assume that the OS will completely suspend our process the moment we
  // return from this call (though this is not technically true on all
  // platforms). So we want to spin and wait for threads to actually process
  // the pause message.
  size_t running_thread_count{};
  while (std::abs(core::CorePlatform::GetCurrentMillisecs() - start_time)
         < max_duration) {
    // If/when we get to a point with no threads waiting to be paused, we're
    // good to go.
    auto threads{EventLoop::GetStillSuspendingEventLoops()};
    running_thread_count = threads.size();
    if (running_thread_count == 0) {
      if (g_buildconfig.debug_build()) {
        Log(LogLevel::kDebug,
            "SuspendApp() completed in "
                + std::to_string(core::CorePlatform::GetCurrentMillisecs()
                                 - start_time)
                + "ms.");
      }
      return;
    }
  }

  // If we made it here, we timed out. Complain.
  Log(LogLevel::kError,
      std::string("SuspendApp() took too long; ")
          + std::to_string(running_thread_count)
          + " threads not yet paused after "
          + std::to_string(core::CorePlatform::GetCurrentMillisecs()
                           - start_time)
          + " ms.");
}

void AppAdapter::UnsuspendApp() {
  assert(g_core);
  assert(g_core->InMainThread());

  if (!app_suspended_) {
    Log(LogLevel::kWarning,
        "AppAdapter::UnsuspendApp() called with app not in paused state.");
    return;
  }
  millisecs_t start_time{core::CorePlatform::GetCurrentMillisecs()};
  g_core->platform->DebugLog(
      "UnsuspendApp@"
      + std::to_string(core::CorePlatform::GetCurrentMillisecs()));
  // assert(app_pause_requested_);
  // app_pause_requested_ = false;
  // UpdatePauseResume_();
  app_suspended_ = false;
  OnAppUnsuspend_();
  if (g_buildconfig.debug_build()) {
    Log(LogLevel::kDebug,
        "UnsuspendApp() completed in "
            + std::to_string(core::CorePlatform::GetCurrentMillisecs()
                             - start_time)
            + "ms.");
  }
}

void AppAdapter::RunMainThreadEventLoopToCompletion() {
  FatalError("RunMainThreadEventLoopToCompletion is not implemented here.");
}

void AppAdapter::DoExitMainThreadEventLoop() {
  FatalError("DoExitMainThreadEventLoop is not implemented here.");
}

auto AppAdapter::FullscreenControlAvailable() const -> bool { return false; }

auto AppAdapter::SupportsVSync() -> bool const { return false; }

auto AppAdapter::SupportsMaxFPS() -> bool const { return false; }

/// As a default, allow graphics stuff in the main thread.
auto AppAdapter::InGraphicsContext() -> bool { return g_core->InMainThread(); }

/// As a default, assume our main thread *is* our graphics context.
void AppAdapter::DoPushGraphicsContextRunnable(Runnable* runnable) {
  DoPushMainThreadRunnable(runnable);
}

auto AppAdapter::FullscreenControlGet() const -> bool {
  assert(g_base->InLogicThread());

  // By default, just go through config (assume we have full control over
  // the fullscreen state ourself).
  return g_base->app_config->Resolve(AppConfig::BoolID::kFullscreen);
}

void AppAdapter::FullscreenControlSet(bool fullscreen) {
  assert(g_base->InLogicThread());
  // By default, just set these in the config and apply it (assumes config
  // changes get plugged into actual fullscreen state).
  g_base->python->objs()
      .Get(fullscreen ? BasePython::ObjID::kSetConfigFullscreenOnCall
                      : BasePython::ObjID::kSetConfigFullscreenOffCall)
      .Call();
}

auto AppAdapter::FullscreenControlKeyShortcut() const
    -> std::optional<std::string> {
  return {};
}

void AppAdapter::CursorPositionForDraw(float* x, float* y) {
  assert(x && y);

  // By default, just use our latest event-delivered cursor position;
  // this should work everywhere though perhaps might not be most optimal.
  if (g_base->input == nullptr) {
    *x = 0.0f;
    *y = 0.0f;
    return;
  }
  *x = g_base->input->cursor_pos_x();
  *y = g_base->input->cursor_pos_y();
}

auto AppAdapter::ShouldUseCursor() -> bool { return true; }

auto AppAdapter::HasHardwareCursor() -> bool { return false; }

void AppAdapter::SetHardwareCursorVisible(bool visible) {}

auto AppAdapter::CanSoftQuit() -> bool { return false; }
auto AppAdapter::CanBackQuit() -> bool { return false; }
void AppAdapter::DoBackQuit() { FatalError("Fixme unimplemented."); }
void AppAdapter::DoSoftQuit() { FatalError("Fixme unimplemented."); }
void AppAdapter::TerminateApp() { FatalError("Fixme unimplemented."); }
auto AppAdapter::HasDirectKeyboardInput() -> bool { return false; }

void AppAdapter::ApplyGraphicsSettings(const GraphicsSettings* settings) {}

auto AppAdapter::GetGraphicsSettings() -> GraphicsSettings* {
  return new GraphicsSettings();
}

auto AppAdapter::GetGraphicsClientContext() -> GraphicsClientContext* {
  return new GraphicsClientContext();
}

auto AppAdapter::GetKeyRepeatDelay() -> float { return 0.3f; }
auto AppAdapter::GetKeyRepeatInterval() -> float { return 0.08f; }

auto AppAdapter::ClipboardIsSupported() -> bool {
  // We only call our actual virtual function once.
  if (!have_clipboard_is_supported_) {
    clipboard_is_supported_ = DoClipboardIsSupported();
    have_clipboard_is_supported_ = true;
  }
  return clipboard_is_supported_;
}

auto AppAdapter::ClipboardHasText() -> bool {
  // If subplatform says they don't support clipboards, don't even ask.
  if (!ClipboardIsSupported()) {
    return false;
  }
  return DoClipboardHasText();
}

void AppAdapter::ClipboardSetText(const std::string& text) {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardSetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  DoClipboardSetText(text);
}

auto AppAdapter::ClipboardGetText() -> std::string {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardGetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  return DoClipboardGetText();
}

auto AppAdapter::DoClipboardIsSupported() -> bool { return false; }

auto AppAdapter::DoClipboardHasText() -> bool {
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
  return false;
}

void AppAdapter::DoClipboardSetText(const std::string& text) {
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
}

auto AppAdapter::DoClipboardGetText() -> std::string {
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
  return "";
}

}  // namespace ballistica::base
