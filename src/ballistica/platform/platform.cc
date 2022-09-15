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
#include <unistd.h>
#endif

#include <csignal>

#include "ballistica/app/app_flavor.h"
#include "ballistica/core/thread.h"
#include "ballistica/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/camera.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/graphics/mesh/sprite_mesh.h"
#include "ballistica/graphics/vr_graphics.h"
#include "ballistica/input/input.h"
#include "ballistica/logic/friend_score_set.h"
#include "ballistica/logic/logic.h"
#include "ballistica/networking/networking_sys.h"
#include "ballistica/platform/sdl/sdl_app.h"
#include "ballistica/platform/stdio_console.h"
#include "ballistica/python/python.h"

#if BA_HEADLESS_BUILD
#include "ballistica/app/app_flavor_headless.h"
#endif

#if BA_VR_BUILD
#include "ballistica/app/app_flavor_vr.h"
#endif

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
  assert(platform->ran_base_post_init_);
  return platform;
}

Platform::Platform() : starttime_(GetCurrentMilliseconds()) {}

auto Platform::PostInit() -> void {
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

Platform::~Platform() = default;

auto Platform::GetLegacyDeviceUUID() -> const std::string& {
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

auto Platform::GetDeviceV1AccountUUIDPrefix() -> std::string {
  Log(LogLevel::kError, "GetDeviceV1AccountUUIDPrefix() unimplemented");
  return "u";
}

auto Platform::GetRealLegacyDeviceUUID(std::string* uuid) -> bool {
  return false;
}

auto Platform::GenerateUUID() -> std::string {
  throw Exception("GenerateUUID() unimplemented");
}

auto Platform::GetPublicDeviceUUID() -> std::string {
  assert(g_python);
  if (public_device_uuid_.empty()) {
    std::list<std::string> inputs{GetDeviceUUIDInputs()};

    // This UUID is supposed to change periodically, so let's plug in
    // some stuff to enforce that.
    inputs.emplace_back(GetOSVersionString());
    inputs.emplace_back(kAppVersion);
    inputs.emplace_back("kerploople");
    auto gil{Python::ScopedInterpreterLock()};
    auto pylist{g_python->StringList(inputs)};
    auto args{g_python->SingleMemberTuple(pylist)};
    auto result = g_python->obj(Python::ObjID::kHashStringsCall).Call(args);
    assert(result.UnicodeCheck());
    public_device_uuid_ = result.Str();
  }
  return public_device_uuid_;
}

auto Platform::GetDeviceUUIDInputs() -> std::list<std::string> {
  throw Exception("GetDeviceUUIDInputs unimplemented");
}

auto Platform::GetDefaultConfigDirectory() -> std::string {
  std::string config_dir;
  // As a default, look for a HOME env var and use that if present
  // this will cover linux and command-line macOS.
  char* home = getenv("HOME");
  if (home) {
    config_dir = std::string(home) + "/.ballisticacore";
  } else {
    printf("GetDefaultConfigDirectory: can't get env var \"HOME\"\n");
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
    if (result != 1)
      Log(LogLevel::kError, "unable to write low level config file.");
    fclose(f);
  } else {
    Log(LogLevel::kError, "unable to open low level config file for writing.");
  }
}

auto Platform::GetUserPythonDirectory() -> std::string {
  // Make sure it exists the first time we run.
  if (!attempted_to_make_user_scripts_dir_) {
    user_scripts_dir_ = DoGetUserPythonDirectory();

    // Attempt to make it. (it's ok if this fails)
    MakeDir(user_scripts_dir_, true);
    attempted_to_make_user_scripts_dir_ = true;
  }
  return user_scripts_dir_;
}

auto Platform::GetVolatileDataDirectory() -> std::string {
  if (!made_volatile_data_dir_) {
    volatile_data_dir_ = GetDefaultVolatileDataDirectory();
    MakeDir(volatile_data_dir_);
    made_volatile_data_dir_ = true;
  }
  return volatile_data_dir_;
}

auto Platform::GetDefaultVolatileDataDirectory() -> std::string {
  // By default, stuff this in a subdir under our config dir.
  return GetConfigDirectory() + BA_DIRSLASH + "vdata";
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
      Log(LogLevel::kInfo, "Using custom app Python path: '"
                               + (GetUserPythonDirectory() + BA_DIRSLASH + "sys"
                                  + BA_DIRSLASH + kAppVersion)
                               + "'.");

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
  // This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return rename(oldname, newname);
#endif
}

auto Platform::Remove(const char* path) -> int {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return remove(path);
#endif
}

// stat() supporting UTF8 strings.
auto Platform::Stat(const char* path, struct BA_STAT* buffer) -> int {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return stat(path, buffer);
#endif
}

// fopen() supporting UTF8 strings.
auto Platform::FOpen(const char* path, const char* mode) -> FILE* {
// This default implementation covers non-windows platforms.
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
  // By default this is simply errno.
  return errno;
}

auto Platform::GetErrnoString() -> std::string {
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

// Return the ballisticacore config dir
// This does not vary across versions.
auto Platform::GetConfigDirectory() -> std::string {
  // Make sure args have been handled since we use them.
  assert(g_app->args_handled);

  if (!have_config_dir_) {
    // If the user provided cfgdir as an arg.
    if (!g_app->user_config_dir.empty()) {
      config_dir_ = g_app->user_config_dir;
    } else {
      config_dir_ = GetDefaultConfigDirectory();
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

    // Non-quiet call should always result in the directory existing.
    // (or an exception should have been raised)
    assert(quiet || FilePathExists(dir));
  }
}

auto Platform::AndroidGetExternalFilesDir() -> std::string {
  throw Exception("AndroidGetExternalFilesDir() unimplemented");
}

auto Platform::DoGetUserPythonDirectory() -> std::string {
  return GetConfigDirectory() + BA_DIRSLASH + "mods";
}

void Platform::DoMakeDir(const std::string& dir, bool quiet) {
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

auto Platform::GetLocale() -> std::string {
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

auto Platform::GetDeviceName() -> std::string {
  assert(ran_base_post_init_);
  return device_name_;
}

auto Platform::DoGetDeviceName() -> std::string {
  // Just go with hostname as a decent default.
  char nbuffer[64];
  int ret = gethostname(nbuffer, sizeof(nbuffer));
  if (ret == 0) {
    nbuffer[sizeof(nbuffer) - 1] = 0;  // Make sure its terminated.
    return nbuffer;
  }
  return "Untitled Device";
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

#pragma clang diagnostic push
#pragma ide diagnostic ignored "NullDereferences"

static void HandleArgs(int argc, char** argv) {
  assert(!g_app->args_handled);
  g_app->args_handled = true;

  // If there's just one arg and it's "--version", return the version.
  if (argc == 2 && !strcmp(argv[1], "--version")) {
    printf("Ballistica %s build %d\n", kAppVersion, kAppBuildNumber);
    fflush(stdout);
    exit(0);
  }
  int dummyval{};
  for (int i = 1; i < argc; ++i) {
    // In our rift build, a '-2d' arg causes us to run in regular 2d mode.
    if (g_buildconfig.rift_build() && !strcmp(argv[i], "-2d")) {
      g_app->vr_mode = false;
    } else if (!strcmp(argv[i], "-exec")) {
      if (i + 1 < argc) {
        g_app->exec_command = argv[i + 1];
      } else {
        printf("%s", "Error: expected arg after -exec\n");
        fflush(stdout);
        exit(-1);
      }
    } else if (!strcmp(argv[i], "--crash")) {
      int* invalid_ptr{&dummyval};

      // A bit of obfuscation to try and keep linters quiet.
      if (explicit_bool(true)) {
        invalid_ptr = nullptr;
      }
      if (explicit_bool(true)) {
        *invalid_ptr = 1;
      }
    } else if (!strcmp(argv[i], "-cfgdir")) {
      if (i + 1 < argc) {
        g_app->user_config_dir = argv[i + 1];

        // Need to convert this to an abs path since we chdir soon.
        bool success =
            g_platform->AbsPath(argv[i + 1], &g_app->user_config_dir);
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
        Log(LogLevel::kError, "Expected arg after -cfgdir.");
        exit(-1);
      }
    }
  }
#pragma clang diagnostic pop

  // In Android's case we have to pull our exec arg from the java/kotlin layer.
  if (g_buildconfig.ostype_android()) {
    g_app->exec_command = g_platform->GetAndroidExecArg();
  }

  // TEMP/HACK: hard code launch args.
  if (explicit_bool(false)) {
    if (g_buildconfig.ostype_android()) {
      g_app->exec_command = "import ba.internal; ba.internal.run_stress_test()";
    }
  }
}

auto Platform::CreateAppFlavor() -> AppFlavor* {
  assert(g_app);
  assert(InMainThread());
  assert(g_main_thread);

  // Hmm do these belong here?...
  HandleArgs(g_app->argc, g_app->argv);

// TEMP - need to init sdl on our legacy mac build even though its not
// technically an SDL app. Kill this once the old mac build is gone.
#if BA_LEGACY_MACOS_BUILD
  SDLApp::InitSDL();
#endif

  AppFlavor* app_flavor{};

#if BA_HEADLESS_BUILD
  app_flavor = new AppFlavorHeadless(g_main_thread);
#elif BA_RIFT_BUILD
  // Rift build can spin up in either VR or regular mode.
  if (g_app->vr_mode) {
    app_flavor = new AppFlavorVR(g_main_thread);
  } else {
    app_flavor = new SDLApp(g_main_thread);
  }
#elif BA_CARDBOARD_BUILD
  app_flavor = new AppFlavorVR(g_main_thread);
#elif BA_SDL_BUILD
  app_flavor = new SDLApp(g_main_thread);
#else
  app_flavor = new AppFlavor(g_main_thread);
#endif

  assert(app_flavor);
  app_flavor->PostInit();
  return app_flavor;
}

auto Platform::CreateGraphics() -> Graphics* {
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

void Platform::WillExitMain(bool errored) {}

auto Platform::GetUIScale() -> UIScale {
  // Handles mac/pc/linux cases.
  return UIScale::kLarge;
}

void Platform::DisplayLog(const std::string& name, LogLevel level,
                          const std::string& msg) {
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
// This default implementation covers non-windows platforms.
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

auto Platform::GetIsStdinATerminal() -> bool {
// This covers non-windows cases.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  return static_cast<bool>(isatty(fileno(stdin)));
#endif
}

auto Platform::GetOSVersionString() -> std::string { return ""; }

auto Platform::GetUserAgentString() -> std::string {
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

  std::string out{std::string("BallisticaCore ") + kAppVersion + subplatform
                  + " (" + std::to_string(kAppBuildNumber) + ") ("
                  + g_buildconfig.platform_string() + version + "; " + device
                  + "; " + GetLocale() + ")"};

  // This gets shipped to various places which might choke on fancy unicode
  // characters, so let's limit to simple ascii.
  out = Utils::StripNonAsciiFromUTF8(out);

  return out;
}

auto Platform::GetCWD() -> std::string {
// This default implementation covers non-windows platforms.
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

void Platform::OnAppStart() {}

auto Platform::ConvertIncomingLeaderboardScore(
    const std::string& leaderboard_id, int score) -> int {
  return score;
}

void Platform::GetFriendScores(const std::string& game,
                               const std::string& game_version, void* data) {
  // As a default, just fail gracefully.
  Log(LogLevel::kError, "FIXME: GetFriendScores unimplemented");
  g_logic->PushFriendScoreSetCall(FriendScoreSet(false, data));
}

void Platform::SubmitScore(const std::string& game, const std::string& version,
                           int64_t score) {
  Log(LogLevel::kError, "FIXME: SubmitScore() unimplemented");
}

void Platform::ReportAchievement(const std::string& achievement) {}

auto Platform::HaveLeaderboard(const std::string& game,
                               const std::string& config) -> bool {
  return false;
}

void Platform::EditText(const std::string& title, const std::string& value,
                        int max_chars) {
  Log(LogLevel::kError, "FIXME: EditText() unimplemented");
}

void Platform::ShowOnlineScoreUI(const std::string& show,
                                 const std::string& game,
                                 const std::string& game_version) {
  Log(LogLevel::kError, "FIXME: ShowOnlineScoreUI() unimplemented");
}

void Platform::Purchase(const std::string& item) {
  // Just print 'unavailable' by default.
  g_python->PushObjCall(Python::ObjID::kUnavailableMessageCall);
}

void Platform::RestorePurchases() {
  Log(LogLevel::kError, "RestorePurchases() unimplemented");
}

void Platform::AndroidSetResString(const std::string& res) {
  throw Exception();
}

void Platform::ApplyConfig() {}

void Platform::AndroidSynthesizeBackPress() {
  Log(LogLevel::kError, "AndroidSynthesizeBackPress() unimplemented");
}

void Platform::AndroidQuitActivity() {
  Log(LogLevel::kError, "AndroidQuitActivity() unimplemented");
}

auto Platform::GetDeviceV1AccountID() -> std::string {
  if (HeadlessMode()) {
    return "S-" + GetLegacyDeviceUUID();
  }

  // Everything else is just considered a 'local' account, though we may
  // give unique ids for unique builds..
  if (g_buildconfig.iircade_build()) {
    return "L-iRc" + GetLegacyDeviceUUID();
  }
  return "L-" + GetLegacyDeviceUUID();
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

auto Platform::NewAutoReleasePool() -> void* { throw Exception(); }

void Platform::DrainAutoReleasePool(void* pool) { throw Exception(); }

void Platform::OpenURL(const std::string& url) {
  // Can't open URLs in VR - just tell the logic thread to show the url.
  if (IsVRMode()) {
    g_logic->PushShowURLCall(url);
    return;
  }

  // Otherwise fall back to our platform-specific handler.
  g_platform->DoOpenURL(url);
}

void Platform::DoOpenURL(const std::string& url) {
  Log(LogLevel::kError, "DoOpenURL unimplemented on this platform.");
}

void Platform::ResetAchievements() {
  Log(LogLevel::kError, "ResetAchievements() unimplemented");
}

void Platform::GameCenterLogin() { throw Exception(); }

void Platform::PurchaseAck(const std::string& purchase,
                           const std::string& order_id) {
  Log(LogLevel::kError, "PurchaseAck() unimplemented");
}

void Platform::RunEvents() {}

auto Platform::GetMemUsageInfo() -> std::string { return "0,0,0"; }

void Platform::OnAppPause() {}
void Platform::OnAppResume() {}

void Platform::MusicPlayerPlay(PyObject* target) {
  Log(LogLevel::kError, "MusicPlayerPlay() unimplemented on this platform");
}
void Platform::MusicPlayerStop() {
  Log(LogLevel::kError, "MusicPlayerStop() unimplemented on this platform");
}
void Platform::MusicPlayerShutdown() {
  Log(LogLevel::kError, "MusicPlayerShutdown() unimplemented on this platform");
}

void Platform::MusicPlayerSetVolume(float volume) {
  Log(LogLevel::kError,
      "MusicPlayerSetVolume() unimplemented on this platform");
}

auto Platform::IsOSPlayingMusic() -> bool { return false; }

void Platform::AndroidShowAppInvite(const std::string& title,
                                    const std::string& message,
                                    const std::string& code) {
  Log(LogLevel::kError, "AndroidShowAppInvite() unimplemented");
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
  Log(LogLevel::kError, "AndroidRefreshFile() unimplemented");
}

void Platform::ShowAd(const std::string& purpose) {
  Log(LogLevel::kError, "ShowAd() unimplemented");
}

auto Platform::GetHasAds() -> bool { return false; }

auto Platform::GetHasVideoAds() -> bool {
  // By default we assume we have this anywhere we have ads.
  return GetHasAds();
}

void Platform::SignInV1(const std::string& account_type) {
  Log(LogLevel::kError, "SignInV1() unimplemented");
}

void Platform::V1LoginDidChange() {
  // Default is no-op.
}

void Platform::SignOutV1() {
  Log(LogLevel::kError, "SignOutV1() unimplemented");
}

void Platform::AndroidShowWifiSettings() {
  Log(LogLevel::kError, "AndroidShowWifiSettings() unimplemented");
}

void Platform::SetHardwareCursorVisible(bool visible) {
// FIXME: Forward this to app?..
#if BA_SDL_BUILD
  SDL_ShowCursor(visible ? SDL_ENABLE : SDL_DISABLE);
#endif
}

auto Platform::QuitApp() -> void { exit(g_app->return_value); }

auto Platform::OpenFileExternally(const std::string& path) -> void {
  Log(LogLevel::kError, "OpenFileExternally() unimplemented");
}

auto Platform::OpenDirExternally(const std::string& path) -> void {
  Log(LogLevel::kError, "OpenDirExternally() unimplemented");
}

auto Platform::MacMusicAppInit() -> void {
  Log(LogLevel::kError, "MacMusicAppInit() unimplemented");
}

auto Platform::MacMusicAppGetVolume() -> int {
  Log(LogLevel::kError, "MacMusicAppGetVolume() unimplemented");
  return 0;
}

auto Platform::MacMusicAppSetVolume(int volume) -> void {
  Log(LogLevel::kError, "MacMusicAppSetVolume() unimplemented");
}

auto Platform::MacMusicAppGetLibrarySource() -> void {
  Log(LogLevel::kError, "MacMusicAppGetLibrarySource() unimplemented");
}

auto Platform::MacMusicAppStop() -> void {
  Log(LogLevel::kError, "MacMusicAppStop() unimplemented");
}

auto Platform::MacMusicAppPlayPlaylist(const std::string& playlist) -> bool {
  Log(LogLevel::kError, "MacMusicAppPlayPlaylist() unimplemented");
  return false;
}
auto Platform::MacMusicAppGetPlaylists() -> std::list<std::string> {
  Log(LogLevel::kError, "MacMusicAppGetPlaylists() unimplemented");
  return {};
}

auto Platform::SetCurrentThreadName(const std::string& name) -> void {
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

auto Platform::Unlink(const char* path) -> void {
// This default implementation covers non-windows platforms.
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

auto Platform::CloseSocket(int socket) -> void {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  close(socket);
#endif
}

auto Platform::GetBroadcastAddrs() -> std::vector<uint32_t> {
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

auto Platform::SetSocketNonBlocking(int sd) -> bool {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  int result = fcntl(sd, F_SETFL, O_NONBLOCK);
  if (result != 0) {
    Log(LogLevel::kError, "Error setting non-blocking socket: "
                              + g_platform->GetSocketErrorString());
    return false;
  }
  return true;
#endif
}

auto Platform::GetTicks() const -> millisecs_t {
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
  if (g_logic) {
    g_logic->PushInterruptSignalCall();
  } else {
    Log(LogLevel::kError, "SigInt handler called before g_logic exists.");
  }
}
#endif

void Platform::SetupInterruptHandling() {
// This default implementation covers non-windows platforms.
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
  std::string out_s{out};
  SDL_free(out);
  return out_s;
#else
  // Shouldn't get here since we default to no clipboard support.
  FatalError("Shouldn't get here.");
  return "";
#endif
}

}  // namespace ballistica
