// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_ACTION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_ACTION_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

class MaterialAction : public Object {
 public:
  enum class Type {
    NODE_MESSAGE,
    SCRIPT_COMMAND,
    SCRIPT_CALL,
    SOUND,
    IMPACT_SOUND,
    SKID_SOUND,
    ROLL_SOUND,
    NODE_MOD,
    PART_MOD,
    NODE_USER_MESSAGE
  };
  MaterialAction() = default;
  virtual auto GetType() const -> Type = 0;
  virtual void Apply(MaterialContext* context, const Part* src_part,
                     const Part* dst_part,
                     const Object::Ref<MaterialAction>& p) = 0;
  virtual void Execute(Node* node1, Node* node2, Scene* scene) {}
  virtual auto GetFlattenedSize() -> size_t { return 0; }
  virtual void Flatten(char** buffer, SessionStream* output_stream) {}
  virtual void Restore(const char** buffer, ClientSession* cs) {}
  auto IsNeededOnClient() -> bool {
    switch (GetType()) {
      case Type::NODE_MESSAGE:
      case Type::SOUND:
      case Type::IMPACT_SOUND:
      case Type::SKID_SOUND:
      case Type::ROLL_SOUND:
      case Type::NODE_MOD:
      case Type::PART_MOD:
        return true;
      default:
        return false;
    }
  }
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_ACTION_H_
