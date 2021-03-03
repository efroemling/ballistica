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
  auto GetDeviceUUIDPrefix() -> std::string override;
  auto GetRealDeviceUUID(std::string* uuid) -> bool override;
  auto GenerateUUID() -> std::string override;
  auto GetDefaultConfigDir() -> std::string override;
  auto GetLocale() -> std::string override;
  auto DoGetDeviceName() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  auto GetUIScale() -> UIScale override;
  auto IsRunningOnDesktop() -> bool override;
  void HandleLog(const std::string& msg) override;
  void SetupDataDirectory() override;
  void GetTextBoundsAndWidth(const std::string& text, Rect* r,
                             float* width) override;
  void FreeTextTexture(void* tex) override;
  auto CreateTextTexture(int width, int height,
                         const std::vector<std::string>& strings,
                         const std::vector<float>& positions,
                         const std::vector<float>& widths, float scale)
      -> void* override;
  auto GetTextTextureData(void* tex) -> uint8_t* override;
  void GetFriendScores(const std::string& game, const std::string& game_version,
                       void* py_callback) override;
  void SubmitScore(const std::string& game, const std::string& version,
                   int64_t score) override;
  void ReportAchievement(const std::string& achievement) override;
  auto HaveLeaderboard(const std::string& game, const std::string& config)
      -> bool override;
  void ShowOnlineScoreUI(const std::string& show, const std::string& game,
                         const std::string& game_version) override;
  void Purchase(const std::string& item) override;
  void RestorePurchases() override;
  auto NewAutoReleasePool() -> void* override;
  void DrainAutoReleasePool(void* pool) override;
  void DoOpenURL(const std::string& url) override;
  void ResetAchievements() override;
  void GameCenterLogin() override;
  void PurchaseAck(const std::string& purchase,
                   const std::string& order_id) override;
  auto IsOSPlayingMusic() -> bool override;
  void SetHardwareCursorVisible(bool visible) override;
  void QuitApp() override;
  void GetScoresToBeat(const std::string& level, const std::string& config,
                       void* py_callback) override;
  void OpenFileExternally(const std::string& path) override;
  void OpenDirExternally(const std::string& path) override;
  void MacMusicAppInit() override;
  auto MacMusicAppGetVolume() -> int override;
  void MacMusicAppSetVolume(int volume) override;
  void MacMusicAppGetLibrarySource() override;
  void MacMusicAppStop() override;
  auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool override;
  auto MacMusicAppGetPlaylists() -> std::list<std::string> override;
  void StartListeningForWiiRemotes() override;
  void StopListeningForWiiRemotes() override;
  auto IsEventPushMode() -> bool override;
  auto ContainsPythonDist() -> bool override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;

 private:
  // std::mutex log_mutex_;
  // std::string log_line_;
};

}  // namespace ballistica

#endif  // BA_XCODE_BUILD || BA_OSTYPE_MACOS
#endif  // BALLISTICA_PLATFORM_APPLE_PLATFORM_APPLE_H_
