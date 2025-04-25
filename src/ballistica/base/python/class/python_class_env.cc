// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_env.h"

#include <map>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/core/platform/core_platform.h"

namespace ballistica::base {

struct EnvEntry_ {
  PyObject* obj;
  const char* typestr;
  const char* docs;
};

static std::map<std::string, EnvEntry_>* g_entries_{};

auto PythonClassEnv::type_name() -> const char* { return "Env"; }

static auto BoolEntry_(bool val, const char* docs) -> EnvEntry_ {
  PyObject* pyval = val ? Py_True : Py_False;
  Py_INCREF(pyval);
  return {pyval, "bool", docs};
}

static auto StrEntry_(const char* val, const char* docs) -> EnvEntry_ {
  return {PyUnicode_FromString(val), "str", docs};
}

static auto OptionalStrEntry_(const char* val, const char* docs) -> EnvEntry_ {
  if (val) {
    return {PyUnicode_FromString(val), "str | None", docs};
  } else {
    Py_INCREF(Py_None);
    return {Py_None, "str | None", docs};
  }
}

static auto IntEntry_(int val, const char* docs) -> EnvEntry_ {
  return {PyLong_FromLong(val), "int", docs};
}

void PythonClassEnv::SetupType(PyTypeObject* cls) {
  // Dynamically allocate this since Python needs to keep it around.
  auto* docsptr = new std::string(
      "Unchanging values for the current running app instance.\n"
      "Access the single shared instance of this class through the\n"
      ":attr:`~babase.App.env` attr on the :class:`~babase.App` class.\n"
      "\n"
      "Attributes:\n");
  auto& docs{*docsptr};

  // Populate our static entries dict. We'll generate Python class docs
  // from that so we don't have to manually keep doc strings in sync.
  assert(!g_entries_);
  assert(Python::HaveGIL());
  g_entries_ = new std::map<std::string, EnvEntry_>();
  auto& envs{*g_entries_};

  envs["android"] = BoolEntry_(g_buildconfig.ostype_android(),
                               "Is this build targeting an Android based OS?");

  envs["engine_build_number"] = IntEntry_(
      kEngineBuildNumber,
      "Integer build number for the engine.\n"
      "\n"
      "This value increases by at least 1 with each release of the engine.\n"
      "It is independent of the human readable `version` string.");

  envs["engine_version"] = StrEntry_(
      kEngineVersion,
      "Human-readable version string for the engine; something like '1.3.24'.\n"
      "\n"
      "This should not be interpreted as a number; it may contain\n"
      "string elements such as 'alpha', 'beta', 'test', etc.\n"
      "If a numeric version is needed, use `build_number`.");

  envs["device_name"] =
      StrEntry_(g_core->platform->GetDeviceName().c_str(),
                "Human readable name of the device running this app.");

  envs["supports_soft_quit"] = BoolEntry_(
      g_buildconfig.ostype_android() || g_buildconfig.ostype_ios_tvos(),
      "Whether the running app supports 'soft' quit options.\n"
      "\n"
      "This generally applies to mobile derived OSs, where an act of\n"
      "'quitting' may leave the app running in the background waiting\n"
      "in case it is used again.");

  envs["debug"] = BoolEntry_(
      g_buildconfig.debug_build(),
      "Whether the app is running in debug mode.\n"
      "\n"
      "Debug builds generally run substantially slower than non-debug\n"
      "builds due to compiler optimizations being disabled and extra\n"
      "checks being run.");

  envs["test"] = BoolEntry_(
      g_buildconfig.test_build(),
      "Whether the app is running in test mode.\n"
      "\n"
      "Test mode enables extra checks and features that are useful for\n"
      "release testing but which do not slow the game down significantly.");

  envs["config_file_path"] =
      StrEntry_(g_core->platform->GetConfigFilePath().c_str(),
                "Where the app's config file is stored on disk.");

  envs["data_directory"] = StrEntry_(g_core->GetDataDirectory().c_str(),
                                     "Where bundled static app data lives.");

  envs["api_version"] = IntEntry_(
      kEngineApiVersion,
      "The app's api version.\n"
      "\n"
      "Only Python modules and packages associated with the current API\n"
      "version number will be detected by the game (see the\n"
      ":class:`babase.MetadataSubsystem`). This value will change whenever\n"
      "substantial backward-incompatible changes are introduced to\n"
      "Ballistica APIs. When that happens, modules/packages should be updated\n"
      "accordingly and set to target the newer API version number.");

  std::optional<std::string> user_py_dir = g_core->GetUserPythonDirectory();
  envs["python_directory_user"] = OptionalStrEntry_(
      user_py_dir ? user_py_dir->c_str() : nullptr,
      "Path where the app expects its user scripts (mods) to live.\n"
      "\n"
      "Be aware that this value may be None if Ballistica is running in\n"
      "a non-standard environment, and that python-path modifications may\n"
      "cause modules to be loaded from other locations.");

  std::optional<std::string> app_py_dir = g_core->GetAppPythonDirectory();
  envs["python_directory_app"] = OptionalStrEntry_(
      app_py_dir ? app_py_dir->c_str() : nullptr,
      "Path where the app expects its bundled modules to live.\n"
      "\n"
      "Be aware that this value may be None if Ballistica is running in\n"
      "a non-standard environment, and that python-path modifications may\n"
      "cause modules to be loaded from other locations.");

  std::optional<std::string> site_py_dir = g_core->GetSitePythonDirectory();
  envs["python_directory_app_site"] = OptionalStrEntry_(
      site_py_dir ? site_py_dir->c_str() : nullptr,
      "Path where the app expects its bundled pip modules to live.\n"
      "\n"
      "Be aware that this value may be None if Ballistica is running in\n"
      "a non-standard environment, and that python-path modifications may\n"
      "cause modules to be loaded from other locations.");

  envs["tv"] =
      BoolEntry_(g_core->platform->IsRunningOnTV(),
                 "Whether the app is targeting a TV-centric experience.");

  envs["vr"] = BoolEntry_(g_core->vr_mode(),
                          "Whether the app is currently running in VR.");

  envs["arcade"] =
      BoolEntry_(g_buildconfig.arcade_build(),
                 "Whether the app is targeting an arcade-centric experience.");

  envs["headless"] =
      BoolEntry_(g_buildconfig.headless_build(),
                 "Whether the app is running headlessly (without a gui).\n"
                 "\n"
                 "This is the opposite of `gui`.");

  envs["gui"] = BoolEntry_(!g_buildconfig.headless_build(),
                           "Whether the app is running with a gui.\n"
                           "\n"
                           "This is the opposite of `headless`.");

  envs["demo"] = BoolEntry_(g_buildconfig.demo_build(),
                            "Whether the app is targeting a demo experience.");

  bool first = true;
  for (auto&& entry : envs) {
    if (!first) {
      docs += "\n";
    }
    docs += "   " + entry.first + " (" + entry.second.typestr + "):\n      "
            + entry.second.docs + "\n";
    first = false;
  }

  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.Env";
  cls->tp_basicsize = sizeof(PythonClassEnv);
  cls->tp_doc = docs.c_str();
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_getattro = (getattrofunc)tp_getattro;
  cls->tp_methods = tp_methods;
}

auto PythonClassEnv::tp_new(PyTypeObject* type, PyObject* args,
                            PyObject* keywds) -> PyObject* {
  auto* self = type->tp_alloc(type, 0);
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  // Using placement new here. Remember that this means we can be destructed
  // in any thread. If that's a problem we need to move to manual
  // allocation/deallocation so we can push deallocation to a specific
  // thread.
  new (self) PythonClassEnv();
  return self;
  BA_PYTHON_NEW_CATCH;
}

void PythonClassEnv::tp_dealloc(PythonClassEnv* self) {
  BA_PYTHON_TRY;
  self->~PythonClassEnv();
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassEnv::tp_getattro(PythonClassEnv* self, PyObject* attr)
    -> PyObject* {
  BA_PYTHON_TRY;

  // Do we need to support other attr types?
  assert(PyUnicode_Check(attr));

  auto&& entry = (*g_entries_).find(PyUnicode_AsUTF8(attr));
  if (entry != g_entries_->end()) {
    Py_INCREF(entry->second.obj);
    return entry->second.obj;
  } else {
    return PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  }
  BA_PYTHON_CATCH;
}

PythonClassEnv::PythonClassEnv() = default;

PythonClassEnv::~PythonClassEnv() = default;

auto PythonClassEnv::Dir(PythonClassEnv* self) -> PyObject* {
  BA_PYTHON_TRY;

  // Start with the standard Python dir listing.
  PyObject* dir_list = Python::generic_dir(reinterpret_cast<PyObject*>(self));
  assert(PyList_Check(dir_list));

  assert(g_entries_);

  // ..and add in our custom attr names.
  for (auto&& env : *g_entries_) {
    PyList_Append(dir_list, PythonRef(PyUnicode_FromString(env.first.c_str()),
                                      PythonRef::kSteal)
                                .get());
  }
  PyList_Sort(dir_list);
  return dir_list;

  BA_PYTHON_CATCH;
}

PyTypeObject PythonClassEnv::type_obj;

// Any methods for our class go here.
PyMethodDef PythonClassEnv::tp_methods[] = {
    {"__dir__", (PyCFunction)Dir, METH_NOARGS,
     "allows inclusion of our custom attrs in standard python dir()"},
    {nullptr}};

}  // namespace ballistica::base
