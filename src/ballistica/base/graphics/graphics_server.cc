// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/graphics_server.h"

#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"

// FIXME: clear out this conditional stuff.
#if BA_SDL_BUILD
#include "ballistica/base/app_adapter/app_adapter_sdl.h"
#else
#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/mesh/mesh_data.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/core/platform/core_platform.h"
#endif

namespace ballistica::base {

#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && !BA_XCODE_NEW_PROJECT
void GraphicsServer::FullscreenCheck() {
  if (!fullscreen_enabled()) {
#if BA_ENABLE_OPENGL
    SDL_WM_ToggleFullScreen(gl_context_->sdl_screen_surface());
#endif
  }
}
#endif

GraphicsServer::GraphicsServer() : event_loop_(g_core->main_event_loop()) {}

GraphicsServer::~GraphicsServer() { assert(g_base->graphics); }

void GraphicsServer::SetRenderHold() {
  assert(g_base->InGraphicsThread());
  render_hold_++;
}

void GraphicsServer::OnMainThreadStartApp() {
  // For janky old non-event-push mode, just fall back on a timer for rendering.
  if (!g_core->platform->IsEventPushMode()) {
    render_timer_ = this->event_loop()->NewTimer(
        1000 / 60, true, NewLambdaRunnable([this] { TryRender(); }));
  }
}

void GraphicsServer::SetFrameDef(FrameDef* framedef) {
  // Note: we're just setting the framedef directly here
  // even though this gets called from the logic thread.
  // Ideally it would seem we should push these to our thread
  // event list, but currently we spin-lock waiting for new
  // frames to appear which would prevent that from working;
  // we would need to change that code.
  {
    std::scoped_lock llock(frame_def_mutex_);
    assert(frame_def_ == nullptr);
    frame_def_ = framedef;
  }
}

auto GraphicsServer::GetRenderFrameDef() -> FrameDef* {
  assert(g_base->InGraphicsThread());
  millisecs_t app_time = g_core->GetAppTimeMillisecs();

  if (!renderer_) {
    return nullptr;
  }

  // If the app says it's minimized, don't do anything.
  // (on iOS we'll get shut down if we make GL calls in this state, etc)
  if (g_base->app_adapter->app_paused()) {
    return nullptr;
  }

  // Do some incremental loading every time we try to render.
  g_base->assets->RunPendingGraphicsLoads();

  // Spin and wait for a short bit for a frame_def to appear. If it does, we
  // grab it, render it, and also message the logic thread to start generating
  // another one.
  while (true) {
    FrameDef* frame_def{};
    {
      std::scoped_lock llock(frame_def_mutex_);
      if (frame_def_) {
        frame_def = frame_def_;
        frame_def_ = nullptr;
      }
    }
    if (frame_def) {
      // As soon as we start working on rendering a frame, ask the logic
      // thread to start working on the next one for us. Keeps things nice and
      // pipelined.
      g_base->logic->event_loop()->PushCall([] { g_base->logic->Draw(); });
      return frame_def;
    }

    // If there's no frame_def for us, sleep for a bit and wait for it.
    // But if we've been waiting for too long, give up.
    // On some platforms such as Android, this frame will still get flipped
    // whether we draw in it or not, so we *really* want to not skip drawing
    // if we can help it.
    millisecs_t t = g_core->GetAppTimeMillisecs() - app_time;
    if (t >= 1000) {
      if (g_buildconfig.debug_build()) {
        Log(LogLevel::kWarning,
            "GraphicsServer: aborting GetRenderFrameDef after "
                + std::to_string(t) + "ms.");
      }
      break;  // Fail.
    }
    core::CorePlatform::SleepMillisecs(1);
  }
  return nullptr;
}

void GraphicsServer::ApplyFrameDefSettings(FrameDef* frame_def) {
  assert(g_base->InGraphicsThread());
  tv_border_ = frame_def->tv_border();
}

// Runs any mesh updates contained in the frame-def.
void GraphicsServer::RunFrameDefMeshUpdates(FrameDef* frame_def) {
  assert(g_base->InGraphicsThread());

  // Run any mesh-data creates/destroys included with this frame_def.
  for (auto&& i : frame_def->mesh_data_creates()) {
    assert(i != nullptr);
    i->iterator_ = mesh_datas_.insert(mesh_datas_.end(), i);
    i->Load(renderer_);
  }
  for (auto&& i : frame_def->mesh_data_destroys()) {
    assert(i != nullptr);
    i->Unload(renderer_);
    mesh_datas_.erase(i->iterator_);
  }
}

// Renders shadow passes and other common parts of a frame_def.
void GraphicsServer::PreprocessRenderFrameDef(FrameDef* frame_def) {
  assert(g_base->InGraphicsThread());

  // Now let the renderer do any preprocess passes (shadows, etc).
  assert(renderer_);
  if (renderer_ != nullptr) {
    renderer_->PreprocessFrameDef(frame_def);
  }
}

// Does the default drawing to the screen, either from the left or right stereo
// eye or in mono.
void GraphicsServer::DrawRenderFrameDef(FrameDef* frame_def, int eye) {
  assert(renderer_);
  if (renderer_) {
    renderer_->RenderFrameDef(frame_def);
  }
}

// Clean up the frame_def once done drawing it.
void GraphicsServer::FinishRenderFrameDef(FrameDef* frame_def) {
  assert(renderer_);
  if (renderer_) {
    renderer_->FinishFrameDef(frame_def);

    // Let the app know a frame render is complete (it may need to do a
    // swap/etc).
    g_base->app_adapter->DidFinishRenderingFrame(frame_def);
  }
}

void GraphicsServer::TryRender() {
  assert(g_base->InGraphicsThread());

  if (FrameDef* frame_def = GetRenderFrameDef()) {
    // Apply settings such as tv-mode passed along on the frame-def.
    ApplyFrameDefSettings(frame_def);

    // Note: we always run mesh updates contained in the framedef
    // even if we don't actually render it.
    // (Hmm this seems flaky; will TryRender always get called
    // for each FrameDef?... perhaps we should separate mesh updates
    // from FrameDefs? Or change our logic so that frame-defs *always* get
    // rendered.
    RunFrameDefMeshUpdates(frame_def);

    // Only actually render if we have a screen and aren't in a hold.
    auto target = renderer()->screen_render_target();
    if (target != nullptr && render_hold_ == 0) {
      PreprocessRenderFrameDef(frame_def);
      DrawRenderFrameDef(frame_def);
      FinishRenderFrameDef(frame_def);
    }

    // Send this frame_def back to the logic thread for deletion or recycling.
    g_base->graphics->ReturnCompletedFrameDef(frame_def);
  }
}

// Reload all media (for debugging/benchmarking purposes).
void GraphicsServer::ReloadMedia() {
  assert(g_base->InGraphicsThread());

  // Immediately unload all renderer data here in this thread.
  if (renderer_) {
    g_base->assets->UnloadRendererBits(true, true);
  }

  // Set a render-hold so we ignore all frame_defs up until the point at which
  // we receive the corresponding remove-hold.
  // (At which point subsequent frame-defs will be be progress-bar frame_defs so
  // we won't hitch if we actually render them.)
  assert(g_base->graphics_server);
  SetRenderHold();

  // Now tell the logic thread to kick off loads for everything, flip on
  // progress bar drawing, and then tell the graphics thread to stop ignoring
  // frame-defs.
  g_base->logic->event_loop()->PushCall([this] {
    g_base->assets->MarkAllAssetsForLoad();
    g_base->graphics->EnableProgressBar(false);
    PushRemoveRenderHoldCall();
  });
}

// Call when renderer context has been lost.
void GraphicsServer::RebuildLostContext() {
  assert(g_base->InGraphicsThread());

  if (!renderer_) {
    Log(LogLevel::kError, "No renderer on GraphicsServer::_rebuildContext.");
    return;
  }

  // Mark our context as lost so the renderer knows to not try and tear things
  // down itself.
  set_renderer_context_lost(true);

  // Unload all texture and mesh data here in the render thread.
  g_base->assets->UnloadRendererBits(true, true);

  // Also unload dynamic meshes.
  for (auto&& i : mesh_datas_) {
    i->Unload(renderer_);
  }

  // And other internal renderer stuff.
  renderer_->Unload();

  set_renderer_context_lost(false);

  // Now reload.
  renderer_->Load();

  // Also (re)load all dynamic meshes.
  for (auto&& i : mesh_datas_) {
    i->Load(renderer_);
  }

  renderer_->ScreenSizeChanged();

  // Set a render-hold so we ignore all frame_defs up until the point at which
  // we receive the corresponding remove-hold.
  // (At which point subsequent frame-defs will be be progress-bar frame_defs so
  // we won't hitch if we actually render them.)
  SetRenderHold();

  // Now tell the logic thread to kick off loads for everything, flip on
  // progress bar drawing, and then tell the graphics thread to stop ignoring
  // frame-defs.
  g_base->logic->event_loop()->PushCall([this] {
    g_base->assets->MarkAllAssetsForLoad();
    g_base->graphics->EnableProgressBar(false);
    PushRemoveRenderHoldCall();
  });
}

void GraphicsServer::SetScreen(
    bool fullscreen, int width, int height,
    TextureQualityRequest texture_quality_requested,
    GraphicsQualityRequest graphics_quality_requested,
    const std::string& android_res) {
  assert(g_base->InGraphicsThread());

  // If we know what we support, filter request types to those we support.
  // (will keep us from rebuilding contexts if request type is flipping between
  // different types we don't support).
  if (g_base->graphics->has_supports_high_quality_graphics_value()) {
    if (!g_base->graphics->supports_high_quality_graphics()
        && graphics_quality_requested > GraphicsQualityRequest::kMedium) {
      graphics_quality_requested = GraphicsQualityRequest::kMedium;
    }
  }

#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && BA_SDL_BUILD
  bool create_fullscreen_check_timer = false;
#endif

  bool do_toggle_fs = false;
  bool do_set_existing_fs = false;

  if (g_core->HeadlessMode()) {
    // We don't actually make or update a renderer in headless, but we
    // still need to set our list of supported textures types/etc. to avoid
    // complaints.
    std::list<TextureCompressionType> c_types;
    SetTextureCompressionTypes(c_types);
    graphics_quality_requested_ = GraphicsQualityRequest::kLow;
    graphics_quality_ = GraphicsQuality::kLow;
    graphics_quality_set_ = true;
    texture_quality_requested_ = TextureQualityRequest::kLow;
    texture_quality_ = TextureQuality::kLow;
    texture_quality_set_ = true;
  } else {
    // OK - starting in SDL2 we never pass in specific resolution requests.
    // we request fullscreen-windows for full-screen situations and that's it.
    // (otherwise we may wind up with huge windows due to passing in desktop
    // resolutions and retina wonkiness)
    width = static_cast<int>(kBaseVirtualResX * 0.8f);
    height = static_cast<int>(kBaseVirtualResY * 0.8f);

    // We should never have to recreate the context after the initial time on
    // our modern builds.
    bool need_full_context_rebuild = (!renderer_);
    bool need_renderer_reload;

    // We need a full renderer reload if quality values have changed.
    need_renderer_reload =
        ((texture_quality_requested_ != texture_quality_requested)
         || (graphics_quality_requested_ != graphics_quality_requested)
         || !texture_quality_set() || !graphics_quality_set());

    // This stuff requires a full context rebuild.
    if (need_full_context_rebuild || need_renderer_reload) {
      HandleFullContextScreenRebuild(need_full_context_rebuild, fullscreen,
                                     width, height, graphics_quality_requested,
                                     texture_quality_requested);
      // On mac, we let window save/restore handle our fullscreen restoring for
      // us. However if document restore is turned off we'll start windowed on
      // every launch.  So if we're trying to make a fullscreen setup, lets
      // check after a short delay to make sure we have it, and run a
      // full-screen-toggle ourself if not.
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && BA_SDL_BUILD
      if (fullscreen) {
        create_fullscreen_check_timer = true;
      }
#endif  // BA_OSTYPE_MACOS

    } else {
      // on SDL2 builds we can just set fullscreen on the existing window; no
      // need for a context rebuild
#if BA_SDL2_BUILD
      do_set_existing_fs = true;
#else
      // On our old custom SDL1.2 mac build, fullscreen toggling winds up here.
      // this doesn't require a context rebuild either.
      if (fullscreen != fullscreen_enabled()) {
        do_toggle_fs = true;
      }
#endif  // BA_SDL2_BUILD
    }

    HandlePushAndroidRes(android_res);

#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && BA_SDL_BUILD
    if (create_fullscreen_check_timer) {
      event_loop()->NewTimer(1000, false,
                             NewLambdaRunnable([this] { FullscreenCheck(); }));
    }
#endif  // BA_OSTYPE_MACOS

    HandleFullscreenToggling(do_set_existing_fs, do_toggle_fs, fullscreen);
  }

  // The first time we complete setting up our screen, we send a message
  // back to the logic thread to complete the init process. (they can't start
  // loading graphics and things until we have our context set up so we know
  // what types of textures to load, etc)
  if (!initial_screen_created_) {
    initial_screen_created_ = true;
    g_base->logic->event_loop()->PushCall(
        [] { g_base->logic->OnInitialScreenCreated(); });
  }
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantParameter"

void GraphicsServer::HandleFullContextScreenRebuild(
    bool need_full_context_rebuild, bool fullscreen, int width, int height,
    GraphicsQualityRequest graphics_quality_requested,
    TextureQualityRequest texture_quality_requested) {
  // Unload renderer-specific data (display-lists, internal textures, etc)
  if (renderer_) {
    // Unload all textures and meshes. These will be reloaded as-needed
    // automatically for the new context.
    g_base->assets->UnloadRendererBits(true, true);

    // Also unload all dynamic meshes.
    for (auto&& i : mesh_datas_) {
      i->Unload(renderer_);
    }

    // And all internal renderer stuff.
    renderer_->Unload();
  }

  // Handle screen/context recreation.
  if (need_full_context_rebuild) {
    // On mac we store the values we *want* separate from those we get.. (so
    // we know when our request has changed; not our result).
#if !(BA_OSTYPE_MACOS && BA_XCODE_BUILD)
    fullscreen_enabled_ = fullscreen;
#endif

    target_res_x_ = static_cast<float>(width);
    target_res_y_ = static_cast<float>(height);

#if BA_ENABLE_OPENGL
    gl_context_ = std::make_unique<GLContext>(width, height, fullscreen);
    res_x_ = static_cast<float>(gl_context_->res_x());
    res_y_ = static_cast<float>(gl_context_->res_y());
#endif

    UpdateVirtualScreenRes();

    // Inform graphics client and logic thread subsystems of the change.
    g_base->logic->event_loop()->PushCall(
        [vx = res_x_virtual_, vy = res_y_virtual_, x = res_x_, y = res_y_] {
          g_base->graphics->SetScreenSize(vx, vy, x, y);
          g_base->logic->OnScreenSizeChange(vx, vy, x, y);
        });
  }

  if (!renderer_) {
#if BA_ENABLE_OPENGL
    renderer_ = new RendererGL();
#endif
  }

  // Make sure we've done this first so we can properly set auto values and
  // whatnot.
  renderer_->CheckCapabilities();

  // Update graphics quality based on request.
  graphics_quality_requested_ = graphics_quality_requested;
  switch (graphics_quality_requested_) {
    case GraphicsQualityRequest::kLow:
      graphics_quality_ = GraphicsQuality::kLow;
      break;
    case GraphicsQualityRequest::kMedium:
      graphics_quality_ = GraphicsQuality::kMedium;
      break;
    case GraphicsQualityRequest::kHigh:
      graphics_quality_ = GraphicsQuality::kHigh;
      break;
    case GraphicsQualityRequest::kHigher:
      graphics_quality_ = GraphicsQuality::kHigher;
      break;
    case GraphicsQualityRequest::kAuto:
      graphics_quality_ = renderer_->GetAutoGraphicsQuality();
      break;
    default:
      Log(LogLevel::kError,
          "Unhandled GraphicsQualityRequest value: "
              + std::to_string(static_cast<int>(graphics_quality_requested_)));
      graphics_quality_ = GraphicsQuality::kLow;
  }

  // If we don't support high quality graphics, make sure we're no higher than
  // medium.
  BA_PRECONDITION(g_base->graphics->has_supports_high_quality_graphics_value());
  if (!g_base->graphics->supports_high_quality_graphics()
      && graphics_quality_ > GraphicsQuality::kMedium) {
    graphics_quality_ = GraphicsQuality::kMedium;
  }
  graphics_quality_set_ = true;

  // Update texture quality based on request.
  texture_quality_requested_ = texture_quality_requested;
  switch (texture_quality_requested_) {
    case TextureQualityRequest::kLow:
      texture_quality_ = TextureQuality::kLow;
      break;
    case TextureQualityRequest::kMedium:
      texture_quality_ = TextureQuality::kMedium;
      break;
    case TextureQualityRequest::kHigh:
      texture_quality_ = TextureQuality::kHigh;
      break;
    case TextureQualityRequest::kAuto:
      texture_quality_ = renderer_->GetAutoTextureQuality();
      break;
    default:
      Log(LogLevel::kError,
          "Unhandled TextureQualityRequest value: "
              + std::to_string(static_cast<int>(texture_quality_requested_)));
      texture_quality_ = TextureQuality::kLow;
  }
  texture_quality_set_ = true;

  // Ok we've got our qualities figured out; now load/update the renderer.
  renderer_->Load();

  // Also (re)load all existing dynamic meshes.
  for (auto&& i : mesh_datas_) {
    i->Load(renderer_);
  }
  renderer_->ScreenSizeChanged();
  renderer_->PostLoad();

  // Set a render-hold so we ignore all frame_defs up until the point at which
  // we receive the corresponding remove-hold.
  // (At which point subsequent frame-defs will be be progress-bar frame_defs
  // so we won't hitch if we actually render them.)
  SetRenderHold();

  // Now tell the logic thread to kick off loads for everything, flip on
  // progress bar drawing, and then tell the graphics thread to stop ignoring
  // frame-defs.
  g_base->logic->event_loop()->PushCall([this] {
    g_base->assets->MarkAllAssetsForLoad();
    g_base->graphics->set_internal_components_inited(false);
    g_base->graphics->EnableProgressBar(false);
    PushRemoveRenderHoldCall();
  });
}

#pragma clang diagnostic pop

// Given physical res, calculate virtual res.
void GraphicsServer::CalcVirtualRes(float* x, float* y) {
  float x_in = (*x);
  float y_in = (*y);
  if ((*x) / (*y) > static_cast<float>(kBaseVirtualResX)
                        / static_cast<float>(kBaseVirtualResY)) {
    (*y) = kBaseVirtualResY;
    (*x) = (*y) * (x_in / y_in);
  } else {
    *x = kBaseVirtualResX;
    *y = (*x) * (y_in / x_in);
  }
}

void GraphicsServer::UpdateVirtualScreenRes() {
  assert(g_base->InGraphicsThread());
  // In vr mode our virtual res is independent of our screen size.
  // (since it gets drawn to an overlay)
  if (g_core->IsVRMode()) {
    res_x_virtual_ = kBaseVirtualResX;
    res_y_virtual_ = kBaseVirtualResY;
  } else {
    res_x_virtual_ = res_x_;
    res_y_virtual_ = res_y_;
    CalcVirtualRes(&res_x_virtual_, &res_y_virtual_);
  }
}

void GraphicsServer::SetScreenResolution(float h, float v) {
  assert(g_base->InGraphicsThread());

  if (target_res_x_ == h && target_res_y_ == v) {
    return;
  }

  target_res_x_ = h;
  target_res_y_ = v;
  res_x_ = h;
  res_y_ = v;
  UpdateVirtualScreenRes();

  // Inform renderer of the change.
  if (renderer_) {
    renderer_->ScreenSizeChanged();
  }

  // Inform graphics client and logic thread subsystems of the change.
  g_base->logic->event_loop()->PushCall(
      [vx = res_x_virtual_, vy = res_y_virtual_, x = res_x_, y = res_y_] {
        g_base->graphics->SetScreenSize(vx, vy, x, y);
        g_base->logic->OnScreenSizeChange(vx, vy, x, y);
      });
}

// FIXME: Shouldn't have android-specific code in here.
void GraphicsServer::HandlePushAndroidRes(const std::string& android_res) {
  if (g_buildconfig.ostype_android()) {
    assert(renderer_);
    if (renderer_ == nullptr) {
      return;
    }
    // We push android res to the java layer here.  We don't actually worry
    // about screen-size-changed callbacks and whatnot, since those will happen
    // automatically once things actually change. We just want to be sure that
    // we have a renderer so we can calc what our auto res should be.
    assert(renderer_);
    std::string fin_res;
    if (android_res == "Auto") {
      fin_res = renderer_->GetAutoAndroidRes();
    } else {
      fin_res = android_res;
    }
    g_core->platform->AndroidSetResString(fin_res);
  }
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantParameter"

void GraphicsServer::HandleFullscreenToggling(bool do_set_existing_fs,
                                              bool do_toggle_fs,
                                              bool fullscreen) {
  if (do_set_existing_fs) {
#if BA_SDL2_BUILD
    bool rift_vr_mode = false;
#if BA_RIFT_BUILD
    if (g_core->IsVRMode()) {
      rift_vr_mode = true;
    }
#endif  // BA_RIFT_BUILD
    if (explicit_bool(!rift_vr_mode)) {
#if BA_OSTYPE_IOS_TVOS
      set_fullscreen_enabled(true);

#else   // BA_OSTYPE_IOS_TVOS
      uint32_t fullscreen_flag = SDL_WINDOW_FULLSCREEN_DESKTOP;
      SDL_SetWindowFullscreen(gl_context_->sdl_window(),
                              fullscreen ? fullscreen_flag : 0);

      // Ideally this should be driven by OS events and not just explicitly by
      // us (so, for instance, if someone presses fullscreen on mac we'd know
      // we've gone into fullscreen).  But this works for now.
      set_fullscreen_enabled(fullscreen);
#endif  // BA_OSTYPE_IOS_TVOS
    }
#endif  // BA_SDL2_BUILD
  } else if (do_toggle_fs) {
    // If we're doing a fullscreen-toggle, we need to do it after coming out of
    // sync mode (because the toggle triggers sync-mode itself).
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && !BA_XCODE_NEW_PROJECT
#if BA_ENABLE_OPENGL
    SDL_WM_ToggleFullScreen(gl_context_->sdl_screen_surface());
#endif
#endif  // macos && xcode_build
  }
}
#pragma clang diagnostic pop

void GraphicsServer::SetTextureCompressionTypes(
    const std::list<TextureCompressionType>& types) {
  texture_compression_types_ = 0;  // Reset.
  for (auto&& i : types) {
    texture_compression_types_ |= (0x01u << (static_cast<uint32_t>(i)));
  }
  texture_compression_types_set_ = true;
}

void GraphicsServer::SetOrthoProjection(float left, float right, float bottom,
                                        float top, float nearval,
                                        float farval) {
  float tx = -((right + left) / (right - left));
  float ty = -((top + bottom) / (top - bottom));
  float tz = -((farval + nearval) / (farval - nearval));

  projection_matrix_.m[0] = 2.0f / (right - left);
  projection_matrix_.m[4] = 0.0f;
  projection_matrix_.m[8] = 0.0f;
  projection_matrix_.m[12] = tx;

  projection_matrix_.m[1] = 0.0f;
  projection_matrix_.m[5] = 2.0f / (top - bottom);
  projection_matrix_.m[9] = 0.0f;
  projection_matrix_.m[13] = ty;

  projection_matrix_.m[2] = 0.0f;
  projection_matrix_.m[6] = 0.0f;
  projection_matrix_.m[10] = -2.0f / (farval - nearval);
  projection_matrix_.m[14] = tz;

  projection_matrix_.m[3] = 0.0f;
  projection_matrix_.m[7] = 0.0f;
  projection_matrix_.m[11] = 0.0f;
  projection_matrix_.m[15] = 1.0f;

  model_view_projection_matrix_dirty_ = true;
  projection_matrix_state_++;
}

void GraphicsServer::SetCamera(const Vector3f& eye, const Vector3f& target,
                               const Vector3f& up_vector) {
  assert(g_base->InGraphicsThread());

  // Reset the modelview stack.
  model_view_stack_.clear();

  auto forward = (target - eye).Normalized();
  auto side = Vector3f::Cross(forward, up_vector).Normalized();
  Vector3f up = Vector3f::Cross(side, forward);

  //------------------
  model_view_matrix_.m[0] = side.x;
  model_view_matrix_.m[4] = side.y;
  model_view_matrix_.m[8] = side.z;
  model_view_matrix_.m[12] = 0.0f;
  //------------------
  model_view_matrix_.m[1] = up.x;
  model_view_matrix_.m[5] = up.y;
  model_view_matrix_.m[9] = up.z;
  model_view_matrix_.m[13] = 0.0f;
  //------------------
  model_view_matrix_.m[2] = -forward.x;
  model_view_matrix_.m[6] = -forward.y;
  model_view_matrix_.m[10] = -forward.z;
  model_view_matrix_.m[14] = 0.0f;
  //------------------
  model_view_matrix_.m[3] = model_view_matrix_.m[7] = model_view_matrix_.m[11] =
      0.0f;
  model_view_matrix_.m[15] = 1.0f;
  //------------------
  model_view_matrix_ =
      Matrix44fTranslate(-eye.x, -eye.y, -eye.z) * model_view_matrix_;
  view_world_matrix_ = model_view_matrix_.Inverse();

  model_view_projection_matrix_dirty_ = true;
  model_world_matrix_dirty_ = true;

  cam_pos_ = eye;
  cam_target_ = target;
  cam_pos_state_++;
  cam_orient_matrix_dirty_ = true;
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"

void GraphicsServer::UpdateCamOrientMatrix() {
  assert(g_base->InGraphicsThread());
  if (cam_orient_matrix_dirty_) {
    cam_orient_matrix_ = kMatrix44fIdentity;
    Vector3f to_cam = cam_pos_ - cam_target_;
    to_cam.Normalize();
    Vector3f world_up(0, 1, 0);
    Vector3f side = Vector3f::Cross(world_up, to_cam);
    side.Normalize();
    Vector3f up = Vector3f::Cross(side, to_cam);
    cam_orient_matrix_.m[0] = side.x;
    cam_orient_matrix_.m[1] = side.y;
    cam_orient_matrix_.m[2] = side.z;
    cam_orient_matrix_.m[4] = to_cam.x;
    cam_orient_matrix_.m[5] = to_cam.y;
    cam_orient_matrix_.m[6] = to_cam.z;
    cam_orient_matrix_.m[8] = up.x;
    cam_orient_matrix_.m[9] = up.y;
    cam_orient_matrix_.m[10] = up.z;
    cam_orient_matrix_.m[3] = cam_orient_matrix_.m[7] =
        cam_orient_matrix_.m[11] = cam_orient_matrix_.m[12] =
            cam_orient_matrix_.m[13] = cam_orient_matrix_.m[14] = 0.0f;
    cam_orient_matrix_.m[15] = 1.0f;
    cam_orient_matrix_state_++;
  }
}

#pragma clang diagnostic pop

#pragma mark PushCalls

void GraphicsServer::PushSetScreenCall(
    bool fullscreen, int width, int height,
    TextureQualityRequest texture_quality_request,
    GraphicsQualityRequest graphics_quality_request,
    const std::string& android_res) {
  event_loop()->PushCall([=] {
    SetScreen(fullscreen, width, height, texture_quality_request,
              graphics_quality_request, android_res);
  });
}

void GraphicsServer::PushReloadMediaCall() {
  event_loop()->PushCall([this] { ReloadMedia(); });
}

void GraphicsServer::PushSetScreenGammaCall(float gamma) {
  event_loop()->PushCall([this, gamma] {
    assert(g_base->InGraphicsThread());
    if (!renderer_) {
      return;
    }
    renderer_->set_screen_gamma(gamma);
  });
}

void GraphicsServer::PushSetScreenPixelScaleCall(float pixel_scale) {
  event_loop()->PushCall([this, pixel_scale] {
    assert(g_base->InGraphicsThread());
    if (!renderer_) {
      return;
    }
    renderer_->set_pixel_scale(pixel_scale);
  });
}

void GraphicsServer::PushSetVSyncCall(bool sync, bool auto_sync) {
  event_loop()->PushCall([this, sync, auto_sync] {
    assert(g_base->InGraphicsThread());

#if BA_SDL_BUILD

    // Currently only supported for AppAdapterSDL.
    // May want to revisit this later.
    if (g_buildconfig.sdl_build()) {
      // Even if we were built with SDL, we may not be running in sdl-app-mode
      // (for instance, Rift in VR mode). Only do this if we're an sdl app.
      if (auto app = dynamic_cast<AppAdapterSDL*>(g_base->app_adapter)) {
        v_sync_ = sync;
        auto_vsync_ = auto_sync;
        if (gl_context_) {
          app->SetAutoVSync(auto_vsync_);
          // Set it directly if not auto...
          if (!auto_vsync_) {
            gl_context_->SetVSync(v_sync_);
          }
        } else {
          Log(LogLevel::kError, "Got SetVSyncCall with no gl context_ref.");
        }
      }
    }
#endif  // BA_HEADLESS_BUILD
  });
}

void GraphicsServer::PushComponentUnloadCall(
    const std::vector<Object::Ref<Asset>*>& components) {
  event_loop()->PushCall([components] {
    // Unload the components.
    for (auto&& i : components) {
      (**i).Unload();
    }
    // Then kick them over to the logic thread for deletion.
    g_base->logic->event_loop()->PushCall([components] {
      for (auto&& i : components) {
        delete i;
      }
    });
  });
}

void GraphicsServer::PushRemoveRenderHoldCall() {
  event_loop()->PushCall([this] {
    assert(render_hold_);
    render_hold_--;
    if (render_hold_ < 0) {
      Log(LogLevel::kError, "RenderHold < 0");
      render_hold_ = 0;
    }
  });
}

}  // namespace ballistica::base
