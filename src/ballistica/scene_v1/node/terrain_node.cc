// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/terrain_node.h"

#include <string>
#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

class TerrainNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS TerrainNode
  BA_NODE_CREATE_CALL(createTerrain);
  BA_BOOL_ATTR(visible_in_reflections, visible_in_reflections,
               set_visible_in_reflections);
  BA_BOOL_ATTR(affect_bg_dynamics, affects_bg_dynamics,
               set_affects_bg_dynamics);
  BA_BOOL_ATTR(bumper, bumper, SetBumper);
  BA_BOOL_ATTR(background, background, set_background);
  BA_BOOL_ATTR(overlay, overlay, set_overlay);
  BA_FLOAT_ATTR(opacity, opacity, set_opacity);
  BA_FLOAT_ATTR(opacity_in_low_or_medium_quality,
                opacity_in_low_or_medium_quality,
                set_opacity_in_low_or_medium_quality);
  BA_STRING_ATTR(reflection, GetReflection, SetReflection);
  BA_FLOAT_ARRAY_ATTR(reflection_scale, reflection_scale, SetReflectionScale);
  BA_BOOL_ATTR(lighting, getLighting, setLighting);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_MESH_ATTR(mesh, mesh, set_mesh);
  BA_TEXTURE_ATTR(color_texture, color_texture, SetColorTexture);
  BA_COLLISION_MESH_ATTR(collision_mesh, collision_mesh, set_collision_mesh);
  BA_MATERIAL_ARRAY_ATTR(materials, materials, set_materials);
  BA_BOOL_ATTR(vr_only, vr_only, set_vr_only);
#undef BA_NODE_TYPE_CLASS

  TerrainNodeType()
      : NodeType("terrain", createTerrain),
        visible_in_reflections(this),
        affect_bg_dynamics(this),
        bumper(this),
        background(this),
        overlay(this),
        opacity(this),
        opacity_in_low_or_medium_quality(this),
        reflection(this),
        reflection_scale(this),
        lighting(this),
        color(this),
        mesh(this),
        color_texture(this),
        collision_mesh(this),
        materials(this),
        vr_only(this) {}
};
static NodeType* node_type{};

auto TerrainNode::InitType() -> NodeType* {
  node_type = new TerrainNodeType();
  return node_type;
}

TerrainNode::TerrainNode(Scene* scene)
    : Node(scene, node_type),
      visible_in_reflections_(true),
      opacity_(1.0f),
      opacity_in_low_or_medium_quality_(-1.0f),
      terrain_part_(this),
      background_(false),
      overlay_(false),
      lighting_(true),
      bumper_(false),
      affect_bg_dynamics_(true),
      bg_dynamics_collision_mesh_(nullptr),
      reflection_(base::ReflectionType::kNone),
      reflection_scale_(3, 1.0f),
      reflection_scale_r_(1.0f),
      reflection_scale_g_(1.0f),
      reflection_scale_b_(1.0f),
      color_(3, 1.0f),
      color_r_(1.0f),
      color_g_(1.0f),
      color_b_(1.0f),
      vr_only_(false) {
  scene->increment_bg_cover_count();
}

TerrainNode::~TerrainNode() {
  scene()->decrement_bg_cover_count();
  RemoveFromBGDynamics();

  // If we've got a collision-mesh, this is a good time to mark
  // it as used since it may be getting opened up to pruning
  // without our reference.
  if (collision_mesh_.exists()) {
    collision_mesh_->collision_mesh_data()->set_last_used_time(
        g_core->AppTimeMillisecs());
  }
}

auto TerrainNode::materials() const -> std::vector<Material*> {
  return RefsToPointers(materials_);
}

void TerrainNode::set_materials(const std::vector<Material*>& vals) {
  materials_ = PointersToRefs(vals);
  terrain_part_.SetMaterials(vals);
}

void TerrainNode::set_mesh(SceneMesh* val) { mesh_ = val; }

void TerrainNode::set_collision_mesh(SceneCollisionMesh* val) {
  // if we had an old one, mark its last-used time so caching works properly..
  if (collision_mesh_.exists()) {
    collision_mesh_->collision_mesh_data()->set_last_used_time(
        g_core->AppTimeMillisecs());
  }
  collision_mesh_ = val;

  // remove any existing..
  RemoveFromBGDynamics();

  if (collision_mesh_.exists()) {
    uint32_t flags = bumper_ ? RigidBody::kIsBumper : 0;
    flags |= RigidBody::kIsTerrain;
    body_ = Object::New<RigidBody>(
        0, &terrain_part_, RigidBody::Type::kGeomOnly,
        RigidBody::Shape::kTrimesh, RigidBody::kCollideBackground,
        RigidBody::kCollideAll ^ RigidBody::kCollideBackground,
        collision_mesh_.get(), flags);
    body_->set_can_cause_impact_damage(true);

    // also ship it to the BG-Dynamics thread..
    if (!bumper_ && affect_bg_dynamics_) {
      AddToBGDynamics();
    }
  } else {
    body_.Clear();
  }
}

void TerrainNode::SetColorTexture(SceneTexture* val) { color_texture_ = val; }

void TerrainNode::SetReflectionScale(const std::vector<float>& vals) {
  if (vals.size() != 1 && vals.size() != 3) {
    throw Exception("Expected float array of size 1 or 3 for reflection_scale",
                    PyExcType::kValue);
  }
  reflection_scale_ = vals;
  if (reflection_scale_.size() == 1) {
    reflection_scale_r_ = reflection_scale_g_ = reflection_scale_b_ =
        reflection_scale_[0];
  } else {
    reflection_scale_r_ = reflection_scale_[0];
    reflection_scale_g_ = reflection_scale_[1];
    reflection_scale_b_ = reflection_scale_[2];
  }
}

void TerrainNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 1 && vals.size() != 3) {
    throw Exception("Expected float array of size 1 or 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;
  if (color_.size() == 1) {
    color_r_ = color_g_ = color_b_ = color_[0];
  } else {
    color_r_ = color_[0];
    color_g_ = color_[1];
    color_b_ = color_[2];
  }
}

auto TerrainNode::GetReflection() const -> std::string {
  return base::Graphics::StringFromReflectionType(reflection_);
}
void TerrainNode::SetReflection(const std::string& val) {
  reflection_ = base::Graphics::ReflectionTypeFromString(val);
}

void TerrainNode::SetBumper(bool val) {
  bumper_ = val;
  if (body_.exists()) {
    uint32_t is_bumper{RigidBody::kIsBumper};
    if (bumper_) {
      body_->set_flags(body_->flags() | is_bumper);  // on
    } else {
      body_->set_flags(body_->flags() & ~is_bumper);  // off
    }
  }
}

void TerrainNode::AddToBGDynamics() {
  assert(bg_dynamics_collision_mesh_ == nullptr && collision_mesh_.exists()
         && !bumper_ && affect_bg_dynamics_);
  bg_dynamics_collision_mesh_ = collision_mesh_.get();
#if !BA_HEADLESS_BUILD
  g_base->bg_dynamics->AddTerrain(
      bg_dynamics_collision_mesh_->collision_mesh_data());
#endif  // !BA_HEADLESS_BUILD
}

void TerrainNode::RemoveFromBGDynamics() {
  if (bg_dynamics_collision_mesh_ != nullptr) {
#if !BA_HEADLESS_BUILD
    g_base->bg_dynamics->RemoveTerrain(
        bg_dynamics_collision_mesh_->collision_mesh_data());
#endif  // !BA_HEADLESS_BUILD
    bg_dynamics_collision_mesh_ = nullptr;
  }
}

void TerrainNode::Draw(base::FrameDef* frame_def) {
  if (!mesh_.exists()) {
    return;
  }
  if (vr_only_ && !g_core->vr_mode()) {
    return;
  }
  base::ObjectComponent c(overlay_      ? frame_def->overlay_3d_pass()
                          : background_ ? frame_def->beauty_pass_bg()
                                        : frame_def->beauty_pass());
  c.SetWorldSpace(true);
  if (color_texture_.exists()) {
    c.SetTexture(color_texture_->texture_data());
  }
  if (lighting_) {
    c.SetLightShadow(base::LightShadowType::kTerrain);
  } else {
    c.SetLightShadow(base::LightShadowType::kNone);
  }
  if (reflection_ != base::ReflectionType::kNone) {
    c.SetReflection(reflection_);
    c.SetReflectionScale(reflection_scale_r_, reflection_scale_g_,
                         reflection_scale_b_);
  }
  float opacity;
  if (frame_def->quality() <= base::GraphicsQuality::kHigh
      && opacity_in_low_or_medium_quality_ >= 0.0f) {
    opacity = opacity_in_low_or_medium_quality_;
  } else {
    opacity = opacity_;
  }

  // these options currently don't have a world-space-optimized version..
  if (opacity < 1.0f || overlay_) {
    c.SetTransparent(true);
    c.SetWorldSpace(false);
    c.SetColor(color_r_, color_g_, color_b_, opacity);
  } else {
    c.SetColor(color_r_, color_g_, color_b_, 1.0f);
  }
  uint32_t draw_flags = 0;
  if (!visible_in_reflections_) {
    draw_flags |= base::kMeshDrawFlagNoReflection;
  }
  c.DrawMeshAsset(mesh_->mesh_data(), draw_flags);
  c.Submit();
}

}  // namespace ballistica::scene_v1
