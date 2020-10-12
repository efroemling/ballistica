// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_MATERIAL_COMPONENT_H_
#define BALLISTICA_DYNAMICS_MATERIAL_MATERIAL_COMPONENT_H_

#include <utility>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

// A component of a material - comprises one or more conditions and actions.
class MaterialComponent : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
    return ThreadIdentifier::kGame;
  }

  auto GetFlattenedSize() -> size_t;
  void Flatten(char** buffer, GameStream* output_stream);
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
  MaterialComponent() = default;
  MaterialComponent(const Object::Ref<MaterialConditionNode>& conditions_in,
                    std::vector<Object::Ref<MaterialAction> > actions_in)
      : conditions(conditions_in), actions(std::move(actions_in)) {}
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_MATERIAL_COMPONENT_H_
