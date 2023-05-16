// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SESSION_DATA_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SESSION_DATA_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSessionData : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(Session* session) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetSession() const -> Session*;

 private:
  static PyMethodDef tp_methods[];
  static PyNumberMethods as_number_;
  static auto tp_repr(PythonClassSessionData* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSessionData* self);

  static auto Exists(PythonClassSessionData* self) -> PyObject*;
  static auto nb_bool(PythonClassSessionData* self) -> int;
  static auto Context(PythonClassSessionData* self) -> PyObject*;
  Object::WeakRef<Session>* session_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SESSION_DATA_H_
