// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_TEXTURE_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_TEXTURE_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassTexture : public PythonClass {
 public:
  static auto type_name() -> const char* { return "Texture"; }
  static auto tp_repr(PythonClassTexture* self) -> PyObject*;
  static void SetupType(PyTypeObject* obj);
  static PyTypeObject type_obj;
  static auto Create(Texture* texture) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetTexture(bool doraise = true) const -> Texture*;

 private:
  static bool s_create_empty_;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassTexture* self);
  static void Delete(Object::Ref<Texture>* ref);
  Object::Ref<Texture>* texture_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_TEXTURE_H_
