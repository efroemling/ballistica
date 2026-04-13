// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/region_node.h"

#include <string>
#include <vector>

#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ode/ode_collision.h"

namespace ballistica::scene_v1 {

class RegionNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS RegionNode
  BA_NODE_CREATE_CALL(CreateRegion);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ARRAY_ATTR(scale, scale, SetScale);
  BA_MATERIAL_ARRAY_ATTR(materials, GetMaterials, SetMaterials);
  BA_STRING_ATTR(type, region_type, SetRegionType);
#undef BA_NODE_TYPE_CLASS

  RegionNodeType()
      : NodeType("region", CreateRegion),
        position(this),
        scale(this),
        materials(this),
        type(this) {}
};

static NodeType* node_type{};

auto RegionNode::InitType() -> NodeType* {
  node_type = new RegionNodeType();
  return node_type;
}

RegionNode::RegionNode(Scene* scene)
    : Node(scene, node_type), part_(this, false) {}

void RegionNode::Draw(base::FrameDef* frame_def) {
  if (g_base->graphics_server->renderer()->debug_draw_mode()) {
    // if (frame_def->renderer()->debug_draw_mode()) {
    if (body_.exists()) {
      body_->Draw(frame_def->beauty_pass(), false);
    }
  }
}

void RegionNode::SetRegionType(const std::string& val) {
  if (val == region_type_) {
    return;
  }
  region_type_ = val;
  body_.Clear();  // will be recreated next step
}

auto RegionNode::GetMaterials() const -> std::vector<Material*> {
  return part_.GetMaterials();
}

void RegionNode::SetMaterials(const std::vector<Material*>& vals) {
  part_.SetMaterials(vals);
}

void RegionNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
  size_or_pos_dirty_ = true;
}

void RegionNode::SetScale(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for scale",
                    PyExcType::kValue);
  }
  scale_ = vals;
  size_or_pos_dirty_ = true;
}

void RegionNode::Step() {
  // create our body if we have none
  if (!body_.exists()) {
    if (region_type_ == "sphere") {
      body_ = Object::New<RigidBody>(
          0, &part_, RigidBody::Type::kGeomOnly, RigidBody::Shape::kSphere,
          RigidBody::kCollideRegion, RigidBody::kCollideActive);
    } else {
      if (region_type_ != "box") {
        BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                    "Got unexpected region type: " + region_type_);
      }
      body_ = Object::New<RigidBody>(
          0, &part_, RigidBody::Type::kGeomOnly, RigidBody::Shape::kBox,
          RigidBody::kCollideRegion, RigidBody::kCollideActive);
    }
    size_or_pos_dirty_ = true;  // always needs updating after create
  }
  if (size_or_pos_dirty_) {
    dGeomSetPosition(body_->geom(), position_[0], position_[1], position_[2]);
    body_->SetDimensions(scale_[0], scale_[1], scale_[2]);
    size_or_pos_dirty_ = false;
  }
}

}  // namespace ballistica::scene_v1
