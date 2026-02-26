// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_LINUX
#include "ballistica/core/platform/linux/platform_linux.h"

#include <sys/utsname.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <list>
#include <string>
#include <vector>

#if BA_ENABLE_OS_FONT_RENDERING
#include "ballistica/core/platform/support/platform_pango.h"
#endif

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/exception.h"

namespace ballistica::core {

PlatformLinux::PlatformLinux() {}

auto PlatformLinux::DoGetDeviceDescription() -> std::string {
  // Let's look for something pretty like "Ubuntu 20.04", etc.
  FILE* file = fopen("/etc/os-release", "r");
  std::optional<std::string> out;
  if (file != NULL) {
    char line[256];  // Adjust the buffer size as needed

    while (fgets(line, sizeof(line), file)) {
      if (strstr(line, "PRETTY_NAME=") != nullptr) {
        // Extract the distribution name and version
        char* start = strchr(line, '"');
        char* end = strrchr(line, '"');
        if (start != nullptr && end != nullptr) {
          *end = '\0';  // Remove the trailing quote
          out = start + 1;
        }
        break;
      }
    }
    fclose(file);
  }
  if (out.has_value()) {
    return *out;
  }
  return Platform::GetDeviceDescription();
}

auto PlatformLinux::GetOSVersionString() -> std::string {
  std::optional<std::string> out;
  struct utsname uts;
  if (uname(&uts) == 0) {
    out = uts.release;

    // Try to parse 3 version numbers.
    unsigned int major, minor, bugfix;
    if (sscanf(uts.release, "%u.%u.%u", &major, &minor, &bugfix) == 3) {
      char buf[128];
      snprintf(buf, sizeof(buf), "%.u.%u.%u", major, minor, bugfix);
      out = buf;
    }
  }
  if (out.has_value()) {
    return *out;
  }
  return Platform::GetOSVersionString();
}

auto PlatformLinux::GetDeviceUUIDInputs() -> std::list<std::string> {
  std::list<std::string> out;

  // For now let's just go with machine-id.
  // Perhaps can add kernel version or something later.
  char buffer[100];
  if (FILE* infile = fopen("/etc/machine-id", "r")) {
    int size = fread(buffer, 1, 99, infile);
    fclose(infile);
    if (size < 10) {
      throw Exception("unexpected machine-id value");
    }
    buffer[size] = 0;
    out.push_back(buffer);
  } else {
    throw Exception("/etc/machine-id not accessible");
  }
  return out;
};

bool PlatformLinux::DoHasTouchScreen() { return false; }

std::string PlatformLinux::GetLegacyPlatformName() { return "linux"; }

std::string PlatformLinux::GetLegacySubplatformName() {
#if BA_VARIANT_TEST_BUILD
  return "test";
#else
  return "";
#endif
}

#if BA_ENABLE_OS_FONT_RENDERING

void PlatformLinux::GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                          float* width) {
  PangoGetTextBoundsAndWidth_(text, r, width);
}

auto PlatformLinux::CreateTextTexture(int width, int height,
                                      const std::vector<std::string>& strings,
                                      const std::vector<float>& positions,
                                      const std::vector<float>& widths,
                                      float scale) -> void* {
  return PangoCreateTextTexture_(width, height, strings, positions, widths,
                                 scale);
}

auto PlatformLinux::GetTextTextureData(void* tex) -> uint8_t* {
  return PangoGetTextTextureData_(tex);
}

void PlatformLinux::FreeTextTexture(void* tex) { PangoFreeTextTexture_(tex); }

#endif  // BA_ENABLE_OS_FONT_RENDERING

}  // namespace ballistica::core

#endif  // BA_PLATFORM_LINUX
