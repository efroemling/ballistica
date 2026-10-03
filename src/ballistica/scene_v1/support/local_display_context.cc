// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/local_display_context.h"

#include <Python.h>

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

// We start our scene's clock at the parent's so bs.time() reads the same
// in here as it does out there, and run under its protocol.
LocalDisplayContext::LocalDisplayContext(Scene* parent_scene)
    : LocalSceneContext(parent_scene->time(),
                        parent_scene->protocol_version()) {}

LocalDisplayContext::~LocalDisplayContext() = default;

auto LocalDisplayContext::GetContextDescription() -> std::string {
  // GetPyLocalDisplay returns a new ref or nullptr.
  auto obj{PythonRef::StolenSoft(GetPyLocalDisplay())};
  if (obj.exists() && obj.get() != Py_None) {
    return obj.Str();
  }
  return SceneV1Context::GetContextDescription();
}

void LocalDisplayContext::RegisterPyLocalDisplay(PyObject* obj) {
  assert(obj && obj != Py_None);
  assert(!py_local_display_weak_ref_.exists());
  py_local_display_weak_ref_.Steal(PyWeakref_NewRef(obj, nullptr));
}

auto LocalDisplayContext::GetPyLocalDisplay() const -> PyObject* {
  auto* ref_obj{py_local_display_weak_ref_.get()};
  if (!ref_obj) {
    return nullptr;
  }
  PyObject* obj{};
  int result = PyWeakref_GetRef(ref_obj, &obj);
  // Return new obj ref (result 1) or nullptr for dead objs (result 0).
  if (result == 0 || result == 1) {
    return obj;
  }
  assert(result == -1);
  PyErr_Clear();
  g_core->logging->Log(
      LogName::kBa, LogLevel::kError,
      "LocalDisplayContext::GetPyLocalDisplay(): error getting weakref obj.");
  return nullptr;
}

}  // namespace ballistica::scene_v1
