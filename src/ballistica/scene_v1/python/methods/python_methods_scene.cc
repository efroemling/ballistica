// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/methods/python_methods_scene.h"

#include <cstdio>
#include <list>
#include <string>
#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_simple_sound.h"
#include "ballistica/base/python/support/python_context_call_runnable.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/scene_v1/connection/connection_to_client.h"
#include "ballistica/scene_v1/dynamics/collision.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/python/class/python_class_activity_data.h"
#include "ballistica/scene_v1/python/class/python_class_session_data.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/client_session_replay.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/json.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

// --------------------------------- time --------------------------------------

static auto PyTime(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }

  return PyFloat_FromDouble(
      0.001
      * static_cast<double>(SceneV1Context::Current().GetTime(TimeType::kSim)));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyTimeDef = {
    "time",                        // name
    (PyCFunction)PyTime,           // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "time() -> bascenev1.Time\n"
    "\n"
    "Return the current scene time in seconds.\n"
    "\n"
    "Scene time maps to local simulation time in bascenev1.Activity or\n"
    "bascenev1.Session Contexts. This means that it may progress slower\n"
    "in slow-motion play modes, stop when the game is paused, etc.\n"
    "\n"
    "Note that the value returned here is simply a float; it just has a\n"
    "unique type in the type-checker's eyes to help prevent it from being\n"
    "accidentally used with time functionality expecting other time types.",
};

// --------------------------------- timer -------------------------------------

static auto PyTimer(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());

  double length;
  int repeat = 0;
  PyObject* call_obj;
  static const char* kwlist[] = {"time", "call", "repeat", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "dO|p",
                                   const_cast<char**>(kwlist), &length,
                                   &call_obj, &repeat)) {
    return nullptr;
  }
  if (length < 0.0) {
    throw Exception("Timer length cannot be < 0.", PyExcType::kValue);
  }
  SceneV1Context::Current().NewTimer(
      TimeType::kSim, static_cast<millisecs_t>(length * 1000.0),
      static_cast<bool>(repeat),
      Object::New<Runnable, base::PythonContextCallRunnable>(call_obj).get());

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyTimerDef = {
    "timer",                       // name
    (PyCFunction)PyTimer,          // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "timer(time: float, call: Callable[[], Any], repeat: bool = False)\n"
    " -> None\n"
    "\n"
    "Schedule a call to run at a later point in time.\n"
    "\n"
    "This function adds a scene-time timer to the current\n"
    ":class:`bascenev1.ContextRef`. This timer cannot be canceled or modified\n"
    "once created. If you require the ability to do so, use the\n"
    ":class:`bascenev1.Timer` class instead.\n"
    "\n"
    "Scene time maps to local simulation time in :class:`bascenev1.Activity`\n"
    "or :class:`bascenev1.Session` Contexts. This means that it may progress\n"
    "slower in slow-motion play modes, stop when the game is paused, etc.\n"
    "\n"
    "Args:\n"
    "\n"
    "  time:\n"
    "    Length of scene time in seconds that the timer will wait\n"
    "    before firing.\n"
    "\n"
    "  call:\n"
    "    A callable Python object. Note that the timer will retain a\n"
    "    strong reference to the callable for as long as it exists, so you\n"
    "    may want to look into concepts such as :class:`bascenev1.WeakCall`\n"
    "    if that is not desired.\n"
    "\n"
    "  repeat:\n"
    "    If True, the timer will fire repeatedly, with each successive\n"
    "    firing having the same delay as the first.\n"
    "\n"
    "Examples\n"
    "========\n"
    "\n"
    "Print some stuff through time::\n"
    "\n"
    "  import bascenev1 as bs\n"
    "  bs.screenmessage('hello from now!')\n"
    "  bs.timer(1.0, bs.Call(bs.screenmessage, 'hello from the future!'))\n"
    "  bs.timer(2.0, bs.Call(bs.screenmessage, 'hello from the future 2!'))\n",
};

// ----------------------------- basetime -----------------------------------

static auto PyBaseTime(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  auto timeval = SceneV1Context::Current().GetTime(TimeType::kBase);
  return PyFloat_FromDouble(0.001 * static_cast<double>(timeval));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyBaseTimeDef = {
    "basetime",                    // name
    (PyCFunction)PyBaseTime,       // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "basetime() -> bascenev1.BaseTime\n"
    "\n"
    "Return the base-time in seconds for the current scene-v1 context.\n"
    "\n"
    "Base-time is a time value that progresses at a constant rate for a "
    "scene,\n"
    "even when the scene is sped up, slowed down, or paused. It may, however,\n"
    "speed up or slow down due to replay speed adjustments or may slow down\n"
    "if the cpu is overloaded."
    "\n"
    "Note that the value returned here is simply a float; it just has a\n"
    "unique type in the type-checker's eyes to help prevent it from being\n"
    "accidentally used with time functionality expecting other time types.",
};

// --------------------------------- timer -------------------------------------

static auto PyBaseTimer(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());

  double length{};
  int repeat{};
  PyObject* call_obj{};
  static const char* kwlist[] = {"time", "call", "repeat", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "dO|p",
                                   const_cast<char**>(kwlist), &length,
                                   &call_obj, &repeat)) {
    return nullptr;
  }

  SceneV1Context::Current().NewTimer(
      TimeType::kBase, static_cast<millisecs_t>(length * 1000.0),
      static_cast<bool>(repeat),
      Object::New<Runnable, base::PythonContextCallRunnable>(call_obj).get());

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyBaseTimerDef = {
    "basetimer",                   // name
    (PyCFunction)PyBaseTimer,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "basetimer(time: float, call: Callable[[], Any], repeat: bool = False)\n"
    " -> None\n"
    "\n"
    "Schedule a call to run at a later point in scene base-time.\n"
    "Base-time is a value that progresses at a constant rate for a scene,\n"
    "even when the scene is sped up, slowed down, or paused. It may,\n"
    "however, speed up or slow down due to replay speed adjustments or may\n"
    "slow down if the cpu is overloaded.\n"
    "\n"
    "This function adds a timer to the current scene context.\n"
    "This timer cannot be canceled or modified once created. If you\n"
    "require the ability to do so, use the bascenev1.BaseTimer class\n"
    "instead.\n"
    "\n"
    "Args:\n"
    "  time:\n"
    "    Length of time in seconds that the timer will wait before firing.\n"
    "\n"
    "  call:\n"
    "    A callable Python object. Remember that the timer will retain a\n"
    "    strong reference to the callable for the duration of the timer, so\n"
    "    you may want to look into concepts such as :class:`~babase.WeakCall`\n"
    "    if that is not desired.\n"
    "\n"
    "  repeat:\n"
    "    If True, the timer will fire repeatedly, with each successive\n"
    "    firing having the same delay as the first.\n"
    "\n"
    "Example: Print some stuff through time::\n"
    "\n"
    "   import bascenev1 as bs\n"
    "\n"
    "   bs.screenmessage('hello from now!')\n"
    "   bs.basetimer(1.0, bs.Call(bs.screenmessage,\n"
    "                'hello from the future!'))\n"
    "   bs.basetimer(2.0, bs.Call(bs.screenmessage,\n"
    "                'hello from the future 2!'))\n",
};

// ------------------------------- getsession ----------------------------------

static auto PyGetSession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int raise = true;
  static const char* kwlist[] = {"doraise", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|i",
                                   const_cast<char**>(kwlist), &raise)) {
    return nullptr;
  }
  if (HostSession* hs = ContextRefSceneV1::FromCurrent().GetHostSession()) {
    PyObject* obj = hs->GetSessionPyObj();
    if (obj) {
      Py_INCREF(obj);
      return obj;
    }
  } else {
    if (raise) {
      throw Exception(PyExcType::kSessionNotFound);
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSessionDef = {
    "getsession",                  // name
    (PyCFunction)PyGetSession,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getsession(doraise: bool = True) -> <varies>\n"
    "\n"
    "Return the session associated with the current context. If there is\n"
    "none, a :class:`~bascenev1.SessionNotFoundError` is raised (unless\n"
    "``doraise`` is False, in which case ``None`` is returned instead)."};

// --------------------------- new_host_session --------------------------------

static auto PyNewHostSession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* benchmark_type_str = nullptr;
  static const char* kwlist[] = {"sessiontype", "benchmark_type", nullptr};
  PyObject* sessiontype_obj;
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|s",
                                   const_cast<char**>(kwlist), &sessiontype_obj,
                                   &benchmark_type_str)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  base::BenchmarkType benchmark_type = base::BenchmarkType::kNone;
  if (benchmark_type_str != nullptr) {
    if (!strcmp(benchmark_type_str, "cpu")) {
      benchmark_type = base::BenchmarkType::kCPU;
    } else if (!strcmp(benchmark_type_str, "gpu")) {
      benchmark_type = base::BenchmarkType::kGPU;
    } else {
      throw Exception(
          "Invalid benchmark type: '" + std::string(benchmark_type_str) + "'",
          PyExcType::kValue);
    }
  }
  appmode->LaunchHostSession(sessiontype_obj, benchmark_type);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNewHostSessionDef = {
    "new_host_session",             // name
    (PyCFunction)PyNewHostSession,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "new_host_session(sessiontype: type[bascenev1.Session],\n"
    "  benchmark_type: str | None = None) -> None\n"
    "\n"
    "(internal)",
};

// -------------------------- new_replay_session -------------------------------

static auto PyNewReplaySession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string file_name;
  PyObject* file_name_obj;
  static const char* kwlist[] = {"file_name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &file_name_obj)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  file_name = Python::GetString(file_name_obj);
  appmode->LaunchReplaySession(file_name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNewReplaySessionDef = {
    "new_replay_session",             // name
    (PyCFunction)PyNewReplaySession,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "new_replay_session(file_name: str) -> None\n"
    "\n"
    "(internal)",
};

// ------------------------------ is_in_replay ---------------------------------

static auto PyIsInReplay(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActive();
  if (appmode
      && dynamic_cast<ClientSessionReplay*>(appmode->GetForegroundSession())) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIsInReplayDef = {
    "is_in_replay",                // name
    (PyCFunction)PyIsInReplay,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "is_in_replay() -> bool\n"
    "\n"
    "(internal)",
};

// -------------------------- register_session-------- -------------------------

static auto PyRegisterSession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* session_obj;
  static const char* kwlist[] = {"session", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &session_obj)) {
    return nullptr;
  }
  HostSession* hsc = ContextRefSceneV1::FromCurrent().GetHostSession();
  if (!hsc) {
    throw Exception("No HostSession found.");
  }

  // Store our py obj with our HostSession and return
  // the HostSession to be stored with our py obj.
  hsc->RegisterPySession(session_obj);
  return PythonClassSessionData::Create(hsc);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRegisterSessionDef = {
    "register_session",              // name
    (PyCFunction)PyRegisterSession,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "register_session(session: bascenev1.Session)"
    " -> bascenev1.SessionData\n"
    "\n"
    "(internal)",
};

// --------------------------- register_activity -------------------------------

static auto PyRegisterActivity(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  PyObject* activity_obj;
  static const char* kwlist[] = {"activity", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &activity_obj)) {
    return nullptr;
  }
  HostSession* hs = ContextRefSceneV1::FromCurrent().GetHostSession();
  if (!hs) {
    throw Exception("No HostSession found");
  }

  // Generate and return an ActivityData for this guy..
  // (basically just a link to its C++ equivalent).
  return PythonClassActivityData::Create(hs->RegisterPyActivity(activity_obj));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRegisterActivityDef = {
    "register_activity",              // name
    (PyCFunction)PyRegisterActivity,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "register_activity(activity: bascenev1.Activity)"
    " -> bascenev1.ActivityData\n"
    "\n"
    "(internal)",
};

// ---------------------- get_foreground_host_session --------------------------

static auto PyGetForegroundHostSession(PyObject* self, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }

  // Note: we return None if not in the logic thread.
  HostSession* s =
      g_base->InLogicThread()
          ? ContextRefSceneV1::FromAppForegroundContext().GetHostSession()
          : nullptr;
  if (s != nullptr) {
    PyObject* obj = s->GetSessionPyObj();
    Py_INCREF(obj);
    return obj;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetForegroundHostSessionDef = {
    "get_foreground_host_session",            // name
    (PyCFunction)PyGetForegroundHostSession,  // method
    METH_VARARGS | METH_KEYWORDS,             // flags

    "get_foreground_host_session() -> bascenev1.Session | None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the bascenev1.Session currently being displayed,"
    " or None if there is\n"
    "none.",
};

// ----------------------------- newactivity -----------------------------------

static auto PyNewActivity(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  static const char* kwlist[] = {"activity_type", "settings", nullptr};
  PyObject* activity_type_obj;
  PyObject* settings_obj = Py_None;
  PythonRef settings;

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|O",
                                   const_cast<char**>(kwlist),
                                   &activity_type_obj, &settings_obj)) {
    return nullptr;
  }

  // If they passed a settings dict, make a shallow copy of it (so we dont
  // inadvertently mess up level lists or whatever the settings came from).
  if (settings_obj != Py_None) {
    if (!PyDict_Check(settings_obj)) {
      throw Exception("Expected a dict for settings.", PyExcType::kType);
    }
    PythonRef args2(Py_BuildValue("(O)", settings_obj), PythonRef::kSteal);
    settings = g_core->python->objs()
                   .Get(core::CorePython::ObjID::kShallowCopyCall)
                   .Call(args2);
    if (!settings.exists()) {
      throw Exception("Unable to shallow-copy settings.");
    }
  } else {
    settings.Acquire(settings_obj);
  }

  HostSession* hs = ContextRefSceneV1::FromCurrent().GetHostSession();
  if (!hs) {
    throw Exception("No HostSession found.", PyExcType::kContext);
  }
  return hs->NewHostActivity(activity_type_obj, settings.get());

  BA_PYTHON_CATCH;
}

static PyMethodDef PyNewActivityDef = {
    "newactivity",                 // name
    (PyCFunction)PyNewActivity,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "newactivity(activity_type: type[bascenev1.Activity],\n"
    "  settings: dict | None = None) -> bascenev1.Activity\n"
    "\n"
    "Instantiates a bascenev1.Activity given a type object.\n"
    "\n"
    "Activities require special setup and thus cannot be directly\n"
    "instantiated; you must go through this function.",
};

// ----------------------------- getactivity -----------------------------------

static auto PyGetActivity(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int raise = true;
  static const char* kwlist[] = {"doraise", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|i",
                                   const_cast<char**>(kwlist), &raise)) {
    return nullptr;
  }

  // Fail gracefully if called from outside the logic thread.
  if (!g_base->InLogicThread()) {
    Py_RETURN_NONE;
  }

  PyObject* ret_obj{};

  if (HostActivity* hostactivity =
          ContextRefSceneV1::FromCurrent().GetHostActivity()) {
    // GetPyActivity() returns a new ref or nullptr.
    auto obj{PythonRef::StolenSoft(hostactivity->GetPyActivity())};
    if (obj.exists()) {
      ret_obj = obj.NewRef();
    }
  }

  if (ret_obj) {
    return ret_obj;
  }

  if (raise) {
    throw Exception(PyExcType::kActivityNotFound);
  }
  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetActivityDef = {
    "getactivity",                 // name
    (PyCFunction)PyGetActivity,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getactivity(doraise: bool = True) -> <varies>\n"
    "\n"
    "Return the current bascenev1.Activity instance.\n"
    "\n"
    "Note that this is based on context_ref; thus code run in a timer\n"
    "generated in Activity 'foo' will properly return 'foo' here, even if\n"
    "another Activity has since been created or is transitioning in.\n"
    "If there is no current Activity, raises a babase.ActivityNotFoundError.\n"
    "If doraise is False, None will be returned instead in that case.",
};

// -------------------------- broadcastmessage ---------------------------------

static auto PyBroadcastMessage(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* message = nullptr;
  PyObject* color_obj = Py_None;
  int top = 0;
  int transient = 0;
  PyObject* image_obj = Py_None;
  PyObject* message_obj;
  PyObject* clients_obj = Py_None;
  int log = 0;
  static const char* kwlist[] = {"message", "color",   "top",       "image",
                                 "log",     "clients", "transient", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O|OpOiOi", const_cast<char**>(kwlist), &message_obj,
          &color_obj, &top, &image_obj, &log, &clients_obj, &transient)) {
    return nullptr;
  }
  std::string message_str = g_base->python->GetPyLString(message_obj);
  message = message_str.c_str();
  Vector3f color{1, 1, 1};
  if (color_obj != Py_None) {
    color = base::BasePython::GetPyVector3f(color_obj);
  }
  if (message == nullptr) {
    PyErr_SetString(PyExc_AttributeError, "No message provided");
    return nullptr;
  }
  if (log) {
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kInfo, message);
  }

  // Transient messages get sent to clients as high-level messages instead of
  // being embedded into the game-stream.
  if (transient) {
    // This option doesn't support top or icons currently.
    if (image_obj != Py_None) {
      throw Exception(
          "The 'image' option is not currently supported for transient mode "
          "messages.",
          PyExcType::kValue);
    }
    if (top) {
      throw Exception(
          "The 'top' option is not currently supported for transient mode "
          "messages.",
          PyExcType::kValue);
    }
    std::vector<int32_t> client_ids;
    if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
      if (clients_obj != Py_None) {
        std::vector<int> client_ids2 = Python::GetInts(clients_obj);
        appmode->connections()->SendScreenMessageToSpecificClients(
            message, color.x, color.y, color.z, client_ids2);
      } else {
        appmode->connections()->SendScreenMessageToAll(message, color.x,
                                                       color.y, color.z);
      }
    }
  } else {
    // Currently specifying client_ids only works for transient messages; we'd
    // need a protocol change to support that in game output streams.
    // (or maintaining separate streams per client; yuck)
    if (clients_obj != Py_None) {
      throw Exception(
          "Specifying clients only works when using the 'transient' option",
          PyExcType::kValue);
    }
    Scene* context_scene = ContextRefSceneV1::FromCurrent().GetMutableScene();
    SessionStream* output_stream =
        context_scene ? context_scene->GetSceneStream() : nullptr;

    SceneTexture* texture = nullptr;
    SceneTexture* tint_texture = nullptr;
    Vector3f tint_color{1.0f, 1.0f, 1.0f};
    Vector3f tint2_color{1.0f, 1.0f, 1.0f};
    if (image_obj != Py_None) {
      if (PyDict_Check(image_obj)) {
        PyObject* obj = PyDict_GetItemString(image_obj, "texture");
        if (!obj) {
          throw Exception("Provided image dict contains no 'texture' entry.",
                          PyExcType::kValue);
        }
        texture = SceneV1Python::GetPySceneTexture(obj);

        obj = PyDict_GetItemString(image_obj, "tint_texture");
        if (!obj) {
          throw Exception(
              "Provided image dict contains no 'tint_texture' entry.",
              PyExcType::kValue);
        }
        tint_texture = SceneV1Python::GetPySceneTexture(obj);

        obj = PyDict_GetItemString(image_obj, "tint_color");
        if (!obj) {
          throw Exception("Provided image dict contains no 'tint_color' entry",
                          PyExcType::kValue);
        }
        tint_color = base::BasePython::GetPyVector3f(obj);
        obj = PyDict_GetItemString(image_obj, "tint2_color");
        if (!obj) {
          throw Exception("Provided image dict contains no 'tint2_color' entry",
                          PyExcType::kValue);
        }
        tint2_color = base::BasePython::GetPyVector3f(obj);
      } else {
        texture = SceneV1Python::GetPySceneTexture(image_obj);
      }
    }

    if (output_stream) {
      // FIXME: for now we just do bottom messages.
      if (texture == nullptr && !top) {
        output_stream->ScreenMessageBottom(message, color.x, color.y, color.z);
      } else if (top && texture != nullptr && tint_texture != nullptr) {
        if (texture->scene() != context_scene) {
          throw Exception("Texture is not from the current context_ref.",
                          PyExcType::kContext);
        }
        if (tint_texture->scene() != context_scene)
          throw Exception("Tint-texture is not from the current context_ref.",
                          PyExcType::kContext);
        output_stream->ScreenMessageTop(
            message, color.x, color.y, color.z, texture, tint_texture,
            tint_color.x, tint_color.y, tint_color.z, tint2_color.x,
            tint2_color.y, tint2_color.z);
      } else {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                             "Unhandled screenmessage output_stream case.");
      }
    }

    // Now display it locally.
    g_base->graphics->screenmessages->AddScreenMessage(
        message, color, static_cast<bool>(top),
        texture ? texture->texture_data() : nullptr,
        tint_texture ? tint_texture->texture_data() : nullptr, tint_color,
        tint2_color);
  }

  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyBroadcastMessageDef = {
    "broadcastmessage",               // name
    (PyCFunction)PyBroadcastMessage,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "broadcastmessage(message: str | babase.Lstr,\n"
    "  color: Sequence[float] | None = None,\n"
    "  top: bool = False,\n"
    "  image: dict[str, Any] | None = None,\n"
    "  log: bool = False,\n"
    "  clients: Sequence[int] | None = None,\n"
    "  transient: bool = False)"
    " -> None\n"
    "\n"
    "Broadcast a screen-message to clients in the current session.\n"
    "\n"
    "If 'top' is True, the message will go to the top message area.\n"
    "For 'top' messages, 'image' must be a dict containing 'texture'\n"
    "and 'tint_texture' textures and 'tint_color' and 'tint2_color'\n"
    "colors. This defines an icon to display alongside the message.\n"
    "If 'log' is True, the message will also be submitted to the log.\n"
    "'clients' can be a list of client-ids the message should be sent\n"
    "to, or None to specify that everyone should receive it.\n"
    "If 'transient' is True, the message will not be included in the\n"
    "game-stream and thus will not show up when viewing replays.\n"
    "Currently the 'clients' option only works for transient messages.",
};

// ------------------------------- newnode -------------------------------------

static auto PyNewNode(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Node* n = SceneV1Python::DoNewNode(args, keywds);
  if (!n) {
    return nullptr;
  }
  return n->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNewNodeDef = {
    "newnode",                     // name
    (PyCFunction)PyNewNode,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "newnode(type: str, owner: bascenev1.Node | None = None,\n"
    "  attrs: dict | None = None,\n"
    "  name: str | None = None,\n"
    "  delegate: Any = None) -> bascenev1.Node\n"
    "\n"
    "Add a node of the given type to the game.\n"
    "\n"
    "If a dict is provided for 'attributes', the node's initial attributes\n"
    "will be set based on them.\n"
    "\n"
    "'name', if provided, will be stored with the node purely for "
    "debugging\n"
    "purposes. If no name is provided, an automatic one will be generated\n"
    "such as 'terrain@foo.py:30'.\n"
    "\n"
    "If 'delegate' is provided, Python messages sent to the node will go "
    "to\n"
    "that object's handlemessage() method. Note that the delegate is "
    "stored\n"
    "as a weak-ref, so the node itself will not keep the object alive.\n"
    "\n"
    "if 'owner' is provided, the node will be automatically killed when "
    "that\n"
    "object dies. 'owner' can be another node or a bascenev1.Actor",
};

// ----------------------------- printnodes ------------------------------------

static auto PyPrintNodes(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  HostActivity* host_activity =
      ContextRefSceneV1::FromAppForegroundContext().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  Scene* scene = host_activity->scene();
  std::string s;
  int count = 1;
  for (auto&& i : scene->nodes()) {
    char buffer[128];
    snprintf(buffer, sizeof(buffer), "#%d:   type: %-14s desc: %s", count,
             i->type()->name().c_str(), i->label().c_str());
    s += buffer;
    g_core->logging->Log(LogName::kBa, LogLevel::kInfo, buffer);
    count++;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPrintNodesDef = {
    "printnodes",  // name
    PyPrintNodes,  // method
    METH_VARARGS,  // flags

    "printnodes() -> None\n"
    "\n"
    "Print various info about existing nodes; useful for debugging.",
};

// -------------------------------- getnodes -----------------------------------

static auto PyGetNodes(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  HostActivity* host_activity =
      ContextRefSceneV1::FromCurrent().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  Scene* scene = host_activity->scene();
  PyObject* py_list = PyList_New(0);
  for (auto&& i : scene->nodes()) {
    PyList_Append(py_list, i->BorrowPyRef());
  }
  return py_list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetNodesDef = {
    "getnodes",    // name
    PyGetNodes,    // method
    METH_VARARGS,  // flags

    "getnodes() -> list\n"
    "\n"
    "Return all nodes in the current scene context.",
};

// -------------------------- get_collision_info -------------------------------

static auto DoGetCollideValue(Dynamics* dynamics, const Collision* c,
                              const char* name) -> PyObject* {
  BA_PYTHON_TRY;
  if (!strcmp(name, "depth")) {
    return Py_BuildValue("f", c->depth);
  } else if (!strcmp(name, "position")) {
    return Py_BuildValue("(fff)", c->x, c->y, c->z);
  } else if (!strcmp(name, "sourcenode")) {
    if (!dynamics->in_collide_message()) {
      PyErr_SetString(
          PyExc_AttributeError,
          "collide value 'sourcenode' is only valid while processing "
          "collide messages");
      return nullptr;
    }
    Node* n = dynamics->GetActiveCollideSrcNode();
    if (n) {
      return n->NewPyRef();
    } else {
      Py_RETURN_NONE;
    }
  } else if (!strcmp(name, "opposingnode")) {
    if (!dynamics->in_collide_message()) {
      PyErr_SetString(
          PyExc_AttributeError,
          "collide value 'opposingnode' is only valid while processing "
          "collide messages");
      return nullptr;
    }
    Node* n = dynamics->GetActiveCollideDstNode();
    if (n) {
      return n->NewPyRef();
    } else {
      Py_RETURN_NONE;
    }
  } else if (!strcmp(name, "opposingbody")) {
    return Py_BuildValue("i", dynamics->GetCollideMessageReverseOrder()
                                  ? c->body_id_2
                                  : c->body_id_1);
  } else {
    PyErr_SetString(
        PyExc_AttributeError,
        (std::string("\"") + name + "\" is not a valid collide value name")
            .c_str());
    return nullptr;
  }
  BA_PYTHON_CATCH;
}

static auto PyGetCollisionInfo(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  HostActivity* host_activity =
      ContextRefSceneV1::FromCurrent().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  Dynamics* dynamics = host_activity->scene()->dynamics();
  assert(dynamics);
  PyObject* obj = nullptr;

  // Take arg list as individual items or possibly a single tuple
  Py_ssize_t argc = PyTuple_GET_SIZE(args);
  if (argc > 1) {
    obj = args;
  } else if (argc == 1) {
    obj = PyTuple_GET_ITEM(args, 0);
  }
  Collision* c = dynamics->active_collision();
  if (!c) {
    PyErr_SetString(PyExc_RuntimeError,
                    "This must be called from a collision callback.");
    return nullptr;
  }
  if (PyUnicode_Check(obj)) {
    return DoGetCollideValue(dynamics, c, PyUnicode_AsUTF8(obj));
  } else if (PyTuple_Check(obj)) {
    Py_ssize_t size = PyTuple_GET_SIZE(obj);

    // NOTE: Need to make sure we never release the GIL or call out to
    // code that could access gc stuff while building this. Ideally should
    // create contents first and then create/fill the tuple as last step.
    // See https://bugs.python.org/issue15108.
    PyObject* return_tuple = PyTuple_New(size);
    for (Py_ssize_t i = 0; i < size; i++) {
      PyObject* o = PyTuple_GET_ITEM(obj, i);
      if (PyUnicode_Check(o)) {
        PyObject* val_obj = DoGetCollideValue(dynamics, c, PyUnicode_AsUTF8(o));
        if (val_obj) {
          PyTuple_SET_ITEM(return_tuple, i, val_obj);
        } else {
          Py_DECREF(return_tuple);
          return nullptr;
        }
      } else {
        Py_DECREF(return_tuple);
        PyErr_SetString(PyExc_TypeError, "Expected a string as tuple member.");
        return nullptr;
      }
    }
    return return_tuple;
  } else {
    PyErr_SetString(PyExc_TypeError, "Expected a string or tuple.");
    return nullptr;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetCollisionInfoDef = {
    "get_collision_info",  // name
    PyGetCollisionInfo,    // method
    METH_VARARGS,          // flags

    "get_collision_info(*args: Any) -> Any\n"
    "\n"
    "Return collision related values\n"
    "\n"
    "Returns a single collision value or tuple of values such as location,\n"
    "depth, nodes involved, etc. Only call this in the handler of a\n"
    "collision-triggered callback or message",
};

// ------------------------------ camerashake ----------------------------------

static auto PyCameraShake(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->InLogicThread());
  float intensity = 1.0f;
  static const char* kwlist[] = {"intensity", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|f",
                                   const_cast<char**>(kwlist), &intensity)) {
    return nullptr;
  }

  if (Scene* scene = ContextRefSceneV1::FromCurrent().GetMutableScene()) {
    // Send to clients/replays (IF we're servering protocol 35+).
    if (classic::ClassicAppMode::GetSingleton()->host_protocol_version()
        >= 35) {
      if (SessionStream* output_stream = scene->GetSceneStream()) {
        output_stream->EmitCameraShake(intensity);
      }
    }

    // Depict locally.
    if (!g_core->HeadlessMode()) {
      g_base->graphics->LocalCameraShake(intensity);
    }
  } else {
    throw Exception("Can't shake the camera in this context_ref.",
                    PyExcType::kContext);
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCameraShakeDef = {
    "camerashake",                 // name
    (PyCFunction)PyCameraShake,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "camerashake(intensity: float = 1.0) -> None\n"
    "\n"
    "Shake the camera.\n"
    "\n"
    "Note that some cameras and/or platforms (such as VR) may not display\n"
    "camera-shake, so do not rely on this always being visible to the\n"
    "player as a gameplay cue.",
};

// -------------------------------- emitfx -------------------------------------

static auto PyEmitFx(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {"position",  "velocity",     "count",
                                 "scale",     "spread",       "chunk_type",
                                 "emit_type", "tendril_type", nullptr};
  PyObject* pos_obj = Py_None;
  PyObject* vel_obj = Py_None;
  int count = 10;
  float scale = 1.0f;
  float spread = 1.0f;
  const char* chunk_type_str = "rock";
  const char* emit_type_str = "chunks";
  const char* tendril_type_str = "smoke";
  assert(g_base->InLogicThread());
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O|Oiffsss", const_cast<char**>(kwlist), &pos_obj,
          &vel_obj, &count, &scale, &spread, &chunk_type_str, &emit_type_str,
          &tendril_type_str)) {
    return nullptr;
  }
  float x, y, z;
  assert(pos_obj);
  {
    std::vector<float> vals = Python::GetFloats(pos_obj);
    if (vals.size() != 3) {
      throw Exception("Expected 3 floats for position.", PyExcType::kValue);
    }
    x = vals[0];
    y = vals[1];
    z = vals[2];
  }
  float vx = 0.0f;
  float vy = 0.0f;
  float vz = 0.0f;
  if (vel_obj != Py_None) {
    std::vector<float> vals = Python::GetFloats(vel_obj);
    if (vals.size() != 3) {
      throw Exception("Expected 3 floats for velocity.", PyExcType::kValue);
    }
    vx = vals[0];
    vy = vals[1];
    vz = vals[2];
  }
  base::BGDynamicsChunkType chunk_type;
  if (!strcmp(chunk_type_str, "rock")) {
    chunk_type = base::BGDynamicsChunkType::kRock;
  } else if (!strcmp(chunk_type_str, "ice")) {
    chunk_type = base::BGDynamicsChunkType::kIce;
  } else if (!strcmp(chunk_type_str, "slime")) {
    chunk_type = base::BGDynamicsChunkType::kSlime;
  } else if (!strcmp(chunk_type_str, "metal")) {
    chunk_type = base::BGDynamicsChunkType::kMetal;
  } else if (!strcmp(chunk_type_str, "spark")) {
    chunk_type = base::BGDynamicsChunkType::kSpark;
  } else if (!strcmp(chunk_type_str, "splinter")) {
    chunk_type = base::BGDynamicsChunkType::kSplinter;
  } else if (!strcmp(chunk_type_str, "sweat")) {
    chunk_type = base::BGDynamicsChunkType::kSweat;
  } else {
    throw Exception(
        "Invalid chunk type: '" + std::string(chunk_type_str) + "'.",
        PyExcType::kValue);
  }
  base::BGDynamicsTendrilType tendril_type;
  if (!strcmp(tendril_type_str, "smoke")) {
    tendril_type = base::BGDynamicsTendrilType::kSmoke;
  } else if (!strcmp(tendril_type_str, "thin_smoke")) {
    tendril_type = base::BGDynamicsTendrilType::kThinSmoke;
  } else if (!strcmp(tendril_type_str, "ice")) {
    tendril_type = base::BGDynamicsTendrilType::kIce;
  } else {
    throw Exception(
        "Invalid tendril type: '" + std::string(tendril_type_str) + "'.",
        PyExcType::kValue);
  }
  base::BGDynamicsEmitType emit_type;
  if (!strcmp(emit_type_str, "chunks")) {
    emit_type = base::BGDynamicsEmitType::kChunks;
  } else if (!strcmp(emit_type_str, "stickers")) {
    emit_type = base::BGDynamicsEmitType::kStickers;
  } else if (!strcmp(emit_type_str, "tendrils")) {
    emit_type = base::BGDynamicsEmitType::kTendrils;
  } else if (!strcmp(emit_type_str, "distortion")) {
    emit_type = base::BGDynamicsEmitType::kDistortion;
  } else if (!strcmp(emit_type_str, "flag_stand")) {
    emit_type = base::BGDynamicsEmitType::kFlagStand;
  } else if (!strcmp(emit_type_str, "fairydust")) {
    emit_type = base::BGDynamicsEmitType::kFairyDust;
  } else {
    throw Exception("Invalid emit type: '" + std::string(emit_type_str) + "'.",
                    PyExcType::kValue);
  }
  if (Scene* scene = ContextRefSceneV1::FromCurrent().GetMutableScene()) {
    base::BGDynamicsEmission e;
    e.emit_type = emit_type;
    e.position = Vector3f(x, y, z);
    e.velocity = Vector3f(vx, vy, vz);
    e.count = count;
    e.scale = scale;
    e.spread = spread;
    e.chunk_type = chunk_type;
    e.tendril_type = tendril_type;

    // Send to clients/replays.
    if (SessionStream* output_stream = scene->GetSceneStream()) {
      output_stream->EmitBGDynamics(e);
    }

    // Depict locally.
    if (!g_core->HeadlessMode()) {
      g_base->bg_dynamics->Emit(e);
    }
  } else {
    throw Exception("Can't emit bg dynamics in this context_ref.",
                    PyExcType::kContext);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEmitFxDef = {
    "emitfx",                      // name
    (PyCFunction)PyEmitFx,         // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "emitfx(position: Sequence[float],\n"
    "  velocity: Sequence[float] | None = None,\n"
    "  count: int = 10, scale: float = 1.0, spread: float = 1.0,\n"
    "  chunk_type: str = 'rock', emit_type: str ='chunks',\n"
    "  tendril_type: str = 'smoke') -> None\n"
    "\n"
    "Emit particles, smoke, etc. into the fx sim layer.\n"
    "\n"
    "The fx sim layer is a secondary dynamics simulation that runs in\n"
    "the background and just looks pretty; it does not affect gameplay.\n"
    "Note that the actual amount emitted may vary depending on graphics\n"
    "settings, exiting element counts, or other factors.",
};

// ----------------------------- set_map_bounds --------------------------------

static auto PySetMapBounds(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  HostActivity* host_activity =
      ContextRefSceneV1::FromCurrent().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  float xmin, ymin, zmin, xmax, ymax, zmax;
  assert(g_base->InLogicThread());
  if (!PyArg_ParseTuple(args, "(ffffff)", &xmin, &ymin, &zmin, &xmax, &ymax,
                        &zmax)) {
    return nullptr;
  }
  host_activity->scene()->SetMapBounds(xmin, ymin, zmin, xmax, ymax, zmax);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetMapBoundsDef = {
    "set_map_bounds",              // name
    (PyCFunction)PySetMapBounds,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "set_map_bounds(bounds: tuple[float, float, float, float, float, "
    "float])\n"
    "  -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Set map bounds. Generally nodes that go outside of this box are "
    "killed.",
};

// -------------------- get_foreground_host_activities -------------------------

static auto PyGetForegroundHostActivity(PyObject* self, PyObject* args,
                                        PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }

  // Note: we return None if not in the logic thread.
  HostActivity* h =
      g_base->InLogicThread()
          ? ContextRefSceneV1::FromAppForegroundContext().GetHostActivity()
          : nullptr;
  if (h != nullptr) {
    // GetPyActivity returns a new ref or nullptr.
    auto obj{PythonRef::StolenSoft(h->GetPyActivity())};
    return obj.NewRef();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetForegroundHostActivityDef = {
    "get_foreground_host_activity",            // name
    (PyCFunction)PyGetForegroundHostActivity,  // method
    METH_VARARGS | METH_KEYWORDS,              // flags

    "get_foreground_host_activity() -> bascenev1.Activity | None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns the bascenev1.Activity currently in the foreground,\n"
    "or None if there is none.\n"};

// --------------------------- get_game_roster ---------------------------------

static auto PyGetGameRoster(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  PythonRef py_client_list(PyList_New(0), PythonRef::kSteal);

  cJSON* party = classic::ClassicAppMode::GetSingleton()->game_roster();
  assert(cJSON_IsArray(party));
  int len = cJSON_GetArraySize(party);
  for (int i = 0; i < len; i++) {
    cJSON* client = cJSON_GetArrayItem(party, i);
    if (cJSON_IsObject(client)) {
      cJSON* spec = cJSON_GetObjectItem(client, "spec");
      cJSON* players = cJSON_GetObjectItem(client, "p");
      PythonRef py_player_list(PyList_New(0), PythonRef::kSteal);
      if (cJSON_IsArray(players)) {
        int plen = cJSON_GetArraySize(players);
        for (int j = 0; j < plen; ++j) {
          cJSON* player = cJSON_GetArrayItem(players, j);
          if (cJSON_IsObject(player)) {
            cJSON* name = cJSON_GetObjectItem(player, "n");
            cJSON* py_name_full = cJSON_GetObjectItem(player, "nf");
            cJSON* id_obj = cJSON_GetObjectItem(player, "i");
            int id_val = cJSON_IsNumber(id_obj) ? id_obj->valueint : -1;
            if (cJSON_IsString(name) && cJSON_IsString(py_name_full)
                && cJSON_IsNumber(id_obj)) {
              PythonRef py_player(
                  Py_BuildValue(
                      "{sssssi}", "name",
                      Utils::GetValidUTF8(name->valuestring, "ggr1").c_str(),
                      "name_full",
                      Utils::GetValidUTF8(py_name_full->valuestring, "ggr2")
                          .c_str(),
                      "id", id_val),
                  PythonRef::kSteal);
              // This increments ref.
              PyList_Append(py_player_list.get(), py_player.get());
            }
          }
        }
      }

      // If there's a client_id with this data, include it; otherwise pass None.
      cJSON* client_id = cJSON_GetObjectItem(client, "i");
      int clientid{};
      PythonRef client_id_ref;
      if (client_id != nullptr) {
        clientid = client_id->valueint;
        client_id_ref.Steal(PyLong_FromLong(clientid));
      } else {
        client_id_ref.Acquire(Py_None);
      }

      // Let's also include a public account-id if we have one.
      std::string account_id;
      if (clientid == -1) {
        account_id = g_base->Plus()->GetPublicV1AccountID();
      } else {
        if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
          auto client2 =
              appmode->connections()->connections_to_clients().find(clientid);
          if (client2
              != appmode->connections()->connections_to_clients().end()) {
            account_id = client2->second->peer_public_account_id();
          }
        }
      }
      PythonRef account_id_ref;
      if (account_id.empty()) {
        account_id_ref.Acquire(Py_None);
      } else {
        account_id_ref.Steal(PyUnicode_FromString(account_id.c_str()));
      }

      auto py_client{PythonRef::Stolen(Py_BuildValue(
          "{sssssOsOsO}", "display_string",
          cJSON_IsString(spec)
              ? PlayerSpec(spec->valuestring).GetDisplayString().c_str()
              : "",
          "spec_string", cJSON_IsString(spec) ? spec->valuestring : "",
          "players", py_player_list.get(), "client_id", client_id_ref.get(),
          "account_id", account_id_ref.get()))};

      PyList_Append(py_client_list.get(), py_client.get());
    }
  }
  return py_client_list.NewRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetGameRosterDef = {
    "get_game_roster",             // name
    (PyCFunction)PyGetGameRoster,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_game_roster() -> list[dict[str, Any]]\n"
    "\n"
    "(internal)",
};

// ----------------------- set_debug_speed_exponent ----------------------------

static auto PySetDebugSpeedExponent(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  int speed;
  if (!PyArg_ParseTuple(args, "i", &speed)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  HostActivity* host_activity =
      ContextRefSceneV1::FromCurrent().GetHostActivity();
  if (!host_activity) {
    throw Exception(PyExcType::kContext);
  }
  if (g_buildconfig.debug_build()) {
    appmode->SetDebugSpeedExponent(speed);
  } else {
    throw Exception("This call only functions in the debug build.");
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetDebugSpeedExponentDef = {
    "set_debug_speed_exponent",  // name
    PySetDebugSpeedExponent,     // method
    METH_VARARGS,                // flags

    "set_debug_speed_exponent(speed: int) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Sets the debug speed scale for the game. Actual speed is "
    "pow(2,speed).",
};

// ----------------------- get_replay_speed_exponent ---------------------------

static auto PyGetReplaySpeedExponent(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  return PyLong_FromLong(appmode->replay_speed_exponent());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetReplaySpeedExponentDef = {
    "get_replay_speed_exponent",  // name
    PyGetReplaySpeedExponent,     // method
    METH_VARARGS,                 // flags

    "get_replay_speed_exponent() -> int\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns current replay speed value. Actual displayed speed is "
    "pow(2,speed).",
};

// ------------------------ set_replay_speed_exponent --------------------------

static auto PySetReplaySpeedExponent(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  int speed;
  if (!PyArg_ParseTuple(args, "i", &speed)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->SetReplaySpeedExponent(speed);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetReplaySpeedExponentDef = {
    "set_replay_speed_exponent",  // name
    PySetReplaySpeedExponent,     // method
    METH_VARARGS,                 // flags

    "set_replay_speed_exponent(speed: int) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Set replay speed. Actual displayed speed is pow(2, speed).",
};

// -------------------------- is_replay_paused ---------------------------------

static auto PyIsReplayPaused(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  if (appmode->is_replay_paused()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIsReplayPausedDef = {
    "is_replay_paused",  // name
    PyIsReplayPaused,    // method
    METH_VARARGS,        // flags

    "is_replay_paused() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns if Replay is paused or not.",
};
// ------------------------ pause_replay ---------------------------------------

static auto PyPauseReplay(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->PauseReplay();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPauseReplayDef = {
    "pause_replay",  // name
    PyPauseReplay,   // method
    METH_VARARGS,    // flags

    "pause_replay() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Pauses replay.",
};

// ------------------------ resume_replay --------------------------------------

static auto PyResumeReplay(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->ResumeReplay();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyResumeReplayDef = {
    "resume_replay",  // name
    PyResumeReplay,   // method
    METH_VARARGS,     // flags

    "resume_replay() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Resumes replay.",
};

// -------------------------- seek_replay --------------------------------------

static auto PySeekReplay(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  auto* session =
      dynamic_cast<ClientSessionReplay*>(appmode->GetForegroundSession());
  if (session == nullptr) {
    throw Exception(
        "Attempting to seek a replay not in replay session context.");
  }
  float delta;
  if (!PyArg_ParseTuple(args, "f", &delta)) {
    return nullptr;
  }
  session->SeekTo(session->base_time()
                  + static_cast<millisecs_t>(delta * 1'000));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySeekReplayDef = {
    "seek_replay",  // name
    PySeekReplay,   // method
    METH_VARARGS,   // flags

    "seek_replay(delta: float) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Rewind or fast-forward replay.",
};

// ----------------------- reset_random_player_names ---------------------------

static auto PyResetRandomPlayerNames(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  SceneV1InputDeviceDelegate::ResetRandomNames();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyResetRandomPlayerNamesDef = {
    "reset_random_player_names",            // name
    (PyCFunction)PyResetRandomPlayerNames,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "reset_random_player_names() -> None\n"
    "\n"
    "(internal)",
};

// --------------------------- get_random_names --------------------------------

static auto PyGetRandomNames(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* list = PyList_New(0);
  const std::list<std::string>& random_name_list = Utils::GetRandomNameList();
  for (const auto& i : random_name_list) {
    assert(Utils::IsValidUTF8(i));
    PyObject* obj = PyUnicode_FromString(i.c_str());
    PyList_Append(list, obj);
    Py_DECREF(obj);
  }
  return list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetRandomNamesDef = {
    "get_random_names",  // name
    PyGetRandomNames,    // method
    METH_VARARGS,        // flags

    "get_random_names() -> list\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns the random names used by the game.",
};

// -------------------------------- ls_objects ---------------------------------

static auto PyLsObjects(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Object::LsObjects();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyLsObjectsDef = {
    "ls_objects",                  // name
    (PyCFunction)PyLsObjects,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "ls_objects() -> None\n"
    "\n"
    "Log debugging info about C++ level objects.\n"
    "\n"
    "This call only functions in debug builds of the game.\n"
    "It prints various info about the current object count, etc.",
};

// --------------------------- ls_input_devices --------------------------------

static auto PyLsInputDevices(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_base->input->LsInputDevices();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyLsInputDevicesDef = {
    "ls_input_devices",             // name
    (PyCFunction)PyLsInputDevices,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "ls_input_devices() -> None\n"
    "\n"
    "Log debugging info about input devices.",
};

// -------------------------- set_internal_music -------------------------------

static auto PySetInternalMusic(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  PyObject* music_obj;
  float volume{1.0};
  int loop{1};
  static const char* kwlist[] = {"music", "volume", "loop", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|fp",
                                   const_cast<char**>(kwlist), &music_obj,
                                   &volume, &loop)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  if (music_obj == Py_None) {
    appmode->SetInternalMusic(nullptr);
  } else {
    auto& sound = base::PythonClassSimpleSound::FromPyObj(music_obj).sound();
    appmode->SetInternalMusic(&sound, volume, loop);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetInternalMusicDef = {
    "set_internal_music",             // name
    (PyCFunction)PySetInternalMusic,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "set_internal_music(music: babase.SimpleSound | None,\n"
    "   volume: float = 1.0, loop: bool  = True) -> None\n"
    "\n"
    "(internal).",
};

// ---------------------------- protocol_version -------------------------------

static auto PyProtocolVersion(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  return PyLong_FromLong(
      classic::ClassicAppMode::GetActiveOrThrow()->host_protocol_version());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyProtocolVersionDef = {
    "protocol_version",              // name
    (PyCFunction)PyProtocolVersion,  // method
    METH_NOARGS,                     // flags

    "protocol_version() -> int\n"
    "\n"
    "(internal)\n",
};

// -----------------------------------------------------------------------------

auto PythonMethodsScene::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyNewReplaySessionDef,
      PyNewHostSessionDef,
      PyGetSessionDef,
      PyGetActivityDef,
      PyNewActivityDef,
      PyGetForegroundHostSessionDef,
      PyRegisterActivityDef,
      PyRegisterSessionDef,
      PyIsInReplayDef,
      PyBroadcastMessageDef,
      PyGetRandomNamesDef,
      PyResetRandomPlayerNamesDef,
      PySetReplaySpeedExponentDef,
      PyGetReplaySpeedExponentDef,
      PyIsReplayPausedDef,
      PySeekReplayDef,
      PyPauseReplayDef,
      PyResumeReplayDef,
      PySetDebugSpeedExponentDef,
      PyGetGameRosterDef,
      PyGetForegroundHostActivityDef,
      PySetMapBoundsDef,
      PyEmitFxDef,
      PyCameraShakeDef,
      PyGetCollisionInfoDef,
      PyGetNodesDef,
      PySetInternalMusicDef,
      PyPrintNodesDef,
      PyNewNodeDef,
      PyLsObjectsDef,
      PyTimeDef,
      PyTimerDef,
      PyBaseTimeDef,
      PyBaseTimerDef,
      PyLsInputDevicesDef,
      PyProtocolVersionDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
