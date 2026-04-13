// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_LOGIC_LOGIC_H_
#define BALLISTICA_BASE_LOGIC_LOGIC_H_

#include <atomic>
#include <memory>

#include "ballistica/shared/generic/runnable.h"

namespace ballistica::base {

const int kDisplayTimeSampleCount{15};

/// The max amount of time a headless app can sleep if no events are
/// pending. This should not be *too* high or it might cause delays when
/// going from no events present to events present.
const microsecs_t kHeadlessMaxDisplayTimeStep{500000};

/// The min amount of time a headless app can sleep. This provides an upper
/// limit on stepping overhead in cases where events are densely packed.
const microsecs_t kHeadlessMinDisplayTimeStep{1000};

/// The logic subsystem of the app. This runs on a dedicated thread and is
/// where most high level app logic happens. Much app functionality
/// including UI calls must be run on the logic thread.
class Logic {
 public:
  Logic();

  /// Where our stuff runs. Be aware this will return nullptr if the app has
  /// not started running yet.
  auto event_loop() const -> EventLoop* { return event_loop_; }

  /// Called in the main thread when the app is starting.
  void OnMainThreadStartApp();

  /// Called in the logic thread when the app is starting.
  void OnAppStart();

  /// Should be called by the app-adapter when graphics (or lack thereof) is
  /// ready to go. This will kick off asset loads and proceed towards the
  /// final app running state.
  void OnGraphicsReady();

  /// Called when the app reaches the RUNNING state.
  void OnAppRunning();

  /// Called once the first app-mode has been set. At this point it is safe
  /// to start using functionality that interacts with app-modes.
  void OnInitialAppModeSet();

  /// Called when our event-loop pauses. Informs Python and other
  /// subsystems.
  void OnAppSuspend();

  /// Called when our event-loop resumes. Informs Python and other
  /// subsystems.
  void OnAppUnsuspend();

  void OnAppShutdown();
  void OnAppShutdownComplete();

  void OnAppActiveChanged();

  void OnAppModeChanged();

  void ApplyAppConfig();
  void OnScreenSizeChange(float virtual_width, float virtual_height,
                          float pixel_width, float pixel_height);

  /// Called when we should ship a new frame-def to the graphics server. In
  /// graphical builds we also use this opportunity to step our logic.
  void Draw();

  /// Kick off a low level app shutdown. Shutdown is an asynchronous process
  /// which may take up to a few seconds to complete. This is safe to call
  /// repeatedly but must be called from the logic thread.
  void Shutdown();

  /// Should be called by the Python layer when it has completed all
  /// shutdown related tasks.
  void CompleteShutdown();

  /// Has CompleteAppBootstrapping been called?
  auto app_bootstrapping_complete() const {
    return app_bootstrapping_complete_;
  }
  void NotifyOfPendingAssetLoads();

  void HandleInterruptSignal();
  void HandleTerminateSignal();

  auto NewAppTimer(microsecs_t length, bool repeat, Runnable* runnable) -> int;
  void DeleteAppTimer(int timer_id);
  void SetAppTimerLength(int timer_id, microsecs_t length);

  auto NewDisplayTimer(microsecs_t length, bool repeat, Runnable* runnable)
      -> int;
  void DeleteDisplayTimer(int timer_id);
  void SetDisplayTimerLength(int timer_id, microsecs_t length);

  /// Get current display-time for the app in seconds.
  auto display_time() { return display_time_; }

  /// Get current display-time for the app in microseconds.
  auto display_time_microsecs() { return display_time_microsecs_; }

  /// Return current display-time increment in seconds.
  auto display_time_increment() { return display_time_increment_; }

  /// Return current display-time increment in microseconds.
  auto display_time_increment_microsecs() {
    return display_time_increment_microsecs_;
  }

  auto applied_app_config() const { return applied_app_config_; }
  auto shutting_down() const { return shutting_down_; }
  auto shutdown_completed() const { return shutdown_completed_; }
  auto graphics_ready() const { return graphics_ready_; }
  auto app_active() const { return app_active_; }
  auto app_active_applied() -> bool const { return app_active_applied_; }

 private:
  void UpdateDisplayTimeForFrameDraw_();
  void UpdateDisplayTimeForHeadlessMode_();
  void PostUpdateDisplayTimeForHeadlessMode_();
  void CompleteAppBootstrapping_();
  void ProcessPendingWork_();
  void UpdatePendingWorkTimer_();
  void StepDisplayTime_();

  seconds_t display_time_{};
  seconds_t display_time_increment_{1.0 / 60.0};
  microsecs_t display_time_microsecs_{};
  microsecs_t display_time_increment_microsecs_{1000000 / 60};

  // Headless scheduling.
  Timer* headless_display_time_step_timer_{};

  // GUI scheduling.
  seconds_t last_display_time_update_app_time_{-1.0};
  seconds_t recent_display_time_increments_[kDisplayTimeSampleCount]{};
  int recent_display_time_increments_index_{-1};

  /// The logic thread maintains its own app-active state which is driven by
  /// the app-thread's state in g_base.
  bool app_active_{true};

  /// We maintain an app-active value that gets changed once we're done
  /// calling the Python layer's app-active-changed callback. App suspension
  /// looks at this to try to ensure that said Python callbacks complete
  /// before the app gets fully suspended.
  std::atomic_bool app_active_applied_{true};
  bool app_bootstrapping_complete_{};
  bool have_pending_loads_{};
  bool applied_app_config_{};
  bool shutting_down_{};
  bool shutdown_completed_{};
  bool graphics_ready_{};
  Timer* process_pending_work_timer_{};
  EventLoop* event_loop_{};
  std::unique_ptr<TimerList> display_timers_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_LOGIC_LOGIC_H_
