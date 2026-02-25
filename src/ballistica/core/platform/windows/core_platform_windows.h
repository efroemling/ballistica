// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_WINDOWS_CORE_PLATFORM_WINDOWS_H_
#define BALLISTICA_CORE_PLATFORM_WINDOWS_CORE_PLATFORM_WINDOWS_H_
#if BA_PLATFORM_WINDOWS

#include <cstdio>
#include <list>
#include <mutex>
#include <string>
#include <string_view>
#include <vector>

#include "ballistica/core/platform/core_platform.h"

namespace ballistica::core {

class WinStackTrace;

class CorePlatformWindows : public CorePlatform {
 public:
  CorePlatformWindows();

  static auto UTF8Encode(std::wstring_view str) -> std::string;
  static auto UTF8Decode(std::string_view str) -> std::wstring;

  auto GetNativeStackTrace() -> NativeStackTrace* override;
  auto GetDeviceV1AccountUUIDPrefix() -> std::string override { return "w"; }
  auto GetDeviceUUIDInputs() -> std::list<std::string> override;
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
  auto GetLocaleTag() -> std::string override;
  auto DoGetDeviceName() -> std::string override;
  auto DoGetDeviceDescription() -> std::string override;
  auto DoHasTouchScreen() -> bool override;
  void EmitPlatformLog(std::string_view name, LogLevel level,
                       std::string_view msg) override;
  void SetEnv(const std::string& name, const std::string& value) override;
  auto GetEnv(const std::string& name) -> std::optional<std::string> override;
  auto GetIsStdinATerminal() -> bool override;
  auto GetOSVersionString() -> std::string override;
  auto GetCWD() -> std::string override;
  void Unlink(const char* path) override;
  void CloseSocket(int socket) override;
  auto GetBroadcastAddrs() -> std::vector<uint32_t> override;
  auto SetSocketNonBlocking(int sd) -> bool override;
  auto GetLegacyPlatformName() -> std::string override;
  auto GetLegacySubplatformName() -> std::string override;

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

  bool have_stdin_stdout_ = false;

  auto FormatWinStackTraceForDisplay(WinStackTrace* stack_trace) -> std::string;

 private:
  std::mutex win_stack_mutex_;
  bool win_sym_inited_{};
  void* win_sym_process_{};
};

}  // namespace ballistica::core

#endif  // BA_PLATFORM_WINDOWS
#endif  // BALLISTICA_CORE_PLATFORM_WINDOWS_CORE_PLATFORM_WINDOWS_H_
