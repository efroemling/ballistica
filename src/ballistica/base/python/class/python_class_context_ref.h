// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_REF_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_REF_H_

#include "ballistica/base/support/context.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

class PythonClassContextRef : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto context_ref() const -> const ContextRef& { return *context_ref_; }
  static auto Create(Context* context) -> PyObject*;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassContextRef* self) -> PyObject*;
  static auto tp_richcompare(PythonClassContextRef* c1, PyObject* c2, int op)
      -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassContextRef* self);
  static auto Enter(PythonClassContextRef* self) -> PyObject*;
  static auto Exit(PythonClassContextRef* self, PyObject* args) -> PyObject*;
  static auto Empty(PyObject* cls, PyObject* args) -> PyObject*;
  static auto IsEmpty(PythonClassContextRef* self) -> PyObject*;
  static auto IsExpired(PythonClassContextRef* self) -> PyObject*;
  ContextRef* context_ref_{};
  ContextRef* context_ref_prev_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_REF_H_
