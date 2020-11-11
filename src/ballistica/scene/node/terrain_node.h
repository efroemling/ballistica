// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_TERRAIN_NODE_H_
#define BALLISTICA_SCENE_NODE_TERRAIN_NODE_H_

#include <string>
#include <vector>

#include "ballistica/dynamics/part.h"
#include "ballistica/scene/node/node.h"

namespace ballistica {

class TerrainNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit TerrainNode(Scene* scene);
  ~TerrainNode() override;
  void Draw(FrameDef* frame_def) override;
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
  auto model() const -> Model* { return model_.get(); }
  void SetModel(Model* m);
  auto color_texture() const -> Texture* { return color_texture_.get(); }
  void SetColorTexture(Texture* val);
  auto collide_model() const -> CollideModel* { return collide_model_.get(); }
  void SetCollideModel(CollideModel* val);
  auto GetMaterials() const -> std::vector<Material*>;
  void SetMaterials(const std::vector<Material*>& vals);
  auto vr_only() const -> bool { return vr_only_; }
  void set_vr_only(bool val) { vr_only_ = val; }

 private:
  void AddToBGDynamics();
  void RemoveFromBGDynamics();
  CollideModel* bg_dynamics_collide_model_;
  bool vr_only_;
  bool bumper_;
  bool affect_bg_dynamics_;
  bool lighting_;
  bool background_;
  bool overlay_;
  float opacity_;
  float opacity_in_low_or_medium_quality_;
  Object::Ref<Model> model_;
  Object::Ref<CollideModel> collide_model_;
  Object::Ref<Texture> color_texture_;
  std::vector<Object::Ref<Material> > materials_;
  Part terrain_part_;
  Object::Ref<RigidBody> body_;
  bool visible_in_reflections_;
  ReflectionType reflection_;
  std::vector<float> reflection_scale_;
  float reflection_scale_r_, reflection_scale_g_, reflection_scale_b_;
  std::vector<float> color_;
  float color_r_, color_g_, color_b_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_TERRAIN_NODE_H_
