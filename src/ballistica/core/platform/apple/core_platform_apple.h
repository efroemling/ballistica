// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_APPLE_CORE_PLATFORM_APPLE_H_
#define BALLISTICA_CORE_PLATFORM_APPLE_CORE_PLATFORM_APPLE_H_
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS

#include <list>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/core/platform/core_platform.h"

namespace ballistica::core {

class CorePlatformApple : public CorePlatform {
 public:
  CorePlatformApple();
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override;
  auto GetRealLegacyDeviceUUID(std::string* uuid) -> bool override;
  auto GenerateUUID() -> std::string override;
  auto DoGetConfigDirectoryMonolithicDefault()
      -> std::optional<std::string> override;
  auto GetLocale() -> std::string override;
  auto DoGetDeviceName() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  auto GetUIScale() -> UIScale override;
  auto IsRunningOnDesktop() -> bool override;
  void DisplayLog(const std::string& name, LogLevel level,
                  const std::string& msg) override;
  void GetTextBoundsAndWidth(const std::string& text, Rect* r,
                             float* width) override;
  void FreeTextTexture(void* tex) override;
  auto CreateTextTexture(int width, int height,
                         const std::vector<std::string>& strings,
                         const std::vector<float>& positions,
                         const std::vector<float>& widths, float scale)
      -> void* override;
  auto GetTextTextureData(void* tex) -> uint8_t* override;
  void SubmitScore(const std::string& game, const std::string& version,
                   int64_t score) override;
  void ReportAchievement(const std::string& achievement) override;
  auto HaveLeaderboard(const std::string& game, const std::string& config)
      -> bool override;
  void ShowOnlineScoreUI(const std::string& show, const std::string& game,
                         const std::string& game_version) override;
  auto NewAutoReleasePool() -> void* override;
  void DrainAutoReleasePool(void* pool) override;
  void ResetAchievements() override;
  void GameCenterLogin() override;
  auto IsOSPlayingMusic() -> bool override;
  void SetHardwareCursorVisible(bool visible) override;
  void OpenFileExternally(const std::string& path) override;
  void OpenDirExternally(const std::string& path) override;
  void MacMusicAppInit() override;
  auto MacMusicAppGetVolume() -> int override;
  void MacMusicAppSetVolume(int volume) override;
  void MacMusicAppGetLibrarySource() override;
  void MacMusicAppStop() override;
  auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool override;
  auto MacMusicAppGetPlaylists() -> std::list<std::string> override;
  auto IsEventPushMode() -> bool override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;

  auto DoClipboardIsSupported() -> bool override;
  auto DoClipboardHasText() -> bool override;
  void DoClipboardSetText(const std::string& text) override;
  auto DoClipboardGetText() -> std::string override;
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;

 protected:
  auto DoGetDataDirectoryMonolithicDefault() -> std::string override;

 private:
};

}  // namespace ballistica::core

#endif  // BA_XCODE_BUILD || BA_OSTYPE_MACOS
#endif  // BALLISTICA_CORE_PLATFORM_APPLE_CORE_PLATFORM_APPLE_H_
