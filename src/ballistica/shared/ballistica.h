// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BALLISTICA_H_
#define BALLISTICA_SHARED_BALLISTICA_H_

#include <cassert>
#include <cstdio>
#include <string>
#include <type_traits>

// Try to ensure they're providing proper config stuff.
#ifndef BA_HAVE_CONFIG
#error ballistica platform config has not been defined!
#endif

// Predeclare a few global namespace things (just enough to pass some
// pointers around without requiring a bunch of library/system headers).
typedef struct _object PyObject;
typedef struct _typeobject PyTypeObject;
typedef struct _ts PyThreadState;
struct PyMethodDef;
struct sockaddr_storage;

#if BA_SDL_BUILD || BA_MINSDL_BUILD
union SDL_Event;
struct SDL_Keysym;
typedef struct _SDL_Joystick SDL_Joystick;
#endif

// Predeclare types from other feature sets that we use.
namespace ballistica::core {
class CoreConfig;
}

// Here we define things for our top level 'shared' namespace.
namespace ballistica {

// Predeclare types we use throughout our FeatureSet so most headers can get
// away with just including this header.
struct cJSON;
class EventLoop;
class Exception;
class FeatureSetNativeComponent;
class JsonDict;
class Matrix44f;
class NativeStackTrace;
class Object;
class Python;
class PythonRef;
class PythonCommand;
class PythonObjectSetBase;
class PythonModuleBuilder;
class Rect;
class Runnable;
class SockAddr;
class Timer;
class TimerList;
class Utils;
class Vector2f;
class Vector3f;
class Vector4f;
class FatalErrorHandling;

// Used internally for time values.
typedef double seconds_t;
typedef int64_t millisecs_t;
typedef int64_t microsecs_t;

// BA_EXPORT_PYTHON_ENUM
/// Types of input a controller can send to the game.
enum class InputType : uint8_t {
  kUpDown = 2,
  kLeftRight,
  kJumpPress,
  kJumpRelease,
  kPunchPress,
  kPunchRelease,
  kBombPress,
  kBombRelease,
  kPickUpPress,
  kPickUpRelease,
  kRun,
  kFlyPress,
  kFlyRelease,
  kStartPress,
  kStartRelease,
  kHoldPositionPress,
  kHoldPositionRelease,
  kLeftPress,
  kLeftRelease,
  kRightPress,
  kRightRelease,
  kUpPress,
  kUpRelease,
  kDownPress,
  kDownRelease,
  kLast  // Sentinel
};

// BA_EXPORT_PYTHON_ENUM
/// Types of quit behavior that can be requested from the app.
///
/// 'soft' may hide/reset the app but keep the process running, depending
///    on the platform (generally a thing on mobile).
///
/// 'back' is a variant of 'soft' which may give 'back-button-pressed'
///    behavior depending on the platform. (returning to some previous
///    activity instead of dumping to the home screen, etc.)
///
/// 'hard' leads to the process exiting. This generally should be avoided
///    on platforms such as mobile where apps are expected to keep running
///    until killed by the OS.
enum class QuitType : uint8_t {
  kSoft,
  kBack,
  kHard,
  kLast  // Sentinel.
};

typedef int64_t TimerMedium;

// BA_EXPORT_PYTHON_ENUM
/// The overall scale the UI is being rendered for. Note that this is
/// independent of pixel resolution. For example, a phone and a desktop PC
/// might render the game at similar pixel resolutions but the size they
/// display content at will vary significantly.
///
/// 'large' is used for devices such as desktop PCs where fine details can
///    be clearly seen. UI elements are generally smaller on the screen
///    and more content can be seen at once.
///
/// 'medium' is used for devices such as tablets, TVs, or VR headsets.
///    This mode strikes a balance between clean readability and amount of
///    content visible.
///
/// 'small' is used primarily for phones or other small devices where
///    content needs to be presented as large and clear in order to remain
///    readable from an average distance.
enum class UIScale : uint8_t {
  kSmall,
  kMedium,
  kLarge,
  kLast  // Sentinel.
};

// BA_EXPORT_PYTHON_ENUM
/// Permissions that can be requested from the OS.
enum class Permission : uint8_t {
  kStorage,
  kLast  // Sentinel.
};

// BA_EXPORT_PYTHON_ENUM
/// Special characters the game can print.
enum class SpecialChar : uint8_t {
  kDownArrow,
  kUpArrow,
  kLeftArrow,
  kRightArrow,
  kTopButton,
  kLeftButton,
  kRightButton,
  kBottomButton,
  kDelete,
  kShift,
  kBack,
  kLogoFlat,
  kRewindButton,
  kPlayPauseButton,
  kFastForwardButton,
  kDpadCenterButton,
  kPlayStationCrossButton,
  kPlayStationCircleButton,
  kPlayStationTriangleButton,
  kPlayStationSquareButton,
  kPlayButton,
  kPauseButton,
  kOuyaButtonO,
  kOuyaButtonU,
  kOuyaButtonY,
  kOuyaButtonA,
  kToken,
  kLogo,
  kTicket,
  kGooglePlayGamesLogo,
  kGameCenterLogo,
  kDiceButton1,
  kDiceButton2,
  kDiceButton3,
  kDiceButton4,
  kGameCircleLogo,
  kPartyIcon,
  kTestAccount,
  kTicketBacking,
  kTrophy1,
  kTrophy2,
  kTrophy3,
  kTrophy0a,
  kTrophy0b,
  kTrophy4,
  kLocalAccount,
  kExplodinaryLogo,
  kFlagUnitedStates,
  kFlagMexico,
  kFlagGermany,
  kFlagBrazil,
  kFlagRussia,
  kFlagChina,
  kFlagUnitedKingdom,
  kFlagCanada,
  kFlagIndia,
  kFlagJapan,
  kFlagFrance,
  kFlagIndonesia,
  kFlagItaly,
  kFlagSouthKorea,
  kFlagNetherlands,
  kFedora,
  kHal,
  kCrown,
  kYinYang,
  kEyeBall,
  kSkull,
  kHeart,
  kDragon,
  kHelmet,
  kMushroom,
  kNinjaStar,
  kVikingHelmet,
  kMoon,
  kSpider,
  kFireball,
  kFlagUnitedArabEmirates,
  kFlagQatar,
  kFlagEgypt,
  kFlagKuwait,
  kFlagAlgeria,
  kFlagSaudiArabia,
  kFlagMalaysia,
  kFlagCzechRepublic,
  kFlagAustralia,
  kFlagSingapore,
  kOculusLogo,
  kSteamLogo,
  kNvidiaLogo,
  kFlagIran,
  kFlagPoland,
  kFlagArgentina,
  kFlagPhilippines,
  kFlagChile,
  kMikirog,
  kV2Logo,
  kLast  // Sentinel
};

// NOTE: When adding exception types here, add a corresponding
// handler in Python::SetPythonException.

/// Python exception types we can raise from our own exceptions.
enum class PyExcType : uint8_t {
  kRuntime,
  kAttribute,
  kIndex,
  kType,
  kKey,
  kValue,
  kReference,
  kContext,
  kNotFound,
  kNodeNotFound,
  kActivityNotFound,
  kSessionNotFound,
  kSessionPlayerNotFound,
  kInputDeviceNotFound,
  kDelegateNotFound,
  kWidgetNotFound
};

enum class LogName : uint8_t {
  kRoot,
  kBa,
  kBaApp,
  kBaDisplayTime,
  kBaLifecycle,
  kBaAudio,
  kBaGraphics,
  kBaPerformance,
  kBaAssets,
  kBaInput,
  kBaNetworking,
  kLast  // Sentinel
};

enum class LogLevel : uint8_t {
  kDebug,
  kInfo,
  kWarning,
  kError,
  kCritical,
};

enum class ThreadSource : uint8_t {
  /// Spin up a new thread for the event loop.
  kCreate,
  /// Wrap the event loop around the current thread.
  kWrapCurrent
};

/// Used for thread identification (mostly just for debugging).
enum class EventLoopID : uint8_t {
  kInvalid,
  kLogic,
  kAssets,
  kFileOut,
  kMain,
  kAudio,
  kNetworkWrite,
  kSuicide,
  kStdin,
  kBGDynamics
};

/// Return the same bool value passed in, but obfuscated enough in debug mode
/// that no 'value is always true/false', 'code will never run', type warnings
/// should appear. In release builds it should optimize away to a no-op.
inline auto explicit_bool(bool val) -> bool {
  if (g_buildconfig.debug_build()) {
    return InlineDebugExplicitBool(val);
  } else {
    return val;
  }
}

/// assert() that the provided pointer is not nullptr.
template <typename T>
auto AssertNotNull(T* ptr) -> T* {
  assert(ptr != nullptr);
  return ptr;
}

template <typename OUT_TYPE, typename IN_TYPE>
auto check_static_cast_fit(IN_TYPE in) -> bool {
  // Make sure we don't try to use this when casting to or from floats or
  // doubles. We don't expect to always get the same value back on casting
  // back in that case.
  static_assert(!std::is_same<IN_TYPE, float>::value
                    && !std::is_same<IN_TYPE, double>::value
                    && !std::is_same<IN_TYPE, const float>::value
                    && !std::is_same<IN_TYPE, const double>::value
                    && !std::is_same<OUT_TYPE, float>::value
                    && !std::is_same<OUT_TYPE, double>::value
                    && !std::is_same<OUT_TYPE, const float>::value
                    && !std::is_same<OUT_TYPE, const double>::value,
                "check_static_cast_fit cannot be used with floats or doubles.");
  return static_cast<IN_TYPE>(static_cast<OUT_TYPE>(in)) == in;
}

/// Simply a static_cast, but in debug builds casts the results back to
/// ensure the value fits into the receiver unchanged. Handy as a sanity
/// check when stuffing a 32 bit value into a 16 bit container, etc.
template <typename OUT_TYPE, typename IN_TYPE>
auto static_cast_check_fit(IN_TYPE in) -> OUT_TYPE {
  assert(check_static_cast_fit<OUT_TYPE>(in));
  return static_cast<OUT_TYPE>(in);
}

/// Simply a static_cast, but in debug builds also runs a dynamic cast to
/// ensure the results would have been the same. Handy for keeping casts
/// lightweight when types are known while still having a sanity check.
template <typename OUT_TYPE, typename IN_TYPE>
auto static_cast_check_type(IN_TYPE in) -> OUT_TYPE {
  auto out_static = static_cast<OUT_TYPE>(in);
  if (g_buildconfig.debug_build()) {
    assert(out_static == dynamic_cast<OUT_TYPE>(in));
  }
  return out_static;
}

/// Given a path, returns the basename as a constexpr.
/// Handy for less verbose __FILE__ usage without adding runtime overhead.
constexpr const char* cxpr_base_name(const char* path) {
  const char* file = path;
  while (*path) {
    const char* cur = path++;
    if (*cur == '/' || *cur == '\\') {
      file = path;
    }
  }
  return file;
}

// This stuff hijacks compile-type pretty-function-printing functionality
// to give human-readable strings for arbitrary types. Note that these
// will not be consistent across platforms and should only be used for
// logging/debugging. Also note that this code is dependent on specific
// compiler output which could change at any time; to watch out for this
// it is recommended to add static_assert()s somewhere to ensure that
// output for a few given types matches expected results.
// For reference, see this topic:
// https://stackoverflow.com/questions/81870
template <typename T>
constexpr std::string_view wrapped_type_name() {
#ifdef __clang__
  return __PRETTY_FUNCTION__;
#elif defined(__GNUC__)
  return __PRETTY_FUNCTION__;
#elif defined(_MSC_VER)
  return __FUNCSIG__;
#else
#error "Unsupported compiler"
#endif
}

// To see what our particular compiler has at the beginning of one of
// these strings, let's generate one for 'void' and look for 'void'.
constexpr std::size_t wrapped_type_name_prefix_length() {
  return wrapped_type_name<void>().find("void");
}

// Similar deal for the end. Subtract the prefix length and length of 'void'
// and what's left is our suffix.
constexpr std::size_t wrapped_type_name_suffix_length() {
  return wrapped_type_name<void>().length() - wrapped_type_name_prefix_length()
         - std::string_view("void").length();
}

template <typename T>
constexpr auto static_type_name_constexpr(bool debug_full = false)
    -> std::string_view {
  auto name{wrapped_type_name<T>()};
  if (!debug_full) {
    name.remove_prefix(wrapped_type_name_prefix_length());
    name.remove_suffix(wrapped_type_name_suffix_length());
  }
  return name;
}

/// Return a human-readable string for the template type.
template <typename T>
static auto static_type_name(bool debug_full = false) -> std::string {
  return std::string(static_type_name_constexpr<T>(debug_full));
}

extern const int kEngineBuildNumber;
extern const char* kEngineVersion;
extern const int kEngineApiVersion;

const int kDefaultPort = 43210;

// Magic numbers at the start of our file types.
const int kBobFileID = 45623;
const int kCobFileID = 13466;

const float kPi = 3.1415926535897932384626433832795028841971693993751f;
const float kPiDeg = kPi / 180.0f;
const float kDegPi = 180.0f / kPi;

#if BA_MONOLITHIC_BUILD
/// Entry point for standard monolithic builds. Handles all initing and
/// running.
auto MonolithicMain(const core::CoreConfig& config) -> int;

/// Special alternate version of MonolithicMain which breaks its work into
/// pieces; used to reduce app-not-responding reports from slow Android
/// devices. Call this repeatedly until it returns true;
auto MonolithicMainIncremental(const core::CoreConfig* config) -> bool;
#endif  // BA_MONOLITHIC_BUILD

/// Log a fatal error and kill the app. Can be called from any thread at any
/// time. Provided message will be shown to the user if possible. This will
/// attempt to ship all accumulated logs to the master-server so the
/// standard Log() call can be used before this to include extra info not
/// relevant to the end user.
void FatalError(const std::string& message = "");

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_BALLISTICA_H_
