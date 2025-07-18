// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_LINUX_CORE_PLATFORM_LINUX_H_
#define BALLISTICA_CORE_PLATFORM_LINUX_CORE_PLATFORM_LINUX_H_
#if BA_PLATFORM_LINUX

#include <list>
#include <string>

#include "ballistica/core/platform/core_platform.h"

namespace ballistica::core {

class CorePlatformLinux : public CorePlatform {
 public:
  CorePlatformLinux();
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override { return "l"; }
  auto DoHasTouchScreen() -> bool override;
  auto GetLegacyPlatformName() -> std::string override;
  auto GetLegacySubplatformName() -> std::string override;
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
  auto DoGetDeviceDescription() -> std::string override;
  auto GetOSVersionString() -> std::string override;
};

}  // namespace ballistica::core

#endif  // BA_PLATFORM_LINUX
#endif  // BALLISTICA_CORE_PLATFORM_LINUX_CORE_PLATFORM_LINUX_H_
