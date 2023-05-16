// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/node_message_material_action.h"

#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

NodeMessageMaterialAction::NodeMessageMaterialAction(bool target_other_in,
                                                     bool at_disconnect_in,
                                                     const char* data_in,
                                                     size_t length_in)
    : target_other(target_other_in),
      at_disconnect(at_disconnect_in),
      data(data_in, length_in) {
  assert(length_in > 0);
}

void NodeMessageMaterialAction::Apply(MaterialContext* context,
                                      const Part* src_part,
                                      const Part* dst_part,
                                      const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  if (at_disconnect) {
    context->disconnect_actions.push_back(p);
  } else {
    context->connect_actions.push_back(p);
  }
}

void NodeMessageMaterialAction::Execute(Node* node1, Node* node2,
                                        Scene* scene) {
  Node* node = target_other ? node2 : node1;
  if (node) {
    scene->dynamics()->set_collide_message_state(true, target_other);
    assert(node);
    assert(data.data());
    node->DispatchNodeMessage(data.data());
    scene->dynamics()->set_collide_message_state(false);
  }
}

}  // namespace ballistica::scene_v1
