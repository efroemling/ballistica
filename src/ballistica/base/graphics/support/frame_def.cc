// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/frame_def.h"

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/mesh/mesh.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_dual_texture_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_object_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_smoke_full.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/core/core.h"

namespace ballistica::base {

FrameDef::FrameDef()
    : main_view_(new FrameDefView(this)),
      current_view_(main_view_.get()),
      overlay_pass_(new RenderPass(RenderPass::Type::kOverlayPass, this)),
      overlay_front_pass_(
          new RenderPass(RenderPass::Type::kOverlayFrontPass, this)),
      vr_cover_pass_(new RenderPass(RenderPass::Type::kVRCoverPass, this)),
      overlay_fixed_pass_(
          new RenderPass(RenderPass::Type::kOverlayFixedPass, this)),
      overlay_flat_pass_(
          new RenderPass(RenderPass::Type::kOverlayFlatPass, this)) {}

FrameDef::~FrameDef() { assert(g_base->InLogicThread()); }

auto FrameDef::GetOverlayFixedPass() -> RenderPass* {
  assert(g_core);
  if (g_core->vr_mode()) {
    return overlay_fixed_pass_.get();
  } else {
    return overlay_pass_.get();
  }
}

auto FrameDef::GetOverlayFlatPass() -> RenderPass* {
  assert(g_core);
  if (g_core->vr_mode()) {
    return overlay_flat_pass_.get();
  } else {
    return overlay_pass_.get();
  }
}

void FrameDef::Reset() {
  assert(g_base->InLogicThread());

  // Update & grab the current settings.
  settings_snapshot_ = g_base->graphics->GetGraphicsSettingsSnapshot();

  auto* settings = settings_snapshot_->get();
  auto* client_context = g_base->graphics->client_context();

  app_time_microsecs_ = 0;
  display_time_microsecs_ = 0;
  display_time_elapsed_microsecs_ = 0;
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
  mesh_index_draw_counts_.clear();
  mesh_buffers_.clear();

  quality_ = Graphics::GraphicsQualityFromRequest(
      settings->graphics_quality, client_context->auto_graphics_quality);

  texture_quality_ = Graphics::TextureQualityFromRequest(
      settings->texture_quality, client_context->auto_texture_quality);

  // pixel_scale_ = g_base->graphics->settings()->pixel_scale;

  // assert(g_base->graphics->has_supports_high_quality_graphics_value());
  main_view_->Reset(g_base->graphics->main_view(), quality_);
  current_view_ = main_view_.get();
  texture_view_count_ = 0;
  wanted_views_.clear();
  view_destroys_.clear();

  overlay_pass_->Reset();
  overlay_front_pass_->Reset();
  if (g_core->vr_mode()) {
    overlay_flat_pass_->Reset();
    overlay_fixed_pass_->Reset();
    vr_cover_pass_->Reset();
  }
}

auto FrameDef::AddTextureView(RenderView* view) -> FrameDefView* {
  assert(g_base->InLogicThread());
  assert(view && view->output() == RenderView::Output::kTexture);
  if (texture_view_count_ >= static_cast<int>(texture_views_.size())) {
    texture_views_.emplace_back(new FrameDefView(this));
  }
  FrameDefView* fview = texture_views_[texture_view_count_].get();
  texture_view_count_++;
  fview->Reset(view, quality_);
  return fview;
}

void FrameDef::Complete() {
  assert(!defining_component_);
  assert(current_view_ == main_view_.get());
  main_view_->Complete();
  for (int i = 0; i < texture_view_count_; i++) {
    texture_views_[i]->Complete();
  }
  overlay_pass_->Complete();
  overlay_front_pass_->Complete();
  if (g_core->vr_mode()) {
    overlay_fixed_pass_->Complete();
    overlay_flat_pass_->Complete();
    vr_cover_pass_->Complete();
  }
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
        mesh_index_draw_counts_.push_back(m->index_draw_count());
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
        mesh_index_draw_counts_.push_back(m->index_draw_count());
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
        mesh_index_draw_counts_.push_back(m->index_draw_count());
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
        mesh_index_draw_counts_.push_back(m->index_draw_count());
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
        mesh_index_draw_counts_.push_back(m->index_draw_count());
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
        mesh_index_draw_counts_.push_back(m->index_draw_count());
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
