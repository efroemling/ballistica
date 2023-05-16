// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_TERRAIN_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_TERRAIN_NODE_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class TerrainNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit TerrainNode(Scene* scene);
  ~TerrainNode() override;
  void Draw(base::FrameDef* frame_def) override;
  auto visible_in_reflections() const -> bool {
    return visible_in_reflections_;
  }
  void set_visible_in_reflections(bool val) { visible_in_reflections_ = val; }
  auto affects_bg_dynamics() const -> bool { return affect_bg_dynamics_; }
  void set_affects_bg_dynamics(bool val) { affect_bg_dynamics_ = val; }
  auto bumper() const -> bool { return bumper_; }
  void SetBumper(bool val);
  auto background() const -> bool { return background_; }
  void set_background(bool val) { background_ = val; }
  auto overlay() const -> bool { return overlay_; }
  void set_overlay(bool val) { overlay_ = val; }
  auto opacity() const -> float { return opacity_; }
  void set_opacity(float val) { opacity_ = val; }
  auto opacity_in_low_or_medium_quality() const -> float {
    return opacity_in_low_or_medium_quality_;
  }
  void set_opacity_in_low_or_medium_quality(float val) {
    opacity_in_low_or_medium_quality_ = val;
  }
  auto GetReflection() const -> std::string;
  void SetReflection(const std::string& val);
  auto reflection_scale() const -> std::vector<float> {
    return reflection_scale_;
  }
  void SetReflectionScale(const std::vector<float>& vals);
  auto getLighting() const -> bool { return lighting_; }
  void setLighting(bool val) { lighting_ = val; }
  auto color() const -> const std::vector<float>& { return color_; }
  void SetColor(const std::vector<float>& vals);
  auto mesh() const -> SceneMesh* { return mesh_.Get(); }
  void set_mesh(SceneMesh* m);
  auto color_texture() const -> SceneTexture* { return color_texture_.Get(); }
  void SetColorTexture(SceneTexture* val);
  auto collision_mesh() const -> SceneCollisionMesh* {
    return collision_mesh_.Get();
  }
  void set_collision_mesh(SceneCollisionMesh* val);
  auto materials() const -> std::vector<Material*>;
  void set_materials(const std::vector<Material*>& vals);
  auto vr_only() const -> bool { return vr_only_; }
  void set_vr_only(bool val) { vr_only_ = val; }

 private:
  void AddToBGDynamics();
  void RemoveFromBGDynamics();
  SceneCollisionMesh* bg_dynamics_collision_mesh_;
  bool vr_only_;
  bool bumper_;
  bool affect_bg_dynamics_;
  bool lighting_;
  bool background_;
  bool overlay_;
  float opacity_;
  float opacity_in_low_or_medium_quality_;
  Object::Ref<SceneMesh> mesh_;
  Object::Ref<SceneCollisionMesh> collision_mesh_;
  Object::Ref<SceneTexture> color_texture_;
  std::vector<Object::Ref<Material> > materials_;
  Part terrain_part_;
  Object::Ref<RigidBody> body_;
  bool visible_in_reflections_;
  base::ReflectionType reflection_;
  std::vector<float> reflection_scale_;
  float reflection_scale_r_, reflection_scale_g_, reflection_scale_b_;
  std::vector<float> color_;
  float color_r_, color_g_, color_b_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_TERRAIN_NODE_H_
