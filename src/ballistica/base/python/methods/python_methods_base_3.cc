// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_base_3.h"

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_simple_sound.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/native_stack_trace.h"
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
    Object::Ref<SoundAsset> sound = g_base->assets->GetSound(name);
    return PythonClassSimpleSound::Create(sound.get());
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
    ":meta private:",
};

// ----------------------- set_main_ui_input_device ----------------------------

static auto PySetMainUIInputDevice(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
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
    device = g_base->input->GetInputDevice(Python::GetInt(input_device_id_obj));
    if (!device) {
      throw Exception("Invalid input-device id.");
    }
  }
  g_base->ui->SetMainUIInputDevice(device);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetMainUIInputDeviceDef = {
    "set_main_ui_input_device",           // name
    (PyCFunction)PySetMainUIInputDevice,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "set_main_ui_input_device(input_device_id: int | None)"
    " -> None\n"
    "\n"
    "Sets the input-device that currently owns the main ui.\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
};
// ------------------------------ set_ui_scale ---------------------------------

static auto PyGetUIScale(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  // FIXME: Should have this return enums directly once we have an easy way
  // to share enums between Python/CPP.
  auto scale = g_base->ui->uiscale();

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
    ":meta private:",
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
    "Return whether a touchscreen is present on the current device.\n"
    "\n"
    ":meta private:",
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
    "This will return False if no system clipboard is available; no need\n"
    " to call :meth:`~babase.clipboard_is_supported()` separately.",
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
    "Ensure that :meth:`~babase.clipboard_is_supported()` returns True before\n"
    "adding buttons/etc. that make use of this functionality.",
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
    "Ensure that :meth:`~babase.clipboard_has_text()` returns True before\n"
    "calling this function.",
};

// ------------------------------ setup_sigint ---------------------------------

static auto PySetUpSigInt(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base) {
    g_base->platform->SetupInterruptHandling();
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
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
    ":meta private:",
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

  permission = g_base->python->GetPyEnum_Permission(permission_obj);

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
    ":meta private:",
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

  permission = g_base->python->GetPyEnum_Permission(permission_obj);
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
    ":meta private:",
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
    "Return whether the current thread is the logic thread.\n"
    "\n"
    "The logic thread is where a large amount of app code runs, and\n"
    "various functionality expects to only be used from there.",
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
    "Are we currently in a main-menu (as opposed to gameplay)?\n"
    "\n"
    ":meta private:",
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
    "Set the name of the current thread (on platforms where available).\n"
    "\n"
    "Thread names are only for debugging and should not be used in logic,\n"
    "as naming behavior can vary across platforms.\n"
    "\n"
    ":meta private:"};

// ---------------------------- get_thread_name ------------------------------

static auto PyGetThreadName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(g_core->CurrentThreadName().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetThreadNameDef = {
    "get_thread_name",             // name
    (PyCFunction)PyGetThreadName,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_thread_name() -> str\n"
    "\n"
    "Return the name of the current thread.\n"
    "\n"
    "This may vary depending on platform and should not be used in logic;\n"
    "only for debugging.\n"
    "\n"
    ":meta private:",
};

// -------------------------------- ehv ----------------------------------------

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
    ":meta private:",
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
    "Returns the amount of time since any game input has been received.\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    "Return whether workspace functionality was ever enabled this run.\n"
    "\n"
    ":meta private:"};

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
    ":meta private:",
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
    "Debugging func for tracking leaked Python errors in the C++ layer.\n"
    "\n"
    ":meta private:",
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
    "Prints info about the current context state; for debugging.\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
};

// ------------------- suppress_config_and_state_writes ------------------------

static auto PySuppressConfigAndStateWrites(PyObject* self, PyObject* args,
                                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  g_base->set_config_and_state_writes_suppressed(true);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySuppressConfigAndStateWritesDef = {
    "suppress_config_and_state_writes",           // name
    (PyCFunction)PySuppressConfigAndStateWrites,  // method
    METH_NOARGS,                                  // flags

    "suppress_config_and_state_writes() -> None\n"
    "\n"
    "Disable subsequent writes of app config and state files by the engine.\n"
    "\n"
    "This can be used by tools intending to manipulate these files\n"
    "manually. Such tools should be sure to restart or quit the app\n"
    "when done to restore normal behavior.\n"};

// ----------------- get_suppress_config_and_state_writes ----------------------

static auto PyGetSuppressConfigAndStateWrites(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->config_and_state_writes_suppressed()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSuppressConfigAndStateWritesDef = {
    "get_suppress_config_and_state_writes",          // name
    (PyCFunction)PyGetSuppressConfigAndStateWrites,  // method
    METH_NOARGS,                                     // flags

    "get_suppress_config_and_state_writes() -> None\n"
    "\n"
    "Are config and state writes suppressed?\n"
    "\n"
    "This can be used by tools intending to manipulate these files\n"
    "manually. Such tools should be sure to restart or quit the app\n"
    "when done to restore normal behavior.\n"};

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
    throw Exception("Invalid config key '" + std::string(key) + "'.",
                    PyExcType::kKey);
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
  std::string vals = Python::GetString(vals_obj);
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
    ":meta private:",
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
    "Return the path to the app log file.\n"
    "\n"
    ":meta private:",
};

// ----------------------------- is_log_full -----------------------------------
static auto PyIsLogFull(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_core->logging->v1_cloud_log_full()) {
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
    ":meta private:",
};

// -------------------------- get_v1_cloud_log ---------------------------------

static auto PyGetV1CloudLog(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string log_fin;
  {
    std::scoped_lock lock(g_core->logging->v1_cloud_log_mutex());
    log_fin = g_core->logging->v1_cloud_log();
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
    ":meta private:",
};

// ---------------------------- mark_log_sent ----------------------------------

static auto PyMarkLogSent(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  // This way we won't try to send it at shutdown time and whatnot
  g_core->logging->set_did_put_v1_cloud_log(true);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMarkLogSentDef = {
    "mark_log_sent",               // name
    (PyCFunction)PyMarkLogSent,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "mark_log_sent() -> None\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    "  uses_increment: int = 1, increment: int = 1) -> None\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    "Generally called when opening a new window or entering some UI.\n"
    "'screen' should be a string description of an app location\n"
    "('Main Menu', etc.)\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
  if (g_buildconfig.platform_android()) {
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
    "Return the android external storage path, or None if there is none.\n"
    "\n"
    ":meta private:",
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
    "This is used by ``print_once()`` type calls to keep from overflowing\n"
    "logs. The call functions by registering the filename and line where\n"
    "The call is made from.  Returns True if this location has not been\n"
    "registered already, and False if it has.\n"
    "\n"
    "Example: This print will only fire for the first loop iteration::\n"
    "\n"
    "    for i in range(10):\n"
    "        if babase.do_once():\n"
    "            print('HelloWorld once from loop!')",
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
    ":meta private:",
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
    "Prevent all keyboard, mouse, and gamepad events from being processed.\n"
    "\n"
    ":meta private:",
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
    "Resume normal keyboard, mouse, and gamepad event processing.\n"
    "\n"
    ":meta private:",
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
    "Return whether current app/platform supports opening dirs externally.\n"
    "\n"
    "(Via the Mac Finder, Windows Explorer, etc.)\n"
    "\n"
    ":meta private:",
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
    "Open the provided dir in the default external app.\n"
    "\n"
    ":meta private:",
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
    "as compared to raising an :class:`Exception`. In the vast majority of\n"
    "cases, however, exceptions should be preferred.",
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
    ":meta private:",
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
  const char* style_str;
  float scale;
  if (!PyArg_ParseTuple(args, "sffsssfs", &text, &x, &y, &h_anchor, &h_align,
                        &v_align, &scale, &style_str)) {
    return nullptr;
  }
  dev_console->AddText(text, x, y, h_anchor, h_align, v_align, scale,
                       style_str);
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
    "  style: str,\n"
    ") -> None\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    "Open the provided file in the default external app.\n"
    "\n"
    ":meta private:",
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
    "Return seconds since any local input occurred (touch, keypress, etc.).\n"
    "\n"
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
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
    ":meta private:",
};

// ------------------------------- menu_press ----------------------------------

static auto PyMenuPress(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // Our C++ call needs to happen in the logic thread, but we can be called
  // from anywhere.
  g_base->logic->event_loop()->PushCall([] {
    g_base->ui->MenuPress(g_base->input->GetFuzzyInputDeviceForMenuButton());
  });

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMenuPressDef = {
    "menu_press",              // name
    (PyCFunction)PyMenuPress,  // method
    METH_NOARGS,               // flags

    "menu_press() -> None\n"
    "\n"
    ":meta private:",
};

// ---------------------------- request_main_ui --------------------------------

static auto PyRequestMainUI(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // Our C++ call needs to happen in the logic thread, but we can be called
  // from anywhere.
  g_base->logic->event_loop()->PushCall([] {
    g_base->ui->RequestMainUI(
        g_base->input->GetFuzzyInputDeviceForMenuButton());
  });

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRequestMainUIDef = {
    "request_main_ui",             // name
    (PyCFunction)PyRequestMainUI,  // method
    METH_NOARGS,                   // flags

    "request_main_ui() -> None\n"
    "\n"
    "High level call to request a main ui if it is not already open.\n"
    "\n"
    "Can be called from any thread.",
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
    ":meta private:",
};

// --------------------- update_internal_logger_levels -------------------------

static auto PyUpdateInternalLoggerLevels(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  g_core->logging->UpdateInternalLoggerLevels();
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
    "is properly reflected in logs originating from the native layer.\n"
    "\n"
    ":meta private:"};
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
      PySetMainUIInputDeviceDef,
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
      PyMenuPressDef,
      PyRequestMainUIDef,
      PyGetDrawVirtualSafeAreaBoundsDef,
      PySetDrawVirtualSafeAreaBoundsDef,
      PyGetInitialAppConfigDef,
      PySetAppConfigDef,
      PyUpdateInternalLoggerLevelsDef,
      PySuppressConfigAndStateWritesDef,
      PyGetSuppressConfigAndStateWritesDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
