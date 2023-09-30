// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/graphics_server.h"

// Kill this.
#include "ballistica/base/graphics/gl/renderer_gl.h"

// FIXME: clear out this conditional stuff.
#if BA_SDL_BUILD
#include "ballistica/base/app_adapter/app_adapter_sdl.h"
#else
#include "ballistica/base/app_adapter/app_adapter.h"
#endif

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/mesh/mesh_data.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

GraphicsServer::GraphicsServer() = default;
GraphicsServer::~GraphicsServer() = default;

void GraphicsServer::SetRenderHold() {
  assert(g_base->app_adapter->InGraphicsContext());
  render_hold_++;
}

void GraphicsServer::OnMainThreadStartApp() {}

void GraphicsServer::EnqueueFrameDef(FrameDef* framedef) {
  // Note: we're just setting the framedef directly here even though this
  // gets called from the logic thread. Ideally it would seem we should push
  // these to our thread event list, but currently we may spin-lock waiting
  // for new frames to appear which would prevent that from working; we
  // would need to change that code.
  {
    std::scoped_lock frame_def_lock(frame_def_mutex_);
    assert(frame_def_ == nullptr);
    frame_def_ = framedef;
  }
}

auto GraphicsServer::TryRender() -> bool {
  assert(g_base->app_adapter->InGraphicsContext());

  bool success{};

  if (FrameDef* frame_def = WaitForRenderFrameDef_()) {
    // Apply settings such as tv-mode that were passed along via the
    // frame-def.
    ApplyFrameDefSettings(frame_def);

    // Note: we run mesh-updates on each frame-def that comes through even
    // if we don't actually render the frame.
    RunFrameDefMeshUpdates(frame_def);

    // Only actually render if we have a screen and aren't in a hold.
    auto target = renderer()->screen_render_target();
    if (target != nullptr && render_hold_ == 0) {
      PreprocessRenderFrameDef(frame_def);
      DrawRenderFrameDef(frame_def);
      FinishRenderFrameDef(frame_def);
      success = true;
    }

    // Send this frame_def back to the logic thread for deletion or recycling.
    g_base->graphics->ReturnCompletedFrameDef(frame_def);
  }
  return success;
}

auto GraphicsServer::WaitForRenderFrameDef_() -> FrameDef* {
  assert(g_base->app_adapter->InGraphicsContext());
  millisecs_t app_time = g_core->GetAppTimeMillisecs();

  if (!renderer_) {
    return nullptr;
  }

  // If the app is paused, never render.
  if (g_base->app_adapter->app_paused()) {
    return nullptr;
  }

  // Do some incremental loading every time we try to render.
  g_base->assets->RunPendingGraphicsLoads();

  // Spin and wait for a short bit for a frame_def to appear.
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
      // thread to start working on the next one for us. Keeps things nice
      // and pipelined.
      g_base->logic->event_loop()->PushCall([] { g_base->logic->Draw(); });
      return frame_def;
    }

    // If there's no frame_def for us, sleep for a bit and wait for it. But
    // if we've been waiting for too long, give up. On some platforms such
    // as Android, this frame will still get flipped whether we draw in it
    // or not, so we *really* want to not skip drawing if we can help it.
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
  assert(g_base->app_adapter->InGraphicsContext());
  tv_border_ = frame_def->tv_border();
}

// Runs any mesh updates contained in the frame-def.
void GraphicsServer::RunFrameDefMeshUpdates(FrameDef* frame_def) {
  assert(g_base->app_adapter->InGraphicsContext());

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
  assert(g_base->app_adapter->InGraphicsContext());

  // Now let the renderer do any preprocess passes (shadows, etc).
  assert(renderer_);
  if (renderer_ != nullptr) {
    renderer_->PreprocessFrameDef(frame_def);
  }
}

// Does the default drawing to the screen, either from the left or right
// stereo eye or in mono.
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
  }
}

// Reload all media (for debugging/benchmarking purposes).
void GraphicsServer::ReloadMedia_() {
  assert(g_base->app_adapter->InGraphicsContext());

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
  // progress bar drawing, and then tell the graphics thread to stop
  // ignoring frame-defs.
  g_base->logic->event_loop()->PushCall([this] {
    g_base->assets->MarkAllAssetsForLoad();
    g_base->graphics->EnableProgressBar(false);
    PushRemoveRenderHoldCall();
  });
}

// Call when a renderer context has been lost.
void GraphicsServer::ReloadLostRenderer() {
  assert(g_base->app_adapter->InGraphicsContext());

  if (!renderer_) {
    Log(LogLevel::kError, "No renderer on GraphicsServer::ReloadLostRenderer.");
    return;
  }

  // Mark our context as lost so the renderer knows to not try and tear things
  // down itself.
  set_renderer_context_lost(true);

  // Unload all texture and mesh data here in the graphics thread.
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

  renderer_->OnScreenSizeChange();

  // Set a render-hold so we ignore all frame_defs up until the point at
  // which we receive the corresponding remove-hold. (At which point
  // subsequent frame-defs will be be progress-bar frame_defs so we won't
  // hitch if we actually render them.)
  SetRenderHold();

  // Now tell the logic thread to kick off loads for everything, flip on
  // progress bar drawing, and then tell the graphics thread to stop
  // ignoring frame-defs.
  g_base->logic->event_loop()->PushCall([this] {
    g_base->assets->MarkAllAssetsForLoad();
    g_base->graphics->EnableProgressBar(false);
    PushRemoveRenderHoldCall();
  });
}

void GraphicsServer::SetNullGraphics() {
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

  // Let the logic thread know screen creation is done (or lack thereof).
  g_base->logic->event_loop()->PushCall(
      [] { g_base->logic->OnGraphicsReady(); });
}

void GraphicsServer::set_renderer(Renderer* renderer) {
  assert(g_base->app_adapter->InGraphicsContext());
  assert(!renderer_loaded_);
  assert(!renderer_);
  renderer_ = renderer;
}

void GraphicsServer::LoadRenderer() {
  assert(g_base->app_adapter->InGraphicsContext());
  if (!renderer_) {
    Log(LogLevel::kError, "LoadRenderer() called with no renderer present.");
    return;
  }
  if (renderer_loaded_) {
    Log(LogLevel::kError,
        "LoadRenderer() called with an already-loaded renderer present.");
    return;
  }

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
  renderer_->OnScreenSizeChange();
  renderer_->PostLoad();

  renderer_loaded_ = true;

  // Set an immediate render-hold so we ignore all frame_defs up until the
  // point at which we receive the corresponding remove-hold. (At which
  // point subsequent frame-defs will be be progress-bar frame_defs so we
  // won't hitch if we actually render them.)
  SetRenderHold();

  // Now tell the logic thread to kick off loads for everything, flip on
  // progress bar drawing, and then ship a remove-hold call back to us.
  g_base->logic->event_loop()->PushCall([this] {
    g_base->assets->MarkAllAssetsForLoad();
    g_base->graphics->set_internal_components_inited(false);
    g_base->graphics->EnableProgressBar(false);
    PushRemoveRenderHoldCall();
  });
}

void GraphicsServer::UnloadRenderer() {
  assert(g_base->app_adapter->InGraphicsContext());
  if (!renderer_) {
    Log(LogLevel::kError, "UnloadRenderer() called with no renderer present.");
    return;
  }
  if (!renderer_loaded_) {
    Log(LogLevel::kError,
        "UnloadRenderer() called with an already unloaded renderer present.");
    return;
  }

  // Unload all textures and meshes. These will be reloaded on-demand for
  // the new context.
  g_base->assets->UnloadRendererBits(true, true);

  // Also unload all dynamic meshes.
  for (auto&& i : mesh_datas_) {
    i->Unload(renderer_);
  }

  // And all internal renderer stuff.
  renderer_->Unload();

  renderer_loaded_ = false;
}

// Given physical res, calculate virtual res.
void GraphicsServer::CalcVirtualRes_(float* x, float* y) {
  float x_in = *x;
  float y_in = *y;
  if (*x / *y > static_cast<float>(kBaseVirtualResX)
                    / static_cast<float>(kBaseVirtualResY)) {
    *y = kBaseVirtualResY;
    *x = *y * (x_in / y_in);
  } else {
    *x = kBaseVirtualResX;
    *y = *x * (y_in / x_in);
  }
}

void GraphicsServer::UpdateVirtualScreenRes_() {
  assert(g_base->app_adapter->InGraphicsContext());

  // In vr mode our virtual res is independent of our screen size.
  // (since it gets drawn to an overlay)
  if (g_core->IsVRMode()) {
    res_x_virtual_ = kBaseVirtualResX;
    res_y_virtual_ = kBaseVirtualResY;
  } else {
    res_x_virtual_ = res_x_;
    res_y_virtual_ = res_y_;
    CalcVirtualRes_(&res_x_virtual_, &res_y_virtual_);
  }
}

void GraphicsServer::SetScreenResolution(float h, float v) {
  assert(g_base->app_adapter->InGraphicsContext());

  // Ignore redundant sets.
  if (res_x_ == h && res_y_ == v) {
    return;
  }
  res_x_ = h;
  res_y_ = v;
  UpdateVirtualScreenRes_();

  // Inform renderer of the change.
  if (renderer_) {
    renderer_->OnScreenSizeChange();
  }

  // Inform all logic thread bits of this change.
  g_base->logic->event_loop()->PushCall(
      [vx = res_x_virtual_, vy = res_y_virtual_, x = res_x_, y = res_y_] {
        g_base->graphics->SetScreenSize(vx, vy, x, y);
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
    // about screen-size-changed callbacks and whatnot, since those will
    // happen automatically once things actually change. We just want to be
    // sure that we have a renderer so we can calc what our auto res should
    // be.
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

void GraphicsServer::SetTextureCompressionTypes(
    const std::list<TextureCompressionType>& types) {
  assert(g_base->app_adapter->InGraphicsContext());
  texture_compression_types_ = 0;
  for (auto&& i : types) {
    texture_compression_types_ |= (0x01u << (static_cast<uint32_t>(i)));
  }
  texture_compression_types_set_ = true;
}

void GraphicsServer::SetOrthoProjection(float left, float right, float bottom,
                                        float top, float nearval,
                                        float farval) {
  assert(g_base->app_adapter->InGraphicsContext());
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
  assert(g_base->app_adapter->InGraphicsContext());

  // Reset the modelview stack.
  model_view_stack_.clear();

  auto forward = (target - eye).Normalized();
  auto side = Vector3f::Cross(forward, up_vector).Normalized();
  Vector3f up = Vector3f::Cross(side, forward);

  model_view_matrix_.m[0] = side.x;
  model_view_matrix_.m[4] = side.y;
  model_view_matrix_.m[8] = side.z;
  model_view_matrix_.m[12] = 0.0f;

  model_view_matrix_.m[1] = up.x;
  model_view_matrix_.m[5] = up.y;
  model_view_matrix_.m[9] = up.z;
  model_view_matrix_.m[13] = 0.0f;

  model_view_matrix_.m[2] = -forward.x;
  model_view_matrix_.m[6] = -forward.y;
  model_view_matrix_.m[10] = -forward.z;
  model_view_matrix_.m[14] = 0.0f;

  model_view_matrix_.m[3] = model_view_matrix_.m[7] = model_view_matrix_.m[11] =
      0.0f;
  model_view_matrix_.m[15] = 1.0f;

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

void GraphicsServer::UpdateCamOrientMatrix_() {
  assert(g_base->app_adapter->InGraphicsContext());
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

void GraphicsServer::PushReloadMediaCall() {
  g_base->app_adapter->PushGraphicsContextCall([this] { ReloadMedia_(); });
}

void GraphicsServer::PushSetScreenPixelScaleCall(float pixel_scale) {
  g_base->app_adapter->PushGraphicsContextCall([this, pixel_scale] {
    assert(g_base->app_adapter->InGraphicsContext());
    if (!renderer_) {
      return;
    }
    renderer_->set_pixel_scale(pixel_scale);
  });
}

void GraphicsServer::PushComponentUnloadCall(
    const std::vector<Object::Ref<Asset>*>& components) {
  g_base->app_adapter->PushGraphicsContextCall([components] {
    assert(g_base->app_adapter->InGraphicsContext());
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
  g_base->app_adapter->PushGraphicsContextCall([this] {
    assert(g_base->app_adapter->InGraphicsContext());
    assert(render_hold_);
    render_hold_--;
    if (render_hold_ < 0) {
      Log(LogLevel::kError, "RenderHold < 0");
      render_hold_ = 0;
    }
  });
}

auto GraphicsServer::InGraphicsContext_() const -> bool {
  return g_base->app_adapter->InGraphicsContext();
}

}  // namespace ballistica::base
