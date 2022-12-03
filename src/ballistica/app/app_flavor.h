// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_APP_FLAVOR_H_
#define BALLISTICA_APP_APP_FLAVOR_H_

#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>

#include "ballistica/app/stress_test.h"
#include "ballistica/ballistica.h"

namespace ballistica {

/// Defines our high level app behavior.
class AppFlavor {
 public:
  explicit AppFlavor(Thread* thread);

  /// Should be run after the instance is created and assigned.
  /// Any setup that may trigger virtual methods or lookups via global
  /// should go here.
  auto PostInit() -> void;

  /// Return whether this class runs its own event loop.
  /// If true, BallisticaMain() will continuously ask the app for events
  /// until the app is quit, at which point BallisticaMain() returns.
  /// If false, BallisticaMain returns immediately and it is assumed
  /// that the OS handles the app lifecycle and pushes events to the app
  /// via callbacks/etc.
  auto ManagesEventLoop() const -> bool;

  /// Called for non-event-loop apps to give them an opportunity to
  /// ensure they are self-sustaining. For instance, an app relying on
  /// frame-draws for its main thread event processing may need to
  /// manually pump events until frame rendering begins.
  virtual auto PrimeEventPump() -> void;

  /// Handle any pending OS events.
  /// On normal graphical builds this is triggered by RunRenderUpkeepCycle();
  /// timer intervals for headless builds, etc.
  /// Should process any pending OS events, etc.
  virtual auto RunEvents() -> void;

  /// Put the app into a paused state. Should be called from the main
  /// thread. Pauses work, closes network sockets, etc.
  /// Corresponds to being backgrounded on mobile, etc.
  /// It is assumed that, as soon as this call returns, all work is
  /// finished and all threads can be suspended by the OS without any
  /// negative side effects.
  auto PauseApp() -> void;

  auto paused() const -> bool { return actually_paused_; }

  /// Resume the app; corresponds to returning to foreground on mobile/etc.
  /// Spins threads back up, re-opens network sockets, etc.
  auto ResumeApp() -> void;

  /// The last time the app was resumed (uses GetRealTime() value).
  auto last_app_resume_time() const -> millisecs_t {
    return last_app_resume_time_;
  }

  /// Should be called when the window/screen resolution changes.
  auto SetScreenResolution(float width, float height) -> void;

  /// Should be called if the platform detects the GL context was lost.
  auto RebuildLostGLContext() -> void;

  /// Attempt to draw a frame.
  auto DrawFrame(bool during_resize = false) -> void;

  /// Used on platforms where our main thread event processing is driven by
  /// frame-draw commands given to us. This should be called after drawing
  /// a frame in order to bring game state up to date and process OS events.
  auto RunRenderUpkeepCycle() -> void;

  /// Called by the graphics-server when drawing completes for a frame.
  virtual auto DidFinishRenderingFrame(FrameDef* frame) -> void;

  /// Return the price of an IAP product as a human-readable string,
  /// or an empty string if not found.
  /// FIXME: move this to platform.
  auto GetProductPrice(const std::string& product) -> std::string;
  auto SetProductPrice(const std::string& product, const std::string& price)
      -> void;

  auto done() const -> bool { return done_; }

  /// Whether we're running under ballisticacore_server.py
  /// (affects some app behavior).
  auto server_wrapper_managed() const -> bool {
    return server_wrapper_managed_;
  }

  virtual auto OnAppStart() -> void;

  // Deferred calls that can be made from other threads.

  auto PushCursorUpdate(bool vis) -> void;
  auto PushShowOnlineScoreUICall(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version) -> void;
  auto PushSubmitScoreCall(const std::string& game,
                           const std::string& game_version, int64_t score)
      -> void;
  auto PushAchievementReportCall(const std::string& achievement) -> void;
  auto PushOpenURLCall(const std::string& url) -> void;
  auto PushStringEditCall(const std::string& name, const std::string& value,
                          int max_chars) -> void;
  auto PushSetStressTestingCall(bool enable, int player_count) -> void;
  auto PushPurchaseCall(const std::string& item) -> void;
  auto PushRestorePurchasesCall() -> void;
  auto PushResetAchievementsCall() -> void;
  auto PushPurchaseAckCall(const std::string& purchase,
                           const std::string& order_id) -> void;
  auto PushNetworkSetupCall(int port, int telnet_port, bool enable_telnet,
                            const std::string& telnet_password) -> void;
  auto PushShutdownCompleteCall() -> void;
  auto thread() const -> Thread* { return thread_; }

 private:
  auto UpdatePauseResume() -> void;
  auto OnPause() -> void;
  auto OnResume() -> void;
  auto ShutdownComplete() -> void;
  Thread* thread_{};
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

}  // namespace ballistica

#endif  // BALLISTICA_APP_APP_FLAVOR_H_
