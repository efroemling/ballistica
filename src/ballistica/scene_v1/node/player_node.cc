// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/player_node.h"

#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

class PlayerNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS PlayerNode
  BA_NODE_CREATE_CALL(CreatePlayer);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_INT_ATTR(playerID, player_id, SetPlayerID);
#undef BA_NODE_TYPE_CLASS
  PlayerNodeType()
      : NodeType("player", CreatePlayer), position(this), playerID(this) {}
};

static NodeType* node_type{};

auto PlayerNode::InitType() -> NodeType* {
  node_type = new PlayerNodeType();
  return node_type;
}

PlayerNode::PlayerNode(Scene* scene) : Node(scene, node_type) {}

PlayerNode::~PlayerNode() = default;

void PlayerNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
}

void PlayerNode::SetPlayerID(int val) {
  player_id_ = val;
  // once this is set we also inform the scene of our existence..
  scene()->SetPlayerNode(player_id_, this);
}

}  // namespace ballistica::scene_v1
