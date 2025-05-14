// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_APPLE_BASE_PLATFORM_APPLE_H_
#define BALLISTICA_BASE_PLATFORM_APPLE_BASE_PLATFORM_APPLE_H_
#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS

#include <string>

#include "ballistica/base/platform/base_platform.h"
namespace ballistica::base {

class BasePlatformApple : public BasePlatform {
 public:
  BasePlatformApple();
  void DoPurchase(const std::string& item) override;
  void RestorePurchases() override;
  void PurchaseAck(const std::string& purchase,
                   const std::string& order_id) override;
  void DoOpenURL(const std::string& url) override;
  auto OverlayWebBrowserIsSupported() -> bool override;
  void DoOverlayWebBrowserOpenURL(const std::string& url) override;
  void DoOverlayWebBrowserClose() override;
  void LoginAdapterGetSignInToken(const std::string& login_type,
                                  int attempt_id) override;
  void LoginAdapterBackEndActiveChange(const std::string& login_type,
                                       bool active) override;
  auto SupportsOpenDirExternally() -> bool override;
  void OpenDirExternally(const std::string& path) override;
  void OpenFileExternally(const std::string& path) override;
};

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD || BA_PLATFORM_MACOS
#endif  // BALLISTICA_BASE_PLATFORM_APPLE_BASE_PLATFORM_APPLE_H_
