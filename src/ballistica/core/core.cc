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
  // Only accept a config in monolithic builds if this is the first import.
  if (config != nullptr) {
    if (!g_buildconfig.monolithic_build()) {
      FatalError("CoreConfig can only be passed in monolithic builds.");
    }
    if (g_core != nullptr) {
      FatalError("CoreConfig can only be passed on the first import call.");
    }

    if (g_core == nullptr) {
      DoImport(*config);
    }
  } else {
    if (g_core == nullptr) {
      DoImport({});
    }
  }
  return g_core;
}

void CoreFeatureSet::DoImport(const CoreConfig& config) {
  millisecs_t start_millisecs = CorePlatform::GetCurrentMillisecs();

  assert(g_core == nullptr);
  g_core = new CoreFeatureSet(config);
  g_core->PostInit();

  // Slightly hacky: have to report our begin time after the fact since
  // core didn't exist before. Can at least add an offset to give an accurate
  // time though.
  auto seconds_since_actual_start =
      static_cast<double>(CorePlatform::GetCurrentMillisecs() - start_millisecs)
      / 1000.0;
  g_core->BootLog("core import begin", -seconds_since_actual_start);
  g_core->BootLog("core import end");
}

CoreFeatureSet::CoreFeatureSet(CoreConfig config)
    : main_thread_id{std::this_thread::get_id()},
      python{new CorePython()},
      platform{CorePlatform::Create()},
      core_config_{std::move(config)},
      last_app_time_measure_microsecs_{CorePlatform::GetCurrentMicrosecs()},
      vr_mode{config.vr_mode} {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_core == nullptr);

  // Test our static-type-name functionality.
  // This code runs at compile time and extracts human readable type names using
  // __PRETTY_FUNCTION__ type functionality. However, it is dependent on
  // specific compiler output and so could break easily if anything changes.
  // Here we add some compile-time checks to alert us if that happens.

  // Remember that results can vary per compiler; make sure we match
  // any one of the expected formats.
  static_assert(static_type_name_constexpr<decltype(g_core)>()
                    == "ballistica::core::CoreFeatureSet *"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "ballistica::core::CoreFeatureSet*"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "class ballistica::core::CoreFeatureSet*"
                || static_type_name_constexpr<decltype(g_core)>()
                       == "CoreFeatureSet*");
  Object::Ref<Runnable> testrunnable{};
  static_assert(
      static_type_name_constexpr<decltype(testrunnable)>()
          == "ballistica::Object::Ref<ballistica::Runnable>"
      || static_type_name_constexpr<decltype(testrunnable)>()
             == "class ballistica::Object::Ref<class ballistica::Runnable>"
      || static_type_name_constexpr<decltype(testrunnable)>()
             == "Object::Ref<Runnable>");

  // int testint{};
  // static_assert(static_type_name_constexpr<decltype(testint)>() == "int");

  // If anything above breaks, enable this code to debug/fix it.
  // This will print a calculated type name as well as the full string
  // it was parsed from. Use this to adjust the filtering as necessary so
  // the resulting type name matches what is expected.
  if (explicit_bool(false)) {
    Log(LogLevel::kError,
        "static_type_name check; name is '"
            + static_type_name<decltype(testrunnable)>() + "' debug_full is '"
            + static_type_name<decltype(testrunnable)>(true) + "'");
  }
}

void CoreFeatureSet::PostInit() {
  // Some of this stuff accesses g_core so we need to run it *after*
  // assigning our singleton.

  // Enable extra timing logs via env var.
  const char* debug_timing_env = getenv("BA_DEBUG_TIMING");
  if (debug_timing_env != nullptr && !strcmp(debug_timing_env, "1")) {
    debug_timing = true;
  }

  if (vr_mode && !g_buildconfig.vr_build()) {
    FatalError("vr_mode enabled in core-config but we are not a vr build.");
  }

  // Let's grab a string of the portion of __FILE__ before our project root.
  // We can use it to make error messages/etc. more pretty by stripping out
  // all but sub-project paths.
  const char* f = __FILE__;
  auto* f_end = strstr(
      f, "src" BA_DIRSLASH "ballistica" BA_DIRSLASH "app" BA_DIRSLASH "app.cc");
  if (!f) {
    Log(LogLevel::kWarning, "Unable to calc project dir from __FILE__.");
  } else {
    build_src_dir_ = std::string(f).substr(0, f_end - f);
  }

  // Note: this checks g_core->main_thread_id which is why it must run in
  // PostInit and not our constructor.
  main_event_loop_ = new EventLoop(EventLoopID::kMain, ThreadSource::kWrapMain);

  // On monolithic builds we need to bring up Python itself.
  if (g_buildconfig.monolithic_build()) {
    python->InitPython();
  }

  // Make sure we're running an acceptable Python version/etc.
  python->VerifyPythonEnvironment();

  // Grab whatever Python stuff we use.
  python->ImportPythonObjs();

  // FIXME: MOVE THIS TO A RUN_APP_TO_COMPLETION() SORT OF PLACE.
  //  For now it does the right thing here since all we have is monolithic
  //  builds but this will need to account for more situations later.
  python->ReleaseMainThreadGIL();
}

auto CoreFeatureSet::SoftImportBase() -> BaseSoftInterface* {
  if (!g_base_soft) {
    python->SoftImportBase();
  }
  return g_base_soft;
}

void CoreFeatureSet::BootLog(const char* msg, double offset_seconds) {
  if (!core_config_.log_boot_process) {
    return;
  }
  char buffer[128];
  // It's not safe to use Log until
  snprintf(buffer, sizeof(buffer), "BOOT: %s @ %.3fs.", msg,
           g_core->GetAppTimeSeconds() + offset_seconds);
  Log(LogLevel::kInfo, buffer);
}

auto CoreFeatureSet::HeadlessMode() -> bool {
  // This is currently a hard-coded value but could theoretically change
  // later if we support running in headless mode from a gui build/etc.
  return g_buildconfig.headless_build();
}

auto CoreFeatureSet::IsVRMode() -> bool { return core_config_.vr_mode; }

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

    // The time calls we're using are supposed to be monotonic, but I've seen
    // 'passed' equal -1 even when it is using std::chrono::steady_clock. Let's
    // do our own filtering here to make 100% sure we don't go backwards.
    if (passed < 0) {
      passed = 0;
    } else {
      // Very large times-passed probably means we went to sleep or something;
      // clamp to a reasonable value.
      if (passed > 250000) {
        passed = 250000;
      }
    }
    app_time_microsecs_ += passed;
    last_app_time_measure_microsecs_ = t;
  }
}

void CoreFeatureSet::UpdateMainThreadID() {
  auto current_id = std::this_thread::get_id();

  // This gets called a lot and it may happen before we are spun up,
  // so just ignore it in that case..
  main_thread_id = current_id;
  main_event_loop_->set_thread_id(current_id);
}

void CoreFeatureSet::StartSuicideTimer(const std::string& action,
                                       millisecs_t delay) {
  if (!started_suicide_) {
    new std::thread(WaitThenDie, delay, action);
    started_suicide_ = true;
  }
}

auto CoreFeatureSet::InMainThread() -> bool {
  if (main_event_loop_) {
    return main_event_loop_->ThreadIsCurrent();
  }
  return false;
}

}  // namespace ballistica::core
