// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_SOUND_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_SOUND_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSceneSound : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static PyTypeObject type_obj;
  static auto tp_repr(PythonClassSceneSound* self) -> PyObject*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(SceneSound* sound) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetSound(bool doraise = true) const -> SceneSound*;

 private:
  static auto Play(PythonClassSceneSound* self, PyObject* args,
                   PyObject* keywds) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSceneSound* self);
  static PyMethodDef tp_methods[];
  static bool s_create_empty_;
  Object::Ref<SceneSound>* sound_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_SOUND_H_
