// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/component/sound.h"

#include "ballistica/assets/assets.h"
#include "ballistica/assets/data/sound_data.h"
#include "ballistica/python/class/python_class_sound.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

Sound::Sound(const std::string& name, Scene* scene)
    : AssetComponent(name, scene) {
  assert(InLogicThread());
  if (scene) {
    if (SceneStream* os = scene->GetSceneStream()) {
      os->AddSound(this);
    }
  }
  {
    Assets::AssetListLock lock;
    sound_data_ = g_assets->GetSoundData(name);
  }
  assert(sound_data_.exists());
}

Sound::~Sound() { MarkDead(); }

void Sound::MarkDead() {
  if (dead_) return;
  if (Scene* s = scene()) {
    if (SceneStream* os = s->GetSceneStream()) {
      os->RemoveSound(this);
    }
  }
  dead_ = true;
}

auto Sound::CreatePyObject() -> PyObject* {
  return PythonClassSound::Create(this);
}

}  // namespace ballistica
