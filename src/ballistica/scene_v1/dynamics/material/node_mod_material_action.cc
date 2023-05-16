// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/node_mod_material_action.h"

#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto NodeModMaterialAction::GetType() const -> MaterialAction::Type {
  return Type::NODE_MOD;
}

auto NodeModMaterialAction::GetFlattenedSize() -> size_t { return 1 + 4; }

void NodeModMaterialAction::Flatten(char** buffer,
                                    SessionStream* output_stream) {
  Utils::EmbedInt8(buffer, static_cast<int8_t>(attr));
  Utils::EmbedFloat32(buffer, attr_val);
}

void NodeModMaterialAction::Restore(const char** buffer, ClientSession* cs) {
  attr = static_cast<NodeCollideAttr>(Utils::ExtractInt8(buffer));
  attr_val = Utils::ExtractFloat32(buffer);
}

void NodeModMaterialAction::Apply(MaterialContext* context,
                                  const Part* src_part, const Part* dst_part,
                                  const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  // Go ahead and make our modification to the context.
  switch (attr) {
    case NodeCollideAttr::kCollideNode:
      context->node_collide = static_cast<bool>(attr_val);
      break;
    default:
      throw Exception();
  }
}

}  // namespace ballistica::scene_v1
