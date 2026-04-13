// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_SDL_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_SDL_H_

#include "ballistica/base/base.h"
#if BA_SDL_BUILD

#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/shared/math/vector2f.h"

// Predeclare for pointers.
struct SDL_Window;

namespace ballistica::base {

class AppAdapterSDL : public AppAdapter {
 public:
  /// Return g_base->app_adapter as an AppAdapterSDL. (Assumes it actually
  /// is one).
  static AppAdapterSDL* Get() {
    assert(g_base && g_base->app_adapter != nullptr);
    assert(dynamic_cast<AppAdapterSDL*>(g_base->app_adapter)
           == static_cast<AppAdapterSDL*>(g_base->app_adapter));
    return static_cast<AppAdapterSDL*>(g_base->app_adapter);
  }

  AppAdapterSDL();

  void OnMainThreadStartApp() override;

  auto TryRender() -> bool;

  auto FullscreenControlAvailable() const -> bool override;
  auto FullscreenControlKeyShortcut() const
      -> std::optional<std::string> override;
  auto SupportsVSync() -> bool const override;
  auto SupportsMaxFPS() -> bool const override;

  auto HasDirectKeyboardInput() -> bool override;
  void ApplyGraphicsSettings(const GraphicsSettings* settings) override;

  auto GetGraphicsSettings() -> GraphicsSettings* override;

  auto GetKeyName(int keycode) -> std::string override;

 protected:
  void DoPushMainThreadRunnable(Runnable* runnable) override;
  void RunMainThreadEventLoopToCompletion() override;
  void DoExitMainThreadEventLoop() override;
  auto InGraphicsContext() -> bool override;
  void DoPushGraphicsContextRunnable(Runnable* runnable) override;
  void CursorPositionForDraw(float* x, float* y) override;
  auto DoClipboardIsSupported() -> bool override;
  auto DoClipboardHasText() -> bool override;
  void DoClipboardSetText(const std::string& text) override;
  auto DoClipboardGetText() -> std::string override;

 private:
  class ScopedAllowGraphics_;
  struct GraphicsSettings_;

  void HandleSDLEvent_(const SDL_Event& event);
  void UpdateScreenSizes_();
  void ReloadRenderer_(const GraphicsSettings_* settings);
  void OnSDLJoystickAdded_(int index);
  void OnSDLJoystickRemoved_(int index);
  // Given an SDL joystick ID, returns our Ballistica input for it.
  auto GetSDLJoystickInput_(int sdl_joystick_id) const -> JoystickInput*;
  // The same but using sdl events.
  auto GetSDLJoystickInput_(const SDL_Event* e) const -> JoystickInput*;
  void AddSDLInputDevice_(JoystickInput* input, int index);
  void RemoveSDLInputDevice_(int index);
  void SleepUntilNextEventCycle_(microsecs_t cycle_start_time);
  void LogEventProcessingTime_(microsecs_t duration, int count);

  int max_fps_{60};
  bool done_{};
  bool fullscreen_{};
  bool vsync_actually_enabled_{};
  bool hidden_{};

  /// With this off, graphics call pushes simply get pushed to the main
  /// thread and graphics code is allowed to run any time in the main
  /// thread. When this is on, pushed graphics-context calls get enqueued
  /// and run as part of drawing, and graphics context calls are only
  /// allowed during draws. This strictness is generally not needed here but
  /// can be useful to test with, as it more closely matches other platforms
  /// that require such a setup.
  bool strict_graphics_context_{};
  bool strict_graphics_allowed_{};
  VSync vsync_{VSync::kUnset};
  uint32_t sdl_runnable_event_id_{};
  std::mutex strict_graphics_calls_mutex_;
  std::vector<Runnable*> strict_graphics_calls_;
  microsecs_t oversleep_{};
  std::vector<JoystickInput*> sdl_joysticks_;
  Vector2f window_size_{1.0f, 1.0f};
  SDL_Window* sdl_window_{};
  void* sdl_gl_context_{};
  seconds_t last_windowevent_close_time_{};
};

}  // namespace ballistica::base

#endif  // BA_SDL_BUILD

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_SDL_H_
