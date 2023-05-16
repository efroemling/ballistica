// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_SOUND_MATERIAL_ACTION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_SOUND_MATERIAL_ACTION_H_

#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/dynamics/material/material_action.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::scene_v1 {

class SoundMaterialAction : public MaterialAction {
 public:
  SoundMaterialAction() = default;
  SoundMaterialAction(SceneSound* sound_in, float volume_in)
      : sound_(sound_in), volume_(volume_in) {}
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  auto GetType() const -> Type override { return Type::SOUND; }
  auto GetFlattenedSize() -> size_t override;
  void Flatten(char** buffer, SessionStream* output_stream) override;
  void Restore(const char** buffer, ClientSession* cs) override;

 private:
  Object::Ref<SceneSound> sound_;
  float volume_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_SOUND_MATERIAL_ACTION_H_
