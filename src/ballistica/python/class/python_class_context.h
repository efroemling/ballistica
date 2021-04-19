// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_H_

#include "ballistica/core/context.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassContext : public PythonClass {
 public:
  static auto type_name() -> const char* { return "Context"; }
  static void SetupType(PyTypeObject* obj);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto context() const -> const Context& { return *context_; }

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassContext* self) -> PyObject*;
  static auto tp_richcompare(PythonClassContext* c1, PyObject* c2, int op)
      -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassContext* self);
  static auto __enter__(PythonClassContext* self) -> PyObject*;
  static auto __exit__(PythonClassContext* self, PyObject* args) -> PyObject*;
  Context* context_;
  Context* context_prev_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_H_
