// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_PLATFORM_WINDOWS_APP_PLATFORM_WINDOWS_H_
#define BALLISTICA_BASE_APP_PLATFORM_WINDOWS_APP_PLATFORM_WINDOWS_H_
#if BA_PLATFORM_WINDOWS

#include <string>
#include <vector>

#include "ballistica/base/app_platform/app_platform.h"

namespace ballistica::base {

class AppPlatformWindows : public AppPlatform {
 public:
  AppPlatformWindows();
  void DoOpenURL(const std::string& url) override;
  void SetupInterruptHandling() override;
  auto SupportsOpenDirExternally() -> bool override;
  void OpenDirExternally(const std::string& path) override;
  void OpenFileExternally(const std::string& path) override;
};

}  // namespace ballistica::base

#endif  // BA_PLATFORM_WINDOWS
#endif  // BALLISTICA_BASE_APP_PLATFORM_WINDOWS_APP_PLATFORM_WINDOWS_H_
