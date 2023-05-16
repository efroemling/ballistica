// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_BOMB_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_BOMB_NODE_H_

#include "ballistica/base/dynamics/bg/bg_dynamics_fuse.h"
#include "ballistica/scene_v1/node/prop_node.h"

namespace ballistica::scene_v1 {

class BombNode : public PropNode {
 public:
  static auto InitType() -> NodeType*;
  explicit BombNode(Scene* scene);
  void Step() override;
  void Draw(base::FrameDef* frame_def) override;
  void OnCreate() override;
  auto fuse_length() const -> float { return fuse_length_; }
  void set_fuse_length(float val) { fuse_length_ = val; }

 protected:
#if !BA_HEADLESS_BUILD
  base::BGDynamicsFuse fuse_;
#endif
  float fuse_length_ = 1.0f;
  Vector3f light_translate_ = {0.0f, 0.0f, 0.0f};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_BOMB_NODE_H_
