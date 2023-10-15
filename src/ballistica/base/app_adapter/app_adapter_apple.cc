// Released under the MIT License. See LICENSE for details.
#if BA_XCODE_BUILD

#include "ballistica/base/app_adapter/app_adapter_apple.h"

#include <BallisticaKit-Swift.h>

#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

/// RAII-friendly way to mark the thread and calls we're allowed to run graphics
/// stuff in.
class AppAdapterApple::ScopedAllowGraphics_ {
 public:
  explicit ScopedAllowGraphics_(AppAdapterApple* adapter) : adapter_{adapter} {
    assert(!adapter_->graphics_allowed_);
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
  BallisticaKit::FromCppPushRawRunnableToMain(runnable);
}

void AppAdapterApple::DoApplyAppConfig() {
  assert(g_base->InLogicThread());

  g_base->graphics_server->PushSetScreenPixelScaleCall(
      g_base->app_config->Resolve(AppConfig::FloatID::kScreenPixelScale));

  auto graphics_quality_requested =
      g_base->graphics->GraphicsQualityFromAppConfig();

  auto texture_quality_requested =
      g_base->graphics->TextureQualityFromAppConfig();

  g_base->app_adapter->PushGraphicsContextCall([=] {
    SetScreen_(texture_quality_requested, graphics_quality_requested);
  });
}

void AppAdapterApple::SetScreen_(
    TextureQualityRequest texture_quality_requested,
    GraphicsQualityRequest graphics_quality_requested) {
  // If we know what we support, filter our request types to what is
  // supported. This will keep us from rebuilding contexts if request type
  // is flipping between different types that we don't support.
  if (g_base->graphics->has_supports_high_quality_graphics_value()) {
    if (!g_base->graphics->supports_high_quality_graphics()
        && graphics_quality_requested > GraphicsQualityRequest::kMedium) {
      graphics_quality_requested = GraphicsQualityRequest::kMedium;
    }
  }

  auto* gs = g_base->graphics_server;

  // We need a full renderer reload if quality values have changed or if we
  // don't have one yet.
  bool need_full_reload =
      ((gs->texture_quality_requested() != texture_quality_requested)
       || (gs->graphics_quality_requested() != graphics_quality_requested)
       || !gs->texture_quality_set() || !gs->graphics_quality_set());

  if (need_full_reload) {
    ReloadRenderer_(graphics_quality_requested, texture_quality_requested);
  }

  // Let the logic thread know we've got a graphics system up and running.
  // It may use this cue to kick off asset loads and other bootstrapping.
  g_base->logic->event_loop()->PushCall(
      [] { g_base->logic->OnGraphicsReady(); });
}

void AppAdapterApple::ReloadRenderer_(
    GraphicsQualityRequest graphics_quality_requested,
    TextureQualityRequest texture_quality_requested) {
  auto* gs = g_base->graphics_server;

  if (gs->renderer() && gs->renderer_loaded()) {
    gs->UnloadRenderer();
  }
  if (!gs->renderer()) {
    gs->set_renderer(new RendererGL());
  }

  // Set a dummy screen resolution to start with. The main thread will kick
  // along the latest real resolution just before each frame draw, but we
  // need *something* here or else we'll get errors due to framebuffers
  // getting made at size 0/etc.
  g_base->graphics_server->SetScreenResolution(320.0, 240.0);

  // Update graphics quality based on request.
  gs->set_graphics_quality_requested(graphics_quality_requested);
  gs->set_texture_quality_requested(texture_quality_requested);

  // (Re)load stuff with these latest quality settings.
  gs->LoadRenderer();
}

void AppAdapterApple::UpdateScreenSizes_() {
  assert(g_base->app_adapter->InGraphicsContext());
}

void AppAdapterApple::SetScreenResolution(float pixel_width,
                                          float pixel_height) {
  auto allow = ScopedAllowGraphics_(this);
  g_base->graphics_server->SetScreenResolution(pixel_width, pixel_height);
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
  // Lastly render.
  return g_base->graphics_server->TryRender();

  return true;
}

auto AppAdapterApple::InGraphicsContext() -> bool {
  return std::this_thread::get_id() == graphics_thread_ && graphics_allowed_;
}

void AppAdapterApple::DoPushGraphicsContextRunnable(Runnable* runnable) {
  auto lock = std::scoped_lock(graphics_calls_mutex_);
  if (graphics_calls_.size() > 1000) {
    BA_LOG_ONCE(LogLevel::kError, "graphics_calls_ got too big.");
  }
  graphics_calls_.push_back(runnable);
}

auto AppAdapterApple::ShouldUseCursor() -> bool {
  // On Mac of course we want our nice custom hardware cursor.
  if (g_buildconfig.ostype_macos()) {
    return true;
  }

  // Anywhere else (iOS, tvOS, etc.) just say no cursor for now. The OS may
  // draw one in some cases (trackpad connected to iPad, etc.) but we don't
  // interfere and just let the OS draw its normal cursor in that case. Can
  // revisit this later if that becomes a more common scenario.
  return false;
}

auto AppAdapterApple::HasHardwareCursor() -> bool {
  // (mac should be only build getting called here)
  assert(g_buildconfig.ostype_macos());

  return true;
}

void AppAdapterApple::SetHardwareCursorVisible(bool visible) {
  // (mac should be only build getting called here)
  assert(g_buildconfig.ostype_macos());
  assert(g_core->InMainThread());

#if BA_OSTYPE_MACOS
  BallisticaKit::CocoaFromCppSetCursorVisible(visible);
#endif
}

void AppAdapterApple::TerminateApp() {
#if BA_OSTYPE_MACOS
  BallisticaKit::CocoaFromCppTerminateApp();
#else
  AppAdapter::TerminateApp();
#endif
}

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD
