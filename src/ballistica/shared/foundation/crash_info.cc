// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/crash_info.h"

#include <chrono>
#include <cstring>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica {

using core::g_core;

CrashInfo g_crash_info{};

namespace {

/// Copy into a fixed buffer, always nul-terminated and never
/// overrunning. Truncation is fine here; a clipped renderer string is
/// far better than none.
void CopyFixed(char* dst, size_t dstsize, const char* src) {
  if (dstsize == 0) {
    return;
  }
  if (src == nullptr) {
    dst[0] = '\0';
    return;
  }
  std::strncpy(dst, src, dstsize - 1);
  dst[dstsize - 1] = '\0';
}

auto EpochSeconds() -> uint64_t {
  auto now = std::chrono::system_clock::now().time_since_epoch();
  return static_cast<uint64_t>(
      std::chrono::duration_cast<std::chrono::seconds>(now).count());
}

}  // namespace

void CrashInfoInit() {
  g_crash_info.format_version = kCrashInfoFormatVersion;
  g_crash_info.build_number = kEngineBuildNumber;
  g_crash_info.launch_time = EpochSeconds();

  CopyFixed(g_crash_info.version, sizeof(g_crash_info.version), kEngineVersion);
  CopyFixed(g_crash_info.platform, sizeof(g_crash_info.platform), BA_PLATFORM);
  CopyFixed(g_crash_info.arch, sizeof(g_crash_info.arch), BA_ARCH);
  CopyFixed(g_crash_info.variant, sizeof(g_crash_info.variant), BA_VARIANT);

  // Matches the fatal-error payload's handling; see the note there on
  // why this macro cannot be referenced at all in public builds.
  g_crash_info.devbuild = false;
  g_crash_info.debugbuild = static_cast<bool>(BA_DEBUG_BUILD);
}

void CrashInfoSetRenderer(const std::string& val) {
  CopyFixed(g_crash_info.renderer, sizeof(g_crash_info.renderer), val.c_str());
}

void CrashInfoSetOSVersion(const std::string& val) {
  // Platforms that can't tell report "unknown"; store that as empty so
  // readers have one absent-value check rather than two.
  CopyFixed(g_crash_info.os_version, sizeof(g_crash_info.os_version),
            val == "unknown" ? "" : val.c_str());
}

void CrashInfoUpdateRuntime(uint32_t app_state) {
  g_crash_info.app_state = app_state;
  g_crash_info.frame_number += 1;

  // Mirror the modded-build signals rather than having the handler
  // reach through g_core for them: at fault time that pointer may be
  // null or garbage, and dereferencing it would crash us inside the
  // handler.
  if (g_core != nullptr) {
    g_crash_info.core_alive = true;
    g_crash_info.rancmds = g_core->user_ran_commands;
    g_crash_info.workspaces = g_core->workspaces_in_use;
    g_crash_info.custompy = g_core->using_custom_app_python_dir();
    g_crash_info.userpy = g_core->user_python_present;
    g_crash_info.modded = g_crash_info.rancmds || g_crash_info.workspaces
                          || g_crash_info.custompy || g_crash_info.userpy;
  } else {
    g_crash_info.core_alive = false;
  }
}

}  // namespace ballistica
