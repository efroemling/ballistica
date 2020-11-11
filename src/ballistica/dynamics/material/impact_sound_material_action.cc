// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/impact_sound_material_action.h"

#include "ballistica/dynamics/dynamics.h"
#include "ballistica/dynamics/material/material_context.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/game/session/client_session.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/media/component/sound.h"

namespace ballistica {

auto ImpactSoundMaterialAction::GetFlattenedSize() -> size_t {
  // 1 byte for number of sounds plus 1 int per sound
  return 1 + 4 * sounds.size() + 2 + 2;
}

void ImpactSoundMaterialAction::Flatten(char** buffer,
                                        GameStream* output_stream) {
  assert(sounds.size() < 100);
  auto sound_count{static_cast<uint8_t>(sounds.size())};
  Utils::EmbedInt8(buffer, sound_count);
  for (int i = 0; i < sound_count; i++) {
    Utils::EmbedInt32NBO(buffer,
                         static_cast_check_fit<int32_t>(
                             output_stream->GetSoundID(sounds[i].get())));
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
  assert(context->dynamics.exists());
  assert(context->dynamics->in_process());

  // For now lets avoid this in low-quality graphics mode (should we make
  // a low-quality sound mode?)
  if (g_graphics_server
      && g_graphics_server->quality() < GraphicsQuality::kMedium) {
    return;
  }

  // Let's only process impact-sounds a bit after the last one finished.
  // (cut down on processing)
  if (context->dynamics->process_real_time()
          - context->dynamics->last_impact_sound_time()
      > 100) {
    assert(!sounds.empty());
    context->impact_sounds.emplace_back(
        context, sounds[rand() % sounds.size()].get(),  // NOLINT
        target_impulse_, volume_);
    context->complex_sound = true;
  }
}

}  // namespace ballistica
