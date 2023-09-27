// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/scorch_node.h"

#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::scene_v1 {

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
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;
}

void ScorchNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
}

void ScorchNode::Draw(base::FrameDef* frame_def) {
  float o = presence_;
  // modulate opacity by local shadow density
  o *= g_base->graphics->GetShadowDensity(position_[0], position_[1],
                                          position_[2]);
  base::SimpleComponent c(frame_def->light_shadow_pass());
  c.SetTransparent(true);
  c.SetColor(color_[0], color_[1], color_[2], o * 0.35f);
  c.SetTexture(g_base->assets->SysTexture(big_ ? base::SysTextureID::kScorchBig
                                               : base::SysTextureID::kScorch));
  {
    auto xf = c.ScopedTransform();
    c.Translate(position_[0], position_[1], position_[2]);
    c.Scale(o * size_ * rand_size_[0], o * size_ * rand_size_[1],
            o * size_ * rand_size_[2]);
    c.Rotate(Utils::precalc_rand_1(id() % kPrecalcRandsCount) * 360.0f, 0, 1,
             0);
    c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kScorch));
  }
  c.Submit();
}

}  // namespace ballistica::scene_v1
