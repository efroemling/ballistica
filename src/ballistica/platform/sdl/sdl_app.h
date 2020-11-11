// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PLATFORM_SDL_SDL_APP_H_
#define BALLISTICA_PLATFORM_SDL_SDL_APP_H_

#if BA_SDL_BUILD

#include <vector>

#include "ballistica/app/app.h"
#include "ballistica/math/vector2f.h"

namespace ballistica {

class SDLApp : public App {
 public:
  static auto InitSDL() -> void;
  explicit SDLApp(Thread* thread);
  auto HandleSDLEvent(const SDL_Event& event) -> void;
  auto RunEvents() -> void override;
  auto DidFinishRenderingFrame(FrameDef* frame) -> void override;
  auto SetAutoVSync(bool enable) -> void;
  static auto SDLJoystickConnected(int index) -> void;
  static auto SDLJoystickDisconnected(int index) -> void;
  auto OnBootstrapComplete() -> void override;

  /// Return g_app as a SDLApp. (assumes it actually is one).
  static SDLApp* get() {
    assert(g_app != nullptr);
    assert(dynamic_cast<SDLApp*>(g_app) == static_cast<SDLApp*>(g_app));
    return static_cast<SDLApp*>(g_app);
  }
  auto SetInitialScreenDimensions(const Vector2f& dimensions) -> void;

 private:
  // Given an sdl joystick ID, returns our ballistica input for it.
  auto GetSDLJoyStickInput(int sdl_joystick_id) const -> Joystick*;

  // The same but using sdl events.
  auto GetSDLJoyStickInput(const SDL_Event* e) const -> Joystick*;

  auto DoSwap() -> void;
  auto SwapBuffers() -> void;
  auto UpdateAutoVSync(int diff) -> void;
  auto AddSDLInputDevice(Joystick* input, int index) -> void;
  auto RemoveSDLInputDevice(int index) -> void;
  millisecs_t last_swap_time_{};
  millisecs_t swap_start_time_{};
  int too_slow_frame_count_{};
  bool auto_vsync_{};
  bool vsync_enabled_{true};
  float average_vsync_fps_{60.0f};
  int vsync_good_frame_count_{};
  int vsync_bad_frame_count_{};
  std::vector<Joystick*> sdl_joysticks_;

  /// This is in points; not pixels.
  Vector2f screen_dimensions_{1.0f, 1.0f};
};

}  // namespace ballistica

#endif  // BA_SDL_BUILD

#endif  // BALLISTICA_PLATFORM_SDL_SDL_APP_H_
