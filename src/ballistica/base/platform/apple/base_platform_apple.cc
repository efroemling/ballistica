// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
#include "ballistica/base/platform/apple/base_platform_apple.h"

#include <string>

#include "ballistica/core/logging/logging.h"

#if BA_XCODE_BUILD
#include "ballistica/base/platform/apple/from_swift.h"
#endif

#if BA_XCODE_BUILD
// This needs to be below ballistica headers since it relies on
// some types in them but does not include headers itself.
#include <BallisticaKit-Swift.h>
#endif

namespace ballistica::base {

BasePlatformApple::BasePlatformApple() {
  // On iOS, keep the device from falling asleep in our app
#if BA_PLATFORM_IOS_TVOS
  // AppleUtils::DisableIdleTimer();
#endif
}

void BasePlatformApple::DoPurchase(const std::string& item) {
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::purchase(item);
  // AppleUtils::DoStoreKitPurchase(item);
#else
  BasePlatform::DoPurchase(item);
#endif
}

void BasePlatformApple::RestorePurchases() {
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::restorePurchases();
  // AppleUtils::DoStoreKitPurchaseRestore();
#else
  BasePlatform::RestorePurchases();
#endif
}

void BasePlatformApple::PurchaseAck(const std::string& purchase,
                                    const std::string& order_id) {
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::purchaseAck(purchase, order_id);
#else
  BasePlatform::PurchaseAck(purchase, order_id);
#endif
}

void BasePlatformApple::DoOpenURL(const std::string& url) {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::openURL(url);
#else
  BallisticaKit::UIKitFromCpp::openURL(url);
#endif  // BA_PLATFORM_MACOS

#else
  // For non-xcode builds, go with the default (Python webbrowser module).
  BasePlatform::DoOpenURL(url);
#endif  // BA_XCODE_BUILD
}

auto BasePlatformApple::OverlayWebBrowserIsSupported() -> bool {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::haveOverlayWebBrowser();
#else
  // TODO(ericf): Implement for uikit.
  return BasePlatform::OverlayWebBrowserIsSupported();
#endif  // BA_PLATFORM_MACOS

#else
  // Fall back to default for non-xcode apple builds.
  return BasePlatform::OverlayWebBrowserIsSupported();
#endif  // BA_XCODE_BUILD
}

void BasePlatformApple::DoOverlayWebBrowserOpenURL(const std::string& url) {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::openURLInOverlayWebBrowser(url);
#else
  // TODO(ericf): Implement for uikit.
  BasePlatform::DoOverlayWebBrowserOpenURL(url);
#endif  // BA_PLATFORM_MACOS

#else
  // For non-xcode builds, go with the default (Python webbrowser module).
  BasePlatform::DoOverlayWebBrowserOpenURL(url);
#endif  // BA_XCODE_BUILD
}

void BasePlatformApple::DoOverlayWebBrowserClose() {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::closeOverlayWebBrowser();
#else
  // TODO(ericf): Implement for uikit.
  BasePlatform::OverlayWebBrowserIsSupported();
#endif  // BA_PLATFORM_MACOS

#else
  // Fall back to default for non-xcode apple builds.
  BasePlatform::OverlayWebBrowserIsSupported();
#endif  // BA_XCODE_BUILD
}

void BasePlatformApple::LoginAdapterGetSignInToken(
    const std::string& login_type, int attempt_id) {
#if BA_USE_GAME_CENTER
  if (login_type == "game_center") {
    BallisticaKit::GameCenterContext::getSignInToken(attempt_id);
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Got unexpected get-sign-in-token login-type: " + login_type);
  }
#else
  BasePlatform::LoginAdapterGetSignInToken(login_type, attempt_id);
#endif
}

void BasePlatformApple::LoginAdapterBackEndActiveChange(
    const std::string& login_type, bool active) {
#if BA_USE_GAME_CENTER
  if (login_type == "game_center") {
    BallisticaKit::GameCenterContext::backEndActiveChange(active);
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Got unexpected back-end-active-change login-type: " + login_type);
  }
#else
  BasePlatform::LoginAdapterBackEndActiveChange(login_type, active);
#endif
}

auto BasePlatformApple::SupportsOpenDirExternally() -> bool {
#if BA_XCODE_BUILD && BA_PLATFORM_MACOS
  return true;
#else
  return BasePlatform::SupportsOpenDirExternally();
#endif
}

void BasePlatformApple::OpenDirExternally(const std::string& path) {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::openDirExternally(path);
#else
  BasePlatform::OpenDirExternally(path);
#endif
}

void BasePlatformApple::OpenFileExternally(const std::string& path) {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::openFileExternally(path);
#else
  BasePlatform::OpenFileExternally(path);
#endif
}

}  // namespace ballistica::base

#endif  // BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
