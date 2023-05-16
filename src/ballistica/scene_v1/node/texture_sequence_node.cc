// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/texture_sequence_node.h"

#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class TextureSequenceNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS TextureSequenceNode
  BA_NODE_CREATE_CALL(CreateTextureSequence);
  BA_INT_ATTR(rate, rate, set_rate);
  BA_TEXTURE_ARRAY_ATTR(input_textures, input_textures, set_input_textures);
  BA_TEXTURE_ATTR_READONLY(output_texture, output_texture);
#undef BA_NODE_TYPE_CLASS

  TextureSequenceNodeType()
      : NodeType("texture_sequence", CreateTextureSequence),
        rate(this),
        input_textures(this),
        output_texture(this) {}
};
static NodeType* node_type{};

auto TextureSequenceNode::InitType() -> NodeType* {
  node_type = new TextureSequenceNodeType();
  return node_type;
}

TextureSequenceNode::TextureSequenceNode(Scene* scene)
    : Node(scene, node_type), index_(0), rate_(1000), sleep_count_(0) {}

auto TextureSequenceNode::input_textures() const -> std::vector<SceneTexture*> {
  return RefsToPointers(input_textures_);
}

void TextureSequenceNode::set_input_textures(
    const std::vector<SceneTexture*>& vals) {
  input_textures_ = PointersToRefs(vals);

  // Make sure index_ doesnt go out of range.
  if (!input_textures_.empty()) {
    index_ = index_ % static_cast<int>(input_textures_.size());
  }
}

auto TextureSequenceNode::output_texture() const -> SceneTexture* {
  if (input_textures_.empty()) {
    return nullptr;
  }
  assert(index_ < static_cast<int>(input_textures_.size()));
  return input_textures_[index_].Get();
}

void TextureSequenceNode::Step() {
  if (sleep_count_ <= 0) {
    if (!input_textures_.empty()) {
      index_ = (index_ + 1) % static_cast<int>(input_textures_.size());
    }
    sleep_count_ = rate_;
  }
  sleep_count_ -= kGameStepMilliseconds;
}

void TextureSequenceNode::set_rate(int val) {
  if (val != rate_) {
    rate_ = val;
    sleep_count_ = val;
  }
}

}  // namespace ballistica::scene_v1
