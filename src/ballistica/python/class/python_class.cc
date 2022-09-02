// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class.h"

#include "ballistica/ballistica.h"
#include "ballistica/python/python.h"

namespace ballistica {

void PythonClass::SetupType(PyTypeObject* obj) {
  PyTypeObject t = {
      PyVarObject_HEAD_INIT(nullptr, 0)
      // .tp_name = "ba.Object",
      // .tp_basicsize = sizeof(PythonClass),
      // .tp_itemsize = 0,
      // .tp_dealloc = (destructor)tp_dealloc,
      // .tp_repr = (reprfunc)tp_repr,
      // .tp_getattro = (getattrofunc)tp_getattro,
      // .tp_setattro = (setattrofunc)tp_setattro,
      // .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
      // .tp_doc = "A ballistica object.",
      // .tp_new = tp_new,
  };

  // python samples use the initializer style above, but it fails
  // in g++ and sounds like it might not be allowed in c++ anyway,
  // ..so this is close enough...
  // (and still more readable than setting ALL values positionally)
  assert(t.tp_itemsize == 0);  // should all be zeroed though..
  t.tp_name = "ba.Object";
  t.tp_basicsize = sizeof(PythonClass);
  t.tp_itemsize = 0;
  t.tp_dealloc = (destructor)tp_dealloc;
  // t.tp_repr = (reprfunc)tp_repr;
  t.tp_getattro = (getattrofunc)tp_getattro;
  t.tp_setattro = (setattrofunc)tp_setattro;
  // NOLINTNEXTLINE (signed bitwise ops)
  t.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  t.tp_doc = "A ballistica object.";
  t.tp_new = tp_new;

  memcpy(obj, &t, sizeof(t));
}

auto PythonClass::tp_repr(PythonClass* self) -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("s", "<Ballistica Object>");
  BA_PYTHON_CATCH;
}
auto PythonClass::tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
    -> PyObject* {
  auto* self = reinterpret_cast<PythonClass*>(type->tp_alloc(type, 0));
  return reinterpret_cast<PyObject*>(self);
}
void PythonClass::tp_dealloc(PythonClass* self) {
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}
auto PythonClass::tp_getattro(PythonClass* node, PyObject* attr) -> PyObject* {
  BA_PYTHON_TRY;
  return PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(node), attr);
  BA_PYTHON_CATCH;
}
auto PythonClass::tp_setattro(PythonClass* node, PyObject* attr, PyObject* val)
    -> int {
  BA_PYTHON_TRY;
  return PyObject_GenericSetAttr(reinterpret_cast<PyObject*>(node), attr, val);
  BA_PYTHON_INT_CATCH;
}

}  // namespace ballistica
