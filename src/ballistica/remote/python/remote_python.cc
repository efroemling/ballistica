// Released under the MIT License. See LICENSE for details.

#include "ballistica/remote/python/remote_python.h"

#include "ballistica/remote/python/methods/python_methods_remote.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_macros.h"
#include "ballistica/shared/python/python_module_builder.h"

namespace ballistica::remote {

// Declare a plain C PyInit_XXX function for our Python module. This is how
// Python inits our binary module (and by extension, our entire
// feature-set).
extern "C" auto PyInit__baremote() -> PyObject* {
  auto* builder = new PythonModuleBuilder(
      "_baremote",

      // Our native methods.
      {PythonMethodsRemote::GetMethods()},

      // Our module exec. Here we can add classes, import other modules, or
      // whatever else (same as a regular Python script module).
      [](PyObject* module) -> int {
        BA_PYTHON_TRY;
        RemoteFeatureSet::OnModuleExec(module);
        return 0;
        BA_PYTHON_INT_CATCH;
      });
  return builder->Build();
}

void RemotePython::AddPythonClasses(PyObject* module) {}

void RemotePython::ImportPythonObjs() {
#include "ballistica/remote/generated/pyembed/binding_remote.inc"
}

}  // namespace ballistica::remote
