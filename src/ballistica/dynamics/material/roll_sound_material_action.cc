// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/roll_sound_material_action.h"

#include "ballistica/assets/component/sound.h"
#include "ballistica/dynamics/dynamics.h"
#include "ballistica/dynamics/material/material_context.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/logic/session/client_session.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

auto RollSoundMaterialAction::GetFlattenedSize() -> size_t { return 4 + 2 + 2; }

void RollSoundMaterialAction::Flatten(char** buffer,
                                      SceneStream* output_stream) {
  Utils::EmbedInt32NBO(buffer, static_cast_check_fit<int32_t>(
                                   output_stream->GetSoundID(sound.get())));
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
  assert(context->dynamics.exists());
  assert(context->dynamics->in_process());

  // For now lets avoid this in low-quality graphics mode
  // (should we make a low-quality sound mode?)
  if (g_graphics && g_graphics_server->quality() < GraphicsQuality::kMedium) {
    return;
  }

  // Let's limit the amount of skid-sounds we spawn, otherwise we'll
  // start using up all our sound resources on skids when things get messy
  if (context->dynamics->getRollSoundCount() < 2) {
    context->roll_sounds.emplace_back(context, sound.get(), target_impulse,
                                      volume);
    context->complex_sound = true;
  }
}

}  // namespace ballistica
