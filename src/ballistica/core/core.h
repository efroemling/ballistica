// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_CORE_H_
#define BALLISTICA_CORE_CORE_H_

#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include "ballistica/core/support/core_config.h"

namespace ballistica::core {

// Predeclare types we use throughout our FeatureSet so most headers can get
// away with just including this header.
class BaseSoftInterface;
class CoreConfig;
class CoreFeatureSet;
class CorePlatform;
class CorePython;
class Logging;

// Our feature-set's globals.
//
// Feature-sets should NEVER directly access globals in another
// feature-set's namespace. All functionality we need from other
// feature-sets should be imported into globals in our own namespace.
// Generally we do this when we are initially imported (just as regular
// Python modules do).

// Our pointer to our own feature-set.
extern CoreFeatureSet* g_core;

// We don't require the base feature-set but can use it if present. Base
// will supply us with this pointer if/when it spins up. So we must never
// assume this pointer is valid and must check for it with each use.
extern BaseSoftInterface* g_base_soft;

/// Core engine functionality.
class CoreFeatureSet {
 public:
  /// Import the core feature set. A core-config can be passed ONLY in
  /// monolithic builds when it is guaranteed that the Import will be
  /// allocating the CoreFeatureSet singleton. Also be aware that the
  /// initial core import must happen from whichever thread is considered
  /// the 'main' thread for the platform.
  static auto Import(const CoreConfig* config = nullptr) -> CoreFeatureSet*;

  /// Attempt to import the base feature-set. Will return nullptr if it is
  /// not available. This should only be used by code with soft dependencies
  /// on base. Regular code should talk to base directly to get its full
  /// interface.
  auto SoftImportBase() -> BaseSoftInterface*;

  /// The core-config we were inited with.
  auto core_config() const -> const CoreConfig&;

  /// Start a timer to force-kill our process after the set length of time.
  /// Can be used during shutdown or when trying to send a crash-report to
  /// ensure we don't hang indefinitely.
  void StartSuicideTimer(const std::string& action, millisecs_t delay);

  /// Apply the config set up by baenv to the engine.
  void ApplyBaEnvConfig();

  /// Are we running headless?
  auto HeadlessMode() -> bool;

  /// Return current app-time in milliseconds.
  ///
  /// App-time is basically the total time that the engine has been actively
  /// running. (The 'App' here is a slight misnomer). It will stop
  /// progressing while the app is suspended and will never go backwards.
  auto AppTimeMillisecs() -> millisecs_t;

  /// Return current app-time in microseconds.
  ///
  /// App-time is basically the total time that the engine has been actively
  /// running. (The 'App' here is a slight misnomer). It will stop
  /// progressing while the app is suspended and will never go backwards.
  auto AppTimeMicrosecs() -> microsecs_t;

  /// Return current app-time in seconds.
  ///
  /// App-time is basically the total time that the engine has been actively
  /// running. (The 'App' here is a slight misnomer). It will stop
  /// progressing while the app is suspended and will never go backwards.
  auto AppTimeSeconds() -> seconds_t;

  /// Are we in the 'main' thread? The thread that first inited Core is
  /// considered the 'main' thread; on most platforms it is the one where
  /// UI calls must be run/etc.
  auto InMainThread() -> bool {
    return std::this_thread::get_id() == main_thread_id();
  }

  /// Base path of build src dir so we can attempt to remove it from any
  /// source file paths we print.
  auto build_src_dir() const { return build_src_dir_; }

  const auto& legacy_user_agent_string() const {
    return legacy_user_agent_string_;
  }

  void set_legacy_user_agent_string(const std::string& val) {
    legacy_user_agent_string_ = val;
  }

  /// Return true if baenv values have been locked in: python paths, log
  /// handling, etc. Early-running code may wish to explicitly avoid making
  /// log calls until this condition is met to ensure predictable behavior.
  auto have_ba_env_vals() const { return have_ba_env_vals_; }

  /// Return the directory where the app expects to find its bundled Python
  /// files.
  auto GetAppPythonDirectory() -> std::optional<std::string>;

  /// Return a directory where the local user can manually place Python
  /// files where they will be accessible by the app. When possible, this
  /// directory should be in a place easily accessible to the user.
  auto GetUserPythonDirectory() -> std::optional<std::string>;

  /// Get the root config directory. This dir contains the app config file
  /// and other data considered essential to the app install.
  auto GetConfigDirectory() -> std::string;

  /// Get the path of the app config file.
  auto GetConfigFilePath() -> std::string;

  /// Get the path of the backup app config file. Backups are written each
  /// time a new config write happens.
  auto GetBackupConfigFilePath() -> std::string;

  /// Get the data directory. This dir contains ba_data and possibly other
  /// platform-specific bits needed for the app to function.
  auto GetDataDirectory() -> std::string;

  /// Get the cache directory. This dir contains data written by the app
  /// that it is able to recreate if needed. Files placed here are
  /// guaranteed to remain in place as long as the app is running, but any
  /// or all files may be purged between app runs.
  auto GetCacheDirectory() -> std::string;

  /// Return the directory where bundled 3rd party Python files live.
  auto GetSitePythonDirectory() -> std::optional<std::string>;

  // Are we using a non-standard app python dir (such as a 'sys' dir within
  // a user-python-dir).
  auto using_custom_app_python_dir() const {
    return using_custom_app_python_dir_;
  }

  /// Register various info about the current thread.
  void RegisterThread(const std::string& name);

  /// Should be called by a thread before it exits.
  void UnregisterThread();

  /// A bool set just before finalizing the Python interpreter and calling
  /// exit() or whatever is intended to be the last gasp of life for the
  /// binary. This can be polled periodically by background threads that may
  /// otherwise prevent the process from exiting.
  auto engine_done() const { return engine_done_; }
  void set_engine_done() { engine_done_ = true; }

  // Const components.
  CorePython* const python;
  CorePlatform* const platform;
  Logging* const logging;

  // The following are misc values that should be migrated to applicable
  // component classes or private vars.
  bool workspaces_in_use{};
  bool reset_vr_orientation{};
  bool user_ran_commands{};
  int master_server_source{};
  std::vector<EventLoop*> suspendable_event_loops;

#if BA_DEBUG_BUILD
  std::mutex object_list_mutex;
  Object* object_list_first{};
  int object_count{};
#endif

  std::thread::id main_thread_id() const { return main_thread_id_; }
  auto vr_mode() const { return vr_mode_; }
  auto event_loops_suspended() const { return event_loops_suspended_; }
  void set_event_loops_suspended(bool val) { event_loops_suspended_ = val; }
  auto CurrentThreadName() -> std::string;

  auto HandOverInitialAppConfig() -> PyObject*;

  auto ba_env_launch_timestamp() {
    // Make sure we set this before accessing it.
    //
    // UPDATE: Early fatal errors may access this before it gets set; we'd
    // rather not mask those by dying here. We can just watch out for -1
    // values in logs.
    //
    // assert(ba_env_launch_timestamp_ > 0.0);

    return ba_env_launch_timestamp_;
  }

 private:
  explicit CoreFeatureSet(CoreConfig config);
  static void DoImport_(const CoreConfig& config);
  auto CalcBuildSrcDir_() -> std::string;
  void RunSanityChecks_();
  void UpdateAppTime_();
  void PostInit_();

  CoreConfig core_config_;
  PyObject* initial_app_config_{};
  std::unordered_map<std::thread::id, std::string> thread_info_map_;
  std::mutex app_time_mutex_;
  std::thread::id main_thread_id_{};
  std::mutex thread_info_map_mutex_;
  std::string legacy_user_agent_string_{"BA_USER_AGENT_UNSET (" BA_PLATFORM
                                        " " BA_ARCH ")"};
  std::string build_src_dir_;
  std::string ba_env_config_dir_;
  std::string ba_env_cache_dir_;
  std::string ba_env_data_dir_;
  std::optional<std::string> ba_env_app_python_dir_;
  std::optional<std::string> ba_env_user_python_dir_;
  std::optional<std::string> ba_env_site_python_dir_;
  double ba_env_launch_timestamp_{-1.0};
  microsecs_t app_time_microsecs_{};
  microsecs_t last_app_time_measure_microsecs_;
  bool event_loops_suspended_{};
  bool tried_importing_base_{};
  bool started_suicide_{};
  bool have_ba_env_vals_{};
  bool vr_mode_{};
  bool using_custom_app_python_dir_{};
  bool engine_done_{};
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_CORE_H_
