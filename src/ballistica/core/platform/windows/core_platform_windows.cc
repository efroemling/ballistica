// Released under the MIT License. See LICENSE for details.

#if BA_PLATFORM_WINDOWS
#include "ballistica/core/platform/windows/core_platform_windows.h"

#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <rpc.h>
#include <shellapi.h>
#include <shlobj_core.h>
#include <stdio.h>
#include <sysinfoapi.h>

/* clang-format off */
// Builds fail if this is further up, so we need to disable clang-format to
// keep that from happening.
//
// This define gives us the unicode version.
#define DBGHELP_TRANSLATE_TCHAR
#include <dbghelp.h>
/* clang-format on */

#include <cstdio>
#include <list>
#include <string>
#include <vector>

#pragma comment(lib, "Rpcrt4.lib")
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")
#if BA_DEBUG_BUILD
#pragma comment(lib, "python313_d.lib")
#else
#pragma comment(lib, "python313.lib")
#endif
#pragma comment(lib, "DbgHelp.lib")

// GUI Only Stuff.
#if !BA_HEADLESS_BUILD
#pragma comment(lib, "libogg.lib")
#pragma comment(lib, "libvorbis.lib")
#pragma comment(lib, "libvorbisfile.lib")
#pragma comment(lib, "OpenAL32.lib")
#pragma comment(lib, "SDL2.lib")
#pragma comment(lib, "SDL2main.lib")
#endif

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/native_stack_trace.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/networking/networking_sys.h"

#if !defined(UNICODE) || !defined(_UNICODE)
#error Unicode not defined.
#endif

namespace ballistica::core {

static const int kTraceMaxStackFrames{256};
static const int kTraceMaxFunctionNameLength{1024};

class WinStackTrace : public NativeStackTrace {
 public:
  explicit WinStackTrace(CorePlatformWindows* platform) : platform_{platform} {
    number_of_frames_ =
        CaptureStackBackTrace(0, kTraceMaxStackFrames, stack_, NULL);
  }

  // Return a human readable version of the trace (with symbolification if
  // available).
  auto FormatForDisplay() noexcept -> std::string {
    return platform_->FormatWinStackTraceForDisplay(this);
  }

  // Should return a copy of itself allocated via new() (or nullptr if not
  // possible).
  auto Copy() const noexcept -> NativeStackTrace* override {
    try {
      auto s = new WinStackTrace(*this);

      // Vanilla copy constructor should do the right thing here.
      assert(s->number_of_frames_ == number_of_frames_
             && memcmp(s->stack_, stack_, sizeof(stack_)) == 0);
      return s;
    } catch (const std::exception&) {
      // If this is failing we're in big trouble anyway.
      return nullptr;
    }
  }

  auto number_of_frames() const { return number_of_frames_; }
  auto* stack() const { return stack_; }

 private:
  CorePlatformWindows* platform_;
  WORD number_of_frames_{};
  void* stack_[kTraceMaxStackFrames];
};

auto CorePlatformWindows::FormatWinStackTraceForDisplay(
    WinStackTrace* stack_trace) -> std::string {
  try {
    std::string out;

    // Win docs say this is not thread safe so limit to one at a time.
    std::scoped_lock lock(win_stack_mutex_);

    // Docs say to do this only once.
    if (!win_sym_inited_) {
      win_sym_process_ = GetCurrentProcess();
      SymInitialize(win_sym_process_, NULL, TRUE);
      win_sym_inited_ = true;
    }

    char buf[sizeof(SYMBOL_INFO)
             + (kTraceMaxFunctionNameLength - 1) * sizeof(TCHAR)];
    SYMBOL_INFO* symbol = reinterpret_cast<SYMBOL_INFO*>(buf);
    symbol->MaxNameLen = kTraceMaxFunctionNameLength;
    symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
    DWORD64 s_displacement;
    DWORD l_displacement;
    IMAGEHLP_LINE64 line;
    line.SizeOfStruct = sizeof(IMAGEHLP_LINE64);

    std::string build_src_dir = g_core ? g_core->build_src_dir() : "";

    char linebuf[kTraceMaxFunctionNameLength + 128];
    for (int i = 0; i < stack_trace->number_of_frames(); i++) {
      DWORD64 address = (DWORD64)(stack_trace->stack()[i]);
      std::string symbol_name_s;
      if (SymFromAddr(win_sym_process_, address, &s_displacement, symbol)) {
        symbol_name_s = UTF8Encode(symbol->Name);
        if (!Utils::IsValidUTF8(symbol_name_s)) {
          // Debugging some wonky utf8 I was seeing come through.
          symbol_name_s = "(got invalid utf8 for symbol name)";
        }
      } else {
        symbol_name_s = "(unknown symbol name)";
      }
      const char* symbol_name = symbol_name_s.c_str();

      if (SymGetLineFromAddr64(win_sym_process_, address, &l_displacement,
                               &line)) {
        std::string filename_s = UTF8Encode(line.FileName);

        if (!Utils::IsValidUTF8(filename_s)) {
          // Debugging some wonky utf8 I was seeing come through.
          filename_s = "(got invalid utf8 for filename)";
        }
        const char* filename = filename_s.c_str();

        // If our filename starts with build_src_dir, trim that part
        // off to make things nice and pretty.
        if (!build_src_dir.empty()
            && !strncmp(filename, build_src_dir.c_str(),
                        build_src_dir.size())) {
          filename += build_src_dir.size();
        }

        snprintf(linebuf, sizeof(linebuf),
                 "%-3d %s in %s: line: %lu: address: 0x%p\n", i, symbol_name,
                 filename, line.LineNumber,
                 reinterpret_cast<void*>(symbol->Address));
      } else {
        snprintf(linebuf, sizeof(linebuf),
                 "SymGetLineFromAddr64 returned error code %lu.\n",
                 GetLastError());
        snprintf(linebuf, sizeof(linebuf), "%-3d %s, address 0x%p.\n", i,
                 symbol_name, reinterpret_cast<void*>(symbol->Address));
      }
      out += linebuf;
    }
    return out;
  } catch (const std::exception&) {
    return "stack-trace construction failed.";
  }
}

auto CorePlatformWindows::GetNativeStackTrace() -> NativeStackTrace* {
  return new WinStackTrace(this);
}

// Convert a wide Unicode string to an UTF8 string.
auto CorePlatformWindows::UTF8Encode(const std::wstring& wstr) -> std::string {
  if (wstr.empty()) return std::string();
  int size_needed = WideCharToMultiByte(
      CP_UTF8, 0, &wstr[0], static_cast<int>(wstr.size()), NULL, 0, NULL, NULL);
  std::string str(size_needed, 0);
  WideCharToMultiByte(CP_UTF8, 0, &wstr[0], static_cast<int>(wstr.size()),
                      &str[0], size_needed, NULL, NULL);
  return str;
}

// Convert an UTF8 string to a wide Unicode String.
auto CorePlatformWindows::UTF8Decode(const std::string& str) -> std::wstring {
  if (str.empty()) return std::wstring();
  int size_needed = MultiByteToWideChar(CP_UTF8, 0, &str[0],
                                        static_cast<int>(str.size()), NULL, 0);
  std::wstring wstr(size_needed, 0);
  MultiByteToWideChar(CP_UTF8, 0, &str[0], static_cast<int>(str.size()),
                      &wstr[0], size_needed);
  return wstr;
}

CorePlatformWindows::CorePlatformWindows() {
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
    //     via start /wait BallisticaKitXXX...
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

auto CorePlatformWindows::GetDeviceUUIDInputs() -> std::list<std::string> {
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

auto CorePlatformWindows::DoGetConfigDirectoryMonolithicDefault()
    -> std::optional<std::string> {
  std::string config_dir;
  wchar_t* path;
  auto result = SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &path);
  if (result != S_OK) {
    throw Exception("Unable to get user local-app-data dir.");
  }
  std::string configdir = UTF8Encode(path) + "\\BallisticaKit";
  return configdir;
}

std::string CorePlatformWindows::GetErrnoString() {
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

std::string CorePlatformWindows::GetSocketErrorString() {
  // on windows, socket errors are returned via WSAGetLastError,
  // (while they're just errno elsewhere..)
  return std::to_string(WSAGetLastError());
}

int CorePlatformWindows::GetSocketError() {
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

auto CorePlatformWindows::Remove(const char* path) -> int {
  return _wremove(UTF8Decode(path).c_str());
}

auto CorePlatformWindows::Stat(const char* path, struct BA_STAT* buffer)
    -> int {
  return _wstat(UTF8Decode(path).c_str(), buffer);
}

auto CorePlatformWindows::Rename(const char* oldname, const char* newname)
    -> int {
  // Unlike other platforms, windows will error if the target file already
  // exists instead of simply overwriting it. So let's attempt to blow away
  // anything there first.
  auto new_name_utf8 = UTF8Decode(newname);
  _wremove(new_name_utf8.c_str());
  return _wrename(UTF8Decode(oldname).c_str(), new_name_utf8.c_str());
}

auto CorePlatformWindows::DoAbsPath(const std::string& path,
                                    std::string* outpath) -> bool {
  wchar_t abspath[MAX_PATH + 1];
  auto path_utf8 = UTF8Decode(path);
  uint32_t pathlen =
      GetFullPathNameW(path_utf8.c_str(), MAX_PATH, abspath, nullptr);
  if (pathlen >= MAX_PATH) {
    // Buffer not big enough. Should handle this case.
    return false;
  }
  *outpath = UTF8Encode(abspath);
  return true;
}

auto CorePlatformWindows::FOpen(const char* path, const char* mode) -> FILE* {
  return _wfopen(UTF8Decode(path).c_str(), UTF8Decode(mode).c_str());
}

void CorePlatformWindows::DoMakeDir(const std::string& dir, bool quiet) {
  std::wstring stemp = UTF8Decode(dir);
  int result = CreateDirectory(stemp.c_str(), 0);
  if (result == 0) {
    DWORD err = GetLastError();
    if (err != ERROR_ALREADY_EXISTS) {
      throw Exception("Unable to create directory: '" + dir + "'");
    }
  }
}

std::string CorePlatformWindows::GetLocaleTag() {
  // Get the windows locale.
  // (see http://msdn.microsoft.com/en-us/goglobal/bb895996.aspx)
  // theres a func to convert this to a string but its not available on xp
  // the standard is lang_COUNTRY I think.
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
    case 16393:
      return "en_IN";
      break;  // English - India
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
      // This will fail to resolve to a Locale but it should generate a
      // warning so we know to fix it.
      return "lcid_" + std::to_string(lcid);
  }
}

std::string CorePlatformWindows::DoGetDeviceName() {
  std::string device_name;
  wchar_t computer_name[256];
  DWORD computer_name_size = 256;
  int result = GetComputerName(computer_name, &computer_name_size);
  if (result != 0) {
    device_name = UTF8Encode(computer_name);
    if (device_name.size() != 0) {
      return device_name;
    }
  }
  // Fall back on default.
  return CorePlatform::DoGetDeviceName();
}

std::string CorePlatformWindows::DoGetDeviceDescription() {
  std::string device_name;
  wchar_t computer_name[256];
  DWORD computer_name_size = 256;

  // We currently return computer name for both the device name
  // and description. Is there a way to get a more hardware-y name
  // (like manufacturer make/model?)
  int result = GetComputerName(computer_name, &computer_name_size);
  if (result != 0) {
    device_name = UTF8Encode(computer_name);
    if (device_name.size() != 0) {
      return device_name;
    }
  }
  // Fall back on default.
  return CorePlatform::DoGetDeviceDescription();
}

bool CorePlatformWindows::DoHasTouchScreen() { return false; }

void CorePlatformWindows::EmitPlatformLog(const std::string& name,
                                          LogLevel level,
                                          const std::string& msg) {
  // Spit this out as a debug-string for when running from msvc.
  OutputDebugString(UTF8Decode(msg).c_str());
}

auto CorePlatformWindows::DoGetDataDirectoryMonolithicDefault() -> std::string {
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

    // If the app path happens to be the current dir, return
    // the default of "." which gives us cleaner looking paths in
    // stack traces/etc.
    auto out = UTF8Encode(sz_file_name);
    if (out == GetCWD()) {
      return CorePlatform::DoGetDataDirectoryMonolithicDefault();
    }
    return out;
  } else {
    FatalError("Unable to deduce application path.");
    return CorePlatform::DoGetDataDirectoryMonolithicDefault();
  }
}

auto CorePlatformWindows::GetEnv(const std::string& name)
    -> std::optional<std::string> {
  // Start with a small static buffer for a quick-out. Most stuff we're
  // fetching should fit in this.
  const int kStaticBufferSize{256};
  wchar_t buffer[kStaticBufferSize];
  auto result = GetEnvironmentVariableW(UTF8Decode(name).c_str(), buffer,
                                        kStaticBufferSize);

  // 0 means var wasn't found. This seems like it would clash with zero-length
  // var values that *are* found, but apparently those can't exist on windows?
  // (empty value deletes a var).
  if (result == 0) {
    return {};
  }

  // If it was found and fits in our small static buffer, we're done.
  if (result <= kStaticBufferSize) {
    return UTF8Encode(buffer);
  }

  // Ok; apparently its big. Allocate a buffer big enough to hold it and try
  // again.
  std::vector<wchar_t> big_buffer(result);
  assert(big_buffer.size() == result);
  result = GetEnvironmentVariableW(UTF8Decode(name).c_str(), big_buffer.data(),
                                   static_cast<DWORD>(big_buffer.size()));

  // This should always succeed at this point; make noise if not.
  if (result == 0 || result > big_buffer.size()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "GetEnv to allocated buffer failed; unexpected.");
    return {};
  }
  return UTF8Encode(big_buffer.data());
}

void CorePlatformWindows::SetEnv(const std::string& name,
                                 const std::string& value) {
  auto result = SetEnvironmentVariableW(UTF8Decode(name).c_str(),
                                        UTF8Decode(value).c_str());
  if (result == 0) {
    throw Exception("SetEnvironmentVariable failed for '" + name
                    + "'; error=" + std::to_string(GetLastError()));
  }
}

bool CorePlatformWindows::GetIsStdinATerminal() {
  return _isatty(_fileno(stdin));
}

std::string CorePlatformWindows::GetOSVersionString() {
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

std::string CorePlatformWindows::GetCWD() {
  wchar_t buffer[MAX_PATH];
  wchar_t* result = _wgetcwd(buffer, MAX_PATH);
  if (result == nullptr) {
    throw Exception("Error getting CWD; errno=" + std::to_string(errno));
  }
  return UTF8Encode(buffer);
}

void CorePlatformWindows::Unlink(const char* path) { _unlink(path); }

void CorePlatformWindows::CloseSocket(int socket) { closesocket(socket); }

std::vector<uint32_t> CorePlatformWindows::GetBroadcastAddrs() {
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
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "Memory allocation failed for GetIpAddrTable\n");
      err = true;
    }

    if (!err) {
      // Make a second call to GetIpAddrTable to get the actual data we want
      if ((dwRetVal = GetIpAddrTable(pIPAddrTable, &dwSize, 0)) != NO_ERROR) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            "GetIpAddrTable failed with error " + std::to_string(dwRetVal));
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

bool CorePlatformWindows::SetSocketNonBlocking(int sd) {
  unsigned long dataval = 1;  // NOLINT (func signature wants long)
  int result = ioctlsocket(sd, FIONBIO, &dataval);
  if (result != 0) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "Error setting non-blocking socket: "
                             + g_core->platform->GetSocketErrorString());
    return false;
  }
  return true;
}

std::string CorePlatformWindows::GetLegacyPlatformName() { return "windows"; }

std::string CorePlatformWindows::GetLegacySubplatformName() {
#if BA_VARIANT_TEST_BUILD
  return "test";
#else
  return "";
#endif
}

}  // namespace ballistica::core

#endif  // BA_PLATFORM_WINDOWS
