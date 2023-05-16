// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_NODE_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_NODE_H_

#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassNode : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Create(Node* node) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;
  auto GetNode(bool doraise = true) const -> Node*;

 private:
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassNode* self);
  static auto tp_repr(PythonClassNode* self) -> PyObject*;
  static auto tp_getattro(PythonClassNode* self, PyObject* attr) -> PyObject*;
  static auto tp_setattro(PythonClassNode* self, PyObject* attr, PyObject* val)
      -> int;
  static auto Exists(PythonClassNode* self) -> PyObject*;
  static auto GetNodeType(PythonClassNode* self) -> PyObject*;
  static auto GetName(PythonClassNode* self) -> PyObject*;
  static auto GetDelegate(PythonClassNode* self, PyObject* args,
                          PyObject* keywds) -> PyObject*;
  static auto Delete(PythonClassNode* self, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto HandleMessage(PythonClassNode* self, PyObject* args) -> PyObject*;
  static auto AddDeathAction(PythonClassNode* self, PyObject* args)
      -> PyObject*;
  static auto ConnectAttr(PythonClassNode* self, PyObject* args) -> PyObject*;
  static auto Dir(PythonClassNode* self) -> PyObject*;
  static auto nb_bool(PythonClassNode* self) -> int;
  static bool s_create_empty_;
  static PyMethodDef tp_methods[];
  Object::WeakRef<Node>* node_;
  static PyNumberMethods as_number_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_NODE_H_
