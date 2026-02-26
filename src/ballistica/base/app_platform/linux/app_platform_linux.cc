// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_LINUX
#include "ballistica/base/app_platform/linux/app_platform_linux.h"

#include <stdlib.h>

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::base {

AppPlatformLinux::AppPlatformLinux() = default;

void AppPlatformLinux::DoOpenURL(const std::string& url) {
  // UPDATE - just relying on default Python webbrowser path now.
  // (technically could kill this override).
  AppPlatform::DoOpenURL(url);
}

auto AppPlatformLinux::SupportsOpenDirExternally() -> bool { return true; }

void AppPlatformLinux::OpenDirExternally(const std::string& path) {
  std::string cmd = std::string("xdg-open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Got return value " + std::to_string(result)
                             + " on xdg-open cmd '" + cmd + "'");
  }
}

void AppPlatformLinux::OpenFileExternally(const std::string& path) {
  std::string cmd = std::string("xdg-open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Got return value " + std::to_string(result)
                             + " on xdg-open cmd '" + cmd + "'");
  }
}

}  // namespace ballistica::base

#endif  // BA_PLATFORM_LINUX
