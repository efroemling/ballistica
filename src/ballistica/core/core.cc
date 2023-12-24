// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/core.h"

#include <cstring>
#include <utility>

#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::core {

CoreFeatureSet* g_core{};
BaseSoftInterface* g_base_soft{};

auto CoreFeatureSet::Import(const CoreConfig* config) -> CoreFeatureSet* {
  // In monolithic builds, we accept an explicit core-config the first time
  // we're imported. It is fully up to the caller to build the config.
  if (g_buildconfig.monolithic_build()) {
    if (config != nullptr) {
      if (g_core != nullptr) {
        FatalError(
            "CoreConfig can only be passed on the first CoreFeatureSet::Import "
            "call.");
      }
      if (g_core == nullptr) {
        DoImport(*config);
      }
    } else {
      // If no config is passed, use a default. If the user wants env vars
      // or anything else factored in, they should do so themselves in the
      // config they pass (CoreConfig::ForEnvVars(), etc.).
      if (g_core == nullptr) {
        DoImport({});
      }
    }
  } else {
    // In modular builds, we generate a CoreConfig *after* Python is spun
    // up, implicitly using Python's sys args and/or env vars when
    // applicable.
    if (config != nullptr) {
      FatalError("CoreConfig can't be explicitly passed in modular builds.");
    }
    if (g_core == nullptr) {
      bool can_do_args = CorePython::WasModularMainCalled();
      if (can_do_args) {
        // Wrangle Python's sys.argv into a standard C-style argc/argv so we
        // can pass to the same handler as the monolithic C route. Note that
        // a few of the values we parse here (--command, etc) have already
        // been handled at the Python layer, but we parse them here just the
        // same so that we have uniform records and invalid-value handling
        // between monolithic and modular.
        std::vector<std::string> argbuffer;
        std::vector<char*> argv = CorePython::FetchPythonArgs(&argbuffer);
        DoImport(CoreConfig::ForArgsAndEnvVars(static_cast<int>(argv.size()),
                                               argv.data()));
      } else {
        // Not using Python sys args but we still want to process env vars.
        DoImport(CoreConfig::ForEnvVars());
      }
    }
  }
  return g_core;
}

void CoreFeatureSet::DoImport(const CoreConfig& config) {
  millisecs_t start_millisecs = CorePlatform::GetCurrentMillisecs();

  assert(g_core == nullptr);
  g_core = new CoreFeatureSet(config);
  g_core->PostInit();

  // Slightly hacky: have to report our begin time after the fact since core
  // didn't exist before. Can at least add an offset to give an accurate
  // time though.
  auto seconds_since_actual_start =
      static_cast<double>(CorePlatform::GetCurrentMillisecs() - start_millisecs)
      / 1000.0;
  g_core->LifecycleLog("core import begin", -seconds_since_actual_start);
  g_core->LifecycleLog("core import end");
}

CoreFeatureSet::CoreFeatureSet(CoreConfig config)
    : main_thread_id_{std::this_thread::get_id()},
      python{new CorePython()},
      platform{CorePlatform::Create()},
      core_config_{std::move(config)},
      last_app_time_measure_microsecs_{CorePlatform::GetCurrentMicrosecs()},
      vr_mode_{config.vr_mode} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_core == nullptr);
}

void CoreFeatureSet::PostInit() {
  // Some of this stuff might access g_core so we run most of our init
  // *after* assigning our singleton to be safe.

  // Should migrate this to classic.
  set_legacy_user_agent_string(platform->GetLegacyUserAgentString());

  RunSanityChecks();

  build_src_dir_ = CalcBuildSrcDir();

  // On monolithic builds we need to bring up Python itself.
  if (g_buildconfig.monolithic_build()) {
    python->InitPython();
  }

  // Make sure we're running an acceptable Python version/etc.
  python->VerifyPythonEnvironment();

  // Grab whatever Python stuff we use.
  python->ImportPythonObjs();

  // Normally we wait until later to start pushing logs through to Python
  // (so that our log handling system is fully bootstrapped), but
  // technically we can push our log calls out to Python any time now since
  // we grabbed the logging calls above. Do so immediately here if asked.
  if (!core_config_.hold_early_logs) {
    python->EnablePythonLoggingCalls();
  }
}

auto CoreFeatureSet::core_config() const -> const CoreConfig& {
  // Try to make a bit of noise if we're accessed in modular builds before
  // baenv values are set, since in that case we won't yet have our final
  // core-config values. Though we want to keep this to a minimal printf so
  // we don't interfere with low-level stuff like FatalError handling that
  // might need core_config access at any time.
  if (!g_buildconfig.monolithic_build()) {
    if (!have_ba_env_vals()) {
      static bool did_warn = false;
      if (!did_warn) {
        did_warn = true;
        printf(
            "WARNING: accessing core_config() before baenv values have been "
            "applied to it.\n");
      }
    }
  }
  return core_config_;
}

void CoreFeatureSet::ApplyBaEnvConfig() {
  // Ask baenv for the config we should use.
  auto envcfg =
      python->objs().Get(core::CorePython::ObjID::kBaEnvGetConfigCall).Call();
  BA_PRECONDITION_FATAL(envcfg.Exists());

  assert(!have_ba_env_vals_);
  have_ba_env_vals_ = true;

  // Pull everything we want out of it.
  ba_env_config_dir_ = envcfg.GetAttr("config_dir").ValueAsString();
  ba_env_data_dir_ = envcfg.GetAttr("data_dir").ValueAsString();
  ba_env_app_python_dir_ =
      envcfg.GetAttr("app_python_dir").ValueAsOptionalString();
  ba_env_user_python_dir_ =
      envcfg.GetAttr("user_python_dir").ValueAsOptionalString();
  ba_env_site_python_dir_ =
      envcfg.GetAttr("site_python_dir").ValueAsOptionalString();

  // Consider app-python-dir to be 'custom' if baenv provided a value for it
  // AND that value differs from baenv's default.
  auto standard_app_python_dir =
      envcfg.GetAttr("standard_app_python_dir").ValueAsString();
  using_custom_app_python_dir_ =
      ba_env_app_python_dir_.has_value()
      && *ba_env_app_python_dir_ != standard_app_python_dir;

  // As a sanity check, die if the data dir we were given doesn't contain a
  // 'ba_data' dir.
  auto fullpath = ba_env_data_dir_ + BA_DIRSLASH + "ba_data";
  if (!platform->FilePathExists(fullpath)) {
    FatalError("ba_data directory not found at '" + fullpath + "'.");
  }
}

auto CoreFeatureSet::GetAppPythonDirectory() -> std::optional<std::string> {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_app_python_dir_;
}

auto CoreFeatureSet::GetUserPythonDirectory() -> std::optional<std::string> {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_user_python_dir_;
}

// Return the ballisticakit config dir. This does not vary across versions.
auto CoreFeatureSet::GetConfigDirectory() -> std::string {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_config_dir_;
}

auto CoreFeatureSet::GetDataDirectory() -> std::string {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_data_dir_;
}

auto CoreFeatureSet::GetSitePythonDirectory() -> std::optional<std::string> {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_site_python_dir_;
}

auto CoreFeatureSet::CalcBuildSrcDir() -> std::string {
  // Let's grab a string of the portion of __FILE__ before our project root.
  // We can use it to make error messages/etc. more pretty by stripping out
  // all but sub-project paths.
  const char* f = __FILE__;
  auto* f_end = strstr(f, "src" BA_DIRSLASH "ballistica" BA_DIRSLASH
                          "core" BA_DIRSLASH "core.cc");
  if (!f_end) {
    Log(LogLevel::kWarning, "Unable to calc build source dir from __FILE__.");
    return "";
  } else {
    return std::string(f).substr(0, f_end - f);
  }
}

void CoreFeatureSet::RunSanityChecks() {
  // Sanity check: make sure asserts are stripped out of release builds
  // (NDEBUG should do this).
#if !BA_DEBUG_BUILD
#ifndef NDEBUG
#error Expected NDEBUG to be defined for release builds.
#endif
  // If this kills the app, something's wrong.
  assert(false);
#endif  // !BA_DEBUG_BUILD

  // Test our static-type-name functionality. This code runs at compile time
  // and extracts human readable type names using __PRETTY_FUNCTION__ type
  // functionality. However, it is dependent on specific compiler output and
  // so could break easily if anything changes. Here we add some
  // compile-time checks to alert us if that happens.

  // Remember that results can vary per compiler; make sure we match any one
  // of the expected formats.
  static_assert(static_type_name_constexpr<decltype(g_core)>()
                    == "ballistica::core::CoreFeatureSet *"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "ballistica::core::CoreFeatureSet*"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "class ballistica::core::CoreFeatureSet*"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "CoreFeatureSet*"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "core::CoreFeatureSet*");
  Object::Ref<Runnable> testrunnable{};
  static_assert(
      static_type_name_constexpr<decltype(testrunnable)>()
          == "ballistica::Object::Ref<ballistica::Runnable>"
      || static_type_name_constexpr<decltype(testrunnable)>()
             == "class ballistica::Object::Ref<class ballistica::Runnable>"
      || static_type_name_constexpr<decltype(testrunnable)>()
             == "Object::Ref<Runnable>");

  // If anything above breaks, enable this code to debug/fix it. This will
  // print a calculated type name as well as the full string it was parsed
  // from. Use this to adjust the filtering as necessary so the resulting
  // type name matches what is expected.
  if (explicit_bool(false)) {
    Log(LogLevel::kError, "static_type_name check; name is '"
                              + static_type_name<decltype(g_core)>()
                              + "' debug_full is '"
                              + static_type_name<decltype(g_core)>(true) + "'");
    Log(LogLevel::kError,
        "static_type_name check; name is '"
            + static_type_name<decltype(testrunnable)>() + "' debug_full is '"
            + static_type_name<decltype(testrunnable)>(true) + "'");
  }

  if (vr_mode_ && !g_buildconfig.vr_build()) {
    FatalError("vr_mode enabled in core-config but we are not a vr build.");
  }
}

auto CoreFeatureSet::SoftImportBase() -> BaseSoftInterface* {
  if (!tried_importing_base_) {
    python->SoftImportBase();
    // Important to set this *AFTER*. Otherwise imports can fail if there is
    // already one in progress.
    tried_importing_base_ = true;
  }
  return g_base_soft;
}

void CoreFeatureSet::LifecycleLog(const char* msg, double offset_seconds) {
  if (!core_config_.lifecycle_log) {
    return;
  }
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "LIFE: %s @ %.3fs.", msg,
           g_core->GetAppTimeSeconds() + offset_seconds);
  Log(LogLevel::kInfo, buffer);
}

auto CoreFeatureSet::HeadlessMode() -> bool {
  // This is currently a hard-coded value but could theoretically change
  // later if we support running in headless mode from a gui build/etc.
  return g_buildconfig.headless_build();
}

// auto CoreFeatureSet::vr_mode() -> bool { return core_config_.vr_mode; }

static void WaitThenDie(millisecs_t wait, const std::string& action) {
  CorePlatform::SleepMillisecs(wait);
  FatalError("Timed out waiting for " + action + ".");
}

auto CoreFeatureSet::GetAppTimeMillisecs() -> millisecs_t {
  UpdateAppTime();
  return app_time_microsecs_ / 1000;
}

auto CoreFeatureSet::GetAppTimeMicrosecs() -> microsecs_t {
  UpdateAppTime();
  return app_time_microsecs_;
}

auto CoreFeatureSet::GetAppTimeSeconds() -> double {
  UpdateAppTime();
  return static_cast<double>(app_time_microsecs_) / 1000000;
}

void CoreFeatureSet::UpdateAppTime() {
  microsecs_t t = CorePlatform::GetCurrentMicrosecs();

  // If we're at a different time than our last query, do our funky math.
  if (t != last_app_time_measure_microsecs_) {
    std::scoped_lock lock(app_time_mutex_);
    microsecs_t passed = t - last_app_time_measure_microsecs_;

    // The time calls we're using are supposed to be monotonic, but I've
    // seen 'passed' equal -1 even when it is using
    // std::chrono::steady_clock. Let's do our own filtering here to make
    // 100% sure we don't go backwards.
    if (passed < 0) {
      passed = 0;
    } else {
      // Very large times-passed probably means we went to sleep or
      // something; clamp to a reasonable value.
      if (passed > 250000) {
        passed = 250000;
      }
    }
    app_time_microsecs_ += passed;
    last_app_time_measure_microsecs_ = t;
  }
}

// void CoreFeatureSet::UpdateMainThreadID() {
//   auto current_id = std::this_thread::get_id();

//   // This gets called a lot and it may happen before we are spun up, so just
//   // ignore it in that case.
//   main_thread_id = current_id;
//   main_event_loop_->set_thread_id(current_id);
// }

void CoreFeatureSet::StartSuicideTimer(const std::string& action,
                                       millisecs_t delay) {
  if (!started_suicide_) {
    new std::thread(WaitThenDie, delay, action);
    started_suicide_ = true;
  }
}

void CoreFeatureSet::RegisterThread(const std::string& name) {
  {
    std::scoped_lock lock(thread_info_map_mutex_);

    // Should be registering each thread just once.
    assert(thread_info_map_.find(std::this_thread::get_id())
           == thread_info_map_.end());
    thread_info_map_[std::this_thread::get_id()] = name;
  }

  // Also set the name at the OS leve when possible. Prepend 'ballistica'
  // since there's generally lots of other random threads in the mix.
  //
  // Note that we currently don't do this for our main thread because (on
  // Linux at least) that changes the process name we see in top/etc. On
  // other platforms we could reconsider, but its generally clear what the
  // main thread is anyway in most scenarios.
  if (!InMainThread()) {
    g_core->platform->SetCurrentThreadName("ballistica " + name);
  }
}

void CoreFeatureSet::UnregisterThread() {
  std::scoped_lock lock(thread_info_map_mutex_);
  auto i = thread_info_map_.find(std::this_thread::get_id());
  assert(i != thread_info_map_.end());
  if (i != thread_info_map_.end()) {
    thread_info_map_.erase(i);
  }
}

auto CoreFeatureSet::CurrentThreadName() -> std::string {
  if (g_core == nullptr) {
    return "unknown(not-yet-inited)";
  }
  {
    std::scoped_lock lock(g_core->thread_info_map_mutex_);
    auto i = g_core->thread_info_map_.find(std::this_thread::get_id());
    if (i != g_core->thread_info_map_.end()) {
      return i->second;
    }
  }

  // Ask pthread for the thread name if we don't have one.
  // FIXME - move this to platform.
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS || BA_OSTYPE_LINUX
  std::string name = "unknown (sys-name=";
  char buffer[256];
  int result = pthread_getname_np(pthread_self(), buffer, sizeof(buffer));
  if (result == 0) {
    name += std::string("\"") + buffer + "\")";
  } else {
    name += "<error " + std::to_string(result) + ">";
  }
  return name;
#else
  return "unknown";
#endif
}

}  // namespace ballistica::core
