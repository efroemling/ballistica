// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/python/core_python.h"

#include <cstdio>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/core/mgen/python_modules_monolithic.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica::core {

#ifdef PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG
static void PythonLowLevelDebugLog_(const char* msg) {
  assert(g_core);
  g_core->platform->LowLevelDebugLog(msg);
}
#endif

static void CheckPyInitStatus(const char* where, const PyStatus& status) {
  if (PyStatus_Exception(status)) {
    FatalError(std::string("Error in ") + where + ": "
               + (status.err_msg ? status.err_msg : "(nullptr err_msg)") + ".");
  }
}

void CorePython::InitPython() {
  assert(g_core->InMainThread());
  assert(g_buildconfig.monolithic_build());
  assert(!monolithic_init_complete_);

  // Install our low level logger in our custom Python builds.
#ifdef PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG
  Py_BallisticaLowLevelDebugLog = PythonLowLevelDebugLog_;
#endif

  // Flip on some extra runtime debugging options in our debug builds.
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

  // When we run baenv.configure it will set Python's pycache_prefix to a
  // path under our cache dir, keeping .pyc files nicely isolated from our
  // scripts and allowing writing of opt .pyc files even for standard
  // library modules which we likely would not have write access to do
  // otherwise. Ideally, however this path should be set earlier, when
  // initing Python itself, so that it covers *all* imports and not just the
  // ones after baenv does its thing. So we attempt to do the same path
  // calculation here that baenv will do so that the value can stay
  // consistent for the whole run. If we don't get it right, baenv will spit
  // out a warning that pycache_prefix is changing mid-run.
  std::optional<std::string> pycache_prefix;
  std::optional<std::string> cache_dir =
      g_core->platform->GetCacheDirectoryMonolithicDefault();
  if (!cache_dir.has_value()) {
    // If we don't have an explicit cache dir, it is based on config-dir.
    // Let's try to calc that.
    std::optional<std::string> config_dir =
        g_core->platform->GetConfigDirectoryMonolithicDefault();
    if (!config_dir.has_value()) {
      // If we don't have an explicit config dir, try to calc it.
      //
      // On unixy OSs our default config dir is '~/.ballisticakit'. So let's
      // calc that if we have a value for $(HOME). This should actually
      // cover all cases; non-unixy OSs should be passing config-dir in
      // explicitly.
      auto home = g_core->platform->GetEnv("HOME");
      if (home.has_value() && !home->empty()) {
        config_dir = *home + BA_DIRSLASH + ".ballisticakit";
      }
    }
    // If we've calced a config-dir, we can calc cache-dir.
    if (config_dir.has_value()) {
      cache_dir = *config_dir + BA_DIRSLASH + "cache";
    }
  }
  // If we've calced a cache-dir, we can calc pycache-dir.
  if (cache_dir.has_value()) {
    pycache_prefix = *cache_dir + BA_DIRSLASH + "pyc";
  }

  if (pycache_prefix.has_value()) {
    PyConfig_SetBytesString(&config, &config.pycache_prefix,
                            pycache_prefix->c_str());
  }

  // In cases where we bundle Python, set up all paths explicitly.
  // https://docs.python.org/3/c-api/init_config.html#path-configuration
  if (g_buildconfig.contains_python_dist()) {
    std::string root = g_buildconfig.platform_windows() ? "C:\\" : "/";

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
    if (g_buildconfig.platform_windows()) {
      // On most platforms we stuff abs paths in here so things can work
      // from wherever and we don't really care where we are. However on
      // Windows we need to be running from where this stuff lives so we
      // pick up various .dlls that live there/etc. So let's make some clear
      // noise if we don't seem to be there. (otherwise it leads to cryptic
      // Python init messages about locale module not being found/etc. which
      // is not very helpful).
      if (!g_core->platform->FilePathExists("DLLs")
          || (!g_core->platform->FilePathExists("lib"))
          || (!g_core->platform->FilePathExists("ba_data"))) {
        FatalError(
            "BallisticaKit seems to be running from the wrong "
            "directory; our stuff isn't here (ba_data, etc.).\nCWD is "
            + g_core->platform->GetCWD());
      }

      // Windows Python by default looks for Lib and DLLs dirs, along with
      // some others, but we want to be more explicit in limiting to those
      // two. It also seems that Windows Python's paths can be incorrect if
      // we're in strange dirs such as \\wsl$\Ubuntu-18.04\ that we get with
      // WSL build setups.

      // NOTE: Python for Windows actually comes with 'Lib', not 'lib', but
      // it seems the interpreter defaults point to ./lib (as of 3.8.5).
      // Normally this doesn't matter since Windows is case-insensitive but
      // under WSL it does. So we currently bundle the dir as 'lib' and use
      // that in our path so that everything is happy (both with us and with
      // python.exe).
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

    // Some platforms need to be able to load binary modules from
    // pylib/lib-dynload.
    if (g_buildconfig.xcode_build()) {
      auto pylibpath = g_core->platform->GetDataDirectoryMonolithicDefault()
                       + BA_DIRSLASH + "pylib" + BA_DIRSLASH + "lib-dynload";
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

  // Optionally prevent .pyc creation.
  if (g_core->core_config().dont_write_bytecode) {
    config.write_bytecode = 0;
  }

  // Init Python.
  CheckPyInitStatus("Py_InitializeFromConfig",
                    Py_InitializeFromConfig(&config));

  PyConfig_Clear(&config);

  monolithic_init_complete_ = true;
}

void CorePython::AtExit(PyObject* call) {
  // Currently this only works in monolithic builds.
  BA_PRECONDITION(g_buildconfig.monolithic_build());
  auto args = PythonRef::Stolen(Py_BuildValue("(O)", call));
  auto result{objs().Get(ObjID::kBaEnvAtExitCall).Call(args)};
  assert(result.exists());
}

void CorePython::FinalizePython() {
  assert(g_core->InMainThread());
  assert(g_buildconfig.monolithic_build());
  assert(g_core->engine_done());
  assert(!finalize_called_);
  assert(monolithic_init_complete_);
  assert(Python::HaveGIL());

  finalize_called_ = true;

  // Run our registered atexit calls/etc.
  auto pre_finalize_result{objs().Get(ObjID::kBaEnvPreFinalizeCall).Call()};
  assert(pre_finalize_result.exists() && pre_finalize_result.get() == Py_None);

  auto result{Py_FinalizeEx()};

  if (result != 0) {
    // We can't use our high level logging here since Python is involved;
    // just print to stderr and any platform logs directly to hopefully get
    // seen.
    std::string errmsg = "Py_FinalizeEx() errored.";
    fprintf(stderr, "%s\n", errmsg.c_str());
    g_core->platform->EmitPlatformLog("root", LogLevel::kError, errmsg);
  }
}

void CorePython::EnablePythonLoggingCalls() {
  if (python_logging_calls_enabled_) {
    return;
  }
  auto gil{Python::ScopedInterpreterLock()};

  // Make sure we've got all our logging Python bits we need.
  assert(objs().Exists(ObjID::kLoggingLevelNotSet));
  assert(objs().Exists(ObjID::kLoggingLevelDebug));
  assert(objs().Exists(ObjID::kLoggingLevelInfo));
  assert(objs().Exists(ObjID::kLoggingLevelWarning));
  assert(objs().Exists(ObjID::kLoggingLevelError));
  assert(objs().Exists(ObjID::kLoggingLevelCritical));
  assert(objs().Exists(ObjID::kLoggerRoot));
  assert(objs().Exists(ObjID::kLoggerRootLogCall));
  assert(objs().Exists(ObjID::kLoggerBa));
  assert(objs().Exists(ObjID::kLoggerBaLogCall));
  assert(objs().Exists(ObjID::kLoggerBaApp));
  assert(objs().Exists(ObjID::kLoggerBaAppLogCall));
  assert(objs().Exists(ObjID::kLoggerBaAudio));
  assert(objs().Exists(ObjID::kLoggerBaAudioLogCall));
  assert(objs().Exists(ObjID::kLoggerBaDisplayTime));
  assert(objs().Exists(ObjID::kLoggerBaDisplayTimeLogCall));
  assert(objs().Exists(ObjID::kLoggerBaGraphics));
  assert(objs().Exists(ObjID::kLoggerBaGraphicsLogCall));
  assert(objs().Exists(ObjID::kLoggerBaLifecycle));
  assert(objs().Exists(ObjID::kLoggerBaLifecycleLogCall));
  assert(objs().Exists(ObjID::kLoggerBaAssets));
  assert(objs().Exists(ObjID::kLoggerBaAssetsLogCall));
  assert(objs().Exists(ObjID::kLoggerBaInput));
  assert(objs().Exists(ObjID::kLoggerBaInputLogCall));
  assert(objs().Exists(ObjID::kLoggerBaNetworking));
  assert(objs().Exists(ObjID::kLoggerBaNetworkingLogCall));

  // Push any early log calls we've been holding on to along to Python.
  {
    std::scoped_lock lock(early_log_lock_);
    python_logging_calls_enabled_ = true;
    for (auto&& entry : early_logs_) {
      LoggingCall(std::get<0>(entry), std::get<1>(entry),
                  "[HELD] " + std::get<2>(entry));
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
    objs_.StoreCallable(ObjID::kBaEnvAtExitCall, *ctx.DictGetItem("atexit"));
    objs_.StoreCallable(ObjID::kBaEnvPreFinalizeCall,
                        *ctx.DictGetItem("pre_finalize"));
  }
}

void CorePython::UpdateInternalLoggerLevels(LogLevel* log_levels) {
  assert(python_logging_calls_enabled_);
  assert(Python::HaveGIL());

  const int log_level_not_set{0};
  const int log_level_debug{10};
  const int log_level_info{20};
  const int log_level_warning{30};
  const int log_level_error{40};
  const int log_level_critical{50};
  assert(log_level_not_set
         == objs().Get(ObjID::kLoggingLevelNotSet).ValueAsInt());
  assert(log_level_debug == objs().Get(ObjID::kLoggingLevelDebug).ValueAsInt());
  assert(log_level_info == objs().Get(ObjID::kLoggingLevelInfo).ValueAsInt());
  assert(log_level_warning
         == objs().Get(ObjID::kLoggingLevelWarning).ValueAsInt());
  assert(log_level_error == objs().Get(ObjID::kLoggingLevelError).ValueAsInt());
  assert(log_level_critical
         == objs().Get(ObjID::kLoggingLevelCritical).ValueAsInt());

  std::pair<LogName, ObjID> pairs[] = {
      {LogName::kRoot, ObjID::kLoggerRoot},
      {LogName::kBa, ObjID::kLoggerBa},
      {LogName::kBaApp, ObjID::kLoggerBaApp},
      {LogName::kBaAudio, ObjID::kLoggerBaAudio},
      {LogName::kBaGraphics, ObjID::kLoggerBaGraphics},
      {LogName::kBaPerformance, ObjID::kLoggerBaPerformance},
      {LogName::kBaDisplayTime, ObjID::kLoggerBaDisplayTime},
      {LogName::kBaLifecycle, ObjID::kLoggerBaLifecycle},
      {LogName::kBaAssets, ObjID::kLoggerBaAssets},
      {LogName::kBaInput, ObjID::kLoggerBaInput},
      {LogName::kBaNetworking, ObjID::kLoggerBaNetworking},
  };

  int count{};
  for (const auto& pair : pairs) {
    count++;
    auto logname{pair.first};
    auto objid{pair.second};
    auto out{objs().Get(objid).GetAttr("getEffectiveLevel").Call()};
    assert(out.exists());
    auto outval{static_cast<int>(out.ValueAsInt())};

    switch (outval) {
      // We ask for resolved level here so we normally shouldn't get NOTSET;
      // however if the root logger is set to that then we do. It means
      // don't apply filtering, so effectively its the same as debug for us.
      case log_level_not_set:
      case log_level_debug:
        log_levels[static_cast<int>(logname)] = LogLevel::kDebug;
        break;
      case log_level_info:
        log_levels[static_cast<int>(logname)] = LogLevel::kInfo;
        break;
      case log_level_warning:
        log_levels[static_cast<int>(logname)] = LogLevel::kWarning;
        break;
      case log_level_error:
        log_levels[static_cast<int>(logname)] = LogLevel::kError;
        break;
      case log_level_critical:
        log_levels[static_cast<int>(logname)] = LogLevel::kCritical;
        break;
      default:
        fprintf(stderr, "Found unexpected resolved logging level %d\n", outval);
    }
  }
  // Sanity check: Make sure we covered our full set of LogNames.
  if (count != static_cast<int>(LogName::kLast)) {
    fprintf(stderr,
            "WARNING: UpdateInternalLoggerLevels does not seem to be covering "
            "all log names.\n");
  }
}

void CorePython::SoftImportBase() {
  auto gil{Python::ScopedInterpreterLock()};
  auto result = PythonRef::StolenSoft(PyImport_ImportModule("_babase"));
  if (!result.exists()) {
    // Ignore any errors here for now. All that will matter is whether base
    // gave us its interface.
    PyErr_Clear();
  }
}

void CorePython::VerifyPythonEnvironment() {
  // Make sure we're running the Python version we require.
  const char* ver = Py_GetVersion();
  if (strncmp(ver, "3.13", 4) != 0) {
    FatalError("We require Python 3.13.x; instead found " + std::string(ver));
  }
}

void CorePython::MonolithicModeBaEnvConfigure() {
  assert(g_buildconfig.monolithic_build());
  assert(g_core);
  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "baenv.configure() begin");

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

  // Import and run baenv.configure() using our 'monolithic' default values
  // for all paths.
  std::optional<std::string> config_dir =
      g_core->platform->GetConfigDirectoryMonolithicDefault();
  std::string data_dir = g_core->platform->GetDataDirectoryMonolithicDefault();
  std::optional<std::string> user_python_dir =
      g_core->platform->GetUserPythonDirectoryMonolithicDefault();
  std::optional<std::string> cache_dir =
      g_core->platform->GetCacheDirectoryMonolithicDefault();

  // clang-format off
  auto kwargs =
    PythonRef::Stolen(Py_BuildValue(
      "{"
      "sO"  // config_dir
      "sO"  // data_dir
      "sO"  // cache_dir
      "sO"  // user_python_dir
      "sO"  // contains_python_dist
      "sO"  // strict_threads_atexit
      "sO"  // setup_pycache_prefix
      "}",
      "config_dir",
        config_dir ? *PythonRef::FromString(*config_dir) : Py_None,
      "data_dir",
        *PythonRef::FromString(data_dir),
      "cache_dir",
        cache_dir ? *PythonRef::FromString(*cache_dir) : Py_None,
      "user_python_dir",
        user_python_dir ? *PythonRef::FromString(*user_python_dir) : Py_None,
      "contains_python_dist",
        g_buildconfig.contains_python_dist() ? Py_True : Py_False,
      "strict_threads_atexit",
        *objs().Get(ObjID::kBaEnvAtExitCall),
      "setup_pycache_prefix",
        Py_True));
  // clang-format on

  auto result = objs()
                    .Get(ObjID::kBaEnvConfigureCall)
                    .Call(objs().Get(ObjID::kEmptyTuple), kwargs);
  if (!result.exists()) {
    FatalError("Environment setup failed (no error info available).");
  }
  if (result.ValueIsString()) {
    FatalError("Environment setup failed:\n" + result.ValueAsString());
  }
  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "baenv.configure() end");
}

void CorePython::LoggingCall(LogName logname, LogLevel loglevel,
                             const std::string& msg) {
  // If we're not yet sending logs to Python, store this one away until we
  // are.
  if (!python_logging_calls_enabled_) {
    std::scoped_lock lock(early_log_lock_);
    early_logs_.emplace_back(logname, loglevel, msg);

    // UPDATE - trying to disable this for now to make the concept of
    // delayed logs a bit less scary. Perhaps we can update fatal-error to
    // dump these or have a mode to immediate-print them as needed.
    if (explicit_bool(false)) {
      // There's a chance that we're going down in flames and this log might
      // be useful to see even if we never get a chance to chip it to
      // Python. So let's make an attempt to get it at least seen now in
      // whatever way we can. (platform display-log call and stderr).
      const char* errmsg{
          "CorePython::LoggingCall() called before Python logging "
          "available."};
      if (g_core->platform) {
        g_core->platform->EmitPlatformLog("root", LogLevel::kError, errmsg);
        g_core->platform->EmitPlatformLog("root", loglevel, msg);
      }
      fprintf(stderr, "%s\n%s\n", errmsg, msg.c_str());
    }
    return;
  }

  // Make sure we're good to go from any thread.
  Python::ScopedInterpreterLock lock;

  ObjID logcallobj;
  bool handled{};
  switch (logname) {
    case LogName::kRoot:
      logcallobj = ObjID::kLoggerRootLogCall;
      handled = true;
      break;
    case LogName::kBa:
      logcallobj = ObjID::kLoggerBaLogCall;
      handled = true;
      break;
    case LogName::kBaApp:
      logcallobj = ObjID::kLoggerBaAppLogCall;
      handled = true;
      break;
    case LogName::kBaAudio:
      logcallobj = ObjID::kLoggerBaAudioLogCall;
      handled = true;
      break;
    case LogName::kBaGraphics:
      logcallobj = ObjID::kLoggerBaGraphicsLogCall;
      handled = true;
      break;
    case LogName::kBaPerformance:
      logcallobj = ObjID::kLoggerBaPerformanceLogCall;
      handled = true;
      break;
    case LogName::kBaDisplayTime:
      logcallobj = ObjID::kLoggerBaDisplayTimeLogCall;
      handled = true;
      break;
    case LogName::kBaAssets:
      logcallobj = ObjID::kLoggerBaAssetsLogCall;
      handled = true;
      break;
    case LogName::kBaInput:
      logcallobj = ObjID::kLoggerBaInputLogCall;
      handled = true;
      break;
    case LogName::kBaNetworking:
      logcallobj = ObjID::kLoggerBaNetworkingLogCall;
      handled = true;
      break;
    case LogName::kBaLifecycle:
      logcallobj = ObjID::kLoggerBaLifecycleLogCall;
      handled = true;
      break;
    case LogName::kLast:
      logcallobj = ObjID::kLoggerRootLogCall;
      break;
  }
  // Handle this here instead of via default clause so we get warnings about
  // new unhandled enum values.
  if (!handled) {
    logcallobj = ObjID::kLoggerRootLogCall;
    fprintf(stderr, "Unexpected LogName %d\n", static_cast<int>(logname));
  }

  ObjID loglevelobjid;
  switch (loglevel) {
    case LogLevel::kDebug:
      loglevelobjid = ObjID::kLoggingLevelDebug;
      break;
    case LogLevel::kInfo:
      loglevelobjid = ObjID::kLoggingLevelInfo;
      break;
    case LogLevel::kWarning:
      loglevelobjid = ObjID::kLoggingLevelWarning;
      break;
    case LogLevel::kError:
      loglevelobjid = ObjID::kLoggingLevelError;
      break;
    case LogLevel::kCritical:
      loglevelobjid = ObjID::kLoggingLevelCritical;
      break;
    default:
      loglevelobjid = ObjID::kLoggingLevelInfo;
      fprintf(stderr, "Unexpected LogLevel %d\n", static_cast<int>(loglevel));
      break;
  }
  PythonRef args(
      Py_BuildValue("(Os)", objs().Get(loglevelobjid).get(), msg.c_str()),
      PythonRef::kSteal);
  objs().Get(logcallobj).Call(args);
}

auto CorePython::WasModularMainCalled() -> bool {
  assert(!g_buildconfig.monolithic_build());

  // This gets called in modular builds before anything is inited, so we need
  // to avoid using anything from g_core or whatnot here; only raw Python
  // stuff.

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
  // This gets called in modular builds before anything is inited, so we need
  // to avoid using anything from g_core or whatnot here; only raw Python
  // stuff.

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
