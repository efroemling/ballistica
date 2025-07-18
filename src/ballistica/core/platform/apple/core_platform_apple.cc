// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/exception.h"
#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
#include "ballistica/core/platform/apple/core_platform_apple.h"

#if BA_XCODE_BUILD
#include <CoreServices/CoreServices.h>
#include <unistd.h>
#endif

#include <uuid/uuid.h>

#include <cstdio>
#include <list>
#include <string>
#include <vector>

#if BA_XCODE_BUILD
#include "ballistica/base/platform/apple/from_swift.h"
#include "ballistica/shared/math/rect.h"
#endif

#include "ballistica/shared/ballistica.h"

#if BA_XCODE_BUILD
// This needs to be below ballistica headers since it relies on
// some types in them but does not include headers itself.
#include <BallisticaKit-Swift.h>
#endif

namespace ballistica::core {

CorePlatformApple::CorePlatformApple() = default;

auto CorePlatformApple::GetDeviceV1AccountUUIDPrefix() -> std::string {
  if (g_buildconfig.platform_macos()) {
    return "m";
  } else if (g_buildconfig.platform_ios_tvos()) {
    return "i";
  } else {
    FatalError("Unhandled V1 UUID case.");
    return "";
  }
}

auto CorePlatformApple::DoGetDeviceName() -> std::string {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD

#pragma clang diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

  CFStringRef machineName = CSCopyMachineName();
  if (machineName != nullptr) {
    char buffer[256];
    std::string out;
    if (CFStringGetCString(machineName, buffer, sizeof(buffer),
                           kCFStringEncodingUTF8)) {
      out = buffer;
    }
    CFRelease(machineName);
    return out;
  }

#pragma clang diagnostic pop

  // FIXME - This code currently hangs if there is an apostrophe in the
  // device name. Should hopefully be fixed in Swift 5.10.
  // https://github.com/apple/swift/issues/69870

  // Ask swift for a pretty name if possible.
  // return BallisticaKit::CocoaFromCpp::getDeviceName();
#elif BA_PLATFORM_IOS_TVOS && BA_XCODE_BUILD
  return BallisticaKit::UIKitFromCpp::getDeviceName();
#endif
  return CorePlatform::DoGetDeviceName();
}

auto CorePlatformApple::DoGetDeviceDescription() -> std::string {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::getDeviceModelName();
#endif
  return CorePlatform::DoGetDeviceDescription();
}

auto CorePlatformApple::GetOSVersionString() -> std::string {
#if BA_XCODE_BUILD
  return BallisticaKit::FromCpp::getOSVersion();
#endif
  return CorePlatform::GetOSVersionString();
}

// Legacy for device-accounts; don't modify this code.
auto CorePlatformApple::GetRealLegacyDeviceUUID(std::string* uuid) -> bool {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  *uuid = std::string(BallisticaKit::CocoaFromCpp::getLegacyDeviceUUID());
  return true;
#endif
#if BA_PLATFORM_IOS_TVOS
  *uuid = std::string(BallisticaKit::UIKitFromCpp::getLegacyDeviceUUID());
  // *uuid = base::AppleUtils::GetIOSUUID();
  return true;
#endif
  return false;
}

#if BA_PLATFORM_MACOS && !BA_XCODE_BUILD
// A fallback function to grab IOPlatformUUID
// (for builds where we don't have access to swift/objc stuff).
static auto GetMacUUIDFallback() -> std::string {
  char buffer[1024];

  // This will get us a full line like "IOPlatformUUID" = "VALUE". We
  // could trim it down to just the value, but it shouldn't hurt anything
  // to just hash the full line.
  if (FILE* inproc = popen(
          "ioreg -d2 -c IOPlatformExpertDevice | grep IOPlatformUUID", "r")) {
    auto size{fread(buffer, 1, sizeof(buffer) - 1, inproc)};
    fclose(inproc);
    assert(size < sizeof(buffer));
    buffer[size] = 0;
    return buffer;
  } else {
    throw Exception("Unable to access IOPlatformUUID");
  }
}
#endif  // BA_PLATFORM_MACOS && !BA_XCODE_BUILD

// For semi-permanent public-uuid hashes; can modify this if we
// find better sources.
auto CorePlatformApple::GetDeviceUUIDInputs() -> std::list<std::string> {
  std::list<std::string> out;
#if BA_PLATFORM_MACOS
#if BA_XCODE_BUILD
  out.push_back(
      std::string(BallisticaKit::CocoaFromCpp::getLegacyDeviceUUID()));
#else   // BA_XCODE_BUILD
  out.push_back(GetMacUUIDFallback());
#endif  // BA_XCODE_BUILD
#endif  // BA_PLATFORM_MACOS

#if BA_PLATFORM_IOS_TVOS
  // out.push_back(base::AppleUtils::GetIOSUUID());
  out.push_back(
      std::string(BallisticaKit::UIKitFromCpp::getLegacyDeviceUUID()));
#endif
  return out;
}

auto CorePlatformApple::DoGetConfigDirectoryMonolithicDefault()
    -> std::optional<std::string> {
#if BA_PLATFORM_IOS_TVOS
  // FIXME - this doesn't seem right.
  printf("FIXME: get proper default-config-dir\n");
  return std::string(getenv("HOME")) + "/Library";
#elif BA_PLATFORM_MACOS && BA_XCODE_BUILD
  return std::string(BallisticaKit::CocoaFromCpp::getApplicationSupportPath())
         + "/BallisticaKit";
#else
  return CorePlatform::DoGetConfigDirectoryMonolithicDefault();
#endif
}

auto CorePlatformApple::DoGetCacheDirectoryMonolithicDefault()
    -> std::optional<std::string> {
#if BA_XCODE_BUILD
  return BallisticaKit::FromCpp::getCacheDirectoryPath();
#else
  return CorePlatform::DoGetCacheDirectoryMonolithicDefault();
#endif
}

auto CorePlatformApple::DoHasTouchScreen() -> bool {
#if BA_PLATFORM_IOS
  return true;
#else
  return false;
#endif
}

auto CorePlatformApple::GetDefaultUIScale() -> UIScale {
#if BA_PLATFORM_IOS
  if (BallisticaKit::UIKitFromCpp::isTablet()) {
    // if (base::AppleUtils::IsTablet()) {
    return UIScale::kMedium;
  } else {
    return UIScale::kSmall;
  }
#else
  // The default case handles mac & tvos.
  return CorePlatform::GetDefaultUIScale();
#endif
}

auto CorePlatformApple::IsRunningOnDesktop() -> bool {
#if BA_PLATFORM_IOS_TVOS
  return false;
#else
  return true;
#endif
}

void CorePlatformApple::EmitPlatformLog(const std::string& name, LogLevel level,
                                        const std::string& msg) {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD

  // HMM: do we want to use proper logging APIs here or simple printing?
  // base::AppleUtils::NSLogStr(msg);
  CorePlatform::EmitPlatformLog(name, level, msg);
#else

  // Fall back to default handler...
  CorePlatform::EmitPlatformLog(name, level, msg);
#endif
}

auto CorePlatformApple::DoGetDataDirectoryMonolithicDefault() -> std::string {
#if BA_XCODE_BUILD
  return BallisticaKit::FromCpp::getResourcesPath();
#else
  // Fall back to default.
  return CorePlatform::DoGetDataDirectoryMonolithicDefault();
#endif
}

#if BA_XCODE_BUILD
class TextTextureWrapper_ {
 public:
  TextTextureWrapper_(int width, int height,
                      const std::vector<std::string>& strings,
                      const std::vector<float>& positions,
                      const std::vector<float>& widths, float scale)
      : data{BallisticaKit::TextTextureData::init(width, height, strings,
                                                  positions, widths, scale)} {}
  BallisticaKit::TextTextureData data;
};
#endif

auto CorePlatformApple::CreateTextTexture(
    int width, int height, const std::vector<std::string>& strings,
    const std::vector<float>& positions, const std::vector<float>& widths,
    float scale) -> void* {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  auto* wrapper =
      new TextTextureWrapper_(width, height, strings, positions, widths, scale);
  //  wrapper->old = base::AppleUtils::CreateTextTexture(width, height, strings,
  //                                                     positions, widths,
  //                                                     scale);
  return wrapper;
#else
  return CorePlatform::CreateTextTexture(width, height, strings, positions,
                                         widths, scale);
#endif
}

auto CorePlatformApple::GetTextTextureData(void* tex) -> uint8_t* {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  auto* wrapper = static_cast<TextTextureWrapper_*>(tex);
  return static_cast<uint8_t*>(wrapper->data.getTextTextureData());
  // return base::AppleUtils::GetTextTextureData(wrapper->old);
#else
  return CorePlatform::GetTextTextureData(tex);
#endif
}

void CorePlatformApple::GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                              float* width) {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD

  auto vals = BallisticaKit::TextTextureData::getTextBoundsAndWidth(text);
  assert(vals.getCount() == 5);
  r->l = vals[0];
  r->r = vals[1];
  r->b = vals[2];
  r->t = vals[3];
  *width = vals[4];

//  base::AppleUtils::GetTextBoundsAndWidth(text, r, width);
//  printf("GOT BOUNDS l=%.2f r=%.2f b=%.2f t=%.2f w=%.2f\n", r->l, r->r, r->b,
//  r->t, *width); printf("SWIFT BOUNDS l=%.2f r=%.2f b=%.2f t=%.2f w=%.2f\n",
//         vals[0], vals[1], vals[2], vals[3], vals[4]);
#else
  CorePlatform::GetTextBoundsAndWidth(text, r, width);
#endif
}

void CorePlatformApple::FreeTextTexture(void* tex) {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  auto* wrapper = static_cast<TextTextureWrapper_*>(tex);
  // base::AppleUtils::FreeTextTexture(wrapper->old);
  delete wrapper;
#else
  CorePlatform::FreeTextTexture(tex);
#endif
}

void CorePlatformApple::SubmitScore(const std::string& game,
                                    const std::string& version, int64_t score) {
#if BA_USE_GAME_CENTER
  BallisticaKit::GameCenterContext::submitScore(game, version, score);
  // base::AppleUtils::SubmitScore(game, version, score);
#else
  CorePlatform::SubmitScore(game, version, score);
#endif
}

void CorePlatformApple::ReportAchievement(const std::string& achievement) {
#if BA_USE_GAME_CENTER
  BallisticaKit::GameCenterContext::reportAchievement(achievement);
  // base::AppleUtils::ReportAchievement(achievement);
#else
  CorePlatform::ReportAchievement(achievement);
#endif
}

void CorePlatformApple::ResetAchievements() {
#if BA_USE_GAME_CENTER
  BallisticaKit::GameCenterContext::resetAchievements();
  // base::AppleUtils::ResetGameCenterAchievements();
#else
  CorePlatform::ResetAchievements();
#endif
}

auto CorePlatformApple::HaveLeaderboard(const std::string& game,
                                        const std::string& config) -> bool {
#if BA_USE_GAME_CENTER
  return BallisticaKit::GameCenterContext::haveLeaderboard(game, config);
  // return base::AppleUtils::HaveGameCenterLeaderboard(game, config);
#else
  return CorePlatform::HaveLeaderboard(game, config);
#endif
}

void CorePlatformApple::ShowGameServiceUI(const std::string& show,
                                          const std::string& game,
                                          const std::string& game_version) {
#if BA_USE_GAME_CENTER
  BallisticaKit::GameCenterContext::showGameServiceUI(show, game, game_version);
  // base::AppleUtils::ShowGameServiceUI(show, game, game_version);
#else
  CorePlatform::ShowGameServiceUI(show, game, game_version);
#endif
}

// auto CorePlatformApple::NewAutoReleasePool() -> void* {
// #if BA_XCODE_BUILD
//   return base::AppleUtils::NewAutoReleasePool();
// #else
//   return CorePlatform::NewAutoReleasePool();
// #endif
// }

// void CorePlatformApple::DrainAutoReleasePool(void* pool) {
// #if BA_XCODE_BUILD
//   base::AppleUtils::DrainAutoReleasePool(pool);
// #else
//   CorePlatform::DrainAutoReleasePool(pool);
// #endif
// }

// void CorePlatformApple::GameCenterLogin() {
// #if BA_USE_GAME_CENTER
//   BallisticaKit::GameCenterContext::signIn();
//   // base::AppleUtils::DoGameCenterLogin();
// #else
//   CorePlatform::GameCenterLogin();
// #endif
// }

auto CorePlatformApple::IsOSPlayingMusic() -> bool {
#if BA_XCODE_BUILD
  // FIXME - should look into doing this properly these days, or whether
  // this is still needed at all.
  return false;
  // return base::AppleUtils::IsMusicPlaying();
#else
  return CorePlatform::IsOSPlayingMusic();
#endif
}

void CorePlatformApple::MacMusicAppInit() {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::macMusicAppInit();
  // base::AppleUtils::MacMusicAppInit();
#else
  CorePlatform::MacMusicAppInit();
#endif
}
auto CorePlatformApple::MacMusicAppGetVolume() -> int {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::macMusicAppGetVolume();
  // return static_cast<int>(base::AppleUtils::MacMusicAppGetVolume());
#else
  return CorePlatform::MacMusicAppGetVolume();
#endif
}
void CorePlatformApple::MacMusicAppSetVolume(int volume) {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::macMusicAppSetVolume(volume);
  // base::AppleUtils::MacMusicAppSetVolume(volume);
#else
  CorePlatform::MacMusicAppSetVolume(volume);
#endif
}

void CorePlatformApple::MacMusicAppStop() {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::macMusicAppStop();
  // base::AppleUtils::MacMusicAppStop();
#else
  CorePlatform::MacMusicAppStop();
#endif
}

auto CorePlatformApple::MacMusicAppPlayPlaylist(const std::string& playlist)
    -> bool {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::macMusicAppPlayPlaylist(playlist);
  // return base::AppleUtils::MacMusicAppPlayPlaylist(playlist.c_str());
#else
  return CorePlatform::MacMusicAppPlayPlaylist(playlist);
#endif
}

auto CorePlatformApple::MacMusicAppGetPlaylists() -> std::list<std::string> {
#if BA_PLATFORM_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::macMusicAppGetPlaylists();
  // mac_music_app_playlists_.clear();
  // mac_music_app_playlists_.push_back("foof");
  // mac_music_app_playlists_.push_back("barf");
  //  std::list<std::string> out;
  //  for (auto&& val : vals) {
  //    out.push_back(std::string(val));
  //  }
  //  return out;
  return mac_music_app_playlists();
#else
  return CorePlatform::MacMusicAppGetPlaylists();
#endif
}

auto CorePlatformApple::GetLegacyPlatformName() -> std::string {
#if BA_PLATFORM_MACOS
  return "mac";
#elif BA_PLATFORM_IOS_TVOS
  return "ios";
#else
#error FIXME
#endif
}

auto CorePlatformApple::GetLegacySubplatformName() -> std::string {
#if BA_VARIANT_TEST_BUILD
  return "test";
#elif BA_XCODE_BUILD
  return "appstore";
#else
  return "";
#endif
}

auto CorePlatformApple::GetBaLocale() -> std::string {
#if BA_XCODE_BUILD
  if (!ba_locale_.has_value()) {
    ba_locale_ = std::string(BallisticaKit::FromCpp::getBaLocale());
  }
  return *ba_locale_;
#else
  return CorePlatform::GetBaLocale();
#endif
}

auto CorePlatformApple::GetLocaleTag() -> std::string {
#if BA_XCODE_BUILD
  if (!locale_tag_.has_value()) {
    locale_tag_ = std::string(BallisticaKit::FromCpp::getLocaleTag());
  }
  return *locale_tag_;
#else
  return CorePlatform::GetLocaleTag();
#endif
}

auto CorePlatformApple::CanShowBlockingFatalErrorDialog() -> bool {
  if (g_buildconfig.xcode_build() && g_buildconfig.platform_macos()) {
    return true;
  }
  return CorePlatform::CanShowBlockingFatalErrorDialog();
}

void CorePlatformApple::BlockingFatalErrorDialog(const std::string& message) {
#if BA_XCODE_BUILD && BA_PLATFORM_MACOS
  BallisticaKit::CocoaFromCpp::blockingFatalErrorDialog(message);
#else
  CorePlatform::BlockingFatalErrorDialog(message);
#endif
}

}  // namespace ballistica::core

#endif  // BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
