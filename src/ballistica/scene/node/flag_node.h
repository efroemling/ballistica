// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_FLAG_NODE_H_
#define BALLISTICA_SCENE_NODE_FLAG_NODE_H_

#include <vector>

#include "ballistica/dynamics/part.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/scene/node/node.h"

namespace ballistica {

class FlagNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit FlagNode(Scene* scene);
  ~FlagNode() override;
  void HandleMessage(const char* data) override;
  void Draw(FrameDef* frame_def) override;
  void Step() override;
  auto GetRigidBody(int id) -> RigidBody* override;
  auto is_area_of_interest() const -> bool {
    return (area_of_interest_ != nullptr);
  }
  void SetIsAreaOfInterest(bool val);
  auto getPosition() const -> std::vector<float>;
  void SetPosition(const std::vector<float>& vals);
  auto color_texture() const -> Texture* { return color_texture_.get(); }
  void set_color_texture(Texture* val) { color_texture_ = val; }
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
  void OnGraphicsQualityChanged(GraphicsQuality q) override;
  void UpdateForGraphicsQuality(GraphicsQuality q);
  void UpdateSpringPoint(int p1, int p2, float rest_length);
  AreaOfInterest* area_of_interest_ = nullptr;
  Part part_;
  std::vector<float> color_ = {1.0f, 1.0f, 1.0f};
  Object::Ref<RigidBody> body_{nullptr};
  Object::Ref<Texture> color_texture_;
  MeshIndexedObjectSplit mesh_;
#if !BA_HEADLESS_BUILD
  Object::Ref<FullShadowSet> full_shadow_set_;
  Object::Ref<SimpleShadowSet> simple_shadow_set_;
#endif  // !BA_HEADLESS_BUILD
  int wind_rand_{};
  float wind_rand_x_{};
  float wind_rand_y_{};
  float wind_rand_z_{};
  float flag_impulse_add_x_{};
  float flag_impulse_add_y_{};
  float flag_impulse_add_z_{};
  bool have_flag_impulse_{};
  int footing_{};
  bool light_weight_{};
  Vector3f flag_points_[25]{};
  Vector3f flag_normals_[25]{};
  Vector3f flag_velocities_[25]{};
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_FLAG_NODE_H_
