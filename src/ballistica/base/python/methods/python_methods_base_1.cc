// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_base_1.h"

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/empty_app_mode.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/support/python_context_call_runnable.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/logging.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

// Python does lots of signed bitwise stuff; turn off those warnings here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

// --------------------------------- appname -----------------------------------

static auto PyAppName(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // This will get subbed out by standard filtering.
  return PyUnicode_FromString("ballisticakit");
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppNameDef = {
    "appname",               // name
    (PyCFunction)PyAppName,  // method
    METH_NOARGS,             // flags

    "appname() -> str\n"
    "\n"
    "(internal)\n",
};

// ------------------------------ app_is_active --------------------------------

static auto PyAppIsActive(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // Note: we're limiting this to the logic thread and using the logic
  // thread's version of app-active here. If we ever need the main thread's
  // version we'll have to do something different.
  BA_PRECONDITION(g_base->InLogicThread());
  if (g_base->logic->app_active()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppIsActiveDef = {
    "app_is_active",             // name
    (PyCFunction)PyAppIsActive,  // method
    METH_NOARGS,                 // flags

    "app_is_active() -> bool\n"
    "\n"
    "(internal)\n",
};
// --------------------------------- run_app -----------------------------------

static auto PyRunApp(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  assert(g_base);
  g_base->RunAppToCompletion();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyRunAppDef = {
    "run_app",              // name
    (PyCFunction)PyRunApp,  // method
    METH_NOARGS,            // flags

    "run_app() -> None\n"
    "\n"
    "Run the app to completion.\n"
    "\n"
    "Note that this only works on platforms/builds where ballistica\n"
    "manages its own event loop.",
};

// --------------------------- complete_shutdown -------------------------------

static auto PyCompleteShutdown(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  assert(g_base);
  g_base->logic->CompleteShutdown();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCompleteShutdownDef = {
    "complete_shutdown",              // name
    (PyCFunction)PyCompleteShutdown,  // method
    METH_NOARGS,                      // flags

    "complete_shutdown() -> None\n"
    "\n"
    "Complete the shutdown process, triggering the app to exit.\n",
};

// -------------------------------- appnameupper -------------------------------

static auto PyAppNameUpper(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // This will get subbed out by standard filtering.
  return PyUnicode_FromString("BallisticaKit");
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppNameUpperDef = {
    "appnameupper",               // name
    (PyCFunction)PyAppNameUpper,  // method
    METH_NOARGS,                  // flags

    "appnameupper() -> str\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return whether this build of the game can display full unicode such "
    "as\n"
    "Emoji, Asian languages, etc.",
};

// ---------------------------- is_xcode_build ---------------------------------

static auto PyIsXCodeBuild(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.xcode_build()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIsXCodeBuildDef = {
    "is_xcode_build",             // name
    (PyCFunction)PyIsXCodeBuild,  // method
    METH_NOARGS,                  // flags

    "is_xcode_build() -> bool\n"
    "\n"
    "(internal)\n",
};

// ----------------------- can_display_full_unicode ----------------------------

static auto PyCanDisplayFullUnicode(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_buildconfig.enable_os_font_rendering()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCanDisplayFullUnicodeDef = {
    "can_display_full_unicode",            // name
    (PyCFunction)PyCanDisplayFullUnicode,  // method
    METH_NOARGS,                           // flags

    "can_display_full_unicode() -> bool\n"
    "\n"
    "(internal)",
};

// -------------------------- app_instance_uuid --------------------------------

static auto PyAppInstanceUUID(PyObject* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(g_base->GetAppInstanceUUID().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppInstanceUUIDDef = {
    "app_instance_uuid",             // name
    (PyCFunction)PyAppInstanceUUID,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "app_instance_uuid() -> str\n"
    "\n"
    "(internal)",
};

// --------------------------- user_ran_commands -------------------------------

static auto PyUserRanCommands(PyObject* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_core->user_ran_commands = true;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUserRanCommandsDef = {
    "user_ran_commands",             // name
    (PyCFunction)PyUserRanCommands,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "user_ran_commands() -> None\n"
    "\n"
    "(internal)",
};

// -------------------------------- pushcall ----------------------------------

static auto PyPushCall(PyObject* self, PyObject* args,
                       PyObject* keywds) -> PyObject* {
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

  if (!g_base->logic->event_loop()) {
    throw Exception("pushcall cannot be used before start-app is called.");
  }

  // 'raw' mode does no thread checking and no context saves/restores.
  if (raw) {
    assert(Python::HaveGIL());
    Py_INCREF(call_obj);
    g_base->logic->event_loop()->PushCall([call_obj] {
      assert(g_base->InLogicThread());
      PythonRef(call_obj, PythonRef::kSteal).Call();
    });
  } else if (from_other_thread) {
    // Warn the user not to use this from the logic thread since it doesnt
    // save/restore context.
    if (!suppress_warning && g_base->InLogicThread()) {
      Log(LogLevel::kWarning,
          "babase.pushcall() called from the logic thread with "
          "from_other_thread set to true (call "
              + Python::ObjToString(call_obj) + " at "
              + Python::GetPythonFileLocation()
              + "). That arg should only be used from other threads.");
    }

    assert(Python::HaveGIL());

    // This can get called from other threads so we can't construct
    // Objects and things here or we'll trip our thread-checks. Instead we
    // just increment the python object's refcount and pass it along raw;
    // the logic thread decrements it when its done.
    Py_INCREF(call_obj);

    // Ship it off to the logic thread to get run.
    g_base->logic->event_loop()->PushCall(
        [call_obj, other_thread_use_fg_context] {
          assert(g_base->InLogicThread());

          // Run this with an empty context by default, or foreground if
          // requested.
          ScopedSetContext ssc(other_thread_use_fg_context
                                   ? g_base->app_mode()->GetForegroundContext()
                                   : ContextRef(nullptr));

          PythonRef(call_obj, PythonRef::kSteal).Call();
        });

  } else {
    if (!g_base->InLogicThread()) {
      throw Exception("You must use from_other_thread mode.");
    }
    Object::New<PythonContextCall>(call_obj)->Schedule();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPushCallDef = {
    "pushcall",                    // name
    (PyCFunction)PyPushCall,       // method
    METH_VARARGS | METH_KEYWORDS,  // flags

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
    "save and restore the babase.Context to behave seamlessly.\n"
    "\n"
    "If you want to push a call from outside of the logic thread,\n"
    "however, you can pass 'from_other_thread' as True. In this case\n"
    "the call will always run in the UI context_ref on the logic thread\n"
    "or whichever context_ref is in the foreground if\n"
    "other_thread_use_fg_context is True.\n"
    "Passing raw=True will disable thread checks and context_ref"
    " sets/restores."};

// ------------------------------ apptime --------------------------------------

static auto PyAppTime(PyObject* self, PyObject* args,
                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyFloat_FromDouble(
      0.001 * static_cast<double>(g_core->GetAppTimeMillisecs()));
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppTimeDef = {
    "apptime",                     // name
    (PyCFunction)PyAppTime,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "apptime() -> babase.AppTime\n"
    "\n"
    "Return the current app-time in seconds.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "App-time is a monotonic time value; it starts at 0.0 when the app\n"
    "launches and will never jump by large amounts or go backwards, even if\n"
    "the system time changes. Its progression will pause when the app is in\n"
    "a suspended state.\n"
    "\n"
    "Note that the AppTime returned here is simply float; it just has a\n"
    "unique type in the type-checker's eyes to help prevent it from being\n"
    "accidentally used with time functionality expecting other time types.",
};

// ------------------------------ apptimer -------------------------------------

static auto PyAppTimer(PyObject* self, PyObject* args,
                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  double length;
  PyObject* call_obj;
  static const char* kwlist[] = {"time", "call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "dO", const_cast<char**>(kwlist), &length, &call_obj)) {
    return nullptr;
  }
  BasePython::EnsureContextAllowsDefaultTimerTypes();
  if (length < 0) {
    throw Exception("Timer length cannot be < 0.", PyExcType::kValue);
  }
  g_base->logic->NewAppTimer(
      static_cast<microsecs_t>(length * 1000000.0), false,
      Object::New<Runnable, PythonContextCallRunnable>(call_obj).Get());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyAppTimerDef = {
    "apptimer",                    // name
    (PyCFunction)PyAppTimer,       // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "apptimer(time: float, call: Callable[[], Any]) -> None\n"
    "\n"
    "Schedule a callable object to run based on app-time.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "This function creates a one-off timer which cannot be canceled or\n"
    "modified once created. If you require the ability to do so, or need\n"
    "a repeating timer, use the babase.AppTimer class instead.\n"
    "\n"
    "##### Arguments\n"
    "###### time (float)\n"
    "> Length of time in seconds that the timer will wait before firing.\n"
    "\n"
    "###### call (Callable[[], Any])\n"
    "> A callable Python object. Note that the timer will retain a\n"
    "strong reference to the callable for as long as the timer exists, so you\n"
    "may want to look into concepts such as babase.WeakCall if that is not\n"
    "desired.\n"
    "\n"
    "##### Examples\n"
    "Print some stuff through time:\n"
    ">>> babase.screenmessage('hello from now!')\n"
    ">>> babase.apptimer(1.0, babase.Call(babase.screenmessage,\n"
    "                          'hello from the future!'))\n"
    ">>> babase.apptimer(2.0, babase.Call(babase.screenmessage,\n"
    "...                       'hello from the future 2!'))\n",
};

// --------------------------- displaytime -------------------------------------

static auto PyDisplayTime(PyObject* self, PyObject* args,
                          PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyFloat_FromDouble(g_base->logic->display_time());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDisplayTimeDef = {
    "displaytime",                 // name
    (PyCFunction)PyDisplayTime,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "displaytime() -> babase.DisplayTime\n"
    "\n"
    "Return the current display-time in seconds.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "Display-time is a time value intended to be used for animation and other\n"
    "visual purposes. It will generally increment by a consistent amount each\n"
    "frame. It will pass at an overall similar rate to AppTime, but trades\n"
    "accuracy for smoothness.\n"
    "\n"
    "Note that the value returned here is simply a float; it just has a\n"
    "unique type in the type-checker's eyes to help prevent it from being\n"
    "accidentally used with time functionality expecting other time types.",
};

// ---------------------------- displaytimer -----------------------------------

static auto PyDisplayTimer(PyObject* self, PyObject* args,
                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  double length;
  PyObject* call_obj;
  static const char* kwlist[] = {"time", "call", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "dO", const_cast<char**>(kwlist), &length, &call_obj)) {
    return nullptr;
  }
  BasePython::EnsureContextAllowsDefaultTimerTypes();
  if (length < 0) {
    throw Exception("Timer length cannot be < 0.", PyExcType::kValue);
  }
  g_base->logic->NewDisplayTimer(
      static_cast<microsecs_t>(length * 1000000.0), false,
      Object::New<Runnable, PythonContextCallRunnable>(call_obj).Get());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDisplayTimerDef = {
    "displaytimer",                // name
    (PyCFunction)PyDisplayTimer,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "displaytimer(time: float, call: Callable[[], Any]) -> None\n"
    "\n"
    "Schedule a callable object to run based on display-time.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "This function creates a one-off timer which cannot be canceled or\n"
    "modified once created. If you require the ability to do so, or need\n"
    "a repeating timer, use the babase.DisplayTimer class instead.\n"
    "\n"
    "Display-time is a time value intended to be used for animation and other\n"
    "visual purposes. It will generally increment by a consistent amount each\n"
    "frame. It will pass at an overall similar rate to AppTime, but trades\n"
    "accuracy for smoothness.\n"
    "\n"
    "##### Arguments\n"
    "###### time (float)\n"
    "> Length of time in seconds that the timer will wait before firing.\n"
    "\n"
    "###### call (Callable[[], Any])\n"
    "> A callable Python object. Note that the timer will retain a\n"
    "strong reference to the callable for as long as the timer exists, so you\n"
    "may want to look into concepts such as babase.WeakCall if that is not\n"
    "desired.\n"
    "\n"
    "##### Examples\n"
    "Print some stuff through time:\n"
    ">>> babase.screenmessage('hello from now!')\n"
    ">>> babase.displaytimer(1.0, babase.Call(babase.screenmessage,\n"
    "...                       'hello from the future!'))\n"
    ">>> babase.displaytimer(2.0, babase.Call(babase.screenmessage,\n"
    "...                       'hello from the future 2!'))\n",
};

// ----------------------------------- quit ------------------------------------

static auto PyQuit(PyObject* self, PyObject* args,
                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->IsAppStarted());

  static const char* kwlist[] = {"confirm", "quit_type", nullptr};
  QuitType quit_type = QuitType::kSoft;
  PyObject* quit_type_obj{Py_None};
  int confirm{};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|pO",
                                   const_cast<char**>(kwlist), &confirm,
                                   &quit_type_obj)) {
    return nullptr;
  }
  if (quit_type_obj != Py_None) {
    quit_type = BasePython::GetPyEnum_QuitType(quit_type_obj);
  }

  g_base->QuitApp(confirm, quit_type);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyQuitDef = {
    "quit",                        // name
    (PyCFunction)PyQuit,           // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "quit(confirm: bool = False,\n"
    "          quit_type: babase.QuitType | None = None\n"
    ") -> None\n"
    "\n"
    "Quit the app.\n"
    "\n"
    "Category: **General Utility Functions**\n"
    "\n"
    "If 'confirm' is True, a confirm dialog will be presented if conditions\n"
    "allow; otherwise the quit will still be immediate.\n"
    "See docs for babase.QuitType for explanations of the optional\n"
    "'quit_type' arg."};

// ----------------------------- apply_config ----------------------------------

static auto PyDoApplyAppConfig(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  g_base->logic->DoApplyAppConfig();

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDoApplyAppConfigDef = {
    "do_apply_app_config",  // name
    PyDoApplyAppConfig,     // method
    METH_VARARGS,           // flags

    "do_apply_app_config() -> None\n"
    "\n"
    "(internal)",
};

// ----------------------------- commit_config ---------------------------------

static auto PyCommitConfig(PyObject* self, PyObject* args,
                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* config_obj;
  static const char* kwlist[] = {"config", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &config_obj)) {
    return nullptr;
  }
  if (config_obj == nullptr || !g_base->python->IsPyLString(config_obj)) {
    throw Exception("ERROR ON JSON DUMP");
  }
  std::string final_str = g_base->python->GetPyLString(config_obj);
  std::string path = g_core->platform->GetConfigFilePath();
  std::string path_temp = path + ".tmp";
  std::string path_prev = path + ".prev";
  if (explicit_bool(true)) {
    FILE* f_out = g_core->platform->FOpen(path_temp.c_str(), "wb");
    if (f_out == nullptr) {
      throw Exception("Error opening config file for writing: '" + path_temp
                      + "': " + g_core->platform->GetErrnoString());
    }

    // Write to temp file.
    size_t result = fwrite(&final_str[0], final_str.size(), 1, f_out);
    if (result != 1) {
      fclose(f_out);
      throw Exception("Error writing config file to '" + path_temp
                      + "': " + g_core->platform->GetErrnoString());
    }
    fclose(f_out);

    // Now move any existing config to .prev.
    if (g_core->platform->FilePathExists(path)) {
      // On windows, rename doesn't overwrite existing files.. need to kill
      // the old explicitly.
      // (hmm; should we just do this everywhere for consistency?)
      if (g_buildconfig.ostype_windows()) {
        if (g_core->platform->FilePathExists(path_prev)) {
          int result2 = g_core->platform->Remove(path_prev.c_str());
          if (result2 != 0) {
            throw Exception("Error removing prev config file '" + path_prev
                            + "': " + g_core->platform->GetErrnoString());
          }
        }
      }
      int result2 = g_core->platform->Rename(path.c_str(), path_prev.c_str());
      if (result2 != 0) {
        throw Exception("Error backing up config file to '" + path_prev
                        + "': " + g_core->platform->GetErrnoString());
      }
    }

    // Now move temp into place.
    int result2 = g_core->platform->Rename(path_temp.c_str(), path.c_str());
    if (result2 != 0) {
      throw Exception("Error renaming temp config file to final '" + path
                      + "': " + g_core->platform->GetErrnoString());
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyCommitConfigDef = {
    "commit_config",               // name
    (PyCFunction)PyCommitConfig,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "commit_config(config: str) -> None\n"
    "\n"
    "(internal)",
};

// ------------------------------- pre_env -------------------------------------

static auto PyPreEnv(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  // This version only include a bare minimum of values but can be called
  // before bootstrapping is complete.

  // Just build this once and recycle it.
  if (!g_base->python->objs().Exists(BasePython::ObjID::kPreEnv)) {
    // clang-format off
    PyObject* env = Py_BuildValue(
        "{"
        "si"  // build_number
        "sO"  // debug_build
        "sO"  // test_build
        "}",
        "build_number", kEngineBuildNumber,
        "debug_build", g_buildconfig.debug_build() ? Py_True : Py_False,
        "test_build", g_buildconfig.test_build() ? Py_True : Py_False);
    // clang-format on
    g_base->python->StorePreEnv(env);
  }
  return g_base->python->objs().Get(BasePython::ObjID::kPreEnv).NewRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyPreEnvDef = {
    "pre_env",              // name
    (PyCFunction)PyPreEnv,  // method
    METH_NOARGS,            // flags

    "pre_env() -> dict\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns a dict containing general info about the operating "
    "environment\n"
    "such as version, platform, etc.\n"
    "This info is now exposed through babase.App; refer to those docs for\n"
    "info on specific elements."};

// --------------------------------- env ---------------------------------------

static auto PyEnv(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_core);
  assert(g_base);

  // Just build this once and recycle it.
  if (!g_base->python->objs().Exists(BasePython::ObjID::kEnv)) {
    std::optional<std::string> user_py_dir = g_core->GetUserPythonDirectory();
    std::optional<std::string> app_py_dir = g_core->GetAppPythonDirectory();
    std::optional<std::string> site_py_dir = g_core->GetSitePythonDirectory();

    // clang-format off
    PyObject* env = Py_BuildValue(
        "{"
        "si"  // build_number
        "ss"  // config_file_path
        "ss"  // locale
        "ss"  // legacy_user_agent_string
        "ss"  // version
        "sO"  // debug_build
        "sO"  // test_build
        "sO"  // python_directory_user
        "sO"  // python_directory_app
        "ss"  // platform
        "ss"  // subplatform
        "sO"  // on_tv
        "sO"  // vr_mode
        "sO"  // demo_mode
        "sO"  // arcade_mode
        "sO"  // headless_mode
        "sO"  // python_directory_app_site
        "ss"  // device_name
        "ss"  // data_directory
        "}",
        "build_number", kEngineBuildNumber,
        "config_file_path", g_core->platform->GetConfigFilePath().c_str(),
        "locale", g_core->platform->GetLocale().c_str(),
        "legacy_user_agent_string", g_core->legacy_user_agent_string().c_str(),
        "version", kEngineVersion,
        "debug_build", g_buildconfig.debug_build() ? Py_True : Py_False,
        "test_build", g_buildconfig.test_build() ? Py_True : Py_False,
        "python_directory_user",
          user_py_dir ? *PythonRef::FromString(*user_py_dir) : Py_None,
        "python_directory_app",
          app_py_dir ? *PythonRef::FromString(*app_py_dir) : Py_None,
        "platform", g_core->platform->GetPlatformName().c_str(),
        "subplatform", g_core->platform->GetSubplatformName().c_str(),
        "on_tv", g_core->platform->IsRunningOnTV() ? Py_True : Py_False,
        "vr_mode", g_core->vr_mode() ? Py_True : Py_False,
        "demo_mode", g_buildconfig.demo_build() ? Py_True : Py_False,
        "arcade_mode", g_buildconfig.arcade_build() ? Py_True : Py_False,
        "headless_mode", g_core->HeadlessMode() ? Py_True : Py_False,
        "python_directory_app_site",
          site_py_dir ? *PythonRef::FromString(*site_py_dir) : Py_None,
        "device_name",
        g_core->platform->GetDeviceName().c_str(),
        "data_directory",
        g_core->GetDataDirectory().c_str());
    // clang-format on
    g_base->python->StoreEnv(env);
  }
  return g_base->python->objs().Get(BasePython::ObjID::kEnv).NewRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEnvDef = {
    "env",               // name
    (PyCFunction)PyEnv,  // method
    METH_NOARGS,         // flags

    "env() -> dict\n"
    "\n"
    "(internal)\n"
    "\n"
    "Returns a dict containing general info about the operating "
    "environment\n"
    "such as version, platform, etc.\n"
    "This info is now exposed through babase.App; refer to those docs for\n"
    "info on specific elements."};

// -------------------------------- emit_log -----------------------------------

static auto PyEmitLog(PyObject* self, PyObject* args,
                      PyObject* keywds) -> PyObject* {
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
    fprintf(stderr, "Invalid log level to emit_log(): %s\n", levelstr);
    level = LogLevel::kInfo;
  }
  Logging::EmitLog(name, level, message);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEmitLogDef = {
    "emit_log",                    // name
    (PyCFunction)PyEmitLog,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "emit_log(name: str, level: str, message: str) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Sends a log message to the in-app console and any per-platform\n"
    "log destinations (Android log, etc.). This generally is not called\n"
    "directly and should instead be fed Python logging output.",
};

// ------------------------------ lifecyclelog ---------------------------------

static auto PyLifecycleLog(PyObject* self, PyObject* args,
                           PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {"message", nullptr};
  const char* message;
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &message)) {
    return nullptr;
  }

  g_core->LifecycleLog(message);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyLifecycleLogDef = {
    "lifecyclelog",                // name
    (PyCFunction)PyLifecycleLog,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "lifecyclelog(message: str) -> None\n"
    "\n"
    "(internal)",
};

// ----------------------------- v1_cloud_log ----------------------------------

static auto PyV1CloudLog(PyObject* self, PyObject* args,
                         PyObject* keywds) -> PyObject* {
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

static PyMethodDef PyV1CloudLogDef = {
    "v1_cloud_log",                // name
    (PyCFunction)PyV1CloudLog,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "v1_cloud_log(message: str) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Push messages to the old v1 cloud log.",
};

// --------------------------- music_player_stop -------------------------------

static auto PyMusicPlayerStop(PyObject* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_core->platform->MusicPlayerStop();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMusicPlayerStopDef = {
    "music_player_stop",             // name
    (PyCFunction)PyMusicPlayerStop,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "music_player_stop() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Stops internal music file playback (for internal use)"};

// ---------------------------- music_player_play ------------------------------

static auto PyMusicPlayerPlay(PyObject* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* files_obj;
  static const char* kwlist[] = {"files", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &files_obj)) {
    return nullptr;
  }
  g_core->platform->MusicPlayerPlay(files_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMusicPlayerPlayDef = {
    "music_player_play",             // name
    (PyCFunction)PyMusicPlayerPlay,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "music_player_play(files: Any) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Starts internal music file playback (for internal use)",
};

// ----------------------- music_player_set_volume -----------------------------

static auto PyMusicPlayerSetVolume(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  float volume;
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "f",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  g_core->platform->MusicPlayerSetVolume(volume);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMusicPlayerSetVolumeDef = {
    "music_player_set_volume",            // name
    (PyCFunction)PyMusicPlayerSetVolume,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "music_player_set_volume(volume: float) -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Sets internal music player volume (for internal use)",
};

// ------------------------- music_player_shutdown -----------------------------

static auto PyMusicPlayerShutdown(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_core->platform->MusicPlayerShutdown();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMusicPlayerShutdownDef = {
    "music_player_shutdown",             // name
    (PyCFunction)PyMusicPlayerShutdown,  // method
    METH_VARARGS | METH_KEYWORDS,        // flags

    "music_player_shutdown() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Finalizes internal music file playback (for internal use)",
};

// ----------------------------- reload_media ----------------------------------

static auto PyReloadMedia(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base->graphics_server);
  g_base->graphics_server->PushReloadMediaCall();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyReloadMediaDef = {
    "reload_media",  // name
    PyReloadMedia,   // method
    METH_VARARGS,    // flags

    "reload_media() -> None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Reload all currently loaded game media; useful for\n"
    "development/debugging.",
};

// --------------------------- mac_music_app_init ------------------------------

static auto PyMacMusicAppInit(PyObject* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  g_core->platform->MacMusicAppInit();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMacMusicAppInitDef = {
    "mac_music_app_init",            // name
    (PyCFunction)PyMacMusicAppInit,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "mac_music_app_init() -> None\n"
    "\n"
    "(internal)"};

// ------------------------- mac_music_app_get_volume --------------------------

static auto PyMacMusicAppGetVolume(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  return PyLong_FromLong(g_core->platform->MacMusicAppGetVolume());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMacMusicAppGetVolumeDef = {
    "mac_music_app_get_volume",           // name
    (PyCFunction)PyMacMusicAppGetVolume,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "mac_music_app_get_volume() -> int\n"
    "\n"
    "(internal)",
};

// ------------------------- mac_music_app_set_volume --------------------------

static auto PyMacMusicAppSetVolume(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int volume;
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  g_core->platform->MacMusicAppSetVolume(volume);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMacMusicAppSetVolumeDef = {
    "mac_music_app_set_volume",           // name
    (PyCFunction)PyMacMusicAppSetVolume,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "mac_music_app_set_volume(volume: int) -> None\n"
    "\n"
    "(internal)",
};

// --------------------------- mac_music_app_stop ------------------------------

static auto PyMacMusicAppStop(PyObject* self, PyObject* args,
                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  g_core->platform->MacMusicAppStop();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMacMusicAppStopDef = {
    "mac_music_app_stop",            // name
    (PyCFunction)PyMacMusicAppStop,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "mac_music_app_stop() -> None\n"
    "\n"
    "(internal)",
};

// ----------------------- mac_music_app_play_playlist -------------------------

static auto PyMacMusicAppPlayPlaylist(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  std::string playlist;
  PyObject* playlist_obj;
  static const char* kwlist[] = {"playlist", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &playlist_obj)) {
    return nullptr;
  }
  playlist = g_base->python->GetPyLString(playlist_obj);
  if (g_core->platform->MacMusicAppPlayPlaylist(playlist)) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMacMusicAppPlayPlaylistDef = {
    "mac_music_app_play_playlist",           // name
    (PyCFunction)PyMacMusicAppPlayPlaylist,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "mac_music_app_play_playlist(playlist: str) -> bool\n"
    "\n"
    "(internal)",
};

// ---------------------- mac_music_app_get_playlists --------------------------

static auto PyMacMusicAppGetPlaylists(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* py_list = PyList_New(0);
  std::list<std::string> playlists =
      g_core->platform->MacMusicAppGetPlaylists();
  for (auto&& i : playlists) {
    PyObject* str_obj = PyUnicode_FromString(i.c_str());
    PyList_Append(py_list, str_obj);
    Py_DECREF(str_obj);
  }
  return py_list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyMacMusicAppGetPlaylistsDef = {
    "mac_music_app_get_playlists",           // name
    (PyCFunction)PyMacMusicAppGetPlaylists,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "mac_music_app_get_playlists() -> list[str]\n"
    "\n"
    "(internal)",
};

// -------------------------- is_os_playing_music ------------------------------

static auto PyIsOSPlayingMusic(PyObject* self, PyObject* args,
                               PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_core->platform->IsOSPlayingMusic()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyIsOSPlayingMusicDef = {
    "is_os_playing_music",            // name
    (PyCFunction)PyIsOSPlayingMusic,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "is_os_playing_music() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    "Tells whether the OS is currently playing music of some sort.\n"
    "\n"
    "(Used to determine whether the app should avoid playing its own)",
};

// -------------------------------- exec_arg -----------------------------------

static auto PyExecArg(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  if (g_core->core_config().exec_command.has_value()) {
    return PyUnicode_FromString(g_core->core_config().exec_command->c_str());
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyExecArgDef = {
    "exec_arg",              // name
    (PyCFunction)PyExecArg,  // method
    METH_NOARGS,             // flags

    "exec_arg() -> str | None\n"
    "\n"
    "(internal)\n",
};

// ----------------------------- on_app_running --------------------------------

static auto PyOnAppRunning(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base && g_base->InLogicThread());
  g_base->logic->OnAppRunning();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOnAppRunningDef = {
    "on_app_running",             // name
    (PyCFunction)PyOnAppRunning,  // method
    METH_NOARGS,                  // flags

    "on_app_running() -> None\n"
    "\n"
    "(internal)\n",
};

// ------------------------ on_initial_app_mode_set ----------------------------

static auto PyOnInitialAppModeSet(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base && g_base->InLogicThread());
  g_base->logic->OnInitialAppModeSet();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOnInitialAppModeSetDef = {
    "on_initial_app_mode_set",           // name
    (PyCFunction)PyOnInitialAppModeSet,  // method
    METH_NOARGS,                         // flags

    "on_initial_app_mode_set() -> None\n"
    "\n"
    "(internal)\n",
};

// ------------------------- reached_end_of_babase -----------------------------

static auto PyReachedEndOfBaBase(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base);
  g_base->OnReachedEndOfBaBaseImport();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyReachedEndOfBaBaseDef = {
    "reached_end_of_babase",            // name
    (PyCFunction)PyReachedEndOfBaBase,  // method
    METH_NOARGS,                        // flags

    "reached_end_of_babase() -> None\n"
    "\n"
    "A simple user-agent-string that should be used in any web requests made\n"
    "on behalf of the engine.",
};

// --------------------------- user_agent_string -------------------------------

static auto PyUserAgentString(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "Ballistica/%s", kEngineVersion);
  return PyUnicode_FromString(buffer);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyUserAgentStringDef = {
    "user_agent_string",             // name
    (PyCFunction)PyUserAgentString,  // method
    METH_NOARGS,                     // flags

    "user_agent_string() -> str\n"
    "\n"
    "(internal)\n",
};

// --------------------- empty_app_mode_activate ----------------------------

static auto PyOnEmptyAppModeActivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  g_base->set_app_mode(EmptyAppMode::GetSingleton());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOnEmptyAppModeActivateDef = {
    "empty_app_mode_activate",              // name
    (PyCFunction)PyOnEmptyAppModeActivate,  // method
    METH_NOARGS,                            // flags

    "empty_app_mode_activate() -> None\n"
    "\n"
    "(internal)\n",
};

// --------------------- empty_app_mode_deactivate --------------------------

static auto PyOnEmptyAppModeDeactivate(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  // Currently doing nothing.
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyOnEmptyAppModeDeactivateDef = {
    "empty_app_mode_deactivate",              // name
    (PyCFunction)PyOnEmptyAppModeDeactivate,  // method
    METH_NOARGS,                              // flags

    "empty_app_mode_deactivate() -> None\n"
    "\n"
    "(internal)\n",
};

// --------------- empty_app_mode_handle_app_intent_default --------------------

static auto PyEmptyAppModeHandleAppIntentDefault(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEmptyAppModeHandleAppIntentDefaultDef = {
    "empty_app_mode_handle_app_intent_default",         // name
    (PyCFunction)PyEmptyAppModeHandleAppIntentDefault,  // method
    METH_NOARGS,                                        // flags

    "empty_app_mode_handle_app_intent_default() -> None\n"
    "\n"
    "(internal)\n",
};

// ---------------- empty_app_mode_handle_app_intent_exec ----------------------

static auto PyEmptyAppModeHandleAppIntentExec(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* command;
  static const char* kwlist[] = {"command", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &command)) {
    return nullptr;
  }
  // Simply run the command.
  if (g_core->core_config().exec_command.has_value()) {
    bool success = PythonCommand(*g_core->core_config().exec_command,
                                 BA_BUILD_COMMAND_FILENAME)
                       .Exec(true, nullptr, nullptr);
    if (!success) {
      // TODO(ericf): what should we do in this case?
      //  Obviously if we add return/success values for intents we should set
      //  that here.
    }
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEmptyAppModeHandleAppIntentExecDef = {
    "empty_app_mode_handle_app_intent_exec",         // name
    (PyCFunction)PyEmptyAppModeHandleAppIntentExec,  // method
    METH_VARARGS | METH_KEYWORDS,                    // flags

    "empty_app_mode_handle_app_intent_exec(command: str) -> None\n"
    "\n"
    "(internal)",
};

// ---------------------- get_immediate_return_code ----------------------------

static auto PyGetImmediateReturnCode(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_core);
  auto val = g_core->core_config().immediate_return_code;
  if (!val.has_value()) {
    Py_RETURN_NONE;
  }
  return PyLong_FromLong(*val);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetImmediateReturnCodeDef = {
    "get_immediate_return_code",            // name
    (PyCFunction)PyGetImmediateReturnCode,  // method
    METH_NOARGS,                            // flags

    "get_immediate_return_code() -> int | None\n"
    "\n"
    "(internal)\n",
};

// ----------------------- shutdown_suppress_begin -----------------------------

static auto PyShutdownSuppressBegin(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base);
  auto val = g_base->ShutdownSuppressBegin();
  if (val) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyShutdownSuppressBeginDef = {
    "shutdown_suppress_begin",             // name
    (PyCFunction)PyShutdownSuppressBegin,  // method
    METH_NOARGS,                           // flags

    "shutdown_suppress_begin() -> bool\n"
    "\n"
    "(internal)\n",
};

// ------------------------ shutdown_suppress_end ------------------------------

static auto PyShutdownSuppressEnd(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base);
  g_base->ShutdownSuppressEnd();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyShutdownSuppressEndDef = {
    "shutdown_suppress_end",             // name
    (PyCFunction)PyShutdownSuppressEnd,  // method
    METH_NOARGS,                         // flags

    "shutdown_suppress_end() -> None\n"
    "\n"
    "(internal)\n",
};

// ----------------------- shutdown_suppress_count -----------------------------

static auto PyShutdownSuppressCount(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_base);
  return PyLong_FromLong(g_base->ShutdownSuppressGetCount());
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyShutdownSuppressCountDef = {
    "shutdown_suppress_count",             // name
    (PyCFunction)PyShutdownSuppressCount,  // method
    METH_NOARGS,                           // flags

    "shutdown_suppress_count() -> int\n"
    "\n"
    "(internal)\n",
};

// --------------------- get_dev_console_input_text ----------------------------

static auto PyGetDevConsoleInputText(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* console = g_base->ui->dev_console();
  BA_PRECONDITION(console);
  return PyUnicode_FromString(console->input_string().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetDevConsoleInputTextDef = {
    "get_dev_console_input_text",           // name
    (PyCFunction)PyGetDevConsoleInputText,  // method
    METH_NOARGS,                            // flags

    "get_dev_console_input_text() -> str\n"
    "\n"
    "(internal)\n",
};

// --------------------- set_dev_console_input_text ----------------------------

static auto PySetDevConsoleInputText(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* console = g_base->ui->dev_console();
  BA_PRECONDITION(console);

  const char* val;
  static const char* kwlist[] = {"val", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &val)) {
    return nullptr;
  }
  console->set_input_string(val);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetDevConsoleInputTextDef = {
    "set_dev_console_input_text",           // name
    (PyCFunction)PySetDevConsoleInputText,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "set_dev_console_input_text(val: str) -> None\n"
    "\n"
    "(internal)\n",
};

// ------------------ dev_console_input_adapter_finish -------------------------

static auto PyDevConsoleInputAdapterFinish(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  auto* console = g_base->ui->dev_console();
  BA_PRECONDITION(console);
  console->InputAdapterFinish();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDevConsoleInputAdapterFinishDef = {
    "dev_console_input_adapter_finish",           // name
    (PyCFunction)PyDevConsoleInputAdapterFinish,  // method
    METH_NOARGS,                                  // flags

    "dev_console_input_adapter_finish() -> None\n"
    "\n"
    "(internal)\n",
};

// -------------------------- audio_shutdown_begin -----------------------------

static auto PyAudioShutdownBegin(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  auto* audio_event_loop = g_base->audio_server->event_loop();
  BA_PRECONDITION(audio_event_loop);
  audio_event_loop->PushCall([] { g_base->audio_server->Shutdown(); });
  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyAudioShutdownBeginDef = {
    "audio_shutdown_begin",             // name
    (PyCFunction)PyAudioShutdownBegin,  // method
    METH_NOARGS,                        // flags

    "audio_shutdown_begin() -> None\n"
    "\n"
    "(internal)\n",
};

// ----------------------- audio_shutdown_is_complete --------------------------

static auto PyAudioShutdownIsComplete(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  if (g_base->audio_server->shutdown_completed()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyAudioShutdownIsCompleteDef = {
    "audio_shutdown_is_complete",            // name
    (PyCFunction)PyAudioShutdownIsComplete,  // method
    METH_NOARGS,                             // flags

    "audio_shutdown_is_complete() -> bool\n"
    "\n"
    "(internal)\n",
};

// ----------------------- graphics_shutdown_begin -----------------------------

static auto PyGraphicsShutdownBegin(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  g_base->app_adapter->PushGraphicsContextCall(
      [] { g_base->graphics_server->Shutdown(); });

  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGraphicsShutdownBeginDef = {
    "graphics_shutdown_begin",             // name
    (PyCFunction)PyGraphicsShutdownBegin,  // method
    METH_NOARGS,                           // flags

    "graphics_shutdown_begin() -> None\n"
    "\n"
    "(internal)\n",
};

// -------------------- graphics_shutdown_is_complete --------------------------

static auto PyGraphicsShutdownIsComplete(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  if (g_base->graphics_server->shutdown_completed()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyGraphicsShutdownIsCompleteDef = {
    "graphics_shutdown_is_complete",            // name
    (PyCFunction)PyGraphicsShutdownIsComplete,  // method
    METH_NOARGS,                                // flags

    "graphics_shutdown_is_complete() -> bool\n"
    "\n"
    "(internal)\n",
};

// --------------------------- invoke_main_menu --------------------------------

static auto PyInvokeMainMenu(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  if (!g_base->ui->MainMenuVisible()) {
    g_base->ui->PushMainMenuPressCall(nullptr);
  }
  Py_RETURN_NONE;

  BA_PYTHON_CATCH;
}

static PyMethodDef PyInvokeMainMenuDef = {
    "invoke_main_menu",             // name
    (PyCFunction)PyInvokeMainMenu,  // method
    METH_NOARGS,                    // flags

    "invoke_main_menu() -> None\n"
    "\n"
    "High level call to bring up the main menu if it is not present.\n"
    "\n"
    "This is essentially the same as pressing the menu button on a controller.",
};
// -----------------------------------------------------------------------------

auto PythonMethodsBase1::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyAppNameDef,
      PyAppIsActiveDef,
      PyRunAppDef,
      PyAppNameUpperDef,
      PyIsXCodeBuildDef,
      PyCanDisplayFullUnicodeDef,
      PyEmitLogDef,
      PyV1CloudLogDef,
      PyEnvDef,
      PyPreEnvDef,
      PyCommitConfigDef,
      PyDoApplyAppConfigDef,
      PyQuitDef,
      PyAppTimerDef,
      PyAppTimeDef,
      PyDisplayTimeDef,
      PyDisplayTimerDef,
      PyPushCallDef,
      PyMusicPlayerShutdownDef,
      PyMusicPlayerSetVolumeDef,
      PyMusicPlayerPlayDef,
      PyMusicPlayerStopDef,
      PyAppInstanceUUIDDef,
      PyUserRanCommandsDef,
      PyReloadMediaDef,
      PyMacMusicAppInitDef,
      PyMacMusicAppGetVolumeDef,
      PyMacMusicAppSetVolumeDef,
      PyMacMusicAppStopDef,
      PyMacMusicAppPlayPlaylistDef,
      PyMacMusicAppGetPlaylistsDef,
      PyIsOSPlayingMusicDef,
      PyLifecycleLogDef,
      PyExecArgDef,
      PyOnAppRunningDef,
      PyOnInitialAppModeSetDef,
      PyReachedEndOfBaBaseDef,
      PyUserAgentStringDef,
      PyOnEmptyAppModeActivateDef,
      PyOnEmptyAppModeDeactivateDef,
      PyEmptyAppModeHandleAppIntentDefaultDef,
      PyEmptyAppModeHandleAppIntentExecDef,
      PyGetImmediateReturnCodeDef,
      PyCompleteShutdownDef,
      PyShutdownSuppressBeginDef,
      PyShutdownSuppressEndDef,
      PyShutdownSuppressCountDef,
      PyGetDevConsoleInputTextDef,
      PySetDevConsoleInputTextDef,
      PyDevConsoleInputAdapterFinishDef,
      PyAudioShutdownBeginDef,
      PyAudioShutdownIsCompleteDef,
      PyGraphicsShutdownBeginDef,
      PyGraphicsShutdownIsCompleteDef,
      PyInvokeMainMenuDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
