// Released under the MIT License. See LICENSE for details.

#include "ballistica/squads/python/methods/python_methods_squads.h"

#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/python/python_macros.h"
#include "ballistica/squads/support/squads_app_mode.h"

namespace ballistica::squads {

// ------------------------ squads_app_mode_activate ---------------------------

static auto PySquadsAppModeActivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  g_base->set_app_mode(SquadsAppMode::GetSingleton());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySquadsAppModeActivateDef = {
    "squads_app_mode_activate",            // name
    (PyCFunction)PySquadsAppModeActivate,  // method
    METH_NOARGS,                           // flags

    "squads_app_mode_activate() -> None\n"
    "\n"
    "(internal)\n",
};

// ----------------------- squads_app_mode_deactivate --------------------------

static auto PySquadsAppModeDeactivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  // Currently doing nothing.
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySquadsAppModeDeactivateDef = {
    "squads_app_mode_deactivate",            // name
    (PyCFunction)PySquadsAppModeDeactivate,  // method
    METH_NOARGS,                             // flags

    "squads_app_mode_deactivate() -> None\n"
    "\n"
    "(internal)\n",
};

// -----------------------------------------------------------------------------

auto PythonMethodsSquads::GetMethods() -> std::vector<PyMethodDef> {
  return {PySquadsAppModeActivateDef, PySquadsAppModeDeactivateDef};
}

}  // namespace ballistica::squads
