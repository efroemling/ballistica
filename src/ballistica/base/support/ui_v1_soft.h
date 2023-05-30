// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_UI_V1_SOFT_H_
#define BALLISTICA_BASE_SUPPORT_UI_V1_SOFT_H_

namespace ballistica::base {

/// 'Soft' interface to the ui_v1 feature-set.
/// Feature-sets listing ui_v1 as a soft requirement must limit their use of
/// it to these methods and should be prepared to handle the not-present
/// case.
class UIV1SoftInterface {
 public:
  virtual void DoHandleDeviceMenuPress(base::InputDevice* device) = 0;
  virtual void DoShowURL(const std::string& url) = 0;
  virtual void DoQuitWindow() = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_UI_V1_SOFT_H_
