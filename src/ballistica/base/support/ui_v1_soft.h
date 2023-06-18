// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_UI_V1_SOFT_H_
#define BALLISTICA_BASE_SUPPORT_UI_V1_SOFT_H_

#include "ballistica/base/ui/ui.h"

// Predeclare some types we use.
namespace ballistica::ui_v1 {
class RootUI;
class Widget;
}  // namespace ballistica::ui_v1

namespace ballistica::base {

/// 'Soft' interface to the ui_v1 feature-set, managed by base.
/// Feature-sets listing ui_v1 as a soft requirement must limit their use of
/// it to these methods and should be prepared to handle the not-present
/// case.
class UIV1SoftInterface {
 public:
  virtual void DoHandleDeviceMenuPress(base::InputDevice* device) = 0;
  virtual void DoShowURL(const std::string& url) = 0;
  virtual void DoQuitWindow() = 0;
  virtual auto NewRootUI() -> ui_v1::RootUI* = 0;
  virtual auto MainMenuVisible() -> bool = 0;
  virtual auto PartyIconVisible() -> bool = 0;
  virtual void ActivatePartyIcon() = 0;
  virtual void HandleLegacyRootUIMouseMotion(float x, float y) = 0;
  virtual auto HandleLegacyRootUIMouseDown(float x, float y) -> bool = 0;
  virtual void HandleLegacyRootUIMouseUp(float x, float y) = 0;
  virtual void Draw(FrameDef* frame_def) = 0;
  virtual void OnAppStart() = 0;
  virtual auto PartyWindowOpen() -> bool = 0;
  virtual void Reset() = 0;
  virtual void OnScreenSizeChange() = 0;
  virtual void OnLanguageChange() = 0;
  virtual auto GetRootWidget() -> ui_v1::Widget* = 0;
  virtual auto SendWidgetMessage(const WidgetMessage& m) -> int = 0;
  virtual void DoApplyAppConfig() = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_UI_V1_SOFT_H_
