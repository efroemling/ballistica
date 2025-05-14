// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_env.h"

#include <map>
#include <memory>
#include <string>
#include <utility>

#include "ballistica/base/base.h"
#include "ballistica/base/platform/base_platform.h"
#include "ballistica/core/platform/core_platform.h"

namespace ballistica::base {

// Define a virtual base class we can make a map of.
//
// NOTE: We assume typestr and docs are statically allocated here so we
// only store pointers. Need to switch to std::string if this ever isn't
// true.
struct EnvEntryBase_ {
  virtual ~EnvEntryBase_() = default;
  virtual auto call() -> PyObject* = 0;
  EnvEntryBase_(const char* typestr, const char* docs)
      : typestr{typestr}, docs{docs} {}
  const char* typestr;
  const char* docs;
};

static std::map<std::string, std::unique_ptr<EnvEntryBase_>>* g_entries_{};

// Define a template subclass we can use to create our various entries.
template <typename L>
struct EnvEntry_ : EnvEntryBase_ {
  L getter;
  auto call() -> PyObject* override { return getter(); }
  EnvEntry_(L getter, const char* typestr, const char* docs)
      : EnvEntryBase_(typestr, docs), getter{std::move(getter)} {}
};

auto PythonClassEnv::type_name() -> const char* { return "Env"; }

static auto BoolEntry_(bool val, const char* docs)
    -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(new EnvEntry_(
      [val] {
        PyObject* pyval = val ? Py_True : Py_False;
        Py_INCREF(pyval);
        return pyval;
      },
      "bool", docs));
}

static auto StrEntry_(const std::string& val, const char* docs)
    -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(new EnvEntry_(
      [val] { return PyUnicode_FromString(val.c_str()); }, "str", docs));
}

static auto OptionalStrEntry_(const std::optional<std::string>& val,
                              const char* docs)
    -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(new EnvEntry_(
      [val] {
        if (val.has_value()) {
          return PyUnicode_FromString(val->c_str());
        } else {
          Py_INCREF(Py_None);
          return Py_None;
        }
      },
      "str | None", docs));
}

static auto IntEntry_(int val, const char* docs)
    -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(
      new EnvEntry_([val] { return PyLong_FromLong(val); }, "int", docs));
}

static auto AppArchitectureEntry_() -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(new EnvEntry_(
      [] {
        auto* val{g_base->platform->GetPyAppArchitecture()};
        Py_INCREF(val);
        return val;
      },
      "bacommon.app.AppArchitecture", "Architecture we are running on."));
}

static auto AppVariantEntry_() -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(new EnvEntry_(
      [] {
        auto* val{g_base->platform->GetPyAppVariant()};
        Py_INCREF(val);
        return val;
      },
      "bacommon.app.AppVariant", "App variant we are running."));
}

static auto AppPlatformEntry_() -> std::unique_ptr<EnvEntryBase_> {
  return std::unique_ptr<EnvEntryBase_>(new EnvEntry_(
      [] {
        auto* val{g_base->platform->GetPyAppPlatform()};
        Py_INCREF(val);
        return val;
      },
      "bacommon.app.AppPlatform", "Platform we are running on."));
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
  g_entries_ = new std::map<std::string, std::unique_ptr<EnvEntryBase_>>();
  auto& envs{*g_entries_};

  envs["android"] = BoolEntry_(g_buildconfig.platform_android(),
                               "Is this build targeting an Android based OS?");

  envs["engine_build_number"] = IntEntry_(
      kEngineBuildNumber,
      "Integer build number for the engine.\n"
      "\n"
      "This value increases by at least 1 with each release of the engine.\n"
      "It is independent of the human readable `version` string.");

  envs["engine_version"] =
      StrEntry_(kEngineVersion,
                "Human-readable version string for the engine; something "
                "like '1.3.24'.\n"
                "\n"
                "This should not be interpreted as a number; it may contain\n"
                "string elements such as 'alpha', 'beta', 'test', etc.\n"
                "If a numeric version is needed, use `build_number`.");

  envs["device_name"] =
      StrEntry_(g_core->platform->GetDeviceName(),
                "Human readable name of the device running this app.");

  envs["supports_soft_quit"] = BoolEntry_(
      g_buildconfig.platform_android() || g_buildconfig.platform_ios_tvos(),
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
      g_buildconfig.variant_test_build(),
      "Whether the app is running in test mode.\n"
      "\n"
      "Test mode enables extra checks and features that are useful for\n"
      "release testing but which do not slow the game down significantly.");

  envs["config_file_path"] =
      StrEntry_(g_core->platform->GetConfigFilePath(),
                "Where the app's config file is stored on disk.");

  envs["data_directory"] = StrEntry_(g_core->GetDataDirectory(),
                                     "Where bundled static app data lives.");

  envs["os_version"] = StrEntry_(
      g_core->platform->GetOSVersionString(),
      "Platform-specific os version string provided by the native layer.\n"
      "\n"
      "Note that more detailed OS information may be available through\n"
      "the Python 'platform' module.");

  envs["api_version"] = IntEntry_(
      kEngineApiVersion,
      "The app's api version.\n"
      "\n"
      "Only Python modules and packages associated with the current API\n"
      "version number will be detected by the game (see the\n"
      ":class:`babase.MetadataSubsystem`). This value will change whenever\n"
      "substantial backward-incompatible changes are introduced to\n"
      "Ballistica APIs. When that happens, modules/packages should be "
      "updated\n"
      "accordingly and set to target the newer API version number.");

  envs["python_directory_user"] = OptionalStrEntry_(
      g_core->GetUserPythonDirectory(),
      "Path where the app expects its user scripts (mods) to live.\n"
      "\n"
      "Be aware that this value may be ``None`` if Ballistica is running in\n"
      "a non-standard environment, and that python-path modifications may\n"
      "cause modules to be loaded from other locations.");

  envs["python_directory_app"] = OptionalStrEntry_(
      g_core->GetAppPythonDirectory(),
      "Path where the app expects its own bundled modules to live.\n"
      "\n"
      "Be aware that this value may be ``None`` if Ballistica is running in\n"
      "a non-standard environment, and that python-path modifications may\n"
      "cause modules to be loaded from other locations.");

  envs["python_directory_app_site"] = OptionalStrEntry_(
      g_core->GetSitePythonDirectory(),
      "Path where the app expects its bundled third party modules to live.\n"
      "\n"
      "Be aware that this value may be ``None`` if Ballistica is running in\n"
      "a non-standard environment, and that python-path modifications may\n"
      "cause modules to be loaded from other locations.");

  envs["tv"] =
      BoolEntry_(g_core->platform->IsRunningOnTV(),
                 "Whether the app is targeting a TV-centric experience.");

  envs["vr"] = BoolEntry_(g_core->vr_mode(),
                          "Whether the app is currently running in VR.");

  envs["arcade"] =
      BoolEntry_(g_buildconfig.variant_arcade(),
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

  envs["demo"] = BoolEntry_(g_buildconfig.variant_demo(),
                            "Whether the app is targeting a demo experience.");
  envs["arch"] = AppArchitectureEntry_();
  envs["variant"] = AppVariantEntry_();
  envs["platform"] = AppPlatformEntry_();

  bool first = true;
  for (auto&& entry : envs) {
    if (!first) {
      docs += "\n";
    }
    docs += "   " + entry.first + " (" + entry.second->typestr + "):\n      "
            + entry.second->docs + "\n";
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
    return entry->second->call();
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
