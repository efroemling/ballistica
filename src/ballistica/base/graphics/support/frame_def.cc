// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/frame_def.h"

#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/core/core.h"

namespace ballistica::base {

FrameDef::FrameDef()
    : light_pass_(new RenderPass(RenderPass::Type::kLightPass, this)),
      light_shadow_pass_(
          new RenderPass(RenderPass::Type::kLightShadowPass, this)),
      beauty_pass_(new RenderPass(RenderPass::Type::kBeautyPass, this)),
      beauty_pass_bg_(new RenderPass(RenderPass::Type::kBeautyPassBG, this)),
      overlay_pass_(new RenderPass(RenderPass::Type::kOverlayPass, this)),
      overlay_front_pass_(
          new RenderPass(RenderPass::Type::kOverlayFrontPass, this)),
      overlay_3d_pass_(new RenderPass(RenderPass::Type::kOverlay3DPass, this)),
      vr_cover_pass_(new RenderPass(RenderPass::Type::kVRCoverPass, this)),
      overlay_fixed_pass_(
          new RenderPass(RenderPass::Type::kOverlayFixedPass, this)),
      overlay_flat_pass_(
          new RenderPass(RenderPass::Type::kOverlayFlatPass, this)),
      blit_pass_(new RenderPass(RenderPass::Type::kBlitPass, this)) {}

FrameDef::~FrameDef() { assert(g_base->InLogicThread()); }

auto FrameDef::GetOverlayFixedPass() -> RenderPass* {
  assert(g_core);
  if (g_core->IsVRMode()) {
    return overlay_fixed_pass_.get();
  } else {
    return overlay_pass_.get();
  }
}

auto FrameDef::GetOverlayFlatPass() -> RenderPass* {
  assert(g_core);
  if (g_core->IsVRMode()) {
    return overlay_flat_pass_.get();
  } else {
    return overlay_pass_.get();
  }
}

void FrameDef::Reset() {
  assert(g_base->InLogicThread());
  app_time_millisecs_ = 0;
  base_time_ = 0;
  base_time_elapsed_ = 0;
  frame_number_ = 0;

#if BA_DEBUG_BUILD
  defining_component_ = false;
#endif

  benchmark_type_ = BenchmarkType::kNone;

  mesh_data_creates_.clear();
  mesh_data_destroys_.clear();

  media_components_.clear();
  meshes_.clear();
  mesh_index_sizes_.clear();
  mesh_buffers_.clear();

  quality_ = g_base->graphics_server->quality();

  assert(g_base->graphics->has_supports_high_quality_graphics_value());
  orbiting_ = (g_base->graphics->camera()->mode() == CameraMode::kOrbit);

  shadow_offset_ = g_base->graphics->shadow_offset();
  shadow_scale_ = g_base->graphics->shadow_scale();
  shadow_ortho_ = g_base->graphics->shadow_ortho();
  tint_ = g_base->graphics->tint();
  ambient_color_ = g_base->graphics->ambient_color();

  vignette_outer_ = g_base->graphics->vignette_outer();
  vignette_inner_ = g_base->graphics->vignette_inner();

  light_pass_->Reset();
  light_shadow_pass_->Reset();
  beauty_pass_->Reset();
  beauty_pass_bg_->Reset();
  overlay_pass_->Reset();
  overlay_front_pass_->Reset();
  if (g_core->IsVRMode()) {
    overlay_flat_pass_->Reset();
    overlay_fixed_pass_->Reset();
    vr_cover_pass_->Reset();
  }
  overlay_3d_pass_->Reset();
  blit_pass_->Reset();
  beauty_pass_->set_floor_reflection(g_base->graphics->floor_reflection());
}

void FrameDef::Finalize() {
  assert(!defining_component_);
  light_pass_->Finalize();
  light_shadow_pass_->Finalize();
  beauty_pass_->Finalize();
  beauty_pass_bg_->Finalize();
  overlay_pass_->Finalize();
  overlay_front_pass_->Finalize();
  if (g_core->IsVRMode()) {
    overlay_fixed_pass_->Finalize();
    overlay_flat_pass_->Finalize();
    vr_cover_pass_->Finalize();
  }
  overlay_3d_pass_->Finalize();
  blit_pass_->Finalize();
}

void FrameDef::AddMesh(Mesh* mesh) {
  // Add this mesh's data to the frame only if we haven't yet.
  if (mesh->last_frame_def_num() != frame_number_) {
    mesh->set_last_frame_def_num(frame_number_);
    meshes_.push_back(mesh->mesh_data_client_handle());
    switch (mesh->type()) {
      case MeshDataType::kIndexedSimpleSplit: {
        auto* m = static_cast<MeshIndexedSimpleSplit*>(mesh);
        assert(m);
        assert(m == dynamic_cast<MeshIndexedSimpleSplit*>(mesh));
        mesh_index_sizes_.push_back(
            static_cast_check_fit<int8_t>(m->index_data_size()));
        mesh_buffers_.emplace_back(m->GetIndexData());
        mesh_buffers_.emplace_back(m->static_data());
        mesh_buffers_.emplace_back(m->dynamic_data());
        break;
      }
      case MeshDataType::kIndexedObjectSplit: {
        auto* m = static_cast<MeshIndexedObjectSplit*>(mesh);
        assert(m);
        assert(m == dynamic_cast<MeshIndexedObjectSplit*>(mesh));
        mesh_index_sizes_.push_back(
            static_cast_check_fit<int8_t>(m->index_data_size()));
        mesh_buffers_.emplace_back(m->GetIndexData());
        mesh_buffers_.emplace_back(m->static_data());
        mesh_buffers_.emplace_back(m->dynamic_data());
        break;
      }
      case MeshDataType::kIndexedSimpleFull: {
        auto* m = static_cast<MeshIndexedSimpleFull*>(mesh);
        assert(m);
        assert(m == dynamic_cast<MeshIndexedSimpleFull*>(mesh));
        mesh_index_sizes_.push_back(
            static_cast_check_fit<int8_t>(m->index_data_size()));
        mesh_buffers_.emplace_back(m->GetIndexData());
        mesh_buffers_.emplace_back(m->data());
        break;
      }
      case MeshDataType::kIndexedDualTextureFull: {
        auto* m = static_cast<MeshIndexedDualTextureFull*>(mesh);
        assert(m);
        assert(m == dynamic_cast<MeshIndexedDualTextureFull*>(mesh));
        mesh_index_sizes_.push_back(
            static_cast_check_fit<int8_t>(m->index_data_size()));
        mesh_buffers_.emplace_back(m->GetIndexData());
        mesh_buffers_.emplace_back(m->data());
        break;
      }
      case MeshDataType::kIndexedSmokeFull: {
        auto* m = static_cast<MeshIndexedSmokeFull*>(mesh);
        assert(m);
        assert(m == dynamic_cast<MeshIndexedSmokeFull*>(mesh));
        mesh_index_sizes_.push_back(
            static_cast_check_fit<int8_t>(m->index_data_size()));
        mesh_buffers_.emplace_back(m->GetIndexData());
        mesh_buffers_.emplace_back(m->data());
        break;
      }
      case MeshDataType::kSprite: {
        auto* m = static_cast<SpriteMesh*>(mesh);
        assert(m);
        assert(m == dynamic_cast<SpriteMesh*>(mesh));
        mesh_index_sizes_.push_back(
            static_cast_check_fit<int8_t>(m->index_data_size()));
        mesh_buffers_.emplace_back(m->GetIndexData());
        mesh_buffers_.emplace_back(m->data());
        break;
      }
      default:
        throw Exception();
    }
  }
}

}  // namespace ballistica::base
