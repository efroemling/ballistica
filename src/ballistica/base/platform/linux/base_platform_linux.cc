// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_LINUX
#include "ballistica/base/platform/linux/base_platform_linux.h"

#include <stdlib.h>

#include <string>

namespace ballistica::base {

BasePlatformLinux::BasePlatformLinux() = default;

void BasePlatformLinux::DoOpenURL(const std::string& url) {
  // UPDATE - just relying on default Python webbrowser path now.
  // (technically could kill this override).
  BasePlatform::DoOpenURL(url);
}

}  // namespace ballistica::base

#endif  // BA_OSTYPE_LINUX
