// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_NODE_MESSAGE_MATERIAL_ACTION_H_
#define BALLISTICA_DYNAMICS_MATERIAL_NODE_MESSAGE_MATERIAL_ACTION_H_

#include "ballistica/ballistica.h"
#include "ballistica/dynamics/material/material_action.h"
#include "ballistica/generic/buffer.h"

namespace ballistica {

// Regular message.
class NodeMessageMaterialAction : public MaterialAction {
 public:
  NodeMessageMaterialAction() = default;
  NodeMessageMaterialAction(bool target_other_in, bool at_disconnect_in,
                            const char* data_in, size_t length_in);
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  void Execute(Node* node1, Node* node2, Scene* scene) override;
  bool target_other{};
  bool at_disconnect{};
  Buffer<char> data;
  auto GetType() const -> Type override { return Type::NODE_MESSAGE; }
  auto GetFlattenedSize() -> size_t override {
    // 1 byte for bools + data
    return static_cast<int>(1 + data.GetFlattenedSize());
  }
  void Flatten(char** buffer, SceneStream* output_stream) override {
    Utils::EmbedBools(buffer, target_other, at_disconnect);
    data.embed(buffer);
  }
  void Restore(const char** buffer, ClientSession* cs) override {
    Utils::ExtractBools(buffer, &target_other, &at_disconnect);
    data.Extract(buffer);
  }
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_NODE_MESSAGE_MATERIAL_ACTION_H_
