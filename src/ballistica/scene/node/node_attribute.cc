// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene/node/node_attribute.h"

#include "ballistica/scene/node/node.h"
#include "ballistica/scene/node/node_attribute_connection.h"
#include "ballistica/scene/node/node_type.h"

namespace ballistica {

auto NodeAttributeUnbound::GetNodeAttributeTypeName(NodeAttributeType t)
    -> std::string {
  switch (t) {
    case NodeAttributeType::kFloat:
      return "float";
    case NodeAttributeType::kFloatArray:
      return "float-array";
    case NodeAttributeType::kInt:
      return "int";
    case NodeAttributeType::kIntArray:
      return "int-array";
    case NodeAttributeType::kBool:
      return "bool";
    case NodeAttributeType::kString:
      return "string";
    case NodeAttributeType::kNode:
      return "node";
    case NodeAttributeType::kNodeArray:
      return "node-array";
    case NodeAttributeType::kPlayer:
      return "player";
    case NodeAttributeType::kMaterialArray:
      return "material-array";
    case NodeAttributeType::kTexture:
      return "texture";
    case NodeAttributeType::kTextureArray:
      return "texture-array";
    case NodeAttributeType::kSound:
      return "sound";
    case NodeAttributeType::kSoundArray:
      return "sound-array";
    case NodeAttributeType::kModel:
      return "model";
    case NodeAttributeType::kModelArray:
      return "model-array";
    case NodeAttributeType::kCollideModel:
      return "collide-model";
    case NodeAttributeType::kCollideModelArray:
      return "collide-model-array";
    default:
      Log("Error: Unknown attr type name: "
          + std::to_string(static_cast<int>(t)));
      return "unknown";
  }
}

NodeAttributeUnbound::NodeAttributeUnbound(NodeType* node_type,
                                           NodeAttributeType type,
                                           std::string name, uint32_t flags)
    : node_type_(node_type),
      type_(type),
      name_(std::move(name)),
      flags_(flags) {
  assert(node_type);
  node_type->attributes_by_name_[name_] = this;
  index_ = static_cast<int>(node_type->attributes_by_index_.size());
  node_type->attributes_by_index_.push_back(this);
}

void NodeAttributeUnbound::NotReadableError(Node* node) {
  throw Exception("Attribute '" + name() + "' on " + node->type()->name()
                  + " node is not readable");
}

void NodeAttributeUnbound::NotWritableError(Node* node) {
  throw Exception("Attribute '" + name() + "' on " + node->type()->name()
                  + " node is not writable");
}

void NodeAttributeUnbound::DisconnectIncoming(Node* node) {
  assert(node);
  auto i = node->attribute_connections_incoming().find(index());
  if (i != node->attribute_connections_incoming().end()) {
    NodeAttributeConnection* a = i->second.get();

#if BA_DEBUG_BUILD
    Object::WeakRef<NodeAttributeConnection> test_ref(a);
#endif

    assert(a != nullptr);
    assert(a->src_node.exists());

    // Remove from src node's outgoing list.
    a->src_node->attribute_connections_.erase(a->src_iterator);

    // Remove from our incoming list; this should kill the connection.
    node->attribute_connections_incoming_.erase(i);

#if BA_DEBUG_BUILD
    if (test_ref.exists()) {
      Log("Error: Attr connection still exists after ref releases!");
    }
#endif
  }
}

auto NodeAttributeUnbound::GetAsFloat(Node* node) -> float {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a float.");
}
void NodeAttributeUnbound::Set(Node* node, float value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a float.");
}
auto NodeAttributeUnbound::GetAsInt(Node* node) -> int64_t {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as an int.");
}
void NodeAttributeUnbound::Set(Node* node, int64_t value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as an int.");
}
auto NodeAttributeUnbound::GetAsBool(Node* node) -> bool {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a bool.");
}
void NodeAttributeUnbound::Set(Node* node, bool value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a bool.");
}
auto NodeAttributeUnbound::GetAsString(Node* node) -> std::string {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a string.");
}
void NodeAttributeUnbound::Set(Node* node, const std::string& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a string.");
}

auto NodeAttributeUnbound::GetAsFloats(Node* node) -> std::vector<float> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a float array.");
}
void NodeAttributeUnbound::Set(Node* node, const std::vector<float>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a float array.");
}
auto NodeAttributeUnbound::GetAsInts(Node* node) -> std::vector<int64_t> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as an int array.");
}
void NodeAttributeUnbound::Set(Node* node, const std::vector<int64_t>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as an int array.");
}

auto NodeAttributeUnbound::GetAsNode(Node* node) -> Node* {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a node.");
}
void NodeAttributeUnbound::Set(Node* node, Node* value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a node.");
}

auto NodeAttributeUnbound::GetAsNodes(Node* node) -> std::vector<Node*> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a node array.");
}
void NodeAttributeUnbound::Set(Node* node, const std::vector<Node*>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a node array.");
}

auto NodeAttributeUnbound::GetAsPlayer(Node* node) -> Player* {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a player.");
}
void NodeAttributeUnbound::Set(Node* node, Player* value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a player.");
}

auto NodeAttributeUnbound::GetAsMaterials(Node* node)
    -> std::vector<Material*> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a material array.");
}
void NodeAttributeUnbound::Set(Node* node,
                               const std::vector<Material*>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a material array.");
}

auto NodeAttributeUnbound::GetAsTexture(Node* node) -> Texture* {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a texture.");
}
void NodeAttributeUnbound::Set(Node* node, Texture* value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a texture.");
}

auto NodeAttributeUnbound::GetAsTextures(Node* node) -> std::vector<Texture*> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a texture array.");
}
void NodeAttributeUnbound::Set(Node* node, const std::vector<Texture*>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a texture array.");
}

auto NodeAttributeUnbound::GetAsSound(Node* node) -> Sound* {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a sound.");
}
void NodeAttributeUnbound::Set(Node* node, Sound* value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a sound.");
}

auto NodeAttributeUnbound::GetAsSounds(Node* node) -> std::vector<Sound*> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a sound array.");
}
void NodeAttributeUnbound::Set(Node* node, const std::vector<Sound*>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a sound array.");
}

auto NodeAttributeUnbound::GetAsModel(Node* node) -> Model* {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a model.");
}
void NodeAttributeUnbound::Set(Node* node, Model* value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a model.");
}

auto NodeAttributeUnbound::GetAsModels(Node* node) -> std::vector<Model*> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a model array.");
}
void NodeAttributeUnbound::Set(Node* node, const std::vector<Model*>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a model array.");
}

auto NodeAttributeUnbound::GetAsCollideModel(Node* node) -> CollideModel* {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a collide-model.");
}
void NodeAttributeUnbound::Set(Node* node, CollideModel* value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a collide-model.");
}

auto NodeAttributeUnbound::GetAsCollideModels(Node* node)
    -> std::vector<CollideModel*> {
  throw Exception("Can't get attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a collide-model array.");
}
void NodeAttributeUnbound::Set(Node* node,
                               const std::vector<CollideModel*>& value) {
  throw Exception("Can't set attr '" + name() + "' on node type '"
                  + node_type()->name() + "' as a collide-model array.");
}

}  // namespace ballistica
