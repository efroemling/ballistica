// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_TYPES_H_
#define BALLISTICA_CORE_TYPES_H_

// Types used throughout the project.
// This header should not depend on any others in the project.
// Types can be defined (or predeclared) here if the are used
// in a significant number of places. The aim is to reduce the
// overall number of headers a given source file needs to pull in,
// helping to keep compile times down.

#ifdef __cplusplus

// Predeclare a few global namespace things
// (just enough to pass some pointers around without
// requiring system-ish headers).
typedef struct _object PyObject;
typedef struct _ts PyThreadState;
typedef struct PyMethodDef PyMethodDef;

#if BA_SDL_BUILD || BA_MINSDL_BUILD
union SDL_Event;
struct SDL_Keysym;
typedef struct _SDL_Joystick SDL_Joystick;
#endif

namespace ballistica {

// Used internally for time values.
typedef int64_t millisecs_t;

// We predeclare all our main ba classes here so that we can
// avoid pulling in their full headers as much as possible
// to keep compile times down.

class AppFlavor;
class AppConfig;
class App;
class AppInternal;
class AreaOfInterest;
class Assets;
class Audio;
class AudioServer;
class AudioStreamer;
class AudioSource;
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
class ButtonWidget;
struct cJSON;
class Camera;
class ClientControllerInterface;
class ClientInputDevice;
class ClientSession;
class CollideModel;
class CollideModelData;
class Collision;
class CollisionCache;
class Connection;
class ConnectionSet;
class ConnectionToClient;
class Context;
class ContextTarget;
class ConnectionToClientUDP;
class ConnectionToHost;
class ConnectionToHostUDP;
class ContainerWidget;
class Console;
class CubeMapTexture;
class Data;
class DataData;
class Dynamics;
class FrameDef;
struct FriendScoreSet;
class Game;
class GLContext;
class GlobalsNode;
class Graphics;
class GraphicsServer;
class HostActivity;
class HostSession;
class Huffman;
class ImageMesh;
class ImageWidget;
class Input;
class InputDevice;
struct JointFixedEF;
class Joystick;
class JsonDict;
class KeyboardInput;
class Material;
class MaterialAction;
class MaterialComponent;
class MaterialConditionNode;
class MaterialContext;
class Matrix44f;
class AssetComponentData;
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
class Model;
class ModelData;
class ModelRendererData;
class NetClientThread;
class NetGraph;
class Networking;
class NetworkReader;
class NetworkWriteModule;
class Node;
class NodeType;
class NodeAttribute;
class NodeAttributeConnection;
class NodeAttributeUnbound;
class Object;
class ObjectComponent;
class Part;
class Python;
class Platform;
class Player;
class PlayerNode;
class PlayerSpec;
class PythonClassCollideModel;
class PythonClassMaterial;
class PythonClassModel;
class PythonClassSound;
class PythonClassTexture;
class Python;
class PythonRef;
class PythonCommand;
class PythonContextCall;
template <typename T>
class RealTimer;
class Rect;
class Renderer;
class RenderComponent;
class RenderCommandBuffer;
class RenderPass;
class RenderTarget;
class ReplayClientSession;
class RemoteAppServer;
class RemoteControlInput;
class RigidBody;
class RootUI;
class RootWidget;
class Runnable;
class Scene;
class SceneStream;
class ScoreToBeat;
class SDLApp;
class SDLContext;
class Session;
class SockAddr;
class Sound;
class SoundData;
class SpriteMesh;
class StackWidget;
class StressTest;
class StdInputModule;
class Module;
class TelnetServer;
class TestInput;
class TextGroup;
class TextGraphics;
class TextMesh;
class TextPacker;
class Texture;
class TextureData;
class TexturePreloadData;
class TextureRendererData;
class TextWidget;
class Thread;
class Timer;
class TimerList;
class TouchInput;
class UI;
class Utils;
class Vector2f;
class Vector3f;
class Vector4f;
class AppFlavorVR;
class V1Account;
class VRGraphics;
class Widget;

// BA_EXPORT_PYTHON_ENUM
/// Types of input a controller can send to the game.
///
/// Category: Enums
///
enum class InputType {
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

typedef int64_t TimerMedium;

// BA_EXPORT_PYTHON_ENUM
/// The overall scale the UI is being rendered for. Note that this is
/// independent of pixel resolution. For example, a phone and a desktop PC
/// might render the game at similar pixel resolutions but the size they
/// display content at will vary significantly.
///
/// Category: Enums
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
enum class UIScale {
  kLarge,
  kMedium,
  kSmall,
  kLast  // Sentinel.
};

// BA_EXPORT_PYTHON_ENUM
/// Specifies the type of time for various operations to target/use.
///
/// Category: Enums
///
/// 'sim' time is the local simulation time for an activity or session.
///    It can proceed at different rates depending on game speed, stops
///    for pauses, etc.
///
/// 'base' is the baseline time for an activity or session.  It proceeds
///    consistently regardless of game speed or pausing, but may stop during
///    occurrences such as network outages.
///
/// 'real' time is mostly based on clock time, with a few exceptions.  It may
///    not advance while the app is backgrounded for instance.  (the engine
///    attempts to prevent single large time jumps from occurring)
enum class TimeType {
  kSim,
  kBase,
  kReal,
  kLast  // Sentinel.
};

// BA_EXPORT_PYTHON_ENUM
/// Specifies the format time values are provided in.
///
/// Category: Enums
enum class TimeFormat {
  kSeconds,
  kMilliseconds,
  kLast  // Sentinel.
};

// BA_EXPORT_PYTHON_ENUM
/// Permissions that can be requested from the OS.
///
/// Category: Enums
enum class Permission {
  kStorage,
  kLast  // Sentinel.
};

// BA_EXPORT_PYTHON_ENUM
/// Special characters the game can print.
///
/// Category: Enums
enum class SpecialChar {
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
  kOuyaButtonO,
  kOuyaButtonU,
  kOuyaButtonY,
  kOuyaButtonA,
  kOuyaLogo,
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
  kAlibabaLogo,
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

enum class AssetType { kTexture, kCollideModel, kModel, kSound, kData, kLast };

/// Python exception types we can raise from our own exceptions.
enum class PyExcType {
  kRuntime,
  kAttribute,
  kIndex,
  kType,
  kValue,
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

enum class SystemTextureID {
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
  kWings
};

enum class SystemCubeMapTextureID {
  kReflectionChar,
  kReflectionPowerup,
  kReflectionSoft,
  kReflectionSharp,
  kReflectionSharper,
  kReflectionSharpest
};

enum class SystemSoundID {
  kDeek = 0,
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
  kSparkle3
};

enum class SystemDataID {};

enum class SystemModelID {
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

enum class NodeCollideAttr {
  /// Whether or not a collision should occur at all.
  /// If this is false for either node in the final context,
  /// no collide events are run.
  kCollideNode
};

enum class PartCollideAttr {
  /// Whether or not a collision should occur at all.
  /// If this is false for either surface in the final context,
  /// no collide events are run.
  kCollide,

  /// Whether to honor node-collisions.
  /// Turn this on if you want a collision to occur even if
  /// The part is ignoring collisions with your node due
  /// to an existing NodeModAction.
  kUseNodeCollide,

  /// Whether a physical collision happens.
  kPhysical,

  /// Friction for physical collisions.
  kFriction,

  /// Stiffness for physical collisions.
  kStiffness,

  /// Damping for physical collisions.
  kDamping,

  /// Bounce for physical collisions.
  kBounce
};

enum class MaterialCondition {
  /// Always evaluates to true.
  kTrue,

  /// Always evaluates to false.
  kFalse,

  /// Dst part contains specified material; requires 1 arg - material id.
  kDstIsMaterial,

  /// Dst part does not contain specified material; requires 1 arg - material
  /// id.
  kDstNotMaterial,

  /// Dst part is in specified node; requires 1 arg - node id.
  kDstIsNode,

  /// Dst part not in specified node; requires 1 arg - node id.
  kDstNotNode,

  /// Dst part is specified part; requires 2 args, node id, part id.
  kDstIsPart,

  /// Dst part not specified part; requires 2 args, node id, part id.
  kDstNotPart,

  /// Dst part contains src material; no args.
  kSrcDstSameMaterial,

  /// Dst part does not contain the src material; no args.
  kSrcDstDiffMaterial,

  /// Dst and src parts in same node; no args.
  kSrcDstSameNode,

  /// Dst and src parts in different node; no args.
  kSrcDstDiffNode,

  /// Src part younger than specified value; requires 1 arg - age.
  kSrcYoungerThan,

  /// Src part equal to or older than specified value; requires 1 arg - age.
  kSrcOlderThan,

  /// Dst part younger than specified value; requires 1 arg - age.
  kDstYoungerThan,

  /// Dst part equal to or older than specified value; requires 1 arg - age.
  kDstOlderThan,

  /// Src part is already colliding with a part on dst node; no args.
  kCollidingDstNode,

  /// Src part is not already colliding with a part on dst node; no args.
  kNotCollidingDstNode,

  /// Set to collide at current point in rule evaluation.
  kEvalColliding,

  /// Set to not collide at current point in rule evaluation.
  kEvalNotColliding
};

/// Types of shading.
/// These do not necessarily correspond to actual shader objects in the renderer
/// (a single shader may handle more than one of these, etc).
/// These are simply categories of looks.
enum class ShadingType {
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

enum class DrawType { kTriangles, kPoints };

/// Hints to the renderer - stuff that is changed rarely should be static,
/// and stuff changed often should be dynamic.
enum class MeshDrawType { kStatic, kDynamic };

enum class ReflectionType {
  kNone,
  kChar,
  kPowerup,
  kSoft,
  kSharp,
  kSharper,
  kSharpest
};

/// Command values sent across the wire in netplay.
/// Must remain consistent across versions!
enum class SessionCommand {
  kBaseTimeStep,
  kStepSceneGraph,
  kAddSceneGraph,
  kRemoveSceneGraph,
  kAddNode,
  kNodeOnCreate,
  kSetForegroundSceneGraph,
  kRemoveNode,
  kAddMaterial,
  kRemoveMaterial,
  kAddMaterialComponent,
  kAddTexture,
  kRemoveTexture,
  kAddModel,
  kRemoveModel,
  kAddSound,
  kRemoveSound,
  kAddCollideModel,
  kRemoveCollideModel,
  kConnectNodeAttribute,
  kNodeMessage,
  kSetNodeAttrFloat,
  kSetNodeAttrInt32,
  kSetNodeAttrBool,
  kSetNodeAttrFloats,
  kSetNodeAttrInt32s,
  kSetNodeAttrString,
  kSetNodeAttrNode,
  kSetNodeAttrNodeNull,
  kSetNodeAttrNodes,
  kSetNodeAttrPlayer,
  kSetNodeAttrPlayerNull,
  kSetNodeAttrMaterials,
  kSetNodeAttrTexture,
  kSetNodeAttrTextureNull,
  kSetNodeAttrTextures,
  kSetNodeAttrSound,
  kSetNodeAttrSoundNull,
  kSetNodeAttrSounds,
  kSetNodeAttrModel,
  kSetNodeAttrModelNull,
  kSetNodeAttrModels,
  kSetNodeAttrCollideModel,
  kSetNodeAttrCollideModelNull,
  kSetNodeAttrCollideModels,
  kPlaySoundAtPosition,
  kPlaySound,
  kEmitBGDynamics,
  kEndOfFile,
  kDynamicsCorrection,
  kScreenMessageBottom,
  kScreenMessageTop,
  kAddData,
  kRemoveData
};

/// Standard messages to send to nodes.
/// Note: the names of these in python are their camelback forms,
/// so SELF_STATE is "selfState", etc.
enum class NodeMessageType {
  /// Generic flash - no args.
  kFlash,
  /// Celebrate message - one int arg for duration.
  kCelebrate,
  /// Left-hand celebrate message - one int arg for duration.
  kCelebrateL,
  /// Right-hand celebrate message - one int arg for duration.
  kCelebrateR,
  /// Instantaneous impulse 3 vector floats.
  kImpulse,
  kKickback,
  /// Knock the target out for an amount of time.
  kKnockout,
  /// Make a hurt sound.
  kHurtSound,
  /// You've been picked up.. lose balance or whatever.
  kPickedUp,
  /// Make a jump sound.
  kJumpSound,
  /// Make an attack sound.
  kAttackSound,
  /// Tell the player to scream.
  kScreamSound,
  /// Move to stand upon the given point facing the given angle.
  /// 3 position floats and one angle float.
  kStand,
  /// Add or remove footing from a node.
  /// First arg is an int - either 1 or -1 for add or subtract.
  kFooting
};

enum class V1LoginState { kSignedOut, kSigningIn, kSignedIn };

enum class CameraMode { kFollow, kOrbit };

enum class MeshDataType {
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

enum class MeshFormat {
  /// 16bit UV, 8bit normal, 8bit pt-index.
  kUV16N8Index8,
  /// 16bit UV, 8bit normal, 16bit pt-index.
  kUV16N8Index16,
  /// 16bit UV, 8bit normal, 32bit pt-index.
  kUV16N8Index32
};

enum class TextureType { k2D, kCubeMap };

enum class TextureFormat {
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
  kETC2_RGBA
};

enum class TextureCompressionType { kS3TC, kPVR, kETC1, kETC2 };

enum class TextureMinQuality { kLow, kMedium, kHigh };

enum NodeAttributeFlag { kNodeAttributeFlagReadOnly = 1u };

enum class NodeAttributeType {
  kFloat,
  kFloatArray,
  kInt,
  kIntArray,
  kBool,
  kString,
  kNode,
  kNodeArray,
  kPlayer,
  kMaterialArray,
  kTexture,
  kTextureArray,
  kSound,
  kSoundArray,
  kModel,
  kModelArray,
  kCollideModel,
  kCollideModelArray
};

enum class ThreadType {
  /// A normal thread spun up by us.
  kStandard,
  /// For wrapping a ballistica thread around the existing main thread.
  kMain
};

/// Used for module-thread identification.
/// Mostly just for debugging, through a few things are affected by this
/// (the Logic thread manages the python GIL, etc).
enum class ThreadIdentifier {
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

enum class V1AccountType {
  kInvalid,
  kTest,
  kGameCenter,
  kGameCircle,
  kGooglePlay,
  kDevice,
  kServer,
  kOculus,
  kSteam,
  kNvidiaChina,
  kV2
};

enum class GraphicsQuality {
  /// Bare minimum graphics.
  kLow,
  /// Basic graphics; no post-processing.
  kMedium,
  /// Graphics with bare minimum post-processing.
  kHigh,
  /// Graphics with full post-processing.
  kHigher,
  /// Select graphics options automatically.
  kAuto
};

enum class TextMeshEntryType { kRegular, kExtras, kOSRendered };

enum ModelDrawFlags { kModelDrawFlagNoReflection = 1 };

enum class LightShadowType { kNone, kTerrain, kObject };

enum class TextureQuality { kAuto, kHigh, kMedium, kLow };

typedef Node* NodeCreateFunc(Scene* sg);

enum class BenchmarkType { kNone, kCPU, kGPU };

#if BA_VR_BUILD
enum class VRHandType { kNone, kDaydreamRemote, kOculusTouchL, kOculusTouchR };
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

}  // namespace ballistica

#endif  // __cplusplus

#endif  // BALLISTICA_CORE_TYPES_H_
