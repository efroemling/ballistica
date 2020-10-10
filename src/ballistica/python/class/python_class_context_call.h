// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_CALL_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_CALL_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassContextCall : public PythonClass {
 public:
  static auto type_name() -> const char* { return "ContextCall"; }
  static void SetupType(PyTypeObject* obj);
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
  Object::Ref<PythonContextCall>* context_call_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_CONTEXT_CALL_H_
