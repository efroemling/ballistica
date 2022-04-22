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
  auto GetDeviceAccountUUIDPrefix() -> std::string override { return "l"; }
  auto GenerateUUID() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  auto DoOpenURL(const std::string& url) -> void override;
  auto OpenFileExternally(const std::string& path) -> void override;
  auto OpenDirExternally(const std::string& path) -> void override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
};

}  // namespace ballistica

#endif  // BA_OSTYPE_LINUX
#endif  // BALLISTICA_PLATFORM_LINUX_PLATFORM_LINUX_H_
