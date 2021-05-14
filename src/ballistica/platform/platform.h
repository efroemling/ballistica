// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PLATFORM_PLATFORM_H_
#define BALLISTICA_PLATFORM_PLATFORM_H_

#include <sys/stat.h>

#include <list>
#include <string>
#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

/// For capturing and printing stack-traces and related errors.
/// Platforms should subclass this and return instances in GetStackTrace().
class PlatformStackTrace {
 public:
  // The stack trace should capture the stack state immediately upon
  // construction but should do the bare minimum amount of work to store it. Any
  // expensive operations such as symbolification should be deferred until
  // GetDescription().
  virtual ~PlatformStackTrace() = default;

  // Return a human readable version of the trace (with symbolification if
  // available).
  virtual auto GetDescription() noexcept -> std::string = 0;

  // Should return a copy of itself allocated via new() (or nullptr if not
  // possible).
  virtual auto copy() const noexcept -> PlatformStackTrace* = 0;
};

// This class attempts to abstract away most platform-specific functionality.
// Ideally we should need to pull in no platform-specific system headers outside
// of the platform*.cc files and can just go through this.
class Platform {
 public:
  static auto Create() -> Platform*;
  Platform();
  virtual ~Platform();

#pragma mark LIFECYCLE/SETTINGS ------------------------------------------------

  /// Called right after g_platform is created/assigned. Any platform
  /// functionality depending on a complete g_platform object existing can
  /// be run here.
  virtual auto PostInit() -> void;

  /// Create the proper App module and add it to the main_thread.
  void CreateApp();

  /// Create the appropriate Graphics subclass for the app.
  Graphics* CreateGraphics();

  virtual void CreateAuxiliaryModules();
  virtual void WillExitMain(bool errored);

  // Inform the platform that all subsystems are up and running and it can
  // start talking to them.
  virtual void OnBootstrapComplete();

  // Get/set values before standard game settings are available
  // (for values needed before SDL init/etc).
  // FIXME: We should have some sort of 'bootconfig.json' file for these.
  // (or simply read the regular config in via c++ immediately)
  auto GetLowLevelConfigValue(const char* key, int default_value) -> int;
  void SetLowLevelConfigValue(const char* key, int value);

  // Called when the app config is being read/applied.
  virtual void ApplyConfig();

  // Called when the app should set itself up to intercept ctrl-c presses.
  virtual void SetupInterruptHandling();

  void FinalCleanup();

#pragma mark FILES -------------------------------------------------------------

  // remove() support UTF8 strings.
  virtual auto Remove(const char* path) -> int;

  // stat() supporting UTF8 strings.
  virtual auto Stat(const char* path, struct BA_STAT* buffer) -> int;

  // fopen() supporting UTF8 strings.
  virtual auto FOpen(const char* path, const char* mode) -> FILE*;

  // rename() supporting UTF8 strings.
  // For cross-platform consistency, this should also remove any file that
  // exists at the target location first.
  virtual auto Rename(const char* oldname, const char* newname) -> int;

  // Simple cross-platform check for existence of a file.
  auto FilePathExists(const std::string& name) -> bool;

  /// Attempt to make a directory; raise an Exception if unable,
  /// unless quiet is true.
  void MakeDir(const std::string& dir, bool quiet = false);

  // Return the current working directory.
  virtual auto GetCWD() -> std::string;

  // Unlink a file.
  virtual auto Unlink(const char* path) -> void;

  /// Return the absolute path for the provided path. Note that this requires
  /// the path to already exist.
  auto AbsPath(const std::string& path, std::string* outpath) -> bool;

#pragma mark CLIPBOARD ---------------------------------------------------------

  /// Return whether clipboard operations are supported at all.
  /// This gets called when determining whether to display clipboard related
  /// UI elements/etc.
  auto ClipboardIsSupported() -> bool;

  /// Return whether there is currently text on the clipboard.
  auto ClipboardHasText() -> bool;

  /// Set current clipboard text. Raises an Exception if clipboard is
  /// unsupported.
  auto ClipboardSetText(const std::string& text) -> void;

  /// Return current text from the clipboard. Raises an Exception if
  /// clipboard is unsupported or if there's no text on the clipboard.
  auto ClipboardGetText() -> std::string;

#pragma mark PRINTING/LOGGING --------------------------------------------------

  // Send a message to the default platform handler.
  // IMPORTANT: No Object::Refs should be created or destroyed within this call,
  // or deadlock can occur.
  virtual void HandleLog(const std::string& msg);

#pragma mark ENVIRONMENT -------------------------------------------------------

  // Return a simple name for the platform: 'mac', 'windows', 'linux', etc.
  virtual auto GetPlatformName() -> std::string;

  // Return a simple name for the subplatform: 'amazon', 'google', etc.
  virtual auto GetSubplatformName() -> std::string;

  // Are we running in event-push-mode?
  // With this on, we return from Main() and the system handles the event loop.
  // With it off, we loop in Main() ourself.
  virtual auto IsEventPushMode() -> bool;

  // Return the interface type based on the environment (phone, tablet, etc).
  virtual auto GetUIScale() -> UIScale;

  // Return a string *reasonably* likely to be unique and consistent for this
  // device. Do not assume this is globally unique and *do not* assume that it
  // will never ever change (hardware upgrades may affect it, etc).
  virtual auto GetUniqueDeviceIdentifier() -> const std::string&;

  // Returns the ID to use for the device account
  auto GetDeviceAccountID() -> std::string;
  auto GetConfigDirectory() -> std::string;
  auto GetConfigFilePath() -> std::string;
  auto GetUserPythonDirectory() -> std::string;
  auto GetAppPythonDirectory() -> std::string;
  auto GetSitePythonDirectory() -> std::string;
  auto GetReplaysDir() -> std::string;

  // Return en_US or whatnot.
  virtual auto GetLocale() -> std::string;
  virtual void SetupDataDirectory();
  virtual auto GetUserAgentString() -> std::string;
  virtual auto GetOSVersionString() -> std::string;

  /// Set an environment variable as utf8, overwriting if it already exists.
  /// Raises an exception on errors.
  virtual void SetEnv(const std::string& name, const std::string& value);

  // Are we being run from a terminal? (should we show prompts, etc?).
  virtual auto IsStdinATerminal() -> bool;

  // Return hostname or other id suitable for network searches, etc.
  auto GetDeviceName() -> std::string;

  // Are we running on a tv?
  virtual auto IsRunningOnTV() -> bool;

  // Are we on a daydream enabled android device?
  virtual auto IsRunningOnDaydream() -> bool;

  // Do we have touchscreen hardware?
  auto HasTouchScreen() -> bool;

  // Are we running on a desktop setup in general?
  virtual auto IsRunningOnDesktop() -> bool;

  // Are we running on fireTV hardware?
  virtual auto IsRunningOnFireTV() -> bool;

  // Return the external storage path (currently only relevant on android).
  virtual auto GetExternalStoragePath() -> std::string;

  // For enabling some special hardware optimizations for nvidia.
  auto is_tegra_k1() const -> bool { return is_tegra_k1_; }
  void set_is_tegra_k1(bool val) { is_tegra_k1_ = val; }

  // Return true if this platform includes its own python distribution
  // (defaults to false).
  virtual auto ContainsPythonDist() -> bool;

#pragma mark INPUT DEVICES -----------------------------------------------------

  // Return a name for a ballistica keycode.
  virtual auto GetKeyName(int keycode) -> std::string;

#pragma mark IN APP PURCHASES --------------------------------------------------

  virtual void Purchase(const std::string& item);

  // Restore purchases (currently only relevant on apple platforms).
  virtual void RestorePurchases();

  // purchase ack'ed by the master-server (so can consume)
  virtual void PurchaseAck(const std::string& purchase,
                           const std::string& order_id);

#pragma mark ANDROID -----------------------------------------------------------

  virtual auto GetAndroidExecArg() -> std::string;
  virtual void AndroidSetResString(const std::string& res);
  virtual auto AndroidIsGPGSConnectionToClient(ConnectionToClient* c) -> bool;
  virtual auto AndroidGPGSNewConnectionToClient(int id) -> ConnectionToClient*;
  virtual auto AndroidGPGSNewConnectionToHost() -> ConnectionToHost*;
  virtual void AndroidSynthesizeBackPress();
  virtual void AndroidQuitActivity();
  virtual void AndroidShowAppInvite(const std::string& title,
                                    const std::string& message,
                                    const std::string& code);
  virtual void AndroidRefreshFile(const std::string& file);
  virtual void AndroidGPGSPartyInvitePlayers();
  virtual void AndroidGPGSPartyShowInvites();
  virtual void AndroidGPGSPartyInviteAccept(const std::string& invite_id);
  virtual void AndroidShowWifiSettings();

#pragma mark PERMISSIONS -------------------------------------------------------

  /// Request the permission asynchronously.
  /// If the permission cannot be requested (due to having been denied, etc)
  /// then this may also present a message or pop-up instructing the user how
  /// to manually grant the permission (up to individual platforms to
  /// implement).
  virtual void RequestPermission(Permission p);

  /// Returns true if this permission has been granted (or if asking is not
  /// required for it).
  virtual auto HavePermission(Permission p) -> bool;

#pragma mark ANALYTICS ---------------------------------------------------------

  virtual void SetAnalyticsScreen(const std::string& screen);
  virtual void IncrementAnalyticsCount(const std::string& name, int increment);
  virtual void IncrementAnalyticsCountRaw(const std::string& name,
                                          int increment);
  virtual void IncrementAnalyticsCountRaw2(const std::string& name,
                                           int uses_increment, int increment);
  virtual void SubmitAnalyticsCounts();

#pragma mark APPLE -------------------------------------------------------------

  virtual auto NewAutoReleasePool() -> void*;
  virtual void DrainAutoReleasePool(void* pool);
  // FIXME: Can we consolidate these with the general music playback calls?
  virtual void MacMusicAppInit();
  virtual auto MacMusicAppGetVolume() -> int;
  virtual void MacMusicAppSetVolume(int volume);
  virtual void MacMusicAppGetLibrarySource();
  virtual void MacMusicAppStop();
  virtual auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool;
  virtual auto MacMusicAppGetPlaylists() -> std::list<std::string>;

#pragma mark TEXT RENDERING ----------------------------------------------------

  // Set bounds/width info for a bit of text.
  // (will only be called in BA_ENABLE_OS_FONT_RENDERING is set)
  virtual void GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                     float* width);
  virtual void FreeTextTexture(void* tex);
  virtual auto CreateTextTexture(int width, int height,
                                 const std::vector<std::string>& strings,
                                 const std::vector<float>& positions,
                                 const std::vector<float>& widths, float scale)
      -> void*;
  virtual auto GetTextTextureData(void* tex) -> uint8_t*;

#pragma mark ACCOUNTS ----------------------------------------------------------

  virtual auto SignIn(const std::string& account_type) -> void;
  virtual auto SignOut() -> void;
  virtual auto GameCenterLogin() -> void;
  virtual auto AccountDidChange() -> void;

#pragma mark MUSIC PLAYBACK ----------------------------------------------------

  // FIXME: currently these are wired up on android; need to generalize
  //  to support mac/itunes or other music player types.
  virtual void MusicPlayerPlay(PyObject* target);
  virtual void MusicPlayerStop();
  virtual void MusicPlayerShutdown();
  virtual void MusicPlayerSetVolume(float volume);

#pragma mark ADS ---------------------------------------------------------------

  virtual void ShowAd(const std::string& purpose);

  // Return whether we have the ability to show *any* ads.
  virtual auto GetHasAds() -> bool;

  // Return whether we have the ability to show longer-form video ads (suitable
  // for rewards).
  virtual auto GetHasVideoAds() -> bool;

#pragma mark GAME SERVICES -----------------------------------------------------

  // Given a raw leaderboard score, convert it to what the game uses.
  // For instance, platforms may return times as milliseconds while we require
  // hundredths of a second, etc.
  virtual auto ConvertIncomingLeaderboardScore(
      const std::string& leaderboard_id, int score) -> int;

  virtual void GetFriendScores(const std::string& game,
                               const std::string& game_version,
                               void* py_callback);
  virtual void SubmitScore(const std::string& game, const std::string& version,
                           int64_t score);
  virtual void ReportAchievement(const std::string& achievement);
  virtual auto HaveLeaderboard(const std::string& game,
                               const std::string& config) -> bool;

  virtual void ShowOnlineScoreUI(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version);
  virtual void ResetAchievements();

#pragma mark NETWORKING --------------------------------------------------------

  virtual void CloseSocket(int socket);
  virtual auto SocketPair(int domain, int type, int protocol, int socks[2])
      -> int;
  virtual auto GetBroadcastAddrs() -> std::vector<uint32_t>;
  virtual auto SetSocketNonBlocking(int sd) -> bool;

#pragma mark ERRORS & DEBUGGING ------------------------------------------------

  // Should return a subclass of PlatformStackTrace allocated via new.
  // Platforms with no meaningful stack trace functionality can return nullptr.
  virtual auto GetStackTrace() -> PlatformStackTrace*;

  // Called during stress testing.
  virtual auto GetMemUsageInfo() -> std::string;

  // Optionally override fatal error reporting. If true is returned, default
  // fatal error reporting will not run.
  virtual auto ReportFatalError(const std::string& message,
                                bool in_top_level_exception_handler) -> bool;

  // Optionally override fatal error handling. If true is returned, default
  // fatal error handling will not run.
  virtual auto HandleFatalError(bool exit_cleanly,
                                bool in_top_level_exception_handler) -> bool;

  // If this platform has the ability to show a blocking dialog on the main
  // thread for fatal errors, return true here.
  virtual auto CanShowBlockingFatalErrorDialog() -> bool;

  // Called on the main thread when a fatal error occurs.
  // Will only be called if CanShowBlockingFatalErrorDialog() is true.
  virtual auto BlockingFatalErrorDialog(const std::string& message) -> void;

  // Use this instead of looking at errno (translates winsock errors to errno).
  virtual auto GetSocketError() -> int;

  // Return a string for the current value of errno.
  virtual auto GetErrnoString() -> std::string;

  // Return a description of errno (unix) or WSAGetLastError() (windows).
  virtual auto GetSocketErrorString() -> std::string;

  /// Set a key to be included in crash logs or other debug cases.
  /// This is expected to be lightweight as it may be called often.
  virtual auto SetDebugKey(const std::string& key, const std::string& value)
      -> void;

  /// Print a log message to be included in crash logs or other debug
  /// mechanisms. Standard log messages (at least with to_server=true) get
  /// send here as well. It can be useful to call this directly to report
  /// extra details that may help in debugging, as these calls are not
  /// considered 'noteworthy' or presented to the user as standard Log()
  /// calls are.
  virtual auto HandleDebugLog(const std::string& msg) -> void;

  static auto DebugLog(const std::string& msg) -> void {
    if (g_platform) {
      g_platform->HandleDebugLog(msg);
    }
  }

  /// Shortcut to set last native Python call we made.
  static auto SetLastPyCall(const std::string& name) {
    if (g_platform) {
      g_platform->py_call_num_++;
      g_platform->SetDebugKey(
          "LastPyCall" + std::to_string(g_platform->py_call_num_ % 10),
          std::to_string(g_platform->py_call_num_) + ":" + name + "@"
              + std::to_string(GetCurrentMilliseconds()));
    }
  }

#pragma mark MISC --------------------------------------------------------------

  // Return a monotonic time measurement in milliseconds since launch.
  // To get a time value that is guaranteed to not jump around or go backwards,
  // use ballistica::GetRealTime() (which is an abstraction around this).
  auto GetTicks() -> millisecs_t;

  // A raw milliseconds value (not relative to launch time).
  static auto GetCurrentMilliseconds() -> millisecs_t;
  static auto GetCurrentSeconds() -> int64_t;

  static void SleepMS(millisecs_t ms);

  // Pop up a text edit dialog.
  virtual void EditText(const std::string& title, const std::string& value,
                        int max_chars);

  // Open the provided URL in a browser or whatnot.
  void OpenURL(const std::string& url);
  virtual auto DemangleCXXSymbol(const std::string& s) -> std::string;

  // Called each time through the main event loop; for custom pumping/handling.
  virtual void RunEvents();

  // Called when the app module is pausing.
  // Note: only app-thread (main thread) stuff should happen here.
  // (don't push calls to other threads/etc).
  virtual void OnAppPause();

  // Called when the app module is resuming.
  virtual void OnAppResume();

  // Is the OS currently playing music? (so we can avoid doing so).
  virtual auto IsOSPlayingMusic() -> bool;

  // Pass platform-specific misc-read-vals along to the OS (as a json string).
  virtual void SetPlatformMiscReadVals(const std::string& vals);

  // Show/hide the hardware cursor.
  virtual void SetHardwareCursorVisible(bool visible);

  // Get the most up-to-date cursor position.
  virtual void GetCursorPosition(float* x, float* y);

  // Quit the app (can be immediate or via posting some high level event).
  virtual void QuitApp();

  // Do we want to deprecate this?...
  virtual void GetScoresToBeat(const std::string& level,
                               const std::string& config, void* py_callback);

  // Open a file using the system default method (in another app, etc.)
  virtual void OpenFileExternally(const std::string& path);

  // Open a directory using the system default method (Finder, etc.)
  virtual void OpenDirExternally(const std::string& path);

  // Currently mac-only (could be generalized though).
  virtual void StartListeningForWiiRemotes();

  // Currently mac-only (could be generalized though).
  virtual void StopListeningForWiiRemotes();

  // Set the name of the current thread (for debugging).
  virtual void SetCurrentThreadName(const std::string& name);

  // If display-resolution can be directly set on this platform,
  // return true and set the native full res here.  Otherwise return false;
  virtual auto GetDisplayResolution(int* x, int* y) -> bool;

  auto using_custom_app_python_dir() const {
    return using_custom_app_python_dir_;
  }

 protected:
  // Open the provided URL in a browser or whatnot.
  virtual void DoOpenURL(const std::string& url);

  // Called once per platform to determine touchscreen presence.
  virtual auto DoHasTouchScreen() -> bool;
  virtual auto DoGetDeviceName() -> std::string;

  // Attempt to actually create a directory.
  // Should not except if it already exists or if quiet is true.
  virtual void DoMakeDir(const std::string& dir, bool quiet);

  // Attempt to actually get an abs path. This will only be called if
  // the path is valid and exists.
  virtual auto DoAbsPath(const std::string& path, std::string* outpath) -> bool;

  // Calc the user scripts dir path for this platform.
  // This will be called once and the path cached.
  virtual auto DoGetUserPythonDirectory() -> std::string;

  // Return the default config directory for this platform.
  virtual auto GetDefaultConfigDir() -> std::string;

  // Return the prefix to use for device UUIDs on this platform.
  virtual auto GetDeviceUUIDPrefix() -> std::string;

  // Return whether there is an actual unique UUID available for this platform,
  // and also return it if so.
  virtual auto GetRealDeviceUUID(std::string* uuid) -> bool;

  // Generate a random UUID string.
  virtual auto GenerateUUID() -> std::string;

  virtual auto DoClipboardIsSupported() -> bool;
  virtual auto DoClipboardHasText() -> bool;
  virtual auto DoClipboardSetText(const std::string& text) -> void;
  virtual auto DoClipboardGetText() -> std::string;

 private:
  int py_call_num_{};
  bool using_custom_app_python_dir_{};
  bool have_config_dir_{};
  bool have_has_touchscreen_value_{};
  bool have_touchscreen_{};
  bool is_tegra_k1_{};
  bool have_clipboard_is_supported_{};
  bool clipboard_is_supported_{};
  millisecs_t starttime_{};
  std::string device_uuid_;
  bool have_device_uuid_{};
  std::string config_dir_;
  std::string user_scripts_dir_;
  std::string app_python_dir_;
  std::string site_python_dir_;
  std::string replays_dir_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PLATFORM_PLATFORM_H_
