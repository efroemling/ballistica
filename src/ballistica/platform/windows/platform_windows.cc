// Released under the MIT License. See LICENSE for details.

#if BA_OSTYPE_WINDOWS
#include "ballistica/platform/windows/platform_windows.h"

#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <rpc.h>
#include <shellapi.h>
#include <shlobj_core.h>
#include <stdio.h>
#include <sysinfoapi.h>

#include <filesystem>

#pragma comment(lib, "Rpcrt4.lib")
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")
#if BA_DEBUG_BUILD
#pragma comment(lib, "python39_d.lib")
#else
#pragma comment(lib, "python39.lib")
#endif

#if !BA_HEADLESS_BUILD
#pragma comment(lib, "libogg.lib")
#pragma comment(lib, "libvorbis.lib")
#pragma comment(lib, "libvorbisfile.lib")
#pragma comment(lib, "OpenAL32.lib")
#pragma comment(lib, "SDL2.lib")
#pragma comment(lib, "SDL2main.lib")
#endif

#include "ballistica/game/game.h"
#include "ballistica/networking/networking_sys.h"
#include "ballistica/platform/min_sdl.h"

#if !defined(UNICODE) || !defined(_UNICODE)
#error Unicode not defined.
#endif

namespace ballistica {

// Convert a wide Unicode string to an UTF8 string.
static std::string utf8_encode(const std::wstring& wstr) {
  if (wstr.empty()) return std::string();
  int size_needed = WideCharToMultiByte(
      CP_UTF8, 0, &wstr[0], static_cast<int>(wstr.size()), NULL, 0, NULL, NULL);
  std::string str(size_needed, 0);
  WideCharToMultiByte(CP_UTF8, 0, &wstr[0], static_cast<int>(wstr.size()),
                      &str[0], size_needed, NULL, NULL);
  return str;
}

// Convert an UTF8 string to a wide Unicode String.
static std::wstring utf8_decode(const std::string& str) {
  if (str.empty()) return std::wstring();
  int size_needed = MultiByteToWideChar(CP_UTF8, 0, &str[0],
                                        static_cast<int>(str.size()), NULL, 0);
  std::wstring wstr(size_needed, 0);
  MultiByteToWideChar(CP_UTF8, 0, &str[0], static_cast<int>(str.size()),
                      &wstr[0], size_needed);
  return wstr;
}

PlatformWindows::PlatformWindows() {
  // We should be built in unicode mode.
  assert(sizeof(TCHAR) == 2);

  // Need to init winsock immediately since we use it for
  // threading/logging/etc.
  {
    WSADATA a_wsa_data;
    WORD a_version_requested = MAKEWORD(2, 2);
    int err = WSAStartup(a_version_requested, &a_wsa_data);
    BA_PRECONDITION(err == 0);
  }

  // If we're built as a console app, just assume we've got stdin and stdout.
  if (g_buildconfig.windows_console_build()) {
    have_stdin_stdout_ = true;
  } else {
    // In GUI mode, attempt to attach to a parent console only if one exists.
    // Note: The behavior here is not currently optimal, which is why we
    // stick with just using the console subsystem mostly.
    // Specifically:
    //   - Can only seem to get stdinput from the parent console if launched
    //     via start /wait BallisticaCoreXXX...
    //   - Am seeing garbled stdout lines in some builds when run from
    //     WSL (namely Release builds for whatever reason).
    if (AttachConsole(ATTACH_PARENT_PROCESS)) {
      freopen("CONIN$", "r", stdin);
      freopen("CONOUT$", "w", stdout);
      freopen("CONOUT$", "w", stderr);
      have_stdin_stdout_ = true;
    } else {
      have_stdin_stdout_ = false;
    }
  }

  // This seems to allow us to print unicode stuff to the console...
  if (have_stdin_stdout_) {
    SetConsoleOutputCP(CP_UTF8);
  }
}

BOOL WINAPI CtrlHandler(DWORD fdwCtrlType) {
  switch (fdwCtrlType) {
    case CTRL_C_EVENT:
      if (g_game) {
        g_game->PushInterruptSignalCall();
      } else {
        Log("SigInt handler called before g_game exists.");
      }
      return TRUE;

    default:
      return FALSE;
  }
}

void PlatformWindows::SetupInterruptHandling() {
  // Set up Ctrl-C handling.
  if (!SetConsoleCtrlHandler(CtrlHandler, TRUE)) {
    Log("Error on SetConsoleCtrlHandler()");
  }
}

auto PlatformWindows::GetDeviceUUIDInputs() -> std::list<std::string> {
  std::list<std::string> out;

  std::string ret;
  char value[64];
  DWORD size = _countof(value);
  DWORD type = REG_SZ;
  HKEY key;
  LONG retKey =
      ::RegOpenKeyExA(HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Cryptography",
                      0, KEY_READ | KEY_WOW64_64KEY, &key);
  LONG retVal = ::RegQueryValueExA(key, "MachineGuid", nullptr, &type,
                                   (LPBYTE)value, &size);
  if (retKey == ERROR_SUCCESS && retVal == ERROR_SUCCESS) {
    ret = value;
  }
  ::RegCloseKey(key);

  out.push_back(ret);
  return out;
}

std::string PlatformWindows::GenerateUUID() {
  std::string val;
  UUID uuid;
  ZeroMemory(&uuid, sizeof(UUID));
  UuidCreate(&uuid);
  RPC_CSTR str_a;
  UuidToStringA(&uuid, &str_a);
  if (str_a != nullptr) {
    val = reinterpret_cast<char*>(str_a);
    RpcStringFreeA(&str_a);
  } else {
    // As a fallback, get processor cycles since boot.
    val = std::to_string(__rdtsc());
  }
  return val;
}

std::string PlatformWindows::GetDefaultConfigDir() {
  std::string config_dir;
  wchar_t* path;
  auto result = SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &path);
  if (result != S_OK) {
    throw Exception("Unable to get user local-app-data dir.");
  }
  std::string configdir = utf8_encode(std::wstring(path)) + "\\BallisticaCore";
  return configdir;
}

std::string PlatformWindows::GetErrnoString() {
  switch (errno) {
    case EPERM:
      return "operation not permitted";
      break;
    case ENOENT:
      return "no such file or directory";
      break;
    case ENOTDIR:
      return "not a directory";
      break;
    case EISDIR:
      return "is a directory";
      break;
    case EROFS:
      return "read only file system";
      break;
    case EACCES:
      return "permission denied";
      break;
    case EEXIST:
      return "file exists";
      break;
    case ENOSPC:
      return "no space left on device";
      break;
    default:
      return "error " + std::to_string(errno);
      break;
  }
}

std::string PlatformWindows::GetSocketErrorString() {
  // on windows, socket errors are returned via WSAGetLastError,
  // (while they're just errno elsewhere..)
  return std::to_string(WSAGetLastError());
}

// auto PlatformWindows::FilePathExists(const std::string& name) -> bool {
//   return std::filesystem::exists(utf8_decode(name));
// }

int PlatformWindows::GetSocketError() {
  int val = WSAGetLastError();
  switch (val) {
    case WSAEINTR:
      return EINTR;
    case WSAEWOULDBLOCK:
      return EWOULDBLOCK;
    default:
      return val;
  }
}

auto PlatformWindows::Remove(const char* path) -> int {
  return _wremove(utf8_decode(path).c_str());
}

auto PlatformWindows::Stat(const char* path, struct BA_STAT* buffer) -> int {
  return _wstat(utf8_decode(path).c_str(), buffer);
}

auto PlatformWindows::Rename(const char* oldname, const char* newname) -> int {
  // Unlike other platforms, windows will error if the target file already
  // exists instead of simply overwriting it. So let's attempt to blow away
  // anything there first.
  auto new_name_utf8 = utf8_decode(newname);
  _wremove(new_name_utf8.c_str());
  return _wrename(utf8_decode(oldname).c_str(), new_name_utf8.c_str());
}

auto PlatformWindows::DoAbsPath(const std::string& path, std::string* outpath)
    -> bool {
  wchar_t abspath[MAX_PATH + 1];
  auto path_utf8 = utf8_decode(path);
  uint32_t pathlen =
      GetFullPathNameW(path_utf8.c_str(), MAX_PATH, abspath, nullptr);
  if (pathlen >= MAX_PATH) {
    // Buffer not big enough. Should handle this case.
    return false;
  }
  *outpath = utf8_encode(std::wstring(abspath));
  return true;
}

auto PlatformWindows::FOpen(const char* path, const char* mode) -> FILE* {
  return _wfopen(utf8_decode(path).c_str(), utf8_decode(mode).c_str());
}

void PlatformWindows::DoMakeDir(const std::string& dir, bool quiet) {
  std::wstring stemp = utf8_decode(dir);
  int result = CreateDirectory(stemp.c_str(), 0);
  if (result == 0) {
    DWORD err = GetLastError();
    if (err != ERROR_ALREADY_EXISTS) {
      throw Exception("Unable to create directory: '" + dir + "'");
    }
  }
}

std::string PlatformWindows::GetLocale() {
  // Get the windows locale.
  // (see http://msdn.microsoft.com/en-us/goglobal/bb895996.aspx)
  // theres a func to convert this to a string but its not available on xp
  // the standard is lang_COUNTRY I think..
  // languages: http://www.loc.gov/standards/iso639-2/php/code_list.php
  // country codes:  http://www.iso.org/iso/prods-services/iso3166ma
  //   /02iso-3166-code-lists/country_names_and_code_elements
  // microsoft locale IDs: http://www.microsoft.com/globaldev
  //   /reference/lcid-all.mspx

  // found page with some extras.. if something is missing here, try these..
  // http://www.codeproject.com/Articles/586099
  //   /NET-Framework-Cultures-with-Formats-SQL-Mapping

  LCID lcid = GetUserDefaultLCID();
  switch (lcid) {
    case 1078:
      return "af";
      break;  // Afrikaans
    case 1039:
      return "is";
      break;  // Icelandic
    case 1052:
      return "sq";
      break;  // Albanian
    case 1057:
      return "id";
      break;  // Indonesian
    case 14337:
      return "ar_AE";
      break;  // Arabic  United Arab Emirates
    case 1040:
      return "it_IT";
      break;  // Italian - Italy
    case 15361:
      return "ar_BH";
      break;  // Arabic - Bahrain
    case 2064:
      return "it_CH";
      break;  // Italian - Switzerland
    case 5121:
      return "ar_DZ";
      break;  // Arabic - Algeria
    case 1041:
      return "ja_JP";
      break;  // Japanese
    case 3073:
      return "ar_EG";
      break;  // Arabic - Egypt
    case 1042:
      return "ko_KR";
      break;  // Korean
    case 2049:
      return "ar_IQ";
      break;  // Arabic - Iraq
    case 1062:
      return "lv";
      break;  // Latvian
    case 11265:
      return "ar_JO";
      break;  // Arabic - Jordan
    case 1063:
      return "lt";
      break;  // Lithuanian
    case 13313:
      return "ar_KW";
      break;  // Arabic - Kuwait
    case 1071:
      return "mk";
      break;  // FYRO Macedonian
    case 12289:
      return "ar_LB";
      break;  // Arabic - Lebanon
    case 1086:
      return "ms_MY";
      break;  // Malay - Malaysia
    case 4097:
      return "ar_LY";
      break;  // Arabic - Libya
    case 2110:
      return "ms_BN";
      break;  // Malay  Brunei
    case 6145:
      return "ar_MA";
      break;  // Arabic - Morocco
    case 1082:
      return "mt";
      break;  // Maltese
    case 8193:
      return "ar_OM";
      break;  // Arabic - Oman
    case 1102:
      return "mr";
      break;  // Marathi
    case 16385:
      return "ar_QA";
      break;  // Arabic - Qatar
    case 1044:
      return "no_NO";
      break;  // Norwegian - Bokmål
    case 1025:
      return "ar_SA";
      break;  // Arabic - Saudi Arabia
    case 2068:
      return "no_NO";
      break;  // Norwegian  Nynorsk
    case 10241:
      return "ar_SY";
      break;  // Arabic - Syria
    case 1045:
      return "pl_PL";
      break;  // Polish
    case 7169:
      return "ar_TN";
      break;  // Arabic - Tunisia
    case 2070:
      return "pt_PT";
      break;  // Portuguese - Portugal
    case 9217:
      return "ar_YE";
      break;  // Arabic - Yemen
    case 1046:
      return "pt_BR";
      break;  // Portuguese - Brazil
    case 1067:
      return "hy";
      break;  // Armenian
    case 1047:
      return "rm";
      break;  // Raeto-Romance
    case 1068:
      return "az_AZ";
      break;  // Azeri  Latin
    case 1048:
      return "ro";
      break;  // Romanian - Romania
    case 2092:
      return "az_AZ";
      break;  // Azeri  Cyrillic
    case 2072:
      return "ro_MO";
      break;  // Romanian - Moldova
    case 1069:
      return "eu";
      break;  // Basque
    case 1049:
      return "ru_RU";
      break;  // Russian
    case 1059:
      return "be";
      break;  // Belarusian
    case 2073:
      return "ru_MO";
      break;  // Russian - Moldova
    case 1026:
      return "bg";
      break;  // Bulgarian
    case 1103:
      return "sa";
      break;  // Sanskrit
    case 1027:
      return "ca";
      break;  // Catalan
    case 3098:
      return "sr_SP";
      break;  // Serbian - Cyrillic
    case 10266:
      return "sr_SP";
      break;  // Serbian - Cyrillic .. are we sure?..
    case 2052:
      return "zh_CN";
      break;  // Chinese - China
    case 2074:
      return "sr_SP";
      break;  // Serbian  Latin
    case 3076:
      return "zh_HK";
      break;  // Chinese - Hong Kong S.A.R.
    case 1074:
      return "tn";
      break;  // Setsuana
    case 5124:
      return "zh_MO";
      break;  // Chinese  Macau S.A.R
    case 1060:
      return "sl_SL";
      break;  // Slovenian
    case 4100:
      return "zh_SG";
      break;  // Chinese - Singapore
    case 1051:
      return "sk";
      break;  // Slovak
    case 1028:
      return "zh_TW";
      break;  // Chinese - Taiwan
    case 1070:
      return "sb";
      break;  // Sorbian
    case 1050:
      return "hr";
      break;  // Croatian
    case 1034:
      return "es_ES";
      break;  // Spanish - Spain
    case 1029:
      return "cs_CZ";
      break;  // Czech
    case 11274:
      return "es_AR";
      break;  // Spanish - Argentina
    case 1030:
      return "da_DK";
      break;  // Danish
    case 16394:
      return "es_BO";
      break;  // Spanish - Bolivia
    case 1043:
      return "nl_NL";
      break;  // Dutch  The Netherlands
    case 13322:
      return "es_CL";
      break;  // Spanish - Chile
    case 2067:
      return "nl_BE";
      break;  // Dutch - Belgium
    case 9226:
      return "es_CO";
      break;  // Spanish - Colombia
    case 3081:
      return "en_AU";
      break;  // English - Australia
    case 5130:
      return "es_CR";
      break;  // Spanish - Costa Rica
    case 10249:
      return "en_BZ";
      break;  // English - Belize
    case 7178:
      return "es_DO";
      break;  // Spanish - Dominican Republic
    case 4105:
      return "en_CA";
      break;  // English - Canada
    case 12298:
      return "es_EC";
      break;  // Spanish - Ecuador
    case 9225:
      return "en_CB";
      break;  // English  Carribbean
    case 4106:
      return "es_GT";
      break;  // Spanish - Guatemala
    case 6153:
      return "en_IE";
      break;  // English - Ireland
    case 18442:
      return "es_HN";
      break;  // Spanish - Honduras
    case 8201:
      return "en_JM";
      break;  // English - Jamaica
    case 2058:
      return "es_MX";
      break;  // Spanish - Mexico
    case 5129:
      return "en_NZ";
      break;  // English - New Zealand
    case 19466:
      return "es_NI";
      break;  // Spanish - Nicaragua
    case 13321:
      return "en_PH";
      break;  // English  Phillippines
    case 6154:
      return "es_PA";
      break;  // Spanish - Panama
    case 7177:
      return "en_ZA";
      break;  // English - South Africa
    case 10250:
      return "es_PE";
      break;  // Spanish - Peru
    case 11273:
      return "en_TT";
      break;  // English - Trinidad
    case 20490:
      return "es_PR";
      break;  // Spanish - Puerto Rico
    case 2057:
      return "en_GB";
      break;  // English - United Kingdom
    case 15370:
      return "es_PY";
      break;  // Spanish - Paraguay
    case 1033:
      return "en_US";
      break;  // English - United States
    case 17418:
      return "es_SV";
      break;  // Spanish - El Salvador
    case 1061:
      return "et";
      break;  // Estonian
    case 14346:
      return "es_UY";
      break;  // Spanish - Uruguay
    case 1065:
      return "fa";
      break;  // Farsi
    case 8202:
      return "es_VE";
      break;  // Spanish - Venezuela
    case 1035:
      return "fi_FI";
      break;  // Finnish
    case 1072:
      return "sx";
      break;  // Sutu
    case 1080:
      return "fo";
      break;  // Faroese
    case 1089:
      return "sw";
      break;  // Swahili
    case 1036:
      return "fr_FR";
      break;  // French - France
    case 1053:
      return "sv_SE";
      break;  // Swedish - Sweden
    case 2060:
      return "fr_BE";
      break;  // French - Belgium
    case 2077:
      return "sv_FI";
      break;  // Swedish - Finland
    case 3084:
      return "fr_CA";
      break;  // French - Canada
    case 1097:
      return "ta";
      break;  // Tamil
    case 5132:
      return "fr_LU";
      break;  // French - Luxembourg
    case 1092:
      return "tt";
      break;  // Tatar
    case 4108:
      return "fr_CH";
      break;  // French - Switzerland
    case 1054:
      return "th";
      break;  // Thai
    case 2108:
      return "gd_IE";
      break;  // Gaelic  Ireland
    case 1055:
      return "tr_TR";
      break;  // Turkish
    case 1084:
      return "gd";
      break;  // Gaelic - Scotland
    case 1073:
      return "ts";
      break;  // Tsonga
    case 1031:
      return "de_DE";
      break;  // German - Germany
    case 1058:
      return "uk";
      break;  // Ukrainian
    case 3079:
      return "de_AT";
      break;  // German - Austria
    case 1056:
      return "ur";
      break;  // Urdu
    case 5127:
      return "de_LI";
      break;  // German - Liechtenstein
    case 2115:
      return "uz_UZ";
      break;  // Uzbek  Cyrillic
    case 4103:
      return "de_LU";
      break;  // German - Luxembourg
    case 1091:
      return "uz_UZ";
      break;  // Uzbek  Latin
    case 2055:
      return "de_CH";
      break;  // German - Switzerland
    case 1066:
      return "vi";
      break;  // Vietnamese
    case 1032:
      return "el";
      break;  // Greek
    case 1076:
      return "xh";
      break;  // Xhosa
    case 1037:
      return "he";
      break;  // Hebrew
    case 1085:
      return "yi";
      break;  // Yiddish
    case 1081:
      return "hi";
      break;  // Hindi
    case 1077:
      return "zu";
      break;  // Zulu
    case 1038:
      return "hu_HU";
      break;  // Hungarian
    default:
      return "lcid_" + std::to_string(lcid);
  }
}

std::string PlatformWindows::DoGetDeviceName() {
  std::string device_name;
  wchar_t computer_name[256];
  DWORD computer_name_size = 256;
  int result = GetComputerName(computer_name, &computer_name_size);
  if (result == 0) {
    device_name = "BallisticaCore Game";
  } else {
    device_name = utf8_encode(std::wstring(computer_name));
    if (device_name.size() == 0) {
      device_name = "BallisticaCore Game";
    }
  }
  return device_name;
}

bool PlatformWindows::DoHasTouchScreen() { return false; }

void PlatformWindows::HandleLog(const std::string& msg) {
  // if (have_stdin_stdout_) {
  //   // On headless builds we use default handler (simple stdout).
  //   return Platform::HandleLog(msg);
  // }

  // Also spit this out as a debug-string for when running from msvc.
  OutputDebugString(utf8_decode(msg).c_str());
}

// (The default SDL handler now covers us)
// bool PlatformWindows::BlockingFatalErrorDialog(const std::string& message) {
//   if (HeadlessMode()) {
//     return Platform::BlockingFatalErrorDialog(message);
//   }
//   MessageBoxA(nullptr, (message.c_str()), "BallisticaCore",
//               MB_ICONERROR | MB_OK);

//   // Our message-box call is blocking so we can return false here
//   // and let the app self-terminate at this point.
//   return false;
// }

void PlatformWindows::SetupDataDirectory() {
  // We always want to launch with the working directory where our executable
  // is, but for some reason that's not the default when visual studio
  // debugging. (and overriding it is a per-user setting; ew).  ...so
  // let's force the issue: grab the path to our executable, lop it off
  // at the last \, and chdir to that.
  {
    wchar_t sz_file_name[MAX_PATH + 1];
    GetModuleFileName(nullptr, sz_file_name, MAX_PATH + 1);
    wchar_t* last_slash = nullptr;
    for (wchar_t* s = sz_file_name; *s != 0; ++s) {
      if (*s == '\\') {
        last_slash = s;
      }
    }
    if (last_slash != nullptr) {
      *last_slash = 0;
      int result = _wchdir(sz_file_name);
      if (result != 0) {
        throw Exception("Unable to chdir to application directory.");
      }
    }
  }

  // Simply complain if ba_data isn't here.
  if (!std::filesystem::is_directory("ba_data")) {
    throw Exception("ba_data directory not found.");
  }
}

void PlatformWindows::SetEnv(const std::string& name,
                             const std::string& value) {
  auto result = SetEnvironmentVariableW(utf8_decode(name).c_str(),
                                        utf8_decode(value).c_str());
  if (result == 0) {
    throw Exception("SetEnvironmentVariable failed for '" + name
                    + "'; error=" + std::to_string(GetLastError()));
  }
}

bool PlatformWindows::IsStdinATerminal() { return _isatty(_fileno(stdin)); }

std::string PlatformWindows::GetOSVersionString() {
  DWORD dw_version = 0;
  DWORD dw_major_version = 0;
  DWORD dw_minor_version = 0;
  DWORD dw_build = 0;

  // This is deprecated, but too lazy to find replacement right now.
  // Just hiding the warning.
#pragma warning(disable : 4996)
  dw_version = GetVersion();
#pragma warning(disable : 4996)
  dw_major_version = (DWORD)(LOBYTE(LOWORD(dw_version)));
  dw_minor_version = (DWORD)(HIBYTE(LOWORD(dw_version)));
  if (dw_version < 0x80000000) {
    dw_build = (DWORD)(HIWORD(dw_version));
  }
  std::string version = std::to_string(dw_major_version) + "."
                        + std::to_string(dw_minor_version) + " "
                        + std::to_string(dw_build);
  return version;
}

std::string PlatformWindows::GetCWD() {
  wchar_t buffer[MAX_PATH];
  wchar_t* result = _wgetcwd(buffer, MAX_PATH);
  if (result == nullptr) {
    throw Exception("Error getting CWD; errno=" + std::to_string(errno));
  }
  return utf8_encode(std::wstring(buffer));
}

void PlatformWindows::DoOpenURL(const std::string& url) {
  auto r = reinterpret_cast<intptr_t>(
      ShellExecute(nullptr, _T("open"), utf8_decode(url).c_str(), nullptr,
                   nullptr, SW_SHOWNORMAL));

  // This should return > 32 on success.
  if (r <= 32) {
    Log("Error " + std::to_string(r) + " opening URL '" + url + "'");
  }
}

void PlatformWindows::OpenFileExternally(const std::string& path) {
  auto r = reinterpret_cast<intptr_t>(
      ShellExecute(nullptr, _T("open"), _T("notepad.exe"),
                   utf8_decode(path).c_str(), nullptr, SW_SHOWNORMAL));
  if (r <= 32) {
    Log("Error " + std::to_string(r) + " on open_file_externally for '" + path
        + "'");
  }
}

void PlatformWindows::OpenDirExternally(const std::string& path) {
  auto r = reinterpret_cast<intptr_t>(
      ShellExecute(nullptr, _T("open"), _T("explorer.exe"),
                   utf8_decode(path).c_str(), nullptr, SW_SHOWNORMAL));
  if (r <= 32) {
    Log("Error " + std::to_string(r) + " on open_dir_externally for '" + path
        + "'");
  }
}

void PlatformWindows::Unlink(const char* path) { _unlink(path); }

void PlatformWindows::CloseSocket(int socket) { closesocket(socket); }

std::vector<uint32_t> PlatformWindows::GetBroadcastAddrs() {
#define MALLOC(x) HeapAlloc(GetProcessHeap(), 0, (x))
#define FREE(x) HeapFree(GetProcessHeap(), 0, (x))
  std::vector<uint32_t> addrs;

  // Variables used by GetIpAddrTable
  PMIB_IPADDRTABLE pIPAddrTable;
  DWORD dwSize = 0;
  DWORD dwRetVal = 0;
  bool err = false;

  // Before calling AddIPAddress we use GetIpAddrTable to get an adapter to
  // which we can add the IP.
  pIPAddrTable = static_cast<MIB_IPADDRTABLE*>(MALLOC(sizeof(MIB_IPADDRTABLE)));

  if (pIPAddrTable) {
    // Make an initial call to GetIpAddrTable to get the necessary size into
    // the dwSize variable
    if (GetIpAddrTable(pIPAddrTable, &dwSize, 0) == ERROR_INSUFFICIENT_BUFFER) {
      FREE(pIPAddrTable);
      pIPAddrTable = static_cast<MIB_IPADDRTABLE*>(MALLOC(dwSize));
    }
    if (pIPAddrTable == nullptr) {
      Log("Error: Memory allocation failed for GetIpAddrTable\n");
      err = true;
    }

    if (!err) {
      // Make a second call to GetIpAddrTable to get the actual data we want
      if ((dwRetVal = GetIpAddrTable(pIPAddrTable, &dwSize, 0)) != NO_ERROR) {
        Log("Error: GetIpAddrTable failed with error "
            + std::to_string(dwRetVal));
        err = true;
      }
    }
    if (!err) {
      for (int i = 0; i < static_cast<int>(pIPAddrTable->dwNumEntries); i++) {
        uint32_t addr = ntohl(pIPAddrTable->table[i].dwAddr);
        uint32_t subnet = ntohl(pIPAddrTable->table[i].dwMask);
        uint32_t broadcast = addr | (~subnet);
        addrs.push_back(broadcast);
        // cout << "ADDR IS " << ((addr>>24)&0xFF) << "." << ((addr>>16)&0xFF)
        // << "." << ((addr>>8)&0xFF) << "." << ((addr>>0)&0xFF) << endl; cout
        // << "NETMASK IS " << ((subnet>>24)&0xFF) << "." <<
        // ((subnet>>16)&0xFF)
        // << "." << ((subnet>>8)&0xFF) << "." << ((subnet>>0)&0xFF) << endl;
        // cout << "BROADCAST IS " << ((broadcast>>24)&0xFF) << "." <<
        // ((broadcast>>16)&0xFF) << "." << ((broadcast>>8)&0xFF) << "." <<
        // ((broadcast>>0)&0xFF) << endl;
      }
    }

    if (pIPAddrTable) {
      FREE(pIPAddrTable);
      pIPAddrTable = nullptr;
    }
  }
  return addrs;
#undef MALLOC
#undef FREE
}

bool PlatformWindows::SetSocketNonBlocking(int sd) {
  unsigned long dataval = 1;  // NOLINT (func signature wants long)
  int result = ioctlsocket(sd, FIONBIO, &dataval);
  if (result != 0) {
    Log("Error setting non-blocking socket: "
        + g_platform->GetSocketErrorString());
    return false;
  }
  return true;
}

std::string PlatformWindows::GetPlatformName() { return "windows"; }

std::string PlatformWindows::GetSubplatformName() {
#if BA_TEST_BUILD
  return "test";
#else
  return "";
#endif
}

bool PlatformWindows::ContainsPythonDist() { return true; }

}  // namespace ballistica

#endif  // BA_OSTYPE_WINDOWS
