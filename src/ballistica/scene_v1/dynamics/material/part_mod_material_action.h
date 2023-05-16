// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_PART_MOD_MATERIAL_ACTION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_PART_MOD_MATERIAL_ACTION_H_

#include "ballistica/scene_v1/dynamics/material/material_action.h"

namespace ballistica::scene_v1 {

class PartModMaterialAction : public MaterialAction {
 public:
  PartModMaterialAction() = default;
  PartModMaterialAction(PartCollideAttr attr_in, float attr_val_in)
      : attr(attr_in), attr_val(attr_val_in) {}
  PartCollideAttr attr{};
  float attr_val{};
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  auto GetType() const -> Type override;
  auto GetFlattenedSize() -> size_t override;
  void Flatten(char** buffer, SessionStream* output_stream) override;
  void Restore(const char** buffer, ClientSession* cs) override;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_PART_MOD_MATERIAL_ACTION_H_
