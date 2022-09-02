// Released under the MIT License. See LICENSE for details.

#include "ballistica/media/component/data.h"

#include "ballistica/game/game_stream.h"
#include "ballistica/python/class/python_class_data.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

Data::Data(const std::string& name, Scene* scene)
    : MediaComponent(name, scene), dead_(false) {
  assert(InLogicThread());

  if (scene) {
    if (GameStream* os = scene->GetGameStream()) {
      os->AddData(this);
    }
  }
  {
    Media::MediaListsLock lock;
    data_data_ = g_media->GetDataData(name);
  }
  assert(data_data_.exists());
}

Data::~Data() { MarkDead(); }

void Data::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (GameStream* os = s->GetGameStream()) {
      os->RemoveData(this);
    }
  }
  dead_ = true;
}

auto Data::CreatePyObject() -> PyObject* {
  return PythonClassData::Create(this);
}

}  // namespace ballistica
