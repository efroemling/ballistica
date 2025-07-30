// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_BASE_H_
#define BALLISTICA_BASE_BASE_H_

#include <atomic>
#include <mutex>
#include <optional>
#include <string>

#include "ballistica/base/discord/discord.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// Predeclare types from other feature sets that we use.
namespace ballistica::core {
class CoreConfig;
class CoreFeatureSet;
}  // namespace ballistica::core

// Feature-sets have their own unique namespace under the ballistica
// namespace.
namespace ballistica::base {

// Predeclare types we use throughout our FeatureSet so most headers can get
// away with just including this header.
class AppAdapter;
class AppConfig;
class AppTimer;
class AppMode;
class PlusSoftInterface;
class AreaOfInterest;
class Assets;
class Audio;
class AudioServer;
class AudioStreamer;
class AudioSource;
class BaseFeatureSet;
class BasePlatform;
class BasePython;
class BGDynamics;
class BGDynamicsServer;
class BGDynamicsDrawSnapshot;
class BGDynamicsEmission;
class BGDynamicsFuse;
struct BGDynamicsFuseData;
class BGDynamicsHeightCache;
class BGDynamicsShadow;
struct BGDynamicsShadowData;
class BGDynamicsVolumeLight;
struct BGDynamicsVolumeLightData;
class Camera;
class ClassicSoftInterface;
class CollisionMeshAsset;
class CollisionCache;
class DevConsole;
class DisplayTimer;
class Context;
class ContextRef;
class DataAsset;
class FrameDef;
class Graphics;
class GraphicsServer;
struct GraphicsSettings;
struct GraphicsClientContext;
class ImageMesh;
class Input;
class InputDevice;
class InputDeviceDelegate;
class JoystickInput;
class KeyboardInput;
class Logic;
class Asset;
class AssetsServer;
class MeshBufferBase;
class MeshBufferVertexSprite;
class MeshBufferVertexSimpleFull;
class MeshBufferVertexSmokeFull;
class Mesh;
class MeshData;
class MeshDataClientHandle;
class MeshIndexBuffer16;
class MeshIndexedSimpleFull;
class MeshIndexedSmokeFull;
class MeshRendererData;
class MeshAsset;
class MeshAssetRendererData;
class NetClientThread;
class NetGraph;
class Networking;
class NetworkReader;
class NetworkWriter;
class NinePatchMesh;
class ObjectComponent;
class PythonClassUISound;
class PythonContextCall;
class Renderer;
class RenderComponent;
class RenderCommandBuffer;
class RenderPass;
class RenderTarget;
class RemoteAppServer;
class RemoteControlInput;
class Repeater;
class ScoreToBeat;
class ScreenMessages;
class AppAdapterSDL;
class SDLContext;
class SoundAsset;
class SpriteMesh;
class StdioConsole;
class Module;
class TestInput;
class TextGroup;
class TextGraphics;
class TextMesh;
class TextPacker;
class TextureAsset;
class TextureAssetPreloadData;
class TextureAssetRendererData;
class TouchInput;
class UI;
class UIDelegateInterface;
class AppAdapterVR;
class GraphicsVR;

enum class AssetType : uint8_t {
  kTexture,
  kCollisionMesh,
  kMesh,
  kSound,
  kData,
  kLast,
};

enum class DrawType : uint8_t {
  kTriangles,
  kPoints,
};

/// Hints to the renderer - stuff that is changed rarely should be static,
/// and stuff changed often should be dynamic.
enum class MeshDrawType : uint8_t {
  kStatic,
  kDynamic,
};

enum class ReflectionType : uint8_t {
  kNone,
  kChar,
  kPowerup,
  kSoft,
  kSharp,
  kSharper,
  kSharpest,
};

enum class GraphicsQuality : uint8_t {
  /// Quality has not yet been set.
  kUnset,
  /// Bare minimum graphics.
  kLow,
  /// Basic graphics; no post-processing.
  kMedium,
  /// Graphics with bare minimum post-processing.
  kHigh,
  /// Graphics with full post-processing.
  kHigher,
};

enum class VSync : uint8_t { kUnset, kNever, kAlways, kAdaptive };
enum class VSyncRequest : uint8_t { kNever, kAlways, kAuto };

/// Requests for exact or auto graphics quality values.
enum class GraphicsQualityRequest : uint8_t {
  kUnset,
  kLow,
  kMedium,
  kHigh,
  kHigher,
  kAuto,
};

// Standard vertex structs used in rendering/fileIO/etc.
// Remember to make sure components are on 4 byte boundaries.
// (need to find out how strict we need to be on Metal, Vulkan, etc).

struct VertexSimpleSplitStatic {
  uint16_t uv[2];
};

struct VertexSimpleSplitDynamic {
  float position[3];
};

struct VertexSimpleFull {
  float position[3];
  uint16_t uv[2];
};

struct VertexDualTextureFull {
  float position[3];
  uint16_t uv[2];
  uint16_t uv2[2];
};

struct VertexObjectSplitStatic {
  uint16_t uv[2];
};

struct VertexObjectSplitDynamic {
  float position[3];
  int16_t normal[3];
  int8_t padding[2];
};

struct VertexObjectFull {
  float position[3];
  uint16_t uv[2];
  int16_t normal[3];
  uint8_t padding[2];
};

struct VertexSmokeFull {
  float position[3];
  float uv[2];
  uint8_t color[4];
  uint8_t diffuse;
  uint8_t padding1[3];
  uint8_t erode;
  uint8_t padding2[3];
};

struct VertexSprite {
  float position[3];
  uint16_t uv[2];
  float size;
  float color[4];
};

enum class MeshFormat : uint8_t {
  /// 16bit UV, 8bit normal, 8bit pt-index.
  kUV16N8Index8,
  /// 16bit UV, 8bit normal, 16bit pt-index.
  kUV16N8Index16,
  /// 16bit UV, 8bit normal, 32bit pt-index.
  kUV16N8Index32,
};

enum class TextureType : uint8_t {
  k2D,
  kCubeMap,
};

enum class TextureFormat : uint8_t {
  kNone,
  kRGBA_8888,
  kRGB_888,
  kRGBA_4444,
  kRGB_565,
  kDXT1,
  kDXT5,
  kETC1,
  kPVR2,
  kPVR4,
  kETC2_RGB,
  kETC2_RGBA,
};

enum class TextureCompressionType : uint8_t {
  kS3TC,
  kPVR,
  kETC1,
  kETC2,
  kASTC,
};

enum class TextureMinQuality : uint8_t {
  kLow,
  kMedium,
  kHigh,
};

enum class CameraMode : uint8_t {
  kFollow,
  kOrbit,
};

enum class MeshDataType : uint8_t {
  kIndexedSimpleSplit,
  kIndexedObjectSplit,
  kIndexedSimpleFull,
  kIndexedDualTextureFull,
  kIndexedSmokeFull,
  kSprite
};

struct TouchEvent {
  enum class Type { kDown, kUp, kMoved, kCanceled };
  Type type{};
  void* touch{};
  bool overall{};  // For sanity-checks.
  float x{};
  float y{};
};

enum class TextMeshEntryType : uint8_t {
  kRegular,
  kExtras,
  kOSRendered,
};

enum MeshDrawFlags : uint8_t {
  kMeshDrawFlagNoReflection = 1,
};

enum class LightShadowType : uint8_t {
  kNone,
  kTerrain,
  kObject,
};

enum class TextureQualityRequest : uint8_t {
  kUnset,
  kAuto,
  kHigh,
  kMedium,
  kLow,
};

enum class TextureQuality : uint8_t {
  kUnset,
  kHigh,
  kMedium,
  kLow,
};

enum class BenchmarkType : uint8_t {
  kNone,
  kCPU,
  kGPU,
};

#if BA_VR_BUILD
enum class VRHandType : uint8_t {
  kNone,
  kDaydreamRemote,
  kOculusTouchL,
  kOculusTouchR,
};
struct VRHandState {
  VRHandType type = VRHandType::kNone;
  float tx = 0.0f;
  float ty = 0.0f;
  float tz = 0.0f;
  float yaw = 0.0f;
  float pitch = 0.0f;
  float roll = 0.0f;
};
struct VRHandsState {
  VRHandState l;
  VRHandState r;
};
#endif  // BA_VR_BUILD

/// Types of shading.
/// These do not necessarily correspond to actual shader objects in the renderer
/// (a single shader may handle more than one of these, etc).
/// These are simply categories of looks.
enum class ShadingType : uint8_t {
  kSimpleColor,
  kSimpleColorTransparent,
  kSimpleColorTransparentDoubleSided,
  kSimpleTexture,
  kSimpleTextureModulated,
  kSimpleTextureModulatedColorized,
  kSimpleTextureModulatedColorized2,
  kSimpleTextureModulatedColorized2Masked,
  kSimpleTextureModulatedTransparent,
  kSimpleTextureModulatedTransFlatness,
  kSimpleTextureModulatedTransparentDoubleSided,
  kSimpleTextureModulatedTransparentColorized,
  kSimpleTextureModulatedTransparentColorized2,
  kSimpleTextureModulatedTransparentColorized2Masked,
  kSimpleTextureModulatedTransparentShadow,
  kSimpleTexModulatedTransShadowFlatness,
  kSimpleTextureModulatedTransparentGlow,
  kSimpleTextureModulatedTransparentGlowMaskUV2,
  kObject,
  kObjectTransparent,
  kObjectLightShadowTransparent,
  kSpecial,
  kShield,
  kObjectReflect,
  kObjectReflectTransparent,
  kObjectReflectAddTransparent,
  kObjectLightShadow,
  kObjectReflectLightShadow,
  kObjectReflectLightShadowDoubleSided,
  kObjectReflectLightShadowColorized,
  kObjectReflectLightShadowColorized2,
  kObjectReflectLightShadowAdd,
  kObjectReflectLightShadowAddColorized,
  kObjectReflectLightShadowAddColorized2,
  kSmoke,
  kSmokeOverlay,
  kPostProcess,
  kPostProcessEyes,
  kPostProcessNormalDistort,
  kSprite,
  kCount
};

enum class SysTextureID : uint8_t {
  kUIAtlas,
  kButtonSquare,
  kWhite,
  kFontSmall0,
  kFontBig,
  kCursor,
  kBoxingGlove,
  kShield,
  kExplosion,
  kTextClearButton,
  kWindowHSmallVMed,
  kWindowHSmallVSmall,
  kGlow,
  kScrollWidget,
  kScrollWidgetGlow,
  kFlagPole,
  kScorch,
  kScorchBig,
  kShadow,
  kLight,
  kShadowSharp,
  kLightSharp,
  kShadowSoft,
  kLightSoft,
  kSparks,
  kEye,
  kEyeTint,
  kFuse,
  kShrapnel1,
  kSmoke,
  kCircle,
  kCircleOutline,
  kCircleNoAlpha,
  kCircleOutlineNoAlpha,
  kCircleShadow,
  kSoftRect,
  kSoftRect2,
  kSoftRectVertical,
  kStartButton,
  kBombButton,
  kOuyaAButton,
  kBackIcon,
  kNub,
  kArrow,
  kMenuButton,
  kUsersButton,
  kActionButtons,
  kTouchArrows,
  kTouchArrowsActions,
  kRGBStripes,
  kUIAtlas2,
  kFontSmall1,
  kFontSmall2,
  kFontSmall3,
  kFontSmall4,
  kFontSmall5,
  kFontSmall6,
  kFontSmall7,
  kFontExtras,
  kFontExtras2,
  kFontExtras3,
  kFontExtras4,
  kCharacterIconMask,
  kBlack,
  kWings,
  kSpinner,
  kSpinner0,
  kSpinner1,
  kSpinner2,
  kSpinner3,
  kSpinner4,
  kSpinner5,
  kSpinner6,
  kSpinner7,
  kSpinner8,
  kSpinner9,
  kSpinner10,
  kSpinner11,
};

enum class SysCubeMapTextureID : uint8_t {
  kReflectionChar,
  kReflectionPowerup,
  kReflectionSoft,
  kReflectionSharp,
  kReflectionSharper,
  kReflectionSharpest
};

enum class SysSoundID {
  kDeek,
  kBlip,
  kBlank,
  kPunch,
  kClick,
  kErrorBeep,
  kSwish,
  kSwish2,
  kSwish3,
  kTap,
  kCorkPop,
  kGunCock,
  kTickingCrazy,
  kSparkle,
  kSparkle2,
  kSparkle3,
  kScoreIncrease,
  kCashRegister,
  kPowerDown,
  kDing,
};

enum class SystemDataID : uint8_t {};

enum class SysMeshID : uint8_t {
  kButtonSmallTransparent,
  kButtonSmallOpaque,
  kButtonMediumTransparent,
  kButtonMediumOpaque,
  kButtonBackTransparent,
  kButtonBackOpaque,
  kButtonBackSmallTransparent,
  kButtonBackSmallOpaque,
  kButtonTabTransparent,
  kButtonTabOpaque,
  kButtonLargeTransparent,
  kButtonLargeOpaque,
  kButtonLargerTransparent,
  kButtonLargerOpaque,
  kButtonSquareTransparent,
  kButtonSquareOpaque,
  kCheckTransparent,
  kScrollBarThumbTransparent,
  kScrollBarThumbOpaque,
  kScrollBarThumbSimple,
  kScrollBarThumbShortTransparent,
  kScrollBarThumbShortOpaque,
  kScrollBarThumbShortSimple,
  kScrollBarTroughTransparent,
  kTextBoxTransparent,
  kImage1x1,
  kImage1x1FullScreen,
  kImage2x1,
  kImage4x1,
  kImage16x1,
#if BA_VR_BUILD
  kImage1x1VRFullScreen,
  kVROverlay,
  kVRFade,
#endif
  kOverlayGuide,
  kWindowHSmallVMedTransparent,
  kWindowHSmallVMedOpaque,
  kWindowHSmallVSmallTransparent,
  kWindowHSmallVSmallOpaque,
  kSoftEdgeOutside,
  kSoftEdgeInside,
  kBoxingGlove,
  kShield,
  kFlagPole,
  kFlagStand,
  kScorch,
  kEyeBall,
  kEyeBallIris,
  kEyeLid,
  kHairTuft1,
  kHairTuft1b,
  kHairTuft2,
  kHairTuft3,
  kHairTuft4,
  kShrapnel1,
  kShrapnelSlime,
  kShrapnelBoard,
  kShockWave,
  kFlash,
  kCylinder,
  kArrowFront,
  kArrowBack,
  kActionButtonLeft,
  kActionButtonTop,
  kActionButtonRight,
  kActionButtonBottom,
  kBox,
  kLocator,
  kLocatorBox,
  kLocatorCircle,
  kLocatorCircleOutline,
  kCrossOut,
  kWing
};

// The screen, no matter what size/aspect, will always fit this virtual
// rectangle, so placing UI elements within these coords is always safe.

// Our standard virtual res (16:9 aspect ratio).
const int kBaseVirtualResX = 1280;
const int kBaseVirtualResY = 720;

// Our feature-set's globals.
//
// Feature-sets should NEVER directly access globals in another
// feature-set's namespace. All functionality we need from other
// feature-sets should be imported into globals in our own namespace.
// Generally we do this when we are initially imported (just as regular
// Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;

/// Our C++ front-end to our feature set. This is what other C++
/// feature-sets can 'Import' from us.
class BaseFeatureSet : public FeatureSetNativeComponent,
                       public core::BaseSoftInterface {
 public:
  /// Instantiates our FeatureSet if needed and returns the single
  /// instance of it. Basically C++ analog to Python import.
  static auto Import() -> BaseFeatureSet*;

  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);

  /// Start app systems in motion.
  void StartApp() override;

  /// Set the app's active state. Should be called from the main thread.
  /// Generally called by the AppAdapter. Being inactive means the app
  /// experience is not front and center and thus it may want to throttle
  /// down its rendering rate, pause single play gameplay, etc. This does
  /// not, however, cause any extreme action such as halting event loops;
  /// use Suspend/Resume for that. And note that the app may still be
  /// visible while inactive, so it should not *completely* stop
  /// drawing/etc.
  void SetAppActive(bool active);

  /// Put the app into a suspended state. Should be called from the main
  /// thread. Generally called by the AppAdapter. Suspends event loops,
  /// closes network sockets, etc. Generally corresponds to being
  /// backgrounded on mobile platforms. It is assumed that, as soon as this
  /// call returns, all engine work is finished and all threads can be
  /// immediately suspended by the OS without any problems.
  void SuspendApp();

  /// Return the app to a running state from a suspended one. Can correspond
  /// to foregrounding on mobile, unminimizing on desktop, etc. Spins
  /// threads back up, re-opens network sockets, etc.
  void UnsuspendApp();

  auto app_suspended() const { return app_suspended_; }

  /// Issue a high level app quit request. Can be called from any thread and
  /// can be safely called repeatedly. If 'confirm' is true, a confirmation
  /// dialog will be presented if the environment and situation allows;
  /// otherwise the quit process will start immediately. A QuitType arg can
  /// optionally be passed to influence quit behavior; on some platforms
  /// such as mobile the default is for the app to recede to the background
  /// but physically remain running.
  void QuitApp(bool confirm = false, QuitType quit_type = QuitType::kSoft);

  /// Called when app shutdown process completes. Sets app to exit.
  void OnAppShutdownComplete();

  auto AppManagesMainThreadEventLoop() -> bool override;

  /// Run app event loop to completion (only applies to flavors which manage
  /// their own event loop).
  void RunAppToCompletion() override;

  auto CurrentContext() -> const ContextRef& {
    assert(InLogicThread());  // Up to caller to ensure this.
    return *context_ref;
  }

  /// Utility call to print 'Success!' with a happy sound.
  /// Safe to call from any thread.
  void SuccessScreenMessage();

  /// Utility call to print 'Error.' with a beep sound.
  /// Safe to call from any thread.
  void ErrorScreenMessage();

  void SetCurrentContext(const ContextRef& context);

  /// Try to load the plus feature-set and return whether it is available.
  auto HavePlus() -> bool;

  /// Access the plus feature-set. Will throw an exception if not present.
  auto Plus() -> PlusSoftInterface*;

  void SetPlus(PlusSoftInterface* plus);

  /// Try to load the classic feature-set and return whether it is available.
  auto HaveClassic() -> bool;

  /// Access the classic feature-set. Will throw an exception if not present.
  auto classic() -> ClassicSoftInterface*;

  void set_classic(ClassicSoftInterface* classic);

  /// Return a string that should be universally unique to this particular
  /// running instance of the app.
  auto GetAppInstanceUUID() -> const std::string&;

  /// Does it appear that we are a blessed build with no known
  /// user-modifications?
  /// Note that some corner cases (such as being called too early in the launch
  /// process) may result in false negatives (saying we're *not* unmodified when
  /// in reality we are unmodified).
  auto IsUnmodifiedBlessedBuild() -> bool override;

  /// Return true if both babase and _babase modules have completed their
  /// import execs. To keep our init order well defined, we want to avoid
  /// allowing certain functionality before this time.
  auto IsBaseCompletelyImported() -> bool;

  auto InMainThread() const -> bool;
  auto InAssetsThread() const -> bool override;
  auto InLogicThread() const -> bool override;
  auto InAudioThread() const -> bool override;
  auto InBGDynamicsThread() const -> bool override;
  auto InNetworkWriteThread() const -> bool override;
  auto InGraphicsContext() const -> bool override;

  /// High level screen-message call. Can be called from any thread.
  void ScreenMessage(const std::string& s,
                     const Vector3f& color = {1.0f, 1.0f, 1.0f}) override;

  /// Has the app bootstrapping phase completed? The bootstrapping phase
  /// involves initial screen/graphics setup. Asset loading is not allowed
  /// until it is complete.
  auto IsAppBootstrapped() const -> bool override;

  /// Has StartApp been called (and completely finished its work)? Code that
  /// sends calls/messages to other threads or otherwise uses app
  /// functionality may want to check this to avoid crashes. Note that some
  /// app functionality such as loading assets is not available until
  /// IsAppBootstrapped returns true. This call is thread safe.
  auto IsAppStarted() const -> bool override;

  void PlusDirectSendV1CloudLogs(const std::string& prefix,
                                 const std::string& suffix, bool instant,
                                 int* result) override;
  auto CreateFeatureSetData(FeatureSetNativeComponent* featureset)
      -> PyObject* override;
  auto FeatureSetFromData(PyObject* obj) -> FeatureSetNativeComponent* override;
  void DoV1CloudLog(const std::string& msg) override;
  void PushDevConsolePrintCall(const std::string& msg, float scale,
                               Vector4f color) override;
  auto GetPyExceptionType(PyExcType exctype) -> PyObject* override;
  auto PrintPythonStackTrace() -> bool override;
  auto GetPyLString(PyObject* obj) -> std::string override;
  auto DoGetContextBaseString() -> std::string override;
  void DoPrintContextAuto() override;
  void DoPushObjCall(const PythonObjectSetBase* objset, int id) override;
  void DoPushObjCall(const PythonObjectSetBase* objset, int id,
                     const std::string& arg) override;
  void OnReachedEndOfBaBaseImport();

  /// Begin a shutdown-suppressing operation. Returns true if the operation
  /// can proceed; otherwise shutdown has already begun and the operation
  /// should be aborted.
  auto ShutdownSuppressBegin() -> bool;

  /// End a shutddown-suppressing operation. Should only be called after a
  /// successful begin.
  void ShutdownSuppressEnd();

  auto ShutdownSuppressGetCount() -> int;
  void ShutdownSuppressDisallow();

  /// Called in the logic thread once our screen is up and assets are
  /// loading.
  void OnAssetsAvailable();

  void PushMainThreadRunnable(Runnable* runnable) override;

  /// Return the currently signed in V2 account id as reported by the Python
  /// layer.
  auto GetV2AccountID() -> std::optional<std::string>;

  /// Return whether clipboard operations are supported at all. This gets
  /// called when determining whether to display clipboard related UI
  /// elements/etc.
  auto ClipboardIsSupported() -> bool;

  /// Return whether there is currently text on the clipboard.
  auto ClipboardHasText() -> bool;

  /// Return current text from the clipboard. Raises an Exception if
  /// clipboard is unsupported or if there's no text on the clipboard.
  auto ClipboardGetText() -> std::string;

  /// Set current clipboard text. Raises an Exception if clipboard is
  /// unsupported.
  void ClipboardSetText(const std::string& text);

  /// Set overall ui scale for the app.
  void SetUIScale(UIScale scale);

  /// Time since epoch on the master-server. Tries to
  /// be correct even if local time is set wrong.
  auto TimeSinceEpochCloudSeconds() -> seconds_t;

  void set_app_mode(AppMode* mode);
  auto* app_mode() const { return app_mode_; }
  auto app_active() -> bool const { return app_active_; }

  /// Whether we're running under ballisticakit_server.py
  /// (affects some app behavior).
  auto server_wrapper_managed() { return server_wrapper_managed_; }

  void set_config_and_state_writes_suppressed(bool val) {
    config_and_state_writes_suppressed_ = val;
  }
  auto config_and_state_writes_suppressed() const {
    return config_and_state_writes_suppressed_;
  }

  /// Reset the engine to a default state. Should only be called by the
  /// active app-mode. App-modes generally call this when first activating,
  /// but may opt to call it at other times.
  void Reset();

  // Const components.
  AppAdapter* const app_adapter;
  AppConfig* const app_config;
  Assets* const assets;
  AssetsServer* const assets_server;
  Audio* const audio;
  AudioServer* const audio_server;
  BasePlatform* const platform;
  BasePython* const python;
  BGDynamics* const bg_dynamics;
  BGDynamicsServer* const bg_dynamics_server;
  ContextRef* const context_ref;
  Graphics* const graphics;
  GraphicsServer* const graphics_server;
  Input* const input;
  Logic* const logic;
  Networking* const networking;
  NetworkReader* const network_reader;
  NetworkWriter* const network_writer;
  StdioConsole* const stdio_console;
  TextGraphics* const text_graphics;
  UI* const ui;
  Utils* const utils;
  Discord* const discord;

  // Non-const components (fixme: clean up access to these).
  TouchInput* touch_input{};

 private:
  BaseFeatureSet();
  void LogStartupMessage_();
  void PrintContextNonLogicThread_();
  void PrintContextForCallableLabel_(const char* label);
  void PrintContextUnavailable_();

  AppMode* app_mode_;
  PlusSoftInterface* plus_soft_{};
  ClassicSoftInterface* classic_soft_{};
  std::mutex shutdown_suppress_lock_;
  /// Main thread informs logic thread when this changes, but then logic
  /// reads original value here set by main. need to be sure they never read
  /// stale values.
  std::atomic_bool app_active_{true};
  int shutdown_suppress_count_{};
  bool have_clipboard_is_supported_{};
  bool clipboard_is_supported_{};
  bool app_active_set_{};
  bool app_suspended_{};
  bool shutdown_suppress_disallowed_{};
  bool tried_importing_plus_{};
  bool tried_importing_classic_{};
  bool tried_importing_ui_v1_{};
  bool called_start_app_{};
  bool app_started_{};
  bool called_run_app_to_completion_{};
  bool base_import_completed_{};
  bool base_native_import_completed_{};
  bool basn_log_behavior_{};
  bool server_wrapper_managed_{};
  bool config_and_state_writes_suppressed_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_BASE_H_
