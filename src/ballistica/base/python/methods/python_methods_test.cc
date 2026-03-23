// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_test.h"

#include <vector>

#include "ballistica/shared/foundation/object_test.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica::base {

// Ignore signed bitwise warnings; Python macros trigger them.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

// ----------------------------- test_object ----------------------------------

static auto PyTestObject(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  RunObjectTests();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyTestObjectDef = {
    "test_object",                 // name
    (PyCFunction)PyTestObject,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "test_object() -> None\n"
    "\n"
    "Run C++ Object ref-count self-tests. Raises RuntimeError on failure.\n"
    "\n"
    ":meta private:",
};

// ----------------------------------------------------------------------------

auto PythonMethodsTest::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyTestObjectDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
