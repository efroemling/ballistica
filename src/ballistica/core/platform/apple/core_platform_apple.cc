// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/core/platform/apple/core_platform_apple.h"

#if BA_XCODE_BUILD
#include <unistd.h>
#endif

#include <uuid/uuid.h>

#if BA_XCODE_BUILD
#include "ballistica/base/platform/apple/apple_utils.h"
#include "ballistica/base/platform/apple/from_swift.h"
#include "ballistica/shared/math/rect.h"
#endif

#if BA_XCODE_BUILD
// This needs to be below ballistica headers since it relies on
// some types in them but does not include headers itself.
#include <BallisticaKit-Swift.h>
#endif

namespace ballistica::core {

CorePlatformApple::CorePlatformApple() = default;

auto CorePlatformApple::GetDeviceV1AccountUUIDPrefix() -> std::string {
#if BA_OSTYPE_MACOS
  return "m";
#elif BA_OSTYPE_IOS_TVOS
  return "i";
#else
#error FIXME
#endif
}

// Legacy for device-accounts; don't modify this code.
auto CorePlatformApple::GetRealLegacyDeviceUUID(std::string* uuid) -> bool {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  *uuid = std::string(BallisticaKit::CocoaFromCpp::GetLegacyDeviceUUID());
  return true;
#endif
#if BA_OSTYPE_IOS_TVOS
  *uuid = std::string(BallisticaKit::UIKitFromCpp::GetLegacyDeviceUUID());
  // *uuid = base::AppleUtils::GetIOSUUID();
  return true;
#endif
  return false;
}

#if BA_OSTYPE_MACOS && !BA_XCODE_BUILD
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
#endif  // BA_OSTYPE_MACOS && !BA_XCODE_BUILD

// For semi-permanent public-uuid hashes; can modify this if we
// find better sources.
auto CorePlatformApple::GetDeviceUUIDInputs() -> std::list<std::string> {
  std::list<std::string> out;
#if BA_OSTYPE_MACOS
#if BA_XCODE_BUILD
  out.push_back(
      std::string(BallisticaKit::CocoaFromCpp::GetLegacyDeviceUUID()));
#else   // BA_XCODE_BUILD
  out.push_back(GetMacUUIDFallback());
#endif  // BA_XCODE_BUILD
#endif  // BA_OSTYPE_MACOS

#if BA_OSTYPE_IOS_TVOS
  // out.push_back(base::AppleUtils::GetIOSUUID());
  out.push_back(
      std::string(BallisticaKit::UIKitFromCpp::GetLegacyDeviceUUID()));
#endif
  return out;
}

auto CorePlatformApple::GenerateUUID() -> std::string {
  char buffer[100];
  uuid_t uuid;
  uuid_generate(uuid);
  uuid_unparse(uuid, buffer);
  return buffer;
}

auto CorePlatformApple::DoGetConfigDirectoryMonolithicDefault()
    -> std::optional<std::string> {
#if BA_OSTYPE_IOS_TVOS
  // FIXME - this doesn't seem right.
  printf("FIXME: get proper default-config-dir\n");
  return std::string(getenv("HOME")) + "/Library";
#elif BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return std::string(BallisticaKit::CocoaFromCpp::GetApplicationSupportPath())
         + "/BallisticaKit";
#else
  return CorePlatform::DoGetConfigDirectoryMonolithicDefault();
#endif
}

auto CorePlatformApple::DoHasTouchScreen() -> bool {
#if BA_OSTYPE_IOS
  return true;
#else
  return false;
#endif
}

auto CorePlatformApple::GetDefaultUIScale() -> UIScale {
#if BA_OSTYPE_IOS
  if (BallisticaKit::UIKitFromCpp::IsTablet()) {
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
#if BA_OSTYPE_IOS_TVOS
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
  return BallisticaKit::FromCpp::GetResourcesPath();
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
  base::AppleUtils::SubmitScore(game, version, score);
#else
  CorePlatform::SubmitScore(game, version, score);
#endif
}

void CorePlatformApple::ReportAchievement(const std::string& achievement) {
#if BA_USE_GAME_CENTER
  base::AppleUtils::ReportAchievement(achievement);
#else
  CorePlatform::ReportAchievement(achievement);
#endif
}

void CorePlatformApple::ResetAchievements() {
#if BA_USE_GAME_CENTER
  base::AppleUtils::ResetGameCenterAchievements();
#else
  CorePlatform::ResetAchievements();
#endif
}

auto CorePlatformApple::HaveLeaderboard(const std::string& game,
                                        const std::string& config) -> bool {
#if BA_USE_GAME_CENTER
  return base::AppleUtils::HaveGameCenterLeaderboard(game, config);
#else
  return CorePlatform::HaveLeaderboard(game, config);
#endif
}

void CorePlatformApple::ShowOnlineScoreUI(const std::string& show,
                                          const std::string& game,
                                          const std::string& game_version) {
#if BA_USE_GAME_CENTER
  base::AppleUtils::ShowOnlineScoreUI(show, game, game_version);
#else
  CorePlatform::ShowOnlineScoreUI(show, game, game_version);
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

void CorePlatformApple::GameCenterLogin() {
#if BA_USE_GAME_CENTER
  base::AppleUtils::DoGameCenterLogin();
#else
  CorePlatform::GameCenterLogin();
#endif
}

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

void CorePlatformApple::OpenFileExternally(const std::string& path) {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::OpenFileExternally(path);
#else
  CorePlatform::OpenFileExternally(path);
#endif
}

void CorePlatformApple::OpenDirExternally(const std::string& path) {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::OpenDirExternally(path);
#else
  CorePlatform::OpenDirExternally(path);
#endif
}

void CorePlatformApple::MacMusicAppInit() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::MacMusicAppInit();
  // base::AppleUtils::MacMusicAppInit();
#else
  CorePlatform::MacMusicAppInit();
#endif
}
auto CorePlatformApple::MacMusicAppGetVolume() -> int {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::MacMusicAppGetVolume();
  // return static_cast<int>(base::AppleUtils::MacMusicAppGetVolume());
#else
  return CorePlatform::MacMusicAppGetVolume();
#endif
}
void CorePlatformApple::MacMusicAppSetVolume(int volume) {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::MacMusicAppSetVolume(volume);
  // base::AppleUtils::MacMusicAppSetVolume(volume);
#else
  CorePlatform::MacMusicAppSetVolume(volume);
#endif
}

// KILL THIS.
void CorePlatformApple::MacMusicAppGetLibrarySource() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  // base::AppleUtils::MacMusicAppGetLibrarySource();
#else
  CorePlatform::MacMusicAppGetLibrarySource();
#endif
}
void CorePlatformApple::MacMusicAppStop() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::MacMusicAppStop();
  // base::AppleUtils::MacMusicAppStop();
#else
  CorePlatform::MacMusicAppStop();
#endif
}

auto CorePlatformApple::MacMusicAppPlayPlaylist(const std::string& playlist)
    -> bool {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return BallisticaKit::CocoaFromCpp::MacMusicAppPlayPlaylist(playlist);
  // return base::AppleUtils::MacMusicAppPlayPlaylist(playlist.c_str());
#else
  return CorePlatform::MacMusicAppPlayPlaylist(playlist);
#endif
}

auto CorePlatformApple::MacMusicAppGetPlaylists() -> std::list<std::string> {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  BallisticaKit::CocoaFromCpp::MacMusicAppGetPlaylists();
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

auto CorePlatformApple::GetPlatformName() -> std::string {
#if BA_OSTYPE_MACOS
  return "mac";
#elif BA_OSTYPE_IOS_TVOS
  return "ios";
#else
#error FIXME
#endif
}

auto CorePlatformApple::GetSubplatformName() -> std::string {
#if BA_TEST_BUILD
  return "test";
#elif BA_XCODE_BUILD
  return "appstore";
#else
  return "";
#endif
}

}  // namespace ballistica::core

#endif  // BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
