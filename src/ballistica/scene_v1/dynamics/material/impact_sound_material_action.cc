// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/impact_sound_material_action.h"

#include "ballistica/base/audio/audio.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/scene_v1/support/client_session.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

auto ImpactSoundMaterialAction::GetFlattenedSize() -> size_t {
  // 1 byte for number of sounds plus 1 int per sound
  return 1 + 4 * sounds.size() + 2 + 2;
}

void ImpactSoundMaterialAction::Flatten(char** buffer,
                                        SessionStream* output_stream) {
  assert(sounds.size() < 100);
  auto sound_count{static_cast<uint8_t>(sounds.size())};
  Utils::EmbedInt8(buffer, sound_count);
  for (int i = 0; i < sound_count; i++) {
    Utils::EmbedInt32NBO(buffer,
                         static_cast_check_fit<int32_t>(
                             output_stream->GetSoundID(sounds[i].Get())));
  }
  Utils::EmbedFloat16NBO(buffer, target_impulse_);
  Utils::EmbedFloat16NBO(buffer, volume_);
}

void ImpactSoundMaterialAction::Restore(const char** buffer,
                                        ClientSession* cs) {
  int count{Utils::ExtractInt8(buffer)};
  BA_PRECONDITION(count > 0 && count < 100);
  sounds.clear();
  for (int i = 0; i < count; i++) {
    sounds.emplace_back(cs->GetSound(Utils::ExtractInt32NBO(buffer)));
  }
  target_impulse_ = Utils::ExtractFloat16NBO(buffer);
  volume_ = Utils::ExtractFloat16NBO(buffer);
}

void ImpactSoundMaterialAction::Apply(MaterialContext* context,
                                      const Part* src_part,
                                      const Part* dst_part,
                                      const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  assert(context->dynamics.Exists());
  assert(context->dynamics->in_process());

  // Avoid this if we're cutting corners.
  if (g_base->audio->UseLowQualityAudio()) {
    return;
  }

  // Let's only process impact-sounds a bit after the last one finished.
  // (cut down on processing)
  if (context->dynamics->process_real_time()
          - context->dynamics->last_impact_sound_time()
      > 100) {
    assert(!sounds.empty());
    context->impact_sounds.emplace_back(
        context, sounds[rand() % sounds.size()].Get(),  // NOLINT
        target_impulse_, volume_);
    context->complex_sound = true;
  }
}

}  // namespace ballistica::scene_v1
