// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_APPLE_BASE_PLATFORM_APPLE_H_
#define BALLISTICA_BASE_PLATFORM_APPLE_BASE_PLATFORM_APPLE_H_
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS

#include "ballistica/base/platform/base_platform.h"

namespace ballistica::base {

class BasePlatformApple : public BasePlatform {
 public:
  BasePlatformApple();

  void DoPurchase(const std::string& item) override;
  void RestorePurchases() override;
  void PurchaseAck(const std::string& purchase,
                   const std::string& order_id) override;
  void TerminateApp() override;

  void DoOpenURL(const std::string& url) override;

  // void SetHardwareCursorVisible(bool visible) override;

 private:
};

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD || BA_OSTYPE_MACOS
#endif  // BALLISTICA_BASE_PLATFORM_APPLE_BASE_PLATFORM_APPLE_H_
