// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/component/data.h"

#include "ballistica/python/class/python_class_data.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

Data::Data(const std::string& name, Scene* scene)
    : AssetComponent(name, scene), dead_(false) {
  assert(InLogicThread());

  if (scene) {
    if (SceneStream* os = scene->GetSceneStream()) {
      os->AddData(this);
    }
  }
  {
    Assets::AssetListLock lock;
    data_data_ = g_assets->GetDataData(name);
  }
  assert(data_data_.exists());
}

Data::~Data() { MarkDead(); }

void Data::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (SceneStream* os = s->GetSceneStream()) {
      os->RemoveData(this);
    }
  }
  dead_ = true;
}

auto Data::CreatePyObject() -> PyObject* {
  return PythonClassData::Create(this);
}

}  // namespace ballistica
