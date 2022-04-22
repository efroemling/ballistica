// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PLATFORM_APPLE_PLATFORM_APPLE_H_
#define BALLISTICA_PLATFORM_APPLE_PLATFORM_APPLE_H_
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS

#include <list>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/platform/platform.h"

namespace ballistica {

class PlatformApple : public Platform {
 public:
  PlatformApple();
  auto GetDeviceAccountUUIDPrefix() -> std::string override;
  auto GetRealLegacyDeviceUUID(std::string* uuid) -> bool override;
  auto GenerateUUID() -> std::string override;
  auto GetDefaultConfigDir() -> std::string override;
  auto GetLocale() -> std::string override;
  auto DoGetDeviceName() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  auto GetUIScale() -> UIScale override;
  auto IsRunningOnDesktop() -> bool override;
  auto HandleLog(const std::string& msg) -> void override;
  auto SetupDataDirectory() -> void override;
  auto GetTextBoundsAndWidth(const std::string& text, Rect* r, float* width)
      -> void override;
  auto FreeTextTexture(void* tex) -> void override;
  auto CreateTextTexture(int width, int height,
                         const std::vector<std::string>& strings,
                         const std::vector<float>& positions,
                         const std::vector<float>& widths, float scale)
      -> void* override;
  auto GetTextTextureData(void* tex) -> uint8_t* override;
  auto GetFriendScores(const std::string& game, const std::string& game_version,
                       void* py_callback) -> void override;
  auto SubmitScore(const std::string& game, const std::string& version,
                   int64_t score) -> void override;
  auto ReportAchievement(const std::string& achievement) -> void override;
  auto HaveLeaderboard(const std::string& game, const std::string& config)
      -> bool override;
  auto ShowOnlineScoreUI(const std::string& show, const std::string& game,
                         const std::string& game_version) -> void override;
  auto Purchase(const std::string& item) -> void override;
  auto RestorePurchases() -> void override;
  auto NewAutoReleasePool() -> void* override;
  auto DrainAutoReleasePool(void* pool) -> void override;
  auto DoOpenURL(const std::string& url) -> void override;
  auto ResetAchievements() -> void override;
  auto GameCenterLogin() -> void override;
  auto PurchaseAck(const std::string& purchase, const std::string& order_id)
      -> void override;
  auto IsOSPlayingMusic() -> bool override;
  auto SetHardwareCursorVisible(bool visible) -> void override;
  auto QuitApp() -> void override;
  auto GetScoresToBeat(const std::string& level, const std::string& config,
                       void* py_callback) -> void override;
  auto OpenFileExternally(const std::string& path) -> void override;
  auto OpenDirExternally(const std::string& path) -> void override;
  auto MacMusicAppInit() -> void override;
  auto MacMusicAppGetVolume() -> int override;
  auto MacMusicAppSetVolume(int volume) -> void override;
  auto MacMusicAppGetLibrarySource() -> void override;
  auto MacMusicAppStop() -> void override;
  auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool override;
  auto MacMusicAppGetPlaylists() -> std::list<std::string> override;
  auto IsEventPushMode() -> bool override;
  auto ContainsPythonDist() -> bool override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;

  auto DoClipboardIsSupported() -> bool override;
  auto DoClipboardHasText() -> bool override;
  auto DoClipboardSetText(const std::string& text) -> void override;
  auto DoClipboardGetText() -> std::string override;
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;

 private:
};

}  // namespace ballistica

#endif  // BA_XCODE_BUILD || BA_OSTYPE_MACOS
#endif  // BALLISTICA_PLATFORM_APPLE_PLATFORM_APPLE_H_
