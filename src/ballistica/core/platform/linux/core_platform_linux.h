// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_LINUX_CORE_PLATFORM_LINUX_H_
#define BALLISTICA_CORE_PLATFORM_LINUX_CORE_PLATFORM_LINUX_H_
#if BA_OSTYPE_LINUX

#include <string>

#include "ballistica/core/platform/core_platform.h"

namespace ballistica::core {

class CorePlatformLinux : public CorePlatform {
 public:
  CorePlatformLinux();
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override { return "l"; }
  auto GenerateUUID() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
  auto DoGetDeviceDescription() -> std::string override;
  auto GetOSVersionString() -> std::string override;
};

}  // namespace ballistica::core

#endif  // BA_OSTYPE_LINUX
#endif  // BALLISTICA_CORE_PLATFORM_LINUX_CORE_PLATFORM_LINUX_H_
