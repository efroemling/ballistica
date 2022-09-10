// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/component/model.h"

#include "ballistica/python/class/python_class_model.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

Model::Model(const std::string& name, Scene* scene)
    : AssetComponent(name, scene), dead_(false) {
  assert(InLogicThread());

  if (scene) {
    if (SceneStream* os = scene->GetSceneStream()) {
      os->AddModel(this);
    }
  }
  {
    Assets::AssetListLock lock;
    model_data_ = g_assets->GetModelData(name);
  }
  assert(model_data_.exists());
}

Model::~Model() { MarkDead(); }

void Model::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (SceneStream* os = s->GetSceneStream()) {
      os->RemoveModel(this);
    }
  }
  dead_ = true;
}

auto Model::CreatePyObject() -> PyObject* {
  return PythonClassModel::Create(this);
}

}  // namespace ballistica
