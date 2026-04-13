// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/feature_set_native_component.h"

#include <Python.h>

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/python/python.h"

namespace ballistica {

const char* kFeatureSetDataAttrName = "_ba_feature_set_data";

FeatureSetNativeComponent::~FeatureSetNativeComponent() = default;

auto FeatureSetNativeComponent::BaseImportThroughPythonModule(
    const char* modulename) -> FeatureSetNativeComponent* {
  // Our feature-set has an associated Python module, so we want all
  // importing to go through Python. This keeps things consistent no
  // matter whether we are used from C++ or Python. We simply import
  // our Python module and then return the FeatureSet pointer that it
  // has stored with itself.

  // Make sure we're holding the GIL so can be run from any thread.
  auto gil{Python::ScopedInterpreterLock()};

  PyObject* module = PyImport_ImportModule(modulename);
  if (!module) {
    // we pass zero here to avoid grabbing references to this exception
    // which can cause objects to stick around and trip up our deletion checks
    // (nodes, actors existing after their games have ended)
    PyErr_PrintEx(0);
    // Currently not going to attempt to recover if we can't get at our own
    // stuff.
    FatalError("Unable to import Python module '" + std::string(modulename)
               + "'.");
  }

  // Grab the wrapper to our C++ pointer from the module.
  auto fs_data_obj = PythonRef::StolenSoft(
      PyObject_GetAttrString(module, kFeatureSetDataAttrName));
  if (!fs_data_obj.exists()) {
    FatalError("Did not find expected feature-set data in module "
               + std::string(modulename));
  }

  // We need our feature-set-data class from _babase for this.
  assert(core::g_core);
  auto* basefs = core::g_core->SoftImportBase();
  if (!basefs) {
    FatalError(
        "_babase is unavailable; can't import ballistica c++ interfaces");
  }

  // Make sure its pointing to an instance and return it.
  auto* feature_set = basefs->FeatureSetFromData(*fs_data_obj);
  BA_PRECONDITION_FATAL(feature_set);

  return feature_set;
}

void FeatureSetNativeComponent::StoreOnPythonModule(PyObject* module) {
  // We need our feature-set-data class from _babase for this.
  assert(core::g_core);
  auto* basefs = core::g_core->SoftImportBase();
  if (!basefs) {
    FatalError(
        "_babase is unavailable; can't import ballistica c++ interfaces");
  }

  // Stuff a pointer to ourself into a Python object and add that to our
  // module. This is how our fellow C++ stuff will get at us.
  PyObject* fsdata = basefs->CreateFeatureSetData(this);
  BA_PRECONDITION_FATAL(fsdata);
  BA_PRECONDITION_FATAL(
      PyObject_SetAttrString(module, kFeatureSetDataAttrName, fsdata) == 0);
}

}  // namespace ballistica
