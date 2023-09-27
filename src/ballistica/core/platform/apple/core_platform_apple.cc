// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/core/platform/apple/core_platform_apple.h"

#if BA_XCODE_BUILD
#include <unistd.h>
#endif
#include <uuid/uuid.h>

#if BA_XCODE_BUILD
#include "ballistica/base/platform/apple/apple_utils.h"
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
  *uuid = base::AppleUtils::GetMacUUID();
  return true;
#endif
#if BA_OSTYPE_IOS_TVOS
  *uuid = base::AppleUtils::GetIOSUUID();
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
  out.push_back(base::AppleUtils::GetMacUUID());
#else   // BA_XCODE_BUILD
  out.push_back(GetMacUUIDFallback());
#endif  // BA_XCODE_BUILD
#endif  // BA_OSTYPE_MACOS

#if BA_OSTYPE_IOS_TVOS
  out.push_back(base::AppleUtils::GetIOSUUID());
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
  return base::AppleUtils::GetApplicationSupportPath() + "/BallisticaKit";
#else
  return CorePlatform::DoGetConfigDirectoryMonolithicDefault();
#endif
}

auto CorePlatformApple::GetLocale() -> std::string {
#if BA_XCODE_BUILD
  return base::AppleUtils::GetLocaleString();
#else
  return CorePlatform::GetLocale();
#endif
}

auto CorePlatformApple::DoGetDeviceName() -> std::string {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return base::AppleUtils::GetDeviceName();
#else
  return CorePlatform::DoGetDeviceName();
#endif
}

auto CorePlatformApple::DoHasTouchScreen() -> bool {
#if BA_OSTYPE_IOS
  return true;
#else
  return false;
#endif
}

auto CorePlatformApple::GetUIScale() -> UIScale {
#if BA_OSTYPE_IOS
  if (base::AppleUtils::IsTablet()) {
    return UIScale::kMedium;
  } else {
    return UIScale::kSmall;
  }
#else
  // default case handles mac/tvos
  return CorePlatform::GetUIScale();
#endif
}

auto CorePlatformApple::IsRunningOnDesktop() -> bool {
#if BA_OSTYPE_IOS_TVOS
  return false;
#else
  return true;
#endif
}

void CorePlatformApple::DisplayLog(const std::string& name, LogLevel level,
                                   const std::string& msg) {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD

  // HMM: do we want to use proper logging APIs here or simple printing?
  // base::AppleUtils::NSLogStr(msg);
  CorePlatform::DisplayLog(name, level, msg);
#else

  // Fall back to default handler...
  CorePlatform::DisplayLog(name, level, msg);
#endif
}

auto CorePlatformApple::DoGetDataDirectoryMonolithicDefault() -> std::string {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  // On Apple package-y builds use our resources dir.
  return base::AppleUtils::GetResourcesPath();
#else
  // Fall back to default.
  return CorePlatform::DoGetDataDirectoryMonolithicDefault();
#endif
}

void CorePlatformApple::GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                              float* width) {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  base::AppleUtils::GetTextBoundsAndWidth(text, r, width);
#else
  CorePlatform::GetTextBoundsAndWidth(text, r, width);
#endif
}

void CorePlatformApple::FreeTextTexture(void* tex) {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  base::AppleUtils::FreeTextTexture(tex);
#else
  CorePlatform::FreeTextTexture(tex);
#endif
}

auto CorePlatformApple::CreateTextTexture(
    int width, int height, const std::vector<std::string>& strings,
    const std::vector<float>& positions, const std::vector<float>& widths,
    float scale) -> void* {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  return base::AppleUtils::CreateTextTexture(width, height, strings, positions,
                                             widths, scale);
#else
  return CorePlatform::CreateTextTexture(width, height, strings, positions,
                                         widths, scale);
#endif
}

auto CorePlatformApple::GetTextTextureData(void* tex) -> uint8_t* {
#if BA_XCODE_BUILD && !BA_HEADLESS_BUILD
  return base::AppleUtils::GetTextTextureData(tex);
#else
  return CorePlatform::GetTextTextureData(tex);
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

auto CorePlatformApple::NewAutoReleasePool() -> void* {
#if BA_XCODE_BUILD
  return base::AppleUtils::NewAutoReleasePool();
#else
  return CorePlatform::NewAutoReleasePool();
#endif
}

void CorePlatformApple::DrainAutoReleasePool(void* pool) {
#if BA_XCODE_BUILD
  base::AppleUtils::DrainAutoReleasePool(pool);
#else
  CorePlatform::DrainAutoReleasePool(pool);
#endif
}

void CorePlatformApple::GameCenterLogin() {
#if BA_USE_GAME_CENTER
  base::AppleUtils::DoGameCenterLogin();
#else
  CorePlatform::GameCenterLogin();
#endif
}

auto CorePlatformApple::IsOSPlayingMusic() -> bool {
#if BA_XCODE_BUILD
  return base::AppleUtils::IsMusicPlaying();
#else
  return CorePlatform::IsOSPlayingMusic();
#endif
}

void CorePlatformApple::OpenFileExternally(const std::string& path) {
#if BA_XCODE_BUILD
  base::AppleUtils::EditTextFile(path.c_str());
#else
  CorePlatform::OpenFileExternally(path);
#endif
}

void CorePlatformApple::OpenDirExternally(const std::string& path) {
#if BA_OSTYPE_MACOS
  std::string cmd = std::string("open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    Log(LogLevel::kError, "Got return value " + std::to_string(result)
                              + " on open cmd '" + cmd + "'");
  }
#else
  CorePlatform::OpenDirExternally(path);
#endif
}

void CorePlatformApple::MacMusicAppInit() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  base::AppleUtils::MacMusicAppInit();
#else
  CorePlatform::MacMusicAppInit();
#endif
}
auto CorePlatformApple::MacMusicAppGetVolume() -> int {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return static_cast<int>(base::AppleUtils::MacMusicAppGetVolume());
#else
  return CorePlatform::MacMusicAppGetVolume();
#endif
}
void CorePlatformApple::MacMusicAppSetVolume(int volume) {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  base::AppleUtils::MacMusicAppSetVolume(volume);
#else
  CorePlatform::MacMusicAppSetVolume(volume);
#endif
}
void CorePlatformApple::MacMusicAppGetLibrarySource() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  base::AppleUtils::MacMusicAppGetLibrarySource();
#else
  CorePlatform::MacMusicAppGetLibrarySource();
#endif
}
void CorePlatformApple::MacMusicAppStop() {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  base::AppleUtils::MacMusicAppStop();
#else
  CorePlatform::MacMusicAppStop();
#endif
}
auto CorePlatformApple::MacMusicAppPlayPlaylist(const std::string& playlist)
    -> bool {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return base::AppleUtils::MacMusicAppPlayPlaylist(playlist.c_str());
#else
  return CorePlatform::MacMusicAppPlayPlaylist(playlist);
#endif
}
auto CorePlatformApple::MacMusicAppGetPlaylists() -> std::list<std::string> {
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  return base::AppleUtils::MacMusicAppGetPlaylists();
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

auto CorePlatformApple::DoClipboardIsSupported() -> bool {
#if BA_XCODE_BUILD
  return base::AppleUtils::ClipboardIsSupported();
#else
  return CorePlatform::DoClipboardIsSupported();
#endif  // BA_XCODE_BUILD
}

auto CorePlatformApple::DoClipboardHasText() -> bool {
#if BA_XCODE_BUILD
  return base::AppleUtils::ClipboardHasText();
#else
  return CorePlatform::DoClipboardHasText();
#endif  // BA_XCODE_BUILD
}

void CorePlatformApple::DoClipboardSetText(const std::string& text) {
#if BA_XCODE_BUILD
  base::AppleUtils::ClipboardSetText(text);
#else
  CorePlatform::DoClipboardSetText(text);
#endif  // BA_XCODE_BUILD
}

auto CorePlatformApple::DoClipboardGetText() -> std::string {
#if BA_XCODE_BUILD
  return base::AppleUtils::ClipboardGetText();
#else
  return CorePlatform::DoClipboardGetText();
#endif  // BA_XCODE_BUILD
}

}  // namespace ballistica::core

#endif  // BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
