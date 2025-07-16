// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/logic/logic.h"

#include <Python.h>

#include <algorithm>
#include <cstdio>
#include <string>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/context.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/base/support/stdio_console.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

Logic::Logic() : display_timers_(new TimerList()) {}

void Logic::OnMainThreadStartApp() {
  // Spin up our logic thread and sit and wait for it to init.
  event_loop_ = new EventLoop(EventLoopID::kLogic);
  g_core->suspendable_event_loops.push_back(event_loop_);
  event_loop_->PushCallSynchronous([this] { OnAppStart(); });
}

void Logic::OnAppStart() {
  assert(g_base->InLogicThread());
  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "on-app-start begin (logic thread)");

  // Our thread should not be holding the GIL here at the start (and
  // probably will not have any Python state at all). So here we set both
  // of those up.
  assert(!PyGILState_Check());
  PyGILState_Ensure();

  // Code running in the logic thread holds the GIL by default.
  event_loop_->SetAcquiresPythonGIL();

  // Stay informed when our event loop is pausing/unpausing.
  event_loop_->AddSuspendCallback(
      NewLambdaRunnableUnmanaged([this] { OnAppSuspend(); }));
  event_loop_->AddUnsuspendCallback(
      NewLambdaRunnableUnmanaged([this] { OnAppUnsuspend(); }));

  // Running in a specific order here and should try to stick to it in
  // other OnAppXXX callbacks so any subsystem interdependencies behave
  // consistently. When pausing or shutting-down we use the opposite order for
  // the same reason. Let's do Python last (or first when pausing, etc) since
  // it will be the most variable; that way it will interact with other
  // subsystems in their normal states which is less likely to lead to
  // problems.
  g_base->app_adapter->OnAppStart();
  g_base->platform->OnAppStart();
  g_base->graphics->OnAppStart();
  g_base->audio->OnAppStart();
  g_base->input->OnAppStart();
  g_base->ui->OnAppStart();
  g_base->app_mode()->OnAppStart();
  if (g_base->HavePlus()) {
    g_base->Plus()->OnAppStart();
  }
  g_base->python->OnAppStart();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "on-app-start end (logic thread)");
}

void Logic::OnGraphicsReady() {
  assert(g_base->InLogicThread());
  if (graphics_ready_) {
    // Only want to fire this logic the first time.
    return;
  }
  graphics_ready_ = true;

  // Ok; graphics-server is telling us we've got a screen (or no screen in
  // the case of headless-mode). We use this as a cue to kick off our
  // business logic.

  // Let the Python layer know the native layer is now fully functional.
  // This will probably result in the Python layer flipping to the INITING
  // state.
  CompleteAppBootstrapping_();

  if (g_core->HeadlessMode()) {
    // Normally we step display-time as part of our frame-drawing process.
    // If we're headless, we're not drawing any frames, but we still want to
    // do minimal processing on any display-time timers so code doesn't
    // break. Let's run at a low-ish rate (10hz) to keep things efficient.
    // Anyone dealing in display-time should be able to handle a wide
    // variety of rates anyway. NOTE: This length is currently milliseconds.
    headless_display_time_step_timer_ = event_loop()->NewTimer(
        kHeadlessMinDisplayTimeStep, true,
        NewLambdaRunnable([this] { StepDisplayTime_(); }).get());
  } else {
    // In gui mode, push an initial frame to the graphics server. From this
    // point it will be self-sustaining, sending us a frame request each
    // time it receives a new frame from us.
    g_base->graphics->BuildAndPushFrameDef();
  }
}

void Logic::CompleteAppBootstrapping_() {
  assert(g_base->InLogicThread());
  assert(g_base->CurrentContext().IsEmpty());

  assert(!app_bootstrapping_complete_);
  app_bootstrapping_complete_ = true;

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "app native bootstrapping complete");

  // Let the assets system know it can start loading stuff now that
  // we have a screen and thus know texture formats/etc.
  // TODO(ericf): It might be nice to kick this off earlier if our logic is
  //  robust enough to create some sort of 'null' textures/meshes before
  //  the renderer is ready and then seamlessly create renderer-specific
  //  ones once the renderer is up. We could likely at least get a lot
  //  of preloads done in the meantime. Though this would require preloads
  //  to be renderer-agnostic; not sure if that will always be the case.
  g_base->assets->StartLoading();

  // Let base know it can create the console or other asset-dependent things.
  g_base->OnAssetsAvailable();

  // Set up our timers.
  process_pending_work_timer_ = event_loop()->NewTimer(
      0, true, NewLambdaRunnable([this] { ProcessPendingWork_(); }).get());
  // asset_prune_timer_ = event_loop()->NewTimer(
  //     2345 * 1000, true, NewLambdaRunnable([] { g_base->assets->Prune();
  //     }).Get());

  // Let our initial dummy app-mode know it has become active.
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
      .Get(BasePython::ObjID::kAppOnNativeBootstrappingCompleteCall)
      .Call();

  UpdatePendingWorkTimer_();
}

void Logic::OnAppRunning() {
  assert(g_base->InLogicThread());
  assert(g_base->CurrentContext().IsEmpty());

  // Currently don't do anything here.
}

void Logic::OnInitialAppModeSet() {
  assert(g_base->InLogicThread());
  assert(g_base->CurrentContext().IsEmpty());

  // We want any sort of raw Python input to only start accepting commands
  // once we've got an initial app-mode set. Generally said commands will
  // assume we're running in that mode and will fail if run before it is set.
  if (auto* console = g_base->ui->dev_console()) {
    console->EnableInput();
  }
  if (g_base->stdio_console) {
    g_base->stdio_console->Start();
  }
}

void Logic::OnAppSuspend() {
  assert(g_base->InLogicThread());
  assert(g_base->CurrentContext().IsEmpty());

  // Note: keep these in opposite order of OnAppStart.
  g_base->python->OnAppSuspend();
  if (g_base->HavePlus()) {
    g_base->Plus()->OnAppSuspend();
  }
  g_base->app_mode()->OnAppSuspend();
  g_base->ui->OnAppSuspend();
  g_base->input->OnAppSuspend();
  g_base->audio->OnAppSuspend();
  g_base->graphics->OnAppSuspend();
  g_base->platform->OnAppSuspend();
  g_base->app_adapter->OnAppSuspend();
}

void Logic::OnAppUnsuspend() {
  assert(g_base->InLogicThread());
  assert(g_base->CurrentContext().IsEmpty());

  // Note: keep these in the same order as OnAppStart.
  g_base->app_adapter->OnAppUnsuspend();
  g_base->platform->OnAppUnsuspend();
  g_base->graphics->OnAppUnsuspend();
  g_base->audio->OnAppUnsuspend();
  g_base->input->OnAppUnsuspend();
  g_base->ui->OnAppUnsuspend();
  g_base->app_mode()->OnAppUnsuspend();
  if (g_base->HavePlus()) {
    g_base->Plus()->OnAppUnsuspend();
  }
  g_base->python->OnAppUnsuspend();
}

void Logic::Shutdown() {
  assert(g_base->InLogicThread());
  assert(g_base->IsAppStarted());

  if (!shutting_down_) {
    shutting_down_ = true;
    OnAppShutdown();
  }
}

void Logic::OnAppShutdown() {
  assert(g_core);
  assert(g_base->CurrentContext().IsEmpty());
  assert(shutting_down_);

  // Nuke the app from orbit if we get stuck while shutting down.
  g_core->StartSuicideTimer("shutdown", 15000);

  // Tell base to disallow shutdown-suppressors from here on out.
  g_base->ShutdownSuppressDisallow();

  // Let our logic thread subsystems know we're shutting down.
  // Note: Keep these in opposite order of OnAppStart.
  // Note2: Any shutdown processes that take a non-zero amount of time
  // should be registered as shutdown-tasks
  g_base->python->OnAppShutdown();
  if (g_base->HavePlus()) {
    g_base->Plus()->OnAppShutdown();
  }
  g_base->app_mode()->OnAppShutdown();
  g_base->ui->OnAppShutdown();
  g_base->input->OnAppShutdown();
  g_base->audio->OnAppShutdown();
  g_base->graphics->OnAppShutdown();
  g_base->platform->OnAppShutdown();
  g_base->app_adapter->OnAppShutdown();
}

void Logic::CompleteShutdown() {
  BA_PRECONDITION(g_base->InLogicThread());
  BA_PRECONDITION(shutting_down_);
  BA_PRECONDITION(!shutdown_completed_);

  shutdown_completed_ = true;
  OnAppShutdownComplete();
}

void Logic::OnAppShutdownComplete() {
  assert(g_base->InLogicThread());

  // Wrap up any last business here in the logic thread and then kick things
  // over to the main thread to exit out of the main loop.

  // Let our logic subsystems know in case there's any last thing they'd
  // like to do right before we exit.
  // Note: Keep these in opposite order of OnAppStart.
  // Note2: Any shutdown processes that take a non-zero amount of time
  // should be registered as shutdown-tasks.
  g_base->python->OnAppShutdownComplete();
  if (g_base->HavePlus()) {
    g_base->Plus()->OnAppShutdownComplete();
  }
  g_base->app_mode()->OnAppShutdownComplete();
  g_base->ui->OnAppShutdownComplete();
  g_base->input->OnAppShutdownComplete();
  g_base->audio->OnAppShutdownComplete();
  g_base->graphics->OnAppShutdownComplete();
  g_base->platform->OnAppShutdownComplete();
  g_base->app_adapter->OnAppShutdownComplete();

  g_base->app_adapter->PushMainThreadCall(
      [] { g_base->OnAppShutdownComplete(); });
}

void Logic::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  // Give all our other subsystems a chance.
  // Note: keep these in the same order as OnAppStart.
  g_base->app_adapter->ApplyAppConfig();
  g_base->platform->ApplyAppConfig();
  g_base->graphics->ApplyAppConfig();
  g_base->audio->ApplyAppConfig();
  g_base->input->ApplyAppConfig();
  g_base->ui->ApplyAppConfig();
  g_base->app_mode()->ApplyAppConfig();
  if (g_base->HavePlus()) {
    g_base->Plus()->ApplyAppConfig();
  }
  g_base->python->ApplyAppConfig();

  // Inform some other subsystems even though they're not our standard
  // set of logic-thread-based ones.
  g_base->networking->ApplyAppConfig();

  applied_app_config_ = true;
}

void Logic::OnScreenSizeChange(float virtual_width, float virtual_height,
                               float pixel_width, float pixel_height) {
  assert(g_base->InLogicThread());

  // Inform all subsystems.
  //
  // Note: keep these in the same order as OnAppStart.
  g_base->app_adapter->OnScreenSizeChange();
  g_base->platform->OnScreenSizeChange();
  g_base->graphics->OnScreenSizeChange();
  g_base->audio->OnScreenSizeChange();
  g_base->input->OnScreenSizeChange();
  g_base->ui->OnScreenSizeChange();
  g_core->platform->OnScreenSizeChange();
  g_base->app_mode()->OnScreenSizeChange();
  if (g_base->HavePlus()) {
    g_base->Plus()->OnScreenSizeChange();
  }
  g_base->python->OnScreenSizeChange();
}

// Bring all logic-thread stuff up to date for a new visual frame.
void Logic::StepDisplayTime_() {
  assert(g_base->InLogicThread());

  // We have two different modes of operation here. When running in headless
  // mode, display time is driven by upcoming events such as sim steps; we
  // basically want to sleep as long as we can and run steps exactly when
  // events occur. When running with a gui, our display-time is driven by
  // real draw times and is intended to keep frame intervals as visually
  // consistent and smooth looking as possible.
  if (g_core->HeadlessMode()) {
    UpdateDisplayTimeForHeadlessMode_();
  } else {
    UpdateDisplayTimeForFrameDraw_();
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
    g_base->Plus()->StepDisplayTime();
  }
  g_base->python->StepDisplayTime();

  // Let's run display-timers *after* we step everything else so most things
  // they interact with will be in an up-to-date state.
  display_timers_->Run(display_time_microsecs_);

  if (g_core->HeadlessMode()) {
    PostUpdateDisplayTimeForHeadlessMode_();
  }
}

void Logic::OnAppModeChanged() {
  assert(g_base->InLogicThread());

  // Kick our headless stepping into high gear; this will snap us out of any
  // long sleep we're currently in the middle of.
  if (g_core->HeadlessMode()) {
    if (g_core->logging->LogLevelEnabled(LogName::kBaDisplayTime,
                                         LogLevel::kDebug)) {
      g_core->logging->Log(
          LogName::kBaDisplayTime, LogLevel::kDebug,
          "Resetting headless display step timer due to app-mode change.");
    }
    assert(headless_display_time_step_timer_);
    headless_display_time_step_timer_->SetLength(kHeadlessMinDisplayTimeStep);
  }
}

void Logic::UpdateDisplayTimeForHeadlessMode_() {
  assert(g_base->InLogicThread());
  // In this case we just keep display time synced up with app time; we
  // don't care about keeping the increments smooth or consistent.

  // The one thing we *do* try to do, however, is keep our timer length
  // updated so that we'll fire exactly when the next app-mode event is
  // scheduled (or at least close enough so we can fudge it and tell them
  // its that exact time).

  auto app_time_microsecs = g_core->AppTimeMicrosecs();

  // Set our int based time vals so we can exactly hit timers.
  auto old_display_time_microsecs = display_time_microsecs_;
  display_time_microsecs_ = app_time_microsecs;
  display_time_increment_microsecs_ =
      display_time_microsecs_ - old_display_time_microsecs;

  // And then our float time vals are driven by our int ones.
  display_time_ = static_cast<double>(display_time_microsecs_) / 1000000.0;
  display_time_increment_ =
      static_cast<double>(display_time_increment_microsecs_) / 1000000.0;

  g_core->logging->Log(
      LogName::kBaDisplayTime, LogLevel::kDebug, [app_time_microsecs] {
        char buffer[256];
        snprintf(buffer, sizeof(buffer),
                 "stepping display-time at app-time %.4f",
                 static_cast<double>(app_time_microsecs) / 1000000.0);
        return std::string(buffer);
      });
}

void Logic::PostUpdateDisplayTimeForHeadlessMode_() {
  assert(g_base->InLogicThread());
  // At this point we've stepped our app-mode, so let's ask it how long
  // we've got until the next event. We'll plug this into our display-update
  // timer so we can try to sleep exactly until that point.
  auto headless_display_step_microsecs =
      std::max(std::min(g_base->app_mode()->GetHeadlessNextDisplayTimeStep(),
                        kHeadlessMaxDisplayTimeStep),
               kHeadlessMinDisplayTimeStep);

  g_core->logging->Log(
      LogName::kBaDisplayTime, LogLevel::kDebug,
      [headless_display_step_microsecs] {
        auto sleepsecs =
            static_cast<double>(headless_display_step_microsecs) / 1000000.0;
        auto apptimesecs = g_core->AppTimeSeconds();
        char buffer[256];
        snprintf(buffer, sizeof(buffer),
                 "will try to sleep for %.4f at app-time %.4f (until %.4f)",
                 sleepsecs, apptimesecs, apptimesecs + sleepsecs);
        return std::string(buffer);
      });

  auto sleep_microsecs = headless_display_step_microsecs;
  headless_display_time_step_timer_->SetLength(sleep_microsecs);
}

void Logic::UpdateDisplayTimeForFrameDraw_() {
  // Here we update our smoothed display-time-increment based on how fast we
  // are currently rendering frames. We want display-time to basically be
  // progressing at the same rate as app-time but in as constant of a manner
  // as possible so that animation, simulation-stepping/etc. appears smooth
  // (using app-times within renders exhibits quite a bit of jitter). Though
  // we also don't want it to be *too* smooth; drops in framerate should
  // still be reflected quickly in display-time-increment otherwise it can
  // look like the game is slowing down or speeding up.

  // Flip debug-log-display-time on to debug this stuff.
  // Things to look for:
  // - 'final' value should mostly stay constant.
  // - 'final' value should not be *too* far from 'current'.
  // - 'current' should mostly show '(avg)'; rarely '(sample)'.
  // - these can vary briefly during load spikes/etc. but should quickly
  //   reconverge to stability. If not, this may need further calibration.
  auto current_app_time = g_core->AppTimeSeconds();

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

    double avg{};
    double min, max;
    min = max = recent_display_time_increments_[0];
    for (int i = 0; i < kDisplayTimeSampleCount; ++i) {
      auto val = recent_display_time_increments_[i];
      avg += val;
      min = std::min(min, val);
      max = std::max(max, val);
    }
    avg /= kDisplayTimeSampleCount;
    double range = max - min;

    // If our range of recent increment values is somewhat large relative to
    // an average value, things are probably chaotic, so just use the
    // current value to respond quickly to changes. If things are more calm,
    // use our nice smoothed value.

    // Let's use 1.0 as a final 'chaos' threshold to make logs easy to read.
    // So our key fudge factor here is chaos_fudge. The higher this value,
    // the lower chaos will be and thus the more the engine will stick to
    // smoothed values. A good way to determine if this value is too high is
    // to launch the game and watch the menu animation. If it visibly speeds
    // up or slows down in a 'rubber band' looking way the moment after
    // launch, it means the value is too high and the engine is sticking
    // with smoothed values when it should instead be reacting immediately.
    // So basically this value should be as high as possible while avoiding
    // that look.
    double chaos_fudge{1.25};
    double chaos = (range / avg) / chaos_fudge;
    bool use_avg = chaos < 1.0;
    auto used = use_avg ? avg : this_increment;

    // Lastly use this 'used' value to update our actual increment - our
    // increment moves only if 'used' value gets farther than [trail_buffer]
    // from it. So ideally it will sit in the middle of the smoothed value
    // range.

    // How far the smoothed increment value needs to get away from the
    // current smooth value to actually start moving it. Example: If our
    // smooth increment is 16.6ms (60fps), don't change our increment until
    // the 'used' value is more than 0.5ms (16.6 * 0.03) from it in either
    // direction.

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
      g_core->logging->Log(
          LogName::kBaDisplayTime, LogLevel::kDebug,
          [trailing_dist, trail_buffer, offs] {
            char buffer[256];
            snprintf(
                buffer, sizeof(buffer),
                "trailing_dist %.6f > trail_buffer %.6f; will offset %.6f).",
                trailing_dist, trail_buffer, offs);
            return std::string(buffer);
          });
      display_time_increment_ = display_time_increment_ + offs;
    }

    // After all is said and done, clamp our increment size to some sane
    // amount. Trying to push too much through in a single instant can
    // overflow thread message lists and whatnot.
    display_time_increment_ = std::min(display_time_increment_, 0.25);

    g_core->logging->Log(
        LogName::kBaDisplayTime, LogLevel::kDebug,
        [this, use_avg, this_increment, chaos, used] {
          char buffer[256];
          snprintf(buffer, sizeof(buffer),
                   "final %.5f current(%s) %.5f sample %.5f chaos %.5f",
                   display_time_increment_, use_avg ? "avg" : "sample", used,
                   this_increment, chaos);
          return std::string(buffer);
        });
  }

  // Lastly, apply our updated increment value to our time.
  display_time_ += display_time_increment_;

  // In this path, our integer values just follow our float ones.
  auto prev_microsecs = display_time_microsecs_;
  display_time_microsecs_ = static_cast<microsecs_t>(display_time_ * 1000000.0);
  display_time_increment_microsecs_ = display_time_microsecs_ - prev_microsecs;
}

// Set up our sleeping based on what we're doing.
void Logic::UpdatePendingWorkTimer_() {
  assert(g_base->InLogicThread());

  // This might get called before we set up our timer in some cases. (such
  // as very early) should be safe to ignore since we update the interval
  // explicitly after creating the timers.
  if (!process_pending_work_timer_) {
    return;
  }

  // If there's loading to do, keep at it rather vigorously.
  if (have_pending_loads_) {
    assert(process_pending_work_timer_);
    process_pending_work_timer_->SetLength(1 * 1000);
  } else {
    // Otherwise we've got nothing to do; go to sleep until something
    // changes.
    assert(process_pending_work_timer_);
    process_pending_work_timer_->SetLength(-1);
  }
}

void Logic::HandleInterruptSignal() {
  assert(g_base->InLogicThread());

  // Interrupt signals are 'gentle' requests to shut down.

  // Special case; when running under the server-wrapper, we completely
  // ignore interrupt signals (the wrapper acts on them).
  if (g_base->server_wrapper_managed()) {
    return;
  }
  Shutdown();
}

void Logic::HandleTerminateSignal() {
  // Interrupt signals are slightly more stern requests to shut down.
  // We always respond to these.
  assert(g_base->InLogicThread());
  Shutdown();
}

void Logic::Draw() {
  assert(g_base->InLogicThread());
  assert(!g_core->HeadlessMode());

  // Push a snapshot of our current state to be rendered in the graphics
  // thread.
  g_base->graphics->BuildAndPushFrameDef();

  // Now bring logic up to date. By doing this *after* fulfilling the draw
  // request, we're minimizing the chance of long logic updates leading to
  // delays in frame-def delivery leading to frame drops. The downside is
  // that when logic updates are fast then logic is basically sitting around
  // twiddling its thumbs and getting a full frame out of date before being
  // drawn. But as high frame rates are becoming more normal this becomes
  // less and less meaningful and its probably best to prioritize smooth
  // visuals.
  StepDisplayTime_();
}

void Logic::NotifyOfPendingAssetLoads() {
  assert(g_base->InLogicThread());
  have_pending_loads_ = true;
  UpdatePendingWorkTimer_();
}

auto Logic::NewAppTimer(microsecs_t length, bool repeat, Runnable* runnable)
    -> int {
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

void Logic::SetAppTimerLength(int timer_id, microsecs_t length) {
  assert(g_base->InLogicThread());
  Timer* t = event_loop()->GetTimer(timer_id);
  if (t) {
    t->SetLength(length);
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Logic::SetAppTimerLength() called on nonexistent timer.");
  }
}

auto Logic::NewDisplayTimer(microsecs_t length, bool repeat, Runnable* runnable)
    -> int {
  // Display-Timers go into a timer-list that we exec explicitly when we
  // step display-time.
  assert(g_base->InLogicThread());
  int offset = 0;
  Timer* t = display_timers_->NewTimer(display_time_microsecs_, length, offset,
                                       repeat ? -1 : 0, runnable);
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
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Logic::SetDisplayTimerLength() called on nonexistent timer.");
  }
}

void Logic::ProcessPendingWork_() {
  have_pending_loads_ = g_base->assets->RunPendingLoadsLogicThread();
  UpdatePendingWorkTimer_();
}

void Logic::OnAppActiveChanged() {
  assert(g_base->InLogicThread());

  // Note: we keep our own active state here in the logic thread and
  // simply refresh it from the atomic value from the main thread here.
  // There are occasions where the main thread's value flip-flops back
  // and forth quickly and we'll generally skip over those this way.
  auto app_active = g_base->app_active();
  if (app_active != app_active_) {
    g_core->logging->Log(
        LogName::kBaLifecycle, LogLevel::kInfo,
        std::string("app-active is now ") + (app_active ? "True" : "False"));

    app_active_ = app_active;

    // For now just informing Python (which informs Python level app-mode).
    // Can expand this to inform everyone else if needed.
    g_base->python->OnAppActiveChanged();

    app_active_applied_ = app_active;
  }
}

}  // namespace ballistica::base
