// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/collision_mesh_asset.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_draw_snapshot.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world_server.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/smoke_component.h"
#include "ballistica/base/graphics/component/sprite_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_object_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_smoke_full.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

BGDynamicsWorld::BGDynamicsWorld(RenderView* view)
    : view_(view), server_(BGDynamicsWorldServer::Create()) {
  assert(g_base->InLogicThread());
}

BGDynamicsWorld::~BGDynamicsWorld() {
  assert(g_base->InLogicThread());

  // Our other half lives on its own thread and goes there, after
  // whatever we have pushed its way. Results it still has for us go
  // with it.
  server_->PushDestroy();
  server_ = nullptr;
}

void BGDynamicsWorld::AddTerrain(CollisionMeshAsset* o,
                                 const Matrix44f& transform) {
  assert(g_base->InLogicThread());

  // Allocate a fresh reference to keep this collision-mesh alive as long as
  // we're using it. Once we're done, we'll pass the pointer back to the
  // main thread to free.
  auto* mesh_ref = new Object::Ref<CollisionMeshAsset>(o);
  server_->PushAddTerrainCall(mesh_ref, transform);
}

void BGDynamicsWorld::RemoveTerrain(CollisionMeshAsset* o) {
  assert(g_base->InLogicThread());
  server_->PushRemoveTerrainCall(o);
}

void BGDynamicsWorld::Emit(const BGDynamicsEmission& e) {
  assert(g_base->InLogicThread());
  server_->PushEmitCall(e);
}

void BGDynamicsWorld::AdoptResults(bool wait_for_pending) {
  assert(g_base->InLogicThread());
  BGDynamicsWorldServer* server = server_;
  if (wait_for_pending) {
    auto t0 = std::chrono::steady_clock::now();
    bool idle = server->WaitForIdle(kBGDynamicsDrawWaitMicros);
    if (g_base->bg_dynamics_server->profile()) {
      wait_profile_micros_ += std::chrono::duration<double, std::micro>(
                                  std::chrono::steady_clock::now() - t0)
                                  .count();
      wait_profile_frames_++;
      if (!idle) {
        wait_profile_timeouts_++;
      }
      if (wait_profile_frames_ >= 300) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kInfo,
            "bg-dynamics draw wait: mean "
                + std::to_string(wait_profile_micros_ / wait_profile_frames_)
                + "us over " + std::to_string(wait_profile_frames_)
                + " frames, " + std::to_string(wait_profile_timeouts_)
                + " timed out.");
        wait_profile_micros_ = 0.0;
        wait_profile_frames_ = wait_profile_timeouts_ = 0;
      }
    }
  }
  BGDynamicsDrawSnapshot* snapshot{};
  BGDynamicsOutputBundle* bundle{};
  server->TakeResults(&snapshot, &bundle);
  if (snapshot) {
    snapshot->SetLogicThreadOwnership();
    SetDrawSnapshot(snapshot);
  }
  if (bundle) {
    SetOutputBundle(bundle);
  }
}

void BGDynamicsWorld::Step(const Vector3f& cam_pos, int step_millisecs) {
  assert(g_base->InLogicThread());

  // Don't actually start doing anything until there's a
  // client-graphics-context. We need this to calculate qualities/etc.
  if (!g_base->graphics->has_client_context()) {
    return;
  }

  // Whatever the bg thread has finished since we last looked.
  AdoptResults(false);

  // The BG dynamics thread just processes steps as fast as it can;
  // we need to throttle what we send or tell it to cut back if its behind
  int step_count = server_->step_count();

  // If we're really getting behind, start pruning stuff.
  // NOTE: unreachable as written -- the feed-skip below caps the pending
  // count at 2 -- so this has been dead since that skip was added. The
  // drop ratio tracked in UpdateLoadSkip_ is the live "behind" signal;
  // re-base this on it (or drop it) when the chunk valve gets revisited.
  if (step_count > 3) {
    TooSlow();
  }

  // If we're slightly behind, just don't send this step; the bg dynamics
  // will slow down a bit but nothing will disappear this way, which should
  // be less jarring.
  //
  // HMMM; wondering if this should be limited in some way; it might lead to
  // oddly slow feeling bg sims if things are consistently slow.
  bool feed_dropped = step_count > 1;
  UpdateLoadSkip_(feed_dropped, step_millisecs);
  if (feed_dropped) {
    return;
  }

  // Pass a newly allocated raw pointer to the bg-dynamics thread; it takes
  // care of disposing it when done.
  auto d = Object::NewDeferred<BGDynamicsWorldServer::StepData>();
  d->graphics_quality = view_->GetQuality(Graphics::GraphicsQualityFromRequest(
      g_base->graphics->settings()->graphics_quality,
      g_base->graphics->client_context()->auto_graphics_quality));
  d->step_millisecs = step_millisecs;
  d->cam_pos = cam_pos;
  d->debug_draw = g_base->graphics->debug_draw();
  d->shadow_range = view_->shadow_range();

  // Channel entities: inputs plus pending create/destroy deltas.
  BGDynamicsForEachPair(
      channels_, d->channels,
      [](auto& channel, auto& step_data) { channel.Gather(&step_data); });

  // Ok send the thread on its way.
  server_->PushStep(d);
}

void BGDynamicsWorld::SetDrawSnapshot(BGDynamicsDrawSnapshot* s) {
  assert(g_base->InLogicThread());
  // Hand the previous one back for reuse: Reset here releases its mesh
  // buffers on this thread (which owns them after
  // SetLogicThreadOwnership) and leaves the vectors' capacity for the
  // bg thread to fill again.
  if (BGDynamicsDrawSnapshot* old = draw_snapshot_.release()) {
    old->Reset();
    server_->RecycleSnapshot(old);
  }
  draw_snapshot_ = std::unique_ptr<BGDynamicsDrawSnapshot>(s);
}

void BGDynamicsWorld::SetOutputBundle(BGDynamicsOutputBundle* bundle) {
  assert(g_base->InLogicThread());
  BGDynamicsForEachPair(
      channels_, bundle->channels,
      [](auto& channel, auto& outputs) { channel.Adopt(&outputs); });
  // Adopt swapped our previous outputs into it; back it goes for reuse.
  server_->RecycleBundle(bundle);
}

void BGDynamicsWorld::UpdateLoadSkip_(bool feed_dropped, int step_millisecs) {
  // Tally feeds over one-second windows. A dropped feed means the bg
  // thread was still chewing on the previous two steps, i.e. the bg
  // sim is running slower than we are.
  feed_window_millisecs_ += step_millisecs;
  feed_window_total_++;
  if (feed_dropped) {
    feed_window_dropped_++;
  }
  millisecs_since_bump_ += step_millisecs;
  millisecs_since_bump_log_ += step_millisecs;
  if (feed_window_millisecs_ < 1000) {
    return;
  }
  float window_seconds = static_cast<float>(feed_window_millisecs_) / 1000.0f;
  float drop_ratio = static_cast<float>(feed_window_dropped_)
                     / static_cast<float>(std::max(feed_window_total_, 1));
  feed_window_millisecs_ = 0;
  feed_window_total_ = 0;
  feed_window_dropped_ = 0;

  // Under --dynamics-profile, report the feed health once a second so
  // the lever's bumps and recovery can be watched.
  if (g_base->bg_dynamics_server->profile()) {
    char buf[120];
    snprintf(buf, sizeof(buf),
             "bg-dynamics feed: %.0f%% dropped this second; character-rig load"
             " skip %.2f",
             100.0f * drop_ratio, load_skip_);
    g_core->logging->Log(LogName::kBa, LogLevel::kInfo, buf);
  }

  if (drop_ratio > 0.5f) {
    // Emergency: the bg sim is at half speed or worse. Shed rig load
    // in 25% steps, no faster than once a second, and say so -- this
    // is a lever we don't expect to need.
    if (millisecs_since_bump_ >= 1000 && load_skip_ < 1.0f) {
      load_skip_ = std::min(1.0f, load_skip_ + 0.25f);
      millisecs_since_bump_ = 0;
      // Warn, but no more than once per 30s: a machine hovering at the
      // threshold would otherwise bump, recover and bump forever.
      if (millisecs_since_bump_log_ >= 30000) {
        std::string suffix;
        if (unlogged_bumps_ > 0) {
          suffix = " (+" + std::to_string(unlogged_bumps_)
                   + " unlogged bumps since last warning)";
        }
        char buf[200];
        snprintf(buf, sizeof(buf),
                 "bg-dynamics overloaded (%.0f%% of feeds dropped this"
                 " second); character-rig load skip -> %.2f%s",
                 100.0f * drop_ratio, load_skip_, suffix.c_str());
        g_core->logging->Log(LogName::kBa, LogLevel::kWarning, buf);
        millisecs_since_bump_log_ = 0;
        unlogged_bumps_ = 0;
      } else {
        unlogged_bumps_++;
      }
    }
  } else if (drop_ratio < 0.1f && load_skip_ > 0.0f) {
    // Healthy again: ease back toward full dynamics at 0.1/s.
    load_skip_ = std::max(0.0f, load_skip_ - 0.1f * window_seconds);
  }
}

void BGDynamicsWorld::TooSlow() {
  if (!EventLoop::AreEventLoopsSuspended()) {
    server_->PushTooSlowCall();
  }
}

void BGDynamicsWorld::SetDebrisFriction(float val) {
  assert(g_base->InLogicThread());
  server_->PushSetDebrisFrictionCall(val);
}

void BGDynamicsWorld::SetDebrisKillHeight(float val) {
  assert(g_base->InLogicThread());
  server_->PushSetDebrisKillHeightCall(val);
}

auto BGDynamicsWorld::QuadIndices_(int slot, size_t quad_count)
    -> const Object::Ref<MeshIndexBuffer16>& {
  assert(g_base->InLogicThread());
  assert(slot >= 0 && slot < 3);
  auto& cached = quad_indices_[slot];
  // 16-bit indices address 4 verts per quad up to 16383 quads.
  assert(quad_count <= 16383);
  size_t have = cached.exists() ? cached->elements.size() / 6 : 0;
  if (quad_count > have) {
    // Grow generously so this settles quickly.
    size_t new_count = std::max(quad_count, std::max(have * 2, size_t{256}));
    new_count = std::min(new_count, size_t{16383});
    auto* ibuf = Object::NewDeferred<MeshIndexBuffer16>(new_count * 6);
    uint16_t* i_out = &ibuf->elements[0];
    for (size_t i = 0; i < new_count; ++i) {
      auto v = static_cast<uint16_t>(i * 4);
      i_out[0] = v;
      i_out[1] = static_cast<uint16_t>(v + 1);
      i_out[2] = static_cast<uint16_t>(v + 2);
      i_out[3] = static_cast<uint16_t>(v + 1);
      i_out[4] = static_cast<uint16_t>(v + 3);
      i_out[5] = static_cast<uint16_t>(v + 2);
      i_out += 6;
    }
    cached = Object::CompleteDeferred(ibuf);
  }
  return cached;
}

void BGDynamicsWorld::Draw(FrameDef* frame_def) {
  assert(g_base->InLogicThread());

  BGDynamicsDrawSnapshot* ds{draw_snapshot_.get()};
  if (!ds) {
    return;
  }

  // Draw sparks.
  if (ds->spark_vertices.exists()) {
    if (!sparks_mesh_.exists()) sparks_mesh_ = Object::New<SpriteMesh>();
    size_t quads = ds->spark_vertices->elements.size() / 4;
    sparks_mesh_->SetIndexData(QuadIndices_(kQuadIndexSlotSparks, quads));
    sparks_mesh_->set_index_draw_count(static_cast<uint32_t>(quads * 6));
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
    c.SetTexture(g_base->assets->base_assets().sparks.get());
    c.DrawMesh(sparks_mesh_.get(), kMeshDrawFlagNoReflection);
    c.Submit();
  }

  // Draw lights.
  if (ds->light_vertices.exists()) {
    assert(!ds->light_vertices->elements.empty());
    if (!lights_mesh_.exists()) lights_mesh_ = Object::New<SpriteMesh>();
    size_t quads = ds->light_vertices->elements.size() / 4;
    lights_mesh_->SetIndexData(QuadIndices_(kQuadIndexSlotLights, quads));
    lights_mesh_->set_index_draw_count(static_cast<uint32_t>(quads * 6));
    lights_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSprite>>(ds->light_vertices));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->base_assets().light_soft.get());
    c.DrawMesh(lights_mesh_.get());
    c.Submit();
  }

  // Draw shadows.
  if (ds->shadow_vertices.exists()) {
    if (!shadows_mesh_.exists()) {
      shadows_mesh_ = Object::New<SpriteMesh>();
    }
    size_t quads = ds->shadow_vertices->elements.size() / 4;
    shadows_mesh_->SetIndexData(QuadIndices_(kQuadIndexSlotShadows, quads));
    shadows_mesh_->set_index_draw_count(static_cast<uint32_t>(quads * 6));
    shadows_mesh_->SetData(
        Object::Ref<MeshBuffer<VertexSprite>>(ds->shadow_vertices));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->base_assets().light.get());
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
      RenderView* view = view_.get();
      for (auto&& i : ds->tendril_shadows) {
        if (i.density > 0.0001f) {
          Vector3f& p(i.p);
          view->DrawBlotch(p, 2.0f * i.density, 0.02f * i.density,
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
      c.SetTexture(g_base->assets->base_assets().fuse.get());
      c.DrawMesh(fuses_mesh_.get(), kMeshDrawFlagNoReflection);
      c.Submit();
    }
  }
}

void BGDynamicsWorld::DrawChunks(FrameDef* frame_def,
                                 std::vector<Matrix44f>* draw_snapshot,
                                 BGDynamicsChunkType chunk_type) {
  if (!draw_snapshot || draw_snapshot->empty()) {
    return;
  }

  // Debug-draw mode: chunks are all box bodies, and each snapshot matrix
  // already bakes in the body's box size, so the unit debug box under it
  // is exactly the collider.
  if (g_base->graphics->debug_draw()) {
    // Flag stands are the one non-dynamic chunk type (no body/geom; just
    // decoration with a placeholder size), so there's nothing to show.
    if (chunk_type == BGDynamicsChunkType::kFlagStand) {
      return;
    }
    float r, g, b;
    switch (chunk_type) {
      case BGDynamicsChunkType::kRock:
        r = 0.6f;
        g = 0.6f;
        b = 0.5f;
        break;
      case BGDynamicsChunkType::kIce:
        r = 0.6f;
        g = 0.7f;
        b = 1.0f;
        break;
      case BGDynamicsChunkType::kSlime:
        r = 0.6f;
        g = 0.9f;
        b = 0.2f;
        break;
      case BGDynamicsChunkType::kMetal:
        r = 0.7f;
        g = 0.7f;
        b = 0.8f;
        break;
      case BGDynamicsChunkType::kSpark:
        r = 1.0f;
        g = 0.6f;
        b = 0.3f;
        break;
      case BGDynamicsChunkType::kSplinter:
        r = 1.0f;
        g = 0.8f;
        b = 0.5f;
        break;
      case BGDynamicsChunkType::kSweat:
        r = 0.7f;
        g = 0.8f;
        b = 1.0f;
        break;
      case BGDynamicsChunkType::kFlagStand:
        return;  // Handled above.
    }
    BGDynamicsDebugTint(&r, &g, &b);
    ObjectComponent c(frame_def->beauty_pass());
    c.SetFacingRatio(true);
    c.SetLightShadow(LightShadowType::kObject);
    c.SetColor(r, g, b);
    auto* box = g_base->graphics->debug_box_mesh();
    for (const Matrix44f& m : *draw_snapshot) {
      auto xf = c.ScopedTransform();
      c.MultMatrix(m.m);
      c.DrawMesh(box, kMeshDrawFlagNoReflection);
    }
    c.Submit();
    return;
  }

  // Draw ourselves into the beauty pass.
  MeshAsset* mesh;
  switch (chunk_type) {
    case BGDynamicsChunkType::kFlagStand:
      mesh = g_base->assets->base_assets().flag_stand.get();
      break;
    case BGDynamicsChunkType::kSplinter:
      mesh = g_base->assets->base_assets().shrapnel_board.get();
      break;
    case BGDynamicsChunkType::kSlime:
      mesh = g_base->assets->base_assets().shrapnel_slime.get();
      break;
    default:
      mesh = g_base->assets->base_assets().shrapnel_rock.get();
      break;
  }
  ObjectComponent c(frame_def->beauty_pass());

  // Set up shading.
  switch (chunk_type) {
    case BGDynamicsChunkType::kRock: {
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.2f, 0.2f, 0.2f);
      c.SetColor(0.6f, 0.6f, 0.5f);
      break;
    }
    case BGDynamicsChunkType::kIce: {
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kSharp);
      c.SetAddColor(0.5f, 0.5f, 0.9f);
      break;
    }
    case BGDynamicsChunkType::kSlime: {
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kSharper);
      c.SetReflectionScale(3.0f, 3.0f, 3.0f);
      c.SetColor(0.0f, 0.0f, 0.0f);
      c.SetAddColor(0.6f, 0.7f, 0.08f);
      break;
    }
    case BGDynamicsChunkType::kMetal: {
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kPowerup);
      c.SetColor(0.5f, 0.5f, 0.55f);
      break;
    }
    case BGDynamicsChunkType::kSpark: {
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kSharp);
      c.SetColor(0.0f, 0.0f, 0.0f, 1.0f);
      c.SetReflectionScale(4.0f, 3.0f, 2.0f);
      c.SetAddColor(3.0f, 0.8f, 0.6f);
      break;
    }
    case BGDynamicsChunkType::kSplinter: {
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kSoft);
      c.SetColor(1.0f, 0.8f, 0.5f);
      break;
    }
    case BGDynamicsChunkType::kSweat: {
      c.SetTransparent(true);
      c.SetPremultiplied(true);
      c.SetLightShadow(LightShadowType::kNone);
      c.SetTexture(g_base->assets->base_assets().shrapnel_rock_color.get());
      c.SetReflection(ReflectionType::kSharp);
      c.SetReflectionScale(0.5f, 0.4f, 0.3f);
      c.SetColor(0.2f, 0.15f, 0.15f, 0.07f);
      c.SetAddColor(0.05f, 0.05f, 0.01f);
      break;
    }
    case BGDynamicsChunkType::kFlagStand: {
      c.SetTexture(g_base->assets->base_assets().flag_pole_color.get());
      c.SetReflection(ReflectionType::kSharp);
      c.SetColor(0.9f, 0.6f, 0.3f, 1.0f);
      break;
    }
  }
  c.DrawMeshAssetInstanced(mesh, *draw_snapshot, kMeshDrawFlagNoReflection);
  c.Submit();
}

}  // namespace ballistica::base
