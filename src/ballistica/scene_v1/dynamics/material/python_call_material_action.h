// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_PYTHON_CALL_MATERIAL_ACTION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_PYTHON_CALL_MATERIAL_ACTION_H_

#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/scene_v1/dynamics/material/material_action.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::scene_v1 {

class PythonCallMaterialAction : public MaterialAction {
 public:
  PythonCallMaterialAction(bool at_disconnect_in, PyObject* call_obj_in);
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  void Execute(Node* node1, Node* node2, Scene* scene) override;
  bool at_disconnect;
  Object::Ref<base::PythonContextCall> call;
  auto GetType() const -> Type override { return Type::SCRIPT_CALL; }
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_PYTHON_CALL_MATERIAL_ACTION_H_
