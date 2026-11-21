// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SQUADS_SQUADS_H_
#define BALLISTICA_SQUADS_SQUADS_H_

#include "ballistica/shared/foundation/feature_set_native_component.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// Predeclare types from other feature sets that we use.
namespace ballistica::core {
class CoreFeatureSet;
}
namespace ballistica::base {
class BaseFeatureSet;
}

// Feature-sets have their own unique namespace under the ballistica
// namespace.
namespace ballistica::squads {

// Predeclare types we use throughout our FeatureSet so most headers can get
// away with just including this header.
class SquadsFeatureSet;
class SquadsPython;
class SquadsAppMode;

// Our feature-set's globals. Feature-sets should NEVER directly access
// globals in another feature-set's namespace. All functionality we need
// from other feature-sets should be imported into globals in our own
// namespace. Generally we do this when we are initially imported (just as
// regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern SquadsFeatureSet* g_squads;

/// The native C++ portion of our feature set. We can make this available
/// for other feature sets to 'Import' directly in C++ in addition to
/// exposing functionality though a Python api.
class SquadsFeatureSet : public FeatureSetNativeComponent {
 public:
  /// Instantiate and return our singleton instance. Basically a Python
  /// import statement.
  static auto Import() -> SquadsFeatureSet*;

  /// Called when our binary Python module first gets imported.
  static void OnModuleExec(PyObject* module);

  // Our sub-components.
  SquadsPython* const python;

 private:
  SquadsFeatureSet();
};

}  // namespace ballistica::squads

#endif  // BALLISTICA_SQUADS_SQUADS_H_
