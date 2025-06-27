// Released under the MIT License. See LICENSE for details.

#include "ballistica/template_fs/python/methods/python_methods_template_fs.h"

#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica::template_fs {

// -------------------------- hello_again_world --------------------------------

static auto PyHelloAgainWorld(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "", const_cast<char**>(kwlist),
                                   &name)) {
    return nullptr;
  }
  g_core->logging->Log(LogName::kBa, LogLevel::kInfo, "HELLO AGAIN WORLD!");
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHelloAgainWorldDef = {
    "hello_again_world",             // name
    (PyCFunction)PyHelloAgainWorld,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "hello_again_world() -> None\n"
    "\n"
    "Another hello world print.",
};

// -----------------------------------------------------------------------------

auto PythonMethodsTemplateFs::GetMethods() -> std::vector<PyMethodDef> {
  return {PyHelloAgainWorldDef};
}

}  // namespace ballistica::template_fs
