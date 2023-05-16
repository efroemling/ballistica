// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_MODULE_BUILDER_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_MODULE_BUILDER_H_

#include <vector>

#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica {

/// Utility class for defining together Python C modules.
/// To use, allocate an instance and call its Build() method. The instance
/// should remain allocated, as it is used as 'static' storage for the Python
/// type.
class PythonModuleBuilder {
 public:
  PythonModuleBuilder(const char* name,
                      const std::vector<std::vector<PyMethodDef>>& method_lists,
                      int (*exec_call)(PyObject* module))
      : name_{name},
        module_def_{PyModuleDef_HEAD_INIT},
        slots_{{Py_mod_exec, reinterpret_cast<void*>(exec_call)},
               {0, nullptr}} {
    // Slight optimization; calc size we'll need for our combined list.
    size_t total_size{};
    for (auto&& methods : method_lists) {
      total_size += methods.size();
    }
    all_methods_.reserve(total_size + 1);

    // Build our single combined method list.
    for (auto&& methods : method_lists) {
      all_methods_.insert(all_methods_.end(), methods.begin(), methods.end());
    }
    // Cap the end.
    all_methods_.push_back(PyMethodDef{nullptr, nullptr, 0, nullptr});
  }

  template <typename T>
  static auto AddClass(PyObject* module) -> PyObject* {
    assert(!T::TypeIsSetUp(&T::type_obj));
    T::SetupType(&T::type_obj);
    BA_PRECONDITION_FATAL(PyType_Ready(&T::type_obj) == 0);
    assert(T::TypeIsSetUp(&T::type_obj));
    int r = PyModule_AddObjectRef(module, T::type_name(),
                                  reinterpret_cast<PyObject*>(&T::type_obj));
    BA_PRECONDITION_FATAL(r == 0);
    return reinterpret_cast<PyObject*>(&T::type_obj);
  }

  auto Build() -> PyObject* {
    assert(Python::HaveGIL());
    assert(module_def_.m_size == 0);  // make sure things start zeroed..
    module_def_.m_methods = all_methods_.data();
    module_def_.m_slots = slots_.data();
    PyObject* module = PyModuleDef_Init(&module_def_);
    BA_PRECONDITION_FATAL(module);
    return module;
  }

 private:
  std::string name_;
  PyModuleDef module_def_;
  std::vector<PyModuleDef_Slot> slots_;
  std::vector<PyMethodDef> all_methods_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_MODULE_BUILDER_H_
