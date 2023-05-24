// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_UI_V1_H_
#define BALLISTICA_UI_V1_UI_V1_H_

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

namespace ballistica::ui_v1 {

// Predeclared types our feature-set provides.
class UIV1FeatureSet;
class UIV1Python;
class Widget;
class ButtonWidget;
class ContainerWidget;
class ImageWidget;
class RootUI;
class RootWidget;
class StackWidget;
class TextWidget;

// Our feature-set's globals.
// Feature-sets should NEVER directly access globals in another feature-set's
// namespace. All functionality we need from other feature-sets should be
// imported into globals in our own namespace. Generally we do this when we
// are initially imported (just as regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern UIV1FeatureSet* g_ui_v1;

/// Our C++ front-end to our feature set. This is what other C++
/// feature-sets can 'Import' from us.
class UIV1FeatureSet : public FeatureSetNativeComponent {
 public:
  /// Instantiate our FeatureSet if needed and return the single
  /// instance of it. Basically a Python import statement.
  static auto Import() -> UIV1FeatureSet*;

  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);

  UIV1Python* const python;

 private:
  UIV1FeatureSet();
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_UI_V1_H_
