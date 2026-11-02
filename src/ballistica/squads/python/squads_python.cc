// Released under the MIT License. See LICENSE for details.

#include "ballistica/squads/python/squads_python.h"

#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_macros.h"
#include "ballistica/shared/python/python_module_builder.h"
#include "ballistica/squads/python/methods/python_methods_squads.h"

namespace ballistica::squads {

// Declare a plain C PyInit_XXX function for our Python module. This is how
// Python inits our binary module (and by extension, our entire
// feature-set).
extern "C" auto PyInit__basquads() -> PyObject* {
  auto* builder = new PythonModuleBuilder(
      "_basquads",

      // Our native methods.
      {PythonMethodsSquads::GetMethods()},

      // Our module exec. Here we can add classes, import other modules, or
      // whatever else (same as a regular Python script module).
      [](PyObject* module) -> int {
        BA_PYTHON_TRY;
        SquadsFeatureSet::OnModuleExec(module);
        return 0;
        BA_PYTHON_INT_CATCH;
      });
  return builder->Build();
}

void SquadsPython::AddPythonClasses(PyObject* module) {}

void SquadsPython::ImportPythonObjs() {
#include "ballistica/squads/generated/pyembed/binding_squads.inc"
}

}  // namespace ballistica::squads
