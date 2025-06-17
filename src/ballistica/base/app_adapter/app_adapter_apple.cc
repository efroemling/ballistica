// Released under the MIT License. See LICENSE for details.
#if BA_XCODE_BUILD

#include "ballistica/base/app_adapter/app_adapter_apple.h"

#include <string>
#include <vector>

#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/apple/from_swift.h"
#include "ballistica/base/platform/support/min_sdl_key_names.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/event_loop.h"

// clang-format off
// This needs to be below ballistica headers since it relies on
// some types in them but does not include headers itself.
#include <BallisticaKit-Swift.h>
// clang-format on

namespace ballistica::base {

/// RAII-friendly way to mark the thread and calls we're allowed to run graphics
/// stuff in.
class AppAdapterApple::ScopedAllowGraphics_ {
 public:
  explicit ScopedAllowGraphics_(AppAdapterApple* adapter) : adapter_{adapter} {
    // We currently assume only one thread will be doing this at any given
    // time; will need to add a lock if that's not always the case.
    assert(!adapter_->graphics_allowed_);
    // Keep graphics thread updated each time through since it can change.
    adapter->graphics_thread_ = std::this_thread::get_id();
    adapter->graphics_allowed_ = true;
  }
  ~ScopedAllowGraphics_() {
    assert(adapter_->graphics_allowed_);
    adapter_->graphics_allowed_ = false;
  }

 private:
  AppAdapterApple* adapter_;
};

auto AppAdapterApple::ManagesMainThreadEventLoop() const -> bool {
  // Nope; we run under a standard Cocoa/UIKit environment and they call us;
  // we don't call them.
  return false;
}

void AppAdapterApple::DoPushMainThreadRunnable(Runnable* runnable) {
  // Kick this along to swift.
  BallisticaKit::FromCpp::pushRawRunnableToMain(runnable);
}

void AppAdapterApple::OnMainThreadStartApp() {
  AppAdapter::OnMainThreadStartApp();
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::onAppStart();
#endif
#if BA_USE_GAME_CENTER
  BallisticaKit::GameCenterContext::onAppStart();
#endif
}

void AppAdapterApple::ApplyAppConfig() { assert(g_base->InLogicThread()); }

void AppAdapterApple::ApplyGraphicsSettings(const GraphicsSettings* settings) {
  auto* graphics_server = g_base->graphics_server;

  // We need a full renderer reload if quality values have changed
  // or if we don't have a renderer yet.
  bool need_full_reload = ((graphics_server->texture_quality_requested()
                            != settings->texture_quality)
                           || (graphics_server->graphics_quality_requested()
                               != settings->graphics_quality));

  // We need a full renderer reload if quality values have changed or if we
  // don't yet have a renderer.

  if (need_full_reload) {
    ReloadRenderer_(settings);
  }
}

void AppAdapterApple::ReloadRenderer_(const GraphicsSettings* settings) {
  auto* gs = g_base->graphics_server;

  if (gs->renderer() && gs->renderer_loaded()) {
    gs->UnloadRenderer();
  }
  if (!gs->renderer()) {
    gs->set_renderer(new RendererGL());
  }

  // Update graphics quality based on request.
  gs->set_graphics_quality_requested(settings->graphics_quality);
  gs->set_texture_quality_requested(settings->texture_quality);

  // (Re)load stuff with these latest quality settings.
  gs->LoadRenderer();
}

auto AppAdapterApple::TryRender() -> bool {
  auto allow = ScopedAllowGraphics_(this);

  // Run & release any pending runnables.
  std::vector<Runnable*> calls;
  {
    // Pull calls off the list before running them; this way we only need to
    // grab the list lock for a moment.
    auto lock = std::scoped_lock(graphics_calls_mutex_);
    if (!graphics_calls_.empty()) {
      graphics_calls_.swap(calls);
    }
  }
  for (auto* call : calls) {
    call->RunAndLogErrors();
    delete call;
  }

  // Lastly, render.
  auto result = g_base->graphics_server->TryRender();

  // A little trick to make mac resizing look a lot smoother. Because we
  // render in a background thread, we often don't render at the most up to
  // date window size during a window resize. Normally this makes our image
  // jerk around in an ugly way, but if we just re-render once or twice in
  // those cases we mostly always get the most up to date window size.
  if (result && resize_friendly_frames_ > 0) {
    // Leave this enabled for just a few frames every time it is set.
    // (so just in case it breaks we won't draw each frame serveral times for
    // eternity).
    resize_friendly_frames_ -= 1;

    // Keep on drawing until the drawn window size
    // matches what we have (or until we try for too long or fail at drawing).
    seconds_t start_time = g_core->AppTimeSeconds();
    for (int i = 0; i < 5; ++i) {
      bool size_differs =
          ((std::abs(resize_target_resolution_.x
                     - g_base->graphics_server->screen_pixel_width())
            > 0.01f)
           || (std::abs(resize_target_resolution_.y
                        - g_base->graphics_server->screen_pixel_height())
               > 0.01f));
      if (size_differs && g_core->AppTimeSeconds() - start_time < 0.1
          && result) {
        result = g_base->graphics_server->TryRender();
      }
    }
  }

  return result;
}

void AppAdapterApple::EnableResizeFriendlyMode(int width, int height) {
  resize_friendly_frames_ = 5;
  resize_target_resolution_ = Vector2f(width, height);
}

auto AppAdapterApple::InGraphicsContext() -> bool {
  return std::this_thread::get_id() == graphics_thread_ && graphics_allowed_;
}

void AppAdapterApple::DoPushGraphicsContextRunnable(Runnable* runnable) {
  auto lock = std::scoped_lock(graphics_calls_mutex_);
  if (graphics_calls_.size() > 1000) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError, "graphics_calls_ got too big.");
  }
  graphics_calls_.push_back(runnable);
}

auto AppAdapterApple::ShouldUseCursor() -> bool {
  // On Mac of course we want our nice custom hardware cursor.
  if (g_buildconfig.platform_macos()) {
    return true;
  }

  // Anywhere else (iOS, tvOS, etc.) just say no cursor for now. The OS may
  // draw one in some cases (trackpad connected to iPad, etc.) but we don't
  // interfere and just let the OS draw its normal cursor in that case. Can
  // revisit this later if that becomes a more common scenario.
  return false;
}

auto AppAdapterApple::HasHardwareCursor() -> bool {
  // Mac should be only build getting called here (see ShouldUseCursor).
  assert(g_buildconfig.platform_macos());

  return true;
}

void AppAdapterApple::SetHardwareCursorVisible(bool visible) {
  // (mac should be only build getting called here)
  assert(g_buildconfig.platform_macos());
  assert(g_core->InMainThread());

#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::setCursorVisible(visible);
#endif
}

void AppAdapterApple::TerminateApp() {
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::terminateApp();
#else
  AppAdapter::TerminateApp();
#endif
}

auto AppAdapterApple::FullscreenControlAvailable() const -> bool {
  // Currently Mac only. Any window-management stuff elsewhere such as
  // iPadOS is out of our hands.
  if (g_buildconfig.platform_macos()) {
    return true;
  }
  return false;
}

auto AppAdapterApple::FullscreenControlGet() const -> bool {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::getMainWindowIsFullscreen();
#else
  return false;
#endif
}

void AppAdapterApple::FullscreenControlSet(bool fullscreen) {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::setMainWindowFullscreen(fullscreen);
#endif
}

auto AppAdapterApple::FullscreenControlKeyShortcut() const
    -> std::optional<std::string> {
  return "fn+F";
}

auto AppAdapterApple::HasDirectKeyboardInput() -> bool { return true; };

auto AppAdapterApple::GetKeyRepeatDelay() -> float {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::getKeyRepeatDelay();
#else
  return AppAdapter::GetKeyRepeatDelay();
#endif
}

auto AppAdapterApple::GetKeyRepeatInterval() -> float {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::getKeyRepeatInterval();
#else
  return AppAdapter::GetKeyRepeatDelay();
#endif
}

auto AppAdapterApple::DoClipboardIsSupported() -> bool {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::clipboardIsSupported();
#else
  return AppAdapter::DoClipboardIsSupported();
#endif
}

auto AppAdapterApple::DoClipboardHasText() -> bool {
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::clipboardHasText();
#else
  return AppAdapter::DoClipboardHasText();
#endif
}

void AppAdapterApple::DoClipboardSetText(const std::string& text) {
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::clipboardSetText(text);
#else
  AppAdapter::DoClipboardSetText(text);
#endif
}

auto AppAdapterApple::DoClipboardGetText() -> std::string {
#if BA_PLATFORM_MACOS
  auto contents = BallisticaKit::CocoaFromCpp::clipboardGetText();
  if (contents) {
    return std::string(contents.get());
  }
  throw Exception("No text on clipboard.");
#else
  return AppAdapter::DoClipboardGetText();
#endif
}

auto AppAdapterApple::GetKeyName(int keycode) -> std::string {
  return MinSDL_GetKeyName(keycode);
}

auto AppAdapterApple::NativeReviewRequestSupported() -> bool {
  // StoreKit currently supports this everywhere except tvOS.
  if (g_buildconfig.xcode_build() && g_buildconfig.use_store_kit()
      && !g_buildconfig.platform_tvos()) {
    return true;
  }
  return false;
}

void AppAdapterApple::DoNativeReviewRequest() {
#if BA_XCODE_BUILD && BA_USE_STORE_KIT && !BA_PLATFORM_TVOS
  BallisticaKit::StoreKitContext::requestReview();
#else
  FatalError("This should not be getting called.");
#endif
}

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD
