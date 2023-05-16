// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/null_node.h"

#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

// nothing to see here folks... move along
class NullNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS NullNode
  BA_NODE_CREATE_CALL(CreateNull);
#undef BA_NODE_TYPE_CLASS

  NullNodeType() : NodeType("null", CreateNull) {}
};

static NodeType* node_type{};

auto NullNode::InitType() -> NodeType* {
  node_type = new NullNodeType();
  return node_type;
}

NullNode::NullNode(Scene* scene) : Node(scene, node_type) {}

}  // namespace ballistica::scene_v1
