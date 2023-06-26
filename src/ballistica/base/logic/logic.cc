// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/logic/logic.h"

#include "ballistica/base/app/app.h"
#include "ballistica/base/app/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/base/ui/console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

Logic::Logic() : display_timers_(new TimerList()) {
  // Enable display-time debug logs via env var.
  auto val = g_core->platform->GetEnv("BA_DEBUG_LOG_DISPLAY_TIME");
  if (val && *val == "1") {
    debug_log_display_time_ = true;
  }
}

void Logic::OnMainThreadStartApp() {
  event_loop_ = new EventLoop(EventLoopID::kLogic);
  g_core->pausable_event_loops.push_back(event_loop_);

  // Sit and wait for our logic thread to run its startup stuff.
  event_loop_->PushCallSynchronous([this] { OnAppStart(); });
}

void Logic::OnAppStart() {
  assert(g_base->InLogicThread());
  g_core->LifecycleLog("on-app-start begin (logic thread)");
  try {
    // Our thread should not be holding the GIL here at the start (and
    // probably not have any Python state at all). So here we set both
    // of those up.
    assert(!PyGILState_Check());
    PyGILState_Ensure();

    // Code running in the logic thread holds the GIL by default.
    event_loop_->SetAcquiresPythonGIL();

    // Keep informed when our thread's event loop is pausing/unpausing.
    event_loop_->AddPauseCallback(
        NewLambdaRunnableUnmanaged([this] { OnAppPause(); }));
    event_loop_->AddResumeCallback(
        NewLambdaRunnableUnmanaged([this] { OnAppResume(); }));

    // Running in a specific order here and should try to stick to it in
    // other OnAppXXX callbacks so any subsystem interdependencies behave
    // consistently. When pausing or shutting-down we use the opposite order for
    // the same reason. Let's do Python last (or first when pausing, etc) since
    // it will be the most variable; that way it will interact with other
    // subsystems in their normal states which is less likely to lead to
    // problems.
    g_base->graphics->OnAppStart();
    g_base->audio->OnAppStart();
    g_base->input->OnAppStart();
    g_base->ui->OnAppStart();
    g_core->platform->OnAppStart();
    g_base->app_mode()->OnAppStart();
    if (g_base->HavePlus()) {
      g_base->plus()->OnAppStart();
    }
    g_base->python->OnAppStart();
  } catch (const std::exception& e) {
    // If anything went wrong, trigger a deferred error.
    // This way it is more likely we can show a fatal error dialog
    // since the main thread won't be blocking waiting for us to init.
    std::string what = e.what();
    this->event_loop()->PushCall([what] {
      // Just throw a std exception since our 'what' probably already
      // contains a stack trace; if we throw a ballistica Exception we
      // wind up with a useless second one.
      throw std::logic_error(what.c_str());
    });
  }
  g_core->LifecycleLog("on-app-start end (logic thread)");
}

void Logic::OnAppPause() {
  assert(g_base->CurrentContext().IsEmpty());

  // Note: keep these in opposite order of OnAppStart.
  g_base->python->OnAppPause();
  if (g_base->HavePlus()) {
    g_base->plus()->OnAppPause();
  }
  g_base->app_mode()->OnAppPause();
  g_core->platform->OnAppPause();
  g_base->ui->OnAppPause();
  g_base->input->OnAppPause();
  g_base->audio->OnAppPause();
  g_base->graphics->OnAppPause();
}

void Logic::OnAppResume() {
  assert(g_base->CurrentContext().IsEmpty());

  // Note: keep these in the same order as OnAppStart.
  g_base->graphics->OnAppResume();
  g_base->audio->OnAppResume();
  g_base->input->OnAppResume();
  g_base->ui->OnAppResume();
  g_core->platform->OnAppResume();
  g_base->app_mode()->OnAppResume();
  if (g_base->HavePlus()) {
    g_base->plus()->OnAppResume();
  }
  g_base->python->OnAppResume();
}

void Logic::OnAppShutdown() {
  assert(g_core);
  assert(g_base->CurrentContext().IsEmpty());

  // Nuke the app from orbit if we get stuck while shutting down.
  g_core->StartSuicideTimer("shutdown", 10000);

  // Note: keep these in opposite order of OnAppStart.
  g_base->python->OnAppShutdown();
  if (g_base->HavePlus()) {
    g_base->plus()->OnAppShutdown();
  }
  g_base->app_mode()->OnAppShutdown();
  g_core->platform->OnAppResume();
  g_base->ui->OnAppShutdown();
  g_base->input->OnAppShutdown();
  g_base->audio->OnAppShutdown();
  g_base->graphics->OnAppShutdown();

  // FIXME: Should add a mechanism where we give the above subsystems
  //  a short bit of time to complete shutdown if they need it.
  //  For now just completing instantly.
  g_base->app->event_loop()->PushCall(
      [] { g_base->app->LogicThreadShutdownComplete(); });
}

void Logic::DoApplyAppConfig() {
  assert(g_base->InLogicThread());

  // Give all our other subsystems a chance.
  // Note: keep these in the same order as OnAppStart.
  g_base->graphics->DoApplyAppConfig();
  g_base->audio->DoApplyAppConfig();
  g_base->input->DoApplyAppConfig();
  g_base->ui->DoApplyAppConfig();
  g_core->platform->DoApplyAppConfig();
  g_base->app_mode()->DoApplyAppConfig();
  if (g_base->HavePlus()) {
    g_base->plus()->DoApplyAppConfig();
  }
  g_base->python->DoApplyAppConfig();

  // Give the app subsystem a chance too even though its main-thread based.
  // We call it here in the logic thread, allowing it to read whatever
  // it needs and pass it to itself in the main thread.
  g_base->app->DoLogicThreadApplyAppConfig();

  applied_app_config_ = true;
}

void Logic::OnInitialScreenCreated() {
  assert(g_base->InLogicThread());

  // Ok; graphics-server is telling us we've got a screen
  // (or no screen in the case of headless-mode).
  // We use this as a cue to kick off our business logic.

  // Let the Python layer know what's up. It will probably flip to
  // 'Launching' state.
  CompleteAppBootstrapping();

  // Push an initial frame to the graphics thread. From this point it will be
  // self-sustaining; sending us a request for a new one each time it receives
  // one we send it.
  if (!g_core->HeadlessMode()) {
    g_base->graphics->BuildAndPushFrameDef();
  }
}

// Launch into main menu or whatever else.
void Logic::CompleteAppBootstrapping() {
  assert(g_base->InLogicThread());
  assert(g_base->CurrentContext().IsEmpty());

  assert(!app_bootstrapping_complete_);
  app_bootstrapping_complete_ = true;

  g_core->LifecycleLog("app bootstrapping complete");

  // Let the assets system know it can start loading stuff now that
  // we have a screen and thus know texture formats/etc.
  // TODO(ericf): It might be nice to kick this off earlier if our logic is
  //  robust enough to create some sort of 'null' textures/meshes before
  //  the renderer is ready and then seamlessly create renderer-specific
  //  ones once the renderer is up. We could likely at least get a lot
  //  of preloads done in the meantime. Though this would require preloads
  //  to be renderer-agnostic; not sure if that's the case.
  g_base->assets->StartLoading();

  // Let base know it can create the console or other asset-dependent things.
  g_base->OnAssetsAvailable();

  // Set up our timers.
  process_pending_work_timer_ = event_loop()->NewTimer(
      0, true, NewLambdaRunnable([this] { ProcessPendingWork(); }));
  asset_prune_timer_ = event_loop()->NewTimer(
      2345, true, NewLambdaRunnable([] { g_base->assets->Prune(); }));

  // Normally we step display-time as part of our frame-drawing process. If
  // we're headless, we're not drawing any frames, but we still want to do
  // minimal processing on any display-time timers. Let's run at a low-ish
  // rate (10hz) to keep things efficient. Anyone dealing in display-time
  // should be able to handle a wide variety of rates anyway.
  if (g_core->HeadlessMode()) {
    // NOTE: This length is currently milliseconds.
    headless_display_time_step_timer_ = event_loop()->NewTimer(
        kAppModeMinHeadlessDisplayStep / 1000, true,
        NewLambdaRunnable([this] { StepDisplayTime(); }));
  }
  // Let our initial app-mode know it has become active.
  g_base->app_mode()->OnActivate();

  // Reset our various subsystems to a default state.
  g_base->ui->Reset();
  g_base->input->Reset();
  g_base->graphics->Reset();
  g_base->python->Reset();
  g_base->audio->Reset();

  // Let Python know we're done bootstrapping so it can flip the app
  // into the 'launching' state.
  g_base->python->objs()
      .Get(BasePython::ObjID::kOnAppBootstrappingCompleteCall)
      .Call();

  UpdatePendingWorkTimer();
}

void Logic::OnScreenSizeChange(float virtual_width, float virtual_height,
                               float pixel_width, float pixel_height) {
  assert(g_base->InLogicThread());

  // First, pass the new values to the graphics subsystem.
  // Then inform everyone else simply that they changed; they can ask
  // g_graphics for whatever specific values they need.
  // Note: keep these in the same order as OnAppStart.
  g_base->graphics->OnScreenSizeChange(virtual_width, virtual_height,
                                       pixel_width, pixel_height);
  g_base->audio->OnScreenSizeChange();
  g_base->input->OnScreenSizeChange();
  g_base->ui->OnScreenSizeChange();
  g_core->platform->OnScreenSizeChange();
  g_base->app_mode()->OnScreenSizeChange();
  if (g_base->HavePlus()) {
    g_base->plus()->OnScreenSizeChange();
  }
  g_base->python->OnScreenSizeChange();
}

// Bring all logic-thread stuff up to date for a new visual frame.
void Logic::StepDisplayTime() {
  assert(g_base->InLogicThread());

  // We have two different modes of operation here. When running in headless
  // mode, display time is driven by upcoming events such as sim steps; we
  // basically want to sleep as long as we can and run steps exactly when
  // events occur. When running with a gui, our display-time is driven by
  // real draw times and is intended to keep frame intervals as visually
  // consistent and smooth looking as possible.
  if (g_core->HeadlessMode()) {
    UpdateDisplayTimeForHeadlessMode();
  } else {
    UpdateDisplayTimeForFrameDraw();
  }

  // Give all our subsystems some update love.
  // Note: keep these in the same order as OnAppStart.
  g_base->graphics->StepDisplayTime();
  g_base->audio->StepDisplayTime();
  g_base->input->StepDisplayTime();
  g_base->ui->StepDisplayTime();
  g_core->platform->StepDisplayTime();
  g_base->app_mode()->StepDisplayTime();
  if (g_base->HavePlus()) {
    g_base->plus()->StepDisplayTime();
  }
  g_base->python->StepDisplayTime();
  g_base->app->LogicThreadStepDisplayTime();

  // Let's run display-timers *after* we step everything else so most things
  // they interact with will be in an up-to-date state.
  display_timers_->Run(display_time_microsecs_);

  if (g_core->HeadlessMode()) {
    PostUpdateDisplayTimeForHeadlessMode();
  }
}

void Logic::OnAppModeChanged() {
  assert(g_base->InLogicThread());

  // Kick our headless stepping into high gear; this will snap us out of
  // any long sleep we're currently in the middle of.
  if (g_core->HeadlessMode()) {
    if (debug_log_display_time_) {
      Log(LogLevel::kDebug,
          "Resetting headless display step timer due to app-mode change.");
    }
    assert(headless_display_time_step_timer_);
    // NOTE: This is currently milliseconds.
    headless_display_time_step_timer_->SetLength(kAppModeMinHeadlessDisplayStep
                                                 / 1000);
  }
}

void Logic::UpdateDisplayTimeForHeadlessMode() {
  assert(g_base->InLogicThread());
  // In this case we just keep display time synced up with app time; we don't
  // care about keeping the increments smooth or consistent.

  // The one thing we *do* try to do, however, is keep our timer length
  // updated so that we fire exactly when the app mode has events scheduled
  // (or at least close enough so we can fudge it and tell them its that exact
  // time).

  auto app_time_microsecs = g_core->GetAppTimeMicrosecs();

  auto old_display_time_microsecs = display_time_microsecs_;
  display_time_microsecs_ = app_time_microsecs;
  display_time_increment_microsecs_ =
      display_time_microsecs_ - old_display_time_microsecs;

  // In this path our float values are driven by our int ones.
  display_time_ = static_cast<double>(display_time_microsecs_) / 1000000.0;
  display_time_increment_ =
      static_cast<double>(display_time_increment_microsecs_) / 1000000.0;

  if (debug_log_display_time_) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "stepping display-time at app-time %.4f",
             static_cast<double>(app_time_microsecs) / 1000000.0);
    Log(LogLevel::kDebug, buffer);
  }
}

void Logic::PostUpdateDisplayTimeForHeadlessMode() {
  assert(g_base->InLogicThread());
  // At this point we've stepped our app-mode, so let's ask it how
  // long we've got until the next event. We'll plug this into our
  // display-update timer so we can try to sleep until that point.
  auto headless_display_step_microsecs =
      std::max(std::min(g_base->app_mode()->GetHeadlessDisplayStep(),
                        kAppModeMaxHeadlessDisplayStep),
               kAppModeMinHeadlessDisplayStep);

  if (debug_log_display_time_) {
    auto sleepsecs =
        static_cast<double>(headless_display_step_microsecs) / 1000000.0;
    auto apptimesecs = g_core->GetAppTimeSeconds();
    char buffer[256];
    snprintf(buffer, sizeof(buffer),
             "will try to sleep for %.4f at app-time %.4f (until %.4f)",
             sleepsecs, apptimesecs, apptimesecs + sleepsecs);
    Log(LogLevel::kDebug, buffer);
  }

  auto sleep_millisecs = headless_display_step_microsecs / 1000;
  headless_display_time_step_timer_->SetLength(sleep_millisecs);
}

void Logic::UpdateDisplayTimeForFrameDraw() {
  // Here we update our smoothed display-time-increment based on how fast
  // we are currently rendering frames. We want display-time to basically
  // be progressing at the same rate as app-time but in as constant
  // of a manner as possible so that animations, simulation-stepping/etc.
  // appears smooth (app-time measurements at render times exhibit quite a bit
  // of jitter). Though we also don't want it to be *too* smooth; drops in
  // framerate should still be reflected quickly in display-time-increment
  // otherwise it can look like the game is slowing down or speeding up.

  // Flip this on to debug this stuff.
  // Things to look for:
  // - 'final' value should mostly stay constant.
  // - 'final' value should not be *too* far from 'used'.
  // - 'use_avg' should mostly be 1.
  // - these can vary briefly during load spikes/etc. but should quickly
  //   reconverge to stability. If not, this may need further calibration.
  auto current_app_time = g_core->GetAppTimeSeconds();

  // We handle the first measurement specially.
  if (last_display_time_update_app_time_ < 0) {
    last_display_time_update_app_time_ = current_app_time;
  } else {
    auto this_increment = current_app_time - last_display_time_update_app_time_;
    last_display_time_update_app_time_ = current_app_time;

    // Store increments into a looping buffer.
    if (recent_display_time_increments_index_ < 0) {
      // For the first sample we fill all entries.
      for (auto& recent_display_time_increment :
           recent_display_time_increments_) {
        recent_display_time_increment = this_increment;
      }
      recent_display_time_increments_index_ = 0;
    } else {
      recent_display_time_increments_[recent_display_time_increments_index_] =
          this_increment;
      recent_display_time_increments_index_ =
          (recent_display_time_increments_index_ + 1) % kDisplayTimeSampleCount;
    }

    // It seems that when things get thrown off it is often due to a single
    // rogue sample being unusually long and often the next one being unusually
    // short. Let's try to filter out some of these cases by ignoring both
    // the longest and shortest sample in our set.
    int max_index{};
    int min_index{};
    double max_val{recent_display_time_increments_[0]};
    double min_val{recent_display_time_increments_[0]};
    for (int i = 0; i < kDisplayTimeSampleCount; ++i) {
      auto val = recent_display_time_increments_[i];
      if (val > max_val) {
        max_val = val;
        max_index = i;
      }
      if (val < min_val) {
        min_val = val;
        min_index = i;
      }
    }

    double avg{};
    double min{};
    double max{};
    int count{};
    for (int i = 0; i < kDisplayTimeSampleCount; ++i) {
      if (i == min_index || i == max_index) {
        continue;
      }
      auto val = recent_display_time_increments_[i];
      if (count == 0) {
        // We may have skipped first index(es) so need to do this here
        // instead of initing min/max to first value.
        min = max = val;
      }
      avg += val;
      min = std::min(min, val);
      max = std::max(max, val);
      count += 1;
    }
    avg /= count;
    double range = max - min;

    // If our range of recent increment values is somewhat large relative to
    // an average value, things are probably chaotic, so just use the
    // current value to respond quickly to changes. If things are more calm,
    // use our nice smoothed value.

    // So in a case where we're seeing an average increment of 16ms, we snap
    // out of avg mode if there's more than 8ms between the longest and
    // shortest increments.
    double chaos = range / avg;
    bool use_avg = chaos < 0.5;
    auto used = use_avg ? avg : this_increment;

    // Lastly use this 'used' value to update our actual increment - our
    // increment moves only if 'used' value gets farther than [trail_buffer]
    // from it. So ideally it will sit in the middle of the smoothed value
    // range.

    // How far the smoothed increment value needs to get away from the final
    // value to actually start moving it. Example: If our avg increment is
    // 16.6ms (60fps), don't change our increment until the 'used' value is
    // more than 0.5ms (16.6 * 0.03) from it in either direction.

    // Note: In practice I'm seeing that higher framerates like 120 need
    // buffers that are larger relative to avg to remain stable. Though
    // perhaps a bit of jitter is not noticeable at high frame rates; just
    // something to keep an eye on.
    auto trail_buffer{avg * 0.03};

    auto trailing_diff = used - display_time_increment_;
    auto trailing_dist = std::abs(trailing_diff);
    if (trailing_dist > trail_buffer) {
      auto offs =
          (trailing_dist - trail_buffer) * (trailing_diff > 0.0 ? 1.0 : -1.0);
      if (debug_log_display_time_) {
        char buffer[256];
        snprintf(buffer, sizeof(buffer),
                 "trailing_dist %.6f > trail_buffer %.6f; will offset %.6f).",
                 trailing_dist, trail_buffer, offs);
        Log(LogLevel::kDebug, buffer);
      }
      display_time_increment_ = display_time_increment_ + offs;
    }

    if (debug_log_display_time_) {
      char buffer[256];
      snprintf(buffer, sizeof(buffer),
               "final %.5f used %.5f use_avg %d sample %.5f chaos %.5f",
               display_time_increment_, used, static_cast<int>(use_avg),
               this_increment, chaos);
      Log(LogLevel::kDebug, buffer);
    }
  }
  // Lastly, apply our updated increment value to our time.
  display_time_ += display_time_increment_;

  // In this path, our integer values just follow our float ones.
  auto prev_microsecs = display_time_microsecs_;
  display_time_microsecs_ = static_cast<microsecs_t>(display_time_ * 1000000.0);
  display_time_increment_microsecs_ = display_time_microsecs_ - prev_microsecs;
}

// Set up our sleeping based on what we're doing.
void Logic::UpdatePendingWorkTimer() {
  assert(g_base->InLogicThread());

  // This might get called before we set up our timer in some cases. (such as
  // very early) should be safe to ignore since we update the interval
  // explicitly after creating the timers.
  if (!process_pending_work_timer_) {
    return;
  }

  // If there's loading to do, keep at it rather vigorously.
  if (have_pending_loads_) {
    assert(process_pending_work_timer_);
    process_pending_work_timer_->SetLength(1);
  } else {
    // Otherwise we've got nothing to do; go to sleep until something changes.
    assert(process_pending_work_timer_);
    process_pending_work_timer_->SetLength(-1);
  }
}

void Logic::HandleInterruptSignal() {
  assert(g_base->InLogicThread());

  // Special case; when running under the server-wrapper, we completely
  // ignore interrupt signals (the wrapper acts on them).
  if (g_base->app->server_wrapper_managed()) {
    return;
  }

  // Go with a low level process shutdown here. In situations
  // where we're getting interrupt signals I don't think we'd ever want
  // high level 'soft' quits.
  Shutdown();
}

void Logic::Draw() {
  assert(g_base->InLogicThread());
  assert(!g_core->HeadlessMode());

  // Push a snapshot of our current state to be rendered in the graphics thread.
  g_base->graphics->BuildAndPushFrameDef();

  // Now bring logic up to date.
  // By doing this *after* fulfilling the draw request, we're minimizing the
  // chance of long logic updates leading to delays in frame-def delivery
  // leading to frame drops. The downside is that when logic updates are fast
  // then logic is basically sitting around twiddling its thumbs and getting
  // a full frame out of date before being drawn. But as high frame rates are
  // becoming more normal this becomes less and less meaningful and its probably
  // best to prioritize smooth visuals.
  StepDisplayTime();
}

void Logic::NotifyOfPendingAssetLoads() {
  assert(g_base->InLogicThread());
  have_pending_loads_ = true;
  UpdatePendingWorkTimer();
}

void Logic::Shutdown() {
  assert(g_base->InLogicThread());

  if (!g_core->shutting_down) {
    g_core->shutting_down = true;
    OnAppShutdown();
  }
}

auto Logic::NewAppTimer(millisecs_t length, bool repeat,
                        const Object::Ref<Runnable>& runnable) -> int {
  // App-Timers simply get injected into our loop and run alongside our own
  // stuff.
  assert(g_base->InLogicThread());
  auto* timer = event_loop()->NewTimer(length, repeat, runnable);
  return timer->id();
}

void Logic::DeleteAppTimer(int timer_id) {
  assert(g_base->InLogicThread());
  event_loop()->DeleteTimer(timer_id);
}

void Logic::SetAppTimerLength(int timer_id, millisecs_t length) {
  assert(g_base->InLogicThread());
  Timer* t = event_loop()->GetTimer(timer_id);
  if (t) {
    t->SetLength(length);
  } else {
    Log(LogLevel::kError,
        "Logic::SetAppTimerLength() called on nonexistent timer.");
  }
}

auto Logic::NewDisplayTimer(microsecs_t length, bool repeat,
                            const Object::Ref<Runnable>& runnable) -> int {
  // Display-Timers go into a timer-list that we exec explicitly when we
  // step display-time.
  assert(g_base->InLogicThread());
  int offset = 0;
  Timer* t = display_timers_->NewTimer(g_core->GetAppTimeMicrosecs(), length,
                                       offset, repeat ? -1 : 0, runnable);
  return t->id();
}

void Logic::DeleteDisplayTimer(int timer_id) {
  assert(g_base->InLogicThread());
  display_timers_->DeleteTimer(timer_id);
}

void Logic::SetDisplayTimerLength(int timer_id, microsecs_t length) {
  assert(g_base->InLogicThread());
  Timer* t = display_timers_->GetTimer(timer_id);
  if (t) {
    t->SetLength(length);
  } else {
    Log(LogLevel::kError,
        "Logic::SetDisplayTimerLength() called on nonexistent timer.");
  }
}

void Logic::ProcessPendingWork() {
  have_pending_loads_ = g_base->assets->RunPendingLoadsLogicThread();
  UpdatePendingWorkTimer();
}

}  // namespace ballistica::base
