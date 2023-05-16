// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_asset.h"

#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::scene_v1 {

SceneAsset::SceneAsset(std::string name, Scene* scene)
    : name_(std::move(name)), scene_(scene) {}

auto SceneAsset::GetPyRef(bool new_ref) -> PyObject* {
  assert(!dead());
  if (!py_object_) {
    // If we have no associated Python object, create it.
    py_object_ = CreatePyObject();
    assert(py_object_ != nullptr);
  }
  if (new_ref) {
    Py_INCREF(py_object_);
  }
  return py_object_;
}

auto SceneAsset::GetObjectDescription() const -> std::string {
  return "<ballistica::" + GetAssetTypeName() + " \"" + name() + "\">";
}

void SceneAsset::ReleasePyObj() {
  assert(g_base->InLogicThread());
  if (py_object_) {
    auto* obj = py_object_;
    py_object_ = nullptr;
    Py_DECREF(obj);
  }
}

}  // namespace ballistica::scene_v1
