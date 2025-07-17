// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DATA_ASSET_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DATA_ASSET_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSceneDataAsset : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static PyTypeObject type_obj;
  static auto tp_repr(PythonClassSceneDataAsset* self) -> PyObject*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(SceneDataAsset* data) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetData(bool doraise = true) const -> SceneDataAsset*;

 private:
  static PyMethodDef tp_methods[];
  static auto GetValue(PythonClassSceneDataAsset* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSceneDataAsset* self);
  static bool s_create_empty_;
  Object::Ref<SceneDataAsset>* data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DATA_ASSET_H_
