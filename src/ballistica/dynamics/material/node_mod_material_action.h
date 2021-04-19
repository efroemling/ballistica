// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_NODE_MOD_MATERIAL_ACTION_H_
#define BALLISTICA_DYNAMICS_MATERIAL_NODE_MOD_MATERIAL_ACTION_H_

#include "ballistica/dynamics/material/material_action.h"

namespace ballistica {

class NodeModMaterialAction : public MaterialAction {
 public:
  NodeModMaterialAction() = default;
  NodeModMaterialAction(NodeCollideAttr attr_in, float attr_val_in)
      : attr(attr_in), attr_val(attr_val_in) {}
  NodeCollideAttr attr{};
  float attr_val{};
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  auto GetType() const -> Type override;
  auto GetFlattenedSize() -> size_t override;
  void Flatten(char** buffer, GameStream* output_stream) override;
  void Restore(const char** buffer, ClientSession* cs) override;
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_NODE_MOD_MATERIAL_ACTION_H_
