// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics.h"

#include <memory>
#include <utility>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/collision_mesh_asset.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_draw_snapshot.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_fuse_data.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_shadow_data.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_volume_light_data.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/smoke_component.h"
#include "ballistica/base/graphics/component/sprite_component.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_smoke_full.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

BGDynamics::BGDynamics() = default;

void BGDynamics::AddTerrain(CollisionMeshAsset* o) {
  assert(g_base->InLogicThread());

  // Allocate a fresh reference to keep this collision-mesh alive as long as
  // we're using it. Once we're done, we'll pass the pointer back to the
  // main thread to free.
  auto* mesh_ref = new Object::Ref<CollisionMeshAsset>(o);
  g_base->bg_dynamics_server->PushAddTerrainCall(mesh_ref);
}

void BGDynamics::RemoveTerrain(CollisionMeshAsset* o) {
  assert(g_base->InLogicThread());
  g_base->bg_dynamics_server->PushRemoveTerrainCall(o);
}

void BGDynamics::Emit(const BGDynamicsEmission& e) {
  assert(g_base->InLogicThread());
  g_base->bg_dynamics_server->PushEmitCall(e);
}

void BGDynamics::Step(const Vector3f& cam_pos, int step_millisecs) {
  assert(g_base->InLogicThread());

  // Don't actually start doing anything until there's a
  // client-graphics-context. We need this to calculate qualities/etc.
  if (!g_base->graphics->has_client_context()) {
    return;
  }

  // The BG dynamics thread just processes steps as fast as it can;
  // we need to throttle what we send or tell it to cut back if its behind
  int step_count = g_base->bg_dynamics_server->step_count();

  // If we're really getting behind, start pruning stuff.
  if (step_count > 3) {
    TooSlow();
  }

  // If we're slightly behind, just don't send this step; the bg dynamics
  // will slow down a bit but nothing will disappear this way, which should
  // be less jarring.
  //
  // HMMM; wondering if this should be limited in some way; it might lead to
  // oddly slow feeling bg sims if things are consistently slow.
  if (step_count > 1) {
    return;
  }

  // Pass a newly allocated raw pointer to the bg-dynamics thread; it takes
  // care of disposing it when done.
  auto d = Object::NewDeferred<BGDynamicsServer::StepData>();
  d->graphics_quality = Graphics::GraphicsQualityFromRequest(
      g_base->graphics->settings()->graphics_quality,
      g_base->graphics->client_context()->auto_graphics_quality);
  d->step_millisecs = step_millisecs;
  d->cam_pos = cam_pos;

  {  // Shadows.
    BA_DEBUG_TIME_CHECK_BEGIN(bg_dynamic_shadow_list_lock);
    {
      std::scoped_lock lock(g_base->bg_dynamics_server->shadow_list_mutex());
      auto size = g_base->bg_dynamics_server->shadows().size();
      d->shadow_step_data_.resize(size);
      if (size > 0) {
        auto sd_client = &(g_base->bg_dynamics_server->shadows()[0]);
        std::pair<BGDynamicsShadowData*, BGDynamicsServer::ShadowStepData>* sd =
            &(d->shadow_step_data_[0]);
        for (size_t i = 0; i < size; i++) {
          // Set to nullptr (for ignore) if the client side is dead.
          sd[i].first = sd_client[i]->client_dead ? nullptr : sd_client[i];
          sd[i].second.position = sd_client[i]->pos_client;
        }
      }
    }
    BA_DEBUG_TIME_CHECK_END(bg_dynamic_shadow_list_lock, 10);
  }
  {  // Volume lights.
    BA_DEBUG_TIME_CHECK_BEGIN(bg_dynamic_volumelights_list_lock);
    {
      std::scoped_lock lock(
          g_base->bg_dynamics_server->volume_light_list_mutex());
      auto size = g_base->bg_dynamics_server->volume_lights().size();
      d->volume_light_step_data_.resize(size);
      if (size > 0) {
        auto vd_client = &(g_base->bg_dynamics_server->volume_lights()[0]);
        std::pair<BGDynamicsVolumeLightData*,
                  BGDynamicsServer::VolumeLightStepData>* vd =
            &(d->volume_light_step_data_[0]);
        for (size_t i = 0; i < size; i++) {
          // Set to nullptr (for ignore) if the client side is dead.
          vd[i].first = vd_client[i]->client_dead ? nullptr : vd_client[i];
          vd[i].second.pos = vd_client[i]->pos_client;
          vd[i].second.radius = vd_client[i]->radius_client;
          vd[i].second.r = vd_client[i]->r_client;
          vd[i].second.g = vd_client[i]->g_client;
          vd[i].second.b = vd_client[i]->b_client;
        }
      }
    }
    BA_DEBUG_TIME_CHECK_END(bg_dynamic_volumelights_list_lock, 10);
  }
  {  // Fuses.
    BA_DEBUG_TIME_CHECK_BEGIN(bg_dynamic_fuse_list_lock);
    {
      std::scoped_lock lock(g_base->bg_dynamics_server->fuse_list_mutex());
      auto size = g_base->bg_dynamics_server->fuses().size();
      d->fuse_step_data_.resize(size);
      if (size > 0) {
        auto fd_client = &(g_base->bg_dynamics_server->fuses()[0]);
        std::pair<BGDynamicsFuseData*, BGDynamicsServer::FuseStepData>* fd =
            &(d->fuse_step_data_[0]);
        for (size_t i = 0; i < size; i++) {
          // Set to nullptr (for ignore) if the client side is dead.
          fd[i].first = fd_client[i]->client_dead_ ? nullptr : fd_client[i];
          fd[i].second.transform = fd_client[i]->transform_client_;
          fd[i].second.have_transform = fd_client[i]->have_transform_client_;
          fd[i].second.length = fd_client[i]->length_client_;
        }
      }
    }
    BA_DEBUG_TIME_CHECK_END(bg_dynamic_fuse_list_lock, 10);
  }

  // Ok send the thread on its way.
  g_base->bg_dynamics_server->PushStep(d);
}

void BGDynamics::SetDrawSnapshot(BGDynamicsDrawSnapshot* s) {
  // We were passed a raw pointer; assign it to our unique_ptr which will
  // take ownership of it and handle disposing it when we get the next one.
  draw_snapshot_ = std::unique_ptr<BGDynamicsDrawSnapshot>(s);
}

void BGDynamics::TooSlow() {
  if (!EventLoop::AreEventLoopsSuspended()) {
    g_base->bg_dynamics_server->PushTooSlowCall();
  }
}

void BGDynamics::SetDebrisFriction(float val) {
  assert(g_base->InLogicThread());
  g_base->bg_dynamics_server->PushSetDebrisFrictionCall(val);
}

void BGDynamics::SetDebrisKillHeight(float val) {
  assert(g_base->InLogicThread());
  g_base->bg_dynamics_server->PushSetDebrisKillHeightCall(val);
}

void BGDynamics::Draw(FrameDef* frame_def) {
  assert(g_base->InLogicThread());

  BGDynamicsDrawSnapshot* ds{draw_snapshot_.get()};
  if (!ds) {
    return;
  }

  // Draw sparks.
  if (ds->spark_vertices.exists()) {
    if (!sparks_mesh_.exists()) sparks_mesh_ = Object::New<SpriteMesh>();
    sparks_mesh_->SetIndexData(ds->spark_indices);
    sparks_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSprite>>(ds->spark_vertices));

    // In high-quality, we draw in the overlay pass so that we don't get wiped
    // out by depth-of-field.
    bool draw_in_overlay = frame_def->quality() >= GraphicsQuality::kHigh;
    SpriteComponent c(draw_in_overlay ? frame_def->overlay_3d_pass()
                                      : frame_def->beauty_pass());
    c.SetCameraAligned(true);
    c.SetColor(2.0f, 2.0f, 2.0f, 1.0f);
    c.SetOverlay(draw_in_overlay);
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kSparks));
    c.DrawMesh(sparks_mesh_.get(), kMeshDrawFlagNoReflection);
    c.Submit();
  }

  // Draw lights.
  if (ds->light_vertices.exists()) {
    assert(ds->light_indices.exists());
    assert(!ds->light_indices->elements.empty());
    assert(!ds->light_vertices->elements.empty());
    if (!lights_mesh_.exists()) lights_mesh_ = Object::New<SpriteMesh>();
    lights_mesh_->SetIndexData(ds->light_indices);
    lights_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSprite>>(ds->light_vertices));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kLightSoft));
    c.DrawMesh(lights_mesh_.get());
    c.Submit();
  }

  // Draw shadows.
  if (ds->shadow_vertices.exists()) {
    assert(ds->shadow_indices.exists());
    if (!shadows_mesh_.exists()) {
      shadows_mesh_ = Object::New<SpriteMesh>();
    }
    shadows_mesh_->SetIndexData(ds->shadow_indices);
    shadows_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSprite>>(ds->shadow_vertices));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kLight));
    c.DrawMesh(shadows_mesh_.get());
    c.Submit();
  }

  // Draw chunks.
  DrawChunks(frame_def, &ds->rocks, BGDynamicsChunkType::kRock);
  DrawChunks(frame_def, &ds->ice, BGDynamicsChunkType::kIce);
  DrawChunks(frame_def, &ds->slime, BGDynamicsChunkType::kSlime);
  DrawChunks(frame_def, &ds->metal, BGDynamicsChunkType::kMetal);
  DrawChunks(frame_def, &ds->sparks, BGDynamicsChunkType::kSpark);
  DrawChunks(frame_def, &ds->splinters, BGDynamicsChunkType::kSplinter);
  DrawChunks(frame_def, &ds->sweats, BGDynamicsChunkType::kSweat);
  DrawChunks(frame_def, &ds->flag_stands, BGDynamicsChunkType::kFlagStand);

  // Draw tendrils.
  if (ds->tendril_vertices.exists()) {
    if (!tendrils_mesh_.exists())
      tendrils_mesh_ = Object::New<MeshIndexedSmokeFull>();
    tendrils_mesh_->SetIndexData(ds->tendril_indices);
    tendrils_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSmokeFull>>(ds->tendril_vertices));
    bool draw_in_overlay = frame_def->quality() >= GraphicsQuality::kHigh;
    SmokeComponent c(draw_in_overlay ? frame_def->overlay_3d_pass()
                                     : frame_def->beauty_pass());
    c.SetOverlay(draw_in_overlay);
    c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
    c.DrawMesh(tendrils_mesh_.get(), kMeshDrawFlagNoReflection);
    c.Submit();

    // Shadows.
    if (frame_def->quality() >= GraphicsQuality::kHigher) {
      for (auto&& i : ds->tendril_shadows) {
        if (i.density > 0.0001f) {
          Vector3f& p(i.p);
          g_base->graphics->DrawBlotch(p, 2.0f * i.density, 0.02f * i.density,
                                       0.01f * i.density, 0, 0.15f * i.density);
        }
      }
    }
  }

  // Draw fuses.
  if (ds->fuse_vertices.exists()) {
    // Update our mesh with this data.
    if (!fuses_mesh_.exists())
      fuses_mesh_ = Object::New<MeshIndexedSimpleFull>();
    fuses_mesh_->SetIndexData(ds->fuse_indices);
    fuses_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSimpleFull>>(ds->fuse_vertices));
    {  // Draw!
      ObjectComponent c(frame_def->beauty_pass());
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kFuse));
      c.DrawMesh(fuses_mesh_.get(), kMeshDrawFlagNoReflection);
      c.Submit();
    }
  }
}

void BGDynamics::DrawChunks(FrameDef* frame_def,
                            std::vector<Matrix44f>* draw_snapshot,
                            BGDynamicsChunkType chunk_type) {
  if (!draw_snapshot || draw_snapshot->empty()) {
    return;
  }

  // Draw ourselves into the beauty pass.
  MeshAsset* mesh;
  switch (chunk_type) {
    case BGDynamicsChunkType::kFlagStand:
      mesh = g_base->assets->SysMesh(SysMeshID::kFlagStand);
      break;
    case BGDynamicsChunkType::kSplinter:
      mesh = g_base->assets->SysMesh(SysMeshID::kShrapnelBoard);
      break;
    case BGDynamicsChunkType::kSlime:
      mesh = g_base->assets->SysMesh(SysMeshID::kShrapnelSlime);
      break;
    default:
      mesh = g_base->assets->SysMesh(SysMeshID::kShrapnel1);
      break;
  }
  ObjectComponent c(frame_def->beauty_pass());

  // Set up shading.
  switch (chunk_type) {
    case BGDynamicsChunkType::kRock: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.2f, 0.2f, 0.2f);
      c.SetColor(0.6f, 0.6f, 0.5f);
      break;
    }
    case BGDynamicsChunkType::kIce: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kSharp);
      c.SetAddColor(0.5f, 0.5f, 0.9f);
      break;
    }
    case BGDynamicsChunkType::kSlime: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kSharper);
      c.SetReflectionScale(3.0f, 3.0f, 3.0f);
      c.SetColor(0.0f, 0.0f, 0.0f);
      c.SetAddColor(0.6f, 0.7f, 0.08f);
      break;
    }
    case BGDynamicsChunkType::kMetal: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kPowerup);
      c.SetColor(0.5f, 0.5f, 0.55f);
      break;
    }
    case BGDynamicsChunkType::kSpark: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kSharp);
      c.SetColor(0.0f, 0.0f, 0.0f, 1.0f);
      c.SetReflectionScale(4.0f, 3.0f, 2.0f);
      c.SetAddColor(3.0f, 0.8f, 0.6f);
      break;
    }
    case BGDynamicsChunkType::kSplinter: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kSoft);
      c.SetColor(1.0f, 0.8f, 0.5f);
      break;
    }
    case BGDynamicsChunkType::kSweat: {
      c.SetTransparent(true);
      c.SetPremultiplied(true);
      c.SetLightShadow(LightShadowType::kNone);
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kShrapnel1));
      c.SetReflection(ReflectionType::kSharp);
      c.SetReflectionScale(0.5f, 0.4f, 0.3f);
      c.SetColor(0.2f, 0.15f, 0.15f, 0.07f);
      c.SetAddColor(0.05f, 0.05f, 0.01f);
      break;
    }
    case BGDynamicsChunkType::kFlagStand: {
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kFlagPole));
      c.SetReflection(ReflectionType::kSharp);
      c.SetColor(0.9f, 0.6f, 0.3f, 1.0f);
      break;
    }
  }
  c.DrawMeshAssetInstanced(mesh, *draw_snapshot, kMeshDrawFlagNoReflection);
  c.Submit();
}

}  // namespace ballistica::base
