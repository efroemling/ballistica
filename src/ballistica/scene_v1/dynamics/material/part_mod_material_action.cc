// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/part_mod_material_action.h"

#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto PartModMaterialAction::GetType() const -> MaterialAction::Type {
  return Type::PART_MOD;
}

auto PartModMaterialAction::GetFlattenedSize() -> size_t { return 1 + 4; }

void PartModMaterialAction::Flatten(char** buffer,
                                    SessionStream* output_stream) {
  Utils::EmbedInt8(buffer, static_cast<int8_t>(attr));
  Utils::EmbedFloat32(buffer, attr_val);
}

void PartModMaterialAction::Restore(const char** buffer, ClientSession* cs) {
  attr = static_cast<PartCollideAttr>(Utils::ExtractInt8(buffer));
  attr_val = Utils::ExtractFloat32(buffer);
}

void PartModMaterialAction::Apply(MaterialContext* context,
                                  const Part* src_part, const Part* dst_part,
                                  const Object::Ref<MaterialAction>& p) {
  // Go ahead and make our modification to the context.
  switch (attr) {
    case PartCollideAttr::kCollide:
      context->collide = static_cast<bool>(attr_val);
      break;
    case PartCollideAttr::kUseNodeCollide:
      context->use_node_collide = static_cast<bool>(attr_val);
      break;
    case PartCollideAttr::kPhysical:
      context->physical = static_cast<bool>(attr_val);
      break;
    case PartCollideAttr::kFriction:
      context->friction = attr_val;
      break;
    case PartCollideAttr::kStiffness:
      context->stiffness = attr_val;
      break;
    case PartCollideAttr::kDamping:
      context->damping = attr_val;
      break;
    case PartCollideAttr::kBounce:
      context->bounce = attr_val;
      break;
    default:
      throw Exception();
  }
}

}  // namespace ballistica::scene_v1
