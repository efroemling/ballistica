// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_H_

#include "ballistica/python/python_sys.h"

namespace ballistica {

// a convenient base class for defining custom python types
class PythonClass {
 public:
  PyObject_HEAD;
  static void SetupType(PyTypeObject* obj);

 private:
  static auto tp_repr(PythonClass* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClass* self);
  static auto tp_getattro(PythonClass* node, PyObject* attr) -> PyObject*;
  static auto tp_setattro(PythonClass* node, PyObject* attr, PyObject* val)
      -> int;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_H_
