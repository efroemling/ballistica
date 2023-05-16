// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_TEXTURE_SEQUENCE_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_TEXTURE_SEQUENCE_NODE_H_

#include <vector>

#include "ballistica/scene_v1/node/node.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::scene_v1 {

class TextureSequenceNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit TextureSequenceNode(Scene* scene);
  void Step() override;
  auto rate() const -> int { return rate_; }
  void set_rate(int val);
  auto input_textures() const -> std::vector<SceneTexture*>;
  void set_input_textures(const std::vector<SceneTexture*>& vals);
  auto output_texture() const -> SceneTexture*;

 private:
  int sleep_count_{};
  int index_{};
  int rate_{};
  std::vector<Object::Ref<SceneTexture> > input_textures_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_TEXTURE_SEQUENCE_NODE_H_
