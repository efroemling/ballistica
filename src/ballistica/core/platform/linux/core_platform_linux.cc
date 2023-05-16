// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_LINUX
#include "ballistica/core/platform/linux/core_platform_linux.h"

#include <stdlib.h>

#include <string>

namespace ballistica::core {

CorePlatformLinux::CorePlatformLinux() {}

std::string CorePlatformLinux::GenerateUUID() {
  std::string val;
  char buffer[100];
  FILE* fd_out = popen("cat /proc/sys/kernel/random/uuid", "r");
  if (fd_out) {
    int size = fread(buffer, 1, 99, fd_out);
    fclose(fd_out);
    if (size == 37) {
      buffer[size - 1] = 0;  // chop off trailing newline
      val = buffer;
    }
  }
  if (val == "") {
    throw Exception("kernel uuid not available");
  }
  return val;
}

auto CorePlatformLinux::GetDeviceUUIDInputs() -> std::list<std::string> {
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

bool CorePlatformLinux::DoHasTouchScreen() { return false; }

void CorePlatformLinux::OpenFileExternally(const std::string& path) {
  std::string cmd = std::string("xdg-open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    Log(LogLevel::kError, "Got return value " + std::to_string(result)
                              + " on xdg-open cmd '" + cmd + "'");
  }
}

void CorePlatformLinux::OpenDirExternally(const std::string& path) {
  std::string cmd = std::string("xdg-open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    Log(LogLevel::kError, "Got return value " + std::to_string(result)
                              + " on xdg-open cmd '" + cmd + "'");
  }
}

std::string CorePlatformLinux::GetPlatformName() { return "linux"; }

std::string CorePlatformLinux::GetSubplatformName() {
#if BA_TEST_BUILD
  return "test";
#else
  return "";
#endif
}

}  // namespace ballistica::core

#endif  // BA_OSTYPE_LINUX
