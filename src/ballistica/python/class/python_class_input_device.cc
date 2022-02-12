// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_input_device.h"

#include "ballistica/game/player.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/python/python.h"

namespace ballistica {

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "RedundantCast"

void PythonClassInputDevice::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.InputDevice";
  obj->tp_basicsize = sizeof(PythonClassInputDevice);
  obj->tp_doc =
      "An input-device such as a gamepad, touchscreen, or keyboard.\n"
      "\n"
      "Category: Gameplay Classes\n"
      "\n"
      "Attributes:\n"
      "\n"
      "   allows_configuring (bool):\n"
      "      Whether the input-device can be configured.\n"
      "\n"
      "   has_meaningful_button_names (bool):\n"
      "      Whether button names returned by this instance match labels\n"
      "      on the actual device. (Can be used to determine whether to show\n"
      "      them in controls-overlays, etc.).\n"
      "\n"
      "   player (Optional[ba.SessionPlayer]):\n"
      "      The player associated with this input device.\n"
      "\n"
      "   client_id (int):\n"
      "      The numeric client-id this device is associated with.\n"
      "      This is only meaningful for remote client inputs; for\n"
      "      all local devices this will be -1.\n"
      "\n"
      "   name (str):\n"
      "      The name of the device.\n"
      "\n"
      "   unique_identifier (str):\n"
      "      A string that can be used to persistently identify the device,\n"
      "      even among other devices of the same type. Used for saving\n"
      "      prefs, etc.\n"
      "\n"
      "   id (int):\n"
      "      The unique numeric id of this device.\n"
      "\n"
      "   instance_number (int):\n"
      "      The number of this device among devices of the same type.\n"
      "\n"
      "   is_controller_app (bool):\n"
      "      Whether this input-device represents a locally-connected\n"
      "      controller-app.\n"
      "\n"
      "   is_remote_client (bool):\n"
      "      Whether this input-device represents a remotely-connected\n"
      "      client.\n"
      "\n";

  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_methods = tp_methods;
  obj->tp_getattro = (getattrofunc)tp_getattro;
  obj->tp_setattro = (setattrofunc)tp_setattro;

  // We provide number methods only for bool functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  obj->tp_as_number = &as_number_;
}

auto PythonClassInputDevice::Create(InputDevice* input_device) -> PyObject* {
  // Make sure we only have one python ref per material.
  if (input_device) {
    assert(!input_device->has_py_ref());
  }
  auto* py_input_device = reinterpret_cast<PythonClassInputDevice*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_input_device) {
    throw Exception("ba.InputDevice creation failed.");
  }
  *(py_input_device->input_device_) = input_device;
  return reinterpret_cast<PyObject*>(py_input_device);
}

auto PythonClassInputDevice::GetInputDevice() const -> InputDevice* {
  InputDevice* input_device = input_device_->get();
  if (!input_device) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return input_device;
}

auto PythonClassInputDevice::tp_repr(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  InputDevice* d = self->input_device_->get();
  int input_device_id = d ? d->index() : -1;
  std::string dname = d ? d->GetDeviceName() : "invalid device";
  return Py_BuildValue("s",
                       (std::string("<Ballistica InputDevice ")
                        + std::to_string(input_device_id) + " (" + dname + ")>")
                           .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::nb_bool(PythonClassInputDevice* self) -> int {
  return self->input_device_->exists();
}

PyNumberMethods PythonClassInputDevice::as_number_;

auto PythonClassInputDevice::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassInputDevice*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InGameThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    self->input_device_ = new Object::WeakRef<InputDevice>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassInputDevice::tp_dealloc(PythonClassInputDevice* self) {
  BA_PYTHON_TRY;
  // These have to be destructed in the game thread - send them along to it if
  // need be.
  // FIXME: Technically the main thread has a pointer to a dead PyObject
  //  until the delete goes through; could that ever be a problem?
  if (!InGameThread()) {
    Object::WeakRef<InputDevice>* d = self->input_device_;
    g_game->PushCall([d] { delete d; });
  } else {
    delete self->input_device_;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassInputDevice::tp_getattro(PythonClassInputDevice* self,
                                         PyObject* attr) -> PyObject* {
  BA_PYTHON_TRY;
  assert(PyUnicode_Check(attr));  // NOLINT (signed bitwise ops)
  const char* s = PyUnicode_AsUTF8(attr);
  if (!strcmp(s, "player")) {
    InputDevice* input_device = self->input_device_->get();
    if (!input_device) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    Player* player = input_device->GetPlayer();
    if (player != nullptr) {
      return player->NewPyRef();
    }
    Py_RETURN_NONE;
  } else if (!strcmp(s, "allows_configuring")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (d->GetAllowsConfiguring()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "has_meaningful_button_names")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (d->HasMeaningfulButtonNames()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "client_id")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyLong_FromLong(d->GetClientID());
  } else if (!strcmp(s, "name")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyUnicode_FromString(d->GetDeviceName().c_str());
  } else if (!strcmp(s, "unique_identifier")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyUnicode_FromString(d->GetPersistentIdentifier().c_str());
  } else if (!strcmp(s, "id")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyLong_FromLong(d->index());
  } else if (!strcmp(s, "instance_number")) {
    InputDevice* d = self->input_device_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyLong_FromLong(d->device_number());
  } else if (!strcmp(s, "is_controller_app")) {
    InputDevice* input_device = self->input_device_->get();
    if (!input_device) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (input_device->IsRemoteApp()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "is_remote_client")) {
    InputDevice* input_device = self->input_device_->get();
    if (!input_device) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (input_device->IsRemoteClient()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  }

  // Fall back to generic behavior.
  PyObject* val;
  val = PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  return val;
  BA_PYTHON_CATCH;
}

// Yes Clion, we always return -1 here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassInputDevice::tp_setattro(PythonClassInputDevice* self,
                                         PyObject* attr, PyObject* val) -> int {
  BA_PYTHON_TRY;
  assert(PyUnicode_Check(attr));  // NOLINT (signed bitwise)
  throw Exception("Attr '" + std::string(PyUnicode_AsUTF8(attr))
                  + "' is not settable on input device objects.");
  // return PyObject_GenericSetAttr(reinterpret_cast<PyObject*>(self), attr,
  // val);
  BA_PYTHON_INT_CATCH;
}

#pragma clang diagnostic pop

auto PythonClassInputDevice::RemoveRemotePlayerFromGame(
    PythonClassInputDevice* self) -> PyObject* {
  BA_PYTHON_TRY;
  InputDevice* d = self->input_device_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  d->RemoveRemotePlayerFromGame();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetDefaultPlayerName(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  InputDevice* d = self->input_device_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return PyUnicode_FromString(d->GetDefaultPlayerName().c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetPlayerProfiles(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  InputDevice* d = self->input_device_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  if (PyObject* profiles = d->GetPlayerProfiles()) {
    Py_INCREF(profiles);
    return profiles;
  } else {
    return Py_BuildValue("{}");  // Empty dict.
  }
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetAccountName(PythonClassInputDevice* self,
                                            PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int full;
  static const char* kwlist[] = {"full", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &full)) {
    return nullptr;
  }
  InputDevice* d = self->input_device_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return PyUnicode_FromString(
      d->GetAccountName(static_cast<bool>(full)).c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::IsConnectedToRemotePlayer(
    PythonClassInputDevice* self) -> PyObject* {
  BA_PYTHON_TRY;
  InputDevice* input_device = self->input_device_->get();
  if (!input_device) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  if (input_device->GetRemotePlayer()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::Exists(PythonClassInputDevice* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (self->input_device_->exists()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetAxisName(PythonClassInputDevice* self,
                                         PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  int id;
  static const char* kwlist[] = {"axis_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &id)) {
    return nullptr;
  }
  InputDevice* input_device = self->input_device_->get();
  if (!input_device) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return PyUnicode_FromString(input_device->GetAxisName(id).c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetButtonName(PythonClassInputDevice* self,
                                           PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InGameThread());
  int id{};
  static const char* kwlist[] = {"button_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &id)) {
    return nullptr;
  }
  InputDevice* d = self->input_device_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }

  // Ask the input-device for the button name.
  std::string bname = d->GetButtonName(id);

  // If this doesn't appear to be lstr json itself, convert it to that.
  if (bname.length() < 1 || bname.c_str()[0] != '{') {
    Utils::StringReplaceAll(&bname, "\"", "\\\"");
    bname = R"({"v":")" + bname + "\"}";
  }
  PythonRef args2(Py_BuildValue("(s)", bname.c_str()), PythonRef::kSteal);
  PythonRef results =
      g_python->obj(Python::ObjID::kLstrFromJsonCall).Call(args2);
  if (!results.exists()) {
    Log("Error creating Lstr from raw button name: '" + bname + "'");
    PythonRef args3(Py_BuildValue("(s)", "?"), PythonRef::kSteal);
    results = g_python->obj(Python::ObjID::kLstrFromJsonCall).Call(args3);
  }
  if (!results.exists()) {
    throw Exception("Internal error creating Lstr.");
  }
  return results.NewRef();

  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassInputDevice::type_obj;
PyMethodDef PythonClassInputDevice::tp_methods[] = {
    {"remove_remote_player_from_game", (PyCFunction)RemoveRemotePlayerFromGame,
     METH_NOARGS,
     "remove_remote_player_from_game() -> None\n"
     "\n"
     "(internal)"},
    {"is_connected_to_remote_player", (PyCFunction)IsConnectedToRemotePlayer,
     METH_NOARGS,
     "is_connected_to_remote_player() -> bool\n"
     "\n"
     "(internal)"},
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Return whether the underlying device for this object is\n"
     "still present.\n"},
    {"get_button_name", (PyCFunction)GetButtonName,
     METH_VARARGS | METH_KEYWORDS,  // NOLINT (signed bitwise ops)
     "get_button_name(button_id: int) -> ba.Lstr\n"
     "\n"
     "Given a button ID, return a human-readable name for that key/button.\n"
     "\n"
     "Can return an empty string if the value is not meaningful to humans."},
    // NOLINTNEXTLINE (signed bitwise ops)
    {"get_axis_name", (PyCFunction)GetAxisName, METH_VARARGS | METH_KEYWORDS,
     "get_axis_name(axis_id: int) -> str\n"
     "\n"
     "Given an axis ID, return the name of the axis on this device.\n"
     "\n"
     "Can return an empty string if the value is not meaningful to humans."},
    {"get_default_player_name", (PyCFunction)GetDefaultPlayerName, METH_NOARGS,
     "get_default_player_name() -> str\n"
     "\n"
     "(internal)\n"
     "\n"
     "Returns the default player name for this device. (used for the 'random'\n"
     "profile)"},
    {"get_account_name", (PyCFunction)GetAccountName,
     METH_VARARGS | METH_KEYWORDS,  // NOLINT (signed bitwise ops)
     "get_account_name(full: bool) -> str\n"
     "\n"
     "Returns the account name associated with this device.\n"
     "\n"
     "(can be used to get account names for remote players)"},
    {"get_player_profiles", (PyCFunction)GetPlayerProfiles, METH_NOARGS,
     "get_player_profiles() -> dict\n"
     "\n"
     "(internal)"},
    {nullptr}};  // namespace ballistica

#pragma clang diagnostic pop

}  // namespace ballistica
