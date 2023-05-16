// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_VEC3_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_VEC3_H_

#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

class PythonClassVec3 : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(const Vector3f& val) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static auto Length(PythonClassVec3* self) -> PyObject*;
  static auto Normalized(PythonClassVec3* self) -> PyObject*;
  static auto Dot(PythonClassVec3* self, PyObject* other) -> PyObject*;
  static auto Cross(PythonClassVec3* self, PyObject* other) -> PyObject*;
  static PyTypeObject type_obj;
  Vector3f value;

 private:
  static PyMethodDef tp_methods[];
  static PySequenceMethods as_sequence_;
  static PyNumberMethods as_number_;
  static auto tp_repr(PythonClassVec3* self) -> PyObject*;
  static auto sq_length(PythonClassVec3* self) -> Py_ssize_t;
  static auto sq_item(PythonClassVec3* self, Py_ssize_t i) -> PyObject*;
  static auto sq_ass_item(PythonClassVec3* self, Py_ssize_t i, PyObject* val)
      -> int;
  static auto nb_add(PythonClassVec3* l, PythonClassVec3* r) -> PyObject*;
  static auto nb_subtract(PythonClassVec3* l, PythonClassVec3* r) -> PyObject*;
  static auto nb_multiply(PyObject* l, PyObject* r) -> PyObject*;
  static auto nb_negative(PythonClassVec3* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto tp_getattro(PythonClassVec3* self, PyObject* attr) -> PyObject*;
  static auto tp_richcompare(PythonClassVec3* c1, PyObject* c2, int op)
      -> PyObject*;
  static auto tp_setattro(PythonClassVec3* self, PyObject* attr, PyObject* val)
      -> int;
};

}  // namespace ballistica::base
#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_VEC3_H_
