// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_TEXTURE_SEQUENCE_NODE_H_
#define BALLISTICA_SCENE_NODE_TEXTURE_SEQUENCE_NODE_H_

#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/scene/node/node.h"

namespace ballistica {

class TextureSequenceNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit TextureSequenceNode(Scene* scene);
  void Step() override;
  auto rate() const -> int { return rate_; }
  void set_rate(int val);
  auto input_textures() const -> std::vector<Texture*>;
  void set_input_textures(const std::vector<Texture*>& vals);
  auto output_texture() const -> Texture*;

 private:
  int sleep_count_{};
  int index_{};
  int rate_{};
  std::vector<Object::Ref<Texture> > input_textures_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_TEXTURE_SEQUENCE_NODE_H_
