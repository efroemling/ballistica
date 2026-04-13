// Released under the MIT License. See LICENSE for details.
#if BA_HEADLESS_BUILD

#include "ballistica/base/app_adapter/app_adapter_headless.h"

#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/support/graphics_client_context.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

AppAdapterHeadless::AppAdapterHeadless() {}

void AppAdapterHeadless::OnMainThreadStartApp() {
  assert(g_core->InMainThread());

  // We're not embedded into any sort of event system, so we just
  // spin up our very own event loop for the main thread.
  main_event_loop_ =
      new EventLoop(EventLoopID::kMain, ThreadSource::kWrapCurrent);
}

void AppAdapterHeadless::ApplyAppConfig() {}

void AppAdapterHeadless::RunMainThreadEventLoopToCompletion() {
  assert(g_core->InMainThread());
  main_event_loop_->RunToCompletion();
}

void AppAdapterHeadless::DoPushMainThreadRunnable(Runnable* runnable) {
  main_event_loop_->PushRunnable(runnable);
}

void AppAdapterHeadless::DoExitMainThreadEventLoop() {
  assert(g_core->InMainThread());
  main_event_loop_->Exit();
}

auto AppAdapterHeadless::GetGraphicsClientContext() -> GraphicsClientContext* {
  // Special dummy form.
  return new GraphicsClientContext(0);
}

}  // namespace ballistica::base

#endif  // BA_HEADLESS_BUILD
