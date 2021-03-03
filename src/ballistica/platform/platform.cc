// Released under the MIT License. See LICENSE for details.

#include "ballistica/platform/platform.h"

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
#include <pthread.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstring>

#include "ballistica/app/app.h"
#include "ballistica/app/headless_app.h"
#include "ballistica/app/vr_app.h"
#include "ballistica/core/thread.h"
#include "ballistica/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/game/friend_score_set.h"
#include "ballistica/game/game.h"
#include "ballistica/game/score_to_beat.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/camera.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/graphics/mesh/sprite_mesh.h"
#include "ballistica/graphics/vr_graphics.h"
#include "ballistica/input/input.h"
#include "ballistica/input/std_input_module.h"
#include "ballistica/networking/networking_sys.h"
#include "ballistica/platform/sdl/sdl_app.h"
#include "ballistica/python/python.h"

// ------------------------- PLATFORM SELECTION --------------------------------

// This ugly chunk of macros simply pulls in the correct platform class header
// for each platform and defines the actual class g_platform will be.

// Android ---------------------------------------------------------------------

#if BA_OSTYPE_ANDROID
#if BA_GOOGLE_BUILD
#include "ballistica/platform/android/google/platform_android_google.h"
#define BA_PLATFORM_CLASS PlatformAndroidGoogle
#elif BA_AMAZON_BUILD
#include "ballistica/platform/android/amazon/platform_android_amazon.h"
#define BA_PLATFORM_CLASS PlatformAndroidAmazon
#elif BA_CARDBOARD_BUILD
#include "ballistica/platform/android/cardboard/platform_android_cardboard.h"
#define BA_PLATFORM_CLASS PlatformAndroidCardboard
#else  // Generic android.
#include "ballistica/platform/android/platform_android.h"
#define BA_PLATFORM_CLASS PlatformAndroid
#endif  // (Android subplatform)

// Apple -----------------------------------------------------------------------

#elif BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
#include "ballistica/platform/apple/platform_apple.h"
#define BA_PLATFORM_CLASS PlatformApple

// Windows ---------------------------------------------------------------------

#elif BA_OSTYPE_WINDOWS
#if BA_RIFT_BUILD
#include "ballistica/platform/windows/platform_windows_oculus.h"
#define BA_PLATFORM_CLASS PlatformWindowsOculus
#else  // generic windows
#include "ballistica/platform/windows/platform_windows.h"
#define BA_PLATFORM_CLASS PlatformWindows
#endif  // windows subtype

// Linux -----------------------------------------------------------------------

#elif BA_OSTYPE_LINUX
#include "ballistica/platform/linux/platform_linux.h"
#define BA_PLATFORM_CLASS PlatformLinux
#else

// Generic ---------------------------------------------------------------------

#define BA_PLATFORM_CLASS Platform

#endif

// ----------------------- END PLATFORM SELECTION ------------------------------

#ifndef BA_PLATFORM_CLASS
#error no BA_PLATFORM_CLASS defined for this platform
#endif

namespace ballistica {

auto Platform::Create() -> Platform* {
  auto platform = new BA_PLATFORM_CLASS();
  platform->PostInit();
  return platform;
}

void Platform::FinalCleanup() {
  if (g_app_globals->temp_cleanup_callback) {
    g_app_globals->temp_cleanup_callback();
  }
}

Platform::Platform() : starttime_(GetCurrentMilliseconds()) {}

auto Platform::PostInit() -> void {}

Platform::~Platform() = default;

auto Platform::GetUniqueDeviceIdentifier() -> const std::string& {
  if (!have_device_uuid_) {
    device_uuid_ = GetDeviceUUIDPrefix();

    std::string real_unique_uuid;
    bool have_real_unique_uuid = GetRealDeviceUUID(&real_unique_uuid);
    if (have_real_unique_uuid) {
      device_uuid_ += real_unique_uuid;
    }

    // Keep demo/arcade uuids unique.
    if (g_buildconfig.demo_build()) {
      device_uuid_ += "_d";
    } else if (g_buildconfig.arcade_build()) {
      device_uuid_ += "_a";
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
          device_uuid_ += buffer;
        }
        fclose(f);
      } else {
        // No existing one; generate it.
        std::string val = GenerateUUID();
        device_uuid_ += val;
        if (FILE* f2 = FOpen(path.c_str(), "wb")) {
          size_t result = fwrite(val.c_str(), val.size(), 1, f2);
          if (result != 1) Log("unable to write bsuuid file.");
          fclose(f2);
        } else {
          Log("unable to open bsuuid file for writing: '" + path + "'");
        }
      }
    }
    have_device_uuid_ = true;
  }
  return device_uuid_;
}

auto Platform::GetDeviceUUIDPrefix() -> std::string {
  Log("GetDeviceUUIDPrefix() unimplemented");
  return "u";
}

auto Platform::GetRealDeviceUUID(std::string* uuid) -> bool { return false; }

auto Platform::GenerateUUID() -> std::string {
  throw Exception("GenerateUUID() unimplemented");
}

auto Platform::GetDefaultConfigDir() -> std::string {
  std::string config_dir;
  // As a default, look for a HOME env var and use that if present
  // this will cover linux and command-line macOS.
  char* home = getenv("HOME");
  if (home) {
    config_dir = std::string(home) + "/.ballisticacore";
  } else {
    printf("GetDefaultConfigDir: can't get env var \"HOME\"\n");
    fflush(stdout);
    throw Exception();
  }
  return config_dir;
}

auto Platform::GetConfigFilePath() -> std::string {
  return GetConfigDirectory() + BA_DIRSLASH + "config.json";
}

auto Platform::GetLowLevelConfigValue(const char* key, int default_value)
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

void Platform::SetLowLevelConfigValue(const char* key, int value) {
  std::string path = GetConfigDirectory() + BA_DIRSLASH + ".cvar_" + key;
  std::string out = std::to_string(value);
  FILE* f = FOpen(path.c_str(), "w");
  if (f) {
    size_t result = fwrite(out.c_str(), out.size(), 1, f);
    if (result != 1) Log("unable to write low level config file.");
    fclose(f);
  } else {
    Log("unable to open low level config file for writing.");
  }
}

auto Platform::GetUserPythonDirectory() -> std::string {
  // Make sure it exists the first time we run.
  static bool attempted_to_make_user_scripts_dir = false;

  if (!attempted_to_make_user_scripts_dir) {
    user_scripts_dir_ = DoGetUserPythonDirectory();

    // Attempt to make it. (it's ok if this fails)
    MakeDir(user_scripts_dir_, true);
    attempted_to_make_user_scripts_dir = true;
  }
  return user_scripts_dir_;
}

auto Platform::GetAppPythonDirectory() -> std::string {
  static bool checked_dir = false;
  if (!checked_dir) {
    checked_dir = true;

    // If there is a sys/VERSION in the user-python dir we use that.
    app_python_dir_ = GetUserPythonDirectory() + BA_DIRSLASH + "sys"
                      + BA_DIRSLASH + kAppVersion;

    // Fall back to our default if that doesn't exist.
    if (FilePathExists(app_python_dir_)) {
      using_custom_app_python_dir_ = true;
      Log("Using custom app Python path: '"
              + (GetUserPythonDirectory() + BA_DIRSLASH + "sys" + BA_DIRSLASH
                 + kAppVersion)
              + "'.",
          true, false);

    } else {
      // Going with relative paths for cleaner tracebacks...
      app_python_dir_ = std::string("ba_data") + BA_DIRSLASH + "python";
    }
  }
  return app_python_dir_;
}

auto Platform::GetSitePythonDirectory() -> std::string {
  static bool checked_dir = false;
  if (!checked_dir) {
    checked_dir = true;

    if (!FilePathExists(site_python_dir_)) {
      // Going with relative paths for cleaner tracebacks...
      site_python_dir_ =
          std::string("ba_data") + BA_DIRSLASH + "python-site-packages";
    }
  }
  return site_python_dir_;
}

auto Platform::GetReplaysDir() -> std::string {
  static bool made_dir = false;
  if (!made_dir) {
    replays_dir_ = GetConfigDirectory() + BA_DIRSLASH + "replays";
    MakeDir(replays_dir_);
    made_dir = true;
  }
  return replays_dir_;
}

// rename() supporting UTF8 strings.
auto Platform::Rename(const char* oldname, const char* newname) -> int {
  // this covers non-windows platforms
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return rename(oldname, newname);
#endif
}

auto Platform::Remove(const char* path) -> int {
  // this covers non-windows platforms
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return remove(path);
#endif
}

// stat() supporting UTF8 strings.
auto Platform::Stat(const char* path, struct BA_STAT* buffer) -> int {
  // this covers non-windows platforms
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return stat(path, buffer);
#endif
}

// fopen() supporting UTF8 strings.
auto Platform::FOpen(const char* path, const char* mode) -> FILE* {
  // this covers non-windows platforms
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return fopen(path, mode);
#endif
}

auto Platform::FilePathExists(const std::string& name) -> bool {
  struct BA_STAT buffer {};
  return (Stat(name.c_str(), &buffer) == 0);
}

auto Platform::GetSocketErrorString() -> std::string {
  // On default platforms we just look at errno.
  return GetErrnoString();
}

auto Platform::GetSocketError() -> int {
  // by default this is simply errno
  return errno;
}

auto Platform::GetErrnoString() -> std::string {
  // this covers non-windows platforms
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

// Return the ballisticacore config dir
// This does not vary across versions.
auto Platform::GetConfigDirectory() -> std::string {
  // Make sure args have been handled since we use them.
  assert(g_app_globals->args_handled);

  if (!have_config_dir_) {
    // If the user provided cfgdir as an arg.
    if (!g_app_globals->user_config_dir.empty()) {
      config_dir_ = g_app_globals->user_config_dir;
    } else {
      config_dir_ = GetDefaultConfigDir();
    }

    // Try to make sure the config dir exists.
    MakeDir(config_dir_);

    have_config_dir_ = true;
  }
  return config_dir_;
}

void Platform::MakeDir(const std::string& dir, bool quiet) {
  bool exists = FilePathExists(dir);
  if (!exists) {
    DoMakeDir(dir, quiet);

    // Non-quiet call should result in directory existing.
    // (or an exception should have been raised)
    assert(quiet || FilePathExists(dir));
  }
}

auto Platform::GetExternalStoragePath() -> std::string {
  throw Exception("GetExternalStoragePath() unimplemented");
}

auto Platform::DoGetUserPythonDirectory() -> std::string {
  return GetConfigDirectory() + BA_DIRSLASH + "mods";
}

void Platform::DoMakeDir(const std::string& dir, bool quiet) {
  // Default case here covers all non-windows platforms.
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

auto Platform::GetLocale() -> std::string {
  const char* lang = getenv("LANG");
  if (lang) {
    return lang;
  } else {
    if (!g_buildconfig.headless_build()) {
      BA_LOG_ONCE("No LANG value available; defaulting to en_US");
    }
    return "en_US";
  }
}

auto Platform::GetDeviceName() -> std::string {
  static std::string device_name;
  static bool have_device_name = false;

  // In headless-mode we always return our party name if that's available
  // (otherwise everything will just be BallisticaCore Game).
  // UPDATE: hmm don't think I like this. Device-name is supposed to go into
  // user-agent-strings and whatnot.
  // Should probably inject public party name at a higher level.
  if (g_buildconfig.headless_build()) {
    // Hmm this might be called from non-main threads; should
    // think about ensuring this is thread-safe perhaps.
    if (g_python != nullptr) {
      std::string pname = g_game->public_party_name();
      if (!pname.empty()) {
        device_name = pname;
        have_device_name = true;
      }
    }
  }

  if (!have_device_name) {
    device_name = DoGetDeviceName();

    // Hmm seem to get some funky invalid utf8 out of
    // this sometimes (mainly on windows). Should look into that
    // more closely or at least log it somewhere.
    device_name = Utils::GetValidUTF8(device_name.c_str(), "dn");
    have_device_name = true;
  }
  return device_name;
}

auto Platform::DoGetDeviceName() -> std::string {
  return "BallisticaCore Game";
}

auto Platform::IsRunningOnTV() -> bool { return false; }

auto Platform::HasTouchScreen() -> bool {
  if (!have_has_touchscreen_value_) {
    have_touchscreen_ = DoHasTouchScreen();
    have_has_touchscreen_value_ = true;
  }
  return have_touchscreen_;
}

auto Platform::IsRunningOnFireTV() -> bool { return false; }

auto Platform::IsRunningOnDaydream() -> bool { return false; }

auto Platform::DoHasTouchScreen() -> bool { throw Exception("UNIMPLEMENTED"); }

auto Platform::IsRunningOnDesktop() -> bool {
  // Default case to cover mac, win, etc.
  return true;
}

void Platform::SleepMS(millisecs_t ms) {
  std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

// General one-time initialization stuff
static void Init() {
  // Sanity check: make sure asserts are stripped out of release builds
  // (NDEBUG should do this).
#if !BA_DEBUG_BUILD
#ifndef NDEBUG
#error Expected NDEBUG to be defined for release builds.
#endif  // NDEBUG
  assert(true);
#endif  // !BA_DEBUG_BUILD

  // Are we running in a terminal?
  if (g_buildconfig.use_stdin_thread()) {
    g_app_globals->is_stdin_a_terminal = g_platform->IsStdinATerminal();
  } else {
    g_app_globals->is_stdin_a_terminal = false;
  }

  // If we're running in a terminal, print some info.
  if (g_app_globals->is_stdin_a_terminal) {
    if (g_buildconfig.headless_build()) {
      printf("BallisticaCore Headless %s build %d.\n", kAppVersion,
             kAppBuildNumber);
      fflush(stdout);
    } else {
      printf("BallisticaCore %s build %d.\n", kAppVersion, kAppBuildNumber);
      fflush(stdout);
    }
  }

  g_app_globals->user_agent_string = g_platform->GetUserAgentString();

  // Figure out where our data is and chdir there.
  g_platform->SetupDataDirectory();

  // Run these just to make sure these dirs exist.
  // (otherwise they might not get made if nothing writes to them).
  g_platform->GetConfigDirectory();
  g_platform->GetUserPythonDirectory();
}

static void HandleArgs(int argc, char** argv) {
  assert(!g_app_globals->args_handled);
  g_app_globals->args_handled = true;

  // If there's just one arg and it's "--version", return the version.
  if (argc == 2 && !strcmp(argv[1], "--version")) {
    printf("Ballistica %s build %d\n", kAppVersion, kAppBuildNumber);
    fflush(stdout);
    exit(0);
  }
  for (int i = 1; i < argc; ++i) {
    // In our rift build, a '-2d' arg causes us to run in regular 2d mode.
    if (g_buildconfig.rift_build() && !strcmp(argv[i], "-2d")) {
      g_app_globals->vr_mode = false;
    } else if (!strcmp(argv[i], "-exec")) {
      if (i + 1 < argc) {
        g_app_globals->exec_command = argv[i + 1];
      } else {
        printf("%s", "Error: expected arg after -exec\n");
        fflush(stdout);
        exit(-1);
      }
    } else if (!strcmp(argv[i], "-cfgdir")) {
      if (i + 1 < argc) {
        g_app_globals->user_config_dir = argv[i + 1];

        // Need to convert this to an abs path since we chdir soon.
        bool success =
            g_platform->AbsPath(argv[i + 1], &g_app_globals->user_config_dir);
        if (!success) {
          // This can fail if the path doesn't exist.
          if (!g_platform->FilePathExists(argv[i + 1])) {
            printf("ERROR: provided config dir does not exist: '%s'\n",
                   argv[i + 1]);
          } else {
            printf(
                "ERROR: unable to determine absolute path of config dir '%s'\n",
                argv[i + 1]);
          }
          fflush(stdout);
          exit(-1);
        }
      } else {
        Log("ERROR: expected arg after -cfgdir");
        exit(-1);
      }
    }
  }

  // In Android's case we have to pull our exec arg from the java/kotlin layer.
  if (g_buildconfig.ostype_android()) {
    g_app_globals->exec_command = g_platform->GetAndroidExecArg();
  }

  // TEMP/HACK: hard code launch args.
  if (explicit_bool(false)) {
    if (g_buildconfig.ostype_android()) {
      g_app_globals->exec_command =
          "import ba.internal; ba.internal.run_stress_test()";
    }
  }
}

void Platform::CreateApp() {
  assert(g_app_globals);
  assert(InMainThread());

  // Hmm do these belong here?...
  HandleArgs(g_app_globals->argc, g_app_globals->argv);
  Init();

// TEMP - need to init sdl on our legacy mac build even though its not
// technically an SDL app. Kill this once the old mac build is gone.
#if BA_LEGACY_MACOS_BUILD
  SDLApp::InitSDL();
#endif

#if BA_HEADLESS_BUILD
  g_main_thread->AddModule<HeadlessApp>();
#elif BA_RIFT_BUILD
  // Rift build can spin up in either VR or regular mode.
  if (g_app_globals->vr_mode) {
    g_main_thread->AddModule<VRApp>();
  } else {
    g_main_thread->AddModule<SDLApp>();
  }
#elif BA_CARDBOARD_BUILD
  g_main_thread->AddModule<VRApp>();
#elif BA_SDL_BUILD
  g_main_thread->AddModule<SDLApp>();
#else
  g_main_thread->AddModule<App>();
#endif

  // Let app do any init it needs to after it is fully constructed.
  g_app->PostInit();
}

auto Platform::CreateGraphics() -> Graphics* {
  assert(InGameThread());
#if BA_VR_BUILD
  return new VRGraphics();
#else
  return new Graphics();
#endif
}

auto Platform::GetKeyName(int keycode) -> std::string {
  // On our actual SDL platforms we're trying to be *pure* sdl so
  // call their function for this. Otherwise we call our own version
  // of it which is basically the same thing (at least for now).
#if BA_SDL_BUILD && !BA_MINSDL_BUILD
  return SDL_GetKeyName(static_cast<SDL_Keycode>(keycode));
#else
  return g_input->GetKeyName(keycode);
#endif
}

void Platform::CreateAuxiliaryModules() {
#if !BA_HEADLESS_BUILD
  auto bg_dynamics_thread = new Thread(ThreadIdentifier::kBGDynamics);
  g_app_globals->pausable_threads.push_back(bg_dynamics_thread);
#endif
#if !BA_HEADLESS_BUILD
  bg_dynamics_thread->AddModule<BGDynamicsServer>();
#endif

  if (g_buildconfig.use_stdin_thread()) {
    // Start listening for stdin commands (on platforms where that makes sense).
    // Note: this thread blocks indefinitely for input so we don't add it to the
    // pausable list.
    auto std_input_thread = new Thread(ThreadIdentifier::kStdin);
    std_input_thread->AddModule<StdInputModule>();
    g_std_input_module->PushBeginReadCall();
  }
}

void Platform::WillExitMain(bool errored) {}

auto Platform::GetUIScale() -> UIScale {
  // Handles mac/pc/linux cases.
  return UIScale::kLarge;
}

void Platform::HandleLog(const std::string& msg) {
  // Do nothing by default.
}

auto Platform::ReportFatalError(const std::string& message,
                                bool in_top_level_exception_handler) -> bool {
  // Don't override handling by default.
  return false;
}

auto Platform::HandleFatalError(bool exit_cleanly,
                                bool in_top_level_exception_handler) -> bool {
  // Don't override handling by default.
  return false;
}

auto Platform::CanShowBlockingFatalErrorDialog() -> bool {
  if (g_buildconfig.sdl2_build()) {
    return true;
  } else {
    return false;
  }
}

auto Platform::BlockingFatalErrorDialog(const std::string& message) -> void {
#if BA_SDL2_BUILD
  assert(InMainThread());
  if (!HeadlessMode()) {
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Fatal Error",
                             message.c_str(), nullptr);
  }
#endif
}

void Platform::SetupDataDirectory() {
// This covers non-windows cases.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  // Default to './ba_data'.
  DIR* d = opendir("ba_data");
  if (d == nullptr) {
    throw Exception("ba_data directory not found.");
  }
  closedir(d);
#endif

  // Apparently Android NDK 22 includes std::filesystem; once that is out
  // then we should be able to use this everywhere.
  // Oh - and we also need to wait for GCC 8, so when we switch to Ubuntu20...
  // Oh; and we should see if switch/etc. supports it before making it a hard
  // requirement.
  // if (!std::filesystem::is_directory("ba_data")) {
  //   throw Exception("ba_data directory not found.");
  // }
}

void Platform::SetEnv(const std::string& name, const std::string& value) {
// This covers non-windows cases.
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

auto Platform::IsStdinATerminal() -> bool {
// This covers non-windows cases.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return static_cast<bool>(isatty(fileno(stdin)));
#endif
}

auto Platform::GetOSVersionString() -> std::string { return ""; }

auto Platform::GetUserAgentString() -> std::string {
  // Fetch our device name here from main thread so it'll be safe
  // to from other threads later (it gets cached as a string)
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
  return std::string("BallisticaCore ") + kAppVersion + subplatform + " ("
         + std::to_string(kAppBuildNumber) + ") ("
         + g_buildconfig.platform_string() + version + "; " + device + "; "
         + GetLocale() + ")";
}

auto Platform::GetCWD() -> std::string {
// Covers non-windows cases.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  char buffer[PATH_MAX];
  return getcwd(buffer, sizeof(buffer));
#endif
}

auto Platform::GetAndroidExecArg() -> std::string { return ""; }

void Platform::GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                     float* width) {
  throw Exception();
}

void Platform::FreeTextTexture(void* tex) { throw Exception(); }

auto Platform::CreateTextTexture(int width, int height,
                                 const std::vector<std::string>& strings,
                                 const std::vector<float>& positions,
                                 const std::vector<float>& widths, float scale)
    -> void* {
  throw Exception();
}

auto Platform::GetTextTextureData(void* tex) -> uint8_t* { throw Exception(); }

void Platform::OnBootstrapComplete() {}

auto Platform::ConvertIncomingLeaderboardScore(
    const std::string& leaderboard_id, int score) -> int {
  return score;
}

void Platform::GetFriendScores(const std::string& game,
                               const std::string& game_version, void* data) {
  // As a default, just fail gracefully.
  Log("FIXME: GetFriendScores unimplemented");
  g_game->PushFriendScoreSetCall(FriendScoreSet(false, data));
}

void Platform::SubmitScore(const std::string& game, const std::string& version,
                           int64_t score) {
  Log("FIXME: SubmitScore() unimplemented");
}

void Platform::ReportAchievement(const std::string& achievement) {}

auto Platform::HaveLeaderboard(const std::string& game,
                               const std::string& config) -> bool {
  return false;
}

void Platform::EditText(const std::string& title, const std::string& value,
                        int max_chars) {
  Log("FIXME: EditText() unimplemented");
}

void Platform::ShowOnlineScoreUI(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version) {
  Log("FIXME: ShowOnlineScoreUI() unimplemented");
}

void Platform::Purchase(const std::string& item) {
  // Just print 'unavailable' by default.
  g_python->PushObjCall(Python::ObjID::kUnavailableMessageCall);
}

void Platform::RestorePurchases() { Log("RestorePurchases() unimplemented"); }

void Platform::AndroidSetResString(const std::string& res) {
  throw Exception();
}

void Platform::ApplyConfig() {}

void Platform::AndroidSynthesizeBackPress() {
  Log("AndroidSynthesizeBackPress() unimplemented");
}

void Platform::AndroidQuitActivity() {
  Log("AndroidQuitActivity() unimplemented");
}

auto Platform::GetDeviceAccountID() -> std::string {
  if (HeadlessMode()) {
    return "S-" + GetUniqueDeviceIdentifier();
  }

  // Everything else is just considered a 'local' account, though we may
  // give unique ids for unique builds..
  if (g_buildconfig.iircade_build()) {
    return "L-iRc" + GetUniqueDeviceIdentifier();
  }
  return "L-" + GetUniqueDeviceIdentifier();
}

auto Platform::DemangleCXXSymbol(const std::string& s) -> std::string {
  // Do __cxa_demangle on platforms that support it.
  // FIXME; I believe there's an equivalent call for windows; should research.
#if !BA_OSTYPE_WINDOWS
  int demangle_status;

  // If we pass null for buffers, this mallocs one for us that we have to free.
  char* demangled_name =
      abi::__cxa_demangle(s.c_str(), nullptr, nullptr, &demangle_status);
  if (demangled_name != nullptr) {
    if (demangle_status != 0) {
      BA_LOG_ONCE("__cxa_demangle got buffer but non-zero status; unexpected");
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

auto Platform::NewAutoReleasePool() -> void* { throw Exception(); }

void Platform::DrainAutoReleasePool(void* pool) { throw Exception(); }

auto Platform::AndroidGPGSNewConnectionToClient(int id) -> ConnectionToClient* {
  throw Exception();
}
auto Platform::AndroidGPGSNewConnectionToHost() -> ConnectionToHost* {
  throw Exception();
}

auto Platform::AndroidIsGPGSConnectionToClient(ConnectionToClient* c) -> bool {
  throw Exception();
}

void Platform::OpenURL(const std::string& url) {
  // Can't open URLs in VR - just tell the game thread to show the url.
  if (IsVRMode()) {
    g_game->PushShowURLCall(url);
    return;
  }

  // Otherwise fall back to our platform-specific handler.
  g_platform->DoOpenURL(url);
}

void Platform::DoOpenURL(const std::string& url) {
  Log("DoOpenURL unimplemented on this platform.");
}

void Platform::ResetAchievements() { Log("ResetAchievements() unimplemented"); }

void Platform::GameCenterLogin() { throw Exception(); }

void Platform::PurchaseAck(const std::string& purchase,
                           const std::string& order_id) {
  Log("PurchaseAck() unimplemented");
}

void Platform::RunEvents() {}

auto Platform::GetMemUsageInfo() -> std::string { return "0,0,0"; }

void Platform::OnAppPause() {}
void Platform::OnAppResume() {}

void Platform::MusicPlayerPlay(PyObject* target) {
  Log("MusicPlayerPlay() unimplemented on this platform");
}
void Platform::MusicPlayerStop() {
  Log("MusicPlayerStop() unimplemented on this platform");
}
void Platform::MusicPlayerShutdown() {
  Log("MusicPlayerShutdown() unimplemented on this platform");
}

void Platform::MusicPlayerSetVolume(float volume) {
  Log("MusicPlayerSetVolume() unimplemented on this platform");
}

auto Platform::IsOSPlayingMusic() -> bool { return false; }

void Platform::AndroidShowAppInvite(const std::string& title,
                                    const std::string& message,
                                    const std::string& code) {
  Log("AndroidShowAppInvite() unimplemented");
}

void Platform::IncrementAnalyticsCount(const std::string& name, int increment) {
}

void Platform::IncrementAnalyticsCountRaw(const std::string& name,
                                          int increment) {}

void Platform::IncrementAnalyticsCountRaw2(const std::string& name,
                                           int uses_increment, int increment) {}

void Platform::SetAnalyticsScreen(const std::string& screen) {}

void Platform::SubmitAnalyticsCounts() {}

void Platform::SetPlatformMiscReadVals(const std::string& vals) {}

void Platform::AndroidRefreshFile(const std::string& file) {
  Log("AndroidRefreshFile() unimplemented");
}

void Platform::ShowAd(const std::string& purpose) {
  Log("ShowAd() unimplemented");
}

auto Platform::GetHasAds() -> bool { return false; }

auto Platform::GetHasVideoAds() -> bool {
  // By default we assume we have this anywhere we have ads.
  return GetHasAds();
}

void Platform::AndroidGPGSPartyInvitePlayers() {
  Log("AndroidGPGSPartyInvitePlayers() unimplemented");
}

void Platform::AndroidGPGSPartyShowInvites() {
  Log("AndroidGPGSPartyShowInvites() unimplemented");
}

void Platform::AndroidGPGSPartyInviteAccept(const std::string& invite_id) {
  Log("AndroidGPGSPartyInviteAccept() unimplemented");
}

void Platform::SignIn(const std::string& account_type) {
  Log("SignIn() unimplemented");
}

void Platform::SignOut() { Log("SignOut() unimplemented"); }

void Platform::AndroidShowWifiSettings() {
  Log("AndroidShowWifiSettings() unimplemented");
}

void Platform::SetHardwareCursorVisible(bool visible) {
// FIXME: Forward this to app?..
#if BA_SDL_BUILD
  SDL_ShowCursor(visible ? SDL_ENABLE : SDL_DISABLE);
#endif
}

void Platform::QuitApp() { exit(g_app_globals->return_value); }

void Platform::GetScoresToBeat(const std::string& level,
                               const std::string& config, void* py_callback) {
  // By default, return nothing.
  g_game->PushScoresToBeatResponseCall(false, std::list<ScoreToBeat>(),
                                       py_callback);
}

void Platform::OpenFileExternally(const std::string& path) {
  Log("OpenFileExternally() unimplemented");
}

void Platform::OpenDirExternally(const std::string& path) {
  Log("OpenDirExternally() unimplemented");
}

void Platform::MacMusicAppInit() { Log("MacMusicAppInit() unimplemented"); }

auto Platform::MacMusicAppGetVolume() -> int {
  Log("MacMusicAppGetVolume() unimplemented");
  return 0;
}

void Platform::MacMusicAppSetVolume(int volume) {
  Log("MacMusicAppSetVolume() unimplemented");
}

void Platform::MacMusicAppGetLibrarySource() {
  Log("MacMusicAppGetLibrarySource() unimplemented");
}

void Platform::MacMusicAppStop() { Log("MacMusicAppStop() unimplemented"); }

auto Platform::MacMusicAppPlayPlaylist(const std::string& playlist) -> bool {
  Log("MacMusicAppPlayPlaylist() unimplemented");
  return false;
}
auto Platform::MacMusicAppGetPlaylists() -> std::list<std::string> {
  Log("MacMusicAppGetPlaylists() unimplemented");
  return std::list<std::string>();
}

void Platform::StartListeningForWiiRemotes() {
  Log("StartListeningForWiiRemotes() unimplemented");
}

void Platform::StopListeningForWiiRemotes() {
  Log("StopListeningForWiiRemotes() unimplemented");
}

void Platform::SetCurrentThreadName(const std::string& name) {
  // Currently we leave the main thread alone, otherwise we show up as
  // "BallisticaMainThread" under "top" on linux (should check other platforms).
  if (InMainThread()) {
    return;
  }
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS
  pthread_setname_np(name.c_str());
#elif BA_OSTYPE_LINUX || BA_OSTYPE_ANDROID
  pthread_setname_np(pthread_self(), name.c_str());
#endif
}

void Platform::Unlink(const char* path) {
  // This covers all but windows.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  unlink(path);
#endif
}

auto Platform::AbsPath(const std::string& path, std::string* outpath) -> bool {
  // Ensure all implementations fail if the file does not exist.
  if (!FilePathExists(path)) {
    return false;
  }
  return DoAbsPath(path, outpath);
}

auto Platform::DoAbsPath(const std::string& path, std::string* outpath)
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

auto Platform::IsEventPushMode() -> bool { return false; }

auto Platform::GetDisplayResolution(int* x, int* y) -> bool { return false; }

void Platform::CloseSocket(int socket) {
// This covers all but windows.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  close(socket);
#endif
}

auto Platform::SocketPair(int domain, int type, int protocol, int socks[2])
    -> int {
  // This covers all but windows.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return socketpair(domain, type, protocol, socks);
#endif
}

auto Platform::GetBroadcastAddrs() -> std::vector<uint32_t> {
// This covers all but windows.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  std::vector<uint32_t> addrs;
  struct ifaddrs* ifaddr;
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

auto Platform::SetSocketNonBlocking(int sd) -> bool {
// This covers all but windows.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  int result = fcntl(sd, F_SETFL, O_NONBLOCK);
  if (result != 0) {
    Log("Error setting non-blocking socket: "
        + g_platform->GetSocketErrorString());
    return false;
  }
  return true;
#endif
}

auto Platform::GetTicks() -> millisecs_t {
  return GetCurrentMilliseconds() - starttime_;
}

auto Platform::GetPlatformName() -> std::string {
  throw Exception("UNIMPLEMENTED");
}

auto Platform::GetSubplatformName() -> std::string {
  // This doesnt always have to be set.
  return "";
}

auto Platform::ContainsPythonDist() -> bool { return false; }

#pragma mark Stack Traces

#if BA_ENABLE_EXECINFO_BACKTRACES

// Stack traces using the functionality in execinfo.h
class PlatformStackTraceExecInfo : public PlatformStackTrace {
 public:
  static constexpr int kMaxStackLevels = 64;

  // The stack trace should capture the stack state immediately upon
  // construction but should do the bare minimum amount of work to store it. Any
  // expensive operations such as symbolification should be deferred until
  // GetDescription().
  PlatformStackTraceExecInfo() { nsize_ = backtrace(array_, kMaxStackLevels); }

  auto GetDescription() noexcept -> std::string override {
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

  auto copy() const noexcept -> PlatformStackTrace* override {
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

auto Platform::GetStackTrace() -> PlatformStackTrace* {
// Our default handler here supports execinfo backtraces where available
// and gives nothing elsewhere.
#if BA_ENABLE_EXECINFO_BACKTRACES
  return new PlatformStackTraceExecInfo();
#else
  return nullptr;
#endif
}

void Platform::RequestPermission(Permission p) {
  // No-op.
}

auto Platform::HavePermission(Permission p) -> bool {
  // Its assumed everything is accessible unless we override saying no.
  return true;
}

#if !BA_OSTYPE_WINDOWS
static void HandleSIGINT(int s) {
  if (g_game) {
    g_game->PushInterruptSignalCall();
  } else {
    Log("SigInt handler called before g_game exists.");
  }
}
#endif

void Platform::SetupInterruptHandling() {
  // For non-windows platforms, set up posix-y SIGINT handling.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  struct sigaction handler {};
  handler.sa_handler = HandleSIGINT;
  sigemptyset(&handler.sa_mask);
  handler.sa_flags = 0;
  sigaction(SIGINT, &handler, nullptr);
#endif
}

void Platform::GetCursorPosition(float* x, float* y) {
  assert(x && y);

  // By default, just use our latest event-delivered cursor position;
  // this should work everywhere though perhaps might not be most optimal.
  if (g_input == nullptr) {
    *x = 0.0f;
    *y = 0.0f;
    return;
  }
  *x = g_input->cursor_pos_x();
  *y = g_input->cursor_pos_y();
}
auto Platform::SetDebugKey(const std::string& key, const std::string& value)
    -> void {}

auto Platform::HandleDebugLog(const std::string& msg) -> void {}

auto Platform::GetCurrentMilliseconds() -> millisecs_t {
  return std::chrono::time_point_cast<std::chrono::milliseconds>(
             std::chrono::steady_clock::now())
      .time_since_epoch()
      .count();
}

auto Platform::GetCurrentSeconds() -> int64_t {
  return std::chrono::time_point_cast<std::chrono::seconds>(
             std::chrono::steady_clock::now())
      .time_since_epoch()
      .count();
}

auto Platform::ClipboardIsSupported() -> bool {
  // We only call our actual virtual function once.
  if (!have_clipboard_is_supported_) {
    clipboard_is_supported_ = DoClipboardIsSupported();
    have_clipboard_is_supported_ = true;
  }
  return clipboard_is_supported_;
}

auto Platform::ClipboardHasText() -> bool {
  // If subplatform says they don't support clipboards, don't even ask.
  if (!ClipboardIsSupported()) {
    return false;
  }
  return DoClipboardHasText();
}

auto Platform::ClipboardSetText(const std::string& text) -> void {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardSetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  DoClipboardSetText(text);
}

auto Platform::ClipboardGetText() -> std::string {
  // If subplatform says they don't support clipboards, this is an error.
  if (!ClipboardIsSupported()) {
    throw Exception("ClipboardGetText called with no clipboard support.",
                    PyExcType::kRuntime);
  }
  return DoClipboardGetText();
}

auto Platform::DoClipboardIsSupported() -> bool {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  return true;
#else
  return false;
#endif
}

auto Platform::DoClipboardHasText() -> bool {
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

auto Platform::DoClipboardSetText(const std::string& text) -> void {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  SDL_SetClipboardText(text.c_str());
#else
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
#endif
}

auto Platform::DoClipboardGetText() -> std::string {
  // Go through SDL functionality on SDL based platforms;
  // otherwise default to no clipboard.
#if BA_SDL2_BUILD && !BA_OSTYPE_IOS_TVOS
  char* out = SDL_GetClipboardText();
  if (out == nullptr) {
    throw Exception("Error fetching clipboard contents.", PyExcType::kRuntime);
  }
  return out;
#else
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
  return "";
#endif
}

}  // namespace ballistica
