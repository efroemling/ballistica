// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_FLASH_NODE_H_
#define BALLISTICA_SCENE_NODE_FLASH_NODE_H_

#include <vector>

#include "ballistica/scene/node/node.h"

namespace ballistica {

class FlashNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit FlashNode(Scene* scene);
  ~FlashNode() override;
  void Draw(FrameDef* frame_def) override;
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& vals);
  auto size() const -> float { return size_; }
  void set_size(float val) { size_ = val; }
  auto color() const -> std::vector<float> { return color_; }
  void set_color(const std::vector<float>& vals) { color_ = vals; }

 private:
  std::vector<float> position_ = {0.0f, 0.0f, 0.0f};
  float size_ = 1.0f;
  std::vector<float> color_ = {0.5f, 0.5f, 0.5f};
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_FLASH_NODE_H_
