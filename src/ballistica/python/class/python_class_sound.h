// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_SOUND_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_SOUND_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassSound : public PythonClass {
 public:
  static auto type_name() -> const char* { return "Sound"; }
  static PyTypeObject type_obj;
  static auto tp_repr(PythonClassSound* self) -> PyObject*;
  static void SetupType(PyTypeObject* obj);
  static auto Create(Sound* sound) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetSound(bool doraise = true) const -> Sound*;

 private:
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSound* self);
  static void Delete(Object::Ref<Sound>* ref);
  static bool s_create_empty_;
  Object::Ref<Sound>* sound_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_SOUND_H_
