// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/python_call_material_action.h"

#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

PythonCallMaterialAction::PythonCallMaterialAction(bool at_disconnect_in,
                                                   PyObject* call_obj_in)
    : at_disconnect(at_disconnect_in),
      call(Object::New<base::PythonContextCall>(call_obj_in)) {}

void PythonCallMaterialAction::Apply(MaterialContext* context,
                                     const Part* src_part, const Part* dst_part,
                                     const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  if (at_disconnect) {
    context->disconnect_actions.push_back(p);
  } else {
    context->connect_actions.push_back(p);
  }
}

void PythonCallMaterialAction::Execute(Node* node1, Node* node2, Scene* scene) {
  scene->dynamics()->set_collide_message_state(true, false);

  // Only run connect commands if both nodes still exist.
  // This way most collision commands can assume both
  // members of the collision exist.
  if (!at_disconnect) {
    if (node1 && node2) {
      call->Run();
    }
  } else {
    // Its a disconnect. Run it if the src node still exists
    // (nodes should know if they've disconnected from others even if
    // it was through death)
    if (node1) {
      call->Run();
    }
  }
  scene->dynamics()->set_collide_message_state(false);
}

}  // namespace ballistica::scene_v1
