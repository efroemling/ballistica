// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_PLATFORM_H_
#define BALLISTICA_CORE_PLATFORM_PLATFORM_H_

#include <sys/stat.h>

#include <cstdio>
#include <functional>
#include <list>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

/// Low level platform-specific functionality is contained here, to be
/// implemented by platform-specific subclasses.
///
/// TODO(ericf): Much of the stuff below should be migrated into
///   AppPlatform or other higher-level places. Core should contain only
///   what is directly needed to bootstrap Python and the engine
///   environment.
class Platform {
 public:
  /// Instantiate the Platform subclass for the current build.
  static auto Create() -> Platform*;

#pragma mark LIFECYCLE/SETTINGS ------------------------------------------------

  /// Called after our singleton has been instantiated. Any construction
  /// functionality requiring virtual functions resolving to their final
  /// class versions can go here.
  virtual void PostInit();

  virtual void OnScreenSizeChange();
  virtual void StepDisplayTime();

  // Get/set values before standard game settings are available (for values
  // needed before SDL init/etc). FIXME: We should have some sort of
  // 'bootconfig.json' file for these. (or simply read the regular config in
  // via c++ immediately)
  auto GetLowLevelConfigValue(const char* key, int default_value) -> int;
  void SetLowLevelConfigValue(const char* key, int value);

#pragma mark FILES -------------------------------------------------------------

  /// remove() supporting UTF8 strings.
  virtual auto Remove(const char* path) -> int;

  /// stat() supporting UTF8 strings.
  virtual auto Stat(const char* path, struct BA_STAT* buffer) -> int;

  /// fopen() supporting UTF8 strings.
  virtual auto FOpen(const char* path, const char* mode) -> FILE*;

  /// rename() supporting UTF8 strings. For cross-platform consistency, this
  /// should also remove any file that exists at the target location first.
  virtual auto Rename(const char* oldname, const char* newname) -> int;

  /// Simple cross-platform check for existence of a file.
  auto FilePathExists(const std::string& name) -> bool;

  /// Attempt to make a directory. Raise an Exception if unable, unless
  /// quiet is true. Succeeds if the directory already exists.
  void MakeDir(const std::string& dir, bool quiet = false);

  /// Return the current working directory.
  virtual auto GetCWD() -> std::string;

  /// Unlink a file.
  virtual void Unlink(const char* path);

  /// Return the absolute path for the provided path. Note that this
  /// requires the path to already exist.
  auto AbsPath(const std::string& path, std::string* outpath) -> bool;

#pragma mark PRINTING/LOGGING --------------------------------------------------

  /// Display a message to any default log for the platform (android log,
  /// etc.) This can be called from any thread. The default implementation does
  /// nothing. Implementations should not print to stdout or stderr, as mapping
  /// those to log messages is handled at a higher level. Implementations should
  /// not use any Python functionality, as this may be called before Python is
  /// spun up or after it is finalized.
  virtual void EmitPlatformLog(std::string_view name, LogLevel level,
                               std::string_view msg);

#pragma mark ENVIRONMENT -------------------------------------------------------

  /// Return a simple name for the platform: 'mac', 'windows', 'linux', etc.
  virtual auto GetLegacyPlatformName() -> std::string;

  /// Return a simple name for the subplatform: 'amazon', 'google', etc.
  virtual auto GetLegacySubplatformName() -> std::string;

  /// Return the interface type based on the environment (phone, tablet,
  /// etc).
  virtual auto GetDefaultUIScale() -> UIScale;

  /// Return default data-directory value for monolithic builds. This will be
  /// passed to pyenv as a starting point, and whatever pyenv gives us back
  /// will be our actual value.
  auto GetDataDirectoryMonolithicDefault() -> std::string;

  /// Return default config-directory value for monolithic builds. This will be
  /// passed to pyenv as a starting point, and whatever pyenv gives us back
  /// will be our actual value.
  auto GetConfigDirectoryMonolithicDefault() -> std::optional<std::string>;

  /// Return default user-python (mods) directory value for monolithic
  /// builds. This will be passed to pyenv as a starting point, and whatever
  /// pyenv gives us back will be our actual value.
  auto GetUserPythonDirectoryMonolithicDefault() -> std::optional<std::string>;

  /// Return default cache-directory value for monolithic builds. This will
  /// be passed to pyenv as a starting point, and whatever pyenv gives us
  /// back will be our actual value.
  auto GetCacheDirectoryMonolithicDefault() -> std::optional<std::string>;

  /// Return the directory where game replay files live.
  auto GetReplaysDir() -> std::string;

  /// Return a `long_value` of a Ballistica locale (ie: "ChineseSimplified")
  /// or an empty string if this is not available. In the empty string case,
  /// the app will fall back to using GetLocaleTag() to determine the
  /// Ballistica locale. By embedding Ballistica locale strings as native
  /// platform translations (ie: strings.xml on Android, etc.) the app can
  /// allow the OS to use whatever logic it wants (fallbacks languages, etc)
  /// to arrive at one of our locales. This is likely to be more robust than
  /// us trying to do the same thing through a single locale tag.
  virtual auto GetBaLocale() -> std::string;

  /// Return a string describing the active language, country, etc. This can
  /// be provided in BCP 47 form (`en-US`) or POSIX locale form
  /// (`en_US.UTF-8`).
  virtual auto GetLocaleTag() -> std::string;

  /// Get the older more complex user-agent-string, used for communication
  /// with v1 servers/etc. This should go away eventually.
  virtual auto GetLegacyUserAgentString() -> std::string;

  /// Return a human readable os version such as "10.4.2".
  /// Can return a blank string when not known/relevant.
  virtual auto GetOSVersionString() -> std::string;

  /// Set an environment variable as utf8, overwriting if it already exists.
  /// Raises an exception on errors.
  virtual void SetEnv(const std::string& name, const std::string& value);

  virtual auto GetEnv(const std::string& name) -> std::optional<std::string>;

  /// Return hostname or other id suitable for displaying in network search
  /// results, etc.
  auto GetDeviceName() -> std::string;

  /// Return a general identifier for the hardware device.
  auto GetDeviceDescription() -> std::string;

  /// Get a UUID for use with things like device-accounts. This function
  /// should not be used for other purposes, should not be modified, and
  /// eventually should go away after device accounts are phased out. Also,
  /// this value should never be shared beyond the local device.
  auto GetLegacyDeviceUUID() -> const std::string&;

  /// Return values which can be hashed to create a public device uuid.
  /// Ideally these values should come from an OS-provided guid. They should
  /// not include anything that is easily user-changeable. IMPORTANT: Only
  /// hashed/transformed versions of these values should ever be shared
  /// beyond the local device.
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

  /// Whether this is a flagged low-end device. Only ever true on Android
  /// (computed Java-side from GLES version + RAM before the renderer comes
  /// up); always false on desktop/iOS. Drives reduced framebuffer color
  /// depth, render resolution, and graphics quality. See
  /// docs/initiatives/low-end-device-tiering.md.
  auto low_end_device() const -> bool { return low_end_device_; }
  void set_low_end_device(bool val) { low_end_device_ = val; }

  /// Run system() command on OSs which support it. Throws exception
  /// elsewhere.
  static auto System(const char* cmd) -> int;

#pragma mark ANDROID -----------------------------------------------------------

  virtual auto GetAndroidExecArg() -> std::string;
  virtual void AndroidSetResString(const std::string& res);
  virtual auto AndroidGetExternalFilesDir() -> std::string;

#pragma mark PERMISSIONS -------------------------------------------------------

  /// Request the permission asynchronously. If the permission cannot be
  /// requested (due to having been denied, etc) then this may also present
  /// a message or pop-up instructing the user how to manually grant the
  /// permission (up to individual platforms to implement).
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

  // virtual auto NewAutoReleasePool() -> void*;
  // virtual void DrainAutoReleasePool(void* pool);
  // FIXME: Can we consolidate these with the general music playback calls?
  virtual void MacMusicAppInit();
  virtual auto MacMusicAppGetVolume() -> int;
  virtual void MacMusicAppSetVolume(int volume);
  virtual auto MacMusicAppGetPlaylists() -> std::list<std::string>;
  virtual auto MacMusicAppPlayPlaylist(const std::string& playlist) -> bool;
  virtual void MacMusicAppStop();

#pragma mark TEXT RENDERING ----------------------------------------------------

  // Set bounds/width info for a bit of text. (will only be called in
  // BA_ENABLE_OS_FONT_RENDERING is set)
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

  virtual void SignInV1(const std::string& account_type);
  virtual void SignOutV1();

  // virtual void GameCenterLogin();
  virtual void V1LoginDidChange();

  /// Returns the ID to use for the device account.
  auto GetDeviceV1AccountID() -> std::string;

  /// Return the prefix to use for device-account ids on this platform.
  virtual auto GetDeviceV1AccountUUIDPrefix() -> std::string;

#pragma mark MUSIC PLAYBACK ----------------------------------------------------

  // FIXME: currently these are wired up on Android; need to generalize to
  //  support mac/itunes or other music player types.
  virtual void MusicPlayerPlay(PyObject* target);
  virtual void MusicPlayerStop();
  virtual void MusicPlayerShutdown();
  virtual void MusicPlayerSetVolume(float volume);

#pragma mark ADS ---------------------------------------------------------------

  virtual void ShowAd(const std::string& purpose);

  // Return whether we have the ability to show *any* ads.
  virtual auto GetHasAds() -> bool;

  // Return whether we have the ability to show longer-form video ads
  // (suitable for rewards).
  virtual auto GetHasVideoAds() -> bool;

#pragma mark GAME SERVICES -----------------------------------------------------

  // Given a raw leaderboard score, convert it to what the game uses.
  // For instance, platforms may return times as milliseconds while we require
  // hundredths of a second, etc.
  virtual auto ConvertIncomingLeaderboardScore(
      const std::string& leaderboard_id, int score) -> int;

  virtual void SubmitScore(const std::string& game, const std::string& version,
                           int64_t score);
  virtual void ReportAchievement(const std::string& achievement);
  virtual auto HaveLeaderboard(const std::string& game,
                               const std::string& config) -> bool;

  virtual void ShowGameServiceUI(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version);
  virtual void ResetAchievements();

#pragma mark NETWORKING --------------------------------------------------------

  virtual void CloseSocket(int socket);
  virtual auto GetBroadcastAddrs() -> std::vector<uint32_t>;
  virtual auto SetSocketNonBlocking(int sd) -> bool;

  /// Callback type for receiving network path availability state.
  using NetworkAvailabilityCallback = std::function<void(bool available)>;

  /// Register a callback to receive OS-reported network path
  /// availability.
  ///
  /// API contract: callers MUST assume the network is unavailable
  /// until a callback fires with ``true``. The callback is invoked
  /// only on changes from the assumed-or-cached state, so consumers
  /// that haven't yet been told ``true`` should treat the network
  /// as down. This avoids both a redundant initial cb(false) and
  /// the race where startup code reads a stale "available" before
  /// the OS has reported.
  ///
  /// In practice this means:
  ///   - First registration: typically no synchronous fire. The
  ///     callback fires once the OS reports (which happens promptly:
  ///     synchronous on platforms with no native monitoring; usually
  ///     within milliseconds on those that do).
  ///   - Late registration (after the OS has already reported
  ///     ``true``): a synchronous cb(true) fires inside this call so
  ///     the late consumer learns current state immediately.
  ///   - Any state change: async cb fires on whatever thread the OS
  ///     dispatches on.
  ///
  /// The callback may fire on ANY thread — the OS-provided dispatch
  /// queue, a worker thread, or the registration thread itself.
  /// Callers are responsible for marshaling to whatever thread they
  /// need, and for any synchronization on state they touch.
  ///
  /// 'false' is a strict "definitely offline" signal — the OS sees
  /// no usable network path (airplane mode, wifi off with no
  /// cellular, ethernet unplugged); callers should short-circuit
  /// network attempts. 'true' is "maybe online" — captive portals,
  /// ISP outages, and DNS issues still report 'true', so existing
  /// reachability probes are still required.
  ///
  /// On platforms without a native implementation, the default
  /// DoStartNetworkAvailabilityMonitoring() reports ``true`` once
  /// and never again, preserving today's "always try" behavior. As
  /// a testing aid, setting environment variable
  /// BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE=1 substitutes a thread
  /// that toggles every 5 seconds (starting offline) in place of
  /// any real platform monitoring, so consumers can be exercised
  /// through both states without actually severing the network.
  ///
  /// There is no deregistration; callbacks are expected to live for
  /// the app's lifetime.
  ///
  /// Non-virtual: this method manages the callback list, change
  /// dedup, and DEBUG-level logging on transitions. Platform
  /// subclasses hook in by overriding
  /// DoStartNetworkAvailabilityMonitoring() and reporting state
  /// changes via SetNetworkAvailability().
  void AddNetworkAvailabilityCallback(NetworkAvailabilityCallback cb);

  /// Stop dispatching network-availability changes to registered
  /// callbacks. Idempotent. Once called, subsequent
  /// SetNetworkAvailability() calls and synchronous fires from
  /// AddNetworkAvailabilityCallback() are no-ops, and OS-level
  /// monitors that are still running on detached threads
  /// (NWPathMonitor, NLM event sink, ConnectivityManager.NetworkCallback)
  /// have no further effect. The OS monitors themselves are not
  /// torn down — they live until process exit — only the dispatch
  /// path is silenced. Intended to be called early in app shutdown,
  /// before subscriber state (e.g. Python interpreter, logic-thread
  /// objects) starts being torn down.
  void StopNetworkAvailabilityDispatch();

#pragma mark ERRORS & DEBUGGING ------------------------------------------------

  /// Should return a subclass of NativeStackTrace allocated via new. It is
  /// up to the caller to call delete on the returned trace when done with
  /// it. Platforms with no meaningful stack trace functionality can return
  /// nullptr.
  virtual auto GetNativeStackTrace() -> NativeStackTrace*;

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
  virtual void BlockingFatalErrorDialog(const std::string& message);

  /// Use this instead of looking at errno (translates winsock errors to errno).
  virtual auto GetSocketError() -> int;

  /// Return a string for the current value of errno.
  virtual auto GetErrnoString() -> std::string;

  /// Return a description of errno (unix) or WSAGetLastError() (windows).
  virtual auto GetSocketErrorString() -> std::string;

  /// Set a key to be included in crash logs or other debug cases.
  /// This is expected to be lightweight as it may be called often.
  virtual void SetDebugKey(const std::string& key, const std::string& value);

  /// Print a log message to be included in crash logs or other debug
  /// mechanisms (example: Crashlytics). V1-cloud-log messages get forwarded
  /// to here as well. It can be useful to call this directly to report
  /// extra details that may help in debugging, as these calls are not
  /// considered 'noteworthy' or presented to the user as standard Log()
  /// calls are.
  void LowLevelDebugLog(const std::string& msg);

#pragma mark MISC --------------------------------------------------------------

  /// Return a time measurement in milliseconds since launch. It *should* be
  /// monotonic. For most purposes, AppTime values are preferable since
  /// their progression pauses during app suspension and they are 100%
  /// guaranteed to not go backwards.
  auto TimeSinceLaunchMillisecs() const -> millisecs_t;

  /// Return a milliseconds value which should not drift or go backwards
  /// even if system time changes. It is not based on any particular
  /// start-time so only use it to measure time differences.
  static auto TimeMonotonicMillisecs() -> millisecs_t;

  /// Return a microseconds value which should not drift or go backwards
  /// even if system time changes. It is not based on any particular
  /// start-time so only use it to measure time differences.
  static auto TimeMonotonicMicrosecs() -> microsecs_t;

  /// Return a seconds value which should not drift or go backwards even if
  /// system time changes. It is not based on any particular start-time so
  /// only use it to measure time differences.
  static auto TimeMonotonicSeconds() -> seconds_t;

  /// Return an integer seconds value which should not drift or go backwards
  /// even if system time changes. It is not based on any particular
  /// start-time so only use it to measure time differences.
  static auto TimeMonotonicWholeSeconds() -> int64_t;

  /// Return seconds since the epoch; same as Python's time.time().
  static auto TimeSinceEpochSeconds() -> seconds_t;

  static void SleepSeconds(seconds_t duration);
  static void SleepMillisecs(millisecs_t duration);
  static void SleepMicrosecs(microsecs_t duration);

  /// Given a C++ symbol, attempt to return a pretty one.
  virtual auto DemangleCXXSymbol(const std::string& s) -> std::string;

  /// Called each time through the main event loop;
  /// for custom pumping/handling.
  virtual void RunEvents();

  /// Is the OS currently playing music? (so we can avoid doing so).
  virtual auto IsOSPlayingMusic() -> bool;

  /// Pass platform-specific misc-read-vals along to the OS (as a json
  /// string).
  virtual void SetPlatformMiscReadVals(const std::string& vals);

  /// Set the name of the current thread (for debugging).
  virtual void SetCurrentThreadName(const std::string& name);

  // If display-resolution can be directly set on this platform, return true
  // and set the native full res here. Otherwise return false;
  virtual auto GetDisplayResolution(int* x, int* y) -> bool;

  /// Are we being run from a terminal? (should we show prompts, etc?).
  auto is_stdin_a_terminal() const { return is_stdin_a_terminal_; }

 protected:
  /// Are we being run from a terminal? (should we show prompts, etc?).
  virtual auto GetIsStdinATerminal() -> bool;

  /// Called once per platform to determine touchscreen presence.
  virtual auto DoHasTouchScreen() -> bool;

  /// Platforms should override this to provide a device name suitable for
  /// displaying in network join lists/etc. Technically this is more like
  /// hostname.
  virtual auto DoGetDeviceName() -> std::string;

  /// Platforms should override this to provide a generic description of the
  /// device; something like "iPhone 12 Pro".
  virtual auto DoGetDeviceDescription() -> std::string;

  /// Attempt to actually create a directory. Should *not* raise Exceptions
  /// if it already exists or if quiet is true.
  virtual void DoMakeDir(const std::string& dir, bool quiet);

  /// Attempt to actually get an abs path. This will only be called if the
  /// path is valid and exists.
  virtual auto DoAbsPath(const std::string& path, std::string* outpath) -> bool;

  /// Calc the user scripts dir path for this platform. This will be called
  /// once and the path cached.
  virtual auto DoGetUserPythonDirectoryMonolithicDefault()
      -> std::optional<std::string>;

  /// Return the default config directory for this platform on monolithic
  /// builds. This will be used if not overridden via command line options,
  /// etc.
  virtual auto DoGetConfigDirectoryMonolithicDefault()
      -> std::optional<std::string>;

  /// Return the default cache directory for this platform on monolithic
  /// builds. This will be used if not overridden via command line options,
  /// etc.
  virtual auto DoGetCacheDirectoryMonolithicDefault()
      -> std::optional<std::string>;

  /// Return the default data directory for this platform on monolithic
  /// builds. This will be used if not overridden by command line options,
  /// etc. This is the one monolithic-default value that is not optional.
  virtual auto DoGetDataDirectoryMonolithicDefault() -> std::string;

  /// Return the default cache dir for this platform. This will be
  /// used if not overridden via command line options/etc.
  // virtual auto GetDefaultCacheDirectory() -> std::string;

  /// Generate a random UUID string.
  auto GenerateUUID() -> std::string;

  virtual void HandleLowLevelDebugLog(const std::string& msg);

  /// Called once on the first network-availability registration for
  /// the platform to subscribe to OS-level monitoring (NWPathMonitor,
  /// ConnectivityManager, INetworkListManager, NetworkManager via
  /// D-Bus, etc.) and feed state back through SetNetworkAvailability().
  /// The default implementation is a no-op (value stays at the
  /// initial 'true'). Not invoked when the
  /// BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE env var is set; the debug
  /// toggle thread runs in place of OS monitoring.
  virtual void DoStartNetworkAvailabilityMonitoring();

  /// Called by subclasses (and the debug toggler) to report the
  /// current network availability state. Thread-safe; callable from
  /// any thread. Logs at DEBUG and dispatches to all registered
  /// callbacks if (and only if) the value differs from the last
  /// reported value.
  void SetNetworkAvailability(bool available);

  Platform();
  virtual ~Platform();

 private:
  void RunNetworkAvailabilityDebugToggle_();

  bool is_stdin_a_terminal_{};
  bool have_has_touchscreen_value_{};
  bool have_touchscreen_{};
  bool low_end_device_{};
  bool made_cache_dir_{};
  bool have_device_uuid_{};
  bool ran_base_post_init_{};
  millisecs_t start_time_millisecs_{};
  std::string device_name_;
  std::string device_description_;
  std::string legacy_device_uuid_;
  std::string cache_dir_;
  std::string replays_dir_;

  std::mutex network_availability_mutex_;
  std::vector<NetworkAvailabilityCallback> network_availability_callbacks_;
  bool network_availability_monitoring_started_{};
  // Defaults to false so consumers must wait for an affirmative
  // signal (a callback firing 'true') before assuming network is
  // up. This avoids races where code at startup reads the value
  // before the platform's first OS report has arrived. Platforms
  // without a real implementation get an immediate 'true' from the
  // default DoStartNetworkAvailabilityMonitoring() so they're not
  // stuck offline forever.
  bool network_availability_value_{false};
  // Set by StopNetworkAvailabilityDispatch() during app shutdown.
  // Once true, SetNetworkAvailability and the synchronous fire in
  // AddNetworkAvailabilityCallback are no-ops. Lets us silence
  // late OS-callback dispatches before subscriber state is torn
  // down by the shutdown cascade.
  bool network_availability_dispatch_stopped_{};
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_PLATFORM_PLATFORM_H_
