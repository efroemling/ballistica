// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_INPUT_DEVICE_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_INPUT_DEVICE_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassInputDevice : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(SceneV1InputDeviceDelegate* input_device) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetInputDevice() const -> SceneV1InputDeviceDelegate*;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassInputDevice* self) -> PyObject*;
  static auto tp_getattro(PythonClassInputDevice* self, PyObject* attr)
      -> PyObject*;
  static auto tp_setattro(PythonClassInputDevice* self, PyObject* attr,
                          PyObject* val) -> int;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassInputDevice* self);
  static auto nb_bool(PythonClassInputDevice* self) -> int;
  static auto DetachFromPlayer(PythonClassInputDevice* self) -> PyObject*;
  static auto GetDefaultPlayerName(PythonClassInputDevice* self) -> PyObject*;
  static auto GetPlayerProfiles(PythonClassInputDevice* self) -> PyObject*;
  static auto GetV1AccountName(PythonClassInputDevice* self, PyObject* args,
                               PyObject* keywds) -> PyObject*;
  static auto IsAttachedToPlayer(PythonClassInputDevice* self) -> PyObject*;
  static auto Exists(PythonClassInputDevice* self) -> PyObject*;
  static auto GetAxisName(PythonClassInputDevice* self, PyObject* args,
                          PyObject* keywds) -> PyObject*;
  static auto GetButtonName(PythonClassInputDevice* self, PyObject* args,
                            PyObject* keywds) -> PyObject*;
  static PyNumberMethods as_number_;
  Object::WeakRef<SceneV1InputDeviceDelegate>* input_device_delegate_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_INPUT_DEVICE_H_
