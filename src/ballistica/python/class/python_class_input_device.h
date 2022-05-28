// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_INPUT_DEVICE_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_INPUT_DEVICE_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassInputDevice : public PythonClass {
 public:
  static auto type_name() -> const char* { return "InputDevice"; }
  static void SetupType(PyTypeObject* obj);
  static auto Create(InputDevice* input_device) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetInputDevice() const -> InputDevice*;

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
  static auto RemoveRemotePlayerFromGame(PythonClassInputDevice* self)
      -> PyObject*;
  static auto GetDefaultPlayerName(PythonClassInputDevice* self) -> PyObject*;
  static auto GetPlayerProfiles(PythonClassInputDevice* self) -> PyObject*;
  static auto GetV1AccountName(PythonClassInputDevice* self, PyObject* args,
                               PyObject* keywds) -> PyObject*;
  static auto IsConnectedToRemotePlayer(PythonClassInputDevice* self)
      -> PyObject*;
  static auto Exists(PythonClassInputDevice* self) -> PyObject*;
  static auto GetAxisName(PythonClassInputDevice* self, PyObject* args,
                          PyObject* keywds) -> PyObject*;
  static auto GetButtonName(PythonClassInputDevice* self, PyObject* args,
                            PyObject* keywds) -> PyObject*;
  static PyNumberMethods as_number_;
  Object::WeakRef<InputDevice>* input_device_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_INPUT_DEVICE_H_
