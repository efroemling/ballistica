// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_TEXTURE_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_TEXTURE_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSceneTexture : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static auto tp_repr(PythonClassSceneTexture* self) -> PyObject*;
  static void SetupType(PyTypeObject* cls);
  static PyTypeObject type_obj;
  static auto Create(SceneTexture* texture) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetTexture(bool doraise = true) const -> SceneTexture*;

 private:
  static bool s_create_empty_;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSceneTexture* self);
  Object::Ref<SceneTexture>* texture_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_TEXTURE_H_
