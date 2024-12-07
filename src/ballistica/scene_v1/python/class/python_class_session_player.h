// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SESSION_PLAYER_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SESSION_PLAYER_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassSessionPlayer : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(Player* player) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetPlayer(bool doraise) const -> Player*;

 private:
  static bool s_create_empty_;
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassSessionPlayer* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSessionPlayer* self);
  static auto tp_getattro(PythonClassSessionPlayer* self, PyObject* attr)
      -> PyObject*;
  static auto tp_setattro(PythonClassSessionPlayer* self, PyObject* attr,
                          PyObject* val) -> int;
  static auto GetName(PythonClassSessionPlayer* self, PyObject* args,
                      PyObject* keywds) -> PyObject*;
  static auto Exists(PythonClassSessionPlayer* self) -> PyObject*;
  static auto SetName(PythonClassSessionPlayer* self, PyObject* args,
                      PyObject* keywds) -> PyObject*;
  static auto ResetInput(PythonClassSessionPlayer* self) -> PyObject*;
  static auto AssignInputCall(PythonClassSessionPlayer* self, PyObject* args,
                              PyObject* keywds) -> PyObject*;
  static auto RemoveFromGame(PythonClassSessionPlayer* self) -> PyObject*;
  static auto GetTeam(PythonClassSessionPlayer* self) -> PyObject*;
  static auto GetV1AccountID(PythonClassSessionPlayer* self) -> PyObject*;
  static auto SetData(PythonClassSessionPlayer* self, PyObject* args,
                      PyObject* keywds) -> PyObject*;
  static auto GetIconInfo(PythonClassSessionPlayer* self) -> PyObject*;
  static auto SetIconInfo(PythonClassSessionPlayer* self, PyObject* args,
                          PyObject* keywds) -> PyObject*;
  static auto SetActivity(PythonClassSessionPlayer* self, PyObject* args,
                          PyObject* keywds) -> PyObject*;
  static auto SetNode(PythonClassSessionPlayer* self, PyObject* args,
                      PyObject* keywds) -> PyObject*;
  static auto GetIcon(PythonClassSessionPlayer* self) -> PyObject*;
  static auto Dir(PythonClassSessionPlayer* self) -> PyObject*;
  Object::WeakRef<Player>* player_;
  static auto nb_bool(PythonClassSessionPlayer* self) -> int;
  static PyNumberMethods as_number_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SESSION_PLAYER_H_
