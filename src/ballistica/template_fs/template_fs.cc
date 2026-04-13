// Released under the MIT License. See LICENSE for details.

#include "ballistica/template_fs/template_fs.h"

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/template_fs/python/template_fs_python.h"

namespace ballistica::template_fs {

TemplateFsFeatureSet* g_template_fs{};
base::BaseFeatureSet* g_base{};
core::CoreFeatureSet* g_core{};

void TemplateFsFeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported.
  // Like any normal Python module, we take this opportunity to
  // import and/or create the stuff we use.

  // Importing core should always be the first thing we do.
  // Various ballistica functionality will fail if this has not been done.
  g_core = core::CoreFeatureSet::Import();

  // Create our feature-set's C++ front-end.
  g_template_fs = new TemplateFsFeatureSet();

  // Store our C++ front-end with our Python module. This is what allows
  // other C++ code to 'import' our C++ front end and talk to us directly.
  g_template_fs->StoreOnPythonModule(module);

  // Import any Python stuff we use into objs_.
  g_template_fs->python->ImportPythonObjs();

  // Import any other C++ feature-set-front-ends we use.
  assert(g_base == nullptr);  // Should be getting set once here.
  g_base = base::BaseFeatureSet::Import();

  // Define our module's classes.
  g_template_fs->python->AddPythonClasses(module);
}

TemplateFsFeatureSet::TemplateFsFeatureSet() : python{new TemplateFsPython()} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_template_fs == nullptr);
}

auto TemplateFsFeatureSet::Import() -> TemplateFsFeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<TemplateFsFeatureSet>("_batemplatefs");
}

void TemplateFsFeatureSet::HelloWorld() const { python->HelloWorld(); }

}  // namespace ballistica::template_fs
