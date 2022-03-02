// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PLATFORM_WINDOWS_PLATFORM_WINDOWS_H_
#define BALLISTICA_PLATFORM_WINDOWS_PLATFORM_WINDOWS_H_
#if BA_OSTYPE_WINDOWS

#include <string>
#include <vector>

#include "ballistica/platform/platform.h"

namespace ballistica {

class PlatformWindows : public Platform {
 public:
  PlatformWindows();
  void SetupInterruptHandling() override;
  auto GetDeviceAccountUUIDPrefix() -> std::string override { return "w"; }
  auto GetPublicDeviceUUIDInputs() -> std::list<std::string> override;
  auto GenerateUUID() -> std::string override;
  auto GetDefaultConfigDir() -> std::string override;
  auto Remove(const char* path) -> int;
  auto Stat(const char* path, struct BA_STAT* buffer) -> int;
  auto Rename(const char* oldname, const char* newname) -> int;
  auto DoAbsPath(const std::string& path, std::string* outpath)
      -> bool override;
  auto FOpen(const char* path, const char* mode) -> FILE* override;
  auto GetErrnoString() -> std::string override;
  auto GetSocketErrorString() -> std::string override;
  auto GetSocketError() -> int override;
  void DoMakeDir(const std::string& dir, bool quiet) override;
  auto GetLocale() -> std::string override;
  auto DoGetDeviceName() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  void HandleLog(const std::string& msg) override;
  void SetupDataDirectory() override;
  void SetEnv(const std::string& name, const std::string& value) override;
  auto IsStdinATerminal() -> bool override;
  auto GetOSVersionString() -> std::string override;
  auto GetCWD() -> std::string override;
  void DoOpenURL(const std::string& url) override;
  void OpenFileExternally(const std::string& path) override;
  void OpenDirExternally(const std::string& path) override;
  void Unlink(const char* path) override;
  void CloseSocket(int socket) override;
  auto GetBroadcastAddrs() -> std::vector<uint32_t> override;
  auto SetSocketNonBlocking(int sd) -> bool override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;
  virtual auto ContainsPythonDist() -> bool;
  bool have_stdin_stdout_ = false;
};

}  // namespace ballistica

#endif  // BA_OSTYPE_WINDOWS
#endif  // BALLISTICA_PLATFORM_WINDOWS_PLATFORM_WINDOWS_H_
