// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_app.h"

#include "ballistica/app/app.h"
#include "ballistica/app/app_flavor.h"
#include "ballistica/assets/component/texture.h"
#include "ballistica/core/logging.h"
#include "ballistica/core/thread.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/logic/connection/connection_set.h"
#include "ballistica/logic/host_activity.h"
#include "ballistica/logic/session/host_session.h"
#include "ballistica/logic/session/replay_client_session.h"
#include "ballistica/python/class/python_class_activity_data.h"
#include "ballistica/python/class/python_class_session_data.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_context_call_runnable.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/scene_stream.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

// Python does lots of signed bitwise stuff; turn off those warnings here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

auto PyAppName(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // This will get subbed out by standard filtering.
  return PyUnicode_FromString("ballisticacore");
  BA_PYTHON_CATCH;
}

auto PyAppNameUpper(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // This will get subbed out by standard filtering.
  return PyUnicode_FromString("BallisticaCore");
  BA_PYTHON_CATCH;
}

auto PyIsXCodeBuild(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.xcode_build()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyCanDisplayFullUnicode(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.enable_os_font_rendering()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyGetSession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int raise = true;
  static const char* kwlist[] = {"doraise", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|i",
                                   const_cast<char**>(kwlist), &raise)) {
    return nullptr;
  }
  if (HostSession* hs = Context::current().GetHostSession()) {
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

auto PyNewHostSession(PyObject* self, PyObject* args, PyObject* keywds)
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
  BenchmarkType benchmark_type = BenchmarkType::kNone;
  if (benchmark_type_str != nullptr) {
    if (!strcmp(benchmark_type_str, "cpu")) {
      benchmark_type = BenchmarkType::kCPU;
    } else if (!strcmp(benchmark_type_str, "gpu")) {
      benchmark_type = BenchmarkType::kGPU;
    } else {
      throw Exception(
          "Invalid benchmark type: '" + std::string(benchmark_type_str) + "'",
          PyExcType::kValue);
    }
  }
  g_logic->LaunchHostSession(sessiontype_obj, benchmark_type);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyNewReplaySession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string file_name;
  PyObject* file_name_obj;
  static const char* kwlist[] = {"file_name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &file_name_obj)) {
    return nullptr;
  }
  file_name = Python::GetPyString(file_name_obj);
  g_logic->LaunchReplaySession(file_name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIsInReplay(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (dynamic_cast<ReplayClientSession*>(g_logic->GetForegroundSession())) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyAppInstanceUUID(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(GetAppInstanceUUID().c_str());
  BA_PYTHON_CATCH;
}

auto PyUserRanCommands(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_app->user_ran_commands = true;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyRegisterSession(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InLogicThread());
  PyObject* session_obj;
  static const char* kwlist[] = {"session", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &session_obj)) {
    return nullptr;
  }
  HostSession* hsc = Context::current().GetHostSession();
  if (!hsc) {
    throw Exception("No HostSession found.");
  }

  // Store our py obj with our HostSession and return
  // the HostSession to be stored with our py obj.
  hsc->RegisterPySession(session_obj);
  return PythonClassSessionData::Create(hsc);
  BA_PYTHON_CATCH;
}

auto PyRegisterActivity(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InLogicThread());
  PyObject* activity_obj;
  static const char* kwlist[] = {"activity", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &activity_obj)) {
    return nullptr;
  }
  HostSession* hs = Context::current().GetHostSession();
  if (!hs) {
    throw Exception("No HostSession found");
  }

  // Generate and return an ActivityData for this guy..
  // (basically just a link to its C++ equivalent).
  return PythonClassActivityData::Create(hs->RegisterPyActivity(activity_obj));
  BA_PYTHON_CATCH;
}

auto PyGetForegroundHostSession(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }

  // Note: we return None if not in the logic thread.
  HostSession* s = InLogicThread()
                       ? g_logic->GetForegroundContext().GetHostSession()
                       : nullptr;
  if (s != nullptr) {
    PyObject* obj = s->GetSessionPyObj();
    Py_INCREF(obj);
    return obj;
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyNewActivity(PyObject* self, PyObject* args, PyObject* keywds)
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
    settings = g_python->obj(Python::ObjID::kShallowCopyCall).Call(args2);
    if (!settings.exists()) {
      throw Exception("Unable to shallow-copy settings.");
    }
  } else {
    settings.Acquire(settings_obj);
  }

  HostSession* hs = Context::current().GetHostSession();
  if (!hs) {
    throw Exception("No HostSession found.", PyExcType::kContext);
  }
  return hs->NewHostActivity(activity_type_obj, settings.get());

  BA_PYTHON_CATCH;
}

auto PyGetActivity(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int raise = true;
  static const char* kwlist[] = {"doraise", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|i",
                                   const_cast<char**>(kwlist), &raise)) {
    return nullptr;
  }

  // Fail gracefully if called from outside the logic thread.
  if (!InLogicThread()) {
    Py_RETURN_NONE;
  }

  if (HostActivity* hostactivity = Context::current().GetHostActivity()) {
    PyObject* obj = hostactivity->GetPyActivity();
    Py_INCREF(obj);
    return obj;
  } else {
    if (raise) {
      throw Exception(PyExcType::kActivityNotFound);
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyPushCall(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* call_obj;
  int from_other_thread{};
  int suppress_warning{};
  int other_thread_use_fg_context{};
  int raw{0};
  static const char* kwlist[] = {"call",
                                 "from_other_thread",
                                 "suppress_other_thread_warning",
                                 "other_thread_use_fg_context",
                                 "raw",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|pppp",
                                   const_cast<char**>(kwlist), &call_obj,
                                   &from_other_thread, &suppress_warning,
                                   &other_thread_use_fg_context, &raw)) {
    return nullptr;
  }

  // 'raw' mode does no thread checking and no context saves/restores.
  if (raw) {
    Py_INCREF(call_obj);
    g_logic->thread()->PushCall([call_obj] {
      assert(InLogicThread());

      PythonRef(call_obj, PythonRef::kSteal).Call();
    });
  } else if (from_other_thread) {
    // Warn the user not to use this from the logic thread since it doesnt
    // save/restore context.
    if (!suppress_warning && InLogicThread()) {
      g_python->IssueCallInLogicThreadWarning(call_obj);
    }

    // This gets called from other python threads so we can't construct
    // Objects and things here or we'll trip our thread-checks. Instead we
    // just increment the python object's refcount and pass it along raw;
    // the logic thread decrements it on the other end.
    Py_INCREF(call_obj);
    g_logic->PushPythonRawCallable(call_obj, other_thread_use_fg_context);
  } else {
    if (!InLogicThread()) {
      throw Exception("You must use from_other_thread mode.");
    }
    g_logic->PushPythonCall(Object::New<PythonContextCall>(call_obj));
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyTime(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* time_type_obj = nullptr;
  PyObject* time_format_obj = nullptr;
  static const char* kwlist[] = {"timetype", "timeformat", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|OO",
                                   const_cast<char**>(kwlist), &time_type_obj,
                                   &time_format_obj)) {
    return nullptr;
  }

  auto time_type = TimeType::kSim;
  if (time_type_obj != nullptr) {
    time_type = Python::GetPyEnum_TimeType(time_type_obj);
  }
  auto time_format = TimeFormat::kSeconds;
  if (time_format_obj != nullptr) {
    time_format = Python::GetPyEnum_TimeFormat(time_format_obj);
  }

  millisecs_t timeval;
  if (time_type == TimeType::kReal) {
    // Special case; we don't require a context for 'real'.
    timeval = GetRealTime();
  } else {
    // Make sure we've got a valid context-target and ask it for
    // this type of time.
    if (!Context::current().target.exists()) {
      throw Exception(PyExcType::kContext);
    }
    timeval = Context::current().target->GetTime(time_type);
  }

  if (time_format == TimeFormat::kSeconds) {
    return PyFloat_FromDouble(0.001 * timeval);
  } else if (time_format == TimeFormat::kMilliseconds) {
    return PyLong_FromLong(static_cast_check_fit<long>(timeval));  // NOLINT
  } else {
    throw Exception(
        "Invalid timeformat: " + std::to_string(static_cast<int>(time_format)),
        PyExcType::kValue);
  }
  BA_PYTHON_CATCH;
}

auto PyTimer(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  assert(InLogicThread());

  PyObject* length_obj;
  int64_t length;
  int repeat = 0;
  int suppress_format_warning = 0;
  PyObject* call_obj;
  PyObject* time_type_obj = nullptr;
  PyObject* time_format_obj = nullptr;
  static const char* kwlist[] = {"time",       "call",
                                 "repeat",     "timetype",
                                 "timeformat", "suppress_format_warning",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "OO|pOOp", const_cast<char**>(kwlist), &length_obj,
          &call_obj, &repeat, &time_type_obj, &time_format_obj,
          &suppress_format_warning)) {
    return nullptr;
  }

  auto time_type = TimeType::kSim;
  if (time_type_obj != nullptr) {
    time_type = Python::GetPyEnum_TimeType(time_type_obj);
  }
  auto time_format = TimeFormat::kSeconds;
  if (time_format_obj != nullptr) {
    time_format = Python::GetPyEnum_TimeFormat(time_format_obj);
  }

#if BA_TEST_BUILD || BA_DEBUG_BUILD
  if (!suppress_format_warning) {
    g_python->TimeFormatCheck(time_format, length_obj);
  }
#endif

  // We currently work with integer milliseconds internally.
  if (time_format == TimeFormat::kSeconds) {
    length = static_cast<int>(Python::GetPyDouble(length_obj) * 1000.0);
  } else if (time_format == TimeFormat::kMilliseconds) {
    length = Python::GetPyInt64(length_obj);
  } else {
    throw Exception("invalid timeformat: '"
                        + std::to_string(static_cast<int>(time_format)) + "'",
                    PyExcType::kValue);
  }
  if (length < 0) {
    throw Exception("Timer length < 0", PyExcType::kValue);
  }

  // Grab a ref to this here so it doesn't leak on exceptions.
  auto runnable(Object::New<Runnable, PythonContextCallRunnable>(call_obj));

  // Special case; we disallow repeating real timers currently.
  if (time_type == TimeType::kReal && repeat) {
    throw Exception("Repeating real timers not allowed here; use ba.Timer().",
                    PyExcType::kValue);
  }

  // Now just make sure we've got a valid context-target and ask us to
  // make us a timer.
  if (!Context::current().target.exists()) {
    throw Exception(PyExcType::kContext);
  }
  Context::current().target->NewTimer(time_type, length,
                                      static_cast<bool>(repeat), runnable);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyScreenMessage(PyObject* self, PyObject* args, PyObject* keywds)
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
  std::string message_str = Python::GetPyString(message_obj);
  message = message_str.c_str();
  Vector3f color{1, 1, 1};
  if (color_obj != Py_None) {
    color = Python::GetPyVector3f(color_obj);
  }
  if (message == nullptr) {
    PyErr_SetString(PyExc_AttributeError, "No message provided");
    return nullptr;
  }
  if (log) {
    Log(LogLevel::kInfo, message);
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
    if (clients_obj != Py_None) {
      std::vector<int> client_ids2 = Python::GetPyInts(clients_obj);
      g_logic->connections()->SendScreenMessageToSpecificClients(
          message, color.x, color.y, color.z, client_ids2);
    } else {
      g_logic->connections()->SendScreenMessageToAll(message, color.x, color.y,
                                                     color.z);
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
    Scene* context_scene = Context::current().GetMutableScene();
    SceneStream* output_stream =
        context_scene ? context_scene->GetSceneStream() : nullptr;

    Texture* texture = nullptr;
    Texture* tint_texture = nullptr;
    Vector3f tint_color{1.0f, 1.0f, 1.0f};
    Vector3f tint2_color{1.0f, 1.0f, 1.0f};
    if (image_obj != Py_None) {
      if (PyDict_Check(image_obj)) {
        PyObject* obj = PyDict_GetItemString(image_obj, "texture");
        if (!obj)
          throw Exception("Provided image dict contains no 'texture' entry.",
                          PyExcType::kValue);
        texture = Python::GetPyTexture(obj);

        obj = PyDict_GetItemString(image_obj, "tint_texture");
        if (!obj)
          throw Exception(
              "Provided image dict contains no 'tint_texture' entry.",
              PyExcType::kValue);
        tint_texture = Python::GetPyTexture(obj);

        obj = PyDict_GetItemString(image_obj, "tint_color");
        if (!obj)
          throw Exception("Provided image dict contains no 'tint_color' entry",
                          PyExcType::kValue);
        tint_color = Python::GetPyVector3f(obj);
        obj = PyDict_GetItemString(image_obj, "tint2_color");
        if (!obj)
          throw Exception("Provided image dict contains no 'tint2_color' entry",
                          PyExcType::kValue);
        tint2_color = Python::GetPyVector3f(obj);
      } else {
        texture = Python::GetPyTexture(image_obj);
      }
    }
    if (output_stream) {
      // FIXME: for now we just do bottom messages.
      if (texture == nullptr && !top) {
        output_stream->ScreenMessageBottom(message, color.x, color.y, color.z);
      } else if (top && texture != nullptr && tint_texture != nullptr) {
        if (texture->scene() != context_scene) {
          throw Exception("Texture is not from the current context.",
                          PyExcType::kContext);
        }
        if (tint_texture->scene() != context_scene)
          throw Exception("Tint-texture is not from the current context.",
                          PyExcType::kContext);
        output_stream->ScreenMessageTop(
            message, color.x, color.y, color.z, texture, tint_texture,
            tint_color.x, tint_color.y, tint_color.z, tint2_color.x,
            tint2_color.y, tint2_color.z);
      } else {
        Log(LogLevel::kError, "Unhandled screenmessage output_stream case.");
      }
    }

    // Now display it locally.
    g_graphics->AddScreenMessage(message, color, static_cast<bool>(top),
                                 texture, tint_texture, tint_color,
                                 tint2_color);
  }

  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

auto PyQuit(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {"soft", "back", nullptr};
  int soft = 0;
  int back = 0;
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|ii",
                                   const_cast<char**>(kwlist), &soft, &back)) {
    return nullptr;
  }

  // FIXME this should all just go through platform

  if (g_buildconfig.ostype_ios_tvos()) {
    // This should never be called on iOS
    Log(LogLevel::kError, "Quit called.");
  }

  bool handled = false;

  // A few types get handled specially on android.
  if (g_buildconfig.ostype_android()) {
#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"

    if (!handled && back) {
      // Back-quit simply synthesizes a back press.
      // Note to self: I remember this behaved slightly differently than
      // doing a soft quit but I should remind myself how...
      g_platform->AndroidSynthesizeBackPress();
      handled = true;
    }

#pragma clang diagnostic pop

    if (!handled && soft) {
      // Soft-quit just kills our activity but doesn't run app shutdown.
      // Thus we'll be able to spin back up (reset to the main menu)
      // if the user re-launches us.
      g_platform->AndroidQuitActivity();
      handled = true;
    }
  }
  if (!handled) {
    g_logic->PushShutdownCall(false);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

#if BA_DEBUG_BUILD
auto PyBless(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  ScreenMessage("WOULD BLESS BUILD " + std::to_string(kAppBuildNumber));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}
#endif  // BA_DEBUG_BUILD

auto PyApplyConfig(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;

  // Hmm; python runs in the logic thread; technically we could just run
  // ApplyConfig() immediately (though pushing is probably safer).
  g_logic->PushApplyConfigCall();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyCommitConfig(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* config_obj;
  static const char* kwlist[] = {"config", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &config_obj)) {
    return nullptr;
  }
  if (config_obj == nullptr || !Python::IsPyString(config_obj)) {
    throw Exception("ERROR ON JSON DUMP");
  }
  std::string final_str = Python::GetPyString(config_obj);
  std::string path = g_platform->GetConfigFilePath();
  std::string path_temp = path + ".tmp";
  std::string path_prev = path + ".prev";
  if (explicit_bool(true)) {
    FILE* f_out = g_platform->FOpen(path_temp.c_str(), "wb");
    if (f_out == nullptr) {
      throw Exception("Error opening config file for writing: '" + path_temp
                      + "': " + g_platform->GetErrnoString());
    }

    // Write to temp file.
    size_t result = fwrite(&final_str[0], final_str.size(), 1, f_out);
    if (result != 1) {
      fclose(f_out);
      throw Exception("Error writing config file to '" + path_temp
                      + "': " + g_platform->GetErrnoString());
    }
    fclose(f_out);

    // Now backup any existing config to .prev.
    if (g_platform->FilePathExists(path)) {
      // On windows, rename doesn't overwrite existing files.. need to kill
      // the old explicitly.
      // (hmm; should we just do this everywhere for consistency?)
      if (g_buildconfig.ostype_windows()) {
        if (g_platform->FilePathExists(path_prev)) {
          int result2 = g_platform->Remove(path_prev.c_str());
          if (result2 != 0) {
            throw Exception("Error removing prev config file '" + path_prev
                            + "': " + g_platform->GetErrnoString());
          }
        }
      }
      int result2 = g_platform->Rename(path.c_str(), path_prev.c_str());
      if (result2 != 0) {
        throw Exception("Error backing up config file to '" + path_prev
                        + "': " + g_platform->GetErrnoString());
      }
    }

    // Now move temp into place.
    int result2 = g_platform->Rename(path_temp.c_str(), path.c_str());
    if (result2 != 0) {
      throw Exception("Error renaming temp config file to final '" + path
                      + "': " + g_platform->GetErrnoString());
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyEnv(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_app->is_bootstrapped);

  static PyObject* env_obj = nullptr;

  // Just build this once and recycle it.
  if (env_obj == nullptr) {
    std::string config_path = g_platform->GetConfigFilePath();
    PyObject* is_debug_build_obj;
#if BA_DEBUG_BUILD
    is_debug_build_obj = Py_True;
#else
    is_debug_build_obj = Py_False;
#endif
    PyObject* is_test_build_obj;
#if BA_TEST_BUILD
    is_test_build_obj = Py_True;
#else
    is_test_build_obj = Py_False;
#endif
    bool demo_mode{g_buildconfig.demo_build()};

    const char* ui_scale;
    switch (g_ui->scale()) {
      case UIScale::kLarge:
        ui_scale = "large";
        break;
      case UIScale::kMedium:
        ui_scale = "medium";
        break;
      case UIScale::kSmall:
        ui_scale = "small";
        break;
      default:
        throw Exception();
    }
    // clang-format off
    env_obj = Py_BuildValue(
        "{"
        "si"  // build_number
        "ss"  // config_file_path
        "ss"  // locale
        "ss"  // user_agent_string
        "ss"  // version
        "sO"  // debug_build
        "sO"  // test_build
        "ss"  // python_directory_user
        "ss"  // python_directory_app
        "ss"  // platform
        "ss"  // subplatform
        "ss"  // ui_scale
        "sO"  // on_tv
        "sO"  // vr_mode
        "sO"  // toolbar_test
        "sO"  // demo_mode
        "sO"  // arcade_mode
        "sO"  // iircade_mode
        "si"  // protocol_version
        "sO"  // headless_mode
        "ss"  // python_directory_app_site
        "ss"  // device_name
        "}",
        "build_number", kAppBuildNumber,
        "config_file_path", config_path.c_str(),
        "locale", g_platform->GetLocale().c_str(),
        "user_agent_string", g_app->user_agent_string.c_str(),
        "version", kAppVersion,
        "debug_build", is_debug_build_obj,
        "test_build", is_test_build_obj,
        "python_directory_user", g_platform->GetUserPythonDirectory().c_str(),
        "python_directory_app", g_platform->GetAppPythonDirectory().c_str(),
        "platform", g_platform->GetPlatformName().c_str(),
        "subplatform", g_platform->GetSubplatformName().c_str(),
        "ui_scale", ui_scale,
        "on_tv", g_platform->IsRunningOnTV() ? Py_True : Py_False,
        "vr_mode", IsVRMode() ? Py_True : Py_False,
        "toolbar_test", BA_TOOLBAR_TEST ? Py_True : Py_False,
        "demo_mode", demo_mode ? Py_True : Py_False,
        "arcade_mode", g_buildconfig.arcade_build() ? Py_True : Py_False,
        "iircade_mode", g_buildconfig.iircade_build() ? Py_True: Py_False,
        "protocol_version", kProtocolVersion,
        "headless_mode", HeadlessMode() ? Py_True : Py_False,
        "python_directory_app_site",
        g_platform->GetSitePythonDirectory().c_str(),
        "device_name",
        g_platform->GetDeviceName().c_str());
    // clang-format on
  }
  Py_INCREF(env_obj);
  g_python->set_env_obj(env_obj);
  return env_obj;
  BA_PYTHON_CATCH;
}

auto PySetStressTesting(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  int testing;
  int player_count;
  if (!PyArg_ParseTuple(args, "pi", &testing, &player_count)) {
    return nullptr;
  }
  g_app_flavor->PushSetStressTestingCall(static_cast<bool>(testing),
                                         player_count);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyDisplayLog(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {"name", "level", "message", nullptr};
  const char* name;
  const char* levelstr;
  const char* message;
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sss",
                                   const_cast<char**>(kwlist), &name, &levelstr,
                                   &message)) {
    return nullptr;
  }

  // Calc LogLevel enum val from their string val.
  LogLevel level;
  if (levelstr == std::string("DEBUG")) {
    level = LogLevel::kDebug;
  } else if (levelstr == std::string("INFO")) {
    level = LogLevel::kInfo;
  } else if (levelstr == std::string("WARNING")) {
    level = LogLevel::kWarning;
  } else if (levelstr == std::string("ERROR")) {
    level = LogLevel::kError;
  } else if (levelstr == std::string("CRITICAL")) {
    level = LogLevel::kCritical;
  } else {
    // Assume we should avoid Log() calls here since it could infinite loop.
    fprintf(stderr, "Invalid log level to display_log(): %s\n", levelstr);
    level = LogLevel::kInfo;
  }
  Logging::DisplayLog(name, level, message);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyV1CloudLog(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* message;
  static const char* kwlist[] = {"message", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &message)) {
    return nullptr;
  }
  Logging::V1CloudLog(message);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyTimeFormatCheck(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {"time_format", "length", nullptr};
  PyObject* time_format_obj;
  PyObject* length_obj;
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO",
                                   const_cast<char**>(kwlist), &time_format_obj,
                                   &length_obj)) {
    return nullptr;
  }
  auto time_format = Python::GetPyEnum_TimeFormat(time_format_obj);

  g_python->TimeFormatCheck(time_format, length_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonMethodsApp::GetMethods() -> std::vector<PyMethodDef> {
  return {
    {"appname", (PyCFunction)PyAppName, METH_NOARGS,
     "appname() -> str\n"
     "\n"
     "(internal)\n"},
        {"appnameupper", (PyCFunction)PyAppNameUpper, METH_NOARGS,
         "appnameupper() -> str\n"
         "\n"
         "(internal)\n"
         "\n"
         "Return whether this build of the game can display full unicode such "
         "as\n"
         "Emoji, Asian languages, etc.\n"},
        {"is_xcode_build", (PyCFunction)PyIsXCodeBuild, METH_NOARGS,
         "is_xcode_build() -> bool\n"
         "\n"
         "(internal)\n"},
        {"can_display_full_unicode", (PyCFunction)PyCanDisplayFullUnicode,
         METH_NOARGS,
         "can_display_full_unicode() -> bool\n"
         "\n"
         "(internal)\n"},
        {"time_format_check", (PyCFunction)PyTimeFormatCheck,
         METH_VARARGS | METH_KEYWORDS,
         "time_format_check(time_format: ba.TimeFormat, length: float | int)\n"
         "  -> None\n"
         "\n"
         "(internal)\n"
         "\n"
         "Logs suspicious time values for timers or animate calls.\n"
         "\n"
         "(for helping with the transition from milliseconds-based time calls\n"
         "to seconds-based ones)"},

        {"display_log", (PyCFunction)PyDisplayLog, METH_VARARGS | METH_KEYWORDS,
         "display_log(name: str, level: str, message: str) -> None\n"
         "\n"
         "(internal)\n"
         "\n"
         "Sends a log message to the in-game console and any per-platform\n"
         "log destinations (Android log, etc.). This generally is not called\n"
         "directly and should instead be fed Python logging output."},

        {"v1_cloud_log", (PyCFunction)PyV1CloudLog,
         METH_VARARGS | METH_KEYWORDS,
         "v1_cloud_log(message: str) -> None\n"
         "\n"
         "(internal)\n"
         "\n"
         "Push messages to the old v1 cloud log."},

        {"set_stress_testing", PySetStressTesting, METH_VARARGS,
         "set_stress_testing(testing: bool, player_count: int) -> None\n"
         "\n"
         "(internal)"},

        {"env", (PyCFunction)PyEnv, METH_NOARGS,
         "env() -> dict\n"
         "\n"
         "(internal)\n"
         "\n"
         "Returns a dict containing general info about the operating "
         "environment\n"
         "such as version, platform, etc.\n"
         "This info is now exposed through ba.App; refer to those docs for\n"
         "info on specific elements."},

        {"commit_config", (PyCFunction)PyCommitConfig,
         METH_VARARGS | METH_KEYWORDS,
         "commit_config(config: str) -> None\n"
         "\n"
         "(internal)"},

        {"apply_config", PyApplyConfig, METH_VARARGS,
         "apply_config() -> None\n"
         "\n"
         "(internal)"},

#if BA_DEBUG_BUILD
        {"bless", (PyCFunction)PyBless, METH_VARARGS | METH_KEYWORDS,
         "bless() -> None\n"
         "\n"
         "(internal)"},
#endif

        {"quit", (PyCFunction)PyQuit, METH_VARARGS | METH_KEYWORDS,
         "quit(soft: bool = False, back: bool = False) -> None\n"
         "\n"
         "Quit the game.\n"
         "\n"
         "Category: **General Utility Functions**\n"
         "\n"
         "On systems like android, 'soft' will end the activity but keep the\n"
         "app running."},

        {"screenmessage", (PyCFunction)PyScreenMessage,
         METH_VARARGS | METH_KEYWORDS,
         "screenmessage(message: str | ba.Lstr,\n"
         "  color: Sequence[float] | None = None,\n"
         "  top: bool = False,\n"
         "  image: dict[str, Any] | None = None,\n"
         "  log: bool = False,\n"
         "  clients: Sequence[int] | None = None,\n"
         "  transient: bool = False)"
         " -> None\n"
         "\n"
         "Print a message to the local client's screen, in a given color.\n"
         "\n"
         "Category: **General Utility Functions**\n"
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
         "Currently the 'clients' option only works for transient messages."},

        {"timer", (PyCFunction)PyTimer, METH_VARARGS | METH_KEYWORDS,
         "timer(time: float, call: Callable[[], Any], repeat: bool = False,\n"
         "  timetype: ba.TimeType = TimeType.SIM,\n"
         "  timeformat: ba.TimeFormat = TimeFormat.SECONDS,\n"
         "  suppress_format_warning: bool = False)\n"
         " -> None\n"
         "\n"
         "Schedule a call to run at a later point in time.\n"
         "\n"
         "Category: **General Utility Functions**\n"
         "\n"
         "This function adds a timer to the current ba.Context.\n"
         "This timer cannot be canceled or modified once created. If you\n"
         " require the ability to do so, use the ba.Timer class instead.\n"
         "\n"
         "##### Arguments\n"
         "###### time (float)\n"
         "> Length of time (in seconds by default) that the timer will wait\n"
         "before firing. Note that the actual delay experienced may vary\n "
         "depending on the timetype. (see below)\n"
         "\n"
         "###### call (Callable[[], Any])\n"
         "> A callable Python object. Note that the timer will retain a\n"
         "strong reference to the callable for as long as it exists, so you\n"
         "may want to look into concepts such as ba.WeakCall if that is not\n"
         "desired.\n"
         "\n"
         "###### repeat (bool)\n"
         "> If True, the timer will fire repeatedly, with each successive\n"
         "firing having the same delay as the first.\n"
         "\n"
         "###### timetype (ba.TimeType)\n"
         "> Can be either `SIM`, `BASE`, or `REAL`. It defaults to\n"
         "`SIM`.\n"
         "\n"
         "###### timeformat (ba.TimeFormat)\n"
         "> Defaults to seconds but can also be milliseconds.\n"
         "\n"
         "- SIM time maps to local simulation time in ba.Activity or "
         "ba.Session\n"
         "Contexts. This means that it may progress slower in slow-motion "
         "play\n"
         "modes, stop when the game is paused, etc.  This time type is not\n"
         "available in UI contexts.\n"
         "- BASE time is also linked to gameplay in ba.Activity or ba.Session\n"
         "Contexts, but it progresses at a constant rate regardless of\n "
         "slow-motion states or pausing.  It can, however, slow down or stop\n"
         "in certain cases such as network outages or game slowdowns due to\n"
         "cpu load. Like 'sim' time, this is unavailable in UI contexts.\n"
         "- REAL time always maps to actual clock time with a bit of "
         "filtering\n"
         "added, regardless of Context. (The filtering prevents it from going\n"
         "backwards or jumping forward by large amounts due to the app being\n"
         "backgrounded, system time changing, etc.)\n"
         "Real time timers are currently only available in the UI context.\n"
         "\n"
         "##### Examples\n"
         "Print some stuff through time:\n"
         ">>> ba.screenmessage('hello from now!')\n"
         ">>> ba.timer(1.0, ba.Call(ba.screenmessage, 'hello from the "
         "future!'))\n"
         ">>> ba.timer(2.0, ba.Call(ba.screenmessage,\n"
         "...                       'hello from the future 2!'))\n"},

        {"time", (PyCFunction)PyTime, METH_VARARGS | METH_KEYWORDS,
         "time(timetype: ba.TimeType = TimeType.SIM,\n"
         "  timeformat: ba.TimeFormat = TimeFormat.SECONDS)\n"
         "  -> <varies>\n"
         "\n"
         "Return the current time.\n"
         "\n"
         "Category: **General Utility Functions**\n"
         "\n"
         "The time returned depends on the current ba.Context and timetype.\n"
         "\n"
         "timetype can be either SIM, BASE, or REAL. It defaults to\n"
         "SIM. Types are explained below:\n"
         "\n"
         "- SIM time maps to local simulation time in ba.Activity or "
         "ba.Session\n"
         "Contexts. This means that it may progress slower in slow-motion "
         "play\n"
         "modes, stop when the game is paused, etc.  This time type is not\n"
         "available in UI contexts.\n"
         "- BASE time is also linked to gameplay in ba.Activity or ba.Session\n"
         "Contexts, but it progresses at a constant rate regardless of\n "
         "slow-motion states or pausing.  It can, however, slow down or stop\n"
         "in certain cases such as network outages or game slowdowns due to\n"
         "cpu load. Like 'sim' time, this is unavailable in UI contexts.\n"
         "- REAL time always maps to actual clock time with a bit of "
         "filtering\n"
         "added, regardless of Context. (The filtering prevents it from going\n"
         "backwards or jumping forward by large amounts due to the app being\n"
         "backgrounded, system time changing, etc.)\n"
         "Real time timers are currently only available in the UI context.\n"
         "\n"
         "The 'timeformat' arg defaults to SECONDS which returns float "
         "seconds,\n"
         "but it can also be MILLISECONDS to return integer milliseconds.\n"
         "\n"
         "Note: If you need pure unfiltered clock time, just use the standard\n"
         "Python functions such as time.time()."},

        {"pushcall", (PyCFunction)PyPushCall, METH_VARARGS | METH_KEYWORDS,
         "pushcall(call: Callable, from_other_thread: bool = False,\n"
         "     suppress_other_thread_warning: bool = False,\n"
         "     other_thread_use_fg_context: bool = False,\n"
         "     raw: bool = False) -> None\n"
         "\n"
         "Push a call to the logic event-loop.\n"
         "Category: **General Utility Functions**\n"
         "\n"
         "This call expects to be used in the logic thread, and will "
         "automatically\n"
         "save and restore the ba.Context to behave seamlessly.\n"
         "\n"
         "If you want to push a call from outside of the logic thread,\n"
         "however, you can pass 'from_other_thread' as True. In this case\n"
         "the call will always run in the UI context on the logic thread\n"
         "or whichever context is in the foreground if\n"
         "other_thread_use_fg_context is True.\n"
         "Passing raw=True will disable thread checks and context"
         " sets/restores."},
        {"getactivity", (PyCFunction)PyGetActivity,
         METH_VARARGS | METH_KEYWORDS,
         "getactivity(doraise: bool = True) -> <varies>\n"
         "\n"
         "Return the current ba.Activity instance.\n"
         "\n"
         "Category: **Gameplay Functions**\n"
         "\n"
         "Note that this is based on context; thus code run in a timer "
         "generated\n"
         "in Activity 'foo' will properly return 'foo' here, even if another\n"
         "Activity has since been created or is transitioning in.\n"
         "If there is no current Activity, raises a ba.ActivityNotFoundError.\n"
         "If doraise is False, None will be returned instead in that case."},

        {"newactivity", (PyCFunction)PyNewActivity,
         METH_VARARGS | METH_KEYWORDS,
         "newactivity(activity_type: type[ba.Activity],\n"
         "  settings: dict | None = None) -> ba.Activity\n"
         "\n"
         "Instantiates a ba.Activity given a type object.\n"
         "\n"
         "Category: **General Utility Functions**\n"
         "\n"
         "Activities require special setup and thus cannot be directly\n"
         "instantiated; you must go through this function."},

        {"get_foreground_host_session", (PyCFunction)PyGetForegroundHostSession,
         METH_VARARGS | METH_KEYWORDS,
         "get_foreground_host_session() -> ba.Session | None\n"
         "\n"
         "(internal)\n"
         "\n"
         "Return the ba.Session currently being displayed, or None if there "
         "is\n"
         "none."},

        {"register_activity", (PyCFunction)PyRegisterActivity,
         METH_VARARGS | METH_KEYWORDS,
         "register_activity(activity: ba.Activity) -> ActivityData\n"
         "\n"
         "(internal)"},

        {"register_session", (PyCFunction)PyRegisterSession,
         METH_VARARGS | METH_KEYWORDS,
         "register_session(session: ba.Session) -> SessionData\n"
         "\n"
         "(internal)"},

        {"is_in_replay", (PyCFunction)PyIsInReplay,
         METH_VARARGS | METH_KEYWORDS,
         "is_in_replay() -> bool\n"
         "\n"
         "(internal)"},

        {"app_instance_uuid", (PyCFunction)PyAppInstanceUUID,
         METH_VARARGS | METH_KEYWORDS,
         "app_instance_uuid() -> str\n"
         "\n"
         "(internal)"},

        {"user_ran_commands", (PyCFunction)PyUserRanCommands,
         METH_VARARGS | METH_KEYWORDS,
         "user_ran_commands() -> None\n"
         "\n"
         "(internal)"},

        {"new_replay_session", (PyCFunction)PyNewReplaySession,
         METH_VARARGS | METH_KEYWORDS,
         "new_replay_session(file_name: str) -> None\n"
         "\n"
         "(internal)"},

        {"new_host_session", (PyCFunction)PyNewHostSession,
         METH_VARARGS | METH_KEYWORDS,
         "new_host_session(sessiontype: type[ba.Session],\n"
         "  benchmark_type: str | None = None) -> None\n"
         "\n"
         "(internal)"},

        {"getsession", (PyCFunction)PyGetSession, METH_VARARGS | METH_KEYWORDS,
         "getsession(doraise: bool = True) -> <varies>\n"
         "\n"
         "Category: **Gameplay Functions**\n"
         "\n"
         "Returns the current ba.Session instance.\n"
         "Note that this is based on context; thus code being run in the UI\n"
         "context will return the UI context here even if a game Session also\n"
         "exists, etc. If there is no current Session, an Exception is raised, "
         "or\n"
         "if doraise is False then None is returned instead."},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
