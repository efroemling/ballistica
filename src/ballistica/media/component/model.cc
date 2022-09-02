// Released under the MIT License. See LICENSE for details.

#include "ballistica/media/component/model.h"

#include "ballistica/game/game_stream.h"
#include "ballistica/python/class/python_class_model.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

Model::Model(const std::string& name, Scene* scene)
    : MediaComponent(name, scene), dead_(false) {
  assert(InLogicThread());

  if (scene) {
    if (GameStream* os = scene->GetGameStream()) {
      os->AddModel(this);
    }
  }
  {
    Media::MediaListsLock lock;
    model_data_ = g_media->GetModelData(name);
  }
  assert(model_data_.exists());
}

Model::~Model() { MarkDead(); }

void Model::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (GameStream* os = s->GetGameStream()) {
      os->RemoveModel(this);
    }
  }
  dead_ = true;
}

auto Model::CreatePyObject() -> PyObject* {
  return PythonClassModel::Create(this);
}

}  // namespace ballistica
