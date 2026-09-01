// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_UI_V1_H_
#define BALLISTICA_UI_V1_UI_V1_H_

#include <ballistica/base/input/device/input_device.h>

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/ui/ui_delegate.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"
#include "ballistica/ui_v1/generated/ui_asset_set.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// UI-Locks: make sure widget-hierarchy doesn't change when its not supposed
// to. Hold a read-lock if you want to make sure things remain constant but
// won't be changing anything (draw code, etc.). Hold a write-lock whenever
// modifying hierarchies to make sure nothing is expecting them to be
// constant.
#if BA_DEBUG_BUILD
#define BA_DEBUG_UI_READ_LOCK \
  ::ballistica::ui_v1::UIV1FeatureSet::UIReadLock ui_read_lock
#define BA_DEBUG_UI_WRITE_LOCK \
  ::ballistica::ui_v1::UIV1FeatureSet::UIWriteLock ui_write_lock
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
  class UIReadLock {
   public:
    explicit UIReadLock();
    ~UIReadLock();

   private:
    BA_DISALLOW_CLASS_COPIES(UIReadLock);
  };
  class UIWriteLock {
   public:
    explicit UIWriteLock();
    ~UIWriteLock();

   private:
    BA_DISALLOW_CLASS_COPIES(UIWriteLock);
  };

  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);

  void DoShowURL(const std::string& url) override;
  auto IsMainUIVisible() -> bool override;
  auto UICoversScreenOpaquely() -> bool override;
  auto BackPressWouldNavigate() -> bool override;
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

  /// The assets our widgets draw themselves with, supplied by the active
  /// app-mode (see bauiv1.set_ui_asset_set). This is what lets an app-mode
  /// skin the ui.
  ///
  /// Supplied during app-mode activation, before the mode asks the
  /// native layer to activate (which is what builds the root widget),
  /// so drawing code can rely on every member being present -- an
  /// activation without a complete set builds no widgets at all (see
  /// OnActivate). Asserts in debug builds if that ever breaks.
  auto assets() -> const UIAssetSet& {
    assert(ui_assets_.complete());
    return ui_assets_;
  }

  /// Supply the art for as long as the current app-mode is active.
  ///
  /// The supply outlives our own deactivate/reactivate cycles (we are
  /// reset on every session change); the Python layer wipes it via
  /// clear_assets() at each app-mode switch (UIV1AppSubsystem.reset()),
  /// so an incoming app-mode can never inherit the outgoing one's art.
  void set_assets(const UIAssetSet& assets) { ui_assets_ = assets; }

  /// Drop any app-mode-supplied art. Called at app-mode switches; safe
  /// while we are inactive (which is when switches happen).
  void clear_assets() { ui_assets_ = UIAssetSet(); }

  /// Do we currently hold a complete asset set? False while zombified
  /// (activated without one) or before any app-mode supplied ours --
  /// the rare code that can run in those states must check this
  /// before touching assets().
  auto have_assets() const -> bool { return ui_assets_.complete(); }

  // Add a widget to a container. If a parent is provided, the widget is
  // added to it; otherwise it is added to the root widget.
  void AddWidget(Widget* w, ContainerWidget* to);
  void DeleteWidget(Widget* widget);

  /// Return the current globally selected widget, or nullptr if none
  /// exists. Must be called from the logic thread.
  auto GetSelectedWidget() -> Widget*;

  void OnScreenSizeChange() override;
  void OnUIScaleChange();

  void OnLanguageChange() override;
  auto GetRootWidget() -> ui_v1::Widget* override;
  auto SendWidgetMessage(const base::WidgetMessage& m) -> int override;
  void ApplyAppConfig() override;

  auto always_use_internal_on_screen_keyboard() const {
    return always_use_internal_on_screen_keyboard_;
  }

  void RegisterWidgetID(const std::string& id, Widget* w);
  void UnregisterWidgetID(const std::string& id, Widget* w);

  auto HasQuitConfirmDialog() -> bool override;
  void ConfirmQuit(QuitType quit_type) override;

  auto WidgetByID(const std::string& val) -> Widget*;

  void UIOpenStateChange(const std::string& tag, int increment);

  const auto ui_open_counts() const {
    assert(g_base->InLogicThread());
    return ui_open_counts_;
  }

 private:
  UIV1FeatureSet();
  UIAssetSet ui_assets_;
  std::unordered_map<std::string, int> ui_open_counts_;
  Object::Ref<ContainerWidget> screen_root_widget_;
  Object::Ref<ContainerWidget> overlay_root_widget_;
  Object::Ref<RootWidget> root_widget_;
  std::unordered_map<std::string, std::vector<Widget*>> widgets_by_id_;
  int ui_read_lock_count_{};
  int ui_write_lock_count_{};
  int language_state_{};
  bool always_use_internal_on_screen_keyboard_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_UI_V1_H_
