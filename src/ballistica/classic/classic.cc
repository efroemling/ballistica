// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/classic.h"

#include "ballistica/classic/python/classic_python.h"
#include "ballistica/classic/support/v1_account.h"

namespace ballistica::classic {

core::CoreFeatureSet* g_core{};
base::BaseFeatureSet* g_base{};
ClassicFeatureSet* g_classic{};

void ClassicFeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported.
  // Like any normal Python module, we take this opportunity to
  // import/create the stuff we use.

  // Importing core should always be the first thing we do.
  // Various ballistica functionality will fail if this has not been done.
  assert(g_core == nullptr);
  g_core = core::CoreFeatureSet::Import();

  g_core->LifecycleLog("_baclassic exec begin");

  // Create our feature-set's C++ front-end.
  assert(g_classic == nullptr);
  g_classic = new ClassicFeatureSet();

  // Store our C++ front-end with our Python module.
  // This is what allows others to 'import' our C++ front end.
  g_classic->StoreOnPythonModule(module);

  // Import any Python stuff we use into objs_.
  g_classic->python->ImportPythonObjs();

  // Import any other C++ feature-set-front-ends we use.
  assert(g_base == nullptr);  // Should be getting set once here.
  g_base = base::BaseFeatureSet::Import();

  // Let base know we exist.
  // (save it the trouble of trying to load us if it uses us passively).
  g_base->set_classic(g_classic);

  g_core->LifecycleLog("_baclassic exec end");
}

ClassicFeatureSet::ClassicFeatureSet()
    : python{new ClassicPython()}, v1_account{new V1Account()} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_classic == nullptr);
}

auto ClassicFeatureSet::Import() -> ClassicFeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<ClassicFeatureSet>("_baclassic");
}

int ClassicFeatureSet::GetControllerValue(base::InputDevice* device,
                                          const std::string& value_name) {
  return python->GetControllerValue(device, value_name);
}

float ClassicFeatureSet::GetControllerFloatValue(
    base::InputDevice* device, const std::string& value_name) {
  return python->GetControllerFloatValue(device, value_name);
}

}  // namespace ballistica::classic
