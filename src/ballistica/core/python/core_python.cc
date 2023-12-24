// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/python/core_python.h"

#include "ballistica/core/mgen/python_modules_monolithic.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica::core {

static void PythonLowLevelDebugLog_(const char* msg) {
  assert(g_core);
  g_core->platform->LowLevelDebugLog(msg);
}

static void CheckPyInitStatus(const char* where, const PyStatus& status) {
  if (PyStatus_Exception(status)) {
    FatalError(std::string("Error in ") + where + ": "
               + (status.err_msg ? status.err_msg : "(nullptr err_msg)") + ".");
  }
}

void CorePython::InitPython() {
  assert(g_core->InMainThread());
  assert(g_buildconfig.monolithic_build());

  // Install our low level logger in our custom Python builds.
#ifdef PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG
  Py_BallisticaLowLevelDebugLog = PythonLowLevelDebugLog_;
#endif

  // Flip on some extra runtime debugging options in debug builds.
  // https://docs.python.org/3/library/devmode.html#devmode
  int dev_mode{g_buildconfig.debug_build()};

  // Pre-config as isolated if we include our own Python and as standard
  // otherwise.
  PyPreConfig preconfig{};
  if (g_buildconfig.contains_python_dist()) {
    PyPreConfig_InitIsolatedConfig(&preconfig);
  } else {
    PyPreConfig_InitPythonConfig(&preconfig);
  }
  preconfig.dev_mode = dev_mode;

  // We want consistent utf-8 everywhere (Python used to default to
  // windows-specific file encodings, etc.)
  preconfig.utf8_mode = 1;

  CheckPyInitStatus("Py_PreInitialize", Py_PreInitialize(&preconfig));

  // Configure as isolated if we include our own Python and as standard
  // otherwise.
  PyConfig config{};
  if (g_buildconfig.contains_python_dist()) {
    PyConfig_InitIsolatedConfig(&config);
    // We manage paths 100% ourself in this case and don't want any site
    // stuff (neither site nor user-site).
    config.site_import = 0;
  } else {
    PyConfig_InitPythonConfig(&config);
  }
  config.dev_mode = dev_mode;
  config.optimization_level = g_buildconfig.debug_build() ? 0 : 1;

  // In cases where we bundle Python, set up all paths explicitly.
  // https://docs.python.org/3/c-api/init_config.html#path-configuration
  if (g_buildconfig.contains_python_dist()) {
    std::string root = g_buildconfig.ostype_windows() ? "C:\\" : "/";

    // In our embedded case, none of these paths are really meaningful, but
    // we want to explicitly provide them so Python doesn't try to calc its
    // own. So let's set them to obvious dummy ones so its clear if they
    // show up anywhere important.
    CheckPyInitStatus(
        "pyconfig home set",
        PyConfig_SetBytesString(&config, &config.home,
                                (root + "dummy_py_home").c_str()));
    CheckPyInitStatus(
        "pyconfig base_exec_prefix set",
        PyConfig_SetBytesString(&config, &config.base_exec_prefix,
                                (root + "dummy_py_base_exec_prefix").c_str()));
    CheckPyInitStatus(
        "pyconfig base_executable set",
        PyConfig_SetBytesString(&config, &config.base_executable,
                                (root + "dummy_py_base_executable").c_str()));
    CheckPyInitStatus(
        "pyconfig base_prefix set",
        PyConfig_SetBytesString(&config, &config.base_prefix,
                                (root + "dummy_py_base_prefix").c_str()));
    CheckPyInitStatus(
        "pyconfig exec_prefix set",
        PyConfig_SetBytesString(&config, &config.exec_prefix,
                                (root + "dummy_py_exec_prefix").c_str()));
    CheckPyInitStatus(
        "pyconfig executable set",
        PyConfig_SetBytesString(&config, &config.executable,
                                (root + "dummy_py_executable").c_str()));
    CheckPyInitStatus(
        "pyconfig prefix set",
        PyConfig_SetBytesString(&config, &config.prefix,
                                (root + "dummy_py_prefix").c_str()));

    // Note: we're using utf-8 mode above so Py_DecodeLocale will convert
    // from utf-8.

    // Interesting note: it seems we can pass relative paths here but they
    // wind up in sys.path as absolute paths (unlike entries we add to
    // sys.path *after* things are up and running). Though nowadays we want
    // to use abs paths anyway to avoid needing chdir so its a moot point.
    if (g_buildconfig.ostype_windows()) {
      // On most platforms we stuff abs paths in here so things can work
      // from wherever. However on Windows we need to be running from where
      // this stuff lives so we pick up various .dlls that live there/etc.
      // So let's make some clear noise if we don't seem to be there.
      // (otherwise it leads to cryptic Python init messages about locale
      // module not being found/etc. which is not very helpful).
      if (!g_core->platform->FilePathExists("DLLs")
          || (!g_core->platform->FilePathExists("lib"))
          || (!g_core->platform->FilePathExists("ba_data"))) {
        FatalError(
            "Ballistica seems to be running from the wrong "
            "directory; our stuff isn't here (ba_data, etc.).\nCWD is "
            + g_core->platform->GetCWD());
      }

      // Windows Python by default looks for Lib and DLLs dirs, along with
      // some others, but we want to be more explicit in limiting to those
      // two. It also seems that windows Python's paths can be incorrect if
      // we're in strange dirs such as \\wsl$\Ubuntu-18.04\ that we get with
      // WSL build setups.

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
      auto pylibpath = g_core->platform->GetDataDirectoryMonolithicDefault()
                       + BA_DIRSLASH + "pylib";
      PyWideStringList_Append(&config.module_search_paths,
                              Py_DecodeLocale(pylibpath.c_str(), nullptr));
    }
    config.module_search_paths_set = 1;
  }

  // In monolithic builds, let Python know how to import all our built-in
  // modules. In other builds, everything will be expected to live on disk
  // as .so files (or symlinks to them).
  if (g_buildconfig.monolithic_build()) {
    MonolithicRegisterPythonModules();
  }

  // Init Python.
  CheckPyInitStatus("Py_InitializeFromConfig",
                    Py_InitializeFromConfig(&config));

  PyConfig_Clear(&config);
}

void CorePython::EnablePythonLoggingCalls() {
  if (python_logging_calls_enabled_) {
    return;
  }
  auto gil{Python::ScopedInterpreterLock()};

  assert(objs().Exists(ObjID::kLoggingDebugCall));
  assert(objs().Exists(ObjID::kLoggingInfoCall));
  assert(objs().Exists(ObjID::kLoggingWarningCall));
  assert(objs().Exists(ObjID::kLoggingErrorCall));
  assert(objs().Exists(ObjID::kLoggingCriticalCall));

  // Push any early log calls we've been holding on to along to Python.
  {
    std::scoped_lock lock(early_log_lock_);
    python_logging_calls_enabled_ = true;
    for (auto&& entry : early_logs_) {
      LoggingCall(entry.first, "[HELD] " + entry.second);
    }
    early_logs_.clear();
  }
}

void CorePython::ImportPythonObjs() {
  // Grab core Python objs we use.
#include "ballistica/core/mgen/pyembed/binding_core.inc"

  // Also grab a few things we define in env.inc. Normally this sort of
  // thing would go in _hooks.py in our Python package, but because we are
  // core we don't have one, so we have to do it via inline code.
  {
#include "ballistica/core/mgen/pyembed/env.inc"
    auto ctx = PythonRef(PyDict_New(), PythonRef::kSteal);
    if (!PythonCommand(env_code, "bameta/pyembed/env.py")
             .Exec(true, *ctx, *ctx)) {
      FatalError("Error in ba Python env code. See log for details.");
    }
    objs_.StoreCallable(ObjID::kPrependSysPathCall,
                        *ctx.DictGetItem("prepend_sys_path"));
    objs_.StoreCallable(ObjID::kBaEnvConfigureCall,
                        *ctx.DictGetItem("import_baenv_and_run_configure"));
    objs_.StoreCallable(ObjID::kBaEnvGetConfigCall,
                        *ctx.DictGetItem("get_env_config"));
  }
}

void CorePython::SoftImportBase() {
  auto gil{Python::ScopedInterpreterLock()};
  auto result = PythonRef::StolenSoft(PyImport_ImportModule("_babase"));
  if (!result.Exists()) {
    // Ignore any errors here for now. All that will matter is whether base
    // gave us its interface.
    PyErr_Clear();
  }
}

void CorePython::VerifyPythonEnvironment() {
  // Make sure we're running the Python version we require.
  const char* ver = Py_GetVersion();
  if (strncmp(ver, "3.11", 4) != 0) {
    FatalError("We require Python 3.11.x; instead found " + std::string(ver));
  }
}

void CorePython::MonolithicModeBaEnvConfigure() {
  assert(g_buildconfig.monolithic_build());
  assert(g_core);
  g_core->LifecycleLog("baenv.configure() begin");

  auto gil{Python::ScopedInterpreterLock()};

  // To start with, stuff a single path into python-paths which should
  // allow us to find our baenv module which will do the rest of the work
  // (adding our full set of paths, etc).
  // data-dir is the one monolithic-default value that MUST be defined
  // so we base it on this.
  auto default_py_dir = std::string("ba_data") + BA_DIRSLASH + "python";
  auto data_dir_mono_default =
      g_core->platform->GetDataDirectoryMonolithicDefault();
  // Keep path clean if data-dir val is ".".
  if (data_dir_mono_default != ".") {
    default_py_dir = data_dir_mono_default + BA_DIRSLASH + default_py_dir;
  }
  auto args = PythonRef::Stolen(Py_BuildValue("(s)", default_py_dir.c_str()));
  objs().Get(ObjID::kPrependSysPathCall).Call(args);

  // Import and run baenv.configure() using our 'monolithic' values for all
  // paths.
  std::optional<std::string> config_dir =
      g_core->platform->GetConfigDirectoryMonolithicDefault();
  std::optional<std::string> data_dir =
      g_core->platform->GetDataDirectoryMonolithicDefault();
  std::optional<std::string> user_python_dir =
      g_core->platform->GetUserPythonDirectoryMonolithicDefault();
  auto kwargs =
      // clang-format off
    PythonRef::Stolen(Py_BuildValue(
      "{"
      "sO"  // config_dir
      "sO"  // data_dir
      "sO"  // user_python_dir
      "sO"  // contains_python_dist
      "}",
      "config_dir",
        config_dir ? *PythonRef::FromString(*config_dir) : Py_None,
      "data_dir",
        data_dir ? *PythonRef::FromString(*data_dir) : Py_None,
      "user_python_dir",
        user_python_dir ? *PythonRef::FromString(*user_python_dir) : Py_None,
      "contains_python_dist",
        g_buildconfig.contains_python_dist() ? Py_True : Py_False));
  // clang-format on
  auto result = objs()
                    .Get(ObjID::kBaEnvConfigureCall)
                    .Call(objs().Get(ObjID::kEmptyTuple), kwargs);
  if (!result.Exists()) {
    FatalError(
        "Environment setup failed.\n"
        "This usually means you are running the app from the wrong location.\n"
        "See log for details.");
  }
  g_core->LifecycleLog("baenv.configure() end");
}

void CorePython::LoggingCall(LogLevel loglevel, const std::string& msg) {
  // If we're not yet sending logs to Python, store this one away until we are.
  if (!python_logging_calls_enabled_) {
    std::scoped_lock lock(early_log_lock_);
    early_logs_.emplace_back(loglevel, msg);

    // UPDATE - trying to disable this for now to make the concept of delayed
    // logs a bit less scary. Perhaps we can update fatal-error to dump these or
    // have a mode to immediate-print them as needed.
    if (explicit_bool(false)) {
      // There's a chance that we're going down in flames and this log
      // might be useful to see even if we never get a chance to chip it to
      // Python. So let's make an attempt to get it at least seen now in
      // whatever way we can. (platform display-log call and stderr).
      const char* errmsg{
          "CorePython::LoggingCall() called before Python"
          " logging available."};
      if (g_core->platform) {
        g_core->platform->EmitPlatformLog("root", LogLevel::kError, errmsg);
        g_core->platform->EmitPlatformLog("root", loglevel, msg);
      }
      fprintf(stderr, "%s\n%s\n", errmsg, msg.c_str());
    }
    return;
  }

  // Ok; seems we've got Python calls. Run the right one for our log level.
  ObjID logcallobj;
  switch (loglevel) {
    case LogLevel::kDebug:
      logcallobj = ObjID::kLoggingDebugCall;
      break;
    case LogLevel::kInfo:
      logcallobj = ObjID::kLoggingInfoCall;
      break;
    case LogLevel::kWarning:
      logcallobj = ObjID::kLoggingWarningCall;
      break;
    case LogLevel::kError:
      logcallobj = ObjID::kLoggingErrorCall;
      break;
    case LogLevel::kCritical:
      logcallobj = ObjID::kLoggingCriticalCall;
      break;
    default:
      logcallobj = ObjID::kLoggingInfoCall;
      fprintf(stderr, "Unexpected LogLevel %d\n", static_cast<int>(loglevel));
      break;
  }

  // Make sure we're good to go from any thread.
  Python::ScopedInterpreterLock lock;

  PythonRef args(Py_BuildValue("(s)", msg.c_str()), PythonRef::kSteal);
  objs().Get(logcallobj).Call(args);
}

auto CorePython::WasModularMainCalled() -> bool {
  assert(!g_buildconfig.monolithic_build());

  // This gets called in modular builds before anything is inited, so we need to
  // avoid using anything from g_core or whatnot here; only raw Python stuff.

  PyObject* baenv = PyImport_ImportModule("baenv");
  if (!baenv) {
    FatalError("Unable to import baenv module.");
  }
  PyObject* env_globals_class = PyObject_GetAttrString(baenv, "_EnvGlobals");
  if (!env_globals_class) {
    FatalError("_EnvGlobals class not found in baenv.");
  }
  PyObject* get_call = PyObject_GetAttrString(env_globals_class, "get");
  if (!get_call) {
    FatalError("get() call not found on baenv._EnvGlobals.");
  }
  PyObject* env_globals_instance = PyObject_CallNoArgs(get_call);
  if (!get_call) {
    FatalError("baenv._EnvGlobals.get() call failed.");
  }
  PyObject* modular_main_called =
      PyObject_GetAttrString(env_globals_instance, "modular_main_called");
  if (!modular_main_called || !PyBool_Check(modular_main_called)) {
    FatalError("modular_main_called bool not found on baenv _EnvGlobals.");
  }
  assert(modular_main_called == Py_True || modular_main_called == Py_False);
  bool val = modular_main_called == Py_True;

  Py_DECREF(baenv);
  Py_DECREF(env_globals_class);
  Py_DECREF(get_call);
  Py_DECREF(env_globals_instance);
  Py_DECREF(modular_main_called);

  return val;
}

auto CorePython::FetchPythonArgs(std::vector<std::string>* buffer)
    -> std::vector<char*> {
  // This gets called in modular builds before anything is inited, so we need to
  // avoid using anything from g_core or whatnot here; only raw Python stuff.

  assert(buffer && buffer->empty());
  PyObject* sys = PyImport_ImportModule("sys");
  if (!sys) {
    FatalError("Unable to import sys module.");
  }
  PyObject* argv = PyObject_GetAttrString(sys, "argv");
  if (!argv || !PyList_Check(argv)) {
    FatalError("Unable to fetch sys.argv list.");
  }
  Py_ssize_t listlen = PyList_GET_SIZE(argv);
  for (Py_ssize_t i = 0; i < listlen; ++i) {
    PyObject* arg = PyList_GET_ITEM(argv, i);
    BA_PRECONDITION_FATAL(PyUnicode_Check(arg));
    buffer->push_back(PyUnicode_AsUTF8(arg));
  }
  Py_DECREF(sys);
  Py_DECREF(argv);

  // Ok, we've filled the buffer so it won't be resizing anymore. Now set up
  // argv pointers to it.
  std::vector<char*> out;
  out.reserve(buffer->size());
  for (size_t i = 0; i < buffer->size(); ++i) {
    out.push_back(const_cast<char*>((*buffer)[i].c_str()));
  }
  return out;
}

}  // namespace ballistica::core
