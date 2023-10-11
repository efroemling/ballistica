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
  /// implementation, this simply returns true in the main thread. Note
  /// that, while it is valid for the graphics context thread to change over
  /// time, no more than one thread at a time should ever be considered the
  /// graphics context.
  virtual auto InGraphicsContext() -> bool;

  /// Push a call to be run in the app's graphics context. This may mean
  /// different things depending on the graphics architecture in use. On
  /// some platforms this simply pushes to the main thread. On others it may
  /// schedule a call to be run just before or after a frame draw in a
  /// dedicated render thread. The default implementation pushes to the main
  /// thread.
  template <typename F>
  void PushGraphicsContextCall(const F& lambda) {
    DoPushGraphicsContextRunnable(NewLambdaRunnableUnmanaged(lambda));
  }

  /// Return whether the current setup should show a cursor for mouse
  /// motion. This generally should be true for desktop type situations or
  /// if a mouse is present on a mobile device and false for purely touch
  /// based situations. This value may change over time if a mouse is
  /// plugged in or unplugged/etc. Default implementation returns true.
  virtual auto ShouldUseCursor() -> bool;

  /// Return whether the app-adapter is having the OS show a cursor.
  /// If this returns false, the engine will take care of drawing a cursor
  /// when necessary. If true, SetHardwareCursorVisible will be called
  /// periodically to inform the adapter what the cursor state should be.
  /// The default implementation returns false;
  virtual auto HasHardwareCursor() -> bool;

  /// If HasHardwareCursor() returns true, this will be called in the main
  /// thread periodically when the adapter should be hiding/showing the
  /// cursor.
  virtual void SetHardwareCursorVisible(bool visible);

  /// Called to get the cursor position when drawing. Default implementation
  /// returns the latest position delivered through the input subsystem, but
  /// subclasses may want to override to provide slightly more up to date
  /// values.
  virtual void CursorPositionForDraw(float* x, float* y);

  /// Put the app into a paused state. Should be called from the main
  /// thread. Pauses work, closes network sockets, etc. May correspond to
  /// being backgrounded on mobile, being minimized on desktop, etc. It is
  /// assumed that, as soon as this call returns, all work is finished and
  /// all threads can be suspended by the OS without any negative side
  /// effects.
  void SuspendApp();

  /// Resume the app; can correspond to foregrounding on mobile,
  /// unminimizing on desktop, etc. Spins threads back up, re-opens network
  /// sockets, etc.
  void UnsuspendApp();

  auto app_suspended() const { return app_suspended_; }

  /// Return whether this AppAdapter supports a 'fullscreen' toggle for its
  /// display. This currently will simply affect whether that option is
  /// available in display settings or via a hotkey.
  virtual auto CanToggleFullscreen() -> bool const;

  /// Return whether this AppAdapter supports vsync controls for its display.
  virtual auto SupportsVSync() -> bool const;

  /// Return whether this AppAdapter supports max-fps controls for its display.
  virtual auto SupportsMaxFPS() -> bool const;

  /// Return whether this platform supports soft-quit. A soft quit is
  /// when the app is reset/backgrounded/etc. but remains running in case
  /// needed again. Generally this is the behavior on mobile apps.
  virtual auto CanSoftQuit() -> bool;

  /// Implement soft-quit behavior. Will always be called in the logic
  /// thread. Make sure to also override CanBackQuit to reflect this being
  /// present. Note that when quitting the app yourself, you should use
  /// g_base->QuitApp(); do not call this directly.
  virtual void DoSoftQuit();

  /// Return whether this platform supports back-quit. A back quit is a
  /// variation of soft-quit generally triggered by a back button, which may
  /// give different results in the OS. For example on Android this may
  /// result in jumping back to the previous Android activity instead of
  /// just ending the current one and dumping to the home screen as normal
  /// soft quit might do.
  virtual auto CanBackQuit() -> bool;

  /// Implement back-quit behavior. Will always be called in the logic
  /// thread. Make sure to also override CanBackQuit to reflect this being
  /// present. Note that when quitting the app yourself, you should use
  /// g_base->QuitApp(); do not call this directly.
  virtual void DoBackQuit();

  /// Terminate the app. This can be immediate or by posting some high
  /// level event. There should be nothing left to do in the engine at
  /// this point.
  virtual void TerminateApp();

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
  void OnAppSuspend_();
  void OnAppUnsuspend_();
  bool app_suspended_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_H_
