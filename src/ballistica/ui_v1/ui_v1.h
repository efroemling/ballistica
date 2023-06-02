// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_UI_V1_H_
#define BALLISTICA_UI_V1_UI_V1_H_

#include <ballistica/base/input/device/input_device.h>

#include "ballistica/base/support/ui_v1_soft.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// Predeclared types from other feature sets that we use.
namespace ballistica::core {
class CoreFeatureSet;
}
namespace ballistica::base {
class BaseFeatureSet;
class WidgetMessage;
}  // namespace ballistica::base

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
class UIV1FeatureSet : public FeatureSetNativeComponent,
                       public base::UIV1SoftInterface {
 public:
  /// Instantiate our FeatureSet if needed and return the single
  /// instance of it. Basically a Python import statement.
  static auto Import() -> UIV1FeatureSet*;

  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);
  void DoHandleDeviceMenuPress(base::InputDevice* device) override;
  void DoShowURL(const std::string& url) override;
  void DoQuitWindow() override;
  auto NewRootUI() -> ui_v1::RootUI* override;
  auto MainMenuVisible() -> bool override;
  auto PartyIconVisible() -> bool override;
  void ActivatePartyIcon() override;
  void HandleLegacyRootUIMouseMotion(float x, float y) override;
  auto HandleLegacyRootUIMouseDown(float x, float y) -> bool override;
  void HandleLegacyRootUIMouseUp(float x, float y) override;
  void Draw(base::FrameDef* frame_def) override;

  UIV1Python* const python;

  auto root_ui() const -> ui_v1::RootUI* {
    assert(root_ui_);
    return root_ui_;
  }
  void OnAppStart() override;
  auto PartyWindowOpen() -> bool override;

  // Return the root widget containing all windows & dialogs
  // Whenever this contains children, the UI is considered to be in focus
  auto screen_root_widget() -> ui_v1::ContainerWidget* {
    return screen_root_widget_.Get();
  }

  auto overlay_root_widget() -> ui_v1::ContainerWidget* {
    return overlay_root_widget_.Get();
  }

  // Return the absolute root widget; this includes persistent UI
  // bits such as the top/bottom bars
  auto root_widget() -> ui_v1::RootWidget* { return root_widget_.Get(); }
  void Reset() override;

  // Add a widget to a container.
  // If a parent is provided, the widget is added to it; otherwise it is added
  // to the root widget.
  void AddWidget(Widget* w, ContainerWidget* to);
  void OnScreenSizeChange() override;
  void OnLanguageChange() override;
  auto GetRootWidget() -> ui_v1::Widget* override;
  auto SendWidgetMessage(const base::WidgetMessage& m) -> int override;

 private:
  UIV1FeatureSet();

  RootUI* root_ui_{};
  Object::Ref<ContainerWidget> screen_root_widget_;
  Object::Ref<ContainerWidget> overlay_root_widget_;
  Object::Ref<RootWidget> root_widget_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_UI_V1_H_
