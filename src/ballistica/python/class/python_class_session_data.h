// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_SESSION_DATA_H_
#define BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_SESSION_DATA_H_

#include "ballistica/core/object.h"
#include "ballistica/python/class/python_class.h"

namespace ballistica {

class PythonClassSessionData : public PythonClass {
 public:
  static auto type_name() -> const char* { return "SessionData"; }
  static void SetupType(PyTypeObject* obj);
  static auto Create(Session* session) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetSession() const -> Session*;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassSessionData* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSessionData* self);
  static auto Exists(PythonClassSessionData* self) -> PyObject*;
  Object::WeakRef<Session>* session_;
  static auto nb_bool(PythonClassSessionData* self) -> int;
  static PyNumberMethods as_number_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_CLASS_PYTHON_CLASS_SESSION_DATA_H_
