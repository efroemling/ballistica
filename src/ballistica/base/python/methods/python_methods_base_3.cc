// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_base_3.h"

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/assets/sound_asset.h"  // IWYU pragma: keep.
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_simple_sound.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/native_stack_trace.h"  // IWYU pragma: keep.
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

// Ignore signed bitwise warnings; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

// ---------------------------- getsimplesound --------------------------------

static auto PyGetSimpleSound(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  BA_PRECONDITION(g_base->assets->asset_loads_allowed());
  {
    Assets::AssetListLock lock;
    return PythonClassSimpleSound::Create(g_base->assets->GetSound(name));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSimpleSoundDef = {
    "getsimplesound",               // name
    (PyCFunction)PyGetSimpleSound,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "getsimplesound(name: str) -> SimpleSound\n"
    "\n"
    "(internal).",
};

// -------------------------- set_ui_input_device ------------------------------

static auto PySetUIInputDevice(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  static const char* kwlist[] = {"input_device_id", nullptr};
  PyObject* input_device_id_obj = Py_None;
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist),
                                   &input_device_id_obj)) {
    return nullptr;
  }
  InputDevice* device{};
  if (input_device_id_obj != Py_None) {
    device =
        g_base->input->GetInputDevice(Python::GetPyInt(input_device_id_obj));
    if (!device) {
      throw Exception("Invalid input-device id.");
    }
  }
  g_base->ui->SetUIInputDevice(device);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetUIInputDeviceDef = {
    "set_ui_input_device",            // name
    (PyCFunction)PySetUIInputDevice,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "set_ui_input_device(input_device_id: int | None)"
    " -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Sets the input-device that currently owns the user interface.",
};

// ------------------------------ set_ui_scale ---------------------------------

static auto PySetUIScale(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  const char* scalestr;

  static const char* kwlist[] = {"scale", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &scalestr)) {
    return nullptr;
  }

  // FIXME: Should have this take an enum directly once we have an easy way
  // to share enums between Python/CPP.
  UIScale scale;
  if (!strcmp(scalestr, "small")) {
    scale = UIScale::kSmall;
  } else if (!strcmp(scalestr, "medium")) {
    scale = UIScale::kMedium;
  } else if (!strcmp(scalestr, "large")) {
    scale = UIScale::kLarge;
  } else {
    throw Exception("Invalid scale value.", PyExcType::kValue);
  }
  g_base->SetUIScale(scale);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetUIScaleDef = {
    "set_ui_scale",                // name
    (PyCFunction)PySetUIScale,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "set_ui_scale(scale: str)"
    " -> None\n"
    "\n"
    "(internal)\n",
};
// ------------------------------ set_ui_scale ---------------------------------

static auto PyGetUIScale(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  // FIXME: Should have this return enums directly once we have an easy way
  // to share enums between Python/CPP.
  auto scale = g_base->ui->scale();

  const char* val;
  switch (scale) {
    case UIScale::kSmall:
      val = "small";
      break;
    case UIScale::kMedium:
      val = "medium";
      break;
    case UIScale::kLarge:
      val = "large";
      break;
    default:
      throw Exception("Unhandled scale value.");
  }
  return PyUnicode_FromString(val);

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetUIScaleDef = {
    "get_ui_scale",             // name
    (PyCFunction)PyGetUIScale,  // method
    METH_NOARGS,                // flags

    "get_ui_scale()"
    " -> str\n"
    "\n"
    "(internal)\n",
};

// ----------------------------- hastouchscreen --------------------------------

static auto PyHasTouchScreen(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  if (g_base && g_base->input->touch_input() != nullptr) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHasTouchScreenDef = {
    "hastouchscreen",               // name
    (PyCFunction)PyHasTouchScreen,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "hastouchscreen() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return whether a touchscreen is present on the current device.",
};

// ------------------------- clipboard_is_supported ----------------------------

static auto PyClipboardIsSupported(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->ClipboardIsSupported()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClipboardIsSupportedDef = {
    "clipboard_is_supported",             // name
    (PyCFunction)PyClipboardIsSupported,  // method
    METH_NOARGS,                          // flags

    "clipboard_is_supported() -> bool\n"
    "\n"
    "Return whether this platform supports clipboard operations at all.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "If this returns False, UIs should not show 'copy to clipboard'\n"
    "buttons, etc.",
};

// --------------------------- clipboard_has_text ------------------------------

static auto PyClipboardHasText(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->ClipboardHasText()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClipboardHasTextDef = {
    "clipboard_has_text",             // name
    (PyCFunction)PyClipboardHasText,  // method
    METH_NOARGS,                      // flags

    "clipboard_has_text() -> bool\n"
    "\n"
    "Return whether there is currently text on the clipboard.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "This will return False if no system clipboard is available; no need\n"
    " to call babase.clipboard_is_supported() separately.",
};

// --------------------------- clipboard_set_text ------------------------------

static auto PyClipboardSetText(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* value;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }
  g_base->ClipboardSetText(value);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClipboardSetTextDef = {
    "clipboard_set_text",             // name
    (PyCFunction)PyClipboardSetText,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "clipboard_set_text(value: str) -> None\n"
    "\n"
    "Copy a string to the system clipboard.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Ensure that babase.clipboard_is_supported() returns True before adding\n"
    " buttons/etc. that make use of this functionality.",
};

// --------------------------- clipboard_get_text ------------------------------

static auto PyClipboardGetText(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  return PyUnicode_FromString(g_base->ClipboardGetText().c_str());
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClipboardGetTextDef = {
    "clipboard_get_text",             // name
    (PyCFunction)PyClipboardGetText,  // method
    METH_NOARGS,                      // flags

    "clipboard_get_text() -> str\n"
    "\n"
    "Return text currently on the system clipboard.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Ensure that babase.clipboard_has_text() returns True before calling\n"
    " this function.",
};

// ------------------------------ setup_sigint ---------------------------------

static auto PySetUpSigInt(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base) {
    g_base->platform->SetupInterruptHandling();
  } else {
    g_core->Log(LogName::kBa, LogLevel::kError,
                "setup_sigint called before g_base exists.");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetUpSigIntDef = {
    "setup_sigint",              // name
    (PyCFunction)PySetUpSigInt,  // method
    METH_NOARGS,                 // flags

    "setup_sigint() -> None\n"
    "\n"
    "(internal)",
};

// ---------------------------- have_permission --------------------------------

static auto PyHavePermission(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  Permission permission;
  PyObject* permission_obj;
  static const char* kwlist[] = {"permission", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &permission_obj)) {
    return nullptr;
  }

  permission = BasePython::GetPyEnum_Permission(permission_obj);

  if (g_core->platform->HavePermission(permission)) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHavePermissionDef = {
    "have_permission",              // name
    (PyCFunction)PyHavePermission,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "have_permission(permission: babase.Permission) -> bool\n"
    "\n"
    "(internal)",
};

// --------------------------- request_permission ------------------------------

static auto PyRequestPermission(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  Permission permission;
  PyObject* permission_obj;
  static const char* kwlist[] = {"permission", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &permission_obj)) {
    return nullptr;
  }

  permission = BasePython::GetPyEnum_Permission(permission_obj);
  g_core->platform->RequestPermission(permission);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRequestPermissionDef = {
    "request_permission",              // name
    (PyCFunction)PyRequestPermission,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "request_permission(permission: babase.Permission) -> None\n"
    "\n"
    "(internal)",
};

// ----------------------------- in_logic_thread -------------------------------

static auto PyInLogicThread(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (g_base->InLogicThread()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyInLogicThreadDef = {
    "in_logic_thread",             // name
    (PyCFunction)PyInLogicThread,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "in_logic_thread() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns whether or not the current thread is the logic thread.",
};

// ------------------------------ in_main_menu ---------------------------------

static auto PyInMainMenu(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  if (g_base->app_mode()->IsInMainMenu()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyInMainMenuDef = {
    "in_main_menu",                // name
    (PyCFunction)PyInMainMenu,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "in_main_menu() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns whether or not the app-mode is currently in a main menu\n"
    "situation (as opposed to gameplay).",
};

// ----------------------------- set_thread_name -------------------------------

static auto PySetThreadName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  g_core->platform->SetCurrentThreadName(name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetThreadNameDef = {
    "set_thread_name",             // name
    (PyCFunction)PySetThreadName,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "set_thread_name(name: str) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Sets the name of the current thread (on platforms where this is\n"
    "available). EventLoop names are only for debugging and should\n"
    "not be used in logic, as naming behavior can vary across platforms.\n",
};

// ------------------------------ get_thread_name ------------------------------

static auto PyGetThreadName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(CurrentThreadName().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetThreadNameDef = {
    "get_thread_name",             // name
    (PyCFunction)PyGetThreadName,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_thread_name() -> str\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns the name of the current thread.\n"
    "This may vary depending on platform and should not be used in logic;\n"
    "only for debugging.",
};

// --------------------------------- ehv ---------------------------------------

// Returns an extra hash value that can be incorporated into security
// checks; this contains things like whether console commands have been run,
// etc.
auto PyExtraHashValue(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  const char* h =
      ((g_core->user_ran_commands || g_core->workspaces_in_use) ? "cjief3l"
                                                                : "wofocj8");
  return PyUnicode_FromString(h);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyExtraHashValueDef = {
    "ehv",                          // name
    (PyCFunction)PyExtraHashValue,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "ehv() -> None\n"
    "\n"
    "(internal)",
};

// ----------------------------- get_idle_time ---------------------------------

static auto PyGetIdleTime(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  return PyLong_FromLong(static_cast_check_fit<long>(  // NOLINT
      g_base->input ? g_base->input->input_idle_time() : 0));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetIdleTimeDef = {
    "get_idle_time",  // name
    PyGetIdleTime,    // method
    METH_VARARGS,     // flags
    "get_idle_time() -> int\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns the amount of time since any game input has been received.",
};

// ------------------------- has_user_run_commands -----------------------------

static auto PyHasUserRunCommands(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_core->user_ran_commands) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHasUserRunCommandsDef = {
    "has_user_run_commands",  // name
    PyHasUserRunCommands,     // method
    METH_VARARGS,             // flags
    "has_user_run_commands() -> bool\n"
    "\n"
    "(internal)",
};

// ---------------------------- workspaces_in_use ------------------------------

static auto PyWorkspacesInUse(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_core->workspaces_in_use) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyWorkspacesInUseDef = {
    "workspaces_in_use",  // name
    PyWorkspacesInUse,    // method
    METH_VARARGS,         // flags
    "workspaces_in_use() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns whether workspaces functionality has been enabled at\n"
    "any point this run.",
};

// ------------------------- contains_python_dist ------------------------------

static auto PyContainsPythonDist(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.contains_python_dist()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyContainsPythonDistDef = {
    "contains_python_dist",  // name
    PyContainsPythonDist,    // method
    METH_VARARGS,            // flags
    "contains_python_dist() -> bool\n"
    "\n"
    "(internal)",
};

// ------------------------- debug_print_py_err --------------------------------

static auto PyDebugPrintPyErr(PyObject* self, PyObject* args) -> PyObject* {
  if (PyErr_Occurred()) {
    // We pass zero here to avoid grabbing references to this exception
    // which can cause objects to stick around and trip up our deletion
    // checks (nodes, actors existing after their games have ended).
    PyErr_PrintEx(0);
    PyErr_Clear();
  }
  Py_RETURN_NONE;
}

static PyMethodDef PyDebugPrintPyErrDef = {
    "debug_print_py_err",  // name
    PyDebugPrintPyErr,     // method
    METH_VARARGS,          // flags

    "debug_print_py_err() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Debugging func for tracking leaked Python errors in the C++ layer.",
};

// ----------------------------- print_context ---------------------------------

static auto PyPrintContext(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  Python::PrintContextAuto();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPrintContextDef = {
    "print_context",               // name
    (PyCFunction)PyPrintContext,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "print_context() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Prints info about the current context_ref state; for debugging.\n",
};

// --------------------------- print_load_info ---------------------------------

static auto PyPrintLoadInfo(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_base->assets->PrintLoadInfo();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPrintLoadInfoDef = {
    "print_load_info",             // name
    (PyCFunction)PyPrintLoadInfo,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "print_load_info() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Category: **General Utility Functions**",
};

// -------------------------- get_replays_dir ----------------------------------

static auto PyGetReplaysDir(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(g_core->platform->GetReplaysDir().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetReplaysDirDef = {
    "get_replays_dir",             // name
    (PyCFunction)PyGetReplaysDir,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_replays_dir() -> str\n"
    "\n"
    "(internal)",
};

// --------------------- get_appconfig_default_value ---------------------------

static auto PyGetAppConfigDefaultValue(PyObject* self, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* key = "";
  static const char* kwlist[] = {"key", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &key)) {
    return nullptr;
  }
  const AppConfig::Entry* entry = g_base->app_config->GetEntry(key);
  if (entry == nullptr) {
    throw Exception("Invalid config value '" + std::string(key) + "'",
                    PyExcType::kValue);
  }
  switch (entry->GetType()) {
    case AppConfig::Entry::Type::kString:
      return PyUnicode_FromString(entry->DefaultStringValue().c_str());
    case AppConfig::Entry::Type::kInt:
      return PyLong_FromLong(entry->DefaultIntValue());
    case AppConfig::Entry::Type::kFloat:
      return PyFloat_FromDouble(entry->DefaultFloatValue());
    case AppConfig::Entry::Type::kBool:
      if (entry->DefaultBoolValue()) {
        Py_RETURN_TRUE;
      }
      Py_RETURN_FALSE;
    default:
      throw Exception(PyExcType::kValue);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetAppConfigDefaultValueDef = {
    "get_appconfig_default_value",            // name
    (PyCFunction)PyGetAppConfigDefaultValue,  // method
    METH_VARARGS | METH_KEYWORDS,             // flags

    "get_appconfig_default_value(key: str) -> Any\n"
    "\n"
    "(internal)",
};

// ---------------------- get_appconfig_builtin_keys ---------------------------

static auto PyAppConfigGetBuiltinKeys(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  PythonRef list(PyList_New(0), PythonRef::kSteal);
  for (auto&& i : g_base->app_config->entries_by_name()) {
    PyList_Append(list.get(), PyUnicode_FromString(i.first.c_str()));
  }
  return list.HandOver();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppConfigGetBuiltinKeysDef = {
    "get_appconfig_builtin_keys",            // name
    (PyCFunction)PyAppConfigGetBuiltinKeys,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "get_appconfig_builtin_keys() -> list[str]\n"
    "\n"
    "(internal)",
};

// ---------------------- resolve_appconfig_value ------------------------------

static auto PyResolveAppConfigValue(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  const char* key;
  static const char* kwlist[] = {"key", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &key)) {
    return nullptr;
  }
  auto entry = g_base->app_config->GetEntry(key);
  if (entry == nullptr) {
    throw Exception("Invalid config value '" + std::string(key) + "'.",
                    PyExcType::kValue);
  }
  switch (entry->GetType()) {
    case AppConfig::Entry::Type::kString:
      return PyUnicode_FromString(entry->StringValue().c_str());
    case AppConfig::Entry::Type::kInt:
      return PyLong_FromLong(entry->IntValue());
    case AppConfig::Entry::Type::kFloat:
      return PyFloat_FromDouble(entry->FloatValue());
    case AppConfig::Entry::Type::kBool:
      if (entry->BoolValue()) {
        Py_RETURN_TRUE;
      }
      Py_RETURN_FALSE;

    default:
      throw Exception(PyExcType::kValue);
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyResolveAppConfigValueDef = {
    "resolve_appconfig_value",             // name
    (PyCFunction)PyResolveAppConfigValue,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "resolve_appconfig_value(key: str) -> Any\n"
    "\n"
    "(internal)",
};

// --------------------- get_low_level_config_value ----------------------------

static auto PyGetLowLevelConfigValue(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* key;
  int default_value;
  static const char* kwlist[] = {"key", "default_value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "si", const_cast<char**>(kwlist), &key, &default_value))
    return nullptr;
  return PyLong_FromLong(
      g_core->platform->GetLowLevelConfigValue(key, default_value));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetLowLevelConfigValueDef = {
    "get_low_level_config_value",           // name
    (PyCFunction)PyGetLowLevelConfigValue,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "get_low_level_config_value(key: str, default_value: int) -> int\n"
    "\n"
    "(internal)",
};

// --------------------- set_low_level_config_value ----------------------------

static auto PySetLowLevelConfigValue(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* key;
  int value;
  static const char* kwlist[] = {"key", "value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "si",
                                   const_cast<char**>(kwlist), &key, &value))
    return nullptr;
  g_core->platform->SetLowLevelConfigValue(key, value);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetLowLevelConfigValueDef = {
    "set_low_level_config_value",           // name
    (PyCFunction)PySetLowLevelConfigValue,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "set_low_level_config_value(key: str, value: int) -> None\n"
    "\n"
    "(internal)",
};

// --------------------- set_platform_misc_read_vals ---------------------------

static auto PySetPlatformMiscReadVals(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* vals_obj;
  static const char* kwlist[] = {"mode", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &vals_obj)) {
    return nullptr;
  }
  std::string vals = g_base->python->GetPyLString(vals_obj);
  g_core->platform->SetPlatformMiscReadVals(vals);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPlatformMiscReadValsDef = {
    "set_platform_misc_read_vals",           // name
    (PyCFunction)PySetPlatformMiscReadVals,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "set_platform_misc_read_vals(mode: str) -> None\n"
    "\n"
    "(internal)",
};

// --------------------- get_v1_cloud_log_file_path ----------------------------

static auto PyGetLogFilePath(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  std::string config_dir = g_core->GetConfigDirectory();
  std::string logpath = config_dir + BA_DIRSLASH + "log.json";
  return PyUnicode_FromString(logpath.c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetLogFilePathDef = {
    "get_v1_cloud_log_file_path",  // name
    PyGetLogFilePath,              // method
    METH_VARARGS,                  // flags

    "get_v1_cloud_log_file_path() -> str\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the path to the app log file.",
};

// --------------------- get_volatile_data_directory ---------------------------

static auto PyGetVolatileDataDirectory(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  return PyUnicode_FromString(
      g_core->platform->GetVolatileDataDirectory().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetVolatileDataDirectoryDef = {
    "get_volatile_data_directory",  // name
    PyGetVolatileDataDirectory,     // method
    METH_VARARGS,                   // flags

    "get_volatile_data_directory() -> str\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the path to the app volatile data directory.\n"
    "This directory is for data generated by the app that does not\n"
    "need to be backed up and can be recreated if necessary.",
};

// ----------------------------- is_log_full -----------------------------------
static auto PyIsLogFull(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_core->v1_cloud_log_full) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIsLogFullDef = {
    "is_log_full",  // name
    PyIsLogFull,    // method
    METH_VARARGS,   // flags

    "is_log_full() -> bool\n"
    "\n"
    "(internal)",
};

// -------------------------- get_v1_cloud_log ---------------------------------

static auto PyGetV1CloudLog(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string log_fin;
  {
    std::scoped_lock lock(g_core->v1_cloud_log_mutex);
    log_fin = g_core->v1_cloud_log;
  }
  // we want to use something with error handling here since the last
  // bit of this string could be truncated utf8 chars..
  return PyUnicode_FromString(
      Utils::GetValidUTF8(log_fin.c_str(), "_glg1").c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetV1CloudLogDef = {
    "get_v1_cloud_log",            // name
    (PyCFunction)PyGetV1CloudLog,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_v1_cloud_log() -> str\n"
    "\n"
    "(internal)",
};

// ---------------------------- mark_log_sent ----------------------------------

static auto PyMarkLogSent(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  // This way we won't try to send it at shutdown time and whatnot
  g_core->did_put_v1_cloud_log = true;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMarkLogSentDef = {
    "mark_log_sent",               // name
    (PyCFunction)PyMarkLogSent,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "mark_log_sent() -> None\n"
    "\n"
    "(internal)",
};

// --------------------- increment_analytics_count -----------------------------

auto PyIncrementAnalyticsCount(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  int increment = 1;
  static const char* kwlist[] = {"name", "increment", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|p", const_cast<char**>(kwlist), &name, &increment))
    g_core->platform->IncrementAnalyticsCount(name, increment);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIncrementAnalyticsCountDef = {
    "increment_analytics_count",             // name
    (PyCFunction)PyIncrementAnalyticsCount,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "increment_analytics_count(name: str, increment: int = 1) -> None\n"
    "\n"
    "(internal)",
};

// -------------------- increment_analytics_count_raw --------------------------

static auto PyIncrementAnalyticsCountRaw(PyObject* self, PyObject* args,
                                         PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  int increment = 1;
  static const char* kwlist[] = {"name", "increment", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|i", const_cast<char**>(kwlist), &name, &increment))
    g_core->platform->IncrementAnalyticsCountRaw(name, increment);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIncrementAnalyticsCountRawDef = {
    "increment_analytics_counts_raw",           // name
    (PyCFunction)PyIncrementAnalyticsCountRaw,  // method
    METH_VARARGS | METH_KEYWORDS,               // flags

    "increment_analytics_counts_raw(name: str, increment: int = 1) -> None\n"
    "\n"
    "(internal)",
};

// ------------------- increment_analytics_count_raw_2 -------------------------

static auto PyIncrementAnalyticsCountRaw2(PyObject* self, PyObject* args,
                                          PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  int uses_increment = 1;
  int increment = 1;
  static const char* kwlist[] = {"name", "uses_increment", "increment",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s|ii",
                                   const_cast<char**>(kwlist), &name,
                                   &uses_increment, &increment)) {
    return nullptr;
  }
  g_core->platform->IncrementAnalyticsCountRaw2(name, uses_increment,
                                                increment);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIncrementAnalyticsCountRaw2Def = {
    "increment_analytics_count_raw_2",           // name
    (PyCFunction)PyIncrementAnalyticsCountRaw2,  // method
    METH_VARARGS | METH_KEYWORDS,                // flags

    "increment_analytics_count_raw_2(name: str,\n"
    "  uses_increment: bool = True, increment: int = 1) -> None\n"
    "\n"
    "(internal)",
};

// ---------------------- submit_analytics_counts ------------------------------

static auto PySubmitAnalyticsCounts(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  g_core->platform->SubmitAnalyticsCounts();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySubmitAnalyticsCountsDef = {
    "submit_analytics_counts",             // name
    (PyCFunction)PySubmitAnalyticsCounts,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "submit_analytics_counts() -> None\n"
    "\n"
    "(internal)",
};

// ------------------------- set_analytics_screen ------------------------------

static auto PySetAnalyticsScreen(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* screen;
  static const char* kwlist[] = {"screen", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &screen)) {
    return nullptr;
  }
  g_core->platform->SetAnalyticsScreen(screen);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetAnalyticsScreenDef = {
    "set_analytics_screen",             // name
    (PyCFunction)PySetAnalyticsScreen,  // method
    METH_VARARGS | METH_KEYWORDS,       // flags

    "set_analytics_screen(screen: str) -> None\n"
    "\n"
    "Used for analytics to see where in the app players spend their time.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Generally called when opening a new window or entering some UI.\n"
    "'screen' should be a string description of an app location\n"
    "('Main Menu', etc.)",
};

// ------------------ login_adapter_get_sign_in_token --------------------------

static auto PyLoginAdapterGetSignInToken(PyObject* self, PyObject* args,
                                         PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* login_type;
  int attempt_id;
  static const char* kwlist[] = {"login_type", "attempt_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "si",
                                   const_cast<char**>(kwlist), &login_type,
                                   &attempt_id)) {
    return nullptr;
  }
  g_base->platform->LoginAdapterGetSignInToken(login_type, attempt_id);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyLoginAdapterGetSignInTokenDef = {
    "login_adapter_get_sign_in_token",          // name
    (PyCFunction)PyLoginAdapterGetSignInToken,  // method
    METH_VARARGS | METH_KEYWORDS,               // flags

    "login_adapter_get_sign_in_token(login_type: str, attempt_id: int)"
    " -> None\n"
    "\n"
    "(internal)",
};

// ----------------- login_adapter_back_end_active_change ----------------------

static auto PyLoginAdapterBackEndActiveChange(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* login_type;
  int active;
  static const char* kwlist[] = {"login_type", "active", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sp",
                                   const_cast<char**>(kwlist), &login_type,
                                   &active)) {
    return nullptr;
  }
  g_base->platform->LoginAdapterBackEndActiveChange(login_type, active);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyLoginAdapterBackEndActiveChangeDef = {
    "login_adapter_back_end_active_change",          // name
    (PyCFunction)PyLoginAdapterBackEndActiveChange,  // method
    METH_VARARGS | METH_KEYWORDS,                    // flags

    "login_adapter_back_end_active_change(login_type: str, active: bool)"
    " -> None\n"
    "\n"
    "(internal)",
};

// ---------------------- set_internal_language_keys ---------------------------

static auto PySetInternalLanguageKeys(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* list_obj;
  PyObject* random_names_list_obj;
  if (!PyArg_ParseTuple(args, "OO", &list_obj, &random_names_list_obj)) {
    return nullptr;
  }
  BA_PRECONDITION(PyList_Check(list_obj));
  BA_PRECONDITION(PyList_Check(random_names_list_obj));
  std::unordered_map<std::string, std::string> language;
  int size = static_cast<int>(PyList_GET_SIZE(list_obj));

  for (int i = 0; i < size; i++) {
    PyObject* entry = PyList_GET_ITEM(list_obj, i);
    if (!PyTuple_Check(entry) || PyTuple_GET_SIZE(entry) != 2
        || !PyUnicode_Check(PyTuple_GET_ITEM(entry, 0))
        || !PyUnicode_Check(PyTuple_GET_ITEM(entry, 1))) {
      throw Exception("Invalid root language data.");
    }
    language[PyUnicode_AsUTF8(PyTuple_GET_ITEM(entry, 0))] =
        PyUnicode_AsUTF8(PyTuple_GET_ITEM(entry, 1));
  }

  size = static_cast<int>(PyList_GET_SIZE(random_names_list_obj));
  std::list<std::string> random_names;
  for (int i = 0; i < size; i++) {
    PyObject* entry = PyList_GET_ITEM(random_names_list_obj, i);
    if (!PyUnicode_Check(entry)) {
      throw Exception("Got non-string in random name list.", PyExcType::kType);
    }
    random_names.emplace_back(PyUnicode_AsUTF8(entry));
  }

  Utils::SetRandomNameList(random_names);
  assert(g_base->logic);
  g_base->assets->SetLanguageKeys(language);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetInternalLanguageKeysDef = {
    "set_internal_language_keys",  // name
    PySetInternalLanguageKeys,     // method
    METH_VARARGS,                  // flags

    "set_internal_language_keys(listobj: list[tuple[str, str]],\n"
    "  random_names_list: list[tuple[str, str]]) -> None\n"
    "\n"
    "(internal)",
};

// -------------------- android_get_external_files_dir -------------------------

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantFunctionResult"

static auto PyAndroidGetExternalFilesDir(PyObject* self, PyObject* args,
                                         PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (g_buildconfig.ostype_android()) {
    std::string path = g_core->platform->AndroidGetExternalFilesDir();
    if (path.empty()) {
      Py_RETURN_NONE;
    } else {
      assert(Utils::IsValidUTF8(path));
      return PyUnicode_FromString(path.c_str());
    }
  } else {
    throw Exception("Only valid on android.");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAndroidGetExternalFilesDirDef = {
    "android_get_external_files_dir",           // name
    (PyCFunction)PyAndroidGetExternalFilesDir,  // method
    METH_VARARGS | METH_KEYWORDS,               // flags

    "android_get_external_files_dir() -> str\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns the android external storage path, or None if there is none "
    "on\n"
    "this device",
};

#pragma clang diagnostic pop

// ------------------------------- do_once -------------------------------------

static auto PyDoOnce(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->python->DoOnce()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDoOnceDef = {
    "do_once",                     // name
    (PyCFunction)PyDoOnce,         // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "do_once() -> bool\n"
    "\n"
    "Return whether this is the first time running a line of code.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "This is used by 'print_once()' type calls to keep from overflowing\n"
    "logs. The call functions by registering the filename and line where\n"
    "The call is made from.  Returns True if this location has not been\n"
    "registered already, and False if it has.\n"
    "\n"
    "##### Example\n"
    "This print will only fire for the first loop iteration:\n"
    ">>> for i in range(10):\n"
    "... if babase.do_once():\n"
    "...     print('HelloWorld once from loop!')",
};

// ------------------------------- getapp --------------------------------------

static auto PyGetApp(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return g_base->python->objs().Get(BasePython::ObjID::kApp).NewRef();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetAppDef = {
    "getapp",                      // name
    (PyCFunction)PyGetApp,         // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getapp() -> babase.App\n"
    "\n"
    "(internal)",
};

// ------------------------------ lock_all_input -------------------------------

static auto PyLockAllInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  assert(g_base->input);
  g_base->input->LockAllInput(false, Python::GetPythonFileLocation());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyLockAllInputDef = {
    "lock_all_input",  // name
    PyLockAllInput,    // method
    METH_VARARGS,      // flags

    "lock_all_input() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Prevents all keyboard, mouse, and gamepad events from being "
    "processed.",
};

// ---------------------------- unlock_all_input -------------------------------

static auto PyUnlockAllInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  assert(g_base->input);
  g_base->input->UnlockAllInput(false, Python::GetPythonFileLocation());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUnlockAllInputDef = {
    "unlock_all_input",  // name
    PyUnlockAllInput,    // method
    METH_VARARGS,        // flags

    "unlock_all_input() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Resumes normal keyboard, mouse, and gamepad event processing.",
};

// --------------------------- native_stack_trace ------------------------------

static auto PyNativeStackTrace(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_core);
  auto* trace = g_core->platform->GetNativeStackTrace();
  if (!trace) {
    Py_RETURN_NONE;
  }
  auto out = trace->FormatForDisplay();
  delete trace;
  return PyUnicode_FromString(out.c_str());
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNativeStackTraceDef = {
    "native_stack_trace",             // name
    (PyCFunction)PyNativeStackTrace,  // method
    METH_NOARGS,                      // flags

    "native_stack_trace() -> str | None\n"
    "\n"
    "Return a native stack trace as a string, or None if not available.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Stack traces contain different data and formatting across platforms.\n"
    "Only use them for debugging.",
};

// --------------------- supports_open_dir_externally --------------------------

static auto PySupportsOpenDirExternally(PyObject* self, PyObject* args,
                                        PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->platform->SupportsOpenDirExternally()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySupportsOpenDirExternallyDef = {
    "supports_open_dir_externally",            // name
    (PyCFunction)PySupportsOpenDirExternally,  // method
    METH_NOARGS,                               // flags

    "supports_open_dir_externally() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return whether the current app/platform supports opening dirs externally\n"
    "(in the Mac Finder, Windows Explorer, etc.).",
};

// -------------------------- open_dir_externally ------------------------------

static auto PyOpenDirExternally(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  char* path = nullptr;
  static const char* kwlist[] = {"path", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &path)) {
    return nullptr;
  }
  g_base->platform->OpenDirExternally(path);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOpenDirExternallyDef = {
    "open_dir_externally",             // name
    (PyCFunction)PyOpenDirExternally,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "open_dir_externally(path: str) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Open the provided dir in the default external app.",
};

// ----------------------------- fatal_error -----------------------------------

static auto PyFatalError(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* message;
  static const char* kwlist[] = {"message", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &message)) {
    return nullptr;
  }
  FatalError(message);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyFatalErrorDef = {
    "fatal_error",                 // name
    (PyCFunction)PyFatalError,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "fatal_error(message: str) -> None\n"
    "\n"
    "Trigger a fatal error. Use this in situations where it is not possible\n"
    "for the engine to continue on in a useful way. This can sometimes\n"
    "help provide more clear information at the exact source of a problem\n"
    "as compared to raising an Exception. In the vast majority of cases,\n"
    "however, Exceptions should be preferred.",
};

// ------------------------- dev_console_add_button ----------------------------

static auto PyDevConsoleAddButton(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  const char* label;
  float x;
  float y;
  float width;
  float height;
  PyObject* call;
  const char* h_anchor;
  float label_scale;
  float corner_radius;
  const char* style;
  int disabled;
  if (!PyArg_ParseTuple(args, "sffffOsffsp", &label, &x, &y, &width, &height,
                        &call, &h_anchor, &label_scale, &corner_radius, &style,
                        &disabled)) {
    return nullptr;
  }
  dev_console->AddButton(label, x, y, width, height, call, h_anchor,
                         label_scale, corner_radius, style, disabled);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleAddButtonDef = {
    "dev_console_add_button",            // name
    (PyCFunction)PyDevConsoleAddButton,  // method
    METH_VARARGS,                        // flags

    "dev_console_add_button(\n"
    "  label: str,\n"
    "  x: float,\n"
    "  y: float,\n"
    "  width: float,\n"
    "  height: float,\n"
    "  call: Callable[[], Any] | None,\n"
    "  h_anchor: str,\n"
    "  label_scale: float,\n"
    "  corner_radius: float,\n"
    "  style: str,\n"
    "  disabled: bool,\n"
    ") -> None\n"
    "\n"
    "(internal)",
};

// ------------------------- dev_console_add_text ------------------------------

static auto PyDevConsoleAddText(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  const char* text;
  float x;
  float y;
  const char* h_anchor;
  const char* h_align;
  const char* v_align;
  float scale;
  if (!PyArg_ParseTuple(args, "sffsssf", &text, &x, &y, &h_anchor, &h_align,
                        &v_align, &scale)) {
    return nullptr;
  }
  dev_console->AddText(text, x, y, h_anchor, h_align, v_align, scale);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleAddTextDef = {
    "dev_console_add_text",            // name
    (PyCFunction)PyDevConsoleAddText,  // method
    METH_VARARGS,                      // flags

    "dev_console_add_text(\n"
    "  text: str,\n"
    "  x: float,\n"
    "  y: float,\n"
    "  h_anchor: str,\n"
    "  h_align: str,\n"
    "  v_align: str,\n"
    "  scale: float,\n"
    ") -> None\n"
    "\n"
    "(internal)",
};

// -------------------- dev_console_add_python_terminal ------------------------

static auto PyDevConsoleAddPythonTerminal(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  if (!PyArg_ParseTuple(args, "")) {
    return nullptr;
  }
  dev_console->AddPythonTerminal();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleAddPythonTerminalDef = {
    "dev_console_add_python_terminal",           // name
    (PyCFunction)PyDevConsoleAddPythonTerminal,  // method
    METH_VARARGS,                                // flags

    "dev_console_add_python_terminal() -> None\n"
    "\n"
    "(internal)",
};

// ------------------------ dev_console_tab_width ------------------------------

static auto PyDevConsoleTabWidth(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  return PyFloat_FromDouble(dev_console->Width());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleTabWidthDef = {
    "dev_console_tab_width",            // name
    (PyCFunction)PyDevConsoleTabWidth,  // method
    METH_NOARGS,                        // flags

    "dev_console_tab_width() -> float\n"
    "\n"
    "(internal)",
};

// ------------------------ dev_console_tab_height -----------------------------

static auto PyDevConsoleTabHeight(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  return PyFloat_FromDouble(dev_console->Height());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleTabHeightDef = {
    "dev_console_tab_height",            // name
    (PyCFunction)PyDevConsoleTabHeight,  // method
    METH_NOARGS,                         // flags

    "dev_console_tab_height() -> float\n"
    "\n"
    "(internal)",
};

// ----------------------- dev_console_base_scale ------------------------------

static auto PyDevConsoleBaseScale(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  return PyFloat_FromDouble(dev_console->BaseScale());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleBaseScaleDef = {
    "dev_console_base_scale",            // name
    (PyCFunction)PyDevConsoleBaseScale,  // method
    METH_NOARGS,                         // flags

    "dev_console_base_scale() -> float\n"
    "\n"
    "(internal)",
};

// -------------------- dev_console_request_refresh ----------------------------

static auto PyDevConsoleRequestRefresh(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* dev_console = g_base->ui->dev_console();
  BA_PRECONDITION(dev_console);
  BA_PRECONDITION(dev_console->IsActive());
  dev_console->RequestRefresh();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleRequestRefreshDef = {
    "dev_console_request_refresh",            // name
    (PyCFunction)PyDevConsoleRequestRefresh,  // method
    METH_NOARGS,                              // flags

    "dev_console_request_refresh() -> None\n"
    "\n"
    "(internal)",
};

// -------------------------- asset_loads_allowed ------------------------------

static auto PyAssetLoadsAllowed(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->assets->asset_loads_allowed()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAssetLoadsAllowedDef = {
    "asset_loads_allowed",             // name
    (PyCFunction)PyAssetLoadsAllowed,  // method
    METH_NOARGS,                       // flags

    "asset_loads_allowed() -> bool\n"
    "\n"
    "(internal)",
};

// -------------------- using_google_play_game_services ------------------------

static auto PyUsingGooglePlayGameServices(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.use_google_play_game_services()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUsingGooglePlayGameServicesDef = {
    "using_google_play_game_services",           // name
    (PyCFunction)PyUsingGooglePlayGameServices,  // method
    METH_NOARGS,                                 // flags

    "using_google_play_game_services() -> bool\n"
    "\n"
    "(internal)",
};

// ---------------------------- using_game_center ------------------------------

static auto PyUsingGameCenter(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.use_game_center()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUsingGameCenterDef = {
    "using_game_center",             // name
    (PyCFunction)PyUsingGameCenter,  // method
    METH_NOARGS,                     // flags

    "using_game_center() -> bool\n"
    "\n"
    "(internal)",
};

// --------------------- native_review_request_supported -----------------------

static auto PyNativeReviewRequestSupported(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->app_adapter->NativeReviewRequestSupported()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNativeReviewRequestSupportedDef = {
    "native_review_request_supported",            // name
    (PyCFunction)PyNativeReviewRequestSupported,  // method
    METH_NOARGS,                                  // flags

    "native_review_request_supported() -> bool\n"
    "\n"
    "(internal)",
};

// -------------------------- native_review_request ----------------------------

static auto PyNativeReviewRequest(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  g_base->app_adapter->NativeReviewRequest();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNativeReviewRequestDef = {
    "native_review_request",             // name
    (PyCFunction)PyNativeReviewRequest,  // method
    METH_NOARGS,                         // flags

    "native_review_request() -> None\n"
    "\n"
    "(internal)",
};

// ------------------------------- temp_testing --------------------------------

static auto PyTempTesting(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  std::string devstr = g_core->platform->GetDeviceName() + " "
                       + g_core->platform->GetOSVersionString();
  if (devstr == "samsung SM-N950F 7.1.1") {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyTempTestingDef = {
    "temp_testing",              // name
    (PyCFunction)PyTempTesting,  // method
    METH_NOARGS,                 // flags

    "temp_testing() -> bool\n"
    "\n"
    "(internal)",
};

// ------------------------- open_file_externally ------------------------------

static auto PyOpenFileExternally(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  char* path = nullptr;
  static const char* kwlist[] = {"path", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &path)) {
    return nullptr;
  }
  g_base->platform->OpenFileExternally(path);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOpenFileExternallyDef = {
    "open_file_externally",             // name
    (PyCFunction)PyOpenFileExternally,  // method
    METH_VARARGS | METH_KEYWORDS,       // flags

    "open_file_externally(path: str) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Open the provided file in the default external app.",
};

// --------------------------- get_input_idle_time -----------------------------

static auto PyGetInputIdleTime(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  return PyFloat_FromDouble(0.001 * g_base->input->input_idle_time());

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetInputIdleTimeDef = {
    "get_input_idle_time",            // name
    (PyCFunction)PyGetInputIdleTime,  // method
    METH_NOARGS,                      // flags

    "get_input_idle_time() -> float\n"
    "\n"
    "Return seconds since any local input occurred (touch, keypress, etc.).",
};

// ------------------ get_draw_virtual_safe_area_bounds ------------------------

static auto PyGetDrawVirtualSafeAreaBounds(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  if (g_base->graphics->draw_virtual_safe_area_bounds()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetDrawVirtualSafeAreaBoundsDef = {
    "get_draw_virtual_safe_area_bounds",          // name
    (PyCFunction)PyGetDrawVirtualSafeAreaBounds,  // method
    METH_NOARGS,                                  // flags

    "get_draw_virtual_safe_area_bounds() -> bool\n"
    "\n"
    "(internal)",
};

// -------------------------- get_initial_app_config ---------------------------

static auto PyGetInitialAppConfig(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  return g_core->HandOverInitialAppConfig();

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetInitialAppConfigDef = {
    "get_initial_app_config",            // name
    (PyCFunction)PyGetInitialAppConfig,  // method
    METH_NOARGS,                         // flags

    "get_initial_app_config() -> dict\n"
    "\n"
    "(internal)",
};

// ------------------ set_draw_virtual_safe_area_bounds ------------------------

static auto PySetDrawVirtualSafeAreaBounds(PyObject* self, PyObject* args,
                                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());

  int value;
  static const char* kwlist[] = {"value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &value)) {
    return nullptr;
  }

  g_base->graphics->set_draw_virtual_safe_area_bounds(value);
  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PySetDrawVirtualSafeAreaBoundsDef = {
    "set_draw_virtual_safe_area_bounds",          // name
    (PyCFunction)PySetDrawVirtualSafeAreaBounds,  // method
    METH_VARARGS | METH_KEYWORDS,                 // flags

    "set_draw_virtual_safe_area_bounds(value: bool) -> None\n"
    "\n"
    "(internal)",
};

// ----------------------------- push_back_press -------------------------------

static auto PyPushBackPress(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  g_base->ui->PushBackButtonCall(nullptr);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPushBackPressDef = {
    "push_back_press",             // name
    (PyCFunction)PyPushBackPress,  // method
    METH_NOARGS,                   // flags

    "push_back_press() -> None\n"
    "\n"
    "(internal)",
};

// ---------------------------- set_app_config ---------------------------------

static auto PySetAppConfig(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* config_obj;
  if (!PyArg_ParseTuple(args, "O", &config_obj)) {
    return nullptr;
  }
  BA_PRECONDITION(PyDict_Check(config_obj));
  g_base->python->SetConfig(config_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetAppConfigDef = {
    "set_app_config",  // name
    PySetAppConfig,    // method
    METH_VARARGS,      // flags

    "set_app_config(config: dict) -> None\n"
    "\n"
    "(internal)",
};

// --------------------- update_internal_logger_levels -------------------------

static auto PyUpdateInternalLoggerLevels(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  g_core->UpdateInternalLoggerLevels();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUpdateInternalLoggerLevelsDef = {
    "update_internal_logger_levels",            // name
    (PyCFunction)PyUpdateInternalLoggerLevels,  // method
    METH_NOARGS,                                // flags

    "update_internal_logger_levels() -> None\n"
    "\n"
    "Update the native layer to re-cache Python logger levels.\n"
    "\n"
    "The native layer caches logger levels so it can efficiently\n"
    "avoid making Python log calls for disabled logger levels. If any\n"
    "logger levels are changed at runtime, call this method after to\n"
    "instruct the native layer to regenerate its cache so the change\n"
    "is properly reflected in logs originating from the native layer."};
// -----------------------------------------------------------------------------

auto PythonMoethodsBase3::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyClipboardIsSupportedDef,
      PyClipboardHasTextDef,
      PyClipboardSetTextDef,
      PyClipboardGetTextDef,
      PyDoOnceDef,
      PyGetAppDef,
      PyAndroidGetExternalFilesDirDef,
      PySetInternalLanguageKeysDef,
      PySetAnalyticsScreenDef,
      PyLoginAdapterGetSignInTokenDef,
      PyLoginAdapterBackEndActiveChangeDef,
      PySubmitAnalyticsCountsDef,
      PyIncrementAnalyticsCountRawDef,
      PyIncrementAnalyticsCountRaw2Def,
      PyIncrementAnalyticsCountDef,
      PyMarkLogSentDef,
      PyGetV1CloudLogDef,
      PyIsLogFullDef,
      PyGetLogFilePathDef,
      PyGetVolatileDataDirectoryDef,
      PySetPlatformMiscReadValsDef,
      PySetLowLevelConfigValueDef,
      PyGetLowLevelConfigValueDef,
      PyResolveAppConfigValueDef,
      PyGetAppConfigDefaultValueDef,
      PyAppConfigGetBuiltinKeysDef,
      PyGetReplaysDirDef,
      PyPrintLoadInfoDef,
      PyPrintContextDef,
      PyDebugPrintPyErrDef,
      PyWorkspacesInUseDef,
      PyHasUserRunCommandsDef,
      PyContainsPythonDistDef,
      PyGetIdleTimeDef,
      PyExtraHashValueDef,
      PySetUIInputDeviceDef,
      PyGetUIScaleDef,
      PySetUIScaleDef,
      PyGetThreadNameDef,
      PySetThreadNameDef,
      PyInLogicThreadDef,
      PyInMainMenuDef,
      PyRequestPermissionDef,
      PyHavePermissionDef,
      PyUnlockAllInputDef,
      PyLockAllInputDef,
      PySetUpSigIntDef,
      PyGetSimpleSoundDef,
      PyHasTouchScreenDef,
      PyNativeStackTraceDef,
      PySupportsOpenDirExternallyDef,
      PyOpenDirExternallyDef,
      PyFatalErrorDef,
      PyDevConsoleAddButtonDef,
      PyDevConsoleAddTextDef,
      PyDevConsoleAddPythonTerminalDef,
      PyDevConsoleTabWidthDef,
      PyDevConsoleTabHeightDef,
      PyDevConsoleBaseScaleDef,
      PyDevConsoleRequestRefreshDef,
      PyAssetLoadsAllowedDef,
      PyUsingGooglePlayGameServicesDef,
      PyUsingGameCenterDef,
      PyNativeReviewRequestSupportedDef,
      PyNativeReviewRequestDef,
      PyTempTestingDef,
      PyOpenFileExternallyDef,
      PyGetInputIdleTimeDef,
      PyPushBackPressDef,
      PyGetDrawVirtualSafeAreaBoundsDef,
      PySetDrawVirtualSafeAreaBoundsDef,
      PyGetInitialAppConfigDef,
      PySetAppConfigDef,
      PyUpdateInternalLoggerLevelsDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
