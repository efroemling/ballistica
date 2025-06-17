// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/app_adapter/app_adapter.h"

#include <string>

#include "ballistica/base/graphics/support/graphics_client_context.h"
#include "ballistica/base/graphics/support/graphics_settings.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

AppAdapter::AppAdapter() = default;

AppAdapter::~AppAdapter() = default;

auto AppAdapter::ManagesMainThreadEventLoop() const -> bool { return true; }

void AppAdapter::OnMainThreadStartApp() {
  assert(g_core);
  assert(g_core->InMainThread());
}

void AppAdapter::OnAppStart() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppSuspend() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppUnsuspend() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppShutdown() { assert(g_base->InLogicThread()); }
void AppAdapter::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }
void AppAdapter::OnScreenSizeChange() { assert(g_base->InLogicThread()); }
void AppAdapter::ApplyAppConfig() { assert(g_base->InLogicThread()); }

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

auto AppAdapter::GetKeyName(int keycode) -> std::string {
  BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
              "CorePlatform::GetKeyName not implemented here.");
  return "?";
}

auto AppAdapter::NativeReviewRequestSupported() -> bool { return false; }

void AppAdapter::NativeReviewRequest() {
  BA_PRECONDITION(NativeReviewRequestSupported());
  PushMainThreadCall([this] { DoNativeReviewRequest(); });
}

void AppAdapter::DoNativeReviewRequest() { FatalError("Fixme unimplemented."); }

auto AppAdapter::ShouldSilenceAudioForInactive() -> bool const { return false; }
auto AppAdapter::SupportsPurchases() -> bool { return false; }

}  // namespace ballistica::base
