// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_

#if BA_XCODE_BUILD

#include <mutex>
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
  void DoNativeReviewRequest() override;

 private:
  class ScopedAllowGraphics_;

  void ReloadRenderer_(const GraphicsSettings* settings);

  std::thread::id graphics_thread_{};
  bool graphics_allowed_{};
  uint8_t resize_friendly_frames_{};
  Vector2f resize_target_resolution_{-1.0f, -1.0f};
  std::mutex graphics_calls_mutex_;
  std::vector<Runnable*> graphics_calls_;
};

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_
