// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/material_context.h"

#include "ballistica/audio/audio.h"
#include "ballistica/dynamics/dynamics.h"
#include "ballistica/dynamics/material/material_action.h"
#include "ballistica/media/component/sound.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

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

MaterialContext::SkidSoundEntry::SkidSoundEntry(
    const MaterialContext::SkidSoundEntry& other) {
  *this = other;
  assert(context);
#if BA_DEBUG_BUILD
  assert(context->dynamics.exists());
#endif
  assert(context->dynamics->in_process());
  context->dynamics->increment_skid_sound_count();
}

MaterialContext::SkidSoundEntry::SkidSoundEntry(MaterialContext* context_in,
                                                Sound* sound_in,
                                                float target_impulse_in,
                                                float volume_in)
    : context(context_in),
      sound(sound_in),
      target_impulse(target_impulse_in),
      volume(volume_in),
      playing(false) {
  assert(context);
  assert(context->dynamics.exists());
  assert(context->dynamics->in_process());
  context->dynamics->increment_skid_sound_count();
}

MaterialContext::SkidSoundEntry::~SkidSoundEntry() {
  assert(context);
  assert(context->dynamics.exists());
  context->dynamics->decrement_skid_sound_count();
  if (playing) {
    g_audio->PushSourceFadeOutCall(play_id, 200);
  }
}

MaterialContext::RollSoundEntry::RollSoundEntry(MaterialContext* context_in,
                                                Sound* sound_in,
                                                float target_impulse_in,
                                                float volume_in)
    : context(context_in),
      sound(sound_in),
      target_impulse(target_impulse_in),
      volume(volume_in),
      playing(false) {
  assert(context);
  assert(context->dynamics.exists());
  assert(context->dynamics->in_process());
  context->dynamics->incrementRollSoundCount();
}

MaterialContext::RollSoundEntry::RollSoundEntry(
    const MaterialContext::RollSoundEntry& other) {
  *this = other;
  assert(context);
  assert(context->dynamics.exists());
  assert(context->dynamics->in_process());
  context->dynamics->incrementRollSoundCount();
}

MaterialContext::RollSoundEntry::~RollSoundEntry() {
  assert(context);
  assert(context->dynamics.exists());
  context->dynamics->decrement_roll_sound_count();
  if (playing) {
    g_audio->PushSourceFadeOutCall(play_id, 200);
  }
}

}  // namespace ballistica
