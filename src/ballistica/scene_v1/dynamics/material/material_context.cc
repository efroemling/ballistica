// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/material_context.h"

#include "ballistica/base/audio/audio.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/material/material_action.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

MaterialContext::MaterialContext(Scene* scene)
    : dynamics(scene->dynamics()),
      friction(1.0f),
      stiffness(1.0f),
      damping(1.0f),
      bounce(0),
      collide(true),
      node_collide(true),
      use_node_collide(true),
      physical(true),
      complex_sound(false) {}

MaterialContext::SoundEntry::SoundEntry(SceneSound* sound_in, float volume_in)
    : sound(sound_in), volume(volume_in) {}

MaterialContext::ImpactSoundEntry::ImpactSoundEntry(MaterialContext* context,
                                                    SceneSound* sound_in,
                                                    float target_impulse_in,
                                                    float volume_in)
    : context(context),
      sound(sound_in),
      target_impulse(target_impulse_in),
      volume(volume_in) {}

MaterialContext::SkidSoundEntry::SkidSoundEntry(
    const MaterialContext::SkidSoundEntry& other) {
  *this = other;
  assert(context);
#if BA_DEBUG_BUILD
  assert(context->dynamics.Exists());
#endif
  assert(context->dynamics->in_process());
  context->dynamics->IncrementSkidSoundCount();
}

MaterialContext::SkidSoundEntry::SkidSoundEntry(MaterialContext* context_in,
                                                SceneSound* sound_in,
                                                float target_impulse_in,
                                                float volume_in)
    : context(context_in),
      sound(sound_in),
      target_impulse(target_impulse_in),
      volume(volume_in),
      playing(false) {
  assert(context);
  assert(context->dynamics.Exists());
  assert(context->dynamics->in_process());
  context->dynamics->IncrementSkidSoundCount();
}

MaterialContext::SkidSoundEntry::~SkidSoundEntry() {
  assert(context);
  assert(context->dynamics.Exists());
  context->dynamics->DecrementSkidSoundCount();
  if (playing) {
    g_base->audio->PushSourceFadeOutCall(play_id, 200);
  }
}

MaterialContext::RollSoundEntry::RollSoundEntry(MaterialContext* context_in,
                                                SceneSound* sound_in,
                                                float target_impulse_in,
                                                float volume_in)
    : context(context_in),
      sound(sound_in),
      target_impulse(target_impulse_in),
      volume(volume_in),
      playing(false) {
  assert(context);
  assert(context->dynamics.Exists());
  assert(context->dynamics->in_process());
  context->dynamics->IncrementRollSoundCount();
}

MaterialContext::RollSoundEntry::RollSoundEntry(
    const MaterialContext::RollSoundEntry& other) {
  *this = other;
  assert(context);
  assert(context->dynamics.Exists());
  assert(context->dynamics->in_process());
  context->dynamics->IncrementRollSoundCount();
}

MaterialContext::RollSoundEntry::~RollSoundEntry() {
  assert(context);
  assert(context->dynamics.Exists());
  context->dynamics->DecrementRollSoundCount();
  if (playing) {
    g_base->audio->PushSourceFadeOutCall(play_id, 200);
  }
}

}  // namespace ballistica::scene_v1
