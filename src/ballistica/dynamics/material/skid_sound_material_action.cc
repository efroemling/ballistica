// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/skid_sound_material_action.h"

#include "ballistica/dynamics/dynamics.h"
#include "ballistica/dynamics/material/material_context.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/game/session/client_session.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/media/component/sound.h"

namespace ballistica {

auto SkidSoundMaterialAction::GetFlattenedSize() -> size_t { return 4 + 2 + 2; }

void SkidSoundMaterialAction::Flatten(char** buffer,
                                      GameStream* output_stream) {
  Utils::EmbedInt32NBO(buffer, static_cast_check_fit<int32_t>(
                                   output_stream->GetSoundID(sound.get())));
  Utils::EmbedFloat16NBO(buffer, target_impulse);
  Utils::EmbedFloat16NBO(buffer, volume);
}

void SkidSoundMaterialAction::Restore(const char** buffer, ClientSession* cs) {
  sound = cs->GetSound(Utils::ExtractInt32NBO(buffer));
  target_impulse = Utils::ExtractFloat16NBO(buffer);
  volume = Utils::ExtractFloat16NBO(buffer);
}

void SkidSoundMaterialAction::Apply(MaterialContext* context,
                                    const Part* src_part, const Part* dst_part,
                                    const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  assert(context->dynamics.exists());
  assert(context->dynamics->in_process());

  // For now lets avoid this in low-quality graphics mode
  // (should we make a low-quality sound mode?).
  if (g_graphics_server
      && g_graphics_server->quality() < GraphicsQuality::kMedium) {
    return;
  }

  // Let's limit the amount of skid-sounds we spawn, otherwise we'll start
  // using up all our sound resources on skids when things get messy.
  if (context->dynamics->skid_sound_count() < 2) {
    context->skid_sounds.emplace_back(context, sound.get(), target_impulse,
                                      volume);
    context->complex_sound = true;
  }
}

}  // namespace ballistica
