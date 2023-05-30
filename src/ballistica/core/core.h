// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_CORE_H_
#define BALLISTICA_CORE_CORE_H_

#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include "ballistica/core/support/core_config.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

// Predeclare types we use throughout our FeatureSet so most
// headers can get away with just including this header.
class CoreConfig;
class CorePython;
class CorePlatform;
class CoreFeatureSet;
class BaseSoftInterface;

// Our feature-set's globals.
// Feature-sets should NEVER directly access globals in another feature-set's
// namespace. All functionality we need from other feature-sets should be
// imported into globals in our own namespace. Generally we do this when we
// are initially imported (just as regular Python modules do).
extern CoreFeatureSet* g_core;

// We don't require the base feature-set but can use it if present.
// Base will supply us with this pointer if/when it spins up.
// So we must never assume this pointer is valid and must check for it
// with each use.
extern BaseSoftInterface* g_base_soft;

/// Platform-agnostic global state for our overall system.
/// This gets created whenever we are used in any capacity, even if
/// we don't create/run an app.
/// Ideally most things here should be migrated to more specific
/// subsystems.
class CoreFeatureSet {
 public:
  /// Import the core feature set. A core-config can be passed ONLY
  /// in monolithic builds when it is guaranteed that the Import will be
  /// allocating the CoreFeatureSet singleton.
  static auto Import(const CoreConfig* config = nullptr) -> CoreFeatureSet*;

  /// Attempt to import the base feature-set. Will return nullptr if it is
  /// not available. This should only be used by code with soft dependencies
  /// on base. Regular code should talk to base directly to get its full
  /// interface.
  auto SoftImportBase() -> BaseSoftInterface*;

  /// The core-config we were inited with.
  const auto& core_config() const { return core_config_; }

  /// Start a timer to force-kill our process after the set length of time.
  /// Can be used during shutdown or when trying to send a crash-report to
  /// ensure we don't hang indefinitely.
  void StartSuicideTimer(const std::string& action, millisecs_t delay);

  // Call this if the main thread changes.
  // Fixme: Should come up with something less hacky feeling.
  void UpdateMainThreadID();

  auto* main_event_loop() const { return main_event_loop_; }
  auto IsVRMode() -> bool;

  /// Are we running headless?
  auto HeadlessMode() -> bool;

  /// Return current app-time in milliseconds.
  /// App-time is basically the total time that the engine has been actively
  /// running. (The 'App' here is a slight misnomer). It will stop progressing
  /// while the app is suspended and will never go backwards.
  auto GetAppTimeMillisecs() -> millisecs_t;

  /// Return current app-time in microseconds.
  /// App-time is basically the total time that the engine has been actively
  /// running. (The 'App' here is a slight misnomer). It will stop progressing
  /// while the app is suspended and will never go backwards.
  auto GetAppTimeMicrosecs() -> microsecs_t;

  /// Return current app-time in seconds.
  /// App-time is basically the total time that the engine has been actively
  /// running. (The 'App' here is a slight misnomer). It will stop progressing
  /// while the app is suspended and will never go backwards.
  auto GetAppTimeSeconds() -> double;

  /// Are we in the thread the main event loop is running on?
  /// Generally this is the thread that runs graphics and os event processing.
  auto InMainThread() -> bool;

  /// Log a boot-related message (only if core_config.lifecycle_log is true).
  void LifecycleLog(const char* msg, double offset_seconds = 0.0);

  /// Base path of build src dir so we can attempt to remove it from
  /// any source file paths we print.
  auto build_src_dir() const { return build_src_dir_; }

  // Subsystems.
  CorePython* const python;
  CorePlatform* const platform;

  // The following are misc values that should be migrated to applicable
  // subsystem classes.
  bool threads_paused{};
  bool workspaces_in_use{};
  bool replay_open{};
  std::vector<EventLoop*> pausable_event_loops;
  std::mutex v1_cloud_log_mutex;
  std::string v1_cloud_log;
  bool did_put_v1_cloud_log{};
  bool v1_cloud_log_full{};
  int master_server_source{};
  int session_count{};
  bool shutting_down{};
  bool have_incentivized_ad{false};
  bool should_pause{};
  bool reset_vr_orientation{};
  bool user_ran_commands{};
  std::string user_agent_string{"BA_USER_AGENT_UNSET (" BA_PLATFORM_STRING ")"};
  int return_value{};
  bool debug_timing{};
  std::thread::id main_thread_id{};

  bool vr_mode;
  std::mutex thread_name_map_mutex;
  std::unordered_map<std::thread::id, std::string> thread_name_map;

#if BA_DEBUG_BUILD
  std::mutex object_list_mutex;
  Object* object_list_first{};
  int object_count{};
#endif

 private:
  static void DoImport(const CoreConfig& config);
  void UpdateAppTime();
  explicit CoreFeatureSet(CoreConfig config);
  void PostInit();
  bool tried_importing_base_{};
  EventLoop* main_event_loop_{};
  CoreConfig core_config_;
  bool started_suicide_{};
  std::string build_src_dir_;
  microsecs_t app_time_microsecs_{};
  microsecs_t last_app_time_measure_microsecs_;
  std::mutex app_time_mutex_;
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_CORE_H_
