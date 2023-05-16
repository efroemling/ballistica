// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_data_asset.h"

#include "ballistica/scene_v1/python/class/python_class_scene_data_asset.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SceneDataAsset::SceneDataAsset(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());

  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->AddData(this);
    }
  }
  {
    base::Assets::AssetListLock lock;
    data_data_ = g_base->assets->GetDataAsset(name);
  }
  assert(data_data_.Exists());
}

SceneDataAsset::~SceneDataAsset() { MarkDead(); }

void SceneDataAsset::MarkDead() {
  if (dead()) {
    return;
  }
  set_dead(true);

  if (Scene* s = scene()) {
    if (SessionStream* os = s->GetSceneStream()) {
      os->RemoveData(this);
    }
  }

  // If we've created a Python ref, it's likewise holding a ref
  // to us, which is a dependency loop. Break the loop to allow us
  // to go down cleanly.
  ReleasePyObj();
}

auto SceneDataAsset::CreatePyObject() -> PyObject* {
  return PythonClassSceneDataAsset::Create(this);
}

}  // namespace ballistica::scene_v1
