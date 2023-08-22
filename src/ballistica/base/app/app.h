// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_H_
#define BALLISTICA_BASE_APP_APP_H_

#include <string>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Defines app behavior for a particular paradigm (regular gui, vr,
/// headless) and/or top level api (SDL, UIKit, etc.).
class App {
 public:
  App();
  virtual ~App();

  /// Should be run after the instance is created and assigned. Any setup
  /// that may trigger virtual methods or lookups via global should go here.
  void PostInit();

  /// Gets called when the app config is being applied. Note that this call
  /// happens in the logic thread, so we should do any reading that needs to
  /// happen in the logic thread and then forward the values to ourself back
  /// in our main thread.
  void DoLogicThreadApplyAppConfig();

  /// Return whether this class runs its own event loop.
  auto ManagesEventLoop() const -> bool;

  /// Called for non-event-loop apps to give them an opportunity to ensure
  /// they are self-sustaining. For instance, an app relying on frame-draws
  /// for its main thread event processing may need to manually pump events
  /// until frame rendering begins.
  virtual void PrimeMainThreadEventPump();

  /// Handle any pending OS events. On normal graphical builds this is
  /// triggered by RunRenderUpkeepCycle(); timer intervals for headless
  /// builds, etc. Should process any pending OS events, etc.
  virtual void RunEvents();

  /// Put the app into a paused state. Should be called from the main
  /// thread. Pauses work, closes network sockets, etc.
  /// Corresponds to being backgrounded on mobile, etc.
  /// It is assumed that, as soon as this call returns, all work is
  /// finished and all threads can be suspended by the OS without any
  /// negative side effects.
  void PauseApp();

  auto paused() const -> bool { return actually_paused_; }

  /// OnAppResume the app; corresponds to returning to foreground on
  /// mobile/etc. Spins threads back up, re-opens network sockets, etc.
  void ResumeApp();

  /// The last time the app was resumed (uses GetAppTimeMillisecs() value).
  auto last_app_resume_time() const -> millisecs_t {
    return last_app_resume_time_;
  }

  /// Should be called if the platform detects the GL context_ref was lost.
  void RebuildLostGLContext();

  /// Attempt to draw a frame.
  void DrawFrame(bool during_resize = false);

  /// Run updates in the logic thread. Generally called once per frame
  /// rendered or at some fixed rate for headless builds.
  void LogicThreadStepDisplayTime();

  /// Used on platforms where our main thread event processing is driven by
  /// frame-draw commands given to us. This should be called after drawing a
  /// frame in order to bring game state up to date and process OS events.
  void RunRenderUpkeepCycle();

  /// Called by the graphics-server when drawing completes for a frame.
  virtual void DidFinishRenderingFrame(FrameDef* frame);

  /// Whether we're running under ballisticakit_server.py
  /// (affects some app behavior).
  auto server_wrapper_managed() const -> bool {
    return server_wrapper_managed_;
  }

  virtual void OnMainThreadStartApp();

  // Deferred calls that can be made from other threads.

  void PushPurchaseCall(const std::string& item);
  void PushRestorePurchasesCall();
  void PushResetAchievementsCall();
  void PushPurchaseAckCall(const std::string& purchase,
                           const std::string& order_id);

  /// Called by the logic thread when all shutdown-related tasks are done.
  void LogicThreadShutdownComplete();

  void LogicThreadOnAppRunning();
  void LogicThreadOnInitialAppModeSet();

 private:
  void UpdatePauseResume_();
  void OnAppPause_();
  void OnAppResume_();
  bool server_wrapper_managed_{};
  bool sys_paused_app_{};
  bool actually_paused_{};
  millisecs_t last_resize_draw_event_time_{};
  millisecs_t last_app_resume_time_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_APP_H_
