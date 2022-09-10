// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_MATERIAL_SKID_SOUND_MATERIAL_ACTION_H_
#define BALLISTICA_DYNAMICS_MATERIAL_SKID_SOUND_MATERIAL_ACTION_H_

#include "ballistica/assets/component/sound.h"
#include "ballistica/ballistica.h"
#include "ballistica/dynamics/material/material_action.h"

namespace ballistica {

// sound created based on collision forces perpendicular to the collision normal
class SkidSoundMaterialAction : public MaterialAction {
 public:
  SkidSoundMaterialAction() = default;
  SkidSoundMaterialAction(Sound* sound_in, float target_impulse_in,
                          float volume_in)
      : sound(sound_in), target_impulse(target_impulse_in), volume(volume_in) {}
  Object::Ref<Sound> sound;
  float target_impulse{};
  float volume{};
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  auto GetType() const -> Type override { return Type::SKID_SOUND; }
  auto GetFlattenedSize() -> size_t override;
  void Flatten(char** buffer, SceneStream* output_stream) override;
  void Restore(const char** buffer, ClientSession* cs) override;
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_MATERIAL_SKID_SOUND_MATERIAL_ACTION_H_
