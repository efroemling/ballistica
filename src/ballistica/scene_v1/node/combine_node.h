// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_COMBINE_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_COMBINE_NODE_H_

#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

// A node used to combine individual input values into one array output value
class CombineNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit CombineNode(Scene* scene);
  auto size() const -> int { return size_; }
  void set_size(int val) {
    size_ = val;
    dirty_ = true;
    do_size_unset_warning_ = false;
  }
  auto input_0() const -> float { return input_0_; }
  void set_input_0(float val) {
    input_0_ = val;
    dirty_ = true;
  }
  auto input_1() const -> float { return input_1_; }
  void set_input_1(float val) {
    input_1_ = val;
    dirty_ = true;
  }
  auto input_2() const -> float { return input_2_; }
  void set_input_2(float val) {
    input_2_ = val;
    dirty_ = true;
  }
  auto input_3() const -> float { return input_3_; }
  void set_input_3(float val) {
    input_3_ = val;
    dirty_ = true;
  }
  auto GetOutput() -> std::vector<float>;

 private:
  bool do_size_unset_warning_ = true;
  float input_0_ = 0.0f;
  float input_1_ = 0.0f;
  float input_2_ = 0.0f;
  float input_3_ = 0.0f;
  int size_ = 4;
  std::vector<float> output_;
  bool dirty_ = true;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_COMBINE_NODE_H_
