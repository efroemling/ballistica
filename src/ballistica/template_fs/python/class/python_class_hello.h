// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_TEMPLATE_FS_PYTHON_CLASS_PYTHON_CLASS_HELLO_H_
#define BALLISTICA_TEMPLATE_FS_PYTHON_CLASS_PYTHON_CLASS_HELLO_H_

#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::template_fs {

/// A simple example native class.
class PythonClassHello : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong types.
  static auto FromPyObj(PyObject* o) -> PythonClassHello& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassHello*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  static PyTypeObject type_obj;

 private:
  PythonClassHello();
  ~PythonClassHello();
  static PyMethodDef tp_methods[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassHello* self);
  static auto TestMethod(PythonClassHello* self, PyObject* args,
                         PyObject* keywds) -> PyObject*;
};

}  // namespace ballistica::template_fs

#endif  // BALLISTICA_TEMPLATE_FS_PYTHON_CLASS_PYTHON_CLASS_HELLO_H_
