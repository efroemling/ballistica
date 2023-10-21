// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/roll_sound_material_action.h"

#include "ballistica/base/audio/audio.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/scene_v1/support/client_session.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto RollSoundMaterialAction::GetFlattenedSize() -> size_t { return 4 + 2 + 2; }

void RollSoundMaterialAction::Flatten(char** buffer,
                                      SessionStream* output_stream) {
  Utils::EmbedInt32NBO(buffer, static_cast_check_fit<int32_t>(
                                   output_stream->GetSoundID(sound.Get())));
  Utils::EmbedFloat16NBO(buffer, target_impulse);
  Utils::EmbedFloat16NBO(buffer, volume);
}

void RollSoundMaterialAction::Restore(const char** buffer, ClientSession* cs) {
  sound = cs->GetSound(Utils::ExtractInt32NBO(buffer));
  target_impulse = Utils::ExtractFloat16NBO(buffer);
  volume = Utils::ExtractFloat16NBO(buffer);
}

void RollSoundMaterialAction::Apply(MaterialContext* context,
                                    const Part* src_part, const Part* dst_part,
                                    const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  assert(context->dynamics.Exists());
  assert(context->dynamics->in_process());

  // Avoid this if we're cutting corners.
  if (g_base->audio->UseLowQualityAudio()) {
    return;
  }

  // Let's limit the amount of skid-sounds we spawn, otherwise we'll
  // start using up all our sound resources on skids when things get messy
  if (context->dynamics->roll_sound_count() < 2) {
    context->roll_sounds.emplace_back(context, sound.Get(), target_impulse,
                                      volume);
    context->complex_sound = true;
  }
}

}  // namespace ballistica::scene_v1
