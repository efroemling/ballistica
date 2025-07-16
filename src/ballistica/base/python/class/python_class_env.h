// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_ENV_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_ENV_H_

#include <map>
#include <string>

#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

/// A simple example native class.
class PythonClassEnv : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto tp_getattro(PythonClassEnv* self, PyObject* attr) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong
  /// types.
  static auto FromPyObj(PyObject* o) -> PythonClassEnv& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassEnv*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  static PyTypeObject type_obj;

 private:
  PythonClassEnv();
  ~PythonClassEnv();
  std::map<std::string, PythonRef> extra_attrs_;
  static PyMethodDef tp_methods[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassEnv* self);
  static auto Dir(PythonClassEnv* self) -> PyObject*;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_ENV_H_
