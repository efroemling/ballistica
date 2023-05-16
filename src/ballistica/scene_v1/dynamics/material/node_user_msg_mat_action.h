// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_NODE_USER_MSG_MAT_ACTION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_NODE_USER_MSG_MAT_ACTION_H_

#include "ballistica/scene_v1/dynamics/material/material_action.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

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

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_NODE_USER_MSG_MAT_ACTION_H_
