// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_COMMON_H_
#define BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_COMMON_H_

#ifdef __cplusplus

#include <cstdint>
#include <cstdlib>

// Universal sanity checks.
#if !BA_DEBUG_BUILD
#ifndef NDEBUG
#error NDEBUG should be defined for all non-debug builds.
#endif  // NDEBUG
#endif  // !BA_DEBUG_BUILD

// This header should be included at the very END of each platform config
// header that will be directly used by a build.
namespace ballistica {

// Default definitions for various things. Per-platform configs
// can override any of these before this is included.

// Monolithic builds consist of a single binary that inits and manages
// Python itself, as opposed to modular builds which are made up of Python
// binary modules which are run under a standard Python runtime. This will
// be 0 for both modular (.so) builds of the engine as well as for static
// libraries such as baplus intended to be linked to either version.
#ifndef BA_MONOLITHIC_BUILD
#define BA_MONOLITHIC_BUILD 1
#endif

#ifndef BA_STAT
#define BA_STAT stat
#endif

#ifndef BA_OSTYPE_WINDOWS
#define BA_OSTYPE_WINDOWS 0
#endif

// Are we building for macOS?
#ifndef BA_OSTYPE_MACOS
#define BA_OSTYPE_MACOS 0
#endif

// Are we building for iOS? (also covers iPadOS)
#ifndef BA_OSTYPE_IOS
#define BA_OSTYPE_IOS 0
#endif

// Are we building for tvOS?
#ifndef BA_OSTYPE_TVOS
#define BA_OSTYPE_TVOS 0
#endif

// Are we building for iOS OR tvOS?
#ifndef BA_OSTYPE_IOS_TVOS
#define BA_OSTYPE_IOS_TVOS 0
#endif

// Are we building for Android?
#ifndef BA_OSTYPE_ANDROID
#define BA_OSTYPE_ANDROID 0
#endif

// Are we building for Linux?
#ifndef BA_OSTYPE_LINUX
#define BA_OSTYPE_LINUX 0
#endif

// On Windows, are we built as a console app (vs a gui app)?
#ifndef BA_WINDOWS_CONSOLE_BUILD
#define BA_WINDOWS_CONSOLE_BUILD 1
#endif

// Does this build support only headless mode?
#ifndef BA_HEADLESS_BUILD
#define BA_HEADLESS_BUILD 0
#endif

// Are we building via an XCode project?
#ifndef BA_XCODE_BUILD
#define BA_XCODE_BUILD 0
#endif

// Does this build use SDL 1.x? (old mac only)
#ifndef BA_SDL_BUILD
#define BA_SDL_BUILD 0
#endif

// Does this build use SDL 2.x?
// #ifndef BA_SDL2_BUILD
// #define BA_SDL2_BUILD 0
// #endif

// Does this build use our 'min-sdl' types?
// (basic SDL types we define ourselves; no actual SDL dependency)
#ifndef BA_MINSDL_BUILD
#define BA_MINSDL_BUILD 0
#endif

// Is this a debug build?
#ifndef BA_DEBUG_BUILD
#define BA_DEBUG_BUILD 0
#endif

// Is this a test build?
#ifndef BA_TEST_BUILD
#define BA_TEST_BUILD 0
#endif

// Does this build include its own full Python distribution?
// Builds such as linux may use rely on system provided ones.
#ifndef BA_CONTAINS_PYTHON_DIST
#define BA_CONTAINS_PYTHON_DIST 0
#endif

#ifndef BA_ENABLE_SDL_JOYSTICKS
#define BA_ENABLE_SDL_JOYSTICKS 0
#endif

#ifndef BA_USE_STORE_KIT
#define BA_USE_STORE_KIT 0
#endif

#ifndef BA_USE_GAME_CENTER
#define BA_USE_GAME_CENTER 0
#endif

#ifndef BA_USE_GOOGLE_PLAY_GAME_SERVICES
#define BA_USE_GOOGLE_PLAY_GAME_SERVICES 0
#endif

#ifndef BA_PLATFORM_STRING
#error platform string undefined
#endif

#ifndef BA_ENABLE_STDIO_CONSOLE
#define BA_ENABLE_STDIO_CONSOLE 0
#endif

#ifndef BA_ENABLE_OS_FONT_RENDERING
#define BA_ENABLE_OS_FONT_RENDERING 0
#endif

// Does this build support vr mode? (does not mean vr mode is always on)
#ifndef BA_VR_BUILD
#define BA_VR_BUILD 0
#endif

// Is this the Google VR build? (Cardboard/Daydream)
#ifndef BA_CARDBOARD_BUILD
#define BA_CARDBOARD_BUILD 0
#endif

#ifndef BA_GEARVR_BUILD
#define BA_GEARVR_BUILD 0
#endif

#ifndef BA_RIFT_BUILD
#define BA_RIFT_BUILD 0
#endif

#ifndef BA_AMAZON_BUILD
#define BA_AMAZON_BUILD 0
#endif

#ifndef BA_STEAM_BUILD
#define BA_STEAM_BUILD 0
#endif

#ifndef BA_GOOGLE_BUILD
#define BA_GOOGLE_BUILD 0
#endif

#ifndef BA_DEMO_BUILD
#define BA_DEMO_BUILD 0
#endif

#ifndef BA_ARCADE_BUILD
#define BA_ARCADE_BUILD 0
#endif

#ifndef BA_SOCKET_POLL_FD
#define BA_SOCKET_POLL_FD pollfd
#endif

#ifndef BA_SOCKET_ERROR_RETURN
#define BA_SOCKET_ERROR_RETURN -1
#endif

#ifndef BA_SOCKET_POLL
#define BA_SOCKET_POLL poll
#endif

#ifndef BA_SOCKET_SEND_DATA_TYPE
#define BA_SOCKET_SEND_DATA_TYPE uint8_t
#endif

#ifndef BA_SOCKET_SETSOCKOPT_VAL_TYPE
#define BA_SOCKET_SETSOCKOPT_VAL_TYPE int
#endif

#ifndef BA_SOCKET_SEND_LENGTH_TYPE
#define BA_SOCKET_SEND_LENGTH_TYPE size_t
#endif

typedef BA_SOCKET_SEND_DATA_TYPE socket_send_data_t;
typedef BA_SOCKET_SEND_LENGTH_TYPE socket_send_length_t;

bool InlineDebugExplicitBool(bool val);

// Little hack so that we avoid 'value is always true/false' and
// 'code will never/always be run' type warnings when using these in debug
// builds.
#if BA_DEBUG_BUILD
#define EXPBOOL_(val) InlineDebugExplicitBool(val)
#else
#define EXPBOOL_(val) val
#endif

// We define a compile-time value g_buildconfig which contains the same config
// values as our config #defines. We should migrate towards using these values
// whenever possible instead of #if blocks, which should improve support for
// code introspection/refactoring tools and type safety while still optimizing
// out just as nicely as #ifs. (though perhaps should verify that).
// In an ideal world, we should never use #ifs/#ifdefs outside of the platform
// subdir or skipping entire files (header guards, gui stuff on headless builds,
// etc.)
class BuildConfig {
 public:
  const char* platform_string() const { return BA_PLATFORM_STRING; }
  bool debug_build() const { return EXPBOOL_(BA_DEBUG_BUILD); }
  bool test_build() const { return EXPBOOL_(BA_TEST_BUILD); }
  bool headless_build() const { return EXPBOOL_(BA_HEADLESS_BUILD); }
  bool monolithic_build() const { return EXPBOOL_(BA_MONOLITHIC_BUILD); }
  bool windows_console_build() const {
    return EXPBOOL_(BA_WINDOWS_CONSOLE_BUILD);
  }

  bool sdl_build() const { return EXPBOOL_(BA_SDL_BUILD); }
  // bool sdl2_build() const { return EXPBOOL_(BA_SDL2_BUILD); }
  bool minsdl_build() const { return EXPBOOL_(BA_MINSDL_BUILD); }
  bool enable_sdl_joysticks() const {
    return EXPBOOL_(BA_ENABLE_SDL_JOYSTICKS);
  }

  bool ostype_windows() const { return EXPBOOL_(BA_OSTYPE_WINDOWS); }
  bool ostype_macos() const { return EXPBOOL_(BA_OSTYPE_MACOS); }
  bool ostype_ios() const { return EXPBOOL_(BA_OSTYPE_IOS); }
  bool ostype_tvos() const { return EXPBOOL_(BA_OSTYPE_TVOS); }
  bool ostype_ios_tvos() const { return EXPBOOL_(BA_OSTYPE_IOS_TVOS); }
  bool ostype_android() const { return EXPBOOL_(BA_OSTYPE_ANDROID); }
  bool ostype_linux() const { return EXPBOOL_(BA_OSTYPE_LINUX); }

  bool xcode_build() const { return EXPBOOL_(BA_XCODE_BUILD); }
  bool vr_build() const { return EXPBOOL_(BA_VR_BUILD); }
  bool cardboard_build() const { return EXPBOOL_(BA_CARDBOARD_BUILD); }
  bool gearvr_build() const { return EXPBOOL_(BA_GEARVR_BUILD); }
  bool rift_build() const { return EXPBOOL_(BA_RIFT_BUILD); }
  bool amazon_build() const { return EXPBOOL_(BA_AMAZON_BUILD); }
  bool google_build() const { return EXPBOOL_(BA_GOOGLE_BUILD); }
  bool demo_build() const { return EXPBOOL_(BA_DEMO_BUILD); }
  bool arcade_build() const { return EXPBOOL_(BA_ARCADE_BUILD); }
  bool steam_build() const { return EXPBOOL_(BA_STEAM_BUILD); }
  bool contains_python_dist() const {
    return EXPBOOL_(BA_CONTAINS_PYTHON_DIST);
  }
  bool use_store_kit() const { return EXPBOOL_(BA_USE_STORE_KIT); }
  bool use_google_play_game_services() const {
    return EXPBOOL_(BA_USE_GOOGLE_PLAY_GAME_SERVICES);
  }
  bool use_game_center() const { return EXPBOOL_(BA_USE_GAME_CENTER); }
  bool enable_stdio_console() const {
    return EXPBOOL_(BA_ENABLE_STDIO_CONSOLE);
  }
  bool enable_os_font_rendering() const {
    return EXPBOOL_(BA_ENABLE_OS_FONT_RENDERING);
  }
};

#undef EXPBOOL_

constexpr BuildConfig g_buildconfig;

}  // namespace ballistica

#endif  // __cplusplus

#define BA_HAVE_CONFIG

#endif  // BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_COMMON_H_
