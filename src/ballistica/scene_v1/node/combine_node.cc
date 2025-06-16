// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/combine_node.h"

#include <algorithm>
#include <vector>

#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class CombineNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS CombineNode
  BA_NODE_CREATE_CALL(CreateLocator);
  BA_FLOAT_ATTR(input0, input_0, set_input_0);
  BA_FLOAT_ATTR(input1, input_1, set_input_1);
  BA_FLOAT_ATTR(input2, input_2, set_input_2);
  BA_FLOAT_ATTR(input3, input_3, set_input_3);
  BA_FLOAT_ARRAY_ATTR_READONLY(output, GetOutput);
  BA_INT_ATTR(size, size, set_size);
#undef BA_NODE_TYPE_CLASS
  CombineNodeType()
      : NodeType("combine", CreateLocator),
        input0(this),
        input1(this),
        input2(this),
        input3(this),
        output(this),
        size(this) {}
};

static NodeType* node_type{};

auto CombineNode::InitType() -> NodeType* {
  node_type = new CombineNodeType();
  return node_type;
}

CombineNode::CombineNode(Scene* scene) : Node(scene, node_type) {}

auto CombineNode::GetOutput() -> std::vector<float> {
  if (dirty_) {
    if (do_size_unset_warning_) {
      do_size_unset_warning_ = false;
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "CombineNode size unset for " + label());
    }
    int actual_size = std::min(4, std::max(0, size_));
    output_.resize(static_cast<size_t>(actual_size));
    if (size_ > 0) {
      output_[0] = input_0_;
    }
    if (size_ > 1) {
      output_[1] = input_1_;
    }
    if (size_ > 2) {
      output_[2] = input_2_;
    }
    if (size_ > 3) {
      output_[3] = input_3_;
    }
    dirty_ = false;
  }
  return output_;
}

}  // namespace ballistica::scene_v1
