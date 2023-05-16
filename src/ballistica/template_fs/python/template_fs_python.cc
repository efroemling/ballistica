// Released under the MIT License. See LICENSE for details.

#include "ballistica/template_fs/python/template_fs_python.h"

#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_module_builder.h"
#include "ballistica/template_fs/python/class/python_class_hello.h"
#include "ballistica/template_fs/python/methods/python_methods_template_fs.h"

namespace ballistica::template_fs {

// Declare a plain c PyInit_XXX function for our Python module;
// this is how Python inits our binary module (and by extension, our
// entire feature-set).
extern "C" auto PyInit__batemplatefs() -> PyObject* {
  auto* builder = new PythonModuleBuilder(
      "_batemplatefs",
      // Native methods to add.
      {PythonMethodsTemplateFs::GetMethods()},
      // Our module exec. Here we can add classes, import other modules,
      // or whatever else (same as a regular Python script module).
      [](PyObject* module) -> int {
        BA_PYTHON_TRY;
        TemplateFsFeatureSet::OnModuleExec(module);
        return 0;
        BA_PYTHON_INT_CATCH;
      });
  return builder->Build();
}

void TemplateFsPython::AddPythonClasses(PyObject* module) {
  PythonModuleBuilder::AddClass<PythonClassHello>(module);
}

void TemplateFsPython::ImportPythonObjs() {
#include "ballistica/template_fs/mgen/pyembed/binding_template_fs.inc"
}

void TemplateFsPython::HelloWorld() {
  // Hold the GIL throughout this call so we can run in any thread.
  // Alternately we could limit this function to the logic thread
  // which always holds the GIL. In that case we'd want to
  // stick a BA_PRECONDITION(InLogicThread()) here to be sure.
  auto gil{Python::ScopedInterpreterLock()};

  // Run the Python callable we grabbed. This will simply print any
  // errors, but we could disable that print and look at the call
  // results if any logic depended on this code running successfully.
  objs_.Get(ObjID::kHelloWorldCall).Call();
}

}  // namespace ballistica::template_fs
