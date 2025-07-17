// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_CALL_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_CALL_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

class PythonClassContextCall : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_call(PythonClassContextCall* self, PyObject* args,
                      PyObject* keywds) -> PyObject*;
  static auto tp_repr(PythonClassContextCall* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassContextCall* self);
  Object::Ref<PythonContextCall>* context_call_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_CALL_H_
