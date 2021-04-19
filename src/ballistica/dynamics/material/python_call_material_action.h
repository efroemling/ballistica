// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_PYTHON_CALL_MATERIAL_ACTION_H_
#define BALLISTICA_DYNAMICS_MATERIAL_PYTHON_CALL_MATERIAL_ACTION_H_

#include "ballistica/ballistica.h"
#include "ballistica/dynamics/material/material_action.h"
#include "ballistica/python/python_context_call.h"

namespace ballistica {

class PythonCallMaterialAction : public MaterialAction {
 public:
  PythonCallMaterialAction(bool at_disconnect_in, PyObject* call_obj_in);
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  void Execute(Node* node1, Node* node2, Scene* scene) override;
  bool at_disconnect;
  Object::Ref<PythonContextCall> call;
  auto GetType() const -> Type override { return Type::SCRIPT_CALL; }
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_PYTHON_CALL_MATERIAL_ACTION_H_
