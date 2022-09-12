// Released under the MIT License. See LICENSE for details.

#include "ballistica/app/app_flavor.h"

#include "ballistica/app/stress_test.h"
#include "ballistica/core/thread.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/input/device/touch_input.h"
#include "ballistica/input/input.h"
#include "ballistica/logic/logic.h"
#include "ballistica/networking/network_reader.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/python/python.h"

namespace ballistica {

AppFlavor::AppFlavor(Thread* thread)
    : thread_(thread), stress_test_(std::make_unique<StressTest>()) {
  // We modify some app behavior when run under the server manager.
  auto* envval = getenv("BA_SERVER_WRAPPER_MANAGED");
  server_wrapper_managed_ = (envval && strcmp(envval, "1") == 0);
}

void AppFlavor::PostInit() {
  // Sanity check: make sure asserts are stripped out of release builds
  // (NDEBUG should do this).
#if !BA_DEBUG_BUILD
#ifndef NDEBUG
#error Expected NDEBUG to be defined for release builds.
#endif  // NDEBUG
  assert(true);
#endif  // !BA_DEBUG_BUILD

  g_app->user_agent_string = g_platform->GetUserAgentString();

  // Figure out where our data is and chdir there.
  g_platform->SetupDataDirectory();

  // Run these just to make sure these dirs exist.
  // (otherwise they might not get made if nothing writes to them).
  g_platform->GetConfigDirectory();
  g_platform->GetUserPythonDirectory();
}

auto AppFlavor::ManagesEventLoop() const -> bool {
  // We have 2 redundant values for essentially the same thing;
  // should get rid of IsEventPushMode() once we've created
  // AppFlavor subclasses for our various platforms.
  return !g_platform->IsEventPushMode();
}

void AppFlavor::RunRenderUpkeepCycle() {
  // This should only be used in cases where the OS is handling the event loop.
  assert(!ManagesEventLoop());
  if (ManagesEventLoop()) {
    return;
  }

  // Pump thread messages (we're being driven by frame-draw callbacks
  // so this is the only place that it gets done at).
  thread()->RunEventLoop(true);  // Single pass only.

  // Now do the general app event cycle for whoever needs to process things.
  RunEvents();
}

void AppFlavor::RebuildLostGLContext() {
  assert(InMainThread());
  assert(g_graphics_server);
  if (g_graphics_server) {
    g_graphics_server->RebuildLostContext();
  }
}

void AppFlavor::DrawFrame(bool during_resize) {
  assert(InMainThread());

  // It's possible to receive frames before we're ready to draw.
  if (!g_graphics_server || !g_graphics_server->renderer()) {
    return;
  }

  millisecs_t starttime = GetRealTime();

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
  g_graphics_server->TryRender();
  RunRenderUpkeepCycle();
}

void AppFlavor::SetScreenResolution(float width, float height) {
  assert(InMainThread());
  if (!HeadlessMode()) {
    g_graphics_server->VideoResize(width, height);
  }
}

void AppFlavor::PushShutdownCompleteCall() {
  thread()->PushCall([this] { ShutdownComplete(); });
}

void AppFlavor::ShutdownComplete() {
  assert(InMainThread());
  assert(g_platform);

  done_ = true;

  // Kill our own event loop (or tell the OS to kill its).
  if (ManagesEventLoop()) {
    thread()->Quit();
  } else {
    g_platform->QuitApp();
  }
}

void AppFlavor::RunEvents() {
  // there's probably a better place for this...
  stress_test_->Update();

  // Give platforms a chance to pump/handle their own events.
  // FIXME: now that we have app class overrides, platform should really
  //  not be doing event handling. (need to fix rift build).
  g_platform->RunEvents();
}

void AppFlavor::UpdatePauseResume() {
  if (actually_paused_) {
    // Unpause if no one wants pause.
    if (!sys_paused_app_) {
      OnResume();
      actually_paused_ = false;
    }
  } else {
    // Pause if anyone wants.
    if (sys_paused_app_) {
      OnPause();
      actually_paused_ = true;
    }
  }
}

void AppFlavor::OnPause() {
  assert(InMainThread());

  // Avoid reading gyro values for a short time to avoid hitches when restored.
  g_graphics->SetGyroEnabled(false);

  // IMPORTANT: Any on-pause related stuff that threads need to do must
  // be done from registered pause-callbacks. If we instead push runnables
  // to them from here they may or may not be called before the thread
  // is actually paused.

  Thread::SetThreadsPaused(true);

  assert(g_networking);
  g_networking->Pause();

  assert(g_network_reader);
  if (g_network_reader) {
    g_network_reader->Pause();
  }

  if (g_app->telnet_server) {
    g_app->telnet_server->Pause();
  }

  g_platform->OnAppPause();
}

void AppFlavor::OnResume() {
  assert(InMainThread());
  last_app_resume_time_ = GetRealTime();
  Thread::SetThreadsPaused(false);

  g_platform->OnAppResume();
  g_networking->Resume();
  g_network_reader->Resume();

  if (g_app->telnet_server) {
    g_app->telnet_server->Resume();
  }

  // Also let the Python layer do what it needs to
  // (starting/stopping music, etc.).
  g_python->PushObjCall(Python::ObjID::kHandleAppResumeCall);
  g_logic->PushOnAppResumeCall();

  g_graphics->SetGyroEnabled(true);

  // When resuming from a paused state, we may want to
  // pause whatever game was running when we last were active.
  // TODO(efro): we should make this smarter so it doesn't happen if
  // we're in a network game or something that we can't pause;
  // bringing up the menu doesn't really accomplish anything there.
  if (g_app->should_pause) {
    g_app->should_pause = false;

    // If we've been completely backgrounded,
    // send a menu-press command to the game; this will
    // bring up a pause menu if we're in the game/etc.
    g_logic->PushMainMenuPressCall(nullptr);
  }
}

auto AppFlavor::GetProductPrice(const std::string& product) -> std::string {
  std::scoped_lock lock(product_prices_mutex_);
  auto i = product_prices_.find(product);
  if (i == product_prices_.end()) {
    return "";
  } else {
    return i->second;
  }
}

void AppFlavor::SetProductPrice(const std::string& product,
                                const std::string& price) {
  std::scoped_lock lock(product_prices_mutex_);
  product_prices_[product] = price;
}

void AppFlavor::PauseApp() {
  assert(InMainThread());
  Platform::DebugLog("PauseApp@"
                     + std::to_string(Platform::GetCurrentMilliseconds()));
  assert(!sys_paused_app_);
  sys_paused_app_ = true;
  UpdatePauseResume();
}

void AppFlavor::ResumeApp() {
  assert(InMainThread());
  Platform::DebugLog("ResumeApp@"
                     + std::to_string(Platform::GetCurrentMilliseconds()));
  assert(sys_paused_app_);
  sys_paused_app_ = false;
  UpdatePauseResume();
}

void AppFlavor::DidFinishRenderingFrame(FrameDef* frame) {}

void AppFlavor::PrimeEventPump() {
  assert(!ManagesEventLoop());

  // Pump events manually until a screen gets created.
  // At that point we use frame-draws to drive our event loop.
  while (!g_graphics_server->initial_screen_created()) {
    thread()->RunEventLoop(true);
    Platform::SleepMS(1);
  }
}

#pragma mark Push-Calls

void AppFlavor::PushShowOnlineScoreUICall(const std::string& show,
                                          const std::string& game,
                                          const std::string& game_version) {
  thread()->PushCall([show, game, game_version] {
    assert(InMainThread());
    g_platform->ShowOnlineScoreUI(show, game, game_version);
  });
}

void AppFlavor::PushNetworkSetupCall(int port, int telnet_port,
                                     bool enable_telnet,
                                     const std::string& telnet_password) {
  thread()->PushCall([port, telnet_port, enable_telnet, telnet_password] {
    assert(InMainThread());
    // Kick these off if they don't exist.
    // (do we want to support changing ports on existing ones?)
    if (g_network_reader == nullptr) {
      new NetworkReader(port);
    }
    if (g_app->telnet_server == nullptr && enable_telnet) {
      new TelnetServer(telnet_port);
      assert(g_app->telnet_server);
      if (telnet_password.empty()) {
        g_app->telnet_server->SetPassword(nullptr);
      } else {
        g_app->telnet_server->SetPassword(telnet_password.c_str());
      }
    }
  });
}

void AppFlavor::PushPurchaseAckCall(const std::string& purchase,
                                    const std::string& order_id) {
  thread()->PushCall(
      [purchase, order_id] { g_platform->PurchaseAck(purchase, order_id); });
}

void AppFlavor::PushPurchaseCall(const std::string& item) {
  thread()->PushCall([item] {
    assert(InMainThread());
    g_platform->Purchase(item);
  });
}

void AppFlavor::PushRestorePurchasesCall() {
  thread()->PushCall([] {
    assert(InMainThread());
    g_platform->RestorePurchases();
  });
}

void AppFlavor::PushOpenURLCall(const std::string& url) {
  thread()->PushCall([url] { g_platform->OpenURL(url); });
}

void AppFlavor::PushGetFriendScoresCall(const std::string& game,
                                        const std::string& game_version,
                                        void* data) {
  thread()->PushCall([game, game_version, data] {
    g_platform->GetFriendScores(game, game_version, data);
  });
}

void AppFlavor::PushSubmitScoreCall(const std::string& game,
                                    const std::string& game_version,
                                    int64_t score) {
  thread()->PushCall([game, game_version, score] {
    g_platform->SubmitScore(game, game_version, score);
  });
}

void AppFlavor::PushAchievementReportCall(const std::string& achievement) {
  thread()->PushCall(
      [achievement] { g_platform->ReportAchievement(achievement); });
}

void AppFlavor::PushStringEditCall(const std::string& name,
                                   const std::string& value, int max_chars) {
  thread()->PushCall([name, value, max_chars] {
    static millisecs_t last_edit_time = 0;
    millisecs_t t = GetRealTime();

    // Ignore if too close together.
    // (in case second request comes in before first takes effect).
    if (t - last_edit_time < 1000) {
      return;
    }
    last_edit_time = t;
    assert(InMainThread());
    g_platform->EditText(name, value, max_chars);
  });
}

void AppFlavor::PushSetStressTestingCall(bool enable, int player_count) {
  thread()->PushCall([this, enable, player_count] {
    stress_test_->SetStressTesting(enable, player_count);
  });
}

void AppFlavor::PushResetAchievementsCall() {
  thread()->PushCall([] { g_platform->ResetAchievements(); });
}

void AppFlavor::OnAppStart() {
  assert(InMainThread());
  assert(g_input);

  // If we're running in a terminal, print some info.
  if (g_platform->is_stdin_a_terminal()) {
    if (g_buildconfig.headless_build()) {
      printf("BallisticaCore Headless %s build %d.\n", kAppVersion,
             kAppBuildNumber);
      fflush(stdout);
    } else {
      printf("BallisticaCore %s build %d.\n", kAppVersion, kAppBuildNumber);
      fflush(stdout);
    }
  }

  // If we've got a nice themed hardware cursor, show it.
  // Otherwise, hide the hardware cursor; we'll draw it in software.
  // (need to run this in postinit because SDL/etc. may not be inited yet
  // as of AppFlavor::AppFlavor()).
  g_platform->SetHardwareCursorVisible(g_buildconfig.hardware_cursor());

  if (!HeadlessMode()) {
    // On desktop systems we just assume keyboard input exists and add it
    // immediately.
    if (g_platform->IsRunningOnDesktop()) {
      g_input->PushCreateKeyboardInputDevices();
    }

    // On non-tv, non-desktop, non-vr systems, create a touchscreen input.
    if (!g_platform->IsRunningOnTV() && !IsVRMode()
        && !g_platform->IsRunningOnDesktop()) {
      g_input->CreateTouchInput();
    }
  }
}

void AppFlavor::PushCursorUpdate(bool vis) {
  thread()->PushCall([vis] {
    assert(InMainThread());
    g_platform->SetHardwareCursorVisible(vis);
  });
}

}  // namespace ballistica
