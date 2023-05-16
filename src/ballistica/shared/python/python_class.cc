// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/python/python_class.h"

#include "ballistica/shared/python/python.h"

namespace ballistica {

void PythonClass::SetupType(PyTypeObject* cls) {
  assert(Py_REFCNT(cls) == 0);

  PyTypeObject t = {PyVarObject_HEAD_INIT(nullptr, 0)};

  // Python samples use the initializer style above, but it fails
  // in g++ and sounds like it might not be allowed in c++ anyway,
  // ..so this is close enough...
  // (and still more readable than setting ALL values positionally)
  assert(t.tp_itemsize == 0);  // should all be zeroed though..
  t.tp_name = "babase.FixmeClassShouldOverride";
  t.tp_basicsize = sizeof(PythonClass);
  t.tp_itemsize = 0;
  t.tp_dealloc = (destructor)tp_dealloc;
  t.tp_getattro = (getattrofunc)tp_getattro;
  t.tp_setattro = (setattrofunc)tp_setattro;
  // NOLINTNEXTLINE (signed bitwise ops)
  t.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
  t.tp_doc = "A ballistica object.";
  t.tp_new = tp_new;

  memcpy(cls, &t, sizeof(t));
}

auto PythonClass::TypeIsSetUp(PyTypeObject* cls) -> bool {
  // Let's just look at its refcount.
  return Py_REFCNT(cls) > 0;
}

auto PythonClass::tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
    -> PyObject* {
  // Simply allocating and returning a zeroed instance of our class here.
  // If subclasses need to construct/destruct any other values in the object
  // they can either do it manually here and in tp_dealloc *or* they can get
  // fancy and use placement-new to allow arbitrary C++ stuff to live in the
  // class.
  auto* self = reinterpret_cast<PythonClass*>(type->tp_alloc(type, 0));
  return reinterpret_cast<PyObject*>(self);
}

void PythonClass::tp_dealloc(PythonClass* self) {
  // Vanilla Python deallocation.
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
