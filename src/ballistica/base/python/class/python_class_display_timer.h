// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_DISPLAY_TIMER_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_DISPLAY_TIMER_H_

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

class PythonClassDisplayTimer : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;

 private:
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassDisplayTimer* self);
  int timer_id_;
  bool have_timer_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_DISPLAY_TIMER_H_
