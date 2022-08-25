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
/// Stack trace classes should capture the stack state immediately upon
/// construction but should do the bare minimum amount of work to store it.
/// Any expensive operations such as symbolification should be deferred until
/// GetDescription().
class PlatformStackTrace {
 public:
  virtual ~PlatformStackTrace() = default;

  // Return a human readable version of the trace (with symbolification if
  // available).
  virtual auto GetDescription() noexcept -> std::string = 0;

  // Should return a copy of itself allocated via new() (or nullptr if not
  // possible).
  virtual auto copy() const noexcept -> PlatformStackTrace* = 0;
};

/// This class attempts to abstract away most platform-specific functionality.
/// Ideally we should need to pull in no platform-specific system headers
/// outside of the platform*.cc files and can just go through this.
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
  auto CreateApp() -> void;

  /// Create the appropriate Graphics subclass for the app.
  auto CreateGraphics() -> Graphics*;

  virtual auto CreateAuxiliaryModules() -> void;
  virtual auto WillExitMain(bool errored) -> void;

  /// Inform the platform that all subsystems are up and running and it can
  /// start talking to them.
  virtual auto OnBootstrapComplete() -> void;

  // Get/set values before standard game settings are available
  // (for values needed before SDL init/etc).
  // FIXME: We should have some sort of 'bootconfig.json' file for these.
  //  (or simply read the regular config in via c++ immediately)
  auto GetLowLevelConfigValue(const char* key, int default_value) -> int;
  auto SetLowLevelConfigValue(const char* key, int value) -> void;

  /// Called when the app config is being read/applied.
  virtual auto ApplyConfig() -> void;

  /// Called when the app should set itself up to intercept ctrl-c presses.
  virtual auto SetupInterruptHandling() -> void;

#pragma mark FILES -------------------------------------------------------------

  /// remove() supporting UTF8 strings.
  virtual auto Remove(const char* path) -> int;

  /// stat() supporting UTF8 strings.
  virtual auto Stat(const char* path, struct BA_STAT* buffer) -> int;

  /// fopen() supporting UTF8 strings.
  virtual auto FOpen(const char* path, const char* mode) -> FILE*;

  /// rename() supporting UTF8 strings.
  /// For cross-platform consistency, this should also remove any file that
  /// exists at the target location first.
  virtual auto Rename(const char* oldname, const char* newname) -> int;

  /// Simple cross-platform check for existence of a file.
  auto FilePathExists(const std::string& name) -> bool;

  /// Attempt to make a directory. Raise an Exception if unable,
  /// unless quiet is true. Succeeds if the directory already exists.
  auto MakeDir(const std::string& dir, bool quiet = false) -> void;

  /// Return the current working directory.
  virtual auto GetCWD() -> std::string;

  /// Unlink a file.
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
  virtual auto HandleLog(const std::string& msg) -> void;

#pragma mark ENVIRONMENT -------------------------------------------------------

  // Return a simple name for the platform: 'mac', 'windows', 'linux', etc.
  virtual auto GetPlatformName() -> std::string;

  // Return a simple name for the subplatform: 'amazon', 'google', etc.
  virtual auto GetSubplatformName() -> std::string;

  // Are we running in event-push-mode?
  // With this on, we return from Main() and the system handles the event loop.
  // With it off, we loop in Main() ourself.
  virtual auto IsEventPushMode() -> bool;

  /// Return the interface type based on the environment (phone, tablet, etc).
  virtual auto GetUIScale() -> UIScale;

  /// Get the root config directory. This dir contains the app config file
  /// and other data considered essential to the app install. This directory
  /// should be included in OS backups.
  auto GetConfigDirectory() -> std::string;

  /// Get the path of the app config file.
  auto GetConfigFilePath() -> std::string;

  /// Get a directory where the app can store internal generated data.
  /// This directory should not be included in backups and the app
  /// should remain functional if this directory is completely cleared
  /// between runs (though it is expected that things stay intact here
  /// *while* the app is running).
  auto GetVolatileDataDirectory() -> std::string;

  /// Return a directory where the local user can manually place Python files
  /// where they will be accessible by the app. When possible, this directory
  /// should be in a place easily accessible to the user.
  auto GetUserPythonDirectory() -> std::string;

  /// Return the directory where the app expects to find its bundled Python
  /// files.
  auto GetAppPythonDirectory() -> std::string;

  /// Return the directory where bundled 3rd party Python files live.
  auto GetSitePythonDirectory() -> std::string;

  /// Return the directory where game replay files live.
  auto GetReplaysDir() -> std::string;

  /// Return en_US or whatnot.
  virtual auto GetLocale() -> std::string;

  virtual auto GetUserAgentString() -> std::string;
  virtual auto GetOSVersionString() -> std::string;

  // Chdir to wherever our bundled data lives.
  // (note to self: should rejigger this to avoid the chdir).
  virtual auto SetupDataDirectory() -> void;

  /// Set an environment variable as utf8, overwriting if it already exists.
  /// Raises an exception on errors.
  virtual void SetEnv(const std::string& name, const std::string& value);

  /// Are we being run from a terminal? (should we show prompts, etc?).
  virtual auto IsStdinATerminal() -> bool;

  /// Return hostname or other id suitable for displaying in network search
  /// results, etc.
  auto GetDeviceName() -> std::string;

  /// Get a UUID for use with things like device-accounts. This function
  /// should not be used for other purposes, should not be modified, and
  /// eventually should go away after device accounts are phased out.
  /// Also, this value should never be shared beyond the local device.
  auto GetLegacyDeviceUUID() -> const std::string&;

  /// Get a UUID for the current device that is meant to be publicly shared.
  /// This value will change occasionally due to OS updates, app updates, or
  /// other factors, so it can not be used as a permanent identifier, but it
  /// should remain constant over short periods and should not be easily
  /// changeable by the user, making it useful for purposes such as temporary
  /// server bans or spam prevention.
  auto GetPublicDeviceUUID() -> std::string;

  /// Return values which can be hashed to create a public device uuid.
  /// Ideally these values should come from an OS-provided guid. They
  /// should not include anything that is easily user-changeable.
  /// IMPORTANT: Only hashed/transformed versions of these values should
  /// ever be shared beyond the local device.
  virtual auto GetDeviceUUIDInputs() -> std::list<std::string>;

  /// Return whether there is an actual legacy-device-uuid value for
  /// this platform, and also return it if so.
  virtual auto GetRealLegacyDeviceUUID(std::string* uuid) -> bool;

  /// Are we running on a tv?
  virtual auto IsRunningOnTV() -> bool;

  /// Are we on a daydream-enabled Android device?
  virtual auto IsRunningOnDaydream() -> bool;

  /// Do we have touchscreen hardware?
  auto HasTouchScreen() -> bool;

  /// Are we running on a desktop setup in general?
  virtual auto IsRunningOnDesktop() -> bool;

  /// Are we running on fireTV hardware?
  virtual auto IsRunningOnFireTV() -> bool;

  // For enabling some special hardware optimizations for nvidia.
  auto is_tegra_k1() const -> bool { return is_tegra_k1_; }
  auto set_is_tegra_k1(bool val) -> void { is_tegra_k1_ = val; }

  /// Return whether this platform includes its own Python distribution
  virtual auto ContainsPythonDist() -> bool;

#pragma mark INPUT DEVICES -----------------------------------------------------

  // Return a name for a ballistica keycode.
  virtual auto GetKeyName(int keycode) -> std::string;

#pragma mark IN APP PURCHASES --------------------------------------------------

  virtual auto Purchase(const std::string& item) -> void;

  // Restore purchases (currently only relevant on Apple platforms).
  virtual auto RestorePurchases() -> void;

  // Purchase was ack'ed by the master-server (so can consume).
  virtual auto PurchaseAck(const std::string& purchase,
                           const std::string& order_id) -> void;

#pragma mark ANDROID -----------------------------------------------------------

  virtual auto GetAndroidExecArg() -> std::string;
  virtual auto AndroidSetResString(const std::string& res) -> void;
  virtual auto AndroidSynthesizeBackPress() -> void;
  virtual auto AndroidQuitActivity() -> void;
  virtual auto AndroidShowAppInvite(const std::string& title,
                                    const std::string& message,
                                    const std::string& code) -> void;
  virtual auto AndroidRefreshFile(const std::string& file) -> void;
  virtual auto AndroidShowWifiSettings() -> void;
  virtual auto AndroidGetExternalFilesDir() -> std::string;

#pragma mark PERMISSIONS -------------------------------------------------------

  /// Request the permission asynchronously.
  /// If the permission cannot be requested (due to having been denied, etc)
  /// then this may also present a message or pop-up instructing the user how
  /// to manually grant the permission (up to individual platforms to
  /// implement).
  virtual auto RequestPermission(Permission p) -> void;

  /// Returns true if this permission has been granted (or if asking is not
  /// required for it).
  virtual auto HavePermission(Permission p) -> bool;

#pragma mark ANALYTICS ---------------------------------------------------------

  virtual auto SetAnalyticsScreen(const std::string& screen) -> void;
  virtual auto IncrementAnalyticsCount(const std::string& name, int increment)
      -> void;
  virtual auto IncrementAnalyticsCountRaw(const std::string& name,
                                          int increment) -> void;
  virtual auto IncrementAnalyticsCountRaw2(const std::string& name,
                                           int uses_increment, int increment)
      -> void;
  virtual auto SubmitAnalyticsCounts() -> void;

#pragma mark APPLE -------------------------------------------------------------

  virtual auto NewAutoReleasePool() -> void*;
  virtual auto DrainAutoReleasePool(void* pool) -> void;
  // FIXME: Can we consolidate these with the general music playback calls?
  virtual auto MacMusicAppInit() -> void;
  virtual auto MacMusicAppGetVolume() -> int;
  virtual auto MacMusicAppSetVolume(int volume) -> void;
  virtual auto MacMusicAppGetLibrarySource() -> void;
  virtual auto MacMusicAppStop() -> void;
  virtual auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool;
  virtual auto MacMusicAppGetPlaylists() -> std::list<std::string>;

#pragma mark TEXT RENDERING ----------------------------------------------------

  // Set bounds/width info for a bit of text.
  // (will only be called in BA_ENABLE_OS_FONT_RENDERING is set)
  virtual auto GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                     float* width) -> void;
  virtual auto FreeTextTexture(void* tex) -> void;
  virtual auto CreateTextTexture(int width, int height,
                                 const std::vector<std::string>& strings,
                                 const std::vector<float>& positions,
                                 const std::vector<float>& widths, float scale)
      -> void*;
  virtual auto GetTextTextureData(void* tex) -> uint8_t*;

#pragma mark ACCOUNTS ----------------------------------------------------------

  virtual auto SignInV1(const std::string& account_type) -> void;
  virtual auto SignOutV1() -> void;

  virtual auto GameCenterLogin() -> void;
  virtual auto V1LoginDidChange() -> void;

  /// Returns the ID to use for the device account.
  auto GetDeviceV1AccountID() -> std::string;

  /// Return the prefix to use for device-account ids on this platform.
  virtual auto GetDeviceV1AccountUUIDPrefix() -> std::string;

#pragma mark MUSIC PLAYBACK ----------------------------------------------------

  // FIXME: currently these are wired up on Android; need to generalize
  //  to support mac/itunes or other music player types.
  virtual auto MusicPlayerPlay(PyObject* target) -> void;
  virtual auto MusicPlayerStop() -> void;
  virtual auto MusicPlayerShutdown() -> void;
  virtual auto MusicPlayerSetVolume(float volume) -> void;

#pragma mark ADS ---------------------------------------------------------------

  virtual auto ShowAd(const std::string& purpose) -> void;

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

  virtual auto GetFriendScores(const std::string& game,
                               const std::string& game_version,
                               void* py_callback) -> void;
  virtual auto SubmitScore(const std::string& game, const std::string& version,
                           int64_t score) -> void;
  virtual auto ReportAchievement(const std::string& achievement) -> void;
  virtual auto HaveLeaderboard(const std::string& game,
                               const std::string& config) -> bool;

  virtual auto ShowOnlineScoreUI(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version) -> void;
  virtual auto ResetAchievements() -> void;

#pragma mark NETWORKING --------------------------------------------------------

  virtual auto CloseSocket(int socket) -> void;
  virtual auto GetBroadcastAddrs() -> std::vector<uint32_t>;
  virtual auto SetSocketNonBlocking(int sd) -> bool;

#pragma mark ERRORS & DEBUGGING ------------------------------------------------

  /// Should return a subclass of PlatformStackTrace allocated via new.
  /// Platforms with no meaningful stack trace functionality can return nullptr.
  virtual auto GetStackTrace() -> PlatformStackTrace*;

  // Called during stress testing.
  virtual auto GetMemUsageInfo() -> std::string;

  /// Optionally override fatal error reporting. If true is returned, default
  /// fatal error reporting will not run.
  virtual auto ReportFatalError(const std::string& message,
                                bool in_top_level_exception_handler) -> bool;

  /// Optionally override fatal error handling. If true is returned, default
  /// fatal error handling will not run.
  virtual auto HandleFatalError(bool exit_cleanly,
                                bool in_top_level_exception_handler) -> bool;

  /// If this platform has the ability to show a blocking dialog on the main
  /// thread for fatal errors, return true here.
  virtual auto CanShowBlockingFatalErrorDialog() -> bool;

  /// Called on the main thread when a fatal error occurs.
  /// Will only be called if CanShowBlockingFatalErrorDialog() is true.
  virtual auto BlockingFatalErrorDialog(const std::string& message) -> void;

  /// Use this instead of looking at errno (translates winsock errors to errno).
  virtual auto GetSocketError() -> int;

  /// Return a string for the current value of errno.
  virtual auto GetErrnoString() -> std::string;

  /// Return a description of errno (unix) or WSAGetLastError() (windows).
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

#pragma mark MISC --------------------------------------------------------------

  // Return a monotonic time measurement in milliseconds since launch.
  // To get a time value that is guaranteed to not jump around or go backwards,
  // use ballistica::GetRealTime() (which is an abstraction around this).
  auto GetTicks() const -> millisecs_t;

  // A raw milliseconds value (not relative to launch time).
  static auto GetCurrentMilliseconds() -> millisecs_t;
  static auto GetCurrentSeconds() -> int64_t;

  static auto SleepMS(millisecs_t ms) -> void;

  /// Pop up a text edit dialog.
  virtual auto EditText(const std::string& title, const std::string& value,
                        int max_chars) -> void;

  /// Open the provided URL in a browser or whatnot.
  auto OpenURL(const std::string& url) -> void;

  /// Given a C++ symbol, attempt to return a pretty one.
  virtual auto DemangleCXXSymbol(const std::string& s) -> std::string;

  /// Called each time through the main event loop;
  /// for custom pumping/handling.
  virtual auto RunEvents() -> void;

  /// Called when the app module is pausing.
  /// Note: only app-thread (main thread) stuff should happen here.
  /// (don't push calls to other threads/etc).
  virtual auto OnAppPause() -> void;

  /// Called when the app module is resuming.
  virtual auto OnAppResume() -> void;

  /// Is the OS currently playing music? (so we can avoid doing so).
  virtual auto IsOSPlayingMusic() -> bool;

  /// Pass platform-specific misc-read-vals along to the OS (as a json string).
  virtual auto SetPlatformMiscReadVals(const std::string& vals) -> void;

  /// Show/hide the hardware cursor.
  virtual auto SetHardwareCursorVisible(bool visible) -> void;

  /// Get the most up-to-date cursor position.
  virtual auto GetCursorPosition(float* x, float* y) -> void;

  /// Quit the app (can be immediate or via posting some high level event).
  virtual auto QuitApp() -> void;

  // Note to self: do we want to deprecate this?...
  virtual auto GetScoresToBeat(const std::string& level,
                               const std::string& config, void* py_callback)
      -> void;

  /// Open a file using the system default method (in another app, etc.)
  virtual auto OpenFileExternally(const std::string& path) -> void;

  /// Open a directory using the system default method (Finder, etc.)
  virtual auto OpenDirExternally(const std::string& path) -> void;

  /// Set the name of the current thread (for debugging).
  virtual auto SetCurrentThreadName(const std::string& name) -> void;

  // If display-resolution can be directly set on this platform,
  // return true and set the native full res here.  Otherwise return false;
  virtual auto GetDisplayResolution(int* x, int* y) -> bool;

  auto using_custom_app_python_dir() const {
    return using_custom_app_python_dir_;
  }

 protected:
  /// Open the provided URL in a browser or whatnot.
  virtual auto DoOpenURL(const std::string& url) -> void;

  /// Called once per platform to determine touchscreen presence.
  virtual auto DoHasTouchScreen() -> bool;

  /// Platforms should override this to provide device name.
  virtual auto DoGetDeviceName() -> std::string;

  /// Attempt to actually create a directory.
  /// Should *not* raise Exceptions if it already exists or if quiet is true.
  virtual auto DoMakeDir(const std::string& dir, bool quiet) -> void;

  /// Attempt to actually get an abs path. This will only be called if
  /// the path is valid and exists.
  virtual auto DoAbsPath(const std::string& path, std::string* outpath) -> bool;

  /// Calc the user scripts dir path for this platform.
  /// This will be called once and the path cached.
  virtual auto DoGetUserPythonDirectory() -> std::string;

  /// Return the default config directory for this platform.
  /// This will be used as the config dir if not overridden via command
  /// line options, etc.
  virtual auto GetDefaultConfigDirectory() -> std::string;

  /// Return the default Volatile data dir for this platform.
  /// This will be used as the volatile-data-dir if not overridden via command
  /// line options/etc.
  virtual auto GetDefaultVolatileDataDirectory() -> std::string;

  /// Generate a random UUID string.
  virtual auto GenerateUUID() -> std::string;

  virtual auto DoClipboardIsSupported() -> bool;
  virtual auto DoClipboardHasText() -> bool;
  virtual auto DoClipboardSetText(const std::string& text) -> void;
  virtual auto DoClipboardGetText() -> std::string;

 private:
  bool using_custom_app_python_dir_{};
  bool have_config_dir_{};
  bool have_has_touchscreen_value_{};
  bool have_touchscreen_{};
  bool is_tegra_k1_{};
  bool have_clipboard_is_supported_{};
  bool clipboard_is_supported_{};
  bool attempted_to_make_user_scripts_dir_{};
  bool made_volatile_data_dir_{};
  bool have_device_uuid_{};
  bool ran_base_post_init_{};
  millisecs_t starttime_{};
  std::string device_name_;
  std::string legacy_device_uuid_;
  std::string config_dir_;
  std::string user_scripts_dir_;
  std::string volatile_data_dir_;
  std::string app_python_dir_;
  std::string site_python_dir_;
  std::string replays_dir_;
  std::string public_device_uuid_;
};

}  // namespace ballistica

#endif  // BALLISTICA_PLATFORM_PLATFORM_H_
