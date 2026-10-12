// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/render_view.h"

#include <algorithm>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/component/sprite_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_16.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/core/core.h"

namespace ballistica::base {

static auto NextRenderViewID() -> int {
  assert(g_base->InLogicThread());
  static int next_id{1};
  return next_id++;
}

RenderView::RenderView(Camera* camera)
    : id_(NextRenderViewID()), output_(Output::kScreen), camera_(camera) {
  assert(camera);
}

RenderView::RenderView(Camera* camera, int width, int height)
    : id_(NextRenderViewID()),
      output_(Output::kTexture),
      width_(width),
      height_(height),
      camera_(camera) {
  assert(camera);
  assert(width > 0 && height > 0);
}

RenderView::~RenderView() {
  assert(g_base->InLogicThread());
  if (output_ == Output::kTexture) {
    // Our texture can outlive us (whatever was drawing it may still
    // hold it), so let it know we're gone...
    if (texture_.exists()) {
      texture_->ClearRenderView();
    }
    // ...and let the renderer know it can let go of what it holds
    // for us.
    g_base->graphics->AddRenderViewDestroy(id_);
  }
}

auto RenderView::texture() -> TextureAsset* {
  assert(g_base->InLogicThread());
  assert(output_ == Output::kTexture);
  if (!texture_.exists()) {
    Assets::AssetListLock lock;
    texture_ = g_base->assets->GetRenderViewTexture(this);
  }
  return texture_.get();
}

auto RenderView::wanted() const -> bool {
  assert(g_base->InLogicThread());
  return last_drawn_frame_number_ >= 0
         && last_drawn_frame_number_ >= g_base->graphics->frame_def_count() - 1;
}

void RenderView::SetSize(int width, int height) {
  assert(g_base->InLogicThread());
  assert(output_ == Output::kTexture);
  assert(width > 0 && height > 0);
  width_ = width;
  height_ = height;
}

void RenderView::DrawWorld(FrameDef* frame_def) {}

auto RenderView::GetQuality(GraphicsQuality app_quality) const
    -> GraphicsQuality {
  GraphicsQuality quality = std::min(app_quality, max_quality_);

  // In vr, views drawing to textures stay under the qualities that
  // draw the world to a camera buffer first; how that gets done for
  // the eyes there is its own business and has not been taught about
  // other views.
  if (output_ == Output::kTexture && g_core->vr_mode()) {
    quality = std::min(quality, GraphicsQuality::kMedium);
  }
  return quality;
}

void RenderView::SetShadowRange(float lower_bottom, float lower_top,
                                float upper_bottom, float upper_top) {
  assert(g_base->InLogicThread());
  assert(lower_top >= lower_bottom && upper_bottom >= lower_top
         && upper_top >= upper_bottom);
  shadow_range_.lower_bottom = lower_bottom;
  shadow_range_.lower_top = lower_top;
  shadow_range_.upper_bottom = upper_bottom;
  shadow_range_.upper_top = upper_top;
}

void RenderView::DrawBlotches(FrameDef* frame_def) {
  assert(g_base->InLogicThread());
  if (!blotch_verts_.empty()) {
    if (!shadow_blotch_mesh_.exists()) {
      shadow_blotch_mesh_ = Object::New<SpriteMesh>();
    }
    shadow_blotch_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        blotch_indices_.size(), &blotch_indices_[0]));
    shadow_blotch_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        blotch_verts_.size(), &blotch_verts_[0]));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->base_assets().light.get());
    c.DrawMesh(shadow_blotch_mesh_.get());
    c.Submit();
  }
  if (!blotch_soft_verts_.empty()) {
    if (!shadow_blotch_soft_mesh_.exists()) {
      shadow_blotch_soft_mesh_ = Object::New<SpriteMesh>();
    }
    shadow_blotch_soft_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        blotch_soft_indices_.size(), &blotch_soft_indices_[0]));
    shadow_blotch_soft_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        blotch_soft_verts_.size(), &blotch_soft_verts_[0]));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->base_assets().light_soft.get());
    c.DrawMesh(shadow_blotch_soft_mesh_.get());
    c.Submit();
  }
  if (!blotch_soft_obj_verts_.empty()) {
    if (!shadow_blotch_soft_obj_mesh_.exists()) {
      shadow_blotch_soft_obj_mesh_ = Object::New<SpriteMesh>();
    }
    shadow_blotch_soft_obj_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        blotch_soft_obj_indices_.size(), &blotch_soft_obj_indices_[0]));
    shadow_blotch_soft_obj_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        blotch_soft_obj_verts_.size(), &blotch_soft_obj_verts_[0]));
    SpriteComponent c(frame_def->light_pass());
    c.SetTexture(g_base->assets->base_assets().light_soft.get());
    c.DrawMesh(shadow_blotch_soft_obj_mesh_.get());
    c.Submit();
  }
}

void RenderView::ClearBlotches() {
  assert(g_base->InLogicThread());
  blotch_indices_.clear();
  blotch_verts_.clear();
  blotch_soft_indices_.clear();
  blotch_soft_verts_.clear();
  blotch_soft_obj_indices_.clear();
  blotch_soft_obj_verts_.clear();
}

void RenderView::DoDrawBlotch_(std::vector<uint16_t>* indices,
                               std::vector<VertexSprite>* verts,
                               const Vector3f& pos, float size, float r,
                               float g, float b, float a) {
  assert(g_base->InLogicThread());
  assert(indices && verts);

  // Add verts.
  assert((*verts).size() < 65536);
  auto count = static_cast<uint16_t>((*verts).size());
  (*verts).resize(count + 4);
  {
    VertexSprite& p((*verts)[count]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 0;
    p.uv[1] = 0;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }
  {
    VertexSprite& p((*verts)[count + 1]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 0;
    p.uv[1] = 65535;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }
  {
    VertexSprite& p((*verts)[count + 2]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 65535;
    p.uv[1] = 0;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }
  {
    VertexSprite& p((*verts)[count + 3]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 65535;
    p.uv[1] = 65535;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }

  // Add indices.
  {
    size_t i_count = (*indices).size();
    (*indices).resize(i_count + 6);
    uint16_t* i = &(*indices)[i_count];
    i[0] = count;
    i[1] = static_cast<uint16_t>(count + 1);
    i[2] = static_cast<uint16_t>(count + 2);
    i[3] = static_cast<uint16_t>(count + 1);
    i[4] = static_cast<uint16_t>(count + 3);
    i[5] = static_cast<uint16_t>(count + 2);
  }
}

}  // namespace ballistica::base
