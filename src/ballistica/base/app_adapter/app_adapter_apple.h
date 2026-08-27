// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_

#if BA_XCODE_BUILD

#include <atomic>
#include <functional>
#include <list>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/shared/generic/runnable.h"
#include "ballistica/shared/math/vector2f.h"

namespace ballistica::base {

class AppAdapterApple : public AppAdapter {
 public:
  /// Given base, returns app-adapter cast to our type. This assumes it
  /// actually *is* our type.
  static auto Get(BaseFeatureSet* base) -> AppAdapterApple* {
    auto* val = static_cast<AppAdapterApple*>(base->app_adapter);
    assert(val);
    assert(dynamic_cast<AppAdapterApple*>(base->app_adapter) == val);
    return val;
  }

  void OnMainThreadStartApp() override;

  auto ManagesMainThreadEventLoop() const -> bool override;
  void ApplyAppConfig() override;

  /// Called by FromSwift.
  auto TryRender() -> bool;

  auto FullscreenControlAvailable() const -> bool override;
  auto FullscreenControlGet() const -> bool override;
  void FullscreenControlSet(bool fullscreen) override;
  auto FullscreenControlKeyShortcut() const
      -> std::optional<std::string> override;

  /// Called by FromSwift (on the main thread) when the OS reports the main
  /// window entering/exiting fullscreen. We cache the value so the logic
  /// thread can read it via FullscreenControlGet without a cross-thread Swift
  /// call. Static because macOS window state restoration can re-enter
  /// fullscreen during launch, *before* the engine (and this adapter) exists;
  /// a static published flag accepts the value at any time. Safe to call from
  /// any thread.
  static void OnFullscreenChanged(bool fullscreen);

  /// Called by FromSwift (on the main thread) when input indicates whether a
  /// pointing device (trackpad/mouse) or direct touch is currently being
  /// used. On change, flips the UI's touch-mode on the logic thread. This is
  /// the Apple analog of Android's PlatformAndroid::PushUsingPointingDevice_;
  /// touch_mode == !using_pointing_device.
  void SetUsingPointingDevice(bool pointing);

  auto ApplyJoystickFeedback(JoystickInput* device, const FeedbackEvent& event)
      -> int override;
  void StopJoystickFeedback(JoystickInput* device) override;

  auto HasDirectKeyboardInput() -> bool override;
  void EnableResizeFriendlyMode(int width, int height);

  auto GetKeyRepeatDelay() -> float override;
  auto GetKeyRepeatInterval() -> float override;
  auto GetKeyName(int keycode) -> std::string override;
  auto NativeReviewRequestSupported() -> bool override;

 protected:
  void DoPushMainThreadRunnable(Runnable* runnable) override;
  void DoPushGraphicsContextRunnable(Runnable* runnable) override;
  auto InGraphicsContext() -> bool override;
  auto ShouldUseCursor() -> bool override;
  auto HasHardwareCursor() -> bool override;
  void SetHardwareCursorVisible(bool visible) override;
  void TerminateApp() override;
  void ApplyGraphicsSettings(const GraphicsSettings* settings) override;
  auto DoClipboardIsSupported() -> bool override;
  auto DoClipboardHasText() -> bool override;
  void DoClipboardSetText(const std::string& text) override;
  auto DoClipboardGetText() -> std::string override;
  void DoClipboardGetTextAsync(
      std::function<void(std::optional<std::string>)> completion_call) override;
  void DoNativeReviewRequest() override;

 private:
  class ScopedAllowGraphics_;

  void ReloadRenderer_(const GraphicsSettings* settings);

#if BA_PLATFORM_IOS
  // Pending clipboard-read completions, appended and popped (FIFO) only
  // in the logic thread; completion order is guaranteed to match request
  // order since reads run on a serial queue (see uikit_pasteboard.mm).
  std::list<std::function<void(std::optional<std::string>)>>
      clipboard_get_text_calls_;
#endif

  // Static so Swift's fullscreen pushes (OnFullscreenChanged) can land
  // before the adapter instance exists; see that method's comment.
  static std::atomic<bool> fullscreen_control_value_;

  std::thread::id graphics_thread_{};
  // Read+written only on the main thread (FromSwift::PushUsingPointingDevice),
  // so a plain bool suffices. Mirrors Android's using_pointing_device_.
  bool using_pointing_device_{};
  bool graphics_allowed_{};
  uint8_t resize_friendly_frames_{};
  Vector2f resize_target_resolution_{-1.0f, -1.0f};
  std::mutex graphics_calls_mutex_;
  std::vector<Runnable*> graphics_calls_;
};

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_
