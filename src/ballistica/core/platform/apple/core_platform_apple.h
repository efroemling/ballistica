// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_APPLE_CORE_PLATFORM_APPLE_H_
#define BALLISTICA_CORE_PLATFORM_APPLE_CORE_PLATFORM_APPLE_H_
#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS

#include <list>
#include <optional>
#include <string>
#include <vector>

#include "ballistica/core/platform/core_platform.h"

namespace ballistica::core {

class CorePlatformApple : public CorePlatform {
 public:
  CorePlatformApple();
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override;
  auto GetRealLegacyDeviceUUID(std::string* uuid) -> bool override;
  auto DoGetConfigDirectoryMonolithicDefault()
      -> std::optional<std::string> override;
  auto DoGetCacheDirectoryMonolithicDefault()
      -> std::optional<std::string> override;
  auto DoHasTouchScreen() -> bool override;
  auto GetDefaultUIScale() -> UIScale override;
  auto IsRunningOnDesktop() -> bool override;
  void EmitPlatformLog(const std::string& name, LogLevel level,
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
  void ShowGameServiceUI(const std::string& show, const std::string& game,
                         const std::string& game_version) override;
  void ResetAchievements() override;
  auto IsOSPlayingMusic() -> bool override;
  void MacMusicAppInit() override;
  auto MacMusicAppGetVolume() -> int override;
  void MacMusicAppSetVolume(int volume) override;
  void MacMusicAppStop() override;
  auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool override;
  auto MacMusicAppGetPlaylists() -> std::list<std::string> override;
  auto GetLegacyPlatformName() -> std::string override;
  auto GetLegacySubplatformName() -> std::string override;

  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
  auto GetBaLocale() -> std::string override;
  auto GetLocaleTag() -> std::string override;
  auto DoGetDeviceName() -> std::string override;
  auto DoGetDeviceDescription() -> std::string override;
  auto GetOSVersionString() -> std::string override;
  auto CanShowBlockingFatalErrorDialog() -> bool override;
  void BlockingFatalErrorDialog(const std::string& message) override;

 protected:
  auto DoGetDataDirectoryMonolithicDefault() -> std::string override;

 private:
  std::optional<std::string> ba_locale_;
  std::optional<std::string> locale_tag_;
};

}  // namespace ballistica::core

#endif  // BA_XCODE_BUILD || BA_PLATFORM_MACOS
#endif  // BALLISTICA_CORE_PLATFORM_APPLE_CORE_PLATFORM_APPLE_H_
