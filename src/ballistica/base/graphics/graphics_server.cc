// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/graphics_server.h"

#include <list>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
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

void GraphicsServer::ApplySettings(const GraphicsSettings* settings) {
  assert(g_base->InGraphicsContext());

  // Only push each unique settings instance through once.
  if (settings->index == settings_index_) {
    return;
  }
  settings_index_ = settings->index;

  assert(settings->resolution.x >= 0.0f && settings->resolution.y >= 0.0f
         && settings->resolution_virtual.x >= 0.0f
         && settings->resolution_virtual.y >= 0.0f);

  // Pull a few things out ourself such as screen resolution.
  tv_border_ = settings->tv_border;
  if (renderer_) {
    renderer_->set_pixel_scale(settings->pixel_scale);
  }
  // Note: need to look at both physical and virtual res here; its possible
  // for physical to stay the same but for virtual to change (ui-scale
  // changes can do this).
  if (res_x_ != settings->resolution.x || res_y_ != settings->resolution.y
      || res_x_virtual_ != settings->resolution_virtual.x
      || res_y_virtual_ != settings->resolution_virtual.y) {
    res_x_ = settings->resolution.x;
    res_y_ = settings->resolution.y;
    res_x_virtual_ = settings->resolution_virtual.x;
    res_y_virtual_ = settings->resolution_virtual.y;
    if (renderer_) {
      renderer_->OnScreenSizeChange();
    }
  }

  // Kick this over to the app-adapter to apply whatever settings they
  // gathered for themself.
  g_base->app_adapter->ApplyGraphicsSettings(settings);

  // If we've not yet sent a context to the client, do so. At some point we
  // may support re-sending this if there are settings that change.
  if (client_context_ == nullptr) {
    set_client_context(g_base->app_adapter->GetGraphicsClientContext());
  }
}

void GraphicsServer::set_client_context(GraphicsClientContext* context) {
  assert(g_base->InGraphicsContext());

  // We have to do a bit of a song and dance with these context pointers. We
  // wrap the context in an immutable object wrapper which is owned by the
  // logic thread and that takes care of killing it when no longer used
  // there, but we also need to keep it alive here in our thread. (which may
  // not be the logic thread). So to accomplish that, we immediately ship a
  // refcount increment over to the logic thread, and once we're done with
  // an obj we ship a decrement.

  auto* old_wrapper = client_context_;
  auto* new_wrapper =
      Object::NewDeferred<Snapshot<GraphicsClientContext>>(context);

  client_context_ = new_wrapper;

  g_base->logic->event_loop()->PushCall([old_wrapper, new_wrapper] {
    // (This has to happen in logic thread).
    auto ref = Object::CompleteDeferred(new_wrapper);

    // Free the old one which the graphics server doesn't need anymore.
    if (old_wrapper) {
      old_wrapper->ObjectDecrementStrongRefCount();
    }

    // Keep the new one alive for the graphics server.
    ref->ObjectIncrementStrongRefCount();

    // Plug the new one in for logic to start using.
    g_base->graphics->set_client_context(new_wrapper);
  });
}

auto GraphicsServer::TryRender() -> bool {
  assert(g_base->app_adapter->InGraphicsContext());

  bool success{};

  if (FrameDef* frame_def = WaitForRenderFrameDef_()) {
    // Apply any new graphics settings passed along via the frame-def.
    ApplySettings(frame_def->settings());

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

    // Send this frame_def back to the logic thread for deletion or
    // recycling.
    g_base->graphics->ReturnCompletedFrameDef(frame_def);
  }

  return success;
}

auto GraphicsServer::WaitForRenderFrameDef_() -> FrameDef* {
  assert(g_base->app_adapter->InGraphicsContext());
  millisecs_t start_time = g_core->AppTimeMillisecs();

  // Spin and wait for a short bit for a frame_def to appear.
  while (true) {
    // Stop waiting if we can't/shouldn't render anyway.
    if (!renderer_ || shutting_down_ || g_base->app_suspended()) {
      return nullptr;
    }

    // Do a bit of incremental loading every time through.
    g_base->assets->RunPendingGraphicsLoads();

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

    // If there's no frame_def for us, sleep for a bit and wait for it.
    millisecs_t t = g_core->AppTimeMillisecs() - start_time;
    if (t >= 1000) {
      if (g_buildconfig.debug_build()) {
        g_core->logging->Log(
            LogName::kBaGraphics, LogLevel::kWarning,
            "GraphicsServer: timed out at " + std::to_string(t)
                + "ms waiting for logic thread to send us a FrameDef.");
      }
      break;  // Fail.
    }
    core::CorePlatform::SleepMillisecs(1);
  }
  return nullptr;
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

  // Set a render-hold so we ignore all frame_defs up until the point at
  // which we receive the corresponding remove-hold. (At which point
  // subsequent frame-defs will be be progress-bar frame_defs so we won't
  // hitch if we actually render them.)
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

  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kDebug,
                       "ReloadLostRenderer() called.");
  if (!renderer_) {
    g_core->logging->Log(
        LogName::kBaGraphics, LogLevel::kError,
        "No renderer on GraphicsServer::ReloadLostRenderer().");
    return;
  }

  // Mark our context as lost so the renderer knows to not try and tear
  // things down itself.
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

void GraphicsServer::set_renderer(Renderer* renderer) {
  assert(g_base->app_adapter->InGraphicsContext());
  assert(!renderer_loaded_);
  assert(!renderer_);
  renderer_ = renderer;
}

void GraphicsServer::LoadRenderer() {
  assert(g_base->app_adapter->InGraphicsContext());
  if (!renderer_) {
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                         "LoadRenderer() called with no renderer present.");
    return;
  }
  if (renderer_loaded_) {
    g_core->logging->Log(
        LogName::kBaGraphics, LogLevel::kError,
        "LoadRenderer() called with an already-loaded renderer present.");
    return;
  }

  graphics_quality_ = Graphics::GraphicsQualityFromRequest(
      graphics_quality_requested_, renderer_->GetAutoGraphicsQuality());

  texture_quality_ = Graphics::TextureQualityFromRequest(
      texture_quality_requested_, renderer_->GetAutoTextureQuality());

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
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                         "UnloadRenderer() called with no renderer present.");
    return;
  }
  if (!renderer_loaded_) {
    g_core->logging->Log(
        LogName::kBaGraphics, LogLevel::kError,
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
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                           "RenderHold < 0");
      render_hold_ = 0;
    }
  });
}

auto GraphicsServer::InGraphicsContext_() const -> bool {
  return g_base->app_adapter->InGraphicsContext();
}

void GraphicsServer::Shutdown() {
  BA_PRECONDITION(!shutting_down_);
  BA_PRECONDITION(g_base->InGraphicsContext());
  shutting_down_ = true;

  // We don't actually do anything here currently; just take note
  // that we're shutting down so we no longer wait for frames to come
  // in from the main thread.
  shutdown_completed_ = true;
}

}  // namespace ballistica::base
