// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_MATH_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_MATH_NODE_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

// An node used to create simple mathematical relationships via
// attribute connections
class MathNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit MathNode(Scene* scene);
  auto GetOutput() -> std::vector<float>;
  auto input_1() const -> const std::vector<float>& { return input_1_; }
  void set_input_1(const std::vector<float>& vals) { input_1_ = vals; }
  auto input_2() const -> std::vector<float> { return input_2_; }
  void set_input_2(const std::vector<float>& vals) { input_2_ = vals; }
  auto GetOperation() const -> std::string;
  void SetOperation(const std::string& val);

 private:
  enum class Operation { kAdd, kSubtract, kMultiply, kDivide, kSin };
  std::vector<float> input_1_;
  std::vector<float> input_2_;
  Operation operation_ = Operation::kAdd;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_MATH_NODE_H_
