// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_LINUX
#include "ballistica/platform/linux/platform_linux.h"

#include <stdlib.h>

#include <string>

namespace ballistica {

PlatformLinux::PlatformLinux() {}

std::string PlatformLinux::GenerateUUID() {
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

void PlatformLinux::DoOpenURL(const std::string& url) {
  // hmmm is there a more universal option than this?...
  int result = system((std::string("xdg-open \"") + url + "\"").c_str());
  if (result != 0) {
    ScreenMessage("error on xdg-open");
  }
}

void PlatformLinux::OpenFileExternally(const std::string& path) {
  std::string cmd = std::string("xdg-open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    Log(LogLevel::kError, "Got return value " + std::to_string(result)
                              + " on xdg-open cmd '" + cmd + "'");
  }
}

void PlatformLinux::OpenDirExternally(const std::string& path) {
  std::string cmd = std::string("xdg-open \"") + path + "\"";
  int result = system(cmd.c_str());
  if (result != 0) {
    Log(LogLevel::kError, "Got return value " + std::to_string(result)
                              + " on xdg-open cmd '" + cmd + "'");
  }
}

std::string PlatformLinux::GetPlatformName() { return "linux"; }

std::string PlatformLinux::GetSubplatformName() {
#if BA_TEST_BUILD
  return "test";
#else
  return "";
#endif
}

}  // namespace ballistica

#endif  // BA_OSTYPE_LINUX
