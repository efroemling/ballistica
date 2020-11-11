// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_REGION_NODE_H_
#define BALLISTICA_SCENE_NODE_REGION_NODE_H_

#include <string>
#include <vector>

#include "ballistica/dynamics/part.h"
#include "ballistica/scene/node/node.h"

namespace ballistica {

// A region node - used to detect if an object is in a certain area
class RegionNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit RegionNode(Scene* scene);
  void Draw(FrameDef* frame_def) override;
  void Step() override;
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& vals);
  auto scale() const -> std::vector<float> { return scale_; }
  void SetScale(const std::vector<float>& vals);
  auto GetMaterials() const -> std::vector<Material*>;
  void SetMaterials(const std::vector<Material*>& vals);
  auto region_type() const -> std::string { return region_type_; }
  void SetRegionType(const std::string& val);

 private:
  bool size_or_pos_dirty_ = true;
  Part part_;
  std::vector<float> position_ = {0.0f, 0.0f, 0.0f};
  std::vector<float> scale_ = {1.0f, 1.0f, 1.0f};
  std::string region_type_ = "box";
  Object::Ref<RigidBody> body_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_REGION_NODE_H_
