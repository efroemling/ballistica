// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_WINDOWS_CORE_PLATFORM_WINDOWS_H_
#define BALLISTICA_CORE_PLATFORM_WINDOWS_CORE_PLATFORM_WINDOWS_H_
#if BA_OSTYPE_WINDOWS

#include <mutex>
#include <string>
#include <vector>

#include "ballistica/core/platform/core_platform.h"

namespace ballistica::core {

class WinStackTrace;

class CorePlatformWindows : public CorePlatform {
 public:
  CorePlatformWindows();

  static auto UTF8Encode(const std::wstring& wstr) -> std::string;
  static auto UTF8Decode(const std::string& str) -> std::wstring;

  auto GetNativeStackTrace() -> NativeStackTrace* override;
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override { return "w"; }
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
  auto GenerateUUID() -> std::string override;
  auto DoGetConfigDirectoryMonolithicDefault()
      -> std::optional<std::string> override;
  auto DoGetDataDirectoryMonolithicDefault() -> std::string override;
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
  auto DoGetDeviceDescription() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  void EmitPlatformLog(const std::string& name, LogLevel level,
                       const std::string& msg) override;
  void SetEnv(const std::string& name, const std::string& value) override;
  auto GetEnv(const std::string& name) -> std::optional<std::string> override;
  auto GetIsStdinATerminal() -> bool override;
  auto GetOSVersionString() -> std::string override;
  auto GetCWD() -> std::string override;
  void Unlink(const char* path) override;
  void CloseSocket(int socket) override;
  auto GetBroadcastAddrs() -> std::vector<uint32_t> override;
  auto SetSocketNonBlocking(int sd) -> bool override;
  auto GetPlatformName() -> std::string override;
  auto GetSubplatformName() -> std::string override;
  bool have_stdin_stdout_ = false;

  auto FormatWinStackTraceForDisplay(WinStackTrace* stack_trace) -> std::string;

 private:
  std::mutex win_stack_mutex_;
  bool win_sym_inited_{};
  void* win_sym_process_{};
};

}  // namespace ballistica::core

#endif  // BA_OSTYPE_WINDOWS
#endif  // BALLISTICA_CORE_PLATFORM_WINDOWS_CORE_PLATFORM_WINDOWS_H_
