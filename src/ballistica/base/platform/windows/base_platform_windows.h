// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_WINDOWS_BASE_PLATFORM_WINDOWS_H_
#define BALLISTICA_BASE_PLATFORM_WINDOWS_BASE_PLATFORM_WINDOWS_H_
#if BA_PLATFORM_WINDOWS

#include <string>
#include <vector>

#include "ballistica/base/platform/base_platform.h"

namespace ballistica::base {

class BasePlatformWindows : public BasePlatform {
 public:
  BasePlatformWindows();
  void DoOpenURL(const std::string& url) override;
  void SetupInterruptHandling() override;
  auto SupportsOpenDirExternally() -> bool override;
  void OpenDirExternally(const std::string& path) override;
  void OpenFileExternally(const std::string& path) override;
};

}  // namespace ballistica::base

#endif  // BA_PLATFORM_WINDOWS
#endif  // BALLISTICA_BASE_PLATFORM_WINDOWS_BASE_PLATFORM_WINDOWS_H_
