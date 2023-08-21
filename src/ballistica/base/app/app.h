// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_H_
#define BALLISTICA_BASE_APP_APP_H_

#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>

#include "ballistica/base/base.h"
#include "ballistica/base/support/stress_test.h"

namespace ballistica::base {

/// Encapsulates high level app behavior for regular apps, vr apps,
/// headless apps, etc.
class App {
 public:
  explicit App(EventLoop* event_loop);

  /// Should be run after the instance is created and assigned. Any setup
  /// that may trigger virtual methods or lookups via global should go here.
  void PostInit();

  /// Gets called when the app config is being applied. Note that this call
  /// happens in the logic thread, so we should do any reading that needs to
  /// happen in the logic thread and then forward the values to ourself back
  /// in our main thread.
  void DoLogicThreadApplyAppConfig();

  /// Return whether this class runs its own event loop. If true,
  /// MonolithicMain() will continuously ask the app for events until the
  /// app is quit, at which point MonolithicMain() returns. If false,
  /// MonolithicMain returns immediately and it is assumed that the OS
  /// handles the app lifecycle and pushes events to the app via
  /// callbacks/etc.
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

  /// Return the price of an IAP product as a human-readable string, or an
  /// empty string if not found. FIXME: move this to platform.
  auto GetProductPrice(const std::string& product) -> std::string;
  void SetProductPrice(const std::string& product, const std::string& price);

  auto done() const -> bool { return done_; }

  /// Whether we're running under ballisticakit_server.py
  /// (affects some app behavior).
  auto server_wrapper_managed() const -> bool {
    return server_wrapper_managed_;
  }

  virtual void OnMainThreadStartApp();

  // Deferred calls that can be made from other threads.

  void PushCursorUpdate(bool vis);
  void PushShowOnlineScoreUICall(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version);
  void PushSubmitScoreCall(const std::string& game,
                           const std::string& game_version, int64_t score);
  void PushAchievementReportCall(const std::string& achievement);
  void PushOpenURLCall(const std::string& url);
  void PushStringEditCall(const std::string& name, const std::string& value,
                          int max_chars);
  void PushSetStressTestingCall(bool enable, int player_count);
  void PushPurchaseCall(const std::string& item);
  void PushRestorePurchasesCall();
  void PushResetAchievementsCall();
  void PushPurchaseAckCall(const std::string& purchase,
                           const std::string& order_id);
  auto event_loop() const -> EventLoop* { return event_loop_; }

  /// Called by the logic thread when all shutdown-related tasks are done
  /// and it is safe to exit the main event loop.
  void LogicThreadShutdownComplete();

  void LogicThreadOnAppRunning();
  void LogicThreadOnInitialAppModeSet();

 private:
  void UpdatePauseResume_();
  void OnAppPause_();
  void OnAppResume_();
  EventLoop* event_loop_{};
  bool done_{};
  bool server_wrapper_managed_{};
  bool sys_paused_app_{};
  bool actually_paused_{};
  std::unique_ptr<StressTest> stress_test_;
  millisecs_t last_resize_draw_event_time_{};
  millisecs_t last_app_resume_time_{};
  std::unordered_map<std::string, std::string> product_prices_;
  std::mutex product_prices_mutex_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_APP_H_
