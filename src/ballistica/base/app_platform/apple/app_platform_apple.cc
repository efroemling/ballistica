// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
#include "ballistica/base/app_platform/apple/app_platform_apple.h"

#include <string>

#include "ballistica/core/logging/logging.h"

#if BA_XCODE_BUILD
#include "ballistica/base/app_platform/apple/from_swift.h"
#endif

#if BA_XCODE_BUILD
// This needs to be below ballistica headers since it relies on
// some types in them but does not include headers itself.
#include <BallisticaKit-Swift.h>
#endif

namespace ballistica::base {

AppPlatformApple::AppPlatformApple() {
  // On iOS, keep the device from falling asleep in our app
#if BA_PLATFORM_IOS_TVOS
  // AppleUtils::DisableIdleTimer();
#endif
}

void AppPlatformApple::DoPurchase(const std::string& item) {
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::purchase(item);
  // AppleUtils::DoStoreKitPurchase(item);
#else
  AppPlatform::DoPurchase(item);
#endif
}

void AppPlatformApple::RestorePurchases() {
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::restorePurchases();
  // AppleUtils::DoStoreKitPurchaseRestore();
#else
  AppPlatform::RestorePurchases();
#endif
}

void AppPlatformApple::PurchaseAck(const std::string& purchase,
                                   const std::string& order_id) {
#if BA_USE_STORE_KIT
  BallisticaKit::StoreKitContext::purchaseAck(purchase, order_id);
#else
  AppPlatform::PurchaseAck(purchase, order_id);
#endif
}

void AppPlatformApple::DoOpenURL(const std::string& url) {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::openURL(url);
#else
  BallisticaKit::UIKitFromCpp::openURL(url);
#endif  // BA_PLATFORM_MACOS

#else
  // For non-xcode builds, go with the default (Python webbrowser module).
  AppPlatform::DoOpenURL(url);
#endif  // BA_XCODE_BUILD
}

auto AppPlatformApple::DoHasGyro() -> bool {
#if BA_XCODE_BUILD && !BA_PLATFORM_MACOS
  return BallisticaKit::UIKitFromCpp::haveGyro();
#else
  // Macs have no gyro, and non-xcode apple builds have no Swift bridge to
  // ask through.
  return AppPlatform::DoHasGyro();
#endif
}

auto AppPlatformApple::OverlayWebBrowserIsSupported() -> bool {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  return BallisticaKit::CocoaFromCpp::haveOverlayWebBrowser();
#else
  return BallisticaKit::UIKitFromCpp::haveOverlayWebBrowser();
#endif  // BA_PLATFORM_MACOS

#else
  // Fall back to default for non-xcode apple builds.
  return AppPlatform::OverlayWebBrowserIsSupported();
#endif  // BA_XCODE_BUILD
}

void AppPlatformApple::DoOverlayWebBrowserOpenURL(const std::string& url) {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::openURLInOverlayWebBrowser(url);
#else
  BallisticaKit::UIKitFromCpp::openURLInOverlayWebBrowser(url);
#endif  // BA_PLATFORM_MACOS

#else
  // For non-xcode builds, go with the default (Python webbrowser module).
  AppPlatform::DoOverlayWebBrowserOpenURL(url);
#endif  // BA_XCODE_BUILD
}

void AppPlatformApple::DoOverlayWebBrowserClose() {
#if BA_XCODE_BUILD
#if BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::closeOverlayWebBrowser();
#else
  BallisticaKit::UIKitFromCpp::closeOverlayWebBrowser();
#endif  // BA_PLATFORM_MACOS

#else
  // Fall back to default for non-xcode apple builds.
  AppPlatform::OverlayWebBrowserIsSupported();
#endif  // BA_XCODE_BUILD
}

void AppPlatformApple::LoginAdapterGetSignInToken(const std::string& login_type,
                                                  int attempt_id) {
#if BA_USE_GAME_CENTER
  if (login_type == "game_center") {
    BallisticaKit::GameCenterContext::getSignInToken(attempt_id);
  } else {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Got unexpected get-sign-in-token login-type: " + login_type);
  }
#else
  AppPlatform::LoginAdapterGetSignInToken(login_type, attempt_id);
#endif
}

void AppPlatformApple::LoginAdapterBackEndActiveChange(
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
  AppPlatform::LoginAdapterBackEndActiveChange(login_type, active);
#endif
}

auto AppPlatformApple::SupportsOpenDirExternally() -> bool {
#if BA_XCODE_BUILD && BA_PLATFORM_MACOS
  return true;
#else
  return AppPlatform::SupportsOpenDirExternally();
#endif
}

void AppPlatformApple::OpenDirExternally(const std::string& path) {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::openDirExternally(path);
#else
  AppPlatform::OpenDirExternally(path);
#endif
}

void AppPlatformApple::OpenFileExternally(const std::string& path) {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::openFileExternally(path);
#else
  AppPlatform::OpenFileExternally(path);
#endif
}

auto AppPlatformApple::HaveStringEditor() -> bool {
#if BA_PLATFORM_IOS_TVOS && BA_XCODE_BUILD
  // iOS/tvOS text entry goes through our UIKit editor dialog; those
  // platforms feed the engine no text events for inline editing.
  return true;
#else
  // Mac edits text widgets inline from real key/text events.
  return AppPlatform::HaveStringEditor();
#endif
}

void AppPlatformApple::DoInvokeStringEditor(const std::string& title,
                                            const std::string& value,
                                            std::optional<int> max_chars,
                                            bool is_password,
                                            const std::string& kind) {
#if BA_PLATFORM_IOS_TVOS && BA_XCODE_BUILD
  // Note that we're on the logic thread here (holding the GIL); the
  // Swift side hops to main asynchronously to present, which is the
  // only safe direction (a blocking hop while holding the GIL can
  // deadlock against the main thread - see UIKitFromCpp.onMain).
  BallisticaKit::UIKitFromCpp::invokeStringEditor(
      title, value, max_chars.has_value() ? *max_chars : -1, is_password, kind);
#else
  AppPlatform::DoInvokeStringEditor(title, value, max_chars, is_password, kind);
#endif
}

}  // namespace ballistica::base

#endif  // BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
