// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_sound.h"

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/scene_v1/python/class/python_class_scene_sound.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SceneSound::SceneSound(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());

  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->AddSound(this);
    }
  }
  {
    base::Assets::AssetListLock lock;
    sound_data_ = g_base->assets->GetSound(name);
  }
  assert(sound_data_.Exists());
}

SceneSound::~SceneSound() { MarkDead(); }

void SceneSound::MarkDead() {
  if (dead()) {
    return;
  }
  set_dead(true);

  if (Scene* s = scene()) {
    if (SessionStream* os = s->GetSceneStream()) {
      os->RemoveSound(this);
    }
  }

  // If we've created a Python ref, it's likewise holding a ref
  // to us, which is a dependency loop. Break the loop to allow us
  // to go down cleanly.
  ReleasePyObj();
}

auto SceneSound::CreatePyObject() -> PyObject* {
  return PythonClassSceneSound::Create(this);
}

}  // namespace ballistica::scene_v1
