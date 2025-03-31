// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_TYPES_H_
#define BALLISTICA_SHARED_FOUNDATION_TYPES_H_

// Types used throughout the project.
// This header should not depend on any others in the project.
// Types can be defined (or predeclared) here if the are used
// in a significant number of places. The aim is to reduce the
// overall number of headers a given source file needs to pull in,
// helping to keep compile times down.

#ifdef __cplusplus

// Predeclare a few global namespace things
// (just enough to pass some pointers around without
// requiring a bunch of library/system headers).
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

namespace ballistica {

// Used internally for time values.
typedef double seconds_t;
typedef int64_t millisecs_t;
typedef int64_t microsecs_t;

// We predeclare all our main ba classes here so that we can
// avoid pulling in their full headers as much as possible
// to keep compile times down.
struct cJSON;
class EventLoop;
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

// FIXME: remove this - a few base things we need.
namespace base {
class AppAdapter;
class Graphics;
}  // namespace base

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

/// Used for thread identification.
/// Mostly just for debugging.
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

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_SHARED_FOUNDATION_TYPES_H_
