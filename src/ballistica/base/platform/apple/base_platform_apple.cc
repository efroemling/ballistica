// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/base/platform/apple/base_platform_apple.h"

#if BA_XCODE_BUILD
#include <BallisticaKit-Swift.h>
#endif

#if BA_XCODE_BUILD
#include "ballistica/base/platform/apple/apple_utils.h"
#endif

namespace ballistica::base {

BasePlatformApple::BasePlatformApple() {
  // On iOS, keep the device from falling asleep in our app
#if BA_OSTYPE_IOS_TVOS
  AppleUtils::DisableIdleTimer();
#endif
}

void BasePlatformApple::DoPurchase(const std::string& item) {
#if BA_USE_STORE_KIT
  AppleUtils::DoStoreKitPurchase(item);
#else
  BasePlatform::DoPurchase(item);
#endif
}

void BasePlatformApple::RestorePurchases() {
#if BA_USE_STORE_KIT
  AppleUtils::DoStoreKitPurchaseRestore();
#else
  BasePlatform::RestorePurchases();
#endif
}

void BasePlatformApple::PurchaseAck(const std::string& purchase,
                                    const std::string& order_id) {
#if BA_XCODE_BUILD
  AppleUtils::PurchaseAck(purchase, order_id);
#else
  BasePlatform::PurchaseAck(purchase, order_id);
#endif
}

void BasePlatformApple::DoOpenURL(const std::string& url) {
#if BA_XCODE_BUILD
#if BA_OSTYPE_MACOS
  BallisticaKit::CocoaFromCppOpenURL(url);
#else
  BallisticaKit::UIKitFromCppOpenURL(url);
#endif  // BA_OSTYPE_MACOS

#else
  // For non-xcode builds, go with the default (Python webbrowser module).
  BasePlatform::DoOpenURL(url);
#endif  // BA_XCODE_BUILD
}

}  // namespace ballistica::base

#endif  // BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
