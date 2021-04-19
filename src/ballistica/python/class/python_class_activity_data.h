// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_ACTIVITY_DATA_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_ACTIVITY_DATA_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassActivityData : public PythonClass {
 public:
  static auto type_name() -> const char* { return "ActivityData"; }
  static void SetupType(PyTypeObject* obj);
  static auto Create(HostActivity* host_activity) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetHostActivity() const -> HostActivity*;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassActivityData* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassActivityData* self);
  static auto exists(PythonClassActivityData* self) -> PyObject*;
  static auto make_foreground(PythonClassActivityData* self) -> PyObject*;
  static auto start(PythonClassActivityData* self) -> PyObject*;
  static auto expire(PythonClassActivityData* self) -> PyObject*;
  Object::WeakRef<HostActivity>* host_activity_;
  static auto nb_bool(PythonClassActivityData* self) -> int;
  static PyNumberMethods as_number_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_ACTIVITY_DATA_H_
