// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_SOUND_MATERIAL_ACTION_H_
#define BALLISTICA_DYNAMICS_MATERIAL_SOUND_MATERIAL_ACTION_H_

#include "ballistica/assets/component/sound.h"
#include "ballistica/ballistica.h"
#include "ballistica/dynamics/material/material_action.h"

namespace ballistica {

class SoundMaterialAction : public MaterialAction {
 public:
  SoundMaterialAction() = default;
  SoundMaterialAction(Sound* sound_in, float volume_in)
      : sound_(sound_in), volume_(volume_in) {}
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  auto GetType() const -> Type override { return Type::SOUND; }
  auto GetFlattenedSize() -> size_t override;
  void Flatten(char** buffer, SceneStream* output_stream) override;
  void Restore(const char** buffer, ClientSession* cs) override;

 private:
  Object::Ref<Sound> sound_;
  float volume_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_SOUND_MATERIAL_ACTION_H_
