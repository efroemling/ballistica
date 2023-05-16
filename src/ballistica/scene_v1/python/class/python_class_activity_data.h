// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_ACTIVITY_DATA_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_ACTIVITY_DATA_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassActivityData : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(HostActivity* host_activity) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetHostActivity() const -> HostActivity*;

 private:
  static PyMethodDef tp_methods[];
  static PyNumberMethods as_number_;
  static auto tp_repr(PythonClassActivityData* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassActivityData* self);
  static auto nb_bool(PythonClassActivityData* self) -> int;

  static auto Exists(PythonClassActivityData* self) -> PyObject*;
  static auto MakeForeground(PythonClassActivityData* self) -> PyObject*;
  static auto Start(PythonClassActivityData* self) -> PyObject*;
  static auto Expire(PythonClassActivityData* self) -> PyObject*;
  static auto Context(PythonClassActivityData* self) -> PyObject*;
  Object::WeakRef<HostActivity>* host_activity_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_ACTIVITY_DATA_H_
