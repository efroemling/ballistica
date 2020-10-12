// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_NODE_USER_MESSAGE_MATERIAL_ACTION_H_
#define BALLISTICA_DYNAMICS_MATERIAL_NODE_USER_MESSAGE_MATERIAL_ACTION_H_

#include "ballistica/ballistica.h"
#include "ballistica/dynamics/material/material_action.h"
#include "ballistica/python/python_ref.h"

namespace ballistica {

// a user message - encapsulates a python object
class NodeUserMessageMaterialAction : public MaterialAction {
 public:
  NodeUserMessageMaterialAction(bool target_other, bool at_disconnect,
                                PyObject* user_message);
  ~NodeUserMessageMaterialAction() override;
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  void Execute(Node* node1, Node* node2, Scene* scene) override;
  bool target_other;
  bool at_disconnect;
  PythonRef user_message_obj;
  auto GetType() const -> Type override { return Type::NODE_USER_MESSAGE; }
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_NODE_USER_MESSAGE_MATERIAL_ACTION_H_
