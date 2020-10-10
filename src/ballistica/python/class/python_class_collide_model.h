// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_COLLIDE_MODEL_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_COLLIDE_MODEL_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassCollideModel : public PythonClass {
 public:
  static auto type_name() -> const char* { return "CollideModel"; }
  static auto tp_repr(PythonClassCollideModel* self) -> PyObject*;
  static void SetupType(PyTypeObject* obj);
  static PyTypeObject type_obj;
  static auto Create(CollideModel* collide_model) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetCollideModel(bool doraise = true) const -> CollideModel*;

 private:
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void Delete(Object::Ref<CollideModel>* ref);
  static void tp_dealloc(PythonClassCollideModel* self);
  static bool s_create_empty_;
  Object::Ref<CollideModel>* collide_model_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_COLLIDE_MODEL_H_
