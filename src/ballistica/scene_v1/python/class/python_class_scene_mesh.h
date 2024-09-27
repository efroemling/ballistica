// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_MESH_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_MESH_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSceneMesh : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static auto tp_repr(PythonClassSceneMesh* self) -> PyObject*;
  static void SetupType(PyTypeObject* cls);
  static PyTypeObject type_obj;
  static auto Create(SceneMesh* mesh) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetMesh(bool doraise = true) const -> SceneMesh*;

 private:
  static bool s_create_empty_;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSceneMesh* self);
  Object::Ref<SceneMesh>* mesh_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_MESH_H_
