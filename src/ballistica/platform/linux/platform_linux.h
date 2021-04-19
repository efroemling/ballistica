// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PLATFORM_LINUX_PLATFORM_LINUX_H_
#define BALLISTICA_PLATFORM_LINUX_PLATFORM_LINUX_H_
#if BA_OSTYPE_LINUX

#include <string>

#include "ballistica/platform/platform.h"

namespace ballistica {

class PlatformLinux : public Platform {
 public:
  PlatformLinux();
  std::string GetDeviceUUIDPrefix() override { return "l"; }
  std::string GenerateUUID() override;
  bool DoHasTouchScreen() override;
  void DoOpenURL(const std::string& url) override;
  void OpenFileExternally(const std::string& path) override;
  void OpenDirExternally(const std::string& path) override;
  std::string GetPlatformName() override;
  std::string GetSubplatformName() override;
};

}  // namespace ballistica

#endif  // BA_OSTYPE_LINUX
#endif  // BALLISTICA_PLATFORM_LINUX_PLATFORM_LINUX_H_
