// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/base_python.h"

#include <string>
#include <vector>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/python/class/python_class_app_timer.h"
#include "ballistica/base/python/class/python_class_context_call.h"
#include "ballistica/base/python/class/python_class_context_ref.h"
#include "ballistica/base/python/class/python_class_display_timer.h"
#include "ballistica/base/python/class/python_class_env.h"
#include "ballistica/base/python/class/python_class_feature_set_data.h"
#include "ballistica/base/python/class/python_class_simple_sound.h"
#include "ballistica/base/python/class/python_class_vec3.h"
#include "ballistica/base/python/methods/python_methods_base_1.h"
#include "ballistica/base/python/methods/python_methods_base_2.h"
#include "ballistica/base/python/methods/python_methods_base_3.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/python/python_command.h"  // IWYU pragma: keep.
#include "ballistica/shared/python/python_module_builder.h"

namespace ballistica::base {

// Declare a plain c PyInit_XXX function for our Python module;
// this is how Python inits our binary module (and by extension, our
// entire feature-set).
extern "C" auto PyInit__babase() -> PyObject* {
  auto* builder =
      new PythonModuleBuilder("_babase",
                              {
                                  PythonMethodsBase1::GetMethods(),
                                  PythonMoethodsBase3::GetMethods(),
                                  PythonMethodsBase2::GetMethods(),
                              },
                              [](PyObject* module) -> int {
                                BA_PYTHON_TRY;
                                BaseFeatureSet::OnModuleExec(module);
                                return 0;
                                BA_PYTHON_INT_CATCH;
                              });
  return builder->Build();
}

BasePython::BasePython() = default;

void BasePython::AddPythonClasses(PyObject* module) {
  PythonModuleBuilder::AddClass<PythonClassFeatureSetData>(module);
  PythonModuleBuilder::AddClass<PythonClassContextRef>(module);
  PythonModuleBuilder::AddClass<PythonClassAppTimer>(module);
  PythonModuleBuilder::AddClass<PythonClassDisplayTimer>(module);
  PythonModuleBuilder::AddClass<PythonClassEnv>(module);
  PythonModuleBuilder::AddClass<PythonClassSimpleSound>(module);
  PythonModuleBuilder::AddClass<PythonClassContextCall>(module);
  PyObject* vec3 = PythonModuleBuilder::AddClass<PythonClassVec3>(module);
  // Register our Vec3 as an abc.Sequence
  // FIXME: should be able to do this in Python bootstrapping
  //  code.
  auto register_call =
      PythonRef::Stolen(PyImport_ImportModule("collections.abc"))
          .GetAttr("Sequence")
          .GetAttr("register");
  PythonRef args(Py_BuildValue("(O)", vec3), PythonRef::kSteal);
  BA_PRECONDITION(register_call.Call(args).exists());
}

void BasePython::ImportPythonObjs() {
  // Import and grab all the Python stuff we use from C++.
  // Note: Binding .inc files expect 'ObjID' and 'objs_' to be defined.
#include "ballistica/base/mgen/pyembed/binding_base.inc"

  // Grab and store our enum values for things like AppPlatform, AppVariant,
  // etc. from the enum types we just grabbed.

  // AppPlatform
  {
    const char* val = g_buildconfig.variant();
    auto args = PythonRef::Stolen(Py_BuildValue("(s)", val));
    auto result = objs_.Get(ObjID::kAppVariantType).Call(args);
    if (!result.exists()) {
      FatalError("Invalid AppVariant value: " + std::string(val));
    }
    objs_.Store(ObjID::kAppVariant, *result);
  }

  // AppArchitecture
  {
    const char* val = g_buildconfig.arch();
    auto args = PythonRef::Stolen(Py_BuildValue("(s)", val));
    auto result = objs_.Get(ObjID::kAppArchitectureType).Call(args);
    if (!result.exists()) {
      FatalError("Invalid AppArchitecture value: " + std::string(val));
    }
    objs_.Store(ObjID::kAppArchitecture, *result);
  }

  // AppPlatform
  {
    const char* val = g_buildconfig.platform();
    auto args = PythonRef::Stolen(Py_BuildValue("(s)", val));
    auto result = objs_.Get(ObjID::kAppPlatformType).Call(args);
    if (!result.exists()) {
      FatalError("Invalid AppPlatform value: " + std::string(val));
    }
    objs_.Store(ObjID::kAppPlatform, *result);
  }
}

void BasePython::ImportPythonAppObjs() {
  // Import and grab all the Python stuff we use from C++.
  // Note: Binding .inc files expect 'ObjID' and 'objs_' to be defined.
#include "ballistica/base/mgen/pyembed/binding_base_app.inc"
}

void BasePython::SoftImportPlus() {
  // To keep our init order clean, we want to root out any attempted uses
  // of this before _babase/babase has been fully imported.
  assert(g_base);
  assert(g_base->IsBaseCompletelyImported());

  auto gil{Python::ScopedInterpreterLock()};
  auto result = PythonRef::StolenSoft(PyImport_ImportModule("_baplus"));
  if (!result.exists()) {
    // Ignore any errors here for now. All that will matter is whether plus
    // gave us its interface.
    PyErr_Clear();
  }
}

void BasePython::SoftImportClassic() {
  // To keep our init order clean, we want to root out any attempted uses
  // of this before _babase/babase has been fully imported.
  assert(g_base);
  assert(g_base->IsBaseCompletelyImported());

  auto gil{Python::ScopedInterpreterLock()};
  auto result = PythonRef::StolenSoft(PyImport_ImportModule("_baclassic"));
  if (!result.exists()) {
    // Ignore any errors here for now. All that will matter is whether plus
    // gave us its interface.
    PyErr_Clear();
  }
}

void BasePython::SetConfig(PyObject* config) {
  objs_.Store(ObjID::kConfig, config);
}

void BasePython::Reset() {
  assert(g_base->InLogicThread());
  assert(g_base);
  // FIXME: This needs updating.
  g_base->graphics->ReleaseFadeEndCommand();
}

void BasePython::OnMainThreadStartApp() {
  auto gil{Python::ScopedInterpreterLock()};
  // Set up some env stuff (interrupt handlers, etc.)
  auto result = objs().Get(ObjID::kOnMainThreadStartAppCall).Call();
  if (!result.exists()) {
    FatalError("babase._env.on_main_thread_start_app() failed.");
  }
}

void BasePython::OnAppStart() {
  assert(g_base->InLogicThread());
  objs().Get(ObjID::kAppOnNativeStartCall).Call();
}

void BasePython::OnAppSuspend() {
  assert(g_base->InLogicThread());
  objs().Get(ObjID::kAppOnNativeSuspendCall).Call();
}

void BasePython::OnAppUnsuspend() {
  assert(g_base->InLogicThread());
  objs().Get(ObjID::kAppOnNativeUnsuspendCall).Call();
}

void BasePython::OnAppShutdown() {
  assert(g_base->InLogicThread());
  objs().Get(ObjID::kAppOnNativeShutdownCall).Call();
}

void BasePython::OnAppShutdownComplete() {
  assert(g_base->InLogicThread());
  objs().Get(ObjID::kAppOnNativeShutdownCompleteCall).Call();
}

void BasePython::ApplyAppConfig() { assert(g_base->InLogicThread()); }

void BasePython::OnScreenSizeChange() {
  assert(g_base->InLogicThread());

  float screen_res_x{g_base->graphics->screen_virtual_width()};
  float screen_res_y{g_base->graphics->screen_virtual_height()};

  // This call runs for all screen sizes including the initial one. However
  // we only want to inform the Python layer of *changes*, so we only store
  // the initial one and don't pass it on.
  if (last_screen_res_x_ < 0.0) {
    last_screen_res_x_ = screen_res_x;
    last_screen_res_y_ = g_base->graphics->screen_virtual_height();
    return;
  }

  // Ignore any redundant values that might come through.
  if (last_screen_res_x_ == screen_res_x
      && last_screen_res_y_ == screen_res_y) {
    return;
  }

  // Aight; we got a fresh, non-initial value. Store it and inform Python.
  last_screen_res_x_ = screen_res_x;
  last_screen_res_y_ = screen_res_y;

  objs().Get(ObjID::kAppOnScreenSizeChangeCall).Call();
}

void BasePython::StepDisplayTime() { assert(g_base->InLogicThread()); }

void BasePython::EnsureContextAllowsDefaultTimerTypes() {
  auto& cref = g_base->CurrentContext();
  if (auto* context = cref.Get()) {
    if (!context->ContextAllowsDefaultTimerTypes()) {
      throw Exception(
          "The current context does not allow creation of"
          " default timer types. There are probably timer types specific"
          " to the context that you should use instead (scene-timers, "
          "base-timers, etc.)");
    }
  }
}

void BasePython::OpenURLWithWebBrowserModule(const std::string& url) {
  // We need to be in the logic thread because our hook does sounds/messages
  // on errors.
  BA_PRECONDITION(g_base->InLogicThread());
  auto args = PythonRef::Stolen(Py_BuildValue("(s)", url.c_str()));
  objs().Get(ObjID::kOpenURLWithWebBrowserModuleCall).Call(args);
}

// Return whether GetPyLString() will succeed for an object.
auto BasePython::IsPyLString(PyObject* o) -> bool {
  assert(Python::HaveGIL());
  assert(o != nullptr);

  return (PyUnicode_Check(o)
          || PyObject_IsInstance(o, objs().Get(ObjID::kLStrClass).get()));
}

auto BasePython::GetPyLString(PyObject* o) -> std::string {
  assert(Python::HaveGIL());
  assert(o != nullptr);

  PyExcType exctype{PyExcType::kType};
  if (PyUnicode_Check(o)) {
    return PyUnicode_AsUTF8(o);
  } else {
    // Check if its a Lstr.  If so; we pull its json string representation.
    int result = PyObject_IsInstance(o, objs().Get(ObjID::kLStrClass).get());
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

auto BasePython::GetPyLStrings(PyObject* o) -> std::vector<std::string> {
  assert(Python::HaveGIL());
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
    vals[i] = GetPyLString(py_objects[i]);
  }
  return vals;
}

auto BasePython::CanGetPyVector3f(PyObject* o) -> bool {
  assert(Python::HaveGIL());
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
  return (Python::IsNumber(PySequence_Fast_GET_ITEM(sequence.get(), 0))
          && Python::IsNumber(PySequence_Fast_GET_ITEM(sequence.get(), 1))
          && Python::IsNumber(PySequence_Fast_GET_ITEM(sequence.get(), 2)));
}

auto BasePython::GetPyVector3f(PyObject* o) -> Vector3f {
  assert(Python::HaveGIL());
  BA_PRECONDITION_FATAL(o != nullptr);

  if (PythonClassVec3::Check(o)) {
    return (reinterpret_cast<PythonClassVec3*>(o))->value;
  }
  if (!PySequence_Check(o)) {
    throw Exception("Object is not a babase.Vec3 or sequence.",
                    PyExcType::kType);
  }
  PythonRef sequence(PySequence_Fast(o, "Not a sequence."), PythonRef::kSteal);
  assert(sequence.exists());  // Should always work; we checked seq.
  if (PySequence_Fast_GET_SIZE(sequence.get()) != 3) {
    throw Exception("Sequence is not of size 3.", PyExcType::kValue);
  }
  return {Python::GetFloat(PySequence_Fast_GET_ITEM(sequence.get(), 0)),
          Python::GetFloat(PySequence_Fast_GET_ITEM(sequence.get(), 1)),
          Python::GetFloat(PySequence_Fast_GET_ITEM(sequence.get(), 2))};
}

void BasePython::StoreEnv(PyObject* obj) { objs_.Store(ObjID::kEnv, obj); }
void BasePython::StorePreEnv(PyObject* obj) {
  objs_.Store(ObjID::kPreEnv, obj);
}

void BasePython::SetRawConfigValue(const char* name, float value) {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  PythonRef value_obj(PyFloat_FromDouble(value), PythonRef::kSteal);
  int result = PyDict_SetItemString(objs().Get(ObjID::kConfig).get(), name,
                                    value_obj.get());
  if (result == -1) {
    // Failed, we have. Clear any Python error that got us here; we're in
    // C++ Exception land now.
    PyErr_Clear();
    throw Exception("Error setting config dict value.");
  }
}

auto BasePython::GetRawConfigValue(const char* name) -> PyObject* {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  return PyDict_GetItemString(objs().Get(ObjID::kConfig).get(), name);
}

auto BasePython::GetRawConfigValue(const char* name, const char* default_value)
    -> std::string {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  PyObject* value =
      PyDict_GetItemString(objs().Get(ObjID::kConfig).get(), name);
  if (value == nullptr || !PyUnicode_Check(value)) {
    return default_value;
  }
  return PyUnicode_AsUTF8(value);
}

auto BasePython::GetRawConfigValue(const char* name, float default_value)
    -> float {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  PyObject* value =
      PyDict_GetItemString(objs().Get(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    return Python::GetFloat(value);
  } catch (const std::exception&) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "expected a float for config value '" + std::string(name) + "'");
    return default_value;
  }
}

auto BasePython::GetRawConfigValue(const char* name,
                                   std::optional<float> default_value)
    -> std::optional<float> {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  PyObject* value =
      PyDict_GetItemString(objs().Get(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    if (value == Py_None) {
      return {};
    }
    return Python::GetFloat(value);
  } catch (const std::exception&) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "expected a float for config value '" + std::string(name) + "'");
    return default_value;
  }
}

auto BasePython::GetRawConfigValue(const char* name, int default_value) -> int {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  PyObject* value =
      PyDict_GetItemString(objs().Get(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    return static_cast_check_fit<int>(Python::GetInt64(value));
  } catch (const std::exception&) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Expected an int value for config value '" + std::string(name) + "'.");
    return default_value;
  }
}

auto BasePython::GetRawConfigValue(const char* name, bool default_value)
    -> bool {
  assert(Python::HaveGIL());
  assert(objs().Exists(ObjID::kConfig));
  PyObject* value =
      PyDict_GetItemString(objs().Get(ObjID::kConfig).get(), name);
  if (value == nullptr) {
    return default_value;
  }
  try {
    return Python::GetBool(value);
  } catch (const std::exception&) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Expected a bool value for config value '" + std::string(name) + "'.");
    return default_value;
  }
}
template <typename T>
auto BasePython::IsPyEnum_(ObjID enum_class_id, PyObject* obj) -> bool {
  PyObject* enum_class_obj = objs().Get(enum_class_id).get();
  assert(enum_class_obj != nullptr && enum_class_obj != Py_None);
  return static_cast<bool>(PyObject_IsInstance(obj, enum_class_obj));
}

template <typename T>
auto BasePython::GetPyEnum_(ObjID enum_class_id, PyObject* obj) -> T {
  // First, make sure what they passed is an instance of the enum class
  // we want.
  PyObject* enum_class_obj = objs().Get(enum_class_id).get();
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

auto BasePython::GetPyEnum_Permission(PyObject* obj) -> Permission {
  return GetPyEnum_<Permission>(ObjID::kPermissionClass, obj);
}

auto BasePython::GetPyEnum_SpecialChar(PyObject* obj) -> SpecialChar {
  return GetPyEnum_<SpecialChar>(ObjID::kSpecialCharClass, obj);
}

auto BasePython::GetPyEnum_QuitType(PyObject* obj) -> QuitType {
  return GetPyEnum_<QuitType>(ObjID::kQuitTypeClass, obj);
}

auto BasePython::IsPyEnum_InputType(PyObject* obj) -> bool {
  return IsPyEnum_<InputType>(ObjID::kInputTypeClass, obj);
}

auto BasePython::GetPyEnum_InputType(PyObject* obj) -> InputType {
  return GetPyEnum_<InputType>(ObjID::kInputTypeClass, obj);
}

// TODO(ericf): Make this a template.
auto BasePython::PyQuitType(QuitType val) -> PythonRef {
  auto args = PythonRef::Stolen(Py_BuildValue("(i)", static_cast<int>(val)));
  auto out = objs().Get(ObjID::kQuitTypeClass).Call(args);
  BA_PRECONDITION(out.exists());
  return out;
}

auto BasePython::GetResource(const char* key, const char* fallback_resource,
                             const char* fallback_value) -> std::string {
  assert(Python::HaveGIL());
  PythonRef results;
  BA_PRECONDITION(key != nullptr);
  const PythonRef& get_resource_call(objs().Get(ObjID::kGetResourceCall));
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
      return GetPyLString(results.get());
    } catch (const std::exception&) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "GetResource failed for '" + std::string(key) + "'");

      // Hmm; I guess let's just return the key to help identify/fix the
      // issue?..
      return std::string("<res-err: ") + key + ">";
    }
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "GetResource failed for '" + std::string(key) + "'");
  }

  // Hmm; I guess let's just return the key to help identify/fix the issue?..
  return std::string("<res-err: ") + key + ">";
}

auto BasePython::GetTranslation(const char* category, const char* s)
    -> std::string {
  assert(Python::HaveGIL());
  PythonRef results;
  PythonRef args(Py_BuildValue("(ss)", category, s), PythonRef::kSteal);
  // Don't print errors.
  results = objs().Get(ObjID::kTranslateCall).Call(args, PythonRef(), false);
  if (results.exists()) {
    try {
      return GetPyLString(results.get());
    } catch (const std::exception&) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "GetTranslation failed for '" + std::string(category) + "'");
      return "";
    }
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "GetTranslation failed for category '" + std::string(category) + "'");
  }
  return "";
}

void BasePython::RunDeepLink(const std::string& url) {
  BA_PRECONDITION(g_base->InLogicThread());
  if (objs().Exists(ObjID::kAppHandleDeepLinkCall)) {
    ScopedSetContext ssc(nullptr);
    PythonRef args(Py_BuildValue("(s)", url.c_str()), PythonRef::kSteal);
    objs().Get(ObjID::kAppHandleDeepLinkCall).Call(args);
  } else {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error on deep-link call");
  }
}

auto BasePython::DoOnce() -> bool {
  std::string location = Python::GetPythonFileLocation(false);
  if (do_once_locations_.find(location) != do_once_locations_.end()) {
    return false;
  }
  do_once_locations_.insert(location);
  return true;
}

auto BasePython::CanPyStringEditAdapterBeReplaced(PyObject* o) -> bool {
  assert(g_base->InLogicThread());

  auto args = PythonRef::Stolen(Py_BuildValue("(O)", o));
  auto result =
      objs().Get(ObjID::kStringEditAdapterCanBeReplacedCall).Call(args);
  if (!result.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error getting StringEdit valid state.");
    return false;
  }
  if (result.get() == Py_True) {
    return true;
  }
  if (result.get() == Py_False) {
    return false;
  }
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       "Got unexpected value for StringEdit valid.");
  return false;
}

void BasePython::OnAppActiveChanged() {
  assert(g_base->InLogicThread());
  objs().Get(ObjID::kAppOnNativeActiveChangedCall).Call();
}

}  // namespace ballistica::base
