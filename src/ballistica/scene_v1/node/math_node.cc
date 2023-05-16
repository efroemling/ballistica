// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/math_node.h"

#include <cmath>

#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class MathNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS MathNode
  BA_NODE_CREATE_CALL(CreateMath);
  BA_FLOAT_ARRAY_ATTR_READONLY(output, GetOutput);
  BA_FLOAT_ARRAY_ATTR(input1, input_1, set_input_1);
  BA_FLOAT_ARRAY_ATTR(input2, input_2, set_input_2);
  BA_STRING_ATTR(operation, GetOperation, SetOperation);
#undef BA_NODE_TYPE_CLASS

  MathNodeType()
      : NodeType("math", CreateMath),
        output(this),
        input1(this),
        input2(this),
        operation(this) {}
};

static NodeType* node_type{};

auto MathNode::InitType() -> NodeType* {
  node_type = new MathNodeType();
  return node_type;
}

MathNode::MathNode(Scene* scene) : Node(scene, node_type) {}

auto MathNode::GetOperation() const -> std::string {
  switch (operation_) {
    case Operation::kAdd:
      return "add";
    case Operation::kSubtract:
      return "subtract";
    case Operation::kMultiply:
      return "multiply";
    case Operation::kDivide:
      return "divide";
    case Operation::kSin:
      return "sin";
  }

    // This should be unreachable, but most compilers complain about
    // control reaching the end of non-void function without it.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
  throw Exception();
#pragma clang diagnostic pop
}

void MathNode::SetOperation(const std::string& val) {
  if (val == "add") {
    operation_ = Operation::kAdd;
  } else if (val == "subtract") {
    operation_ = Operation::kSubtract;
  } else if (val == "multiply") {
    operation_ = Operation::kMultiply;
  } else if (val == "divide") {
    operation_ = Operation::kDivide;
  } else if (val == "sin") {
    operation_ = Operation::kSin;
  } else {
    throw Exception("Invalid math node op '" + val + "'");
  }
}

auto MathNode::GetOutput() -> std::vector<float> {
  size_t val_count = std::min(input_1_.size(), input_2_.size());
  std::vector<float> outputs(val_count);
  switch (operation_) {
    case Operation::kAdd: {
      for (size_t i = 0; i < val_count; i++) {
        outputs[i] = (input_1_[i] + input_2_[i]);
      }
      break;
    }
    case Operation::kSubtract: {
      for (size_t i = 0; i < val_count; i++) {
        outputs[i] = (input_1_[i] - input_2_[i]);
      }
      break;
    }
    case Operation::kMultiply: {
      for (size_t i = 0; i < val_count; i++) {
        outputs[i] = (input_1_[i] * input_2_[i]);
      }
      break;
    }
    case Operation::kDivide: {
      for (size_t i = 0; i < val_count; i++) {
        outputs[i] = (input_1_[i] / input_2_[i]);
      }
      break;
    }
    case Operation::kSin: {
      for (size_t i = 0; i < val_count; i++) {
        outputs[i] = (sinf(input_1_[i]));
      }
      break;
    }
  }
  return outputs;
}

}  // namespace ballistica::scene_v1
