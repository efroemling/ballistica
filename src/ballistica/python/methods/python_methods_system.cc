// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_system.h"

#include <algorithm>
#include <list>
#include <string>
#include <unordered_map>

#include "ballistica/app/app.h"
#include "ballistica/app/app_config.h"
#include "ballistica/app/app_globals.h"
#include "ballistica/game/game_stream.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/game/session/replay_client_session.h"
#include "ballistica/graphics/camera.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/input/input.h"
#include "ballistica/media/component/texture.h"
#include "ballistica/media/media.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_context_call_runnable.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

// Ignore signed bitwise warnings; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

auto PyIsRunningOnOuya(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("is_running_on_ouya");
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PySetUpSigInt(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_up_sig_int");
  if (g_app) {
    g_app->PushInterruptSignalSetupCall();
  } else {
    Log("SigInt handler called before g_app exists.");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIsRunningOnFireTV(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("is_running_on_fire_tv");
  if (g_platform->IsRunningOnFireTV()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyHavePermission(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("have_permission");
  BA_PRECONDITION(InGameThread());
  Permission permission;
  PyObject* permission_obj;
  static const char* kwlist[] = {"permission", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &permission_obj)) {
    return nullptr;
  }

  permission = Python::GetPyEnum_Permission(permission_obj);

  if (g_platform->HavePermission(permission)) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyRequestPermission(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("request_permission");
  BA_PRECONDITION(InGameThread());
  Permission permission;
  PyObject* permission_obj;
  static const char* kwlist[] = {"permission", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "O", const_cast<char**>(kwlist), &permission_obj)) {
    return nullptr;
  }

  permission = Python::GetPyEnum_Permission(permission_obj);
  g_platform->RequestPermission(permission);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyInGameThread(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("in_game_thread");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  if (InGameThread()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PySetThreadName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_thread_name");
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  g_platform->SetCurrentThreadName(name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetThreadName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_thread_name");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(GetCurrentThreadName().c_str());
  BA_PYTHON_CATCH;
}

// returns an extra hash value that can be incorporated into security checks;
// this contains things like whether console commands have been run, etc.
auto PyExtraHashValue(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("extra_hash_value");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  const char* h = (g_app_globals->user_ran_commands ? "cjief3l" : "wofocj8");
  return PyUnicode_FromString(h);
  BA_PYTHON_CATCH;
}

auto PySetHaveMods(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_have_mods");
  int have_mods;
  if (!PyArg_ParseTuple(args, "p", &have_mods)) return nullptr;
  g_app_globals->have_mods = static_cast<bool>(have_mods);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetIdleTime(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_idle_time");
  return PyLong_FromLong(static_cast_check_fit<long>(  // NOLINT
      g_input ? g_input->input_idle_time() : 0));
  BA_PYTHON_CATCH;
}

auto PyHasUserRunCommands(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("has_user_run_commands");
  if (g_app_globals->user_ran_commands) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyHasUserMods(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("has_user_mods");
  if (g_app_globals->have_mods) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyValueTest(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("value_test");
  const char* arg;
  double change = 0.0f;
  double absolute = 0.0f;
  bool have_change = false;
  bool have_absolute = false;
  PyObject* change_obj = Py_None;
  PyObject* absolute_obj = Py_None;
  static const char* kwlist[] = {"arg", "change", "absolute", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s|OO",
                                   const_cast<char**>(kwlist), &arg,
                                   &change_obj, &absolute_obj)) {
    return nullptr;
  }
  if (change_obj != Py_None) {
    if (absolute_obj != Py_None) {
      throw Exception("Can't provide both a change and absolute");
    }
    have_change = true;
    change = Python::GetPyDouble(change_obj);
  }
  if (absolute_obj != Py_None) {
    have_absolute = true;
    absolute = Python::GetPyDouble(absolute_obj);
  }
  double return_val = 0.0f;
  if (!strcmp(arg, "bufferTime")) {
    if (have_change) {
      g_app_globals->buffer_time += static_cast<int>(change);
    }
    if (have_absolute) {
      g_app_globals->buffer_time = static_cast<int>(absolute);
    }
    g_app_globals->buffer_time = std::max(0, g_app_globals->buffer_time);
    return_val = g_app_globals->buffer_time;
  } else if (!strcmp(arg, "delaySampling")) {
    if (have_change) {
      g_app_globals->delay_samples += static_cast<int>(change);
    }
    if (have_absolute) {
      g_app_globals->buffer_time = static_cast<int>(absolute);
    }
    g_app_globals->delay_samples = std::max(1, g_app_globals->delay_samples);
    return_val = g_app_globals->delay_samples;
  } else if (!strcmp(arg, "dynamicsSyncTime")) {
    if (have_change) {
      g_app_globals->dynamics_sync_time += static_cast<int>(change);
    }
    if (have_absolute) {
      g_app_globals->dynamics_sync_time = static_cast<int>(absolute);
    }
    g_app_globals->dynamics_sync_time =
        std::max(0, g_app_globals->dynamics_sync_time);
    return_val = g_app_globals->dynamics_sync_time;
  } else if (!strcmp(arg, "showNetInfo")) {
    if (have_change && change > 0.5f) {
      g_graphics->set_show_net_info(true);
    }
    if (have_change && change < -0.5f) {
      g_graphics->set_show_net_info(false);
    }
    if (have_absolute) {
      g_graphics->set_show_net_info(static_cast<bool>(absolute));
    }
    return_val = g_graphics->show_net_info();
  } else if (!strcmp(arg, "allowCameraMovement")) {
    Camera* camera = g_graphics->camera();
    if (camera) {
      if (have_change && change > 0.5f) {
        camera->set_lock_panning(false);
      }
      if (have_change && change < -0.5f) {
        camera->set_lock_panning(true);
      }
      if (have_absolute) {
        camera->set_lock_panning(!static_cast<bool>(absolute));
      }
      return_val = !camera->lock_panning();
    }
  } else if (!strcmp(arg, "cameraPanSpeedScale")) {
    Camera* camera = g_graphics->camera();
    if (camera) {
      double val = camera->pan_speed_scale();
      if (have_change) {
        camera->set_pan_speed_scale(static_cast<float>(val + change));
      }
      if (have_absolute) {
        camera->set_pan_speed_scale(static_cast<float>(absolute));
      }
      if (camera->pan_speed_scale() < 0) {
        camera->set_pan_speed_scale(0);
      }
      return_val = camera->pan_speed_scale();
    }
  } else {
    auto handled =
        g_graphics->ValueTest(arg, have_absolute ? &absolute : nullptr,
                              have_change ? &change : nullptr, &return_val);
    if (!handled) {
      ScreenMessage("invalid arg: " + std::string(arg));
    }
  }

  return PyFloat_FromDouble(return_val);

  BA_PYTHON_CATCH;
}

auto PyDebugPrintPyErr(PyObject* self, PyObject* args) -> PyObject* {
  Platform::SetLastPyCall("debug_print_py_err");
  if (PyErr_Occurred()) {
    // we pass zero here to avoid grabbing references to this exception
    // which can cause objects to stick around and trip up our deletion checks
    // (nodes, actors existing after their games have ended)
    PyErr_PrintEx(0);
    PyErr_Clear();
  }
  Py_RETURN_NONE;
}

auto PyPrintContext(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("print_context");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  Python::LogContextAuto();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyPrintLoadInfo(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("print_load_info");
  g_media->PrintLoadInfo();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetReplaysDir(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_replays_dir");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return PyUnicode_FromString(g_platform->GetReplaysDir().c_str());
  BA_PYTHON_CATCH;
}

auto PyGetAppConfigDefaultValue(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_app_config_default_value");
  const char* key = "";
  static const char* kwlist[] = {"key", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &key)) {
    return nullptr;
  }
  const AppConfig::Entry* entry = g_app_config->GetEntry(key);
  if (entry == nullptr) {
    throw Exception("Invalid config value '" + std::string(key) + "'",
                    PyExcType::kValue);
  }
  switch (entry->GetType()) {
    case AppConfig::Entry::Type::kString:
      return PyUnicode_FromString(entry->DefaultStringValue().c_str());
    case AppConfig::Entry::Type::kInt:
      return PyLong_FromLong(entry->DefaultIntValue());
    case AppConfig::Entry::Type::kFloat:
      return PyFloat_FromDouble(entry->DefaultFloatValue());
    case AppConfig::Entry::Type::kBool:
      if (entry->DefaultBoolValue()) {
        Py_RETURN_TRUE;
      }
      Py_RETURN_FALSE;
    default:
      throw Exception(PyExcType::kValue);
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyAppConfigGetBuiltinKeys(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("app_config_get_builtin_keys");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  PythonRef list(PyList_New(0), PythonRef::kSteal);
  for (auto&& i : g_app_config->entries_by_name()) {
    PyList_Append(list.get(), PyUnicode_FromString(i.first.c_str()));
  }
  return list.HandOver();
  BA_PYTHON_CATCH;
}

auto PyResolveAppConfigValue(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("resolve_app_config_value");

  const char* key;
  static const char* kwlist[] = {"key", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &key)) {
    return nullptr;
  }
  auto entry = g_app_config->GetEntry(key);
  if (entry == nullptr) {
    throw Exception("Invalid config value '" + std::string(key) + "'.",
                    PyExcType::kValue);
  }
  switch (entry->GetType()) {
    case AppConfig::Entry::Type::kString:
      return PyUnicode_FromString(entry->StringValue().c_str());
    case AppConfig::Entry::Type::kInt:
      return PyLong_FromLong(entry->IntValue());
    case AppConfig::Entry::Type::kFloat:
      return PyFloat_FromDouble(entry->FloatValue());
    case AppConfig::Entry::Type::kBool:
      if (entry->BoolValue()) {
        Py_RETURN_TRUE;
      }
      Py_RETURN_FALSE;

    default:
      throw Exception(PyExcType::kValue);
  }
  BA_PYTHON_CATCH;
}

auto PyGetLowLevelConfigValue(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_low_level_config_value");
  const char* key;
  int default_value;
  static const char* kwlist[] = {"key", "default_value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "si", const_cast<char**>(kwlist), &key, &default_value))
    return nullptr;
  return PyLong_FromLong(
      g_platform->GetLowLevelConfigValue(key, default_value));
  BA_PYTHON_CATCH;
}

auto PySetLowLevelConfigValue(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_low_level_config_value");
  const char* key;
  int value;
  static const char* kwlist[] = {"key", "value", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "si",
                                   const_cast<char**>(kwlist), &key, &value))
    return nullptr;
  g_platform->SetLowLevelConfigValue(key, value);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPlatformMiscReadVals(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_platform_misc_read_vals");
  PyObject* vals_obj;
  static const char* kwlist[] = {"mode", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &vals_obj)) {
    return nullptr;
  }
  std::string vals = Python::GetPyString(vals_obj);
  g_platform->SetPlatformMiscReadVals(vals);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetLogFilePath(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_log_file_path");
  std::string config_dir = g_platform->GetConfigDirectory();
  std::string logpath = config_dir + BA_DIRSLASH + "log.json";
  return PyUnicode_FromString(logpath.c_str());
  BA_PYTHON_CATCH;
}

auto PyIsLogFull(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("is_log_full");
  if (g_app_globals->log_full) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyGetLog(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_log");
  std::string log_fin;
  {
    std::lock_guard<std::mutex> lock(g_app_globals->log_mutex);
    log_fin = g_app_globals->log;
  }
  // we want to use something with error handling here since the last
  // bit of this string could be truncated utf8 chars..
  return PyUnicode_FromString(
      Utils::GetValidUTF8(log_fin.c_str(), "_glg1").c_str());
  BA_PYTHON_CATCH;
}

auto PyMarkLogSent(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("mark_log_sent");
  // this way we won't try to send it at shutdown time and whatnot
  g_app_globals->put_log = true;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIncrementAnalyticsCount(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("increment_analytics_count");
  const char* name;
  int increment = 1;
  static const char* kwlist[] = {"name", "increment", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|p", const_cast<char**>(kwlist), &name, &increment)) {
    return nullptr;
  }
  g_platform->IncrementAnalyticsCount(name, increment);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIncrementAnalyticsCountRaw(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("increment_analytics_count_raw");
  const char* name;
  int increment = 1;
  static const char* kwlist[] = {"name", "increment", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "s|i", const_cast<char**>(kwlist), &name, &increment)) {
    return nullptr;
  }
  g_platform->IncrementAnalyticsCountRaw(name, increment);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIncrementAnalyticsCountRaw2(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("increment_analytics_count_raw2");
  const char* name;
  int uses_increment = 1;
  int increment = 1;
  static const char* kwlist[] = {"name", "uses_increment", "increment",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s|ii",
                                   const_cast<char**>(kwlist), &name,
                                   &uses_increment, &increment)) {
    return nullptr;
  }
  g_platform->IncrementAnalyticsCountRaw2(name, uses_increment, increment);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySubmitAnalyticsCounts(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("submit_analytics_counts");
  g_platform->SubmitAnalyticsCounts();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetAnalyticsScreen(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_analytics_screen");
  const char* screen;
  static const char* kwlist[] = {"screen", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &screen)) {
    return nullptr;
  }
  g_platform->SetAnalyticsScreen(screen);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetInternalLanguageKeys(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_internal_language_keys");
  PyObject* list_obj;
  PyObject* random_names_list_obj;
  if (!PyArg_ParseTuple(args, "OO", &list_obj, &random_names_list_obj)) {
    return nullptr;
  }
  BA_PRECONDITION(PyList_Check(list_obj));
  BA_PRECONDITION(PyList_Check(random_names_list_obj));
  std::unordered_map<std::string, std::string> language;
  int size = static_cast<int>(PyList_GET_SIZE(list_obj));
  for (int i = 0; i < size; i++) {
    PyObject* entry = PyList_GET_ITEM(list_obj, i);
    if (!PyTuple_Check(entry) || PyTuple_GET_SIZE(entry) != 2
        || !PyUnicode_Check(PyTuple_GET_ITEM(entry, 0))
        || !PyUnicode_Check(PyTuple_GET_ITEM(entry, 1))) {
      throw Exception("Invalid root language data.");
    }
    language[PyUnicode_AsUTF8(PyTuple_GET_ITEM(entry, 0))] =
        PyUnicode_AsUTF8(PyTuple_GET_ITEM(entry, 1));
  }
  size = static_cast<int>(PyList_GET_SIZE(random_names_list_obj));
  std::list<std::string> random_names;
  for (int i = 0; i < size; i++) {
    PyObject* entry = PyList_GET_ITEM(random_names_list_obj, i);
    if (!PyUnicode_Check(entry)) {
      throw Exception("Got non-string in random name list.", PyExcType::kType);
    }
    random_names.emplace_back(PyUnicode_AsUTF8(entry));
  }
  Utils::SetRandomNameList(random_names);
  assert(g_game);
  g_game->SetLanguageKeys(language);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyIsOuyaBuild(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("is_ouya_builds");
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyAndroidMediaScanFile(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("android_media_scan_file");
  const char* file_name;
  static const char* kwlist[] = {"file_name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &file_name)) {
    return nullptr;
  }
  g_platform->AndroidRefreshFile(file_name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyAndroidGetExternalStoragePath(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("android_get_external_storage_path");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
#if BA_OSTYPE_ANDROID
  std::string path = g_platform->GetExternalStoragePath();
  if (path.empty()) {
    Py_RETURN_NONE;
  } else {
    assert(Utils::IsValidUTF8(path));
    return PyUnicode_FromString(path.c_str());
  }
#else   // BA_OSTYPE_ANDROID
  throw Exception("Only valid on android.");
#endif  // BA_OSTYPE_ANDROID
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyAndroidShowWifiSettings(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("android_show_wifi_settings");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_platform->AndroidShowWifiSettings();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyPrintObjects(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("print_objects");
  Object::PrintObjects();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyDoOnce(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("do_once");
  if (g_python->DoOnce()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PyApp(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("app");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  return g_python->obj(Python::ObjID::kApp).NewRef();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonMethodsSystem::GetMethods() -> std::vector<PyMethodDef> {
  return {
      {"printobjects", (PyCFunction)PyPrintObjects,
       METH_VARARGS | METH_KEYWORDS,
       "printobjects() -> None\n"
       "\n"
       "Print debugging info about game objects.\n"
       "\n"
       "Category: General Utility Functions\n"
       "\n"
       "This call only functions in debug builds of the game.\n"
       "It prints various info about the current object count, etc."},

      {"do_once", (PyCFunction)PyDoOnce, METH_VARARGS | METH_KEYWORDS,
       "do_once() -> bool\n"
       "\n"
       "Return whether this is the first time running a line of code.\n"
       "\n"
       "Category: General Utility Functions\n"
       "\n"
       "This is used by 'print_once()' type calls to keep from overflowing\n"
       "logs. The call functions by registering the filename and line where\n"
       "The call is made from.  Returns True if this location has not been\n"
       "registered already, and False if it has.\n"
       "\n"
       "# Example: this print will only fire for the first loop iteration:\n"
       "for i in range(10):\n"
       "    if ba.do_once():\n"
       "        print('Hello once from loop!')"},

      {"_app", (PyCFunction)PyApp, METH_VARARGS | METH_KEYWORDS,
       "_app() -> ba.App\n"
       "\n"
       "(internal)"},

      {"android_media_scan_file", (PyCFunction)PyAndroidMediaScanFile,
       METH_VARARGS | METH_KEYWORDS,
       "android_media_scan_file(file_name: str) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Refreshes Android MTP Index for a file; use this to get file\n"
       "modifications to be reflected in Android File Transfer."},

      {"android_get_external_storage_path",
       (PyCFunction)PyAndroidGetExternalStoragePath,
       METH_VARARGS | METH_KEYWORDS,
       "android_get_external_storage_path() -> str\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns the android external storage path, or None if there is none "
       "on\n"
       "this device"},

      {"android_show_wifi_settings", (PyCFunction)PyAndroidShowWifiSettings,
       METH_VARARGS | METH_KEYWORDS,
       "android_show_wifi_settings() -> None\n"
       "\n"
       "(internal)"},

      {"is_ouya_build", PyIsOuyaBuild, METH_VARARGS,
       "is_ouya_build() -> bool\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns whether we're running the ouya-specific version"},

      {"set_internal_language_keys", PySetInternalLanguageKeys, METH_VARARGS,
       "set_internal_language_keys(listobj: List[Tuple[str, str]],\n"
       "  random_names_list: List[Tuple[str, str]]) -> None\n"
       "\n"
       "(internal)"},

      {"set_analytics_screen", (PyCFunction)PySetAnalyticsScreen,
       METH_VARARGS | METH_KEYWORDS,
       "set_analytics_screen(screen: str) -> None\n"
       "\n"
       "Used for analytics to see where in the app players spend their time.\n"
       "\n"
       "Category: General Utility Functions\n"
       "\n"
       "Generally called when opening a new window or entering some UI.\n"
       "'screen' should be a string description of an app location\n"
       "('Main Menu', etc.)"},

      {"submit_analytics_counts", (PyCFunction)PySubmitAnalyticsCounts,
       METH_VARARGS | METH_KEYWORDS,
       "submit_analytics_counts() -> None\n"
       "\n"
       "(internal)"},

      {"increment_analytics_count_raw_2",
       (PyCFunction)PyIncrementAnalyticsCountRaw2, METH_VARARGS | METH_KEYWORDS,
       "increment_analytics_count_raw_2(name: str,\n"
       "  uses_increment: bool = True, increment: int = 1) -> None\n"
       "\n"
       "(internal)"},

      {"increment_analytics_counts_raw",
       (PyCFunction)PyIncrementAnalyticsCountRaw, METH_VARARGS | METH_KEYWORDS,
       "increment_analytics_counts_raw(name: str, increment: int = 1) -> None\n"
       "\n"
       "(internal)"},

      {"increment_analytics_count", (PyCFunction)PyIncrementAnalyticsCount,
       METH_VARARGS | METH_KEYWORDS,
       "increment_analytics_count(name: str, increment: int = 1) -> None\n"
       "\n"
       "(internal)"},

      {"mark_log_sent", (PyCFunction)PyMarkLogSent,
       METH_VARARGS | METH_KEYWORDS,
       "mark_log_sent() -> None\n"
       "\n"
       "(internal)"},

      {"getlog", (PyCFunction)PyGetLog, METH_VARARGS | METH_KEYWORDS,
       "getlog() -> str\n"
       "\n"
       "(internal)"},

      {"is_log_full", PyIsLogFull, METH_VARARGS,
       "is_log_full() -> bool\n"
       "\n"
       "(internal)"},

      {"get_log_file_path", PyGetLogFilePath, METH_VARARGS,
       "get_log_file_path() -> str\n"
       "\n"
       "(internal)\n"
       "\n"
       "Return the path to the app log file."},

      {"set_platform_misc_read_vals", (PyCFunction)PySetPlatformMiscReadVals,
       METH_VARARGS | METH_KEYWORDS,
       "set_platform_misc_read_vals(mode: str) -> None\n"
       "\n"
       "(internal)"},

      {"set_low_level_config_value", (PyCFunction)PySetLowLevelConfigValue,
       METH_VARARGS | METH_KEYWORDS,
       "set_low_level_config_value(key: str, value: int) -> None\n"
       "\n"
       "(internal)"},

      {"get_low_level_config_value", (PyCFunction)PyGetLowLevelConfigValue,
       METH_VARARGS | METH_KEYWORDS,
       "get_low_level_config_value(key: str, default_value: int) -> int\n"
       "\n"
       "(internal)"},

      {"resolve_appconfig_value", (PyCFunction)PyResolveAppConfigValue,
       METH_VARARGS | METH_KEYWORDS,
       "resolve_appconfig_value(key: str) -> Any\n"
       "\n"
       "(internal)"},

      {"get_appconfig_default_value", (PyCFunction)PyGetAppConfigDefaultValue,
       METH_VARARGS | METH_KEYWORDS,
       "get_appconfig_default_value(key: str) -> Any\n"
       "\n"
       "(internal)"},

      {"get_appconfig_builtin_keys", (PyCFunction)PyAppConfigGetBuiltinKeys,
       METH_VARARGS | METH_KEYWORDS,
       "get_appconfig_builtin_keys() -> List[str]\n"
       "\n"
       "(internal)"},

      {"get_replays_dir", (PyCFunction)PyGetReplaysDir,
       METH_VARARGS | METH_KEYWORDS,
       "get_replays_dir() -> str\n"
       "\n"
       "(internal)"},

      {"print_load_info", (PyCFunction)PyPrintLoadInfo,
       METH_VARARGS | METH_KEYWORDS,
       "print_load_info() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: General Utility Functions"},

      {"print_context", (PyCFunction)PyPrintContext,
       METH_VARARGS | METH_KEYWORDS,
       "print_context() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Prints info about the current context state; for debugging.\n"},

      {"debug_print_py_err", PyDebugPrintPyErr, METH_VARARGS,
       "debug_print_py_err() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Debugging func for tracking leaked Python errors in the C++ layer.."},

      {"value_test", (PyCFunction)PyValueTest, METH_VARARGS | METH_KEYWORDS,
       "value_test(arg: str, change: float = None, absolute: float = None)\n"
       "  -> float\n"
       "\n"
       "(internal)"},

      {"has_user_mods", PyHasUserMods, METH_VARARGS,
       "has_user_mods() -> bool\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns whether the system varies from default configuration\n"
       "(by user mods, etc)"},

      {"has_user_run_commands", PyHasUserRunCommands, METH_VARARGS,
       "has_user_run_commands() -> bool\n"
       "\n"
       "(internal)"},

      {"get_idle_time", PyGetIdleTime, METH_VARARGS,
       "get_idle_time() -> int\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns the amount of time since any game input has been received."},

      {"set_have_mods", PySetHaveMods, METH_VARARGS,
       "set_have_mods(have_mods: bool) -> None\n"
       "\n"
       "(internal)"},

      {"ehv", (PyCFunction)PyExtraHashValue, METH_VARARGS | METH_KEYWORDS,
       "ehv() -> None\n"
       "\n"
       "(internal)"},

      {"get_thread_name", (PyCFunction)PyGetThreadName,
       METH_VARARGS | METH_KEYWORDS,
       "get_thread_name() -> str\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns the name of the current thread.\n"
       "This may vary depending on platform and should not be used in logic;\n"
       "only for debugging."},

      {"set_thread_name", (PyCFunction)PySetThreadName,
       METH_VARARGS | METH_KEYWORDS,
       "set_thread_name(name: str) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Sets the name of the current thread (on platforms where this is\n"
       "available). Thread names are only for debugging and should not be\n"
       "used in logic, as naming behavior can vary across platforms.\n"},

      {"in_game_thread", (PyCFunction)PyInGameThread,
       METH_VARARGS | METH_KEYWORDS,
       "in_game_thread() -> bool\n"
       "\n"
       "(internal)\n"
       "\n"
       "Returns whether or not the current thread is the game thread."},

      {"request_permission", (PyCFunction)PyRequestPermission,
       METH_VARARGS | METH_KEYWORDS,
       "request_permission(permission: ba.Permission) -> None\n"
       "\n"
       "(internal)"},

      {"have_permission", (PyCFunction)PyHavePermission,
       METH_VARARGS | METH_KEYWORDS,
       "have_permission(permission: ba.Permission) -> bool\n"
       "\n"
       "(internal)"},

      {"is_running_on_fire_tv", PyIsRunningOnFireTV, METH_VARARGS,
       "is_running_on_fire_tv() -> bool\n"
       "\n"
       "(internal)"},

      {"is_running_on_ouya", PyIsRunningOnOuya, METH_VARARGS,
       "is_running_on_ouya() -> bool\n"
       "\n"
       "(internal)"},

      {"setup_sigint", (PyCFunction)PySetUpSigInt, METH_NOARGS,
       "setup_sigint() -> None\n"
       "\n"
       "(internal)"},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
