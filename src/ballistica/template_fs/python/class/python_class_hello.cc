// Released under the MIT License. See LICENSE for details.

#include "ballistica/template_fs/python/class/python_class_hello.h"

#include "ballistica/core/core.h"

using ballistica::core::g_core;

namespace ballistica::template_fs {

auto PythonClassHello::type_name() -> const char* { return "Hello"; }

void PythonClassHello::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "_batemplatefs.Hello";
  cls->tp_basicsize = sizeof(PythonClassHello);
  cls->tp_doc = "Simple example.";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_methods = tp_methods;
}

auto PythonClassHello::tp_new(PyTypeObject* type, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  auto* self = type->tp_alloc(type, 0);
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  // Being a bit fancy here and using placement-new on top of the
  // python-allocated memory. This lets C++-y parts of our class such as
  // constructors/destructors and embedded objects work as expected.
  new (self) PythonClassHello();
  return self;
  BA_PYTHON_NEW_CATCH;
}

void PythonClassHello::tp_dealloc(PythonClassHello* self) {
  BA_PYTHON_TRY;

  // Because we used placement-new, we need to manually run the equivalent
  // destructor to clean ourself up. Note that if anything goes wrong here
  // it'll simply print an error; we don't set any Python error state. Not
  // sure if that is ever even allowed from destructors anyway.

  // IMPORTANT: With Python objects we can't guarantee that this destructor
  // runs in a particular thread, so if that is something we need then we
  // should manually allocate stuff in tp_new and then ship a pointer off
  // from here to whatever thread needs to clean it up.
  self->~PythonClassHello();
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PythonClassHello::PythonClassHello() {
  core::g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                             "Hello from PythonClassHello constructor!!!");
}

PythonClassHello::~PythonClassHello() {
  g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                       "Goodbye from PythonClassHello destructor!!!");
}

auto PythonClassHello::TestMethod(PythonClassHello* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int val{};
  static const char* kwlist[] = {"val", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|i",
                                   const_cast<char**>(kwlist), &val)) {
    return nullptr;
  }
  g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                       "Hello from PythonClassHello.test_method!!! (val="
                           + std::to_string(val) + ")");
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassHello::type_obj;

// Any methods for our class go here.
PyMethodDef PythonClassHello::tp_methods[] = {
    {"testmethod", (PyCFunction)PythonClassHello::TestMethod,
     METH_VARARGS | METH_KEYWORDS,
     "testmethod(val: int = 0) -> None\n"
     "\n"
     "Just testing.\n"
     ""},

    {nullptr}};

}  // namespace ballistica::template_fs
