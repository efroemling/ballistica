// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/session_globals_node.h"

#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

class SessionGlobalsNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS SessionGlobalsNode
  BA_NODE_CREATE_CALL(CreateSessionGlobals);
  BA_INT64_ATTR_READONLY(real_time, AppTimeMillisecs);
  BA_INT64_ATTR_READONLY(time, GetTime);
  BA_INT64_ATTR_READONLY(step, GetStep);
#undef BA_NODE_TYPE_CLASS
  SessionGlobalsNodeType()
      : NodeType("sessionglobals", CreateSessionGlobals),
        real_time(this),
        time(this),
        step(this) {}
};

static NodeType* node_type{};

auto SessionGlobalsNode::InitType() -> NodeType* {
  node_type = new SessionGlobalsNodeType();
  return node_type;
}

SessionGlobalsNode::SessionGlobalsNode(Scene* scene) : Node(scene, node_type) {
  // We don't expose this as an attr, but we tell our scene to display stuff in
  // the fixed overlay position by default when doing vr.
  this->scene()->set_use_fixed_vr_overlay(true);
}

SessionGlobalsNode::~SessionGlobalsNode() = default;

auto SessionGlobalsNode::AppTimeMillisecs() -> millisecs_t {
  // Pull this from our scene so we return consistent values throughout a step.
  return scene()->last_step_real_time();
}

auto SessionGlobalsNode::GetTime() -> millisecs_t { return scene()->time(); }

auto SessionGlobalsNode::GetStep() -> int64_t { return scene()->stepnum(); }

}  // namespace ballistica::scene_v1
