// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_BASE_TIMER_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_BASE_TIMER_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassBaseTimer : public PythonClass {
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
  static void tp_dealloc(PythonClassBaseTimer* self);
  int timer_id_;
  ContextRefSceneV1* context_ref_;
  bool have_timer_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_BASE_TIMER_H_
