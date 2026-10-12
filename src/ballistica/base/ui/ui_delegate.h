// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_UI_DELEGATE_H_
#define BALLISTICA_BASE_UI_UI_DELEGATE_H_

#include <string>

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/ui/widget_message.h"

// Predeclare some types we use.

namespace ballistica::ui_v1 {
class RootUI;
class Widget;
}  // namespace ballistica::ui_v1

namespace ballistica::base {

class UIDelegateInterface {
 public:
  /// Called when this delegate is becoming the active one.
  virtual void OnActivate() = 0;

  /// Called when this delegate is resigning active status.
  ///
  /// Note that this fires on every session reset, not once per
  /// app-mode; anything scoped to the *supplying app-mode* should be
  /// wiped by that app-subsystem's reset() on the Python side, which
  /// runs at every app-mode switch.
  virtual void OnDeactivate() = 0;

  virtual void OnScreenSizeChange() = 0;
  virtual void OnLanguageChange() = 0;
  virtual void ApplyAppConfig() = 0;

  /// Called by ShowURL(). Will always be called in the logic thread.
  virtual void DoShowURL(const std::string& url) = 0;

  virtual auto IsMainUIVisible() -> bool = 0;

  /// Return whether UI elements currently cover the entire visible
  /// screen (the virtual outer rect) opaquely; used to skip rendering the world
  /// behind the UI. Must be conservative: return true only when full
  /// coverage is guaranteed.
  virtual auto UICoversScreenOpaquely() -> bool = 0;

  /// Would a back/menu press right now do something in-game (navigate
  /// out of a window, close a popup, bring up the in-game menu) rather
  /// than being a no-op at the top level? Platforms where the OS acts
  /// on the press itself unless we consume it (tvOS's menu button) must
  /// decide synchronously whether to swallow it, so they need this
  /// answered in advance rather than after routing the press.
  virtual auto BackPressWouldNavigate() -> bool = 0;

  virtual auto IsPartyIconVisible() -> bool = 0;
  virtual void ActivatePartyIcon() = 0;
  virtual void Draw(FrameDef* frame_def) = 0;
  virtual auto IsPartyWindowOpen() -> bool = 0;
  virtual auto GetRootWidget() -> ui_v1::Widget* = 0;
  virtual auto SendWidgetMessage(const WidgetMessage& m) -> int = 0;
  virtual void SetSquadSizeLabel(int num) = 0;
  virtual void SetAccountSignInState(bool signed_in,
                                     const std::string& name) = 0;

  /// Should return true if this app mode can confirm quitting the app.
  virtual auto HasQuitConfirmDialog() -> bool = 0;

  /// Will be called in the logic thread if HasQuitConfirmDialog() returns
  /// true. Should present a quit confirmation dialog to the user and call
  /// BaseFeatureSet::QuitApp() with the provided quit_type if confirmed.
  virtual void ConfirmQuit(QuitType quit_type) = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_UI_DELEGATE_H_
