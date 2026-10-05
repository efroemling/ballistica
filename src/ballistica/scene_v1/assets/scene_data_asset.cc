// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_data_asset.h"

#include <string>

#include "ballistica/scene_v1/python/class/python_class_scene_data_asset.h"

namespace ballistica::scene_v1 {

SceneDataAsset::SceneDataAsset(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());

  // Data assets feed host-side game logic only; clients never need
  // them, so (unlike textures, meshes, etc.) they never go on the scene
  // stream. (They once did, as kAddData/kRemoveData, which clients
  // never handled -- a hosted bs.getdata() dropped every joiner.)
  {
    base::Assets::AssetListLock lock;
    data_data_ = g_base->assets->GetDataAsset(name);
  }
  assert(data_data_.exists());
}

SceneDataAsset::~SceneDataAsset() { MarkDead(); }

void SceneDataAsset::MarkDead() {
  if (dead()) {
    return;
  }
  set_dead(true);

  // If we've created a Python ref, it's likewise holding a ref
  // to us, which is a dependency loop. Break the loop to allow us
  // to go down cleanly.
  ReleasePyObj();
}

auto SceneDataAsset::CreatePyObject() -> PyObject* {
  return PythonClassSceneDataAsset::Create(this);
}

}  // namespace ballistica::scene_v1
