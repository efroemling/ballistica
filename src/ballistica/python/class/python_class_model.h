// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_MODEL_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_MODEL_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassModel : public PythonClass {
 public:
  static auto type_name() -> const char* { return "Model"; }
  static auto tp_repr(PythonClassModel* self) -> PyObject*;
  static void SetupType(PyTypeObject* obj);
  static PyTypeObject type_obj;
  static auto Create(Model* model) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetModel(bool doraise = true) const -> Model*;

 private:
  static bool s_create_empty_;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassModel* self);
  static void Delete(Object::Ref<Model>* ref);
  Object::Ref<Model>* model_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_MODEL_H_
