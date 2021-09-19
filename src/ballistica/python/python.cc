// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/python.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/audio/audio.h"
#include "ballistica/dynamics/material/material.h"
#include "ballistica/game/account.h"
#include "ballistica/game/friend_score_set.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/player.h"
#include "ballistica/game/score_to_beat.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/input/device/joystick.h"
#include "ballistica/input/device/keyboard_input.h"
#include "ballistica/media/component/collide_model.h"
#include "ballistica/media/component/model.h"
#include "ballistica/media/component/sound.h"
#include "ballistica/media/component/texture.h"
#include "ballistica/python/class/python_class_activity_data.h"
#include "ballistica/python/class/python_class_collide_model.h"
#include "ballistica/python/class/python_class_context.h"
#include "ballistica/python/class/python_class_context_call.h"
#include "ballistica/python/class/python_class_data.h"
#include "ballistica/python/class/python_class_input_device.h"
#include "ballistica/python/class/python_class_material.h"
#include "ballistica/python/class/python_class_model.h"
#include "ballistica/python/class/python_class_node.h"
#include "ballistica/python/class/python_class_session_data.h"
#include "ballistica/python/class/python_class_session_player.h"
#include "ballistica/python/class/python_class_sound.h"
#include "ballistica/python/class/python_class_texture.h"
#include "ballistica/python/class/python_class_timer.h"
#include "ballistica/python/class/python_class_vec3.h"
#include "ballistica/python/class/python_class_widget.h"
#include "ballistica/python/methods/python_methods_app.h"
#include "ballistica/python/methods/python_methods_gameplay.h"
#include "ballistica/python/methods/python_methods_graphics.h"
#include "ballistica/python/methods/python_methods_input.h"
#include "ballistica/python/methods/python_methods_media.h"
#include "ballistica/python/methods/python_methods_system.h"
#include "ballistica/python/methods/python_methods_ui.h"
#include "ballistica/python/python_command.h"
#include "ballistica/python/python_context_call_runnable.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/text_widget.h"

// Sanity test: our XCode, Android, and Windows builds should be
// using a debug build of the python library.
// Todo: could also verify this at runtime by checking for
// existence of sys.gettotalrefcount(). (is that still valid in 3.8?)
#if BA_DEBUG_BUILD
#if BA_XCODE_BUILD || BA_OSTYPE_ANDROID || BA_OSTYPE_WINDOWS
#ifndef Py_DEBUG
#error Expected Py_DEBUG to be defined for this build.
#endif  // Py_DEBUG
#endif  // BA_XCODE_BUILD || BA_OSTYPE_ANDROID
#endif  // BA_DEBUG_BUILD

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

// Used by our built in exception type.
void Python::SetPythonException(PyExcType exctype, const char* description) {
  PyObject* pytype{};
  switch (exctype) {
    case PyExcType::kRuntime:
      pytype = PyExc_RuntimeError;
      break;
    case PyExcType::kAttribute:
      pytype = PyExc_AttributeError;
      break;
    case PyExcType::kIndex:
      pytype = PyExc_IndexError;
      break;
    case PyExcType::kValue:
      pytype = PyExc_ValueError;
      break;
    case PyExcType::kType:
      pytype = PyExc_TypeError;
      break;
    case PyExcType::kContext:
      pytype = g_python->obj(Python::ObjID::kContextError).get();
      break;
    case PyExcType::kNotFound:
      pytype = g_python->obj(Python::ObjID::kNotFoundError).get();
      break;
    case PyExcType::kNodeNotFound:
      pytype = g_python->obj(Python::ObjID::kNodeNotFoundError).get();
      break;
    case PyExcType::kSessionPlayerNotFound:
      pytype = g_python->obj(Python::ObjID::kSessionPlayerNotFoundError).get();
      break;
    case PyExcType::kInputDeviceNotFound:
      pytype = g_python->obj(Python::ObjID::kInputDeviceNotFoundError).get();
      break;
    case PyExcType::kDelegateNotFound:
      pytype = g_python->obj(Python::ObjID::kDelegateNotFoundError).get();
      break;
    case PyExcType::kWidgetNotFound:
      pytype = g_python->obj(Python::ObjID::kWidgetNotFoundError).get();
      break;
    case PyExcType::kActivityNotFound:
      pytype = g_python->obj(Python::ObjID::kActivityNotFoundError).get();
      break;
    case PyExcType::kSessionNotFound:
      pytype = g_python->obj(Python::ObjID::kSessionNotFoundError).get();
      break;
  }
  assert(pytype != nullptr && PyType_Check(pytype));
  PyErr_SetString(pytype, description);
}

const char* Python::ScopedCallLabel::current_label_ = nullptr;

auto Python::HaveGIL() -> bool { return static_cast<bool>(PyGILState_Check()); }

void Python::PrintStackTrace() {
  ScopedInterpreterLock lock;
  auto objid{Python::ObjID::kPrintTraceCall};
  if (g_python->objexists(objid)) {
    g_python->obj(objid).Call();
  } else {
    Log("Warning: Python::PrintStackTrace() called before bootstrap complete; "
        "not printing.");
  }
}

// Return whether GetPyString() will succeed for an object.
auto Python::IsPyString(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  return (PyUnicode_Check(o)
          || PyObject_IsInstance(
              o, g_python->obj(Python::ObjID::kLStrClass).get()));
}

auto Python::GetPyString(PyObject* o) -> std::string {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType exctype{PyExcType::kType};
  if (PyUnicode_Check(o)) {
    return PyUnicode_AsUTF8(o);
  } else {
    // Check if its a Lstr.  If so; we pull its json string representation.
    int result =
        PyObject_IsInstance(o, g_python->obj(Python::ObjID::kLStrClass).get());
    if (result == -1) {
      PyErr_Clear();
      result = 0;
    }
    if (result == 1) {
      // At this point its not a simple type error if something goes wonky.
      // Perhaps we should try to preserve any error type raised by
      // the _get_json() call...
      exctype = PyExcType::kRuntime;
      PythonRef get_json_call(PyObject_GetAttrString(o, "_get_json"),
                              PythonRef::kSteal);
      if (get_json_call.CallableCheck()) {
        PythonRef json = get_json_call.Call();
        if (PyUnicode_Check(json.get())) {
          return PyUnicode_AsUTF8(json.get());
        }
      }
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get string from value: " + Python::ObjToString(o) + ".", exctype);
}

template <typename T>
auto GetPyIntT(PyObject* o) -> T {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PyLong_Check(o)) {
    return static_cast_check_fit<T>(PyLong_AS_LONG(o));
  }
  if (PyNumber_Check(o)) {
    PyObject* f = PyNumber_Long(o);
    if (f) {
      auto val = static_cast_check_fit<T>(PyLong_AS_LONG(f));
      Py_DECREF(f);
      return val;
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();

  // Assuming any failure here was type related.
  throw Exception("Can't get int from value: " + Python::ObjToString(o) + ".",
                  PyExcType::kType);
}

auto Python::GetPyInt64(PyObject* o) -> int64_t {
  return GetPyIntT<int64_t>(o);
}

auto Python::GetPyInt(PyObject* o) -> int { return GetPyIntT<int>(o); }

auto Python::GetPyBool(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (o == Py_True) {
    return true;
  }
  if (o == Py_False) {
    return false;
  }
  if (PyLong_Check(o)) {
    return (PyLong_AS_LONG(o) != 0);
  }
  if (PyNumber_Check(o)) {
    if (PyObject* o2 = PyNumber_Long(o)) {
      auto val = PyLong_AS_LONG(o2);
      Py_DECREF(o2);
      return (val != 0);
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();

  // Assuming any failure here was type related.
  throw Exception("Can't get bool from value: " + Python::ObjToString(o) + ".",
                  PyExcType::kType);
}

auto Python::IsPySession(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  int result =
      PyObject_IsInstance(o, g_python->obj(ObjID::kSessionClass).get());
  if (result == -1) {
    PyErr_Clear();
    result = 0;
  }
  return static_cast<bool>(result);
}

auto Python::GetPySession(PyObject* o) -> Session* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType pyexctype{PyExcType::kType};
  if (IsPySession(o)) {
    // Look for an _sessiondata attr on it.
    if (PyObject* sessiondata = PyObject_GetAttrString(o, "_sessiondata")) {
      // This will deallocate for us.
      PythonRef ref(sessiondata, PythonRef::kSteal);
      if (PythonClassSessionData::Check(sessiondata)) {
        // This will succeed or throw its own Exception.
        return (reinterpret_cast<PythonClassSessionData*>(sessiondata))
            ->GetSession();
      }
    } else {
      pyexctype = PyExcType::kRuntime;  // Wonky session obj.
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get Session from value: " + Python::ObjToString(o) + ".",
      pyexctype);
}

auto Python::IsPyPlayer(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  int result = PyObject_IsInstance(o, g_python->obj(ObjID::kPlayerClass).get());
  if (result == -1) {
    result = 0;
    PyErr_Clear();
  }
  return static_cast<bool>(result);
}

auto Python::GetPyPlayer(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Player* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType pyexctype{PyExcType::kType};

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }

  // Make sure it's a subclass of ba.Player.
  if (IsPyPlayer(o)) {
    // Look for an sessionplayer attr on it.
    if (PyObject* sessionplayer = PyObject_GetAttrString(o, "sessionplayer")) {
      // This will deallocate for us.
      PythonRef ref(sessionplayer, PythonRef::kSteal);

      if (PythonClassSessionPlayer::Check(sessionplayer)) {
        // This will succeed or throw an exception itself.
        return (reinterpret_cast<PythonClassSessionPlayer*>(sessionplayer))
            ->GetPlayer(!allow_empty_ref);
      }
    } else {
      pyexctype = PyExcType::kRuntime;  // We've got a wonky object.
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get player from value: " + Python::ObjToString(o) + ".",
      pyexctype);
}

auto Python::IsPyHostActivity(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  int result =
      PyObject_IsInstance(o, g_python->obj(ObjID::kActivityClass).get());
  if (result == -1) {
    result = 0;
    PyErr_Clear();
  }
  return static_cast<bool>(result);
}

auto Python::GetPyHostActivity(PyObject* o) -> HostActivity* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  PyExcType pyexctype{PyExcType::kType};

  // Make sure it's a subclass of ba.Activity.
  if (IsPyHostActivity(o)) {
    // Look for an _activity_data attr on it.
    if (PyObject* activity_data = PyObject_GetAttrString(o, "_activity_data")) {
      // This will deallocate for us.
      PythonRef ref(activity_data, PythonRef::kSteal);
      if (PythonClassActivityData::Check(activity_data)) {
        return (reinterpret_cast<PythonClassActivityData*>(activity_data))
            ->GetHostActivity();
      }
    } else {
      pyexctype = PyExcType::kRuntime;  // activity obj is wonky.
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get activity from value: " + Python::ObjToString(o) + ".",
      pyexctype);
}

auto Python::GetPyNode(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Node* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassNode::Check(o)) {
    // This will succeed or throw its own Exception.
    return (reinterpret_cast<PythonClassNode*>(o))->GetNode(!allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception("Can't get node from value: " + Python::ObjToString(o) + ".",
                  PyExcType::kType);
}

auto Python::GetPyInputDevice(PyObject* o) -> InputDevice* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PythonClassInputDevice::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassInputDevice*>(o)->GetInputDevice();
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get input-device from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPySessionPlayer(PyObject* o, bool allow_empty_ref,
                                bool allow_none) -> Player* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSessionPlayer::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSessionPlayer*>(o)->GetPlayer(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get ba.SessionPlayer from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyTexture(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Texture* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassTexture::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassTexture*>(o)->GetTexture(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get ba.Texture from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyModel(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Model* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassModel::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassModel*>(o)->GetModel(!allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get ba.Model from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPySound(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Sound* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassSound::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassSound*>(o)->GetSound(!allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get ba.Sound from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyData(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Data* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassData::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassData*>(o)->GetData(!allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get ba.Data from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyCollideModel(PyObject* o, bool allow_empty_ref,
                               bool allow_none) -> CollideModel* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassCollideModel::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassCollideModel*>(o)->GetCollideModel(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get ba.CollideModel from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyWidget(PyObject* o) -> Widget* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PythonClassWidget::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassWidget*>(o)->GetWidget();
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get widget from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyMaterial(PyObject* o, bool allow_empty_ref, bool allow_none)
    -> Material* {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (allow_none && (o == Py_None)) {
    return nullptr;
  }
  if (PythonClassMaterial::Check(o)) {
    // This will succeed or throw its own Exception.
    return reinterpret_cast<PythonClassMaterial*>(o)->GetMaterial(
        !allow_empty_ref);
  }

  // Nothing here should have led to an unresolved Python error state.
  assert(!PyErr_Occurred());

  throw Exception(
      "Can't get material from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::CanGetPyDouble(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  return static_cast<bool>(PyNumber_Check(o));
}

auto Python::GetPyDouble(PyObject* o) -> double {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  // Try to take the fast path if its a float.
  if (PyFloat_Check(o)) {
    return PyFloat_AS_DOUBLE(o);
  }
  if (PyNumber_Check(o)) {
    if (PyObject* f = PyNumber_Float(o)) {
      double val = PyFloat_AS_DOUBLE(f);
      Py_DECREF(f);
      return val;
    }
  }

  // Failed, we have.
  // Clear any Python error that got us here; we're in C++ Exception land now.
  PyErr_Clear();
  throw Exception(
      "Can't get double from value: " + Python::ObjToString(o) + ".",
      PyExcType::kType);
}

auto Python::GetPyFloats(PyObject* o) -> std::vector<float> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  Py_ssize_t size = PySequence_Fast_GET_SIZE(sequence.get());
  PyObject** py_objects = PySequence_Fast_ITEMS(sequence.get());
  std::vector<float> vals(static_cast<size_t>(size));
  assert(vals.size() == size);
  for (Py_ssize_t i = 0; i < size; i++) {
    vals[i] = Python::GetPyFloat(py_objects[i]);
  }
  return vals;
}

auto Python::GetPyStrings(PyObject* o) -> std::vector<std::string> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  Py_ssize_t size = PySequence_Fast_GET_SIZE(sequence.get());
  PyObject** py_objects = PySequence_Fast_ITEMS(sequence.get());
  std::vector<std::string> vals(static_cast<size_t>(size));
  assert(vals.size() == size);
  for (Py_ssize_t i = 0; i < size; i++) {
    vals[i] = Python::GetPyString(py_objects[i]);
  }
  return vals;
}

template <typename T>
auto GetPyIntsT(PyObject* o) -> std::vector<T> {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  Py_ssize_t size = PySequence_Fast_GET_SIZE(sequence.get());
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<T> vals(static_cast<size_t>(size));
  assert(vals.size() == size);
  for (Py_ssize_t i = 0; i < size; i++) {
    vals[i] = GetPyIntT<T>(pyobjs[i]);
  }
  return vals;
}

auto Python::GetPyInts64(PyObject* o) -> std::vector<int64_t> {
  return GetPyIntsT<int64_t>(o);
}

auto Python::GetPyInts(PyObject* o) -> std::vector<int> {
  return GetPyIntsT<int>(o);
}

// Hmm should just template the above func?
auto Python::GetPyUInts64(PyObject* o) -> std::vector<uint64_t> {
  return GetPyIntsT<uint64_t>(o);
}

auto Python::GetPyNodes(PyObject* o) -> std::vector<Node*> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Node*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = Python::GetPyNode(pyobjs[i]);
  }
  return vals;
}

auto Python::GetPyMaterials(PyObject* o) -> std::vector<Material*> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Material*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPyMaterial(pyobjs[i]);  // DON'T allow nullptr refs.
  }
  return vals;
}

auto Python::GetPyTextures(PyObject* o) -> std::vector<Texture*> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Texture*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPyTexture(pyobjs[i]);  // DON'T allow nullptr refs or None.
  }
  return vals;
}

auto Python::GetPySounds(PyObject* o) -> std::vector<Sound*> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Sound*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPySound(pyobjs[i]);  // DON'T allow nullptr refs
  }
  return vals;
}

auto Python::GetPyModels(PyObject* o) -> std::vector<Model*> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<Model*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPyModel(pyobjs[i], false);  // DON'T allow nullptr refs.
  }
  return vals;
}

auto Python::GetPyCollideModels(PyObject* o) -> std::vector<CollideModel*> {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (!PySequence_Check(o)) {
    throw Exception("Object is not a sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());
  auto size = static_cast<size_t>(PySequence_Fast_GET_SIZE(sequence.get()));
  PyObject** pyobjs = PySequence_Fast_ITEMS(sequence.get());
  std::vector<CollideModel*> vals(size);
  assert(vals.size() == size);
  for (size_t i = 0; i < size; i++) {
    vals[i] = GetPyCollideModel(pyobjs[i]);  // DON'T allow nullptr refs.
  }
  return vals;
}

auto Python::GetPyPoint2D(PyObject* o) -> Point2D {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  Point2D p;
  if (!PyTuple_Check(o) || (PyTuple_GET_SIZE(o) != 2)) {
    throw Exception("Expected 2 member tuple for point.", PyExcType::kType);
  }
  p.x = Python::GetPyFloat(PyTuple_GET_ITEM(o, 0));
  p.y = Python::GetPyFloat(PyTuple_GET_ITEM(o, 1));
  return p;
}

auto Python::CanGetPyVector3f(PyObject* o) -> bool {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PythonClassVec3::Check(o)) {
    return true;
  }
  if (!PySequence_Check(o)) {
    return false;
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());  // Should always work; we checked seq.
  if (PySequence_Fast_GET_SIZE(sequence.get()) != 3) {
    return false;
  }
  return (
      Python::CanGetPyDouble(PySequence_Fast_GET_ITEM(sequence.get(), 0))
      && Python::CanGetPyDouble(PySequence_Fast_GET_ITEM(sequence.get(), 1))
      && Python::CanGetPyDouble(PySequence_Fast_GET_ITEM(sequence.get(), 2)));
}

auto Python::GetPyVector3f(PyObject* o) -> Vector3f {
  assert(HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PythonClassVec3::Check(o)) {
    return (reinterpret_cast<PythonClassVec3*>(o))->value;
  }
  if (!PySequence_Check(o)) {
    throw Exception("Object is not a ba.Vec3 or sequence.", PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());  // Should always work; we checked seq.
  if (PySequence_Fast_GET_SIZE(sequence.get()) != 3) {
    throw Exception("Sequence is not of size 3.", PyExcType::kValue);
  }
  return {Python::GetPyFloat(PySequence_Fast_GET_ITEM(sequence.get(), 0)),
          Python::GetPyFloat(PySequence_Fast_GET_ITEM(sequence.get(), 1)),
          Python::GetPyFloat(PySequence_Fast_GET_ITEM(sequence.get(), 2))};
}

Python::Python() = default;

void Python::Reset(bool do_init) {
  assert(InGameThread());
  assert(g_python);

  bool was_inited = inited_;

  if (inited_) {
    ReleaseGamePadInput();
    ReleaseKeyboardInput();
    g_graphics->ReleaseFadeEndCommand();
    inited_ = false;
  }

  if (!was_inited && do_init) {
    // Flip on some extra runtime debugging options in debug builds.
    // https://docs.python.org/3.9/library/devmode.html#devmode
    int dev_mode{g_buildconfig.debug_build()};

    // Pre-config as isolated if we include our own Python and as standard
    // otherwise.
    PyPreConfig preconfig;
    if (g_platform->ContainsPythonDist()) {
      PyPreConfig_InitIsolatedConfig(&preconfig);
    } else {
      PyPreConfig_InitPythonConfig(&preconfig);
    }
    preconfig.dev_mode = dev_mode;

    // We want consistent utf-8 everywhere (Python used to default to
    // windows-specific file encodings, etc.)
    preconfig.utf8_mode = 1;

    PyStatus status = Py_PreInitialize(&preconfig);
    BA_PRECONDITION(!PyStatus_Exception(status));

    // Configure as isolated if we include our own Python and as standard
    // otherwise.
    PyConfig config;
    if (g_platform->ContainsPythonDist()) {
      PyConfig_InitIsolatedConfig(&config);
    } else {
      PyConfig_InitPythonConfig(&config);
    }
    config.dev_mode = dev_mode;
    if (!g_buildconfig.debug_build()) {
      config.optimization_level = 1;
    }

    // In cases where we bundle Python, set up all paths explicitly.
    // see https://docs.python.org/3.8/
    //     c-api/init_config.html#path-configuration
    if (g_platform->ContainsPythonDist()) {
      PyConfig_SetBytesString(&config, &config.base_exec_prefix, "");
      PyConfig_SetBytesString(&config, &config.base_executable, "");
      PyConfig_SetBytesString(&config, &config.base_prefix, "");
      PyConfig_SetBytesString(&config, &config.exec_prefix, "");
      PyConfig_SetBytesString(&config, &config.executable, "");
      PyConfig_SetBytesString(&config, &config.prefix, "");

      // Interesting note: it seems we can pass relative paths here but
      // they wind up in sys.path as absolute paths (unlike entries we add
      // to sys.path after things are up and running).
      if (g_buildconfig.ostype_windows()) {
        // Windows Python looks for Lib and DLLs dirs by default, along with
        // some others, but we want to be more explicit in limiting to these. It
        // also seems that windows Python's paths can be incorrect if we're in
        // strange dirs such as \\wsl$\Ubuntu-18.04\ that we get with WSL build
        // setups.

        // NOTE: Python for windows actually comes with 'Lib', not 'lib', but
        // it seems the interpreter defaults point to ./lib (as of 3.8.5).
        // Normally this doesn't matter since windows is case-insensitive but
        // under WSL it does.
        // So we currently bundle the dir as 'lib' and use that in our path so
        // that everything is happy (both with us and with python.exe).
        PyWideStringList_Append(&config.module_search_paths,
                                Py_DecodeLocale("lib", nullptr));
        PyWideStringList_Append(&config.module_search_paths,
                                Py_DecodeLocale("DLLs", nullptr));
      } else {
        PyWideStringList_Append(&config.module_search_paths,
                                Py_DecodeLocale("pylib", nullptr));
      }
      config.module_search_paths_set = 1;
    }

    // Inits our _ba module and runs Py_Initialize().
    AppInternalPyInitialize(&config);

    // Grab __main__ in case we need to use it later.
    PyObject* m;
    BA_PRECONDITION(m = PyImport_AddModule("__main__"));
    BA_PRECONDITION(main_dict_ = PyModule_GetDict(m));

    const char* ver = Py_GetVersion();
    if (strncmp(ver, "3.8", 3) != 0) {
      throw Exception("We require Python 3.8.x; instead found "
                      + std::string(ver));
    }

    // Create a dict for execing our bootstrap code in so
    // we don't pollute the __main__ namespace.
    auto bootstrap_context{PythonRef(PyDict_New(), PythonRef::kSteal)};

    // Get the app up and running.
    // Run a few core bootstrappy things first:
    // - get stdout/stderr redirection up so we can intercept python output
    // - add our user and system script dirs to python path
    // - import and instantiate our app-state class

#include "ballistica/generated/python_embedded/bootstrap.inc"
    PyObject* result =
        PyRun_String(bootstrap_code, Py_file_input, bootstrap_context.get(),
                     bootstrap_context.get());
    if (result == nullptr) {
      PyErr_PrintEx(0);

      // Throw a simple exception so we don't get a stack trace.
      throw std::logic_error(
          "Error in ba Python bootstrapping. See log for details.");
    }
    Py_DECREF(result);

    // Import and grab all the Python stuff we use.
#include "ballistica/generated/python_embedded/binding.inc"

    AppInternalPythonPostInit();

    // Alright I guess let's pull ba in to main, since pretty
    // much all interactive commands will be using it.
    // If we ever build the game as a pure python module we should
    // of course not do this.
    BA_PRECONDITION(PyRun_SimpleString("import ba") == 0);

    // Read the config file and store the config dict for easy access.
    obj(ObjID::kReadConfigCall).Call();
    StoreObj(ObjID::kConfig, obj(ObjID::kApp).GetAttr("config").get());
    assert(PyDict_Check(obj(ObjID::kConfig).get()));

    // Turn off fancy-pants cyclic garbage-collection.
    // We run it only at explicit times to avoid random hitches and keep
    // things more deterministic.
    // Non-reference-looped objects will still get cleaned up
    // immediately, so we should try to structure things to avoid
    // reference loops (just like Swift, ObjC, etc).
    g_python->obj(Python::ObjID::kGCDisableCall).Call();
  }
  if (do_init) {
    inited_ = true;
  }
}

auto Python::GetModuleMethods() -> std::vector<PyMethodDef> {
  std::vector<PyMethodDef> all_methods;
  for (auto&& methods : {
           PythonMethodsUI::GetMethods(),
           PythonMethodsInput::GetMethods(),
           PythonMethodsApp::GetMethods(),
           PythonMethodsGameplay::GetMethods(),
           PythonMethodsGraphics::GetMethods(),
           PythonMethodsMedia::GetMethods(),
           PythonMethodsSystem::GetMethods(),
       }) {
    all_methods.insert(all_methods.end(), methods.begin(), methods.end());
  }
  return all_methods;
}

template <class T>
auto AddClass(PyObject* module) -> PyObject* {
  T::SetupType(&T::type_obj);
  BA_PRECONDITION(PyType_Ready(&T::type_obj) == 0);
  Py_INCREF(&T::type_obj);
  int r = PyModule_AddObject(module, T::type_name(),
                             reinterpret_cast<PyObject*>(&T::type_obj));
  BA_PRECONDITION(r == 0);
  return reinterpret_cast<PyObject*>(&T::type_obj);
}
auto Python::InitModuleClasses(PyObject* module) -> void {
  // Init our classes and add them to our module.
  AddClass<PythonClassNode>(module);
  AddClass<PythonClassWidget>(module);
  AddClass<PythonClassSessionPlayer>(module);
  AddClass<PythonClassSessionData>(module);
  AddClass<PythonClassActivityData>(module);
  AddClass<PythonClassContext>(module);
  AddClass<PythonClassContextCall>(module);
  AddClass<PythonClassInputDevice>(module);
  AddClass<PythonClassTimer>(module);
  AddClass<PythonClassMaterial>(module);
  AddClass<PythonClassTexture>(module);
  AddClass<PythonClassSound>(module);
  AddClass<PythonClassData>(module);
  AddClass<PythonClassModel>(module);
  AddClass<PythonClassCollideModel>(module);
  PyObject* vec3 = AddClass<PythonClassVec3>(module);

  // Register our vec3 as an abc.Sequence
  auto register_call =
      PythonRef(PyImport_ImportModule("collections.abc"), PythonRef::kSteal)
          .GetAttr("Sequence")
          .GetAttr("register");
  PythonRef args(Py_BuildValue("(O)", vec3), PythonRef::kSteal);
  BA_PRECONDITION(register_call.Call(args).exists());
}

void Python::PushObjCall(ObjID obj_id) {
  g_game->PushCall([obj_id] {
    ScopedSetContext cp(g_game->GetUIContext());
    g_python->obj(obj_id).Call();
  });
}

void Python::PushObjCall(ObjID obj_id, const std::string& arg) {
  g_game->PushCall([this, obj_id, arg] {
    ScopedSetContext cp(g_game->GetUIContext());
    PythonRef args(Py_BuildValue("(s)", arg.c_str()),
                   ballistica::PythonRef::kSteal);
    obj(obj_id).Call(args);
  });
}

Python::~Python() { Reset(false); }

auto Python::GetResource(const char* key, const char* fallback_resource,
                         const char* fallback_value) -> std::string {
  assert(InGameThread());
  PythonRef results;
  BA_PRECONDITION(key != nullptr);
  const PythonRef& get_resource_call(obj(ObjID::kGetResourceCall));
  if (fallback_value != nullptr) {
    if (fallback_resource == nullptr) {
      BA_PRECONDITION(key != nullptr);
      PythonRef args(Py_BuildValue("(sOs)", key, Py_None, fallback_value),
                     PythonRef::kSteal);

      // Don't print errors.
      results = get_resource_call.Call(args, PythonRef(), false);
    } else {
      PythonRef args(
          Py_BuildValue("(sss)", key, fallback_resource, fallback_value),
          PythonRef::kSteal);

      // Don't print errors.
      results = get_resource_call.Call(args, PythonRef(), false);
    }
  } else if (fallback_resource != nullptr) {
    PythonRef args(Py_BuildValue("(ss)", key, fallback_resource),
                   PythonRef::kSteal);

    // Don't print errors
    results = get_resource_call.Call(args, PythonRef(), false);
  } else {
    PythonRef args(Py_BuildValue("(s)", key), PythonRef::kSteal);

    // Don't print errors.
    results = get_resource_call.Call(args, PythonRef(), false);
  }
  if (results.exists()) {
    try {
      return GetPyString(results.get());
    } catch (const std::exception&) {
      Log("GetResource failed for '" + std::string(key) + "'");

      // Hmm; I guess let's just return the key to help identify/fix the
      // issue?..
      return std::string("<res-err: ") + key + ">";
    }
  } else {
    Log("GetResource failed for '" + std::string(key) + "'");
  }

  // Hmm; I guess let's just return the key to help identify/fix the issue?..
  return std::string("<res-err: ") + key + ">";
}

auto Python::GetTranslation(const char* category, const char* s)
    -> std::string {
  assert(InGameThread());
  PythonRef results;
  PythonRef args(Py_BuildValue("(ss)", category, s), PythonRef::kSteal);
  // Don't print errors.
  results = obj(ObjID::kTranslateCall).Call(args, PythonRef(), false);
  if (results.exists()) {
    try {
      return GetPyString(results.get());
    } catch (const std::exception&) {
      Log("GetTranslation failed for '" + std::string(category) + "'");
      return "";
    }
  } else {
    Log("GetTranslation failed for category '" + std::string(category) + "'");
  }
  return "";
}

void Python::RunDeepLink(const std::string& url) {
  assert(InGameThread());
  if (objexists(ObjID::kDeepLinkCall)) {
    ScopedSetContext cp(g_game->GetUIContext());
    PythonRef args(Py_BuildValue("(s)", url.c_str()), PythonRef::kSteal);
    obj(ObjID::kDeepLinkCall).Call(args);
  } else {
    Log("Error on deep-link call");
  }
}

void Python::PlayMusic(const std::string& music_type, bool continuous) {
  assert(InGameThread());
  if (music_type.empty()) {
    PythonRef args(
        Py_BuildValue("(OO)", Py_None, continuous ? Py_True : Py_False),
        PythonRef::kSteal);
    obj(ObjID::kDoPlayMusicCall).Call(args);
  } else {
    PythonRef args(Py_BuildValue("(sO)", music_type.c_str(),
                                 continuous ? Py_True : Py_False),
                   PythonRef::kSteal);
    obj(ObjID::kDoPlayMusicCall).Call(args);
  }
}

void Python::ShowURL(const std::string& url) {
  if (objexists(ObjID::kShowURLWindowCall)) {
    ScopedSetContext cp(g_game->GetUIContext());
    PythonRef args(Py_BuildValue("(s)", url.c_str()), PythonRef::kSteal);
    obj(ObjID::kShowURLWindowCall).Call(args);
  } else {
    Log("Error: ShowURLWindowCall nonexistent.");
  }
}

auto Python::FilterChatMessage(std::string* message, int client_id) -> bool {
  assert(message);
  ScopedSetContext cp(g_game->GetUIContext());
  PythonRef args(Py_BuildValue("(si)", message->c_str(), client_id),
                 PythonRef::kSteal);
  PythonRef result = obj(ObjID::kFilterChatMessageCall).Call(args);

  // If something went wrong, just allow all messages through verbatim.
  if (!result.exists()) {
    return true;
  }

  // If they returned None, they want to ignore the message.
  if (result.get() == Py_None) {
    return false;
  }

  // Replace the message string with whatever they gave us.
  try {
    *message = Python::GetPyString(result.get());
  } catch (const std::exception& e) {
    Log("Error getting string from chat filter: " + std::string(e.what()));
  }
  return true;
}

void Python::HandleLocalChatMessage(const std::string& message) {
  ScopedSetContext cp(g_game->GetUIContext());
  PythonRef args(Py_BuildValue("(s)", message.c_str()), PythonRef::kSteal);
  obj(ObjID::kHandleLocalChatMessageCall).Call(args);
}

void Python::DispatchScoresToBeatResponse(
    bool success, const std::list<ScoreToBeat>& scores_to_beat,
    void* callback_in) {
  // callback_in was a newly allocated PythonContextCall.
  // This will make it ref-counted so it'll die when we're done with it
  auto callback(
      Object::MakeRefCounted(static_cast<PythonContextCall*>(callback_in)));

  // Empty type denotes error.
  if (!success) {
    PythonRef args(Py_BuildValue("(O)", Py_None), PythonRef::kSteal);
    callback->Run(args);
  } else {
    PyObject* py_list = PyList_New(0);
    for (const auto& i : scores_to_beat) {
      PyObject* val = Py_BuildValue("{sssssssd}", "player", i.player.c_str(),
                                    "type", i.type.c_str(), "value",
                                    i.value.c_str(), "time", i.time);
      PyList_Append(py_list, val);
      Py_DECREF(val);
    }
    PythonRef args(Py_BuildValue("(O)", py_list), PythonRef::kSteal);
    Py_DECREF(py_list);
    callback->Run(args);
  }
}

// Put together a node message with all args on the provided tuple (starting
// with arg_offset) returns false on failure, true on success.
void Python::DoBuildNodeMessage(PyObject* args, int arg_offset, Buffer<char>* b,
                                PyObject** user_message_obj) {
  Py_ssize_t tuple_size = PyTuple_GET_SIZE(args);
  if (tuple_size - arg_offset < 1) {
    throw Exception("Got message of size zero.", PyExcType::kValue);
  }
  std::string type;
  PyObject* obj;

  // Pull first arg.
  obj = PyTuple_GET_ITEM(args, arg_offset);
  BA_PRECONDITION(obj);
  if (!PyUnicode_Check(obj)) {
    // If first arg is not a string, its an actual message itself.
    (*user_message_obj) = obj;
    return;
  } else {
    (*user_message_obj) = nullptr;
  }
  type = Python::GetPyString(obj);
  NodeMessageType ac = Scene::GetNodeMessageType(type);
  const char* format = Scene::GetNodeMessageFormat(ac);
  assert(format);
  const char* f = format;

  // Allow space for 1 type byte (fixme - may need more than 1).
  size_t full_size = 1;
  for (Py_ssize_t i = arg_offset + 1; i < tuple_size; i++) {
    // Make sure our format string ends the same time as our arg count.
    if (*f == 0) {
      throw Exception(
          "Wrong number of arguments on node message '" + type + "'.",
          PyExcType::kValue);
    }
    obj = PyTuple_GET_ITEM(args, i);
    BA_PRECONDITION(obj);
    switch (*f) {
      case 'I':

        // 4 byte int
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 4;
        break;
      case 'i':

        // 2 byte int.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 2;
        break;
      case 'c':  // NOLINT(bugprone-branch-clone)

        // 1 byte int.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 1;
        break;
      case 'b':

        // bool (currently 1 byte int).
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected an int for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 1;
        break;
      case 'F':

        // 32 bit float.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected a float for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 4;
        break;
      case 'f':

        // 16 bit float.
        if (!PyNumber_Check(obj)) {
          throw Exception("Expected a float for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += 2;
        break;
      case 's':
        if (!PyUnicode_Check(obj)) {
          throw Exception("Expected a string for node message arg "
                              + std::to_string(i - (arg_offset + 1)) + ".",
                          PyExcType::kType);
        }
        full_size += strlen(PyUnicode_AsUTF8(obj)) + 1;
        break;
      default:
        throw Exception("Invalid argument type: " + std::to_string(*f) + ".",
                        PyExcType::kValue);
        break;
    }
    f++;
  }

  // Make sure our format string ends the same time as our arg count.
  if (*f != 0) {
    throw Exception("Wrong number of arguments on node message '" + type + "'.",
                    PyExcType::kValue);
  }
  (*b).Resize(full_size);
  char* ptr = (*b).data();
  *ptr = static_cast<char>(ac);
  ptr++;
  f = format;
  for (Py_ssize_t i = arg_offset + 1; i < tuple_size; i++) {
    obj = PyTuple_GET_ITEM(args, i);
    BA_PRECONDITION(obj);
    switch (*f) {
      case 'I':
        Utils::EmbedInt32NBO(
            &ptr, static_cast_check_fit<int32_t>(Python::GetPyInt64(obj)));
        break;
      case 'i':
        Utils::EmbedInt16NBO(
            &ptr, static_cast_check_fit<int16_t>(Python::GetPyInt64(obj)));
        break;
      case 'c':  // NOLINT(bugprone-branch-clone)
        Utils::EmbedInt8(
            &ptr, static_cast_check_fit<int8_t>(Python::GetPyInt64(obj)));
        break;
      case 'b':
        Utils::EmbedInt8(
            &ptr, static_cast_check_fit<int8_t>(Python::GetPyInt64(obj)));
        break;
      case 'F':
        Utils::EmbedFloat32(&ptr, Python::GetPyFloat(obj));
        break;
      case 'f':
        Utils::EmbedFloat16NBO(&ptr, Python::GetPyFloat(obj));
        break;
      case 's':
        Utils::EmbedString(&ptr, PyUnicode_AsUTF8(obj));
        break;
      default:
        throw Exception(PyExcType::kValue);
        break;
    }
    f++;
  }
}

auto Python::GetPythonFileLocation(bool pretty) -> std::string {
  PyFrameObject* f = PyEval_GetFrame();
  if (f) {
    const char* path;
    if (f->f_code && f->f_code->co_filename) {
      assert(PyUnicode_Check(f->f_code->co_filename));
      path = PyUnicode_AsUTF8(f->f_code->co_filename);
      if (pretty) {
        if (path[0] == '<') {
          // Filter stuff like <string:
          // /Users/ericf/Documents/ballistica/src/bsGame.cpp line 724>:1
          return "<internal>";
        } else {
          // Advance past any '/' and '\'s
          while (true) {
            const char* s = strchr(path, '/');
            if (s) {
              path = s + 1;
            } else {
              const char* s2 = strchr(path, '\\');
              if (s2) {
                path = s2 + 1;
              } else {
                break;
              }
            }
          }
        }
      }
    } else {
      path = "<filename_unavailable>";
    }
    std::string name =
        std::string(path) + ":" + std::to_string(PyFrame_GetLineNumber(f));
    return name;
  }
  return "<unknown>";
}

void Python::SetNodeAttr(Node* node, const char* attr_name,
                         PyObject* value_obj) {
  assert(node);
  GameStream* out_stream = node->scene()->GetGameStream();
  NodeAttribute attr = node->GetAttribute(attr_name);
  switch (attr.type()) {
    case NodeAttributeType::kFloat: {
      float val = Python::GetPyFloat(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kInt: {
      int64_t val = Python::GetPyInt64(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kBool: {
      bool val = Python::GetPyBool(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kFloatArray: {
      std::vector<float> vals = Python::GetPyFloats(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kIntArray: {
      std::vector<int64_t> vals = Python::GetPyInts64(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kString: {
      std::string val = Python::GetPyString(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kNode: {
      // Allow dead-refs or None.
      Node* val = Python::GetPyNode(value_obj, true, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kNodeArray: {
      std::vector<Node*> vals = Python::GetPyNodes(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kPlayer: {
      // Allow dead-refs and None.
      Player* val = Python::GetPyPlayer(value_obj, true, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kMaterialArray: {
      std::vector<Material*> vals = Python::GetPyMaterials(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kTexture: {
      // Don't allow dead-refs, do allow None.
      Texture* val = Python::GetPyTexture(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kTextureArray: {
      std::vector<Texture*> vals = Python::GetPyTextures(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kSound: {
      // Don't allow dead-refs, do allow None.
      Sound* val = Python::GetPySound(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kSoundArray: {
      std::vector<Sound*> vals = Python::GetPySounds(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kModel: {
      // Don't allow dead-refs, do allow None.
      Model* val = Python::GetPyModel(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kModelArray: {
      std::vector<Model*> vals = Python::GetPyModels(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    case NodeAttributeType::kCollideModel: {
      // Don't allow dead-refs, do allow None.
      CollideModel* val = Python::GetPyCollideModel(value_obj, false, true);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, val);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(val);
      break;
    }
    case NodeAttributeType::kCollideModelArray: {
      std::vector<CollideModel*> vals = Python::GetPyCollideModels(value_obj);
      if (out_stream) {
        out_stream->SetNodeAttr(attr, vals);
      }

      // If something was driving this attr, disconnect it.
      attr.DisconnectIncoming();
      attr.Set(vals);
      break;
    }
    default:
      throw Exception("FIXME: unhandled attr type in SetNodeAttr: '"
                      + attr.GetTypeName() + "'.");
  }
}

static auto CompareAttrIndices(
    const std::pair<NodeAttributeUnbound*, PyObject*>& first,
    const std::pair<NodeAttributeUnbound*, PyObject*>& second) -> bool {
  return (first.first->index() < second.first->index());
}

auto Python::DoNewNode(PyObject* args, PyObject* keywds) -> Node* {
  PyObject* delegate_obj = Py_None;
  PyObject* owner_obj = Py_None;
  PyObject* name_obj = Py_None;
  static const char* kwlist[] = {"type", "owner",    "attrs",
                                 "name", "delegate", nullptr};
  char* type;
  PyObject* dict = nullptr;
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|OOOO", const_cast<char**>(kwlist), &type, &owner_obj,
          &dict, &name_obj, &delegate_obj)) {
    return nullptr;
  }

  std::string name;
  if (name_obj != Py_None) {
    name = GetPyString(name_obj);
  } else {
    // By default do something like 'text@foo.py:20'.
    name = std::string(type) + "@" + GetPythonFileLocation();
  }

  Scene* scene = Context::current().GetMutableScene();
  if (!scene) {
    throw Exception("Can't create nodes in this context.", PyExcType::kContext);
  }

  Node* node = scene->NewNode(type, name, delegate_obj);

  // Handle attr values fed in.
  if (dict) {
    if (!PyDict_Check(dict)) {
      throw Exception("Expected dict for arg 2.", PyExcType::kType);
    }
    NodeType* t = node->type();
    PyObject* key{};
    PyObject* value{};
    Py_ssize_t pos{};

    // We want to set initial attrs in order based on their attr indices.
    std::list<std::pair<NodeAttributeUnbound*, PyObject*> > attr_vals;

    // Grab all initial attr/values and add them to a list.
    while (PyDict_Next(dict, &pos, &key, &value)) {
      if (!PyUnicode_Check(key)) {
        throw Exception("Expected string key in attr dict.", PyExcType::kType);
      }
      try {
        attr_vals.emplace_back(
            t->GetAttribute(std::string(PyUnicode_AsUTF8(key))), value);
      } catch (const std::exception&) {
        Log("ERROR: Attr not found on initial attr set: '"
            + std::string(PyUnicode_AsUTF8(key)) + "' on " + type + " node '"
            + name + "'");
      }
    }

    // Run the sets in the order of attr indices.
    attr_vals.sort(CompareAttrIndices);
    for (auto&& i : attr_vals) {
      try {
        SetNodeAttr(node, i.first->name().c_str(), i.second);
      } catch (const std::exception& e) {
        Log("ERROR: exception in initial attr set for attr '" + i.first->name()
            + "' on " + type + " node '" + name + "':" + e.what());
      }
    }
  }

  // If an owner was provided, set it up.
  if (owner_obj != Py_None) {
    // If its a node, set up a dependency at the scene level
    // (then we just have to delete the owner node and the scene does the
    // rest).
    if (PythonClassNode::Check(owner_obj)) {
      Node* owner_node = GetPyNode(owner_obj, true);
      if (owner_node == nullptr) {
        Log("ERROR: empty node-ref passed for 'owner'; pass None if you want "
            "no owner.");
      } else if (owner_node->scene() != node->scene()) {
        Log("ERROR: owner node is from a different scene; ignoring.");
      } else {
        owner_node->AddDependentNode(node);
      }
    } else {
      throw Exception(
          "Invalid node owner: " + Python::ObjToString(owner_obj) + ".",
          PyExcType::kType);
    }
  }

  // Lastly, call this node's OnCreate method for any final setup it may want to
  // do.
  try {
    // Tell clients to do the same.
    if (GameStream* output_stream = scene->GetGameStream()) {
      output_stream->NodeOnCreate(node);
    }
    node->OnCreate();
  } catch (const std::exception& e) {
    Log("ERROR: exception in OnCreate() for node "
        + ballistica::ObjToString(node) + "':" + e.what());
  }

  return node;
}

// Return the node attr as a PyObject, or nullptr if the node doesn't have that
// attr.
auto Python::GetNodeAttr(Node* node, const char* attr_name) -> PyObject* {
  assert(node);
  NodeAttribute attr = node->GetAttribute(attr_name);
  switch (attr.type()) {
    case NodeAttributeType::kFloat:
      return PyFloat_FromDouble(attr.GetAsFloat());
      break;
    case NodeAttributeType::kInt:
      return PyLong_FromLong(
          static_cast_check_fit<long>(attr.GetAsInt()));  // NOLINT
      break;
    case NodeAttributeType::kBool:
      if (attr.GetAsBool()) {
        Py_RETURN_TRUE;
      } else {
        Py_RETURN_FALSE;
      }
      break;
    case NodeAttributeType::kString: {
      if (g_buildconfig.debug_build()) {
        std::string s = attr.GetAsString();
        assert(Utils::IsValidUTF8(s));
        return PyUnicode_FromString(s.c_str());
      } else {
        return PyUnicode_FromString(attr.GetAsString().c_str());
      }
      break;
    }
    case NodeAttributeType::kNode: {
      // Return a new py ref to this node or create a new empty ref.
      Node* n = attr.GetAsNode();
      return n ? n->NewPyRef() : PythonClassNode::Create(nullptr);
      break;
    }
    case NodeAttributeType::kPlayer: {
      // Player attrs deal with custom user ba.Player classes;
      // not our internal SessionPlayer class.
      Player* p = attr.GetAsPlayer();
      if (p == nullptr) {
        Py_RETURN_NONE;
      }
      PyObject* gameplayer = p->GetPyActivityPlayer();
      Py_INCREF(gameplayer);
      return gameplayer;
      // return p ? p->NewPyRef() : PythonClassSessionPlayer::Create(nullptr);
      break;
    }
    case NodeAttributeType::kFloatArray: {
      std::vector<float> vals = attr.GetAsFloats();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        PyTuple_SET_ITEM(vals_obj, i, PyFloat_FromDouble(vals[i]));
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kIntArray: {
      std::vector<int64_t> vals = attr.GetAsInts();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        PyTuple_SET_ITEM(vals_obj, i,
                         PyLong_FromLong(static_cast_check_fit<long>(  // NOLINT
                             vals[i])));
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kNodeArray: {
      std::vector<Node*> vals = attr.GetAsNodes();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Node* n = vals[i];
        PyTuple_SET_ITEM(vals_obj, i,
                         n ? n->NewPyRef() : PythonClassNode::Create(nullptr));
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kTexture: {
      Texture* t = attr.GetAsTexture();
      if (!t) {
        Py_RETURN_NONE;
      }
      return t->NewPyRef();
      break;
    }
    case NodeAttributeType::kSound: {
      Sound* s = attr.GetAsSound();
      if (!s) {
        Py_RETURN_NONE;
      }
      return s->NewPyRef();
      break;
    }
    case NodeAttributeType::kModel: {
      Model* m = attr.GetAsModel();
      if (!m) {
        Py_RETURN_NONE;
      }
      return m->NewPyRef();
      break;
    }
    case NodeAttributeType::kCollideModel: {
      CollideModel* c = attr.GetAsCollideModel();
      if (!c) {
        Py_RETURN_NONE;
      }
      return c->NewPyRef();
      break;
    }
    case NodeAttributeType::kMaterialArray: {
      std::vector<Material*> vals = attr.GetAsMaterials();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Material* m = vals[i];

        // Array attrs should never return nullptr materials.
        assert(m);
        PyTuple_SET_ITEM(vals_obj, i, m->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kTextureArray: {
      std::vector<Texture*> vals = attr.GetAsTextures();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Texture* t = vals[i];

        // Array attrs should never return nullptr textures.
        assert(t);
        PyTuple_SET_ITEM(vals_obj, i, t->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kSoundArray: {
      std::vector<Sound*> vals = attr.GetAsSounds();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Sound* s = vals[i];

        // Array attrs should never return nullptr sounds.
        assert(s);
        PyTuple_SET_ITEM(vals_obj, i, s->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kModelArray: {
      std::vector<Model*> vals = attr.GetAsModels();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        Model* m = vals[i];

        // Array attrs should never return nullptr models.
        assert(m);
        PyTuple_SET_ITEM(vals_obj, i, m->NewPyRef());
      }
      return vals_obj;
      break;
    }
    case NodeAttributeType::kCollideModelArray: {
      std::vector<CollideModel*> vals = attr.GetAsCollideModels();
      Py_ssize_t size = vals.size();
      PyObject* vals_obj = PyTuple_New(size);
      BA_PRECONDITION(vals_obj);
      for (Py_ssize_t i = 0; i < size; i++) {
        CollideModel* c = vals[i];

        // Array attrs should never return nullptr collide-models.
        assert(c);
        PyTuple_SET_ITEM(vals_obj, i, c->NewPyRef());
      }
      return vals_obj;
      break;
    }

    default:
      throw Exception("FIXME: unhandled attr type in GetNodeAttr: '"
                      + attr.GetTypeName() + "'.");
  }
  return nullptr;
}

void Python::IssueCallInGameThreadWarning(PyObject* call_obj) {
  Log("WARNING: ba.pushcall() called from the game thread with "
      "from_other_thread set to true (call "
      + ObjToString(call_obj) + " at " + GetPythonFileLocation()
      + "). That arg should only be used from other threads.");
}

void Python::LaunchStringEdit(TextWidget* w) {
  assert(InGameThread());
  BA_PRECONDITION(w);

  ScopedSetContext cp(g_game->GetUIContext());
  g_audio->PlaySound(g_media->GetSound(SystemSoundID::kSwish));

  // Gotta run this in the next cycle.
  PythonRef args(Py_BuildValue("(Osi)", w->BorrowPyRef(),
                               w->description().c_str(), w->max_chars()),
                 PythonRef::kSteal);
  g_game->PushPythonCallArgs(
      Object::New<PythonContextCall>(obj(ObjID::kOnScreenKeyboardClass).get()),
      args);
}

void Python::CaptureGamePadInput(PyObject* obj) {
  assert(InGameThread());
  ReleaseGamePadInput();
  if (PyCallable_Check(obj)) {
    game_pad_call_.Acquire(obj);
  } else {
    throw Exception("Object is not callable.", PyExcType::kType);
  }
}

void Python::ReleaseGamePadInput() { game_pad_call_.Release(); }

void Python::CaptureKeyboardInput(PyObject* obj) {
  assert(InGameThread());
  ReleaseKeyboardInput();
  if (PyCallable_Check(obj)) {
    keyboard_call_.Acquire(obj);
  } else {
    throw Exception("Object is not callable.", PyExcType::kType);
  }
}
void Python::ReleaseKeyboardInput() { keyboard_call_.Release(); }

void Python::HandleFriendScoresCB(const FriendScoreSet& score_set) {
  // This is the initial strong-ref to this pointer
  // so it will be cleaned up properly.
  Object::Ref<PythonContextCall> cb(
      static_cast<PythonContextCall*>(score_set.user_data));

  // We pass None on error.
  if (!score_set.success) {
    PythonRef args(Py_BuildValue("(O)", Py_None), PythonRef::kSteal);
    cb->Run(args);
  } else {
    // Otherwise convert it to a python list and pass that.
    PyObject* py_list = PyList_New(0);
    std::string icon_str;
#if BA_USE_GOOGLE_PLAY_GAME_SERVICES
    icon_str = g_game->CharStr(SpecialChar::kGooglePlayGamesLogo);
#elif BA_USE_GAME_CIRCLE
    icon_str = g_game->CharStr(SpecialChar::kGameCircleLogo);
#elif BA_USE_GAME_CENTER
    icon_str = g_game->CharStr(SpecialChar::kGameCenterLogo);
#endif
    for (auto&& i : score_set.entries) {
      PyObject* obj =
          Py_BuildValue("[isi]", i.score, (icon_str + i.name).c_str(),
                        static_cast<int>(i.is_me));
      PyList_Append(py_list, obj);
      Py_DECREF(obj);
    }
    PythonRef args(Py_BuildValue("(O)", py_list), PythonRef::kSteal);
    Py_DECREF(py_list);
    cb->Run(args);
  }
}

auto Python::HandleKeyPressEvent(const SDL_Keysym& keysym) -> bool {
  assert(InGameThread());
  if (!keyboard_call_.exists()) {
    return false;
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());
  InputDevice* keyboard = g_input->keyboard_input();
  PythonRef args(
      Py_BuildValue("({s:s,s:i,s:O})", "type", "BUTTONDOWN", "button",
                    static_cast<int>(keysym.sym), "input_device",
                    keyboard ? keyboard->BorrowPyRef() : Py_None),
      PythonRef::kSteal);
  keyboard_call_.Call(args);
  return true;
}
auto Python::HandleKeyReleaseEvent(const SDL_Keysym& keysym) -> bool {
  assert(InGameThread());
  if (!keyboard_call_.exists()) {
    return false;
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());
  InputDevice* keyboard = g_input->keyboard_input();
  PythonRef args(Py_BuildValue("({s:s,s:i,s:O})", "type", "BUTTONUP", "button",
                               static_cast<int>(keysym.sym), "input_device",
                               keyboard ? keyboard->BorrowPyRef() : Py_None),
                 PythonRef::kSteal);
  keyboard_call_.Call(args);
  return true;
}

auto Python::HandleJoystickEvent(const SDL_Event& event,
                                 InputDevice* input_device) -> bool {
  assert(InGameThread());
  assert(input_device != nullptr);
  if (!game_pad_call_.exists()) {
    return false;
  }
  ScopedSetContext cp(g_game->GetUIContextTarget());
  InputDevice* device{};

  device = input_device;

  // If we got a device we can pass events.
  if (device) {
    switch (event.type) {
      case SDL_JOYBUTTONDOWN: {
        PythonRef args(
            Py_BuildValue(
                "({s:s,s:i,s:O})", "type", "BUTTONDOWN", "button",
                static_cast<int>(event.jbutton.button) + 1,  // give them base-1
                "input_device", device->BorrowPyRef()),
            PythonRef::kSteal);
        game_pad_call_.Call(args);
        break;
      }
      case SDL_JOYBUTTONUP: {
        PythonRef args(
            Py_BuildValue(
                "({s:s,s:i,s:O})", "type", "BUTTONUP", "button",
                static_cast<int>(event.jbutton.button) + 1,  // give them base-1
                "input_device", device->BorrowPyRef()),
            PythonRef::kSteal);
        game_pad_call_.Call(args);
        break;
      }
      case SDL_JOYHATMOTION: {
        PythonRef args(
            Py_BuildValue(
                "({s:s,s:i,s:i,s:O})", "type", "HATMOTION", "hat",
                static_cast<int>(event.jhat.hat) + 1,  // give them base-1
                "value", event.jhat.value, "input_device",
                device->BorrowPyRef()),
            PythonRef::kSteal);
        game_pad_call_.Call(args);
        break;
      }
      case SDL_JOYAXISMOTION: {
        PythonRef args(
            Py_BuildValue(
                "({s:s,s:i,s:f,s:O})", "type", "AXISMOTION", "axis",
                static_cast<int>(event.jaxis.axis) + 1,  // give them base-1
                "value",
                std::min(1.0f,
                         std::max(-1.0f, static_cast<float>(event.jaxis.value)
                                             / 32767.0f)),
                "input_device", device->BorrowPyRef()),
            PythonRef::kSteal);
        game_pad_call_.Call(args);
        break;
      }
      default:
        break;
    }
  }
  return true;
}

auto Python::GetContextBaseString() -> std::string {
  std::string context_str;
  std::string sim_time_string;
  std::string base_time_string;
  try {
    sim_time_string =
        std::to_string(Context::current().target->GetTime(TimeType::kSim));
  } catch (const std::exception&) {
    sim_time_string = "<unavailable>";
  }
  try {
    base_time_string =
        std::to_string(Context::current().target->GetTime(TimeType::kBase));
  } catch (const std::exception&) {
    base_time_string = "<unavailable>";
  }

  if (Context::current().GetUIContext()) {
    context_str = "<UI Context>";
  } else if (HostActivity* ha = Context::current().GetHostActivity()) {
    // If its a HostActivity, print the Python obj.
    PythonRef ha_obj(ha->GetPyActivity(), PythonRef::kAcquire);
    if (ha_obj.get() != Py_None) {
      context_str = ha_obj.Str();
    } else {
      context_str = ha->GetObjectDescription();
    }
  } else if (Context::current().target.exists()) {
    context_str = Context::current().target->GetObjectDescription();
  } else {
    context_str = "<empty context>";
  }
  std::string s = "\n  context: " + context_str + "\n  real-time: "
                  + std::to_string(GetRealTime()) + "\n  sim-time: "
                  + sim_time_string + "\n  base-time: " + base_time_string;
  return s;
}

void Python::LogContextForCallableLabel(const char* label) {
  assert(InGameThread());
  assert(label);
  std::string s = std::string("  root call: ") + label;
  s += g_python->GetContextBaseString();
  Log(s);
}

void Python::LogContextNonGameThread() {
  std::string s =
      std::string("  root call: <not in game thread; context unavailable>");
  Log(s);
}

void Python::LogContextEmpty() {
  assert(InGameThread());
  std::string s = std::string("  root call: <unavailable>");
  s += g_python->GetContextBaseString();
  Log(s);
}

void Python::LogContextAuto() {
  // Lets print whatever context info is available.
  // FIXME: If we have recursive calls this may not print
  // the context we'd expect; we'd need a unified stack.
  if (!InGameThread()) {
    LogContextNonGameThread();
  } else if (const char* label = ScopedCallLabel::current_label()) {
    LogContextForCallableLabel(label);
  } else if (PythonCommand* cmd = PythonCommand::current_command()) {
    cmd->LogContext();
  } else if (PythonContextCall* call = PythonContextCall::current_call()) {
    call->LogContext();
  } else {
    LogContextEmpty();
  }
}

void Python::AcquireGIL() {
  if (thread_state_) {
    PyEval_RestoreThread(thread_state_);
    thread_state_ = nullptr;
  }
}
void Python::ReleaseGIL() {
  assert(thread_state_ == nullptr);
  thread_state_ = PyEval_SaveThread();
}

void Python::AddCleanFrameCommand(const Object::Ref<PythonContextCall>& c) {
  clean_frame_commands_.push_back(c);
}

void Python::RunCleanFrameCommands() {
  for (auto&& i : clean_frame_commands_) {
    i->Run();
  }
  clean_frame_commands_.clear();
}

auto Python::GetControllerValue(InputDevice* input_device,
                                const std::string& value_name) -> int {
  assert(objexists(ObjID::kGetDeviceValueCall));
  PythonRef args(
      Py_BuildValue("(Os)", input_device->BorrowPyRef(), value_name.c_str()),
      PythonRef::kSteal);
  PythonRef ret_val;
  {
    Python::ScopedCallLabel label("get_device_value");
    ret_val = obj(ObjID::kGetDeviceValueCall).Call(args);
  }
  if (!PyLong_Check(ret_val.get())) {
    throw Exception("Non-int returned from get_device_value call.",
                    PyExcType::kType);
  }
  return static_cast<int>(PyLong_AsLong(ret_val.get()));
}

auto Python::GetControllerFloatValue(InputDevice* input_device,
                                     const std::string& value_name) -> float {
  assert(objexists(ObjID::kGetDeviceValueCall));
  PythonRef args(
      Py_BuildValue("(Os)", input_device->BorrowPyRef(), value_name.c_str()),
      PythonRef::kSteal);
  PythonRef ret_val = obj(ObjID::kGetDeviceValueCall).Call(args);
  if (!PyFloat_Check(ret_val.get())) {
    if (PyLong_Check(ret_val.get())) {
      return static_cast<float>(PyLong_AsLong(ret_val.get()));
    } else {
      throw Exception(
          "Non float/int returned from GetControllerFloatValue call.",
          PyExcType::kType);
    }
  }
  return static_cast<float>(PyFloat_AsDouble(ret_val.get()));
}

void Python::HandleDeviceMenuPress(InputDevice* input_device) {
  assert(objexists(ObjID::kDeviceMenuPressCall));

  // Ignore if input is locked...
  if (g_input->IsInputLocked()) {
    return;
  }
  ScopedSetContext cp(g_game->GetUIContext());
  PythonRef args(Py_BuildValue("(O)", input_device ? input_device->BorrowPyRef()
                                                   : Py_None),
                 PythonRef::kSteal);
  {
    Python::ScopedCallLabel label("handleDeviceMenuPress");
    obj(ObjID::kDeviceMenuPressCall).Call(args);
  }
}

auto Python::GetLastPlayerNameFromInputDevice(InputDevice* device)
    -> std::string {
  assert(objexists(ObjID::kGetLastPlayerNameFromInputDeviceCall));
  PythonRef args(Py_BuildValue("(O)", device ? device->BorrowPyRef() : Py_None),
                 PythonRef::kSteal);
  try {
    return Python::GetPyString(
        obj(ObjID::kGetLastPlayerNameFromInputDeviceCall).Call(args).get());
  } catch (const std::exception&) {
    return "<invalid>";
  }
}

auto Python::ObjToString(PyObject* obj) -> std::string {
  if (obj) {
    return PythonRef(obj, PythonRef::kAcquire).Str();
  } else {
    return "<nullptr PyObject*>";
  }
}

void Python::PartyInvite(const std::string& player,
                         const std::string& invite_id) {
  ScopedSetContext cp(g_game->GetUIContext());
  PythonRef args(
      Py_BuildValue(
          "(OO)",
          PythonRef(PyUnicode_FromString(player.c_str()), PythonRef::kSteal)
              .get(),
          PythonRef(PyUnicode_FromString(invite_id.c_str()), PythonRef::kSteal)
              .get()),
      PythonRef::kSteal);
  obj(ObjID::kHandlePartyInviteCall).Call(args);
}

void Python::PartyInviteRevoke(const std::string& invite_id) {
  ScopedSetContext cp(g_game->GetUIContext());
  PythonRef args(
      Py_BuildValue("(O)", PythonRef(PyUnicode_FromString(invite_id.c_str()),
                                     PythonRef::kSteal)
                               .get()),
      PythonRef::kSteal);
  obj(ObjID::kHandlePartyInviteRevokeCall).Call(args);
}

void Python::StoreObj(ObjID id, PyObject* pyobj, bool incref) {
  assert(id < ObjID::kLast);
  assert(pyobj);
  if (g_buildconfig.debug_build()) {
    // Assuming we're setting everything once
    // (make sure we don't accidentally overwrite things we don't intend to).
    if (objs_[static_cast<int>(id)].exists()) {
      throw Exception("Python::StoreObj() called twice for val '"
                      + std::to_string(static_cast<int>(id)) + "'.");
    }

    // Also make sure we're not storing an object that's already been stored.
    for (auto&& i : objs_) {
      if (i.get() != nullptr && i.get() == pyobj) {
        throw Exception("Python::StoreObj() called twice for same ptr; id="
                        + std::to_string(static_cast<int>(id)) + ".");
      }
    }
  }
  if (incref) {
    Py_INCREF(pyobj);
  }
  objs_[static_cast<int>(id)].Steal(pyobj);
}

void Python::StoreObjCallable(ObjID id, PyObject* pyobj, bool incref) {
  StoreObj(id, pyobj, incref);
  BA_PRECONDITION(obj(id).CallableCheck());
}

void Python::StoreObj(ObjID id, const char* expr, PyObject* context) {
  PyObject* obj =
      PythonCommand(expr, "<PyObj Set>").RunReturnObj(false, context);
  if (obj == nullptr) {
    throw Exception("Unable to get value: '" + std::string(expr) + "'.");
  }
  StoreObj(id, obj);
}

void Python::StoreObjCallable(ObjID id, const char* expr, PyObject* context) {
  PyObject* obj =
      PythonCommand(expr, "<PyObj Set>").RunReturnObj(false, context);
  if (obj == nullptr) {
    throw Exception("Unable to get value: '" + std::string(expr) + "'.");
  }
  StoreObjCallable(id, obj);
}

void Python::SetRawConfigValue(const char* name, float value) {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  PythonRef value_obj(PyFloat_FromDouble(value), PythonRef::kSteal);
  int result =
      PyDict_SetItemString(obj(ObjID::kConfig).get(), name, value_obj.get());
  if (result == -1) {
    // Failed, we have.
    // Clear any Python error that got us here; we're in C++ Exception land now.
    PyErr_Clear();
    throw Exception("Error setting config dict value.");
  }
}

auto Python::GetRawConfigValue(const char* name) -> PyObject* {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  return PyDict_GetItemString(obj(ObjID::kConfig).get(), name);
}

auto Python::GetRawConfigValue(const char* name, const char* default_value)
    -> std::string {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  PyObject* value = PyDict_GetItemString(obj(ObjID::kConfig).get(), name);
  if (value == nullptr || !PyUnicode_Check(value)) {
    return default_value;
  }
  return PyUnicode_AsUTF8(value);
}

auto Python::GetRawConfigValue(const char* name, float default_value) -> float {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  PyObject* value = PyDict_GetItemString(obj(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    return GetPyFloat(value);
  } catch (const std::exception&) {
    Log("expected a float for config value '" + std::string(name) + "'");
    return default_value;
  }
}

auto Python::GetRawConfigValue(const char* name,
                               std::optional<float> default_value)
    -> std::optional<float> {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  PyObject* value = PyDict_GetItemString(obj(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    if (value == Py_None) {
      return std::optional<float>();
    }
    return GetPyFloat(value);
  } catch (const std::exception&) {
    Log("expected a float for config value '" + std::string(name) + "'");
    return default_value;
  }
}

auto Python::GetRawConfigValue(const char* name, int default_value) -> int {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  PyObject* value = PyDict_GetItemString(obj(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    return static_cast_check_fit<int>(GetPyInt64(value));
  } catch (const std::exception&) {
    Log("Expected an int value for config value '" + std::string(name) + "'.");
    return default_value;
  }
}

auto Python::GetRawConfigValue(const char* name, bool default_value) -> bool {
  assert(InGameThread());
  assert(objexists(ObjID::kConfig));
  PyObject* value = PyDict_GetItemString(obj(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    return GetPyBool(value);
  } catch (const std::exception&) {
    Log("Expected a bool value for config value '" + std::string(name) + "'.");
    return default_value;
  }
}

auto Python::DoOnce() -> bool {
  std::string location = GetPythonFileLocation(false);
  if (do_once_locations_.find(location) != do_once_locations_.end()) {
    return false;
  }
  do_once_locations_.insert(location);
  return true;
}

void Python::TimeFormatCheck(TimeFormat time_format, PyObject* length_obj) {
  std::string warn_msg;
  double length = Python::GetPyDouble(length_obj);
  if (time_format == TimeFormat::kSeconds) {
    // If we get a value more than a few hundred seconds, they might
    // have meant milliseconds.
    if (length >= 200.0) {
      static bool warned = false;
      if (!warned) {
        Log("Warning: time value "
            +std::to_string(length)+" passed as seconds;"
            " did you mean milliseconds?"
            " (if so, pass suppress_format_warning=True to stop this warning)");
        PrintStackTrace();
        warned = true;
      }
    }
  } else if (time_format == TimeFormat::kMilliseconds) {
    // If we get a value less than 1 millisecond, they might have meant
    // seconds. (also ignore 0 which could be valid)
    if (length < 1.0 && length > 0.0000001) {
      static bool warned = false;
      if (!warned) {
        Log("Warning: time value "
            + std::to_string(length) + " passed as milliseconds;"
            " did you mean seconds?"
            " (if so, pass suppress_format_warning=True to stop this warning)");
        PrintStackTrace();
        warned = true;
      }
    }
  } else {
    static bool warned = false;
    if (!warned) {
      BA_LOG_ONCE("TimeFormatCheck got timeformat value: '"
                  + std::to_string(static_cast<int>(time_format)) + "'");
      warned = true;
    }
  }
}

auto Python::ValidatedPackageAssetName(PyObject* package, const char* name)
    -> std::string {
  assert(InGameThread());
  assert(objexists(ObjID::kAssetPackageClass));

  if (!PyObject_IsInstance(package, obj(ObjID::kAssetPackageClass).get())) {
    throw Exception("Object is not an AssetPackage.", PyExcType::kType);
  }

  // Ok; they've passed us an asset-package object.
  // Now validate that its context is current...
  PythonRef context_obj(PyObject_GetAttrString(package, "context"),
                        PythonRef::kSteal);
  if (!context_obj.exists()
      || !(PyObject_IsInstance(
          context_obj.get(),
          reinterpret_cast<PyObject*>(&PythonClassContext::type_obj)))) {
    throw Exception("Asset package context not found.", PyExcType::kNotFound);
  }
  auto* pycontext = reinterpret_cast<PythonClassContext*>(context_obj.get());
  Object::WeakRef<ContextTarget> ctargetref = pycontext->context().target;
  if (!ctargetref.exists()) {
    throw Exception("Asset package context does not exist.",
                    PyExcType::kNotFound);
  }
  Object::WeakRef<ContextTarget> ctargetref2 = Context::current().target;
  if (ctargetref.get() != ctargetref2.get()) {
    throw Exception("Asset package context is not current.");
  }

  // Hooray; the asset package's context exists and is current.
  // Ok; now pull the package id...
  PythonRef package_id(PyObject_GetAttrString(package, "package_id"),
                       PythonRef::kSteal);
  if (!PyUnicode_Check(package_id.get())) {
    throw Exception("Got non-string AssetPackage ID.", PyExcType::kType);
  }

  // TODO(ericf): make sure the package is valid for this context,
  // and return a fully qualified name with the package included.

  printf("would give %s:%s\n", PyUnicode_AsUTF8(package_id.get()), name);
  return name;
}

class Python::ScopedInterpreterLock::Impl {
 public:
  Impl() : need_lock_(true), gstate_(PyGILState_UNLOCKED) {
    if (need_lock_) {
      if (need_lock_) {
        // Grab the python GIL.
        gstate_ = PyGILState_Ensure();
      }
    }
  }
  ~Impl() {
    if (need_lock_) {
      // Release the python GIL.
      PyGILState_Release(gstate_);
    }
  }

 private:
  bool need_lock_ = false;
  PyGILState_STATE gstate_;
};

Python::ScopedInterpreterLock::ScopedInterpreterLock()
    : impl_{new Python::ScopedInterpreterLock::Impl()}
// impl_{std::make_unique<Python::ScopedInterpreterLock::Impl>()}
{}

Python::ScopedInterpreterLock::~ScopedInterpreterLock() { delete impl_; }

template <typename T>
auto IsPyEnum(Python::ObjID enum_class_id, PyObject* obj) -> bool {
  PyObject* enum_class_obj = g_python->obj(enum_class_id).get();
  assert(enum_class_obj != nullptr && enum_class_obj != Py_None);
  return static_cast<bool>(PyObject_IsInstance(obj, enum_class_obj));
}

template <typename T>
auto GetPyEnum(Python::ObjID enum_class_id, PyObject* obj) -> T {
  // First, make sure what they passed is an instance of the enum class
  // we want.
  PyObject* enum_class_obj = g_python->obj(enum_class_id).get();
  assert(enum_class_obj != nullptr && enum_class_obj != Py_None);
  if (!PyObject_IsInstance(obj, enum_class_obj)) {
    throw Exception(Python::ObjToString(obj) + " is not an instance of "
                        + Python::ObjToString(enum_class_obj) + ".",
                    PyExcType::kType);
  }

  // Now get its value as an int and make sure its in range
  // (based on its kLast member in C++ land).
  PythonRef value_obj(PyObject_GetAttrString(obj, "value"), PythonRef::kSteal);
  if (!value_obj.exists() || !PyLong_Check(value_obj.get())) {
    throw Exception(
        Python::ObjToString(obj) + " is not a valid int-valued enum.",
        PyExcType::kType);
  }
  auto value = PyLong_AS_LONG(value_obj.get());
  if (value < 0 || value >= static_cast<int>(T::kLast)) {
    throw Exception(
        Python::ObjToString(obj) + " is an invalid out-of-range enum value.",
        PyExcType::kValue);
  }
  return static_cast<T>(value);
}

// Explicitly instantiate the few variations we use.
// (so we can avoid putting the full function in the header)
// template TimeFormat Python::GetPyEnum(Python::ObjID enum_class, PyObject*
// obj); template TimeType Python::GetPyEnum(Python::ObjID enum_class, PyObject*
// obj); template SpecialChar Python::GetPyEnum(Python::ObjID enum_class,
// PyObject* obj); template Permission Python::GetPyEnum(Python::ObjID
// enum_class, PyObject* obj);

auto Python::GetPyEnum_Permission(PyObject* obj) -> Permission {
  return GetPyEnum<Permission>(Python::ObjID::kPermissionClass, obj);
}

auto Python::GetPyEnum_SpecialChar(PyObject* obj) -> SpecialChar {
  return GetPyEnum<SpecialChar>(Python::ObjID::kSpecialCharClass, obj);
}

auto Python::GetPyEnum_TimeType(PyObject* obj) -> TimeType {
  return GetPyEnum<TimeType>(Python::ObjID::kTimeTypeClass, obj);
}

auto Python::GetPyEnum_TimeFormat(PyObject* obj) -> TimeFormat {
  return GetPyEnum<TimeFormat>(Python::ObjID::kTimeFormatClass, obj);
}

auto Python::IsPyEnum_InputType(PyObject* obj) -> bool {
  return IsPyEnum<InputType>(Python::ObjID::kInputTypeClass, obj);
}

auto Python::GetPyEnum_InputType(PyObject* obj) -> InputType {
  return GetPyEnum<InputType>(Python::ObjID::kInputTypeClass, obj);
}

// (some stuff borrowed from python's source code - used in our overriding of
// objects' dir() results)

/* alphabetical order */
_Py_IDENTIFIER(__class__);
_Py_IDENTIFIER(__dict__);

/* ------------------------- PyObject_Dir() helpers ------------------------- */

/*
 Merge the __dict__ of aclass into dict, and recursively also all
 the __dict__s of aclass's base classes.  The order of merging isn't
 defined, as it's expected that only the final set of dict keys is
 interesting.
 Return 0 on success, -1 on error.
 */

static auto merge_class_dict(PyObject* dict, PyObject* aclass) -> int {
  PyObject* classdict;
  PyObject* bases;
  _Py_IDENTIFIER(__bases__);

  assert(PyDict_Check(dict));
  assert(aclass);

  /* Merge in the type's dict (if any). */
  classdict = _PyObject_GetAttrId(aclass, &PyId___dict__);
  if (classdict == nullptr) {
    PyErr_Clear();
  } else {
    int status = PyDict_Update(dict, classdict);
    Py_DECREF(classdict);
    if (status < 0) return -1;
  }

  /* Recursively merge in the base types' (if any) dicts. */
  bases = _PyObject_GetAttrId(aclass, &PyId___bases__);
  if (bases == nullptr) {
    PyErr_Clear();
  } else {
    /* We have no guarantee that bases is a real tuple */
    Py_ssize_t i;
    Py_ssize_t n;
    n = PySequence_Size(bases); /* This better be right */
    if (n < 0) {
      PyErr_Clear();
    } else {
      for (i = 0; i < n; i++) {
        int status;
        PyObject* base = PySequence_GetItem(bases, i);
        if (base == nullptr) {
          Py_DECREF(bases);
          return -1;
        }
        status = merge_class_dict(dict, base);
        Py_DECREF(base);
        if (status < 0) {
          Py_DECREF(bases);
          return -1;
        }
      }
    }
    Py_DECREF(bases);
  }
  return 0;
}

/* __dir__ for generic objects: returns __dict__, __class__,
 and recursively up the __class__.__bases__ chain.
 */
auto Python::generic_dir(PyObject* self) -> PyObject* {
  PyObject* result = nullptr;
  PyObject* dict = nullptr;
  PyObject* itsclass = nullptr;

  /* Get __dict__ (which may or may not be a real dict...) */
  dict = _PyObject_GetAttrId(self, &PyId___dict__);
  if (dict == nullptr) {
    PyErr_Clear();
    dict = PyDict_New();
  } else if (!PyDict_Check(dict)) {
    Py_DECREF(dict);
    dict = PyDict_New();
  } else {
    /* Copy __dict__ to avoid mutating it. */
    PyObject* temp = PyDict_Copy(dict);
    Py_DECREF(dict);
    dict = temp;
  }

  if (dict == nullptr) goto error;

  /* Merge in attrs reachable from its class. */
  itsclass = _PyObject_GetAttrId(self, &PyId___class__);
  if (itsclass == nullptr)
    /* XXX(tomer): Perhaps fall back to obj->ob_type if no
     __class__ exists? */
    PyErr_Clear();
  else if (merge_class_dict(dict, itsclass) != 0)
    goto error;

  result = PyDict_Keys(dict);
  /* fall through */
error:
  Py_XDECREF(itsclass);
  Py_XDECREF(dict);
  return result;
}
////////////////   end __dir__ helpers

#pragma clang diagnostic pop

}  // namespace ballistica
