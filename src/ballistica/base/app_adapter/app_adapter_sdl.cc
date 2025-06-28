// Released under the MIT License. See LICENSE for details.

#if BA_SDL_BUILD

#include "ballistica/base/app_adapter/app_adapter_sdl.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
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
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/buildconfig/buildconfig_common.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

/// RAII-friendly way to mark where in the main thread we're allowed to run
/// graphics code (only applies in strict-graphics-context mode).
class AppAdapterSDL::ScopedAllowGraphics_ {
 public:
  explicit ScopedAllowGraphics_(AppAdapterSDL* adapter) : adapter_{adapter} {
    assert(!adapter_->strict_graphics_allowed_);
    adapter->strict_graphics_allowed_ = true;
  }
  ~ScopedAllowGraphics_() {
    assert(adapter_->strict_graphics_allowed_);
    adapter_->strict_graphics_allowed_ = false;
  }

 private:
  AppAdapterSDL* adapter_;
};

AppAdapterSDL::AppAdapterSDL() {
  assert(!g_core->HeadlessMode());
  assert(g_core->InMainThread());
}

void AppAdapterSDL::OnMainThreadStartApp() {
  AppAdapter::OnMainThreadStartApp();

  // App is starting. Let's fire up the ol' SDL.
  uint32_t sdl_flags{SDL_INIT_VIDEO | SDL_INIT_JOYSTICK};

  if (strict_graphics_context_) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kWarning,
                         "AppAdapterSDL strict_graphics_context_ is enabled."
                         " Remember to turn this off.");
  }

  // We may or may not want xinput on windows.
  if (g_buildconfig.platform_windows()) {
    if (!g_core->platform->GetLowLevelConfigValue("enablexinput", 1)) {
      SDL_SetHint(SDL_HINT_XINPUT_ENABLED, "0");
    }
  }

  // We wrangle our own signal handling; don't bring SDL into it.
  SDL_SetHint(SDL_HINT_NO_SIGNAL_HANDLERS, "1");

  int result = SDL_Init(sdl_flags);
  if (result < 0) {
    FatalError(std::string("SDL_Init failed: ") + SDL_GetError());
  }

  // Register events we can send ourself.
  sdl_runnable_event_id_ = SDL_RegisterEvents(1);
  assert(sdl_runnable_event_id_ != static_cast<uint32_t>(-1));

  // SDL builds just assume keyboard input is available.
  g_base->input->PushCreateKeyboardInputDevices();

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

  // This adapter draws a software cursor; hide the actual OS one.
  SDL_ShowCursor(SDL_DISABLE);
}

/// Our particular flavor of graphics settings.
struct AppAdapterSDL::GraphicsSettings_ : public GraphicsSettings {
  bool fullscreen = g_base->app_config->Resolve(AppConfig::BoolID::kFullscreen);
  VSyncRequest vsync = g_base->graphics->VSyncFromAppConfig();
  int max_fps = g_base->app_config->Resolve(AppConfig::IntID::kMaxFPS);
};

auto AppAdapterSDL::GetGraphicsSettings() -> GraphicsSettings* {
  assert(g_base->InLogicThread());
  return new GraphicsSettings_();
}

void AppAdapterSDL::ApplyGraphicsSettings(
    const GraphicsSettings* settings_base) {
  assert(g_core->InMainThread());
  assert(!g_core->HeadlessMode());

  // In strict mode, allow graphics stuff while in here.
  auto allow = ScopedAllowGraphics_(this);

  // Settings will always be our subclass (since we created it).
  auto* settings = static_cast<const GraphicsSettings_*>(settings_base);

  // Apply any changes.
  bool do_toggle_fs{};
  bool do_set_existing_fullscreen{};

  auto* graphics_server = g_base->graphics_server;

  // We need a full renderer reload if quality values have changed
  // or if we don't have a renderer yet.
  bool need_full_reload = ((sdl_window_ == nullptr
                            || graphics_server->texture_quality_requested()
                                   != settings->texture_quality)
                           || (graphics_server->graphics_quality_requested()
                               != settings->graphics_quality));

  if (need_full_reload) {
    ReloadRenderer_(settings);
  } else if (settings->fullscreen != fullscreen_) {
    SDL_SetWindowFullscreen(
        sdl_window_, settings->fullscreen ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
    fullscreen_ = settings->fullscreen;
  }

  // VSync always gets set independent of the screen (though we set it down
  // here to make sure we have a screen when its set).
  VSync vsync;
  switch (settings->vsync) {
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
  max_fps_ = settings->max_fps;

  // Take -1 to mean no max. Otherwise clamp to a reasonable range.
  if (max_fps_ != -1) {
    max_fps_ = std::max(10, max_fps_);
    max_fps_ = std::min(99999, max_fps_);
  }
}

void AppAdapterSDL::RunMainThreadEventLoopToCompletion() {
  assert(g_core->InMainThread());

  while (!done_) {
    auto cycle_start_time{g_core->AppTimeMicrosecs()};

    // Events.
    SDL_Event event;
    int event_count{};
    while (SDL_PollEvent(&event) && (!done_)) {
      HandleSDLEvent_(event);
      event_count++;
    }

    // Draw.
    auto draw_start_time{g_core->AppTimeMicrosecs()};
    LogEventProcessingTime_(draw_start_time - cycle_start_time, event_count);
    if (!hidden_ && TryRender()) {
      SDL_GL_SwapWindow(sdl_window_);
    }

    // Sleep.
    SleepUntilNextEventCycle_(cycle_start_time);

    // Repeat.
  }
}

void AppAdapterSDL::LogEventProcessingTime_(microsecs_t duration, int count) {
  // Note if events took more than 2 milliseconds.
  if (duration < 1000) {
    return;
  }
  g_core->logging->Log(
      LogName::kBaPerformance, LogLevel::kDebug, [duration, count] {
        char buf[256];
        snprintf(buf, sizeof(buf),
                 "event processing took too long (%.2fms for %d events)",
                 duration / 1000.0f, count);
        return std::string(buf);
      });
}

auto AppAdapterSDL::TryRender() -> bool {
  if (strict_graphics_context_) {
    // In strict mode, allow graphics stuff in here. Otherwise we allow it
    // anywhere in the main thread.
    auto allow = ScopedAllowGraphics_(this);

    // Run & release any pending runnables.
    std::vector<Runnable*> calls;
    {
      // Pull calls off the list before running them; this way we only need
      // to grab the list lock for a moment.
      auto lock = std::scoped_lock(strict_graphics_calls_mutex_);
      if (!strict_graphics_calls_.empty()) {
        strict_graphics_calls_.swap(calls);
      }
    }
    for (auto* call : calls) {
      call->RunAndLogErrors();
      delete call;
    }
    // Lastly render.
    return g_base->graphics_server->TryRender();
  } else {
    // Simpler path; just render.
    return g_base->graphics_server->TryRender();
  }
}

void AppAdapterSDL::SleepUntilNextEventCycle_(microsecs_t cycle_start_time) {
  // Special case: if we're hidden, we simply sleep for a long bit; no fancy
  // timing.
  if (hidden_) {
    g_core->platform->SleepSeconds(0.1);
    return;
  }

  // Special case which means no max, and thus no sleeping. Farewell poor
  // laptop battery; we hardly knew ye.
  if (max_fps_ == -1) {
    return;
  }

  // Normally we just calc when our next draw should happen and sleep 'til
  // then.
  microsecs_t now = g_core->AppTimeMicrosecs();
  auto used_max_fps = max_fps_;
  millisecs_t millisecs_per_frame = 1000000 / used_max_fps;

  // Special case: if we've got vsync enabled, let's tweak our drawing to
  // happen just a *tiny* bit faster than requested. This means, if our
  // max-fps matches the refresh rate, we should gently push us up against
  // the vsync wall and keep vsync doing most of the delay work. In that
  // case the logging below should show mostly 'sleep skipped.'. Without this
  // delay, our render kick-offs tend to drift around the middle of the
  // vsync cycle and I worry there could be bad interference patterns in
  // certain spots close to the edges. Note that we want this tweak to be
  // small enough that it won't be noticable in situations where vsync and
  // max-fps *don't* match. For instance, limiting to 60hz on a 120hz
  // vsynced monitor should still work as expected.
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
    g_core->logging->Log(LogName::kBaPerformance, LogLevel::kDebug,
                         [now, cycle_start_time, target_time] {
                           char buf[256];
                           snprintf(buf, sizeof(buf),
                                    "render %.1fms sleep skipped",
                                    (now - cycle_start_time) / 1000.0f);
                           return std::string(buf);
                         });
  } else {
    g_core->logging->Log(LogName::kBaPerformance, LogLevel::kDebug,
                         [now, cycle_start_time, target_time] {
                           char buf[256];
                           snprintf(buf, sizeof(buf),
                                    "render %.1fms sleep %.1fms",
                                    (now - cycle_start_time) / 1000.0f,
                                    (target_time - now) / 1000.0f);
                           return std::string(buf);
                         });
    g_core->platform->SleepMicrosecs(target_time - now);
  }

  // Maintain an 'oversleep' amount to compensate for the timer not being
  // exact. This should keep us exactly at our target frame-rate in the
  // end.
  now = g_core->AppTimeMicrosecs();
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

  auto starttime{core::CorePlatform::TimeMonotonicMicrosecs()};
  bool log_long_events{true};

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
        break;
      }
      if (JoystickInput* js = GetSDLJoystickInput_(&event)) {
        if (g_base) {
          g_base->input->PushJoystickEvent(event, js);
        }
      } else {
        g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                             "Unable to get SDL Joystick for event type "
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
      if (!event.key.repeat) {
        g_base->input->PushKeyPressEvent(event.key.keysym);
      }
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
      if (g_core->AppTimeSeconds() - last_windowevent_close_time_ < 0.1) {
        // If they hit the window close button, skip the confirm.
        g_base->QuitApp(false);
      } else {
        // For all other quits we might want to default to a confirm dialog.
        // Update: going to try without confirm for a bit and see how that
        // feels.
        g_base->QuitApp(false);
      }
      break;

    case SDL_TEXTINPUT: {
      g_base->input->PushTextInputEvent(event.text.text);
      break;
    }

    case SDL_WINDOWEVENT: {
      switch (event.window.event) {
        case SDL_WINDOWEVENT_ENTER:
          g_base->input->set_cursor_in_window(true);
          break;

        case SDL_WINDOWEVENT_LEAVE:
          g_base->input->set_cursor_in_window(false);
          break;

        case SDL_WINDOWEVENT_CLOSE: {
          // Simply note that this happened. We use this to adjust our
          // SDL_QUIT behavior (quit is called right after this).
          last_windowevent_close_time_ = g_core->AppTimeSeconds();
          break;
        }

        case SDL_WINDOWEVENT_MAXIMIZED: {
          if (g_buildconfig.platform_macos() && !fullscreen_) {
            // Special case: on Mac, we wind up here if someone fullscreens
            // our window via the window widget. This *basically* is the
            // same thing as setting fullscreen through sdl, so we want to
            // treat this as if we've changed the setting ourself. We write
            // it to the config so that UIs can poll for it and pick up the
            // change. We don't do this on other platforms where a maximized
            // window is more distinctly different than a fullscreen one.
            // Though I guess some Linux window managers have a fullscreen
            // function so theoretically we should there. Le sigh. Maybe SDL
            // 3 will tidy up this situation.
            fullscreen_ = true;
            g_base->logic->event_loop()->PushCall([] {
              g_base->python->objs()
                  .Get(BasePython::ObjID::kStoreConfigFullscreenOnCall)
                  .Call();
            });
          }
          break;
        }

        case SDL_WINDOWEVENT_RESTORED:
          if (g_buildconfig.platform_macos() && fullscreen_) {
            // See note above about Mac fullscreen.
            fullscreen_ = false;
            g_base->logic->event_loop()->PushCall([] {
              g_base->python->objs()
                  .Get(BasePython::ObjID::kStoreConfigFullscreenOffCall)
                  .Call();
            });
          }
          break;

        case SDL_WINDOWEVENT_MINIMIZED:
          break;

        case SDL_WINDOWEVENT_HIDDEN: {
          // We plug this into the app's overall 'Active' state so it can
          // pause stuff or throttle down processing or whatever else.
          if (!hidden_) {
            g_base->SetAppActive(false);
          }
          // Also note that we are *completely* hidden, so we can totally
          // stop drawing ('Inactive' app state does not imply this in and
          // of itself).
          hidden_ = true;
          break;
        }

        case SDL_WINDOWEVENT_SHOWN: {
          if (hidden_) {
            g_base->SetAppActive(true);
          }
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
        auto starttime2{core::CorePlatform::TimeMonotonicMicrosecs()};

        auto* runnable = static_cast<Runnable*>(event.user.data1);
        assert(runnable);
        runnable->RunAndLogErrors();

        // Log calls longer than a millisecond or so.
        log_long_events = false;  // We handle this ourself.
        auto duration{core::CorePlatform::TimeMonotonicMicrosecs()
                      - starttime2};
        if (duration > 1000) {
          g_core->logging->Log(
              LogName::kBaPerformance, LogLevel::kDebug, [duration, runnable] {
                char buf[256];
                snprintf(buf, sizeof(buf),
                         "main thread runnable took too long (%.2fms): %s",
                         duration / 1000.0f,
                         runnable->GetObjectDescription().c_str());
                return std::string(buf);
              });
        }
        delete runnable;
      }
      break;
    }
  }

  if (log_long_events) {
    // Make noise for anything taking longer than a millisecond or so.
    auto duration{core::CorePlatform::TimeMonotonicMicrosecs() - starttime};
    if (duration > 1000) {
      g_core->logging->Log(
          LogName::kBaPerformance, LogLevel::kDebug, [duration] {
            char buf[256];
            snprintf(buf, sizeof(buf), "sdl event took too long (%.2fms)",
                     duration / 1000.0f);
            return std::string(buf);
          });
    }
  }
}

void AppAdapterSDL::OnSDLJoystickAdded_(int device_index) {
  assert(g_base);
  assert(g_core->InMainThread());

  // Create the joystick here in the main thread and then pass it over to
  // the logic thread to be added to the action.
  JoystickInput* j{};
  try {
    j = Object::NewDeferred<JoystickInput>(device_index);
  } catch (const std::exception& exc) {
    g_core->logging->Log(
        LogName::kBaInput, LogLevel::kError,
        std::string("Error creating JoystickInput for SDL device-index "
                    + std::to_string(device_index) + ": ")
            + exc.what());
    return;
  }
  assert(j != nullptr);
  auto instance_id = SDL_JoystickInstanceID(j->sdl_joystick());
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

  // Note: am running into this with a PS5 controller on macOS Sequoia beta.
  if (!j) {
    g_core->logging->Log(
        LogName::kBaInput, LogLevel::kError,
        "GetSDLJoystickInput_() returned nullptr on RemoveSDLInputDevice_();"
        " joysticks size is "
            + std::to_string(sdl_joysticks_.size()) + "; index is "
            + std::to_string(index) + ".");
    return;
  }

  assert(j);
  if (static_cast_check_fit<int>(sdl_joysticks_.size()) > index) {
    sdl_joysticks_[index] = nullptr;
  } else {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "Invalid index on RemoveSDLInputDevice: size is "
                             + std::to_string(sdl_joysticks_.size())
                             + "; index is " + std::to_string(index) + ".");
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
  for (auto* sdl_joystick : sdl_joysticks_) {
    if ((sdl_joystick != nullptr) && sdl_joystick->sdl_joystick_id() >= 0
        && sdl_joystick->sdl_joystick_id() == sdl_joystick_id)
      return sdl_joystick;
  }
  return nullptr;  // Epic fail.
}

void AppAdapterSDL::ReloadRenderer_(const GraphicsSettings_* settings) {
  assert(g_base->app_adapter->InGraphicsContext());

  auto* gs = g_base->graphics_server;

  if (gs->renderer() && gs->renderer_loaded()) {
    gs->UnloadRenderer();
  }

  // If we don't haven't yet, create our window and renderer.
  if (!sdl_window_) {
    fullscreen_ = settings->fullscreen;

    // A reasonable default window size.
    int width, height;
    if (g_base->ui->uiscale() == UIScale::kSmall) {
      width = static_cast<int>(1300.0f * 0.8f);
      height = static_cast<int>(600.0f * 0.8f);
    } else {
      width = static_cast<int>(kBaseVirtualResX * 0.8f);
      height = static_cast<int>(kBaseVirtualResY * 0.8f);
    }

    uint32_t flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN
                     | SDL_WINDOW_ALLOW_HIGHDPI | SDL_WINDOW_RESIZABLE;
    if (settings->fullscreen) {
      flags |= SDL_WINDOW_FULLSCREEN_DESKTOP;
    }

    int context_flags{};
    if (g_buildconfig.platform_macos()) {
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

  // Update graphics-server's qualities based on request.
  gs->set_graphics_quality_requested(settings->graphics_quality);
  gs->set_texture_quality_requested(settings->texture_quality);

  gs->LoadRenderer();
}

void AppAdapterSDL::UpdateScreenSizes_() {
  // This runs in the main thread in response to SDL events.
  assert(g_core->InMainThread());

  // Grab logical window dimensions (points?). This is the coordinate space
  // SDL's events deal in.
  int win_size_x, win_size_y;
  SDL_GetWindowSize(sdl_window_, &win_size_x, &win_size_y);
  window_size_ = Vector2f(win_size_x, win_size_y);

  // Also grab the new size of the drawable; this is our physical (pixel)
  // dimensions.
  int pixels_x, pixels_y;
  SDL_GL_GetDrawableSize(sdl_window_, &pixels_x, &pixels_y);

  // Push this over to the logic thread which owns the canonical value
  // for this.
  g_base->logic->event_loop()->PushCall([pixels_x, pixels_y] {
    g_base->graphics->SetScreenResolution(static_cast<float>(pixels_x),
                                          static_cast<float>(pixels_y));
  });
}

auto AppAdapterSDL::InGraphicsContext() -> bool {
  // In strict mode, make sure we're in the right thread *and* within our
  // render call.
  if (strict_graphics_context_) {
    return g_core->InMainThread() && strict_graphics_allowed_;
  }
  // By default, allow anywhere in main thread.
  return g_core->InMainThread();
}

void AppAdapterSDL::DoPushGraphicsContextRunnable(Runnable* runnable) {
  // In strict mode, make sure we're in our TryRender() call.
  if (strict_graphics_context_) {
    auto lock = std::scoped_lock(strict_graphics_calls_mutex_);
    if (strict_graphics_calls_.size() > 1000) {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                  "strict_graphics_calls_ got too big.");
    }
    strict_graphics_calls_.push_back(runnable);
  } else {
    DoPushMainThreadRunnable(runnable);
  }
}

void AppAdapterSDL::CursorPositionForDraw(float* x, float* y) {
  // Note: disabling this code, but leaving it in here for now as a proof of
  // concept in case its worth revisiting later. In my current tests on Mac,
  // Windows, and Linux, I'm seeing basicaly zero difference between
  // immediate calculated values and ones from the event system, so I'm
  // guessing remaining latency might be coming from the fact that frames
  // tend to get assembled 1/60th of a second before it is displayed or
  // whatnot. It'd probably be a better use of time to just wire up hardware
  // cursor support for this build.
  if (explicit_bool(true)) {
    AppAdapter::CursorPositionForDraw(x, y);
    return;
  }

  assert(x && y);

  // Grab latest values from the input subsystem (what would get used by
  // default).
  float event_x = g_base->input->cursor_pos_x();
  float event_y = g_base->input->cursor_pos_y();

  // Now ask sdl for it's latest values and wrangle the math ourself.
  int sdl_x, sdl_y;
  SDL_GetMouseState(&sdl_x, &sdl_y);

  // Convert window coords to normalized.
  float normalized_x = static_cast<float>(sdl_x) / window_size_.x;
  float normalized_y = 1.0f - static_cast<float>(sdl_y) / window_size_.y;

  // Convert normalized coords to virtual coords.
  float immediate_x = g_base->graphics->PixelToVirtualX(
      normalized_x * g_base->graphics->screen_pixel_width());
  float immediate_y = g_base->graphics->PixelToVirtualY(
      normalized_y * g_base->graphics->screen_pixel_height());

  float diff_x = immediate_x - event_x;
  float diff_y = immediate_y - event_y;
  printf("DIFFS: %.2f %.2f\n", diff_x, diff_y);
  fflush(stdout);

  *x = immediate_x;
  *y = immediate_y;
}

auto AppAdapterSDL::FullscreenControlAvailable() const -> bool { return true; }
auto AppAdapterSDL::FullscreenControlKeyShortcut() const
    -> std::optional<std::string> {
  // On our SDL build we support F11 and Alt+Enter to toggle fullscreen.
  // Let's mention Alt+Enter which seems like it might be more commonly used
  return "Alt+Enter";
};

auto AppAdapterSDL::SupportsVSync() -> bool const { return true; }
auto AppAdapterSDL::SupportsMaxFPS() -> bool const { return true; }

auto AppAdapterSDL::HasDirectKeyboardInput() -> bool {
  // We always provide direct keyboard events.
  return true;
}

auto AppAdapterSDL::DoClipboardIsSupported() -> bool { return true; }

auto AppAdapterSDL::DoClipboardHasText() -> bool {
  return SDL_HasClipboardText();
}

void AppAdapterSDL::DoClipboardSetText(const std::string& text) {
  SDL_SetClipboardText(text.c_str());
}

auto AppAdapterSDL::DoClipboardGetText() -> std::string {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
  char* out = SDL_GetClipboardText();
  if (out == nullptr) {
    throw Exception("Error fetching clipboard contents.", PyExcType::kRuntime);
  }
  std::string out_s{out};
  SDL_free(out);
  return out_s;
}

auto AppAdapterSDL::GetKeyName(int keycode) -> std::string {
  return SDL_GetKeyName(static_cast<SDL_Keycode>(keycode));
}

}  // namespace ballistica::base

#endif  // BA_SDL_BUILD
