// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/material/sound_material_action.h"

#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/scene_v1/support/client_session.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

void SoundMaterialAction::Apply(MaterialContext* context, const Part* src_part,
                                const Part* dst_part,
                                const Object::Ref<MaterialAction>& p) {
  assert(context && src_part && dst_part);
  context->connect_sounds.emplace_back(sound_.Get(), volume_);
}

auto SoundMaterialAction::GetFlattenedSize() -> size_t { return 4 + 2; }

void SoundMaterialAction::Flatten(char** buffer, SessionStream* output_stream) {
  Utils::EmbedInt32NBO(buffer, static_cast_check_fit<int32_t>(
                                   output_stream->GetSoundID(sound_.Get())));
  Utils::EmbedFloat16NBO(buffer, volume_);
}

void SoundMaterialAction::Restore(const char** buffer, ClientSession* cs) {
  sound_ = cs->GetSound(Utils::ExtractInt32NBO(buffer));
  volume_ = Utils::ExtractFloat16NBO(buffer);
}

}  // namespace ballistica::scene_v1
