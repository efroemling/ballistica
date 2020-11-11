// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_DATA_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_DATA_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassData : public PythonClass {
 public:
  static auto type_name() -> const char* { return "Data"; }
  static PyTypeObject type_obj;
  static auto tp_repr(PythonClassData* self) -> PyObject*;
  static void SetupType(PyTypeObject* obj);
  static auto Create(Data* data) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  auto GetData(bool doraise = true) const -> Data*;

 private:
  static PyMethodDef tp_methods[];
  static auto GetValue(PythonClassData* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClassData* self);
  static void Delete(Object::Ref<Data>* ref);
  static bool s_create_empty_;
  Object::Ref<Data>* data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_DATA_H_
