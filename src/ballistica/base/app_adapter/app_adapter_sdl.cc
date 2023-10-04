// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/buildconfig/buildconfig_common.h"
#if BA_SDL_BUILD

#include "ballistica/base/app_adapter/app_adapter_sdl.h"
#include "ballistica/base/base.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

AppAdapterSDL::AppAdapterSDL() {
  assert(!g_core->HeadlessMode());
  assert(g_core->InMainThread());

  // Enable display-time debug logs via env var.
  auto val = g_core->platform->GetEnv("BA_DEBUG_LOG_SDL_FRAME_TIMING");
  if (val && *val == "1") {
    debug_log_sdl_frame_timing_ = true;
  }
}

void AppAdapterSDL::OnMainThreadStartApp() {
  // App is starting. Let's fire up the ol' SDL.
  uint32_t sdl_flags{SDL_INIT_VIDEO | SDL_INIT_JOYSTICK};

  // We may or may not want xinput on windows.
  if (g_buildconfig.ostype_windows()) {
    if (!g_core->platform->GetLowLevelConfigValue("enablexinput", 1)) {
      SDL_SetHint(SDL_HINT_XINPUT_ENABLED, "0");
    }
  }

  int result = SDL_Init(sdl_flags);
  if (result < 0) {
    FatalError(std::string("SDL_Init failed: ") + SDL_GetError());
  }

  // Register events we can send ourself.
  sdl_runnable_event_id_ = SDL_RegisterEvents(1);
  assert(sdl_runnable_event_id_ != (uint32_t)-1);

  // Note: parent class can add some input devices so need to bring up sdl
  // before we let it run. That code should maybe be relocated/refactored.
  AppAdapter::OnMainThreadStartApp();

  if (g_buildconfig.enable_sdl_joysticks()) {
    // We want events from joysticks.
    SDL_JoystickEventState(SDL_ENABLE);

    // Add already-existing SDL joysticks. Any added later will come
    // through as joystick-added events.
    //
    // TODO(ericf): Check to see if this is necessary or if we always get
    // connected events even for these initial ones.
    if (explicit_bool(true)) {
      int joystick_count = SDL_NumJoysticks();
      for (int i = 0; i < joystick_count; i++) {
        AppAdapterSDL::OnSDLJoystickAdded_(i);
      }
    }
  }
}

void AppAdapterSDL::DoApplyAppConfig() {
  assert(g_base->InLogicThread());

  g_base->graphics_server->PushSetScreenPixelScaleCall(
      g_base->app_config->Resolve(AppConfig::FloatID::kScreenPixelScale));

  auto graphics_quality_requested =
      g_base->graphics->GraphicsQualityFromAppConfig();

  auto texture_quality_requested =
      g_base->graphics->TextureQualityFromAppConfig();

  // Android res string.
  // std::string android_res =
  //     g_base->app_config->Resolve(AppConfig::StringID::kResolutionAndroid);

  bool fullscreen = g_base->app_config->Resolve(AppConfig::BoolID::kFullscreen);
  auto vsync = g_base->graphics->VSyncFromAppConfig();
  int max_fps = g_base->app_config->Resolve(AppConfig::IntID::kMaxFPS);

  // Tell the main thread to set up the screen with these settings.
  g_base->app_adapter->PushMainThreadCall([=] {
    SetScreen_(fullscreen, max_fps, vsync, texture_quality_requested,
               graphics_quality_requested);
  });
}

void AppAdapterSDL::RunMainThreadEventLoopToCompletion() {
  assert(g_core->InMainThread());

  while (!done_) {
    microsecs_t cycle_start_time = g_core->GetAppTimeMicrosecs();

    // Events.
    SDL_Event event;
    while (SDL_PollEvent(&event) && (!done_)) {
      HandleSDLEvent_(event);
    }

    // Draw.
    if (!hidden_ && g_base->graphics_server->TryRender()) {
      SDL_GL_SwapWindow(sdl_window_);
    }

    // Sleep.
    SleepUntilNextEventCycle_(cycle_start_time);

    // Repeat.
  }
}

void AppAdapterSDL::SleepUntilNextEventCycle_(microsecs_t cycle_start_time) {
  // Special case: if we're hidden, we simply sleep for a long bit; no fancy
  // timing.
  if (hidden_) {
    g_core->platform->SleepMillisecs(100);
    return;
  }

  // Special case which means no max, and thus no sleeping. Farewell poor
  // laptop battery; we hardly knew ye.
  if (max_fps_ == -1) {
    return;
  }

  // Normally we just calc when our next draw should happen and sleep 'til
  // then.
  microsecs_t now = g_core->GetAppTimeMicrosecs();
  auto used_max_fps = max_fps_;
  millisecs_t millisecs_per_frame = 1000000 / used_max_fps;

  // Special case: if we've got vsync enabled, let's tweak our drawing to
  // happen just a *tiny* bit faster than requested. This means, if our
  // max-fps matches the refresh rate, we'll be trying to render just a
  // *bit* faster than vsync which should push us up against the vsync wall
  // and keep vsync doing most of the delay work. In that case the logging
  // below should show mostly 'no sleep.'. Without this delay, our render
  // kick-offs tend to drift around the middle of the vsync cycle and I
  // worry there could be bad interference patterns in certain spots close
  // to the edges. Note that we want this tweak to be small enough that it
  // won't be noticable in situations where vsync and max-fps *don't* match.
  // For instance, limiting to 60hz on a 120hz vsynced monitor should still
  // work as expected.
  if (vsync_actually_enabled_) {
    millisecs_per_frame = 99 * millisecs_per_frame / 100;
  }
  microsecs_t target_time = cycle_start_time + millisecs_per_frame - oversleep_;

  // Set a minimum so we don't sleep if we're within a few millisecs of
  // where we want to be. Sleep tends to run over by a bit so we'll probably
  // render closer to our target time by just skipping the sleep. And the
  // oversleep system will compensate for our earliness just as it does if
  // we sleep too long.
  const microsecs_t min_sleep{2000};
  if (now + min_sleep >= target_time) {
    if (debug_log_sdl_frame_timing_) {
      Log(LogLevel::kDebug, "no sleep.");  // 'till brooklyn!
    }
  } else {
    if (debug_log_sdl_frame_timing_) {
      char buf[256];
      snprintf(buf, sizeof(buf), "render %.1f sleep %.1f",
               (now - cycle_start_time) / 1000.0f,
               (target_time - now) / 1000.0f);
      Log(LogLevel::kDebug, buf);
    }
    g_core->platform->SleepMicrosecs(target_time - now);
  }

  // Maintain an 'oversleep' amount to compensate for the timer not being
  // exact. This should keep us exactly at our target frame-rate in the
  // end.
  now = g_core->GetAppTimeMicrosecs();
  oversleep_ = now - target_time;

  // Prevent oversleep from compensating by more than a few millisecs per
  // frame (not sure if this would ever be a problem but lets be safe).
  oversleep_ = std::max(int64_t{-3000}, oversleep_);
  oversleep_ = std::min(int64_t{3000}, oversleep_);
}

void AppAdapterSDL::DoPushMainThreadRunnable(Runnable* runnable) {
  // Our main thread is the SDL event loop, so add this as an SDL event.
  assert(sdl_runnable_event_id_ != 0);
  SDL_Event event;
  SDL_memset(&event, 0, sizeof(event));
  event.type = sdl_runnable_event_id_;
  event.user.code = 0;
  event.user.data1 = runnable;
  event.user.data2 = 0;
  SDL_PushEvent(&event);
}

void AppAdapterSDL::DoExitMainThreadEventLoop() {
  assert(g_core->InMainThread());
  done_ = true;
}

void AppAdapterSDL::HandleSDLEvent_(const SDL_Event& event) {
  assert(g_core->InMainThread());
  assert(g_base);

  switch (event.type) {
    case SDL_JOYAXISMOTION:
    case SDL_JOYBUTTONDOWN:
    case SDL_JOYBUTTONUP:
    case SDL_JOYBALLMOTION:
    case SDL_JOYHATMOTION: {
      // It seems that joystick connection/disconnection callbacks can fire
      // while there are still events for that joystick in the queue. So
      // take care to ignore events for no-longer-existing joysticks.
      assert(event.jaxis.which == event.jbutton.which
             && event.jaxis.which == event.jhat.which);
      if (static_cast<size_t>(event.jbutton.which) >= sdl_joysticks_.size()
          || sdl_joysticks_[event.jbutton.which] == nullptr) {
        return;
      }
      if (JoystickInput* js = GetSDLJoystickInput_(&event)) {
        if (g_base) {
          g_base->input->PushJoystickEvent(event, js);
        }
      } else {
        Log(LogLevel::kError, "Unable to get SDL Joystick for event type "
                                  + std::to_string(event.type));
      }
      break;
    }

    case SDL_MOUSEBUTTONDOWN: {
      const SDL_MouseButtonEvent* e = &event.button;

      // Convert sdl's coords to normalized view coords.
      float x = static_cast<float>(e->x) / window_size_.x;
      float y = 1.0f - static_cast<float>(e->y) / window_size_.y;
      g_base->input->PushMouseDownEvent(e->button, Vector2f(x, y));
      break;
    }

    case SDL_MOUSEBUTTONUP: {
      const SDL_MouseButtonEvent* e = &event.button;

      // Convert sdl's coords to normalized view coords.
      float x = static_cast<float>(e->x) / window_size_.x;
      float y = 1.0f - static_cast<float>(e->y) / window_size_.y;
      g_base->input->PushMouseUpEvent(e->button, Vector2f(x, y));
      break;
    }

    case SDL_MOUSEMOTION: {
      const SDL_MouseMotionEvent* e = &event.motion;

      // Convert sdl's coords to normalized view coords.
      float x = static_cast<float>(e->x) / window_size_.x;
      float y = 1.0f - static_cast<float>(e->y) / window_size_.y;
      g_base->input->PushMouseMotionEvent(Vector2f(x, y));
      break;
    }

    case SDL_KEYDOWN: {
      g_base->input->PushKeyPressEvent(event.key.keysym);
      break;
    }

    case SDL_KEYUP: {
      g_base->input->PushKeyReleaseEvent(event.key.keysym);
      break;
    }

    case SDL_MOUSEWHEEL: {
      const SDL_MouseWheelEvent* e = &event.wheel;
      int scroll_speed{500};
      g_base->input->PushMouseScrollEvent(
          Vector2f(static_cast<float>(e->x * scroll_speed),
                   static_cast<float>(e->y * scroll_speed)));
      break;
    }

    case SDL_JOYDEVICEADDED:
      OnSDLJoystickAdded_(event.jdevice.which);
      break;

    case SDL_JOYDEVICEREMOVED:
      OnSDLJoystickRemoved_(event.jdevice.which);
      break;

    case SDL_QUIT:
      g_base->logic->event_loop()->PushCall([] { g_base->ui->ConfirmQuit(); });
      break;

    case SDL_TEXTINPUT: {
      g_base->input->PushTextInputEvent(event.text.text);
      break;
    }

    case SDL_WINDOWEVENT: {
      switch (event.window.event) {
        case SDL_WINDOWEVENT_MAXIMIZED: {
          if (g_buildconfig.ostype_macos() && !fullscreen_) {
            // Special case: on Mac, we wind up here if someone fullscreens
            // our window via the window widget. This *basically* is the
            // same thing as setting fullscreen through sdl, so we want to
            // treat this as if we've changed the setting ourself. We write
            // it to the config so that UIs can poll for it and pick up the
            // change. We don't do this on other platforms where a maximized
            // window is more distinctly different than a fullscreen one.
            fullscreen_ = true;
            g_base->logic->event_loop()->PushCall([] {
              g_base->python->objs()
                  .Get(BasePython::ObjID::kSetConfigFullscreenOnCall)
                  .Call();
            });
          }
          break;
        }

        case SDL_WINDOWEVENT_RESTORED:
          if (g_buildconfig.ostype_macos() && fullscreen_) {
            // See note above about Mac fullscreen.
            fullscreen_ = false;
            g_base->logic->event_loop()->PushCall([] {
              g_base->python->objs()
                  .Get(BasePython::ObjID::kSetConfigFullscreenOffCall)
                  .Call();
            });
          }
          break;

        case SDL_WINDOWEVENT_MINIMIZED:
          break;

        case SDL_WINDOWEVENT_HIDDEN: {
          // Let's keep track of when we're hidden so we can stop drawing
          // and sleep more. Theoretically we could put the app into a full
          // suspended state like we do on mobile (pausing event loops/etc.)
          // but that would be more involved; we'd need to ignore most SDL
          // events while sleeping (except for SDL_WINDOWEVENT_SHOWN) and
          // would need to rebuild our controller lists/etc when we resume.
          // For now just gonna keep things simple and keep running.
          hidden_ = true;
          break;
        }

        case SDL_WINDOWEVENT_SHOWN: {
          hidden_ = false;
          break;
        }

        case SDL_WINDOWEVENT_SIZE_CHANGED: {
          // Note: this should cover all size changes; there is also
          // SDL_WINDOWEVENT_RESIZED but according to the docs it only covers
          // external events such as user window resizes.
          UpdateScreenSizes_();
          break;
        }
        default:
          break;
      }
      break;
    }

    default: {
      // Lastly handle our custom events (can't since their
      // values are dynamic).
      if (event.type == sdl_runnable_event_id_) {
        auto* runnable = static_cast<Runnable*>(event.user.data1);
        runnable->RunAndLogErrors();
        delete runnable;
        return;
      }
      break;
    }
  }
}

void AppAdapterSDL::OnSDLJoystickAdded_(int device_index) {
  assert(g_base);
  assert(g_core->InMainThread());

  // Create the joystick here in the main thread and then pass it over to
  // the logic thread to be added to the action.
  auto* j = Object::NewDeferred<JoystickInput>(device_index);
  int instance_id = SDL_JoystickInstanceID(j->sdl_joystick());
  AddSDLInputDevice_(j, instance_id);
}

void AppAdapterSDL::OnSDLJoystickRemoved_(int index) {
  assert(g_core->InMainThread());
  assert(index >= 0);
  RemoveSDLInputDevice_(index);
}

void AppAdapterSDL::AddSDLInputDevice_(JoystickInput* input, int index) {
  assert(g_base && g_base->input != nullptr);
  assert(input != nullptr);
  assert(g_core->InMainThread());
  assert(index >= 0);

  // Keep a mapping of SDL input-device indices to our Joysticks.
  if (static_cast_check_fit<int>(sdl_joysticks_.size()) <= index) {
    sdl_joysticks_.resize(static_cast<size_t>(index) + 1, nullptr);
  }
  sdl_joysticks_[index] = input;

  g_base->input->PushAddInputDeviceCall(input, true);
}

void AppAdapterSDL::RemoveSDLInputDevice_(int index) {
  assert(g_core->InMainThread());
  assert(index >= 0);
  JoystickInput* j = GetSDLJoystickInput_(index);
  assert(j);
  if (static_cast_check_fit<int>(sdl_joysticks_.size()) > index) {
    sdl_joysticks_[index] = nullptr;
  } else {
    Log(LogLevel::kError, "Invalid index on RemoveSDLInputDevice: size is "
                              + std::to_string(sdl_joysticks_.size())
                              + "; index is " + std::to_string(index));
  }
  g_base->input->PushRemoveInputDeviceCall(j, true);
}

auto AppAdapterSDL::GetSDLJoystickInput_(const SDL_Event* e) const
    -> JoystickInput* {
  assert(g_core->InMainThread());
  int joy_id;

  // Attempt to pull the joystick id from the event.
  switch (e->type) {
    case SDL_JOYAXISMOTION:
      joy_id = e->jaxis.which;
      break;
    case SDL_JOYBUTTONDOWN:
    case SDL_JOYBUTTONUP:
      joy_id = e->jbutton.which;
      break;
    case SDL_JOYBALLMOTION:
      joy_id = e->jball.which;
      break;
    case SDL_JOYHATMOTION:
      joy_id = e->jhat.which;
      break;
    default:
      return nullptr;
  }
  return GetSDLJoystickInput_(joy_id);
}

auto AppAdapterSDL::GetSDLJoystickInput_(int sdl_joystick_id) const
    -> JoystickInput* {
  assert(g_core->InMainThread());
  for (auto sdl_joystick : sdl_joysticks_) {
    if ((sdl_joystick != nullptr) && (*sdl_joystick).sdl_joystick_id() >= 0
        && (*sdl_joystick).sdl_joystick_id() == sdl_joystick_id)
      return sdl_joystick;
  }
  return nullptr;  // Epic fail.
}

void AppAdapterSDL::SetScreen_(
    bool fullscreen, int max_fps, VSyncRequest vsync_requested,
    TextureQualityRequest texture_quality_requested,
    GraphicsQualityRequest graphics_quality_requested) {
  assert(InGraphicsContext());
  assert(!g_core->HeadlessMode());

  // If we know what we support, filter our request types to what is
  // supported. This will keep us from rebuilding contexts if request type
  // is flipping between different types that we don't support.
  if (g_base->graphics->has_supports_high_quality_graphics_value()) {
    if (!g_base->graphics->supports_high_quality_graphics()
        && graphics_quality_requested > GraphicsQualityRequest::kMedium) {
      graphics_quality_requested = GraphicsQualityRequest::kMedium;
    }
  }

  bool do_toggle_fs{};
  bool do_set_existing_fullscreen{};

  auto* gs = g_base->graphics_server;

  // We need a full renderer reload if quality values have changed
  // or if we don't have one yet.
  bool need_full_reload =
      ((sdl_window_ == nullptr
        || gs->texture_quality_requested() != texture_quality_requested)
       || (gs->graphics_quality_requested() != graphics_quality_requested)
       || !gs->texture_quality_set() || !gs->graphics_quality_set());

  if (need_full_reload) {
    ReloadRenderer_(fullscreen, graphics_quality_requested,
                    texture_quality_requested);
  } else if (fullscreen != fullscreen_) {
    SDL_SetWindowFullscreen(sdl_window_,
                            fullscreen ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
    fullscreen_ = fullscreen;
  }

  // VSync always gets set independent of the screen (though we set it down
  // here to make sure we have a screen when its set).
  VSync vsync;
  switch (vsync_requested) {
    case VSyncRequest::kNever:
      vsync = VSync::kNever;
      break;
    case VSyncRequest::kAlways:
      vsync = VSync::kAlways;
      break;
    case VSyncRequest::kAuto:
      vsync = VSync::kAdaptive;
      break;
    default:
      vsync = VSync::kNever;
      break;
  }
  if (vsync != vsync_) {
    switch (vsync) {
      case VSync::kUnset:
      case VSync::kNever: {
        SDL_GL_SetSwapInterval(0);
        vsync_actually_enabled_ = false;
        break;
      }
      case VSync::kAlways: {
        SDL_GL_SetSwapInterval(1);
        vsync_actually_enabled_ = true;
        break;
      }
      case VSync::kAdaptive: {
        // In this case, let's try setting to 'adaptive' and turn it off if
        // that is unsupported.
        auto result = SDL_GL_SetSwapInterval(-1);
        if (result == 0) {
          vsync_actually_enabled_ = true;
        } else {
          SDL_GL_SetSwapInterval(0);
          vsync_actually_enabled_ = false;
        }
        break;
      }
    }
    vsync_ = vsync;
  }

  // This we can set anytime. Probably could have just set it from the logic
  // thread where we read it, but let's be pedantic and keep everything to
  // the main thread.
  max_fps_ = max_fps;
  // Allow -1 to mean no max.
  if (max_fps_ != -1) {
    max_fps_ = std::max(10, max_fps_);
    max_fps_ = std::min(99999, max_fps_);
  }

  // Let the logic thread know we've got a graphics system up and running.
  // It may use this cue to kick off asset loads and other bootstrapping.
  g_base->logic->event_loop()->PushCall(
      [] { g_base->logic->OnGraphicsReady(); });
}

void AppAdapterSDL::ReloadRenderer_(
    bool fullscreen, GraphicsQualityRequest graphics_quality_requested,
    TextureQualityRequest texture_quality_requested) {
  assert(g_base->app_adapter->InGraphicsContext());

  auto* gs = g_base->graphics_server;

  if (gs->renderer() && gs->renderer_loaded()) {
    gs->UnloadRenderer();
  }

  // If we don't haven't yet, create our window and renderer.
  if (!sdl_window_) {
    fullscreen_ = fullscreen;

    // A reasonable default window size.
    auto width = static_cast<int>(kBaseVirtualResX * 0.8f);
    auto height = static_cast<int>(kBaseVirtualResY * 0.8f);

    uint32_t flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN
                     | SDL_WINDOW_ALLOW_HIGHDPI | SDL_WINDOW_RESIZABLE;
    if (fullscreen) {
      flags |= SDL_WINDOW_FULLSCREEN_DESKTOP;
    }

    int context_flags{};
    if (g_buildconfig.ostype_macos()) {
      // On Mac we ask for a GL 4.1 Core profile. This is supported by all
      // hardware that we officially support and is also the last version of
      // GL supported on Apple hardware. So we have a nice fixed target to
      // work with.
      SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4);
      SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1);
      SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK,
                          SDL_GL_CONTEXT_PROFILE_CORE);
      context_flags |= SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG;
    } else {
      // On other platforms, let's not ask for anything in particular.
      // We'll work with whatever they give us if its 4.x or 3.x or we'll
      // show a lovely error if it's older.

      // Wondering if there would be a smarter strategy here; for example
      // trying a few different specific core profiles.

      // Actually, in reading a bit more, Nvidia actually recommends
      // compatibility profiles and their core profiles may actually be
      // slightly slower due to extra checks, so what we're doing here might
      // be optimal.
    }
    if (g_buildconfig.debug_build()) {
      // Curious if this has any real effects anywhere.
      context_flags |= SDL_GL_CONTEXT_DEBUG_FLAG;
    }
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, context_flags);

    sdl_window_ =
        SDL_CreateWindow(nullptr, SDL_WINDOWPOS_UNDEFINED,
                         SDL_WINDOWPOS_UNDEFINED, width, height, flags);
    if (!sdl_window_) {
      FatalError("Unable to create SDL Window of size " + std::to_string(width)
                 + " by " + std::to_string(height));
    }
    sdl_gl_context_ = SDL_GL_CreateContext(sdl_window_);
    if (!sdl_gl_context_) {
      FatalError("Unable to create SDL GL Context");
    }

    SDL_SetWindowTitle(sdl_window_, "BallisticaKit");

    UpdateScreenSizes_();

    // Now assign a GL renderer to the graphics-server to do its work.
    assert(!gs->renderer());
    if (!gs->renderer()) {
      gs->set_renderer(new RendererGL());
    }
  }

  // Update graphics quality based on request.
  gs->set_graphics_quality_requested(graphics_quality_requested);
  gs->set_texture_quality_requested(texture_quality_requested);

  gs->LoadRenderer();
}

void AppAdapterSDL::UpdateScreenSizes_() {
  assert(g_base->app_adapter->InGraphicsContext());

  // Grab logical window dimensions (points?). This is the coordinate space
  // SDL's events deal in.
  int win_size_x, win_size_y;
  SDL_GetWindowSize(sdl_window_, &win_size_x, &win_size_y);
  window_size_ = Vector2f(win_size_x, win_size_y);

  // Also grab the new size of the drawable; this is our physical (pixel)
  // dimensions.
  int pixels_x, pixels_y;
  SDL_GL_GetDrawableSize(sdl_window_, &pixels_x, &pixels_y);
  g_base->graphics_server->SetScreenResolution(static_cast<float>(pixels_x),
                                               static_cast<float>(pixels_y));
}

auto AppAdapterSDL::CanToggleFullscreen() -> bool const { return true; }
auto AppAdapterSDL::SupportsVSync() -> bool const { return true; }
auto AppAdapterSDL::SupportsMaxFPS() -> bool const { return true; }

}  // namespace ballistica::base

#endif  // BA_SDL_BUILD
