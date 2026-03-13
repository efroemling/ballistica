// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_PLATFORM_LINUX_APP_PLATFORM_LINUX_H_
#define BALLISTICA_BASE_APP_PLATFORM_LINUX_APP_PLATFORM_LINUX_H_
#if BA_PLATFORM_LINUX

#include <string>

#include "ballistica/base/app_platform/app_platform.h"

namespace ballistica::base {

class AppPlatformLinux : public AppPlatform {
 public:
  AppPlatformLinux();
  void DoOpenURL(const std::string& url) override;
  auto SupportsOpenDirExternally() -> bool override;
  void OpenDirExternally(const std::string& path) override;
  void OpenFileExternally(const std::string& path) override;
};

}  // namespace ballistica::base

#endif  // BA_PLATFORM_LINUX
#endif  // BALLISTICA_BASE_APP_PLATFORM_LINUX_APP_PLATFORM_LINUX_H_
