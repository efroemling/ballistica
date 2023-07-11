// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/platform/core_platform.h"

#if !BA_OSTYPE_WINDOWS
#include <dirent.h>
#endif
#include <fcntl.h>

// Trying to avoid platform-specific headers here except for
// a few mostly-cross-platform bits where its worth the mess.
#if !BA_OSTYPE_WINDOWS
#if BA_ENABLE_EXECINFO_BACKTRACES
#include <execinfo.h>
#endif
#include <cxxabi.h>
#include <unistd.h>
#endif

#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/networking/networking_sys.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_sys.h"

// ------------------------- PLATFORM SELECTION --------------------------------

// This ugly chunk of macros simply pulls in the correct platform class header
// for each platform and defines the actual class g_core->platform will be.

// Android ---------------------------------------------------------------------

#if BA_OSTYPE_ANDROID
#if BA_GOOGLE_BUILD
#include "ballistica/core/platform/android/google/core_plat_andr_google.h"
#define BA_PLATFORM_CLASS CorePlatformAndroidGoogle
#elif BA_AMAZON_BUILD
#include "ballistica/core/platform/android/amazon/core_plat_andr_amazon.h"
#define BA_PLATFORM_CLASS CorePlatformAndroidAmazon
#elif BA_CARDBOARD_BUILD
#include "ballistica/core/platform/android/cardboard/core_pl_an_cardboard.h"
#define BA_PLATFORM_CLASS CorePlatformAndroidCardboard
#else  // Generic android.
#include "ballistica/core/platform/android/core_platform_android.h"
#define BA_PLATFORM_CLASS CorePlatformAndroid
#endif  // (Android subplatform)

// Apple -----------------------------------------------------------------------

#elif BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/core/platform/apple/core_platform_apple.h"
#define BA_PLATFORM_CLASS CorePlatformApple

// Windows ---------------------------------------------------------------------

#elif BA_OSTYPE_WINDOWS
#if BA_RIFT_BUILD
#include "ballistica/core/platform/windows/core_platform_windows_oculus.h"
#define BA_PLATFORM_CLASS CorePlatformWindowsOculus
#else  // generic windows
#include "ballistica/core/platform/windows/core_platform_windows.h"
#define BA_PLATFORM_CLASS CorePlatformWindows
#endif  // windows subtype

// Linux -----------------------------------------------------------------------

#elif BA_OSTYPE_LINUX
#include "ballistica/core/platform/linux/core_platform_linux.h"
#define BA_PLATFORM_CLASS CorePlatformLinux
#else

// Generic ---------------------------------------------------------------------

#define BA_PLATFORM_CLASS CorePlatform

#endif

// ----------------------- END PLATFORM SELECTION ------------------------------

#ifndef BA_PLATFORM_CLASS
#error no BA_PLATFORM_CLASS defined for this platform
#endif

// A call that can be used by custom built native libraries (Python, etc.)
// to forward along debug messages to us.
// FIXME: Reconcile this with our existing C++ version. This one does not
//  require the engine to be spun up so it better suited for things like
//  debugging native libs.
extern "C" {
void BallisticaLowLevelDebugLog(const char* msg) {}
}

namespace ballistica::core {

auto CorePlatform::Create() -> CorePlatform* {
  auto platform = new BA_PLATFORM_CLASS();
  platform->PostInit();
  assert(platform->ran_base_post_init_);
  return platform;
}

void CorePlatform::DebugLog(const std::string& msg) { HandleDebugLog(msg); }

CorePlatform::CorePlatform() : start_time_millisecs_(GetCurrentMillisecs()) {}

void CorePlatform::PostInit() {
  // Hmm; we seem to get some funky invalid utf8 out of
  // this sometimes (mainly on windows). Should look into that
  // more closely or at least log it somewhere.
  device_name_ = Utils::GetValidUTF8(DoGetDeviceName().c_str(), "dn");
  ran_base_post_init_ = true;

  // Are we running in a terminal?
  if (g_buildconfig.enable_stdio_console()) {
    is_stdin_a_terminal_ = GetIsStdinATerminal();
  } else {
    is_stdin_a_terminal_ = false;
  }
}

CorePlatform::~CorePlatform() = default;

auto CorePlatform::GetLegacyDeviceUUID() -> const std::string& {
  if (!have_device_uuid_) {
    legacy_device_uuid_ = GetDeviceV1AccountUUIDPrefix();

    std::string real_unique_uuid;
    bool have_real_unique_uuid = GetRealLegacyDeviceUUID(&real_unique_uuid);
    if (have_real_unique_uuid) {
      legacy_device_uuid_ += real_unique_uuid;
    }

    // Keep demo/arcade uuids unique.
    if (g_buildconfig.demo_build()) {
      legacy_device_uuid_ += "_d";
    } else if (g_buildconfig.arcade_build()) {
      legacy_device_uuid_ += "_a";
    }

    // Ok, as a fallback on platforms where we don't yet have a way to get a
    // real UUID, lets do our best to generate one and stuff it in a file
    // in our config dir. This should be globally-unique, but the downside is
    // the user can tamper with it.
    if (!have_real_unique_uuid) {
      std::string path = GetConfigDirectory() + BA_DIRSLASH + ".bsuuid";

      if (FILE* f = FOpen(path.c_str(), "rb")) {
        // There's an existing one; read it.
        char buffer[100];
        size_t size = fread(buffer, 1, 99, f);
        if (size >= 0) {
          assert(size < 100);
          buffer[size] = 0;
          legacy_device_uuid_ += buffer;
        }
        fclose(f);
      } else {
        // No existing one; generate it.
        std::string val = GenerateUUID();
        legacy_device_uuid_ += val;
        if (FILE* f2 = FOpen(path.c_str(), "wb")) {
          size_t result = fwrite(val.c_str(), val.size(), 1, f2);
          if (result != 1)
            Log(LogLevel::kError, "unable to write bsuuid file.");
          fclose(f2);
        } else {
          Log(LogLevel::kError,
              "unable to open bsuuid file for writing: '" + path + "'");
        }
      }
    }
    have_device_uuid_ = true;
  }
  return legacy_device_uuid_;
}

auto CorePlatform::GetDeviceV1AccountUUIDPrefix() -> std::string {
  Log(LogLevel::kError, "GetDeviceV1AccountUUIDPrefix() unimplemented");
  return "u";
}

auto CorePlatform::GetRealLegacyDeviceUUID(std::string* uuid) -> bool {
  return false;
}

auto CorePlatform::GenerateUUID() -> std::string {
  throw Exception("GenerateUUID() unimplemented");
}

auto CorePlatform::GetDeviceUUIDInputs() -> std::list<std::string> {
  throw Exception("GetDeviceUUIDInputs unimplemented");
}

auto CorePlatform::DoGetConfigDirectoryMonolithicDefault()
    -> std::optional<std::string> {
  std::string config_dir;
  // Go with unset here; let baenv handle it in Python-land.
  return {};
}

auto CorePlatform::GetConfigFilePath() -> std::string {
  return GetConfigDirectory() + BA_DIRSLASH + "config.json";
}

// FIXME: should make this unnecessary.
auto CorePlatform::GetLowLevelConfigValue(const char* key, int default_value)
    -> int {
  std::string path = GetConfigDirectory() + BA_DIRSLASH + ".cvar_" + key;
  int val = default_value;
  FILE* f = FOpen(path.c_str(), "r");
  if (f) {
    int val2;
    int result = fscanf(f, "%d", &val2);  // NOLINT
    if (result == 1) {
      // I'm guessing scanned val is probably untouched on failure
      // but why risk it? Let's only copy it in if it looks successful.
      val = val2;
    }
    fclose(f);
  }
  return val;
}

// FIXME: should make this unnecessary.
void CorePlatform::SetLowLevelConfigValue(const char* key, int value) {
  std::string path = GetConfigDirectory() + BA_DIRSLASH + ".cvar_" + key;
  std::string out = std::to_string(value);
  FILE* f = FOpen(path.c_str(), "w");
  if (f) {
    size_t result = fwrite(out.c_str(), out.size(), 1, f);
    if (result != 1)
      Log(LogLevel::kError, "unable to write low level config file.");
    fclose(f);
  } else {
    Log(LogLevel::kError, "unable to open low level config file for writing.");
  }
}

auto CorePlatform::GetUserPythonDirectory() -> std::optional<std::string> {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_user_python_dir_;
}

auto CorePlatform::GetVolatileDataDirectory() -> std::string {
  if (!made_volatile_data_dir_) {
    volatile_data_dir_ = GetDefaultVolatileDataDirectory();
    MakeDir(volatile_data_dir_);
    made_volatile_data_dir_ = true;
  }
  return volatile_data_dir_;
}

auto CorePlatform::GetDefaultVolatileDataDirectory() -> std::string {
  // By default, stuff this in a subdir under our config dir.
  return GetConfigDirectory() + BA_DIRSLASH + "vdata";
}

auto CorePlatform::GetAppPythonDirectory() -> std::optional<std::string> {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_app_python_dir_;
}

auto CorePlatform::GetSitePythonDirectory() -> std::optional<std::string> {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_site_python_dir_;
}

auto CorePlatform::GetReplaysDir() -> std::string {
  static bool made_dir = false;
  if (!made_dir) {
    replays_dir_ = GetConfigDirectory() + BA_DIRSLASH + "replays";
    MakeDir(replays_dir_);
    made_dir = true;
  }
  return replays_dir_;
}

// rename() supporting UTF8 strings.
auto CorePlatform::Rename(const char* oldname, const char* newname) -> int {
  // This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return rename(oldname, newname);
#endif
}

auto CorePlatform::Remove(const char* path) -> int {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return remove(path);
#endif
}

// stat() supporting UTF8 strings.
auto CorePlatform::Stat(const char* path, struct BA_STAT* buffer) -> int {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return stat(path, buffer);
#endif
}

// fopen() supporting UTF8 strings.
auto CorePlatform::FOpen(const char* path, const char* mode) -> FILE* {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return fopen(path, mode);
#endif
}

auto CorePlatform::FilePathExists(const std::string& name) -> bool {
  struct BA_STAT buffer {};
  return (Stat(name.c_str(), &buffer) == 0);
}

auto CorePlatform::GetSocketErrorString() -> std::string {
  // On default platforms we just look at errno.
  return GetErrnoString();
}

auto CorePlatform::GetSocketError() -> int {
  // By default this is simply errno.
  return errno;
}

auto CorePlatform::GetErrnoString() -> std::string {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#elif BA_OSTYPE_LINUX
  // We seem to be getting a gnu-specific version on linux
  // which returns a char pointer that doesn't always point
  // to the provided buffer.  Sounds like there's a way to
  // get the posix version which returns an error int through some
  // #define magic but just gonna handle both flavors for now
  char buffer[256];
  buffer[0] = 0;
  const char* s = strerror_r(errno, buffer, sizeof(buffer));
  buffer[255] = 0;  // Not sure if we need to clamp on overrun but cant hurt.
  return s;
#else
  char buffer[256];
  buffer[0] = 0;
  strerror_r(errno, buffer, sizeof(buffer));
  buffer[255] = 0;  // Not sure if we need to clamp on overrun but cant hurt.
  return buffer;
#endif
}

// Return the ballisticakit config dir
// This does not vary across versions.
auto CorePlatform::GetConfigDirectory() -> std::string {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_config_dir_;
}

auto CorePlatform::GetConfigDirectoryMonolithicDefault()
    -> std::optional<std::string> {
  // CoreConfig value trumps all. Otherwise go with platform-specific default.
  if (g_core->core_config().config_dir.has_value()) {
    return *g_core->core_config().config_dir;
  }
  return DoGetConfigDirectoryMonolithicDefault();
}

auto CorePlatform::GetDataDirectory() -> std::string {
  BA_PRECONDITION(have_ba_env_vals_);
  return ba_env_data_dir_;
}

auto CorePlatform::GetDataDirectoryMonolithicDefault() -> std::string {
  // CoreConfig arg trumps all. Otherwise ask for platform-specific value.
  if (g_core->core_config().data_dir.has_value()) {
    return *g_core->core_config().data_dir;
  }
  return DoGetDataDirectoryMonolithicDefault();
}

void CorePlatform::MakeDir(const std::string& dir, bool quiet) {
  bool exists = FilePathExists(dir);
  if (!exists) {
    DoMakeDir(dir, quiet);

    // Non-quiet call should always result in the directory existing.
    // (or an exception should have been raised)
    assert(quiet || FilePathExists(dir));
  }
}

auto CorePlatform::AndroidGetExternalFilesDir() -> std::string {
  throw Exception("AndroidGetExternalFilesDir() unimplemented");
}

auto CorePlatform::GetUserPythonDirectoryMonolithicDefault()
    -> std::optional<std::string> {
  // CoreConfig arg trumps all. Otherwise ask for platform-specific value.
  if (g_core->core_config().user_python_dir.has_value()) {
    return *g_core->core_config().user_python_dir;
  }
  return DoGetUserPythonDirectoryMonolithicDefault();
}

auto CorePlatform::DoGetUserPythonDirectoryMonolithicDefault()
    -> std::optional<std::string> {
  // Go with unset; let baenv calc this in Python-land
  return {};
}

void CorePlatform::DoMakeDir(const std::string& dir, bool quiet) {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  int result = mkdir(dir.c_str(),
                     // NOLINTNEXTLINE  (signed values in bitwise stuff)
                     S_IRWXU | S_IRGRP | S_IWGRP | S_IXGRP | S_IROTH | S_IXOTH);
  if (result != 0 && errno != EEXIST && !quiet) {
    throw Exception("Unable to create directory '" + dir + "' (errno "
                    + std::to_string(errno) + ")");
  }
#endif
}

auto CorePlatform::GetLocale() -> std::string {
  const char* lang = getenv("LANG");
  if (lang) {
    return lang;
  } else {
    if (!g_buildconfig.headless_build()) {
      BA_LOG_ONCE(LogLevel::kError,
                  "No LANG value available; defaulting to en_US");
    }
    return "en_US";
  }
}

auto CorePlatform::GetDeviceName() -> std::string {
  assert(ran_base_post_init_);
  return device_name_;
}

auto CorePlatform::DoGetDeviceName() -> std::string {
  // Check devicename in env_var
  char* devicename;
  devicename = getenv("BA_DEVICE_NAME");
  if (devicename != nullptr) {
    return devicename;
  }

  // Else just go with hostname as a decent default.
  char nbuffer[64];
  int ret = gethostname(nbuffer, sizeof(nbuffer));
  if (ret == 0) {
    nbuffer[sizeof(nbuffer) - 1] = 0;  // Make sure its terminated.
    return nbuffer;
  }
  return "Untitled Device";
}

auto CorePlatform::IsRunningOnTV() -> bool { return false; }

auto CorePlatform::HasTouchScreen() -> bool {
  if (!have_has_touchscreen_value_) {
    have_touchscreen_ = DoHasTouchScreen();
    have_has_touchscreen_value_ = true;
  }
  return have_touchscreen_;
}

auto CorePlatform::IsRunningOnFireTV() -> bool { return false; }

auto CorePlatform::IsRunningOnDaydream() -> bool { return false; }

auto CorePlatform::DoHasTouchScreen() -> bool {
  throw Exception("UNIMPLEMENTED");
}

auto CorePlatform::IsRunningOnDesktop() -> bool {
  // Default case to cover mac, win, etc.
  return true;
}

void CorePlatform::SleepMillisecs(millisecs_t ms) {
  std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "NullDereferences"

void CorePlatform::WillExitMain(bool errored) {}

auto CorePlatform::GetUIScale() -> UIScale {
  // Handles mac/pc/linux cases.
  return UIScale::kLarge;
}

void CorePlatform::DisplayLog(const std::string& name, LogLevel level,
                              const std::string& msg) {
  // Do nothing by default.
}

auto CorePlatform::ReportFatalError(const std::string& message,
                                    bool in_top_level_exception_handler)
    -> bool {
  // Don't override handling by default.
  return false;
}

auto CorePlatform::HandleFatalError(bool exit_cleanly,
                                    bool in_top_level_exception_handler)
    -> bool {
  // Don't override handling by default.
  return false;
}

auto CorePlatform::CanShowBlockingFatalErrorDialog() -> bool {
  if (g_buildconfig.sdl2_build()) {
    return true;
  } else {
    return false;
  }
}

void CorePlatform::BlockingFatalErrorDialog(const std::string& message) {
#if BA_SDL2_BUILD
  assert(g_core->InMainThread());
  if (!g_core->HeadlessMode()) {
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Fatal Error",
                             message.c_str(), nullptr);
  }
#endif
}

auto CorePlatform::DoGetDataDirectoryMonolithicDefault() -> std::string {
  // By default, assume we're in it.
  return ".";
}

void CorePlatform::SetEnv(const std::string& name, const std::string& value) {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  auto result = setenv(name.c_str(), value.c_str(), true);
  if (result != 0) {
    throw Exception("Failed to set environment variable '" + name
                    + "'; errno=" + std::to_string(errno));
  }
#endif
}

auto CorePlatform::GetEnv(const std::string& name)
    -> std::optional<std::string> {
  // This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  std::optional<std::string> out{};
  if (char* val = getenv(name.c_str())) {
    out = val;
  }
  return out;
#endif
}

auto CorePlatform::GetIsStdinATerminal() -> bool {
// This covers non-windows cases.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return static_cast<bool>(isatty(fileno(stdin)));
#endif
}

auto CorePlatform::GetOSVersionString() -> std::string { return ""; }

auto CorePlatform::GetLegacyUserAgentString() -> std::string {
  std::string device = GetDeviceName();
  std::string version = GetOSVersionString();
  if (!version.empty()) {
    version = " " + version;
  }

  // Include a store identifier in the build.
  std::string subplatform;
  if (g_buildconfig.headless_build()) {
    subplatform = "HdlS";
  } else if (g_buildconfig.cardboard_build()) {
    subplatform = "GpCb";
  } else if (g_buildconfig.gearvr_build()) {
    subplatform = "OcGVRSt";
  } else if (g_buildconfig.rift_build()) {
    subplatform = "OcRftSt";
  } else if (g_buildconfig.amazon_build()) {
    subplatform = "AmSt";
  } else if (g_buildconfig.google_build()) {
    subplatform = "GpSt";
  } else if (g_buildconfig.use_store_kit() && g_buildconfig.ostype_macos()) {
    subplatform = "McApSt";
  } else if (g_buildconfig.use_store_kit() && g_buildconfig.ostype_ios()) {
    subplatform = "IosApSt";
  } else if (g_buildconfig.use_store_kit() && g_buildconfig.ostype_tvos()) {
    subplatform = "TvsApSt";
  } else if (g_buildconfig.demo_build()) {
    subplatform = "DeMo";
  } else if (g_buildconfig.arcade_build()) {
    subplatform = "ArCd";
  } else if (g_buildconfig.iircade_build()) {
    subplatform = "iiRcd";
  } else {
    subplatform = "TstB";
  }

  if (!subplatform.empty()) {
    subplatform = " " + subplatform;
  }
  if (IsRunningOnTV()) {
    subplatform += " OnTV";
  }

  std::string out{std::string("BallisticaKit ") + kEngineVersion + subplatform
                  + " (" + std::to_string(kEngineBuildNumber) + ") ("
                  + g_buildconfig.platform_string() + version + "; " + device
                  + "; " + GetLocale() + ")"};

  // This gets shipped to various places which might choke on fancy unicode
  // characters, so let's limit to simple ascii.
  out = Utils::StripNonAsciiFromUTF8(out);

  return out;
}

auto CorePlatform::GetCWD() -> std::string {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  char buffer[PATH_MAX];
  return getcwd(buffer, sizeof(buffer));
#endif
}

auto CorePlatform::GetAndroidExecArg() -> std::string { return ""; }

void CorePlatform::GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                         float* width) {
  throw Exception();
}

void CorePlatform::FreeTextTexture(void* tex) { throw Exception(); }

auto CorePlatform::CreateTextTexture(int width, int height,
                                     const std::vector<std::string>& strings,
                                     const std::vector<float>& positions,
                                     const std::vector<float>& widths,
                                     float scale) -> void* {
  throw Exception();
}

auto CorePlatform::GetTextTextureData(void* tex) -> uint8_t* {
  throw Exception();
}

void CorePlatform::OnAppStart() {
  // assert(g_base_soft && g_base_soft->InLogicThread());
}

void CorePlatform::OnAppPause() {
  // assert(g_base_soft && g_base_soft->InLogicThread());
}

void CorePlatform::OnAppResume() {
  // assert(g_base_soft && g_base_soft->InLogicThread());
}

void CorePlatform::OnAppShutdown() {
  // assert(g_base_soft && g_base_soft->InLogicThread());
}

void CorePlatform::OnScreenSizeChange() {
  assert(g_base_soft && g_base_soft->InLogicThread());
}

void CorePlatform::StepDisplayTime() {
  assert(g_base_soft && g_base_soft->InLogicThread());
}

auto CorePlatform::ConvertIncomingLeaderboardScore(
    const std::string& leaderboard_id, int score) -> int {
  return score;
}

void CorePlatform::SubmitScore(const std::string& game,
                               const std::string& version, int64_t score) {
  Log(LogLevel::kError, "FIXME: SubmitScore() unimplemented");
}

void CorePlatform::ReportAchievement(const std::string& achievement) {}

auto CorePlatform::HaveLeaderboard(const std::string& game,
                                   const std::string& config) -> bool {
  return false;
}

void CorePlatform::EditText(const std::string& title, const std::string& value,
                            int max_chars) {
  Log(LogLevel::kError, "FIXME: EditText() unimplemented");
}

void CorePlatform::ShowOnlineScoreUI(const std::string& show,
                                     const std::string& game,
                                     const std::string& game_version) {
  Log(LogLevel::kError, "FIXME: ShowOnlineScoreUI() unimplemented");
}

void CorePlatform::AndroidSetResString(const std::string& res) {
  throw Exception();
}

void CorePlatform::DoApplyAppConfig() {}

void CorePlatform::AndroidSynthesizeBackPress() {
  Log(LogLevel::kError, "AndroidSynthesizeBackPress() unimplemented");
}

void CorePlatform::AndroidQuitActivity() {
  Log(LogLevel::kError, "AndroidQuitActivity() unimplemented");
}

auto CorePlatform::GetDeviceV1AccountID() -> std::string {
  if (g_core->HeadlessMode()) {
    return "S-" + GetLegacyDeviceUUID();
  }

  // Everything else is just considered a 'local' account, though we may
  // give unique ids for unique builds..
  if (g_buildconfig.iircade_build()) {
    return "L-iRc" + GetLegacyDeviceUUID();
  }
  return "L-" + GetLegacyDeviceUUID();
}

auto CorePlatform::DemangleCXXSymbol(const std::string& s) -> std::string {
  // Do __cxa_demangle on platforms that support it.
  // FIXME; I believe there's an equivalent call for windows; should research.
#if !BA_OSTYPE_WINDOWS
  int demangle_status;

  // If we pass null for buffers, this mallocs one for us that we have to free.
  char* demangled_name =
      abi::__cxa_demangle(s.c_str(), nullptr, nullptr, &demangle_status);
  if (demangled_name != nullptr) {
    if (demangle_status != 0) {
      BA_LOG_ONCE(LogLevel::kError,
                  "__cxa_demangle got buffer but non-zero status; unexpected");
    }
    std::string retval = demangled_name;
    free(static_cast<void*>(demangled_name));
    return retval;
  } else {
    return s;
  }
#else
  return s;
#endif
}

auto CorePlatform::NewAutoReleasePool() -> void* { throw Exception(); }

void CorePlatform::DrainAutoReleasePool(void* pool) { throw Exception(); }

void CorePlatform::ResetAchievements() {
  Log(LogLevel::kError, "ResetAchievements() unimplemented");
}

void CorePlatform::GameCenterLogin() { throw Exception(); }

void CorePlatform::RunEvents() {}

auto CorePlatform::GetMemUsageInfo() -> std::string { return "0,0,0"; }

void CorePlatform::MusicPlayerPlay(PyObject* target) {
  Log(LogLevel::kError, "MusicPlayerPlay() unimplemented on this platform");
}

void CorePlatform::MusicPlayerStop() {
  Log(LogLevel::kError, "MusicPlayerStop() unimplemented on this platform");
}

void CorePlatform::MusicPlayerShutdown() {
  Log(LogLevel::kError, "MusicPlayerShutdown() unimplemented on this platform");
}

void CorePlatform::MusicPlayerSetVolume(float volume) {
  Log(LogLevel::kError,
      "MusicPlayerSetVolume() unimplemented on this platform");
}

auto CorePlatform::IsOSPlayingMusic() -> bool { return false; }

void CorePlatform::AndroidShowAppInvite(const std::string& title,
                                        const std::string& message,
                                        const std::string& code) {
  Log(LogLevel::kError, "AndroidShowAppInvite() unimplemented");
}

void CorePlatform::IncrementAnalyticsCount(const std::string& name,
                                           int increment) {}

void CorePlatform::IncrementAnalyticsCountRaw(const std::string& name,
                                              int increment) {}

void CorePlatform::IncrementAnalyticsCountRaw2(const std::string& name,
                                               int uses_increment,
                                               int increment) {}

void CorePlatform::SetAnalyticsScreen(const std::string& screen) {}

void CorePlatform::SubmitAnalyticsCounts() {}

void CorePlatform::SetPlatformMiscReadVals(const std::string& vals) {}

void CorePlatform::ShowAd(const std::string& purpose) {
  Log(LogLevel::kError, "ShowAd() unimplemented");
}

auto CorePlatform::GetHasAds() -> bool { return false; }

auto CorePlatform::GetHasVideoAds() -> bool {
  // By default we assume we have this anywhere we have ads.
  return GetHasAds();
}

void CorePlatform::SignInV1(const std::string& account_type) {
  Log(LogLevel::kError, "SignInV1() unimplemented");
}

void CorePlatform::V1LoginDidChange() {
  // Default is no-op.
}

void CorePlatform::SignOutV1() {
  Log(LogLevel::kError, "SignOutV1() unimplemented");
}

void CorePlatform::AndroidShowWifiSettings() {
  Log(LogLevel::kError, "AndroidShowWifiSettings() unimplemented");
}

void CorePlatform::SetHardwareCursorVisible(bool visible) {
// FIXME: Forward this to app?..
#if BA_SDL_BUILD
  SDL_ShowCursor(visible ? SDL_ENABLE : SDL_DISABLE);
#endif
}

void CorePlatform::QuitApp() { exit(g_core->return_value); }

void CorePlatform::OpenFileExternally(const std::string& path) {
  Log(LogLevel::kError, "OpenFileExternally() unimplemented");
}

void CorePlatform::OpenDirExternally(const std::string& path) {
  Log(LogLevel::kError, "OpenDirExternally() unimplemented");
}

void CorePlatform::MacMusicAppInit() {
  Log(LogLevel::kError, "MacMusicAppInit() unimplemented");
}

auto CorePlatform::MacMusicAppGetVolume() -> int {
  Log(LogLevel::kError, "MacMusicAppGetVolume() unimplemented");
  return 0;
}

void CorePlatform::MacMusicAppSetVolume(int volume) {
  Log(LogLevel::kError, "MacMusicAppSetVolume() unimplemented");
}

void CorePlatform::MacMusicAppGetLibrarySource() {
  Log(LogLevel::kError, "MacMusicAppGetLibrarySource() unimplemented");
}

void CorePlatform::MacMusicAppStop() {
  Log(LogLevel::kError, "MacMusicAppStop() unimplemented");
}

auto CorePlatform::MacMusicAppPlayPlaylist(const std::string& playlist)
    -> bool {
  Log(LogLevel::kError, "MacMusicAppPlayPlaylist() unimplemented");
  return false;
}
auto CorePlatform::MacMusicAppGetPlaylists() -> std::list<std::string> {
  Log(LogLevel::kError, "MacMusicAppGetPlaylists() unimplemented");
  return {};
}

void CorePlatform::SetCurrentThreadName(const std::string& name) {
  // Currently we leave the main thread alone, otherwise we show up as
  // "BallisticaMainThread" under "top" on linux (should check other platforms).
  if (g_core->InMainThread()) {
    return;
  }
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
  pthread_setname_np(name.c_str());
#elif BA_OSTYPE_LINUX || BA_OSTYPE_ANDROID
  pthread_setname_np(pthread_self(), name.c_str());
#endif
}

void CorePlatform::Unlink(const char* path) {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  unlink(path);
#endif
}

auto CorePlatform::AbsPath(const std::string& path, std::string* outpath)
    -> bool {
  // Ensure all implementations fail if the file does not exist.
  if (!FilePathExists(path)) {
    return false;
  }
  return DoAbsPath(path, outpath);
}

auto CorePlatform::DoAbsPath(const std::string& path, std::string* outpath)
    -> bool {
  // This covers all but windows.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  char buffer[PATH_MAX + 1];
  char* ptr = realpath(path.c_str(), buffer);
  if (ptr) {
    *outpath = ptr;
    return true;
  }
  return false;
#endif
}

auto CorePlatform::IsEventPushMode() -> bool { return false; }

auto CorePlatform::GetDisplayResolution(int* x, int* y) -> bool {
  return false;
}

void CorePlatform::CloseSocket(int socket) {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  close(socket);
#endif
}

auto CorePlatform::GetBroadcastAddrs() -> std::vector<uint32_t> {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  std::vector<uint32_t> addrs;
  struct ifaddrs* ifaddr{};
  if (getifaddrs(&ifaddr) != -1) {
    int i = 0;
    for (ifaddrs* ifa = ifaddr; ifa != nullptr; ifa = ifa->ifa_next) {
      // Turns out this can be null if the interface has no addrs.
      if (ifa->ifa_addr == nullptr) {
        continue;
      }
      int family = ifa->ifa_addr->sa_family;
      if (family == AF_INET) {
        if (ifa->ifa_addr != nullptr) {
          uint32_t addr = ntohl(  // NOLINT (clang-tidy signed bitwise whining)
              (reinterpret_cast<sockaddr_in*>(ifa->ifa_addr))->sin_addr.s_addr);
          uint32_t sub = ntohl(  // NOLINT (clang-tidy signed bitwise whining)
              (reinterpret_cast<sockaddr_in*>(ifa->ifa_netmask))
                  ->sin_addr.s_addr);
          uint32_t broadcast = addr | (~sub);
          addrs.push_back(broadcast);
          i++;
        }
      }
    }
    freeifaddrs(ifaddr);
  }
  return addrs;
#endif
}

auto CorePlatform::SetSocketNonBlocking(int sd) -> bool {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  int result = fcntl(sd, F_SETFL, O_NONBLOCK);
  if (result != 0) {
    Log(LogLevel::kError, "Error setting non-blocking socket: "
                              + g_core->platform->GetSocketErrorString());
    return false;
  }
  return true;
#endif
}

auto CorePlatform::GetTicks() const -> millisecs_t {
  return GetCurrentMillisecs() - start_time_millisecs_;
}

auto CorePlatform::GetPlatformName() -> std::string {
  throw Exception("UNIMPLEMENTED");
}

auto CorePlatform::GetSubplatformName() -> std::string {
  // This doesnt always have to be set.
  return "";
}

#pragma mark Stack Traces

#if BA_ENABLE_EXECINFO_BACKTRACES

// Stack traces using the functionality in execinfo.h
class PlatformStackTraceExecInfo : public PlatformStackTrace {
 public:
  static constexpr int kMaxStackLevels = 64;

  // The stack trace should capture the stack state immediately upon
  // construction but should do the bare minimum amount of work to store it. Any
  // expensive operations such as symbolification should be deferred until
  // FormatForDisplay().
  PlatformStackTraceExecInfo() { nsize_ = backtrace(array_, kMaxStackLevels); }

  auto FormatForDisplay() noexcept -> std::string override {
    try {
      std::string s;
      char** symbols = backtrace_symbols(array_, nsize_);
      for (int i = 0; i < nsize_; i++) {
        s += std::string(symbols[i]);
        if (i < nsize_ - 1) {
          s += "\n";
        }
      }
      free(symbols);
      return s;
    } catch (const std::exception&) {
      return "backtrace construction failed.";
    }
  }

  auto Copy() const noexcept -> PlatformStackTrace* override {
    try {
      auto s = new PlatformStackTraceExecInfo(*this);

      // Vanilla copy constructor should do the right thing here.
      assert(s->nsize_ == nsize_
             && memcmp(s->array_, array_, sizeof(array_)) == 0);
      return s;
    } catch (const std::exception&) {
      // If this is failing we're in big trouble anyway.
      return nullptr;
    }
  }

 private:
  void* array_[kMaxStackLevels]{};
  int nsize_{};
};
#endif

auto CorePlatform::GetStackTrace() -> PlatformStackTrace* {
// Our default handler here supports execinfo backtraces where available
// and gives nothing elsewhere.
#if BA_ENABLE_EXECINFO_BACKTRACES
  return new PlatformStackTraceExecInfo();
#else
  return nullptr;
#endif
}

void CorePlatform::RequestPermission(Permission p) {
  // No-op.
}

auto CorePlatform::HavePermission(Permission p) -> bool {
  // Its assumed everything is accessible unless we override saying no.
  return true;
}

void CorePlatform::SetDebugKey(const std::string& key,
                               const std::string& value) {}

void CorePlatform::HandleDebugLog(const std::string& msg) {}

auto CorePlatform::GetCurrentMillisecs() -> millisecs_t {
  return std::chrono::time_point_cast<std::chrono::milliseconds>(
             std::chrono::steady_clock::now())
      .time_since_epoch()
      .count();
}

auto CorePlatform::GetCurrentMicrosecs() -> millisecs_t {
  return std::chrono::time_point_cast<std::chrono::microseconds>(
             std::chrono::steady_clock::now())
      .time_since_epoch()
      .count();
}

auto CorePlatform::GetCurrentWholeSeconds() -> int64_t {
  return std::chrono::time_point_cast<std::chrono::seconds>(
             std::chrono::steady_clock::now())
      .time_since_epoch()
      .count();
}

auto CorePlatform::ClipboardIsSupported() -> bool {
  // We only call our actual virtual function once.
  if (!have_clipboard_is_supported_) {
    clipboard_is_supported_ = DoClipboardIsSupported();
    have_clipboard_is_supported_ = true;
  }
  return clipboard_is_supported_;
}

auto CorePlatform::ClipboardHasText() -> bool {
  // If subplatform says they don't support clipboards, don't even ask.
  if (!ClipboardIsSupported()) {
    return false;
  }
  return DoClipboardHasText();
}

void CorePlatform::ClipboardSetText(const std::string& text) {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardSetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  DoClipboardSetText(text);
}

auto CorePlatform::ClipboardGetText() -> std::string {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardGetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  return DoClipboardGetText();
}

auto CorePlatform::DoClipboardIsSupported() -> bool {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  return true;
#else
  return false;
#endif
}

auto CorePlatform::DoClipboardHasText() -> bool {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  return SDL_HasClipboardText();
#else
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
  return false;
#endif
}

void CorePlatform::DoClipboardSetText(const std::string& text) {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  SDL_SetClipboardText(text.c_str());
#else
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
#endif
}

auto CorePlatform::DoClipboardGetText() -> std::string {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  char* out = SDL_GetClipboardText();
  if (out == nullptr) {
    throw Exception("Error fetching clipboard contents.", PyExcType::kRuntime);
  }
  std::string out_s{out};
  SDL_free(out);
  return out_s;
#else
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
  return "";
#endif
}

auto CorePlatform::System(const char* cmd) -> int {
#if BA_OSTYPE_IOS_TVOS
  throw Exception("system() call is not supported on this OS.");
#else
  return system(cmd);
#endif
}

void CorePlatform::SetBaEnvVals(const PythonRef& ref) {
  assert(!have_ba_env_vals_);
  have_ba_env_vals_ = true;

  ba_env_config_dir_ = ref.GetAttr("config_dir").ValueAsString();
  ba_env_data_dir_ = ref.GetAttr("data_dir").ValueAsString();
  ba_env_app_python_dir_ =
      ref.GetAttr("app_python_dir").ValueAsOptionalString();
  ba_env_user_python_dir_ =
      ref.GetAttr("user_python_dir").ValueAsOptionalString();
  ba_env_site_python_dir_ =
      ref.GetAttr("site_python_dir").ValueAsOptionalString();

  // Consider app-python-dir 'custom' if baenv provided a value
  // for it AND that value differs from baenv's default.
  auto standard_app_python_dir =
      ref.GetAttr("standard_app_python_dir").ValueAsString();
  using_custom_app_python_dir_ =
      ba_env_app_python_dir_.has_value()
      && *ba_env_app_python_dir_ != standard_app_python_dir;

  // Ok, now look for the existence of ba_data in the dir we've got.
  auto fullpath = ba_env_data_dir_ + BA_DIRSLASH + "ba_data";
  if (!FilePathExists(fullpath)) {
    FatalError("ba_data directory not found at '" + fullpath + "'.");
  }
}

}  // namespace ballistica::core
