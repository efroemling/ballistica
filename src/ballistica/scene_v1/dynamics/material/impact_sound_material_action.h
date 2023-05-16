// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_IMPACT_SOUND_MATERIAL_ACTION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_IMPACT_SOUND_MATERIAL_ACTION_H_

#include <vector>

#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/dynamics/material/material_action.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::scene_v1 {

// A sound created based on collision forces parallel to the collision normal.
class ImpactSoundMaterialAction : public MaterialAction {
 public:
  ImpactSoundMaterialAction() = default;
  ImpactSoundMaterialAction(const std::vector<SceneSound*>& sounds_in,
                            float target_impulse_in, float volume_in)
      : sounds(PointersToRefs(sounds_in)),
        target_impulse_(target_impulse_in),
        volume_(volume_in) {}
  std::vector<Object::Ref<SceneSound> > sounds;
  void Apply(MaterialContext* context, const Part* src_part,
             const Part* dst_part,
             const Object::Ref<MaterialAction>& p) override;
  auto GetType() const -> Type override { return Type::IMPACT_SOUND; }
  auto GetFlattenedSize() -> size_t override;
  void Flatten(char** buffer, SessionStream* output_stream) override;
  void Restore(const char** buffer, ClientSession* cs) override;

 private:
  float target_impulse_{};
  float volume_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_IMPACT_SOUND_MATERIAL_ACTION_H_
