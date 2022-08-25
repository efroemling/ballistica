// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_input.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/game/game.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/input/device/touch_input.h"
#include "ballistica/input/input.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyGetConfigurableGamePads(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  std::vector<InputDevice*> gamepads = g_input->GetConfigurableGamePads();
  PyObject* list = PyList_New(0);
  for (auto&& i : gamepads) {
    PyObject* obj = i->NewPyRef();
    PyList_Append(list, obj);
    Py_DECREF(obj);
  }
  return list;
  BA_PYTHON_CATCH;
}

auto PyHaveTouchScreenInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_app_globals->touch_input) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PySetTouchscreenEditing(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  int editing;
  if (!PyArg_ParseTuple(args, "p", &editing)) {
    return nullptr;
  }
  if (g_app_globals->touch_input) {
    g_app_globals->touch_input->set_editing(static_cast<bool>(editing));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyCaptureGamePadInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  assert(g_python);
  PyObject* obj;
  if (!PyArg_ParseTuple(args, "O", &obj)) {
    return nullptr;
  }
  g_python->CaptureGamePadInput(obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyReleaseGamePadInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  assert(g_python);
  g_python->ReleaseGamePadInput();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyCaptureKeyboardInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  if (!g_python) {
    return nullptr;
  }
  PyObject* obj;
  if (!PyArg_ParseTuple(args, "O", &obj)) {
    return nullptr;
  }
  g_python->CaptureKeyboardInput(obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyReleaseKeyboardInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  if (!g_python) {
    return nullptr;
  }
  g_python->ReleaseKeyboardInput();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyLockAllInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  assert(g_input);
  g_input->LockAllInput(false, Python::GetPythonFileLocation());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyUnlockAllInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  assert(g_input);
  g_input->UnlockAllInput(false, Python::GetPythonFileLocation());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetUIInputDevice(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  InputDevice* d = g_ui->GetUIInputDevice();
  if (d) {
    return d->NewPyRef();
  } else {
    Py_RETURN_NONE;
  }
  BA_PYTHON_CATCH;
}

auto PySetUIInputDevice(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  static const char* kwlist[] = {"input", nullptr};
  PyObject* input_device_obj = Py_None;
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &input_device_obj)) {
    return nullptr;
  }
  g_ui->SetUIInputDevice((input_device_obj == Py_None)
                             ? nullptr
                             : Python::GetPyInputDevice(input_device_obj));

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetInputDevice(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  const char* name;
  const char* unique_id;
  int doraise = true;
  static const char* kwlist[] = {"name", "unique_id", "doraise", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "ss|i",
                                   const_cast<char**>(kwlist), &name,
                                   &unique_id, &doraise)) {
    return nullptr;
  }
  InputDevice* d = g_input->GetInputDevice(name, unique_id);
  if (d) {
    return d->NewPyRef();
  } else {
    if (doraise) {
      throw Exception(std::string("Input device not found: '") + name + " "
                          + unique_id + "'.",
                      PyExcType::kInputDeviceNotFound);
    } else {
      Py_RETURN_NONE;
    }
  }
  BA_PYTHON_CATCH;
}

auto PyGetLocalActiveInputDevicesCount(PyObject* self, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  BA_PRECONDITION(g_input);
  return PyLong_FromLong(g_input->GetLocalActiveInputDeviceCount());
  BA_PYTHON_CATCH;
}

auto PythonMethodsInput::GetMethods() -> std::vector<PyMethodDef> {
  return {
      {"get_local_active_input_devices_count",
       (PyCFunction)PyGetLocalActiveInputDevicesCount,
       METH_VARARGS | METH_KEYWORDS,
       "get_local_active_input_devices_count() -> int\n"
       "\n"
       "(internal)"},

      {"getinputdevice", (PyCFunction)PyGetInputDevice,
       METH_VARARGS | METH_KEYWORDS,
       "getinputdevice(name: str, unique_id: str, doraise: bool = True)\n"
       "  -> <varies>\n"
       "\n"
       "(internal)\n"
       "\n"
       "Given a type name and a unique identifier, returns an InputDevice.\n"
       "Throws an Exception if the input-device is not found, or returns None\n"
       "if 'doraise' is False.\n"},

      {"set_ui_input_device", (PyCFunction)PySetUIInputDevice,
       METH_VARARGS | METH_KEYWORDS,
       "set_ui_input_device(input_device: ba.InputDevice | None) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Sets the input-device that currently owns the user interface."},

      {"get_ui_input_device", (PyCFunction)PyGetUIInputDevice,
       METH_VARARGS | METH_KEYWORDS,
       "get_ui_input_device() -> ba.InputDevice\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns the input-device that currently owns the user interface, or\n"
       "None if there is none."},

      {"unlock_all_input", PyUnlockAllInput, METH_VARARGS,
       "unlock_all_input() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Resumes normal keyboard, mouse, and gamepad event processing."},

      {"lock_all_input", PyLockAllInput, METH_VARARGS,
       "lock_all_input() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Prevents all keyboard, mouse, and gamepad events from being "
       "processed."},

      {"release_keyboard_input", PyReleaseKeyboardInput, METH_VARARGS,
       "release_keyboard_input() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Resumes normal keyboard event processing."},

      {"capture_keyboard_input", PyCaptureKeyboardInput, METH_VARARGS,
       "capture_keyboard_input(call: Callable[[dict], None]) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Add a callable to be called for subsequent keyboard-game-pad events.\n"
       "The method is passed a dict containing info about the event."},

      {"release_gamepad_input", PyReleaseGamePadInput, METH_VARARGS,
       "release_gamepad_input() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Resumes normal gamepad event processing."},

      {"capture_gamepad_input", PyCaptureGamePadInput, METH_VARARGS,
       "capture_gamepad_input(call: Callable[[dict], None]) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Add a callable to be called for subsequent gamepad events.\n"
       "The method is passed a dict containing info about the event."},

      {"set_touchscreen_editing", PySetTouchscreenEditing, METH_VARARGS,
       "set_touchscreen_editing(editing: bool) -> None\n"
       "\n"
       "(internal)"},

      {"have_touchscreen_input", PyHaveTouchScreenInput, METH_VARARGS,
       "have_touchscreen_input() -> bool\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns whether or not a touch-screen input is present"},

      {"get_configurable_game_pads", PyGetConfigurableGamePads, METH_VARARGS,
       "get_configurable_game_pads() -> list\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns a list of the currently connected gamepads that can be\n"
       "configured."},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
