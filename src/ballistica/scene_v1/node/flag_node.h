// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_FLAG_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_FLAG_NODE_H_

#include <vector>

#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class FlagNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit FlagNode(Scene* scene);
  ~FlagNode() override;
  void HandleMessage(const char* data) override;
  void Draw(base::FrameDef* frame_def) override;
  void Step() override;
  auto GetRigidBody(int id) -> RigidBody* override;
  auto is_area_of_interest() const -> bool {
    return (area_of_interest_ != nullptr);
  }
  void SetIsAreaOfInterest(bool val);
  auto getPosition() const -> std::vector<float>;
  void SetPosition(const std::vector<float>& vals);
  auto color_texture() const -> SceneTexture* { return color_texture_.Get(); }
  void set_color_texture(SceneTexture* val) { color_texture_ = val; }
  auto light_weight() const -> bool { return light_weight_; }
  void SetLightWeight(bool val);
  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& vals);
  auto GetMaterials() const -> std::vector<Material*>;
  void SetMaterials(const std::vector<Material*>& materials);

 private:
  class FullShadowSet;
  class SimpleShadowSet;
  void UpdateAreaOfInterest();
  void GetRigidBodyPickupLocations(int id, float* obj, float* character,
                                   float* hand1, float* hand2) override;
  void UpdateDimensions();
  void ResetFlagMesh();
  void UpdateFlagMesh();
  void UpdateForGraphicsQuality(base::GraphicsQuality q);
  void UpdateSpringPoint(int p1, int p2, float rest_length);

  base::GraphicsQuality graphics_quality_{};
  bool light_weight_{};
  bool have_flag_impulse_{};
  base::AreaOfInterest* area_of_interest_{};
  Part part_;
  std::vector<float> color_ = {1.0f, 1.0f, 1.0f};
  Object::Ref<RigidBody> body_;
  Object::Ref<SceneTexture> color_texture_;
  base::MeshIndexedObjectSplit mesh_;
  Object::Ref<FullShadowSet> full_shadow_set_;
  Object::Ref<SimpleShadowSet> simple_shadow_set_;
  int wind_rand_{};
  int footing_{};
  float wind_rand_x_{};
  float wind_rand_y_{};
  float wind_rand_z_{};
  float flag_impulse_add_x_{};
  float flag_impulse_add_y_{};
  float flag_impulse_add_z_{};
  Vector3f flag_points_[25]{};
  Vector3f flag_normals_[25]{};
  Vector3f flag_velocities_[25]{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_FLAG_NODE_H_
