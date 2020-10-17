// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_APP_H_
#define BALLISTICA_APP_APP_H_

#include <map>
#include <memory>
#include <mutex>
#include <string>

#include "ballistica/core/module.h"

namespace ballistica {

/// Our high level app interface module.
/// It runs in the main thread and is what platform wrappers
/// should primarily interact with.
class App : public Module {
 public:
  explicit App(Thread* thread);
  ~App() override;

  /// This gets run after the constructor completes.
  /// Any setup that may trigger a virtual method/etc. should go here.
  auto PostInit() -> void;

  /// Return whether this class runs its own event loop.
  /// If true, BallisticaMain() will continuously ask the app for events
  /// until the app is quit, at which point BallisticaMain() returns.
  /// If false, BallisticaMain returns immediately and it is assumed
  /// that the OS handles the app lifecycle and pushes events to the app
  /// via callbacks/etc.
  auto UsesEventLoop() const -> bool;

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

  // These should be called by the window, view-controller, sdl,
  // or whatever is driving the app. They must be called from the main thread.

  /// Should be called on mobile when the app is backgrounded.
  /// Pauses threads, closes network sockets, etc.
  auto PauseApp() -> void;

  auto paused() const -> bool { return actually_paused_; }

  /// Should be called on mobile when the app is foregrounded.
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

  virtual auto OnBootstrapComplete() -> void;

  // Deferred calls that can be made from other threads.

  auto PushCursorUpdate(bool vis) -> void;
  auto PushShowOnlineScoreUICall(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version) -> void;
  auto PushGetFriendScoresCall(const std::string& game,
                               const std::string& game_version, void* data)
      -> void;
  auto PushSubmitScoreCall(const std::string& game,
                           const std::string& game_version, int64_t score)
      -> void;
  auto PushAchievementReportCall(const std::string& achievement) -> void;
  auto PushGetScoresToBeatCall(const std::string& level,
                               const std::string& config, void* py_callback)
      -> void;
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
  auto PushInterruptSignalSetupCall() -> void;

 private:
  auto UpdatePauseResume() -> void;
  auto OnPause() -> void;
  auto OnResume() -> void;
  auto ShutdownComplete() -> void;
  bool done_{};
  bool server_wrapper_managed_{};
  bool sys_paused_app_{};
  bool user_paused_app_{};
  bool actually_paused_{};
  std::unique_ptr<StressTest> stress_test_;
  millisecs_t last_resize_draw_event_time_{};
  millisecs_t last_app_resume_time_{};
  std::map<std::string, std::string> product_prices_;
  std::mutex product_prices_mutex_;
};

}  // namespace ballistica

#endif  // BALLISTICA_APP_APP_H_
