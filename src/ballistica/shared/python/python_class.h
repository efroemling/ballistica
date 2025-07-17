// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_CLASS_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_CLASS_H_

#include "ballistica/shared/python/python_macros.h"

namespace ballistica {

// A convenient class for defining Python C types.
// Subclasses should include a static type object and can then
// provide/override whichever aspects of it they want.
// Be aware that if this class is added to multiple Python modules it will
// be considered the exact same type to Python since the static type object
// is the same for each.
class PythonClass {
 public:
  PyObject_HEAD;
  static void SetupType(PyTypeObject* cls);

  /// For sanity checking; to make sure classes aren't used before
  /// being inited.
  static auto TypeIsSetUp(PyTypeObject* cls) -> bool;

#pragma clang diagnostic push
#pragma ide diagnostic ignored "cppcoreguidelines-pro-type-member-init"
  // This ugly mess is just to define a constructor that does nothing.
  // Otherwise we get a default constructor that zeroes out the stuff in
  // PyObject_HEAD. Pretty much the only time our constructors actually fire is
  // if we're doing a placement-new on top of tp_alloc() results and in that
  // case we don't want to touch anything Python already set or we get a nice
  // crash.
  PythonClass() {}  // NOLINT(modernize-use-equals-default)
#pragma clang diagnostic pop

 private:
  static auto tp_repr(PythonClass* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
      -> PyObject*;
  static void tp_dealloc(PythonClass* self);
  static auto tp_getattro(PythonClass* node, PyObject* attr) -> PyObject*;
  static auto tp_setattro(PythonClass* node, PyObject* attr, PyObject* val)
      -> int;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_CLASS_H_
