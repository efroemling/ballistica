// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_collision_mesh.h"

#include "ballistica/scene_v1/python/class/python_class_scene_collision_mesh.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SceneCollisionMesh::SceneCollisionMesh(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());
  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->AddCollisionMesh(this);
    }
  }
  {
    base::Assets::AssetListLock lock;
    collision_mesh_data_ = g_base->assets->GetCollisionMesh(name);
  }
  assert(collision_mesh_data_.Exists());
}

SceneCollisionMesh::~SceneCollisionMesh() { MarkDead(); }

void SceneCollisionMesh::MarkDead() {
  if (dead()) {
    return;
  }
  set_dead(true);

  if (Scene* s = scene()) {
    if (SessionStream* os = s->GetSceneStream()) {
      os->RemoveCollisionMesh(this);
    }
  }

  // If we've created a Python ref, it's likewise holding a ref
  // to us, which is a dependency loop. Break the loop to allow us
  // to go down cleanly.
  ReleasePyObj();
}

auto SceneCollisionMesh::CreatePyObject() -> PyObject* {
  return PythonClassSceneCollisionMesh::Create(this);
}

}  // namespace ballistica::scene_v1
