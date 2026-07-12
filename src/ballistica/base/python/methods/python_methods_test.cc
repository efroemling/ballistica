// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_test.h"

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"
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

// ---------------------- get_text_line_break_offsets -------------------------

static auto PyGetTextLineBreakOffsets(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  const char* text;
  static const char* kwlist[] = {"text", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &text)) {
    return nullptr;
  }
  std::vector<int> offsets = g_core->platform->GetTextLineBreakOffsets(text);
  PyObject* list = PyList_New(static_cast<Py_ssize_t>(offsets.size()));
  for (size_t i = 0; i < offsets.size(); ++i) {
    PyList_SET_ITEM(list, static_cast<Py_ssize_t>(i),
                    PyLong_FromLong(offsets[i]));
  }
  return list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetTextLineBreakOffsetsDef = {
    "get_text_line_break_offsets",           // name
    (PyCFunction)PyGetTextLineBreakOffsets,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "get_text_line_break_offsets(text: str) -> list[int]\n"
    "\n"
    "Return utf-8 byte offsets where a new line may begin in some text.\n"
    "\n"
    "Uses the OS text stack's line-break analysis (UAX #14) where\n"
    "available; falls back to simple space-based breaks elsewhere\n"
    "(e.g. headless builds). Logic thread only.\n"
    "\n"
    ":meta private:",
};

// ----------------------------------------------------------------------------

auto PythonMethodsTest::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyTestObjectDef,
      PyGetTextLineBreakOffsetsDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
