// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_TEMPLATE_FS_TEMPLATE_FS_H_
#define BALLISTICA_TEMPLATE_FS_TEMPLATE_FS_H_

#include "ballistica/shared/foundation/feature_set_front_end.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// Predeclared types from other feature sets that we use.
namespace ballistica::core {
class CoreFeatureSet;
}
namespace ballistica::base {
class BaseFeatureSet;
}

// Feature-sets have their own unique namespace under the ballistica namespace.
namespace ballistica::template_fs {

// Predeclared types our feature-set provides.
class TemplateFsFeatureSet;
class TemplateFsPython;

// Our feature-set's globals.
// Feature-sets should NEVER directly access globals in another feature-set's
// namespace. All functionality we need from other feature-sets should be
// imported into globals in our own namespace. Generally we do this when we
// are initially imported (just as regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern TemplateFsFeatureSet* g_template_fs;

/// Our C++ front-end to our feature set. This is what other C++
/// feature-sets can 'Import' from us.
class TemplateFsFeatureSet : public FeatureSetFrontEnd {
 public:
  /// Instantiate our FeatureSet if needed and return the single
  /// instance of it. Basically a Python import statement.
  static auto Import() -> TemplateFsFeatureSet*;

  /// Called when our binary Python module first gets imported.
  static void OnModuleExec(PyObject* module);

  /// Ye olde hello world test.
  void HelloWorld() const;

  // Our sub-components.
  TemplateFsPython* const python;

 private:
  TemplateFsFeatureSet();
};

}  // namespace ballistica::template_fs

#endif  // BALLISTICA_TEMPLATE_FS_TEMPLATE_FS_H_
