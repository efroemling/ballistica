// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_TIMER_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_TIMER_H_

#include "ballistica/ballistica.h"
#include "ballistica/python/class/python_class.h"
#include "ballistica/python/python.h"

namespace ballistica {

class PythonClassTimer : public PythonClass {
 public:
  static auto type_name() -> const char* { return "Timer"; }
  static void SetupType(PyTypeObject* obj);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;

 private:
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassTimer* self);
  static void DoDelete(bool have_timer, TimeType time_type, int timer_id,
                       Context* context);
  TimeType time_type_;
  int timer_id_;
  Context* context_;
  bool have_timer_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_TIMER_H_
