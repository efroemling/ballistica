// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_

#include <string>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Adapts app behavior specific to a particular paradigm and/or api
/// environment. For example, 'Headless', 'VROculus', 'SDL', etc. Multiple
/// of these may be supported on a single platform, unlike the Platform
/// classes where generally there is a single one for the whole platform.
/// For example, on Windows, we might have GUI, VR, and Headless
/// AppAdapters, but they all might share the same CorePlatform and
/// BasePlatform classes.
class AppAdapter {
 public:
  AppAdapter();
  virtual ~AppAdapter();

  virtual void OnMainThreadStartApp();

  /// Return whether this class runs its own event loop.
  auto ManagesEventLoop() const -> bool;

  /// Called for non-event-loop-managing apps to give them an opportunity to
  /// ensure they are self-sustaining. For instance, an app relying on
  /// frame-draws for its main thread event processing may need to manually
  /// pump events until a screen-creation event goes through which should
  /// keep things running thereafter.
  virtual void PrimeMainThreadEventPump();

  /// Handle any pending OS events. On normal graphical builds this is
  /// triggered by RunRenderUpkeepCycle(); timer intervals for headless
  /// builds, etc. Should process any pending OS events, etc.
  virtual void RunEvents();

  /// Put the app into a paused state. Should be called from the main
  /// thread. Pauses work, closes network sockets, etc. May correspond to
  /// being backgrounded on mobile, being minimized on desktop, etc. It is
  /// assumed that, as soon as this call returns, all work is finished and
  /// all threads can be suspended by the OS without any negative side
  /// effects.
  void PauseApp();

  /// Resume the app; can correspond to foregrounding on mobile,
  /// unminimizing on desktop, etc. Spins threads back up, re-opens network
  /// sockets, etc.
  void ResumeApp();

  auto app_paused() const { return app_paused_; }

  /// The last time the app was resumed (uses GetAppTimeMillisecs() value).
  auto last_app_resume_time() const { return last_app_resume_time_; }

  /// Attempt to draw a frame.
  void DrawFrame(bool during_resize = false);

  /// Gets called when the app config is being applied. Note that this call
  /// happens in the logic thread, so we should do any reading that needs to
  /// happen in the logic thread and then forward the values to ourself back
  /// in our main thread.
  virtual void LogicThreadDoApplyAppConfig();

  /// Used on platforms where our main thread event processing is driven by
  /// frame-draw commands given to us. This should be called after drawing a
  /// frame in order to bring game state up to date and process OS events.
  void RunRenderUpkeepCycle();

  /// Called by the graphics-server when drawing completes for a frame.
  virtual void DidFinishRenderingFrame(FrameDef* frame);

 private:
  void UpdatePauseResume_();
  void OnAppPause_();
  void OnAppResume_();
  bool app_pause_requested_{};
  bool app_paused_{};
  millisecs_t last_resize_draw_event_time_{};
  millisecs_t last_app_resume_time_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_
