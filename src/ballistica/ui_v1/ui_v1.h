// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_UI_V1_H_
#define BALLISTICA_UI_V1_UI_V1_H_

#include <ballistica/base/input/device/input_device.h>

#include <string>

#include "ballistica/base/ui/ui_delegate.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// UI-Locks: make sure widget-lists don't change under you. Use a read-lock
// if you just need to ensure lists remain intact but won't be changing
// anything. Use a write-lock whenever modifying a list.
#if BA_DEBUG_BUILD
#define BA_DEBUG_UI_READ_LOCK \
  ::ballistica::ui_v1::UIV1FeatureSet::UILock ui_lock(false)
#define BA_DEBUG_UI_WRITE_LOCK \
  ::ballistica::ui_v1::UIV1FeatureSet::UILock ui_lock(true)
#else
#define BA_DEBUG_UI_READ_LOCK
#define BA_DEBUG_UI_WRITE_LOCK
#endif

// Predeclared types from other feature sets that we use.
namespace ballistica::core {
class CoreFeatureSet;
}
namespace ballistica::base {
class BaseFeatureSet;
struct WidgetMessage;
}  // namespace ballistica::base

namespace ballistica::ui_v1 {

// Predeclare types we use throughout our FeatureSet so most headers can get
// away with just including this header.
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

// Our feature-set's globals. Feature-sets should NEVER directly access
// globals in another feature-set's namespace. All functionality we need
// from other feature-sets should be imported into globals in our own
// namespace. Generally we do this when we are initially imported (just as
// regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern UIV1FeatureSet* g_ui_v1;

/// Our C++ front-end to our feature set. This is what other C++
/// feature-sets can 'Import' from us.
class UIV1FeatureSet : public FeatureSetNativeComponent,
                       public base::UIDelegateInterface {
 public:
  /// Instantiate our FeatureSet if needed and return the single instance of
  /// it. Basically a Python import statement.
  static auto Import() -> UIV1FeatureSet*;

  /// Used to ensure widgets are not created or destroyed at certain times
  /// (while traversing widget hierarchy, etc).
  class UILock {
   public:
    explicit UILock(bool write);
    ~UILock();

   private:
    BA_DISALLOW_CLASS_COPIES(UILock);
  };

  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);

  void DoShowURL(const std::string& url) override;
  auto IsMainUIVisible() -> bool override;
  auto IsPartyIconVisible() -> bool override;
  void ActivatePartyIcon() override;
  void Draw(base::FrameDef* frame_def) override;

  void SetSquadSizeLabel(int num) override;
  void SetAccountSignInState(bool signed_in, const std::string& name) override;

  UIV1Python* const python;

  void OnActivate() override;
  void OnDeactivate() override;

  auto IsPartyWindowOpen() -> bool override;

  // Return the root widget containing all windows & dialogs. Whenever this
  // contains children, the UI is considered to be in focus
  auto screen_root_widget() -> ui_v1::ContainerWidget* {
    return screen_root_widget_.get();
  }

  auto overlay_root_widget() -> ui_v1::ContainerWidget* {
    return overlay_root_widget_.get();
  }

  // Return the absolute root widget; this includes persistent UI bits such
  // as the top/bottom bars
  auto root_widget() -> ui_v1::RootWidget* { return root_widget_.get(); }
  // void Reset() override;

  // Add a widget to a container. If a parent is provided, the widget is
  // added to it; otherwise it is added to the root widget.
  void AddWidget(Widget* w, ContainerWidget* to);
  void DeleteWidget(Widget* widget);

  void OnScreenSizeChange() override;
  void OnUIScaleChange();

  void OnLanguageChange() override;
  auto GetRootWidget() -> ui_v1::Widget* override;
  auto SendWidgetMessage(const base::WidgetMessage& m) -> int override;
  void ApplyAppConfig() override;

  auto always_use_internal_on_screen_keyboard() const {
    return always_use_internal_on_screen_keyboard_;
  }
  auto set_party_window_open(bool value) { party_window_open_ = value; }

  auto HasQuitConfirmDialog() -> bool override;
  void ConfirmQuit(QuitType quit_type) override;

 private:
  UIV1FeatureSet();
  Object::Ref<ContainerWidget> screen_root_widget_;
  Object::Ref<ContainerWidget> overlay_root_widget_;
  Object::Ref<RootWidget> root_widget_;
  int ui_lock_count_{};
  int language_state_{};
  bool always_use_internal_on_screen_keyboard_{};
  bool party_window_open_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_UI_V1_H_
