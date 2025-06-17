// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_input_device.h"

#include <string>

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "RedundantCast"

auto PythonClassInputDevice::type_name() -> const char* {
  return "InputDevice";
}

void PythonClassInputDevice::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.InputDevice";
  cls->tp_basicsize = sizeof(PythonClassInputDevice);
  cls->tp_doc =
      "An input-device such as a gamepad, touchscreen, or keyboard.\n"
      "\n"
      "Attributes:\n"
      "\n"
      "   allows_configuring (bool):\n"
      "      Whether the input-device can be configured in the app.\n"
      "\n"
      "   allows_configuring_in_system_settings (bool):\n"
      "      Whether the input-device can be configured in the system.\n"
      "      setings app. This can be used to redirect the user to go there\n"
      "      if they attempt to configure the device.\n"
      "\n"
      "   has_meaningful_button_names (bool):\n"
      "      Whether button names returned by this instance match labels\n"
      "      on the actual device. (Can be used to determine whether to show\n"
      "      them in controls-overlays, etc.).\n"
      "\n"
      "   player (bascenev1.SessionPlayer | None):\n"
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
      "\n"
      "   is_test_input (bool):\n"
      "      Whether this input-device is a dummy device for testing.\n"
      "\n";

  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
  cls->tp_getattro = (getattrofunc)tp_getattro;
  cls->tp_setattro = (setattrofunc)tp_setattro;

  // We provide number methods only for bool functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_bool = (inquiry)nb_bool;
  cls->tp_as_number = &as_number_;
}

auto PythonClassInputDevice::Create(SceneV1InputDeviceDelegate* input_device)
    -> PyObject* {
  // Make sure we only have one python ref per material.
  if (input_device) {
    assert(!input_device->HasPyRef());
  }
  assert(TypeIsSetUp(&type_obj));
  auto* py_input_device = reinterpret_cast<PythonClassInputDevice*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_input_device) {
    throw Exception("bascenev1.InputDevice creation failed.");
  }
  *py_input_device->input_device_delegate_ = input_device;
  return reinterpret_cast<PyObject*>(py_input_device);
}

auto PythonClassInputDevice::GetInputDevice() const
    -> SceneV1InputDeviceDelegate* {
  SceneV1InputDeviceDelegate* input_device = input_device_delegate_->get();
  if (!input_device) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return input_device;
}

auto PythonClassInputDevice::tp_repr(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneV1InputDeviceDelegate* d = self->input_device_delegate_->get();
  int input_device_id = d ? d->input_device().index() : -1;
  std::string dname = d ? d->input_device().GetDeviceName() : "invalid device";
  return Py_BuildValue("s",
                       (std::string("<Ballistica InputDevice ")
                        + std::to_string(input_device_id) + " (" + dname + ")>")
                           .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::nb_bool(PythonClassInputDevice* self) -> int {
  return self->input_device_delegate_->exists();
}

PyNumberMethods PythonClassInputDevice::as_number_;

auto PythonClassInputDevice::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassInputDevice*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  self->input_device_delegate_ =
      new Object::WeakRef<SceneV1InputDeviceDelegate>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassInputDevice::tp_dealloc(PythonClassInputDevice* self) {
  BA_PYTHON_TRY;
  // These have to be destructed in the logic thread - send them along to it if
  // need be.
  // FIXME: Technically the main thread has a pointer to a dead PyObject
  //  until the delete goes through; could that ever be a problem?
  if (!g_base->InLogicThread()) {
    Object::WeakRef<SceneV1InputDeviceDelegate>* d =
        self->input_device_delegate_;
    g_base->logic->event_loop()->PushCall([d] { delete d; });
  } else {
    delete self->input_device_delegate_;
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
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    Player* player = d->GetPlayer();
    if (player != nullptr) {
      return player->NewPyRef();
    }
    Py_RETURN_NONE;
  } else if (!strcmp(s, "allows_configuring")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (d->input_device().GetAllowsConfiguring()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "allows_configuring_in_system_settings")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (d->input_device().IsMFiController()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "has_meaningful_button_names")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (d->input_device().HasMeaningfulButtonNames()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "client_id")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyLong_FromLong(d->GetClientID());
  } else if (!strcmp(s, "name")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyUnicode_FromString(d->input_device().GetDeviceName().c_str());
  } else if (!strcmp(s, "unique_identifier")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyUnicode_FromString(
        d->input_device().GetPersistentIdentifier().c_str());
  } else if (!strcmp(s, "id")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyLong_FromLong(d->input_device().index());
  } else if (!strcmp(s, "instance_number")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    return PyLong_FromLong(d->input_device().number());
  } else if (!strcmp(s, "is_controller_app")) {
    auto* d = self->input_device_delegate_->get();
    if (!d) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (d->input_device().IsRemoteApp()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "is_remote_client")) {
    auto* delegate = self->input_device_delegate_->get();
    if (!delegate) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (delegate->IsRemoteClient()) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (!strcmp(s, "is_test_input")) {
    auto* delegate = self->input_device_delegate_->get();
    if (!delegate) {
      throw Exception(PyExcType::kInputDeviceNotFound);
    }
    if (delegate->input_device().IsTestInput()) {
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

auto PythonClassInputDevice::DetachFromPlayer(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneV1InputDeviceDelegate* d = self->input_device_delegate_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  d->DetachFromPlayer();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetDefaultPlayerName(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneV1InputDeviceDelegate* d = self->input_device_delegate_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return PyUnicode_FromString(d->GetDefaultPlayerName().c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetPlayerProfiles(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneV1InputDeviceDelegate* d = self->input_device_delegate_->get();
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

auto PythonClassInputDevice::GetV1AccountName(PythonClassInputDevice* self,
                                              PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int full;
  static const char* kwlist[] = {"full", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &full)) {
    return nullptr;
  }
  SceneV1InputDeviceDelegate* d = self->input_device_delegate_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return PyUnicode_FromString(
      d->GetAccountName(static_cast<bool>(full)).c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::IsAttachedToPlayer(PythonClassInputDevice* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  SceneV1InputDeviceDelegate* input_device =
      self->input_device_delegate_->get();
  if (!input_device) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  if (input_device->AttachedToPlayer()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::Exists(PythonClassInputDevice* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (self->input_device_delegate_->exists()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetAxisName(PythonClassInputDevice* self,
                                         PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  int id;
  static const char* kwlist[] = {"axis_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &id)) {
    return nullptr;
  }
  SceneV1InputDeviceDelegate* input_device =
      self->input_device_delegate_->get();
  if (!input_device) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }
  return PyUnicode_FromString(
      input_device->input_device().GetAxisName(id).c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassInputDevice::GetButtonName(PythonClassInputDevice* self,
                                           PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  int id{};
  static const char* kwlist[] = {"button_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &id)) {
    return nullptr;
  }
  SceneV1InputDeviceDelegate* d = self->input_device_delegate_->get();
  if (!d) {
    throw Exception(PyExcType::kInputDeviceNotFound);
  }

  // Ask the input-device for the button name.
  std::string bname = d->input_device().GetButtonName(id);

  // If this doesn't appear to be lstr json itself, convert it to that.
  if (bname.length() < 1 || bname.c_str()[0] != '{') {
    Utils::StringReplaceAll(&bname, "\"", "\\\"");
    bname = R"({"v":")" + bname + "\"}";
  }
  PythonRef args2(Py_BuildValue("(s)", bname.c_str()), PythonRef::kSteal);
  PythonRef results = g_base->python->objs()
                          .Get(base::BasePython::ObjID::kLstrFromJsonCall)
                          .Call(args2);
  if (!results.exists()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Error creating Lstr from raw button name: '" + bname + "'");
    PythonRef args3(Py_BuildValue("(s)", "?"), PythonRef::kSteal);
    results = g_base->python->objs()
                  .Get(base::BasePython::ObjID::kLstrFromJsonCall)
                  .Call(args3);
  }
  if (!results.exists()) {
    throw Exception("Internal error creating Lstr.");
  }
  return results.NewRef();

  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassInputDevice::type_obj;
PyMethodDef PythonClassInputDevice::tp_methods[] = {
    {"detach_from_player", (PyCFunction)DetachFromPlayer, METH_NOARGS,
     "detach_from_player() -> None\n"
     "\n"
     "Detach the device from any player it is controlling.\n"
     "\n"
     "This applies both to local players and remote players."},
    {"is_attached_to_player", (PyCFunction)IsAttachedToPlayer, METH_NOARGS,
     "is_attached_to_player() -> bool\n"
     "\n"
     "Return whether this device is controlling a player of some sort.\n"
     "\n"
     "This can mean either a local player or a remote player."},
    {"exists", (PyCFunction)Exists, METH_NOARGS,
     "exists() -> bool\n"
     "\n"
     "Return whether the underlying device for this object is\n"
     "still present.\n"},
    {"get_button_name", (PyCFunction)GetButtonName,
     METH_VARARGS | METH_KEYWORDS,  // NOLINT (signed bitwise ops)
     "get_button_name(button_id: int) -> babase.Lstr\n"
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
    {"get_v1_account_name", (PyCFunction)GetV1AccountName,
     METH_VARARGS | METH_KEYWORDS,  // NOLINT (signed bitwise ops)
     "get_v1_account_name(full: bool) -> str\n"
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

}  // namespace ballistica::scene_v1
