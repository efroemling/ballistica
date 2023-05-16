// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_SCORCH_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_SCORCH_NODE_H_

#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class ScorchNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit ScorchNode(Scene* scene);
  ~ScorchNode() override;
  void Draw(base::FrameDef* frame_def) override;
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& vals);
  auto presence() const -> float { return presence_; }
  void set_presence(float val) { presence_ = val; }
  auto size() const -> float { return size_; }
  void set_size(float val) { size_ = val; }
  auto big() const -> bool { return big_; }
  void set_big(bool val) { big_ = val; }
  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& vals);

 private:
  std::vector<float> position_{0.0f, 0.0f, 0.0f};
  std::vector<float> color_{0.07f, 0.03f, 0.0f};
  float presence_{1.0f};
  float size_{1.0f};
  bool big_{};
  float rand_size_[3]{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_SCORCH_NODE_H_
