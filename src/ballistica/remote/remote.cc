// Released under the MIT License. See LICENSE for details.

#include "ballistica/remote/remote.h"

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/remote/python/remote_python.h"

namespace ballistica::remote {

RemoteFeatureSet* g_remote{};
base::BaseFeatureSet* g_base{};
core::CoreFeatureSet* g_core{};

void RemoteFeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported.
  // Like any normal Python module, we take this opportunity to
  // import and/or create the stuff we use.

  // Importing core should always be the first thing we do.
  // Various ballistica functionality will fail if this has not been done.
  g_core = core::CoreFeatureSet::Import();

  // Create our feature-set's C++ front-end.
  g_remote = new RemoteFeatureSet();

  // Store our C++ front-end with our Python module. This is what allows
  // other C++ code to 'import' our C++ front end and talk to us directly.
  g_remote->StoreOnPythonModule(module);

  // Import any Python stuff we use into objs_.
  g_remote->python->ImportPythonObjs();

  // Import any other C++ feature-set-front-ends we use.
  assert(g_base == nullptr);  // Should be getting set once here.
  g_base = base::BaseFeatureSet::Import();

  // Define our module's classes.
  g_remote->python->AddPythonClasses(module);
}

RemoteFeatureSet::RemoteFeatureSet() : python{new RemotePython()} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_remote == nullptr);
}

auto RemoteFeatureSet::Import() -> RemoteFeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<RemoteFeatureSet>("_baremote");
}

}  // namespace ballistica::remote
