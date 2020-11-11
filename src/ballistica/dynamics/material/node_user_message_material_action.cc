// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/node_user_message_material_action.h"

#include "ballistica/core/context.h"
#include "ballistica/dynamics/dynamics.h"
#include "ballistica/dynamics/material/material_context.h"
#include "ballistica/media/component/sound.h"
#include "ballistica/scene/node/node.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

NodeUserMessageMaterialAction::NodeUserMessageMaterialAction(
    bool target_other_in, bool at_disconnect_in, PyObject* user_message_obj_in)
    : target_other(target_other_in), at_disconnect(at_disconnect_in) {
  user_message_obj.Acquire(user_message_obj_in);
}

void NodeUserMessageMaterialAction::Apply(
    MaterialContext* context, const Part* src_part, const Part* dst_part,
    const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  if (at_disconnect) {
    context->disconnect_actions.push_back(p);
  } else {
    context->connect_actions.push_back(p);
  }
}

NodeUserMessageMaterialAction::~NodeUserMessageMaterialAction() = default;

void NodeUserMessageMaterialAction::Execute(Node* node1, Node* node2,
                                            Scene* scene) {
  // See who they want to send the message to.
  Node* target_node = target_other ? node2 : node1;

  if (!at_disconnect) {
    // Only deliver 'connect' messages if both nodes still exist.
    // This way handlers can avoid having to deal with that ultra-rare
    // corner case.
    if (!node1 || !node2) {
      return;
    }
  } else {
    // Deliver 'disconnect' messages if the target node still exists
    // even if the opposing one doesn't. Nodes should always know when
    // they stop colliding even if it was through death.
    if (!target_node) {
      return;
    }
  }

  ScopedSetContext cp(target_node->context());
  scene->dynamics()->set_collide_message_state(true, target_other);
  target_node->DispatchUserMessage(user_message_obj.get(),
                                   "Material User-Message dispatch");
  scene->dynamics()->set_collide_message_state(false);
}

}  // namespace ballistica
