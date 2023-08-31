// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/base/platform/apple/base_platform_apple.h"

#if BA_XCODE_BUILD
#include <unistd.h>
#endif
#include <uuid/uuid.h>

#if BA_XCODE_BUILD
#include "ballistica/core/platform/apple/apple_utils.h"
#endif

namespace ballistica::base {

#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-use-equals-default"

BasePlatformApple::BasePlatformApple() {  // NOLINT: trivial constructor false
                                          // positive
  // On iOS, keep the device from falling asleep in our app
#if BA_OSTYPE_IOS_TVOS
  core::AppleUtils::DisableIdleTimer();
#endif
}

#pragma clang diagnostic pop

void BasePlatformApple::DoPurchase(const std::string& item) {
#if BA_USE_STORE_KIT
  core::AppleUtils::DoStoreKitPurchase(item);
#else
  BasePlatform::DoPurchase(item);
#endif
}

void BasePlatformApple::RestorePurchases() {
#if BA_USE_STORE_KIT
  core::AppleUtils::DoStoreKitPurchaseRestore();
#else
  BasePlatform::RestorePurchases();
#endif
}

void BasePlatformApple::PurchaseAck(const std::string& purchase,
                                    const std::string& order_id) {
#if BA_XCODE_BUILD
  core::AppleUtils::PurchaseAck(purchase, order_id);
#else
  BasePlatform::PurchaseAck(purchase, order_id);
#endif
}

void BasePlatformApple::DoOpenURL(const std::string& url) {
#if BA_XCODE_BUILD
  // Go ahead and do this ourself. Though perhaps the default
  // Python path would be fine.
  core::AppleUtils::OpenURL(url.c_str());
#else
  // Otherwise go with the default (Python webbrowser module).
  BasePlatform::DoOpenURL(url);
#endif
}

void BasePlatformApple::QuitApp() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  core::AppleUtils::Quit();  // will post a cocoa terminate
#else
  BasePlatform::QuitApp();
#endif
}

}  // namespace ballistica::base

#endif  // BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
