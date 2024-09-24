// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_COMPONENT_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_COMPONENT_H_

#include <utility>
#include <vector>

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// A component of a material - comprises one or more conditions and actions.
class MaterialComponent : public Object {
 public:
  auto GetDefaultOwnerThread() const -> EventLoopID override {
    return EventLoopID::kLogic;
  }

  auto GetFlattenedSize() -> size_t;
  void Flatten(char** buffer, SessionStream* output_stream);
  void Restore(const char** buffer, ClientSession* cs);

  // Actions are stored as shared pointers so references
  // to them can be stored with pending events
  // in case the component is deleted before they are run.
  std::vector<Object::Ref<MaterialAction> > actions;
  Object::Ref<MaterialConditionNode> conditions;
  auto eval_conditions(const Object::Ref<MaterialConditionNode>& condition,
                       const Material& c, const Part* part,
                       const Part* opposing_part, const MaterialContext& s)
      -> bool;

  // Apply the component to a context.
  void Apply(MaterialContext* c, const Part* src_part, const Part* dst_part);
  MaterialComponent();
  MaterialComponent(
      const Object::Ref<MaterialConditionNode>& conditions_in,
      const std::vector<Object::Ref<MaterialAction> >& actions_in);
  ~MaterialComponent();
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_COMPONENT_H_
