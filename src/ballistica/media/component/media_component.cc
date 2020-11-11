// Released under the MIT License. See LICENSE for details.

#include "ballistica/media/component/media_component.h"

#include <string>
#include <utility>

#include "ballistica/python/python_sys.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

MediaComponent::MediaComponent(std::string name, Scene* scene)
    : name_(std::move(name)), scene_(scene) {}

auto MediaComponent::GetPyRef(bool new_ref) -> PyObject* {
  if (!py_object_) {
    // if we have no python object, create it
    py_object_ = CreatePyObject();
    assert(py_object_ != nullptr);
  }
  if (new_ref) {
    Py_INCREF(py_object_);
  }
  return py_object_;
}

auto MediaComponent::GetObjectDescription() const -> std::string {
  return "<ballistica::" + GetMediaComponentTypeName() + " \"" + name() + "\">";
}

void MediaComponent::ClearPyObject() {
  assert(py_object_ != nullptr);
  py_object_ = nullptr;
}

}  // namespace ballistica
