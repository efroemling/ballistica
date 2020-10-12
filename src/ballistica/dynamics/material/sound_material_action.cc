// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/material/sound_material_action.h"

#include "ballistica/dynamics/material/material_context.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/game/session/client_session.h"
#include "ballistica/generic/utils.h"
#include "ballistica/media/component/sound.h"

namespace ballistica {

void SoundMaterialAction::Apply(MaterialContext* context, const Part* src_part,
                                const Part* dst_part,
                                const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  context->connect_sounds.emplace_back(sound_.get(), volume_);
}

auto SoundMaterialAction::GetFlattenedSize() -> size_t { return 4 + 2; }

void SoundMaterialAction::Flatten(char** buffer, GameStream* output_stream) {
  Utils::EmbedInt32NBO(buffer, static_cast_check_fit<int32_t>(
                                   output_stream->GetSoundID(sound_.get())));
  Utils::EmbedFloat16NBO(buffer, volume_);
}

void SoundMaterialAction::Restore(const char** buffer, ClientSession* cs) {
  sound_ = cs->GetSound(Utils::ExtractInt32NBO(buffer));
  volume_ = Utils::ExtractFloat16NBO(buffer);
}

}  // namespace ballistica
