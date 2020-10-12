// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene/node/scorch_node.h"

#include <vector>

#include "ballistica/generic/utils.h"
#include "ballistica/graphics/component/simple_component.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/scene/node/node_type.h"

namespace ballistica {

class ScorchNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS ScorchNode
  BA_NODE_CREATE_CALL(CreateScorch);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ATTR(presence, presence, set_presence);
  BA_FLOAT_ATTR(size, size, set_size);
  BA_BOOL_ATTR(big, big, set_big);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
#undef BA_NODE_TYPE_CLASS
  ScorchNodeType()
      : NodeType("scorch", CreateScorch),
        position(this),
        presence(this),
        size(this),
        big(this),
        color(this) {}
};

static NodeType* node_type{};

auto ScorchNode::InitType() -> NodeType* {
  node_type = new ScorchNodeType();
  return node_type;
}

ScorchNode::ScorchNode(Scene* scene) : Node(scene, node_type) {
  rand_size_[0] = 0.7f + RandomFloat() * 0.6f;
  rand_size_[1] = 0.7f + RandomFloat() * 0.6f;
  rand_size_[2] = 0.7f + RandomFloat() * 0.6f;
}

ScorchNode::~ScorchNode() = default;

void ScorchNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3)
    throw Exception("Expected float array of length 3 for color");
  color_ = vals;
}

void ScorchNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3)
    throw Exception("Expected float array of length 3 for position");
  position_ = vals;
}

void ScorchNode::Draw(FrameDef* frame_def) {
  float o = presence_;
  // modulate opacity by local shadow density
  o *= g_graphics->GetShadowDensity(position_[0], position_[1], position_[2]);
  SimpleComponent c(frame_def->light_shadow_pass());
  c.SetTransparent(true);
  c.SetColor(color_[0], color_[1], color_[2], o * 0.35f);
  c.SetTexture(g_media->GetTexture(big_ ? SystemTextureID::kScorchBig
                                        : SystemTextureID::kScorch));
  c.PushTransform();
  c.Translate(position_[0], position_[1], position_[2]);
  c.Scale(o * size_ * rand_size_[0], o * size_ * rand_size_[1],
          o * size_ * rand_size_[2]);
  c.Rotate(Utils::precalc_rands_1[id() % kPrecalcRandsCount] * 360.0f, 0, 1, 0);
  c.DrawModel(g_media->GetModel(SystemModelID::kScorch));
  c.PopTransform();
  c.Submit();
}

}  // namespace ballistica
