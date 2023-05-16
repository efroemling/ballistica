// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_CONTEXT_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_CONTEXT_H_

#include <vector>

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// Contexts materials use when getting and setting collision data
class MaterialContext {
 public:
  BA_DEBUG_PTR(Dynamics) dynamics;
  float friction{};
  float stiffness{};
  float damping{};
  float bounce{};
  bool collide{};
  bool node_collide{};
  bool use_node_collide{};
  bool physical{};

  // This should get set to true if
  // anything is added to impact_sounds, skid_sounds, or roll_sounds.
  // This way we know to calculate collision forces, relative velocities, etc.
  bool complex_sound{};
  std::vector<Object::Ref<MaterialAction> > connect_actions;
  std::vector<Object::Ref<MaterialAction> > disconnect_actions;
  struct SoundEntry {
    Object::Ref<SceneSound> sound;
    float volume;
    SoundEntry(SceneSound* sound_in, float volume_in);
  };
  class ImpactSoundEntry {
   public:
    MaterialContext* context;
    Object::Ref<SceneSound> sound;
    float volume;
    float target_impulse;
    ImpactSoundEntry(MaterialContext* context, SceneSound* sound_in,
                     float target_impulse_in, float volume_in);
  };
  class SkidSoundEntry {
   public:
    MaterialContext* context{};
    Object::Ref<SceneSound> sound;
    float volume{};
    float target_impulse{};
    // Used to keep track of the playing sound.
    uint32_t play_id{};
    bool playing{};
    SkidSoundEntry(MaterialContext* context, SceneSound* sound_in,
                   float target_impulse_in, float volume_in);
    ~SkidSoundEntry();
    SkidSoundEntry(const SkidSoundEntry& other);
  };
  class RollSoundEntry {
   public:
    MaterialContext* context{};
    Object::Ref<SceneSound> sound;
    float volume{};
    float target_impulse{};
    // Used to keep track of the playing sound.
    uint32_t play_id{};
    bool playing{};
    RollSoundEntry(MaterialContext* context, SceneSound* sound_in,
                   float target_impulse_in, float volume_in);
    RollSoundEntry(const RollSoundEntry& other);
    ~RollSoundEntry();
  };
  std::vector<SoundEntry> connect_sounds;
  std::vector<ImpactSoundEntry> impact_sounds;
  std::vector<SkidSoundEntry> skid_sounds;
  std::vector<RollSoundEntry> roll_sounds;
  explicit MaterialContext(Scene* scene_in);

 private:
  BA_DISALLOW_CLASS_COPIES(MaterialContext);
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_MATERIAL_MATERIAL_CONTEXT_H_
