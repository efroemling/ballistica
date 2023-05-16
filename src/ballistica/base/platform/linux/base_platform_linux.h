// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PLATFORM_LINUX_BASE_PLATFORM_LINUX_H_
#define BALLISTICA_BASE_PLATFORM_LINUX_BASE_PLATFORM_LINUX_H_
#if BA_OSTYPE_LINUX

#include <string>

#include "ballistica/base/platform/base_platform.h"

namespace ballistica::base {

class BasePlatformLinux : public BasePlatform {
 public:
  BasePlatformLinux();
  void DoOpenURL(const std::string& url) override;
};

}  // namespace ballistica::base

#endif  // BA_OSTYPE_LINUX
#endif  // BALLISTICA_BASE_PLATFORM_LINUX_BASE_PLATFORM_LINUX_H_
