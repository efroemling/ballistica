// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_FEATURE_SET_NATIVE_COMPONENT_H_
#define BALLISTICA_SHARED_FOUNDATION_FEATURE_SET_NATIVE_COMPONENT_H_

#include "ballistica/shared/foundation/macros.h"

namespace ballistica {

extern const char* kFeatureSetDataAttrName;

/// Base-class for portions of feature-sets exposed directly to C++.
/// Using this, one can 'import' feature-sets directly in C++ without
/// worrying about wrangling the Python layer (or whether the feature-set
/// even has a Python component to it).
class FeatureSetNativeComponent {
 public:
  virtual ~FeatureSetNativeComponent();

  /// Generally a feature-set's native component is stored in a special
  /// Python object with a predefined name inside its native Python module.
  /// This allows native feature set components to 'Import' each other by
  /// importing each other's native Python modules and looking for said
  /// special object. This method does that storing.
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
      -> FeatureSetNativeComponent*;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_FEATURE_SET_NATIVE_COMPONENT_H_
