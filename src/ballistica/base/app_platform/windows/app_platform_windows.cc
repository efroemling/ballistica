// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_WINDOWS
#include "ballistica/base/app_platform/windows/app_platform_windows.h"

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
#include "ballistica/core/platform/windows/platform_windows.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

AppPlatformWindows::AppPlatformWindows() {}

void AppPlatformWindows::DoOpenURL(const std::string& url) {
  if (explicit_bool(true)) {
    // Switching to the default implementation which goes through Python's
    // webbrowser module. If this works well enough we can kill this
    // override completely.
    AppPlatform::DoOpenURL(url);
  } else {
    auto r = reinterpret_cast<intptr_t>(ShellExecute(
        nullptr, _T("open"), core::PlatformWindows::UTF8Decode(url).c_str(),
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
      // For safety, do nothing but set a simple flag here.
      g_event_loop_got_ctrl_c = true;
      return TRUE;

    default:
      return FALSE;
  }
}

void AppPlatformWindows::SetupInterruptHandling() {
  // Set up Ctrl-C handling.
  if (!SetConsoleCtrlHandler(CtrlHandler, TRUE)) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error on SetConsoleCtrlHandler()");
  }
}

auto AppPlatformWindows::SupportsOpenDirExternally() -> bool { return true; }

void AppPlatformWindows::OpenDirExternally(const std::string& path) {
  auto r = reinterpret_cast<intptr_t>(ShellExecute(
      nullptr, _T("open"), _T("explorer.exe"),
      core::PlatformWindows::UTF8Decode(path).c_str(), nullptr, SW_SHOWNORMAL));
  if (r <= 32) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error " + std::to_string(r)
                             + " on open_dir_externally for '" + path + "'");
  }
}

void AppPlatformWindows::OpenFileExternally(const std::string& path) {
  auto r = reinterpret_cast<intptr_t>(ShellExecute(
      nullptr, _T("open"), _T("notepad.exe"),
      core::PlatformWindows::UTF8Decode(path).c_str(), nullptr, SW_SHOWNORMAL));
  if (r <= 32) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error " + std::to_string(r)
                             + " on open_file_externally for '" + path + "'");
  }
}

}  // namespace ballistica::base

#endif  // BA_PLATFORM_WINDOWS
