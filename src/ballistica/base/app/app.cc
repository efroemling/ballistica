// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/app/app.h"

#include "ballistica/base/app/stress_test.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/input/device/touch_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::base {

App::App(EventLoop* event_loop)
    : event_loop_(event_loop), stress_test_(std::make_unique<StressTest>()) {
  // We modify some app behavior when run under the server manager.
  auto* envval = getenv("BA_SERVER_WRAPPER_MANAGED");
  server_wrapper_managed_ = (envval && strcmp(envval, "1") == 0);
}

void App::PostInit() {
  // Sanity check: make sure asserts are stripped out of release builds
  // (NDEBUG should do this).
#if !BA_DEBUG_BUILD
#ifndef NDEBUG
#error Expected NDEBUG to be defined for release builds.
#endif  // NDEBUG
  assert(true);
#endif  // !BA_DEBUG_BUILD

  g_core->user_agent_string = g_core->platform->GetUserAgentString();
}

void App::LogicThreadApplyAppConfig() {
  // Note: this gets called in the logic thread since that's where
  // config reading happens. We should grab whatever values we need
  // and then forward them to ourself in the main thread.
  // We also can give our other main-thread-based subsystems a chance
  // to do the same.
  assert(g_base->InLogicThread());

  g_base->networking->ApplyAppConfig();
}

void App::LogicThreadStepDisplayTime() { assert(g_base->InLogicThread()); }

auto App::ManagesEventLoop() const -> bool {
  // We have 2 redundant values for essentially the same thing;
  // should get rid of IsEventPushMode() once we've created
  // App subclasses for our various platforms.
  return !g_core->platform->IsEventPushMode();
}

void App::RunRenderUpkeepCycle() {
  // This should only be used in cases where the OS is handling the event loop.
  assert(!ManagesEventLoop());
  if (ManagesEventLoop()) {
    return;
  }

  // Pump thread messages (we're being driven by frame-draw callbacks
  // so this is the only place that it gets done at).
  event_loop()->RunEventLoop(true);  // Single pass only.

  // Now do the general app event cycle for whoever needs to process things.
  RunEvents();
}

void App::RebuildLostGLContext() {
  assert(g_base->InGraphicsThread());
  assert(g_base->graphics_server);
  if (g_base->graphics_server) {
    g_base->graphics_server->RebuildLostContext();
  }
}

void App::DrawFrame(bool during_resize) {
  assert(g_base->InGraphicsThread());

  // It's possible to receive frames before we're ready to draw.
  if (!g_base->graphics_server || !g_base->graphics_server->renderer()) {
    return;
  }

  millisecs_t starttime = g_core->GetAppTimeMillisecs();

  // A resize-draw event means that we're drawing due to a window resize.
  // In this case we ignore regular draw events for a short while
  // afterwards which makes resizing smoother.
  // FIXME: should figure out the *correct* way to handle this;
  //  I believe the underlying cause here is some sort of context contention
  //  across threads.
  if (during_resize) {
    last_resize_draw_event_time_ = starttime;
  } else {
    if (starttime - last_resize_draw_event_time_ < (1000 / 30)) {
      return;
    }
  }
  g_base->graphics_server->TryRender();
  RunRenderUpkeepCycle();
}

void App::LogicThreadShutdownComplete() {
  assert(g_core->InMainThread());
  assert(g_core);

  done_ = true;

  // Kill our own event loop (or tell the OS to kill its).
  if (ManagesEventLoop()) {
    event_loop()->Quit();
  } else {
    g_core->platform->QuitApp();
  }
}

void App::RunEvents() {
  // there's probably a better place for this...
  stress_test_->Update();

  // Give platforms a chance to pump/handle their own events.
  // FIXME: now that we have app class overrides, platform should really
  //  not be doing event handling. (need to fix rift build).
  g_core->platform->RunEvents();
}

void App::UpdatePauseResume() {
  if (actually_paused_) {
    // Unpause if no one wants pause.
    if (!sys_paused_app_) {
      OnAppResume();
      actually_paused_ = false;
    }
  } else {
    // OnAppPause if anyone wants.
    if (sys_paused_app_) {
      OnAppPause();
      actually_paused_ = true;
    }
  }
}

void App::OnAppPause() {
  assert(g_core->InMainThread());

  // IMPORTANT: Any pause related stuff that event-loop-threads need to do
  // should be done from their registered pause-callbacks. If we instead push
  // runnables to them from here they may or may not be called before their
  // event-loop is actually paused.

  // Pause all event loops.
  EventLoop::SetThreadsPaused(true);

  if (g_base->network_reader) {
    g_base->network_reader->OnAppPause();
  }
  g_base->networking->OnAppPause();
  g_core->platform->OnAppPause();
}

void App::OnAppResume() {
  assert(g_core->InMainThread());
  last_app_resume_time_ = g_core->GetAppTimeMillisecs();

  // Spin all event-loops back up.
  EventLoop::SetThreadsPaused(false);

  // Run resumes that expect to happen in the main thread.
  g_core->platform->OnAppResume();
  g_base->network_reader->OnAppResume();
  g_base->networking->OnAppResume();

  // When resuming from a paused state, we may want to
  // pause whatever game was running when we last were active.
  // TODO(efro): we should make this smarter so it doesn't happen if
  //  we're in a network game or something that we can't pause;
  //  bringing up the menu doesn't really accomplish anything there.
  if (g_core->should_pause) {
    g_core->should_pause = false;

    // If we've been completely backgrounded,
    // send a menu-press command to the game; this will
    // bring up a pause menu if we're in the game/etc.
    if (!g_base->ui->MainMenuVisible()) {
      g_base->ui->PushMainMenuPressCall(nullptr);
    }
  }
}

auto App::GetProductPrice(const std::string& product) -> std::string {
  std::scoped_lock lock(product_prices_mutex_);
  auto i = product_prices_.find(product);
  if (i == product_prices_.end()) {
    return "";
  } else {
    return i->second;
  }
}

void App::SetProductPrice(const std::string& product,
                          const std::string& price) {
  std::scoped_lock lock(product_prices_mutex_);
  product_prices_[product] = price;
}

void App::PauseApp() {
  assert(g_core);
  assert(g_core->InMainThread());
  millisecs_t start_time{core::CorePlatform::GetCurrentMillisecs()};

  // Apple mentioned 5 seconds to run stuff once backgrounded or
  // they bring down the hammer. Let's aim to stay under 2.
  millisecs_t max_duration{2000};

  g_core->platform->DebugLog(
      "PauseApp@" + std::to_string(core::CorePlatform::GetCurrentMillisecs()));
  assert(!sys_paused_app_);
  sys_paused_app_ = true;
  UpdatePauseResume();

  // We assume that the OS will completely suspend our process the moment
  // we return from this call (though this is not technically true on all
  // platforms). So we want to spin and wait for threads to actually
  // process the pause message.
  size_t running_thread_count{};
  while (std::abs(core::CorePlatform::GetCurrentMillisecs() - start_time)
         < max_duration) {
    // If/when we get to a point with no threads waiting to be paused,
    // we're good to go.
    auto threads{EventLoop::GetStillPausingThreads()};
    running_thread_count = threads.size();
    if (running_thread_count == 0) {
      if (g_buildconfig.debug_build()) {
        Log(LogLevel::kDebug,
            "PauseApp() completed in "
                + std::to_string(core::CorePlatform::GetCurrentMillisecs()
                                 - start_time)
                + "ms.");
      }
      return;
    }
  }

  // If we made it here, we timed out. Complain.
  Log(LogLevel::kError,
      std::string("PauseApp() took too long; ")
          + std::to_string(running_thread_count)
          + " threads not yet paused after "
          + std::to_string(core::CorePlatform::GetCurrentMillisecs()
                           - start_time)
          + " ms.");
}

void App::ResumeApp() {
  assert(g_core && g_core->InMainThread());
  millisecs_t start_time{core::CorePlatform::GetCurrentMillisecs()};
  g_core->platform->DebugLog(
      "ResumeApp@" + std::to_string(core::CorePlatform::GetCurrentMillisecs()));
  assert(sys_paused_app_);
  sys_paused_app_ = false;
  UpdatePauseResume();
  if (g_buildconfig.debug_build()) {
    Log(LogLevel::kDebug,
        "ResumeApp() completed in "
            + std::to_string(core::CorePlatform::GetCurrentMillisecs()
                             - start_time)
            + "ms.");
  }
}

void App::DidFinishRenderingFrame(FrameDef* frame) {}

void App::PrimeMainThreadEventPump() {
  assert(!ManagesEventLoop());

  // Pump events manually until a screen gets created.
  // At that point we use frame-draws to drive our event loop.
  while (!g_base->graphics_server->initial_screen_created()) {
    event_loop()->RunEventLoop(true);
    core::CorePlatform::SleepMillisecs(1);
  }
}

#pragma mark Push-Calls

// FIXME - move this call to Platform.
void App::PushShowOnlineScoreUICall(const std::string& show,
                                    const std::string& game,
                                    const std::string& game_version) {
  event_loop()->PushCall([show, game, game_version] {
    assert(g_core->InMainThread());
    g_core->platform->ShowOnlineScoreUI(show, game, game_version);
  });
}

void App::PushPurchaseAckCall(const std::string& purchase,
                              const std::string& order_id) {
  event_loop()->PushCall([purchase, order_id] {
    g_base->platform->PurchaseAck(purchase, order_id);
  });
}

void App::PushPurchaseCall(const std::string& item) {
  event_loop()->PushCall([item] {
    assert(g_core->InMainThread());
    g_base->platform->Purchase(item);
  });
}

void App::PushRestorePurchasesCall() {
  event_loop()->PushCall([] {
    assert(g_core->InMainThread());
    g_base->platform->RestorePurchases();
  });
}

void App::PushOpenURLCall(const std::string& url) {
  event_loop()->PushCall([url] { g_base->platform->OpenURL(url); });
}

void App::PushSubmitScoreCall(const std::string& game,
                              const std::string& game_version, int64_t score) {
  event_loop()->PushCall([game, game_version, score] {
    g_core->platform->SubmitScore(game, game_version, score);
  });
}

void App::PushAchievementReportCall(const std::string& achievement) {
  event_loop()->PushCall(
      [achievement] { g_core->platform->ReportAchievement(achievement); });
}

void App::PushStringEditCall(const std::string& name, const std::string& value,
                             int max_chars) {
  event_loop()->PushCall([name, value, max_chars] {
    static millisecs_t last_edit_time = 0;
    millisecs_t t = g_core->GetAppTimeMillisecs();

    // Ignore if too close together.
    // (in case second request comes in before first takes effect).
    if (t - last_edit_time < 1000) {
      return;
    }
    last_edit_time = t;
    assert(g_core->InMainThread());
    g_core->platform->EditText(name, value, max_chars);
  });
}

void App::PushSetStressTestingCall(bool enable, int player_count) {
  event_loop()->PushCall([this, enable, player_count] {
    stress_test_->Set(enable, player_count);
  });
}

void App::PushResetAchievementsCall() {
  event_loop()->PushCall([] { g_core->platform->ResetAchievements(); });
}

void App::OnMainThreadStartApp() {
  assert(g_base);
  assert(g_core);
  assert(g_core->InMainThread());

  // If we've got a nice themed hardware cursor, show it.
  // Otherwise, hide the hardware cursor; we'll draw it in software.
  // (need to run this in postinit because SDL/etc. may not be inited yet
  // as of App::App()).
  g_core->platform->SetHardwareCursorVisible(g_buildconfig.hardware_cursor());

  if (!g_core->HeadlessMode()) {
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

void App::PushCursorUpdate(bool vis) {
  event_loop()->PushCall([vis] {
    assert(g_core && g_core->InMainThread());
    g_core->platform->SetHardwareCursorVisible(vis);
  });
}

}  // namespace ballistica::base
