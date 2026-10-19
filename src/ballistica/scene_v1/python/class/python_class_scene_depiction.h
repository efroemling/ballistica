// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DEPICTION_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DEPICTION_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/scene_v1/support/scene_depiction.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

/// Python wrapper for a session-level SceneDepiction (exposed as
/// bascenev1.Depiction). Opaque: constructed from a depiction's json and
/// plugged into node attrs of the depiction type.
class PythonClassSceneDepiction : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  /// Wrap an existing SceneDepiction (one whose original wrapper is
  /// gone; e.g. read back off a node attr). Returns a new reference.
  static auto Create(SceneDepiction* d) -> PyObject*;
  auto GetDepiction(bool doraise = true) const -> SceneDepiction* {
    SceneDepiction* d = depiction_->get();
    if ((!d) && doraise) throw Exception("Invalid Depiction");
    return d;
  }

 private:
  static bool s_create_empty_;
  static PyMethodDef tp_methods[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void Delete(Object::Ref<SceneDepiction>* d);
  static void tp_dealloc(PythonClassSceneDepiction* self);
  static auto tp_repr(PythonClassSceneDepiction* self) -> PyObject*;
  Object::Ref<SceneDepiction>* depiction_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DEPICTION_H_
