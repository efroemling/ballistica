// Released under the MIT License. See LICENSE for details.

#include "ballistica/remote/python/methods/python_methods_remote.h"

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/remote/support/remote_app_mode.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica::remote {

// ------------------------ remote_app_mode_activate ---------------------------

static auto PyRemoteAppModeActivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  g_base->set_app_mode(RemoteAppMode::GetSingleton());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRemoteAppModeActivateDef = {
    "remote_app_mode_activate",            // name
    (PyCFunction)PyRemoteAppModeActivate,  // method
    METH_NOARGS,                           // flags

    "remote_app_mode_activate() -> None\n"
    "\n"
    "(internal)\n",
};

// ----------------------- remote_app_mode_deactivate --------------------------

static auto PyRemoteAppModeDeactivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  // Currently doing nothing.
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRemoteAppModeDeactivateDef = {
    "remote_app_mode_deactivate",            // name
    (PyCFunction)PyRemoteAppModeDeactivate,  // method
    METH_NOARGS,                             // flags

    "remote_app_mode_deactivate() -> None\n"
    "\n"
    "(internal)\n",
};

// ------------------------- remote_set_connected ------------------------------

static auto PyRemoteSetConnected(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  int connected{};
  static const char* kwlist[] = {"connected", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &connected)) {
    return nullptr;
  }
  if (auto* mode = RemoteAppMode::GetActive()) {
    mode->SetConnected(static_cast<bool>(connected));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRemoteSetConnectedDef = {
    "remote_set_connected",             // name
    (PyCFunction)PyRemoteSetConnected,  // method
    METH_VARARGS | METH_KEYWORDS,       // flags

    "remote_set_connected(connected: bool) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Tell the remote app-mode whether its client is connected to a game\n"
    "(input devices count as attached, and touch controls show, while it\n"
    "is).",
};

// ----------------------- remote_set_input_callback ---------------------------

static auto PyRemoteSetInputCallback(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  PyObject* call{};
  static const char* kwlist[] = {"call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &call)) {
    return nullptr;
  }
  if (call != Py_None && !PyCallable_Check(call)) {
    throw Exception("Expected a callable or None.", PyExcType::kType);
  }
  if (auto* mode = RemoteAppMode::GetActive()) {
    mode->SetInputCallback(call);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRemoteSetInputCallbackDef = {
    "remote_set_input_callback",            // name
    (PyCFunction)PyRemoteSetInputCallback,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "remote_set_input_callback(call: Callable[[int, int, int], None] | None)"
    " -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Set the callable receiving controller state as (buttons, h, v) each\n"
    "time it changes while the remote app-mode is active.",
};

// -----------------------------------------------------------------------------

auto PythonMethodsRemote::GetMethods() -> std::vector<PyMethodDef> {
  return {PyRemoteAppModeActivateDef, PyRemoteAppModeDeactivateDef,
          PyRemoteSetConnectedDef, PyRemoteSetInputCallbackDef};
}

}  // namespace ballistica::remote
