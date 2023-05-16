// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_FEATURE_SET_FRONT_END_H_
#define BALLISTICA_SHARED_FOUNDATION_FEATURE_SET_FRONT_END_H_

#include "ballistica/core/core.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica {

extern const char* kFeatureSetDataAttrName;

/// Base-class for portions of feature-sets exposed directly to C++.
/// Using this, one can 'import' feature-sets directly in C++ without
/// worrying about wrangling the Python layer (or whether the feature-set
/// even has a Python component to it).
class FeatureSetFrontEnd {
 public:
  virtual ~FeatureSetFrontEnd();

  /// FeatureSets with C++ front-ends AND Python binary module components
  /// should use this during module exec to store themselves with the module.
  /// Then their Import() method should use ImportThroughPythonModule below
  /// to fetch the front-end. This keeps the C++ and Python layers nicely
  /// synced.
  void StoreOnPythonModule(PyObject* module);

 protected:
  /// Should be used by FeatureSets in their Import() methods to pull their
  /// data from their associated Python module.
  template <typename T>
  static auto ImportThroughPythonModule(const char* modulename) -> T* {
    auto* fs_typed =
        dynamic_cast<T*>(BaseImportThroughPythonModule(modulename));
    BA_PRECONDITION_FATAL(fs_typed);
    return fs_typed;
  }

 private:
  static auto BaseImportThroughPythonModule(const char* modulename)
      -> FeatureSetFrontEnd*;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_FEATURE_SET_FRONT_END_H_
