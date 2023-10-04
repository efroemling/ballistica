// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/generic/lambda_runnable.h"

namespace ballistica::base {

/// Adapts app behavior specific to a particular paradigm and/or api
/// environment. For example, 'Headless', 'VROculus', 'SDL', etc. These may
/// be mixed & matched with platform classes to define a build. For example,
/// on Windows, we might have SDL, VR, and Headless AppAdapters, but they
/// all might share the same CorePlatform and BasePlatform classes.
class AppAdapter {
 public:
  /// Instantiate the AppAdapter subclass for the current build.
  static auto Create() -> AppAdapter*;

  /// Called in the main thread when the app is being started.
  virtual void OnMainThreadStartApp();

  // Logic thread callbacks.
  virtual void OnAppStart();
  virtual void OnAppPause();
  virtual void OnAppResume();
  virtual void OnAppShutdown();
  virtual void OnAppShutdownComplete();
  virtual void OnScreenSizeChange();
  virtual void DoApplyAppConfig();

  /// Return whether this class manages the main thread event loop itself.
  /// Default is true. If this is true, RunMainThreadEventLoopToCompletion()
  /// will be called to run the app. This should return false on builds
  /// where the OS manages the main thread event loop and we just sit in it
  /// and receive events via callbacks/etc.
  virtual auto ManagesMainThreadEventLoop() const -> bool;

  /// When called, the main thread event loop should be run until
  /// ExitMainThreadEventLoop() is called. This will only be called if
  /// ManagesMainThreadEventLoop() returns true.
  virtual void RunMainThreadEventLoopToCompletion();

  /// Called when the main thread event loop should exit. Will only be
  /// called if ManagesMainThreadEventLoop() returns true.
  virtual void DoExitMainThreadEventLoop();

  /// Push a call to be run in the app's 'main' thread. This is the thread
  /// where the OS generally expects event and UI processing to happen in.
  template <typename F>
  void PushMainThreadCall(const F& lambda) {
    DoPushMainThreadRunnable(NewLambdaRunnableUnmanaged(lambda));
  }

  /// Should return whether the current thread and/or context setup is the
  /// one where graphics calls should be made. For the default
  /// implementation, this simply returns true in the main thread.
  virtual auto InGraphicsContext() -> bool;

  /// Push a call to be run in the app's graphics context. Be aware that
  /// this may mean different threads on different platforms.
  template <typename F>
  void PushGraphicsContextCall(const F& lambda) {
    DoPushGraphicsContextRunnable(NewLambdaRunnableUnmanaged(lambda));
  }

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

  /// Return whether this AppAdapter supports a 'fullscreen' toggle for its
  /// display. This currently will simply affect whether that option is
  /// available in display settings or via a hotkey.
  virtual auto CanToggleFullscreen() -> bool const;

  /// Return whether this AppAdapter supports vsync controls for its display.
  virtual auto SupportsVSync() -> bool const;

  /// Return whether this AppAdapter supports max-fps controls for its display.
  virtual auto SupportsMaxFPS() -> bool const;

 protected:
  AppAdapter();
  virtual ~AppAdapter();

  /// Push a raw pointer Runnable to the platform's 'main' thread. The main
  /// thread should call its RunAndLogErrors() method and then delete it.
  virtual void DoPushMainThreadRunnable(Runnable* runnable) = 0;

  /// Push a raw pointer Runnable to be run in the platform's graphics
  /// context. By default this is simply the main thread.
  virtual void DoPushGraphicsContextRunnable(Runnable* runnable);

 private:
  void OnAppPause_();
  void OnAppResume_();
  bool app_paused_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_
