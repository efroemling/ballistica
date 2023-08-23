// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_LOGIC_LOGIC_H_
#define BALLISTICA_BASE_LOGIC_LOGIC_H_

#include <memory>
#include <set>
#include <string>

#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

const int kDisplayTimeSampleCount{15};

/// The logic subsystem of the app. This runs on a dedicated thread and is
/// where most high level app logic happens. Much app functionality
/// including UI calls must be run on the logic thread.
class Logic {
 public:
  Logic();

  /// Where our stuff runs. Be aware this will return nullptr if the app has
  /// not started running yet.
  auto event_loop() const -> EventLoop* { return event_loop_; }

  void OnMainThreadStartApp();
  void OnInitialScreenCreated();
  void OnAppStart();

  /// Called by Python when the app reaches the RUNNING state.
  void OnAppRunning();

  /// Called by Python after the first app-mode has been set. At this point
  /// it is safe to start using functionality that interacts with app-modes.
  void OnInitialAppModeSet();

  /// Called when our event-loop pauses. Informs Python and other
  /// subsystems.
  void OnAppPause();

  /// Called when our event-loop resumes. Informs Python and other
  /// subsystems.
  void OnAppResume();

  void OnAppShutdown();
  void OnAppShutdownComplete();

  void OnAppModeChanged();

  void DoApplyAppConfig();
  void OnScreenSizeChange(float virtual_width, float virtual_height,
                          float pixel_width, float pixel_height);

  /// Called when we should ship a new frame-def to the graphics server. In
  /// graphical builds we also use this opportunity to step our logic.
  void Draw();

  /// Kick off an app shutdown. Shutdown is an asynchronous process which
  /// may take a bit of time to complete. Safe to call repeatedly.
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

  auto NewAppTimer(millisecs_t length, bool repeat,
                   const Object::Ref<Runnable>& runnable) -> int;
  void DeleteAppTimer(int timer_id);
  void SetAppTimerLength(int timer_id, millisecs_t length);

  auto NewDisplayTimer(microsecs_t length, bool repeat,
                       const Object::Ref<Runnable>& runnable) -> int;
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

 private:
  void UpdateDisplayTimeForFrameDraw();
  void UpdateDisplayTimeForHeadlessMode();
  void PostUpdateDisplayTimeForHeadlessMode();
  void CompleteAppBootstrapping();
  void ProcessPendingWork();
  void UpdatePendingWorkTimer();
  void StepDisplayTime();

  double display_time_{};
  microsecs_t display_time_microsecs_{};
  double display_time_increment_{1.0 / 60.0};
  microsecs_t display_time_increment_microsecs_{1000000 / 60};

  // GUI scheduling.
  double last_display_time_update_app_time_{-1.0};
  double recent_display_time_increments_[kDisplayTimeSampleCount]{};
  int recent_display_time_increments_index_{-1};

  // Headless scheduling.

  std::unique_ptr<TimerList> display_timers_;
  EventLoop* event_loop_{};
  Timer* process_pending_work_timer_{};
  Timer* headless_display_time_step_timer_{};
  Timer* asset_prune_timer_{};
  Timer* debug_timer_{};
  bool app_bootstrapping_complete_{};
  bool have_pending_loads_{};
  bool debug_log_display_time_{};
  bool applied_app_config_{};
  bool shutting_down_{};
  bool shutdown_completed_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_LOGIC_LOGIC_H_
