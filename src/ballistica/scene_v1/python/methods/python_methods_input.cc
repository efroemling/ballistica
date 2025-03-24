// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/methods/python_methods_input.h"

#include <string>
#include <vector>

#include "ballistica/base/input/device/touch_input.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::scene_v1 {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

// ----------------------- get_configurable_game_pads --------------------------

static auto PyGetConfigurableGamePads(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::vector<base::InputDevice*> gamepads =
      g_base->input->GetConfigurableGamePads();
  PyObject* list = PyList_New(0);
  for (auto&& i : gamepads) {
    // We require scene-v1 input-devices; try to cast.
    base::InputDeviceDelegate* delegate = &i->delegate();
    if (auto* c_delegate =
            dynamic_cast<SceneV1InputDeviceDelegate*>(delegate)) {
      PyObject* obj = c_delegate->NewPyRef();
      PyList_Append(list, obj);
      Py_DECREF(obj);
    }
  }
  return list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetConfigurableGamePadsDef = {
    "get_configurable_game_pads",  // name
    PyGetConfigurableGamePads,     // method
    METH_VARARGS,                  // flags

    "get_configurable_game_pads() -> list\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns a list of the currently connected gamepads that can be\n"
    "configured.",
};

// ------------------------ have_touchscreen_input -----------------------------

static auto PyHaveTouchScreenInput(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->touch_input) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHaveTouchScreenInputDef = {
    "have_touchscreen_input",  // name
    PyHaveTouchScreenInput,    // method
    METH_VARARGS,              // flags

    "have_touchscreen_input() -> bool\n"
    "\n"
    "Internal; Return whether or not a touch-screen input is present.\n"
    "\n"
    ":meta private:",
};

// ------------------------- set_touchscreen_editing ---------------------------

static auto PySetTouchscreenEditing(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  int editing;
  if (!PyArg_ParseTuple(args, "p", &editing)) {
    return nullptr;
  }
  if (g_base->touch_input) {
    g_base->touch_input->set_editing(static_cast<bool>(editing));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetTouchscreenEditingDef = {
    "set_touchscreen_editing",  // name
    PySetTouchscreenEditing,    // method
    METH_VARARGS,               // flags

    "set_touchscreen_editing(editing: bool) -> None\n"
    "\n"
    "(internal)",
};

// ------------------------- capture_gamepad_input -----------------------------

static auto PyCaptureGamePadInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* obj;
  if (!PyArg_ParseTuple(args, "O", &obj)) {
    return nullptr;
  }
  g_scene_v1->python->CaptureJoystickInput(obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCaptureGamePadInputDef = {
    "capture_gamepad_input",  // name
    PyCaptureGamePadInput,    // method
    METH_VARARGS,             // flags

    "capture_gamepad_input(call: Callable[[dict], None]) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Add a callable to be called for subsequent gamepad events.\n"
    "The method is passed a dict containing info about the event.",
};

// ------------------------- release_gamepad_input -----------------------------

static auto PyReleaseGamePadInput(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  g_scene_v1->python->ReleaseJoystickInputCapture();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyReleaseGamePadInputDef = {
    "release_gamepad_input",  // name
    PyReleaseGamePadInput,    // method
    METH_VARARGS,             // flags

    "release_gamepad_input() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Resumes normal gamepad event processing.",
};

// ------------------------ capture_keyboard_input -----------------------------

static auto PyCaptureKeyboardInput(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  assert(g_scene_v1);
  PyObject* obj;
  if (!PyArg_ParseTuple(args, "O", &obj)) {
    return nullptr;
  }
  g_scene_v1->python->CaptureKeyboardInput(obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCaptureKeyboardInputDef = {
    "capture_keyboard_input",  // name
    PyCaptureKeyboardInput,    // method
    METH_VARARGS,              // flags

    "capture_keyboard_input(call: Callable[[dict], None]) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Add a callable to be called for subsequent keyboard-game-pad events.\n"
    "The method is passed a dict containing info about the event.",
};

// ------------------------- release_keyboard_input ----------------------------

static auto PyReleaseKeyboardInput(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  assert(g_scene_v1);
  g_scene_v1->python->ReleaseKeyboardInputCapture();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyReleaseKeyboardInputDef = {
    "release_keyboard_input",  // name
    PyReleaseKeyboardInput,    // method
    METH_VARARGS,              // flags

    "release_keyboard_input() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Resumes normal keyboard event processing.",
};

// --------------------------- get_ui_input_device -----------------------------

static auto PyGetUIInputDevice(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  base::InputDevice* d = g_base->ui->GetUIInputDevice();
  if (d) {
    // We require scene-v1 input-devices; try to cast.
    auto* delegate = &d->delegate();
    if (auto* c_delegate =
            dynamic_cast<SceneV1InputDeviceDelegate*>(delegate)) {
      return c_delegate->NewPyRef();
    } else {
      // Assuming this would be due to getting called in another app-mode.
      // Wonder if it would be wise to error in that case...
      BA_LOG_ONCE(
          LogName::kBa, LogLevel::kWarning,
          "scene_v1: Found unexpected delegate "
              + (delegate ? delegate->GetObjectDescription() : "(nullptr)")
              + " for ui-input-device " + d->GetObjectDescription() + ".");
      Py_RETURN_NONE;
    }
  } else {
    Py_RETURN_NONE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetUIInputDeviceDef = {
    "get_ui_input_device",            // name
    (PyCFunction)PyGetUIInputDevice,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "get_ui_input_device() -> bascenev1.InputDevice | None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns the input-device that currently owns the user interface, or\n"
    "None if there is none.",
};

// ---------------------------- getinputdevice ---------------------------------

static auto PyGetInputDevice(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  const char* name;
  const char* unique_id;
  int doraise = true;
  static const char* kwlist[] = {"name", "unique_id", "doraise", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "ss|i",
                                   const_cast<char**>(kwlist), &name,
                                   &unique_id, &doraise)) {
    return nullptr;
  }
  base::InputDevice* d = g_base->input->GetInputDevice(name, unique_id);
  if (d) {
    // We require scene-v1 input-devices; try to cast.
    auto* delegate = &d->delegate();
    if (auto* c_delegate =
            dynamic_cast<SceneV1InputDeviceDelegate*>(delegate)) {
      return c_delegate->NewPyRef();
    } else {
      // Perhaps will want to return None in this case once we've got
      // newer versions of InputDevice; we'll see...
      throw Exception(
          "Unexpected delegate "
          + (delegate ? delegate->GetObjectDescription() : "(nullptr)")
          + " for input device " + d->GetObjectDescription() + ".");
    }
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

static PyMethodDef PyGetInputDeviceDef = {
    "getinputdevice",               // name
    (PyCFunction)PyGetInputDevice,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "getinputdevice(name: str, unique_id: str, doraise: bool = True)\n"
    "  -> <varies>\n"
    "\n"
    "(internal)\n"
    "\n"
    "Given a type name and a unique identifier, returns an InputDevice.\n"
    "Throws an Exception if the input-device is not found, or returns None\n"
    "if 'doraise' is False.\n",
};

// ------------------ get_local_active_input_devices_count ---------------------

static auto PyGetLocalActiveInputDevicesCount(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->input);
  return PyLong_FromLong(g_base->input->GetLocalActiveInputDeviceCount());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetLocalActiveInputDevicesCountDef = {
    "get_local_active_input_devices_count",          // name
    (PyCFunction)PyGetLocalActiveInputDevicesCount,  // method
    METH_VARARGS | METH_KEYWORDS,                    // flags

    "get_local_active_input_devices_count() -> int\n"
    "\n"
    "(internal)",
};

// -----------------------------------------------------------------------------

auto PythonMethodsInput::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyGetLocalActiveInputDevicesCountDef,
      PyGetInputDeviceDef,
      PyGetUIInputDeviceDef,
      PyReleaseKeyboardInputDef,
      PyCaptureKeyboardInputDef,
      PyReleaseGamePadInputDef,
      PyCaptureGamePadInputDef,
      PySetTouchscreenEditingDef,
      PyHaveTouchScreenInputDef,
      PyGetConfigurableGamePadsDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
