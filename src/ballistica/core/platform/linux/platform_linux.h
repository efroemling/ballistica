// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_LINUX_PLATFORM_LINUX_H_
#define BALLISTICA_CORE_PLATFORM_LINUX_PLATFORM_LINUX_H_
#if BA_PLATFORM_LINUX

#include <list>
#include <string>
#include <vector>

#include "ballistica/core/platform/platform.h"

namespace ballistica::core {

class PlatformLinux : public Platform {
 public:
  PlatformLinux();
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override { return "l"; }
  auto DoHasTouchScreen() -> bool override;
  auto GetLegacyPlatformName() -> std::string override;
  auto GetLegacySubplatformName() -> std::string override;
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
  auto DoGetDeviceDescription() -> std::string override;
  auto GetOSVersionString() -> std::string override;

#if BA_ENABLE_OS_FONT_RENDERING
  void GetTextBoundsAndWidth(const std::string& text, Rect* r,
                             float* width) override;
  void FreeTextTexture(void* tex) override;
  auto CreateTextTexture(int width, int height,
                         const std::vector<std::string>& strings,
                         const std::vector<float>& positions,
                         const std::vector<float>& widths, float scale)
      -> void* override;
  auto GetTextTextureData(void* tex) -> uint8_t* override;
#endif
};

}  // namespace ballistica::core

#endif  // BA_PLATFORM_LINUX
#endif  // BALLISTICA_CORE_PLATFORM_LINUX_PLATFORM_LINUX_H_
