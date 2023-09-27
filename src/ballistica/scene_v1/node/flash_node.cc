// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/flash_node.h"

#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::scene_v1 {

class FlashNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS FlashNode
  BA_NODE_CREATE_CALL(CreateFlash);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ATTR(size, size, set_size);
  BA_FLOAT_ARRAY_ATTR(color, color, set_color);
#undef BA_NODE_TYPE_CLASS

  FlashNodeType()
      : NodeType("flash", CreateFlash),
        position(this),
        size(this),
        color(this) {}
};
static NodeType* node_type{};

auto FlashNode::InitType() -> NodeType* {
  node_type = new FlashNodeType();
  return node_type;
}

FlashNode::FlashNode(Scene* scene) : Node(scene, node_type) {}

FlashNode::~FlashNode() = default;

void FlashNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
}

void FlashNode::Draw(base::FrameDef* frame_def) {
  base::ObjectComponent c(frame_def->beauty_pass());
  c.SetLightShadow(base::LightShadowType::kNone);
  c.SetColor(color_[0], color_[1], color_[2], 1.0f);
  {
    auto xf = c.ScopedTransform();
    c.Translate(position_[0], position_[1], position_[2]);
    c.Scale(size_, size_, size_);
    c.Rotate(RandomFloat() * 360.0f, 1, 1, 0);
    c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kFlash));
  }
  c.Submit();
}

}  // namespace ballistica::scene_v1
