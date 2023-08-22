// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_SDL_H_
#define BALLISTICA_BASE_APP_APP_SDL_H_

#if BA_SDL_BUILD

#include <vector>

#include "ballistica/base/app/app.h"
#include "ballistica/shared/math/vector2f.h"

namespace ballistica::base {

class AppSDL : public App {
 public:
  static void InitSDL();
  AppSDL();
  void HandleSDLEvent(const SDL_Event& event);
  void RunEvents() override;
  void DidFinishRenderingFrame(FrameDef* frame) override;
  void SetAutoVSync(bool enable);
  void OnMainThreadStartApp() override;

  /// Return g_base->app as an AppSDL. (assumes it actually is one).
  static AppSDL* Get() {
    assert(g_base && g_base->app != nullptr);
    assert(dynamic_cast<AppSDL*>(g_base->app)
           == static_cast<AppSDL*>(g_base->app));
    return static_cast<AppSDL*>(g_base->app);
  }
  void SetInitialScreenDimensions(const Vector2f& dimensions);

 private:
  // Given an sdl joystick ID, returns our Ballistica input for it.
  auto GetSDLJoystickInput_(int sdl_joystick_id) const -> JoystickInput*;
  // The same but using sdl events.
  auto GetSDLJoystickInput_(const SDL_Event* e) const -> JoystickInput*;
  static void SDLJoystickConnected_(int index);
  static void SDLJoystickDisconnected_(int index);
  void DoSwap_();
  void SwapBuffers_();
  void UpdateAutoVSync_(int diff);
  void AddSDLInputDevice_(JoystickInput* input, int index);
  void RemoveSDLInputDevice_(int index);
  millisecs_t last_swap_time_{};
  millisecs_t swap_start_time_{};
  int too_slow_frame_count_{};
  bool auto_vsync_{};
  bool vsync_enabled_{true};
  float average_vsync_fps_{60.0f};
  int vsync_good_frame_count_{};
  int vsync_bad_frame_count_{};
  std::vector<JoystickInput*> sdl_joysticks_;
  /// This is in points, not pixels.
  Vector2f screen_dimensions_{1.0f, 1.0f};
};

}  // namespace ballistica::base

#endif  // BA_SDL_BUILD

#endif  // BALLISTICA_BASE_APP_APP_SDL_H_
