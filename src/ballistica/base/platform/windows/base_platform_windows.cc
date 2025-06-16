// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_WINDOWS
#include "ballistica/base/platform/windows/base_platform_windows.h"

#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <rpc.h>
#include <shellapi.h>
#include <shlobj_core.h>
#include <stdio.h>
#include <sysinfoapi.h>

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/windows/core_platform_windows.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

BasePlatformWindows::BasePlatformWindows() {}

void BasePlatformWindows::DoOpenURL(const std::string& url) {
  if (explicit_bool(true)) {
    // Switching to the default implementation which goes through Python's
    // webbrowser module. If this works well enough we can kill this
    // override completely.
    BasePlatform::DoOpenURL(url);
  } else {
    auto r = reinterpret_cast<intptr_t>(ShellExecute(
        nullptr, _T("open"), core::CorePlatformWindows::UTF8Decode(url).c_str(),
        nullptr, nullptr, SW_SHOWNORMAL));

    // This should return > 32 on success.
    if (r <= 32) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "Error " + std::to_string(r) + " opening URL '" + url + "'");
    }
  }
}

BOOL WINAPI CtrlHandler(DWORD fdwCtrlType) {
  switch (fdwCtrlType) {
    case CTRL_C_EVENT:
      if (g_base && g_base->logic) {
        g_base->logic->event_loop()->PushCall(
            [] { g_base->logic->HandleInterruptSignal(); });
      } else {
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "SigInt handler called before g_logic exists.");
      }
      return TRUE;

    default:
      return FALSE;
  }
}

void BasePlatformWindows::SetupInterruptHandling() {
  // Set up Ctrl-C handling.
  if (!SetConsoleCtrlHandler(CtrlHandler, TRUE)) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error on SetConsoleCtrlHandler()");
  }
}

auto BasePlatformWindows::SupportsOpenDirExternally() -> bool { return true; }

void BasePlatformWindows::OpenDirExternally(const std::string& path) {
  auto r = reinterpret_cast<intptr_t>(
      ShellExecute(nullptr, _T("open"), _T("explorer.exe"),
                   core::CorePlatformWindows::UTF8Decode(path).c_str(), nullptr,
                   SW_SHOWNORMAL));
  if (r <= 32) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error " + std::to_string(r)
                             + " on open_dir_externally for '" + path + "'");
  }
}

void BasePlatformWindows::OpenFileExternally(const std::string& path) {
  auto r = reinterpret_cast<intptr_t>(
      ShellExecute(nullptr, _T("open"), _T("notepad.exe"),
                   core::CorePlatformWindows::UTF8Decode(path).c_str(), nullptr,
                   SW_SHOWNORMAL));
  if (r <= 32) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error " + std::to_string(r)
                             + " on open_file_externally for '" + path + "'");
  }
}

}  // namespace ballistica::base

#endif  // BA_PLATFORM_WINDOWS
