// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/component/collide_model.h"

#include "ballistica/python/class/python_class_collide_model.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

CollideModel::CollideModel(const std::string& name, Scene* scene)
    : AssetComponent(name, scene), dead_(false) {
  assert(InLogicThread());
  if (scene) {
    if (SceneStream* os = scene->GetSceneStream()) {
      os->AddCollideModel(this);
    }
  }
  {
    Assets::AssetListLock lock;
    collide_model_data_ = g_assets->GetCollideModelData(name);
  }
  assert(collide_model_data_.exists());
}

CollideModel::~CollideModel() { MarkDead(); }

void CollideModel::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (SceneStream* os = s->GetSceneStream()) {
      os->RemoveCollideModel(this);
    }
  }
  dead_ = true;
}

auto CollideModel::CreatePyObject() -> PyObject* {
  return PythonClassCollideModel::Create(this);
}

}  // namespace ballistica
