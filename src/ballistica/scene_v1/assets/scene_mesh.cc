// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_mesh.h"

#include "ballistica/scene_v1/python/class/python_class_scene_mesh.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SceneMesh::SceneMesh(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());

  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->AddMesh(this);
    }
  }
  {
    base::Assets::AssetListLock lock;
    mesh_data_ = g_base->assets->GetMesh(name);
  }
  assert(mesh_data_.Exists());
}

SceneMesh::~SceneMesh() { MarkDead(); }

void SceneMesh::MarkDead() {
  if (dead()) {
    return;
  }
  set_dead(true);
  if (Scene* s = scene()) {
    if (SessionStream* os = s->GetSceneStream()) {
      os->RemoveMesh(this);
    }
  }

  // If we've created a Python ref, it's likewise holding a ref
  // to us, which is a dependency loop. Break the loop to allow us
  // to go down cleanly.
  ReleasePyObj();
}

auto SceneMesh::CreatePyObject() -> PyObject* {
  return PythonClassSceneMesh::Create(this);
}

}  // namespace ballistica::scene_v1
