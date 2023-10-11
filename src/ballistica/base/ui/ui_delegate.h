// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_UI_DELEGATE_H_
#define BALLISTICA_BASE_UI_UI_DELEGATE_H_

#include "ballistica/base/ui/ui.h"

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
  virtual void OnDeactivate() = 0;

  virtual void OnScreenSizeChange() = 0;
  virtual void OnLanguageChange() = 0;
  virtual void DoApplyAppConfig() = 0;

  virtual void DoHandleDeviceMenuPress(base::InputDevice* device) = 0;
  virtual void DoShowURL(const std::string& url) = 0;
  // virtual void DoQuitWindow() = 0;
  virtual auto MainMenuVisible() -> bool = 0;
  virtual auto PartyIconVisible() -> bool = 0;
  virtual void ActivatePartyIcon() = 0;
  virtual void HandleLegacyRootUIMouseMotion(float x, float y) = 0;
  virtual auto HandleLegacyRootUIMouseDown(float x, float y) -> bool = 0;
  virtual void HandleLegacyRootUIMouseUp(float x, float y) = 0;
  virtual void Draw(FrameDef* frame_def) = 0;
  virtual auto PartyWindowOpen() -> bool = 0;
  virtual void Reset() = 0;
  virtual auto GetRootWidget() -> ui_v1::Widget* = 0;
  virtual auto SendWidgetMessage(const WidgetMessage& m) -> int = 0;

  /// Should return true if this app mode can confirm quitting the app.
  virtual auto HasQuitConfirmDialog() -> bool = 0;

  /// Will be called in the logic thread if HasQuitConfirmDialog() returns
  /// true. Should present a quit confirmation dialog to the user and call
  /// BaseFeatureSet::QuitApp() with the provided quit_type if confirmed.
  virtual void ConfirmQuit(QuitType quit_type) = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_UI_DELEGATE_H_
