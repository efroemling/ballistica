// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/app/app.h"

#include "ballistica/core/thread.h"
#include "ballistica/game/game.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/input/device/touch_input.h"
#include "ballistica/input/input.h"
#include "ballistica/networking/network_reader.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/python/python.h"

namespace ballistica {

App::App(Thread* thread) : Module("app", thread) {
  assert(g_app == nullptr);
  g_app = this;

  // So anyone who needs to use the 'main' thread id can get at it...
  Thread::UpdateMainThreadID();

  // We modify some app behavior when run under the server manager.
  auto* envval = getenv("BA_SERVER_WRAPPER_MANAGED");
  server_wrapper_managed_ = (envval && strcmp(envval, "1") == 0);
}

void App::PostInit() {
  // If we've got a nice themed hardware cursor, show it.
  // Otherwise hide the hardware cursor; we'll draw it in software.
  // (need to run this in postinit because SDL/etc may not be inited yet
  // as of App::App().
  g_platform->SetHardwareCursorVisible(g_buildconfig.hardware_cursor());
}

App::~App() = default;

auto App::UsesEventLoop() const -> bool {
  // We have 2 redundant values for essentially the same thing;
  // should get rid of IsEventPushMode() once we've created
  // App subclasses for our various platforms.
  return !g_platform->IsEventPushMode();
}

void App::PushInterruptSignalSetupCall() {
  g_platform->SetupInterruptHandling();
}

void App::RunRenderUpkeepCycle() {
  // This should only be used in cases where the OS is handling the event loop.
  assert(!UsesEventLoop());
  if (UsesEventLoop()) {
    return;
  }

  // Pump thread messages (we're being driven by frame-draw callbacks
  // so this is the only place that it gets done at).
  thread()->RunEventLoop(true);  // Single pass only.

  // Now do the general app event cycle for whoever needs to process things.
  RunEvents();
}

void App::RebuildLostGLContext() {
  assert(InMainThread());
  assert(g_graphics_server);
  if (g_graphics_server) {
    g_graphics_server->RebuildLostContext();
  }
}

void App::DrawFrame(bool during_resize) {
  assert(InMainThread());

  // Its possible to receive frames before we're ready to draw.
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

void App::SetScreenResolution(float width, float height) {
  assert(InMainThread());
  if (!HeadlessMode()) {
    g_graphics_server->VideoResize(width, height);
  }
}

void App::PushShutdownCompleteCall() {
  PushCall([this] { ShutdownComplete(); });
}

void App::ShutdownComplete() {
  assert(g_platform);

  // Need to call our cleanup stuff that would otherwise get called in main.
  g_platform->FinalCleanup();

  done_ = true;

  // Kill our own event loop (or tell the OS to kill its).
  if (UsesEventLoop()) {
    thread()->Quit();
  } else {
    g_platform->QuitApp();
  }
}

void App::RunEvents() {
  if (!HeadlessMode()) {
    // there's probably a better place for this...
    UpdateStressTesting();
  }

  // Give platforms a chance to pump/handle their own events.
  // FIXME: now that we have app class overrides, platform should really
  //  not be doing event handling. (need to fix rift build).
  g_platform->RunEvents();
}

void App::UpdatePauseResume() {
  if (actually_paused_) {
    // Unpause if no one wants pause.
    if (!sys_paused_app_ && !user_paused_app_) {
      OnResume();
      actually_paused_ = false;
    }
  } else {
    // Pause if anyone wants.
    if (sys_paused_app_ || user_paused_app_) {
      OnPause();
      actually_paused_ = true;
    }
  }
}

void App::OnPause() {
  assert(InMainThread());

  // Avoid reading gyro values for a short time to avoid hitches when restored.
  g_graphics->SetGyroEnabled(false);

  // IMPORTANT: Any on-pause related stuff that threads need to do must
  // must be done from their HandleThreadPause(). If we push runnables to them
  // they may or may not be called before the thread is actually paused.

  Thread::SetThreadsPaused(true);

  assert(g_networking);
  g_networking->Pause();

  assert(g_network_reader);
  if (g_network_reader) {
    g_network_reader->Pause();
  }

  if (g_app_globals->telnet_server) {
    g_app_globals->telnet_server->Pause();
  }

  g_platform->OnAppPause();
}

void App::OnResume() {
  assert(InMainThread());
  last_app_resume_time_ = GetRealTime();
  Thread::SetThreadsPaused(false);

  g_platform->OnAppResume();
  g_networking->Resume();
  g_network_reader->Resume();

  if (g_app_globals->telnet_server) {
    g_app_globals->telnet_server->Resume();
  }

  // Also let the Python layer do what it needs to
  // (starting/stopping music, etc).
  g_python->PushObjCall(Python::ObjID::kHandleAppResumeCall);
  g_game->PushOnAppResumeCall();

  g_graphics->SetGyroEnabled(true);

  // When resuming from a paused state, we may want to
  // pause whatever game was running when we last were active.
  // TODO(efro): we should make this smarter so it doesn't happen if
  // we're in a network game or something that we can't pause;
  // bringing up the menu doesn't really accomplish anything there.
  if (g_app_globals->should_pause) {
    g_app_globals->should_pause = false;

    // If we've been completely backgrounded,
    // send a menu-press command to the game; this will
    // bring up a pause menu if we're in the game/etc.
    g_game->PushMainMenuPressCall(nullptr);
  }
}

auto App::GetProductPrice(const std::string& product) -> std::string {
  std::lock_guard<std::mutex> lock(product_prices_mutex_);
  auto i = product_prices_.find(product);
  if (i == product_prices_.end()) {
    return "";
  } else {
    return i->second;
  }
}

void App::SetProductPrice(const std::string& product,
                          const std::string& price) {
  std::lock_guard<std::mutex> lock(product_prices_mutex_);
  product_prices_[product] = price;
}

void App::PauseApp() {
  assert(InMainThread());
  Platform::DebugLog("PauseApp@"
                     + std::to_string(Platform::GetCurrentMilliseconds()));
  assert(!sys_paused_app_);
  sys_paused_app_ = true;
  UpdatePauseResume();
}

void App::ResumeApp() {
  assert(InMainThread());
  Platform::DebugLog("ResumeApp@"
                     + std::to_string(Platform::GetCurrentMilliseconds()));
  assert(sys_paused_app_);
  sys_paused_app_ = false;
  UpdatePauseResume();
}

void App::DidFinishRenderingFrame(FrameDef* frame) {}

void App::PrimeEventPump() {
  assert(!UsesEventLoop());

  // Pump events manually until a screen gets created.
  // At that point we use frame-draws to drive our event loop.
  while (!g_graphics_server->initial_screen_created()) {
    g_main_thread->RunEventLoop(true);
    Platform::SleepMS(1);
  }
}

#pragma mark Push-Calls

void App::PushShowOnlineScoreUICall(const std::string& show,
                                    const std::string& game,
                                    const std::string& game_version) {
  PushCall([this, show, game, game_version] {
    assert(InMainThread());
    g_platform->ShowOnlineScoreUI(show, game, game_version);
  });
}

void App::PushNetworkSetupCall(int port, int telnet_port, bool enable_telnet,
                               const std::string& telnet_password) {
  PushCall([this, port, telnet_port, enable_telnet, telnet_password] {
    assert(InMainThread());
    // Kick these off if they don't exist.
    // (do we want to support changing ports on existing ones?)
    if (g_network_reader == nullptr) {
      new NetworkReader(port);
    }
    if (g_app_globals->telnet_server == nullptr && enable_telnet) {
      new TelnetServer(telnet_port);
      assert(g_app_globals->telnet_server);
      if (telnet_password.empty()) {
        g_app_globals->telnet_server->SetPassword(nullptr);
      } else {
        g_app_globals->telnet_server->SetPassword(telnet_password.c_str());
      }
    }
  });
}

void App::PushPurchaseAckCall(const std::string& purchase,
                              const std::string& order_id) {
  PushCall([this, purchase, order_id] {
    g_platform->PurchaseAck(purchase, order_id);
  });
}

void App::PushGetScoresToBeatCall(const std::string& level,
                                  const std::string& config,
                                  void* py_callback) {
  PushCall([this, level, config, py_callback] {
    assert(InMainThread());
    g_platform->GetScoresToBeat(level, config, py_callback);
  });
}

void App::PushPurchaseCall(const std::string& item) {
  PushCall([this, item] {
    assert(InMainThread());
    g_platform->Purchase(item);
  });
}

void App::PushRestorePurchasesCall() {
  PushCall([this] {
    assert(InMainThread());
    g_platform->RestorePurchases();
  });
}

void App::PushOpenURLCall(const std::string& url) {
  PushCall([this, url] { g_platform->OpenURL(url); });
}

void App::PushGetFriendScoresCall(const std::string& game,
                                  const std::string& game_version, void* data) {
  PushCall([this, game, game_version, data] {
    g_platform->GetFriendScores(game, game_version, data);
  });
}

void App::PushSubmitScoreCall(const std::string& game,
                              const std::string& game_version, int64_t score) {
  PushCall([this, game, game_version, score] {
    g_platform->SubmitScore(game, game_version, score);
  });
}

void App::PushAchievementReportCall(const std::string& achievement) {
  PushCall([this, achievement] { g_platform->ReportAchievement(achievement); });
}

void App::PushStringEditCall(const std::string& name, const std::string& value,
                             int max_chars) {
  PushCall([this, name, value, max_chars] {
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

void App::PushSetStressTestingCall(bool enable, int player_count) {
  PushCall([this, enable, player_count] {
    bool was_stress_testing = stress_testing_;
    stress_testing_ = enable;
    stress_test_player_count_ = player_count;

    // If we're turning on, reset our intervals and things.
    if (!was_stress_testing && stress_testing_) {
      // So our first sample is 1 interval from now...
      last_stress_test_update_time_ = GetRealTime();
      // Reset our frames-rendered tally.
      if (g_graphics && g_graphics_server->renderer()) {
        last_total_frames_rendered_ =
            g_graphics_server->renderer()->total_frames_rendered();
      } else {
        // Assume zero if there's no graphics yet.
        last_total_frames_rendered_ = 0;
      }
    }
  });
}

void App::PushResetAchievementsCall() {
  PushCall([this] { g_platform->ResetAchievements(); });
}

void App::OnBootstrapComplete() {
  assert(InMainThread());
  assert(g_input);

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

void App::PushCursorUpdate(bool vis) {
  PushCall([this, vis] {
    assert(InMainThread());
    g_platform->SetHardwareCursorVisible(vis);
  });
}

void App::UpdateStressTesting() {
  // Handle a little misc stuff here.
  // If we're currently running stress-tests, update that stuff.
  if (stress_testing_ && g_input) {
    // Update our fake inputs to make our dudes run around.
    g_input->ProcessStressTesting(stress_test_player_count_);

    // Every 10 seconds update our stress-test stats.
    millisecs_t t = GetRealTime();
    if (t - last_stress_test_update_time_ >= 10000) {
      if (stress_test_stats_file_ == nullptr) {
        assert(g_platform);
        std::string f_name =
            g_platform->GetUserPythonDirectory() + "/stress_test_stats.csv";
        stress_test_stats_file_ = g_platform->FOpen(f_name.c_str(), "wb");
        if (stress_test_stats_file_ != nullptr) {
          fprintf(stress_test_stats_file_,
                  "time,averageFps,nodes,models,collideModels,textures,sounds,"
                  "pssMem,sharedDirtyMem,privateDirtyMem\n");
          fflush(stress_test_stats_file_);
          if (g_buildconfig.ostype_android()) {
            // On android, let the OS know we've added or removed a file
            // (limit to android or we'll get an unimplemented warning)
            g_platform->AndroidRefreshFile(f_name);
          }
        }
      }
      if (stress_test_stats_file_ != nullptr) {
        // See how many frames we've rendered this past interval.
        int total_frames_rendered;
        if (g_graphics && g_graphics_server->renderer()) {
          total_frames_rendered =
              g_graphics_server->renderer()->total_frames_rendered();
        } else {
          total_frames_rendered = last_total_frames_rendered_;
        }
        float avg =
            static_cast<float>(total_frames_rendered
                               - last_total_frames_rendered_)
            / (static_cast<float>(t - last_stress_test_update_time_) / 1000.0f);
        last_total_frames_rendered_ = total_frames_rendered;
        uint32_t model_count = 0;
        uint32_t collide_model_count = 0;
        uint32_t texture_count = 0;
        uint32_t sound_count = 0;
        uint32_t node_count = 0;
        if (g_media) {
          model_count = g_media->total_model_count();
          collide_model_count = g_media->total_collide_model_count();
          texture_count = g_media->total_texture_count();
          sound_count = g_media->total_sound_count();
        }
        assert(g_game);
        std::string mem_usage = g_platform->GetMemUsageInfo();
        fprintf(stress_test_stats_file_, "%d,%.1f,%d,%d,%d,%d,%d,%s\n",
                static_cast<int>(GetRealTime()), avg, node_count, model_count,
                collide_model_count, texture_count, sound_count,
                mem_usage.c_str());
        fflush(stress_test_stats_file_);
      }
      last_stress_test_update_time_ = t;
    }
  }
}

}  // namespace ballistica
