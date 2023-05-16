// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_COLLISION_MESH_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_COLLISION_MESH_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSceneCollisionMesh : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static auto tp_repr(PythonClassSceneCollisionMesh* self) -> PyObject*;
  static void SetupType(PyTypeObject* cls);
  static PyTypeObject type_obj;
  static auto Create(SceneCollisionMesh* collision_mesh) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetCollisionMesh(bool doraise = true) const -> SceneCollisionMesh*;

 private:
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSceneCollisionMesh* self);
  static bool s_create_empty_;
  Object::Ref<SceneCollisionMesh>* collision_mesh_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_COLLISION_MESH_H_
