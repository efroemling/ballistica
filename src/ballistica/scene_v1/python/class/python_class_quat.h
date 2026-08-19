// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_QUAT_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_QUAT_H_

#include "ballistica/shared/python/python_class.h"
#include "ode/ode_common.h"

namespace ballistica::scene_v1 {

class PythonClassQuat : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(const dQuaternion& val) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static auto FromAngles(PyObject* cls, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto FromDirection(PyObject* cls, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto Slerp(PyObject* cls, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto Inverse(PythonClassQuat* self) -> PyObject*;
  static auto Normalized(PythonClassQuat* self) -> PyObject*;
  static PyTypeObject type_obj;
  dQuaternion value{};

 private:
  static PyMethodDef tp_methods[];
  static PySequenceMethods as_sequence_;
  static PyNumberMethods as_number_;
  static auto tp_repr(PythonClassQuat* self) -> PyObject*;
  static auto sq_length(PythonClassQuat* self) -> Py_ssize_t;
  static auto sq_item(PythonClassQuat* self, Py_ssize_t i) -> PyObject*;
  static auto nb_multiply(PyObject* l, PyObject* r) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto tp_getattro(PythonClassQuat* self, PyObject* attr) -> PyObject*;
  static auto tp_richcompare(PythonClassQuat* c1, PyObject* c2, int op)
      -> PyObject*;
};

}  // namespace ballistica::scene_v1
#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_QUAT_H_
