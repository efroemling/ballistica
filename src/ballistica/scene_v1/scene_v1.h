// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SCENE_V1_H_
#define BALLISTICA_SCENE_V1_SCENE_V1_H_

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/shared/foundation/feature_set_native_component.h"

// Common header that most everything using our feature-set should include.
// It predeclares our feature-set's various types and globals and other
// bits.

// Predeclared types from other feature sets that we use.
namespace ballistica::core {
class CoreFeatureSet;
}
namespace ballistica::base {
class BaseFeatureSet;
}

namespace ballistica::scene_v1 {

// Protocol version we host games with and write replays to. This should be
// incremented whenever there are changes made to the session-commands layer
// (new/removed/changed nodes, attrs, data files, behavior, etc.).

// Note that the packet/gamepacket/message layer can vary more organically
// based on build-numbers of connected clients/servers since none of that
// data is stored; these protocol versions just need to be observed by
// anything emitting or ingesting scene streams.

// Oldest protocol version we can act as a host for.
const int kProtocolVersionHostMin = 43;

// Oldest protocol version we can act as a client to. This can generally be
// left as-is as long as only new nodes/attrs/commands are added and old
// behavior remains the same when not using the new stuff.
const int kProtocolVersionClientMin = 24;

// Newest protocol version we can act as a client OR host for.
const int kProtocolVersionMax = 43;

// The protocol version we actually host is now read as a setting; see
// kSceneV1HostProtocol in ballistica/base/support/app_config.h.

// Protocol changes:
//
// 25: Added a few new achievement graphics and new node attrs for displaying
//     stuff in front of the UI.
//
// 26: Added penguin.
//
// 27: Added templates for LOTS of characters.
//
// 28: Added cyborg and enabled fallback sounds and textures.
//
// 29: Added bunny and eggs.
//
// 30: Added support for resource-strings in text-nodes and screen-messages.
//
// 31: Added support for short-form resource-strings, time-display-node, and
//     string-to-string attr connections.
//
// 32: Added json based player profiles message, added shield
//     always_show_health_bar attr.
//
// 33: Handshake/handshake-response now send json dicts instead of
//     just player-specs.
//
// 34: New image_node enums, data assets.
//
// 35: Camera shake in netplay. how did I apparently miss this for 10 years!?!
//
// 36: Enables V2 auth for servers when authenticate-clients is enabled.
//     This gives servers verified v2 account info for all joiners and
//     allows screening them before they are even allowed in the game,
//     unlike V1 auth. It is also free from V1 auth's spoofing
//     vulnerabilities.
//
// 37: Allows behavior_version 2 on spaz nodes which has punch-grab-spam
//     protection. Note that if you are running a server and prefer the
//     old behavior, you can still set that attr to 1 in mod code.
//
// 38: New hosting floor for the 1.8 cycle; stream semantics identical to
//     37 (the packet/message-layer additions that rode along -- V2 LAN
//     host-query pair, pre-join requirements exchange, party passwords --
//     vary by build number, not protocol). Replays now stamp the TRUE
//     stream protocol they contain rather than kProtocolVersionMax.
//     Frozen as-is once it reached public builds (2026-07-20); the
//     asset-package-native-worlds stream work originally slated to land
//     incrementally under 38 moved to 39.
//
// 39: Asset-package-native worlds. Stream-level exact-apverid package
//     tables with integer-indexed LangStr string refs and asset refs;
//     fixed per-session package universes declared fully in stream
//     baselines (see strings-asset-migration.md D23/D25 and
//     asset-packages.md #36). Frozen as-is once it reached public builds
//     (2026-07-30); further stream work moves to 40.
//
// 40: Two changes, both landing after 39 froze on the 2026-07-30 public
//     push.
//
//     New image-node 'in_world' bool attr (public PR #950), letting an
//     image render into the world like a text node rather than as
//     overlay. Node attrs are addressed over the wire by their position
//     in the type's attribute table (NodeType::attributes_by_index_), so
//     this was APPENDED after 'front' -- existing indices are untouched
//     and only a new trailing one appears. A pre-40 client receiving a
//     set-attr for that index would fail its GetAttribute precondition,
//     which is what makes an added attr protocol-visible even though it
//     shifts nothing.
//
//     Controller force feedback: kInputDeviceFeedback, carrying
//     (player_id, opaque json payload) so whoever controls a player can
//     be asked for rumble/haptics. Needed a version bump because new
//     stream commands are unskippable by older clients -- but it is
//     deliberately the LAST bump this feature should ever need, since
//     its framing is frozen and all future growth happens inside the
//     json dict (see controller-force-feedback.md D1/D2).
//
// 41: New terrain-node 'position' and 'rotate' float-array attrs, letting a
//     terrain be placed and oriented instead of being pinned to wherever
//     its mesh authored it. Same appended-attr situation as image-node
//     'in_world' in 40 -- existing indices are untouched, but a pre-41
//     client receiving a set-attr for a trailing index it doesn't have
//     would fail its GetAttribute precondition, so we raise the hosting
//     floor along with the max.
//
// 42: New prop-node 'rotate' quaternion attr (w, x, y, z; readable and
//     writable, applied at body creation if set beforehand) and
//     globals-node 'gravity' float-array attr (per-scene ode world
//     gravity). From public PR #959 / issue #948. Both appended at the
//     end of their type's attr tables per the standing rule (see 40/41
//     above), and the hosting floor rises with the max as usual so
//     pre-42 clients never see indices they lack.
//
//     RETROACTIVE NOTE: this bump shipped BROKEN in dev/alpha builds
//     2026-08-12..2026-08-18. The append rule has a wrinkle 42 missed:
//     attr wire indices are assigned in C++ construction order, and
//     base-class attrs construct before subclass attrs -- so appending
//     'rotate' to the prop base table INSERTED it mid-table for the
//     derived bomb type, shifting bomb's 'fuse_length' from 22 to 23
//     and breaking every pre-42 stream containing a fused bomb (old
//     servers and replays connect an animcurve into index 22, which
//     resolved to the float-array 'rotate' -> instant session error).
//     Fixed in 43.
//
// 43: Repair of 42's bomb-table breakage; no new features. Prop-node
//     'rotate' is now registered with kNodeAttributeFlagLateIndex, so
//     it takes its index AFTER any subclass attrs: prop keeps rotate=22
//     (same as 42 intended) and bomb returns to its historical
//     fuse_length=22 with rotate=23. Builds speaking broken-42 tables
//     are fenced off by the version bump (disposable dev/alpha builds
//     only; 42 never reached a stable release).
//
//     STANDING RULE, amended: appending an attr to a node type's table
//     keeps existing indices stable ONLY for types nothing derives
//     from. When adding an attr to a type with subclasses (currently
//     just prop -> bomb), register it with the late-index flag (see
//     BA_*_ATTR_LATE macros / kNodeAttributeFlagLateIndex) so subclass
//     attrs keep their positions. tests/test_scene_v1's golden
//     attr-table test pins every index; a diff there means a protocol
//     bump (or a mistake).

// Sim step size in milliseconds.
const int kGameStepMilliseconds = 8;

// Sim step size in seconds.
const float kGameStepSeconds =
    (static_cast<float>(kGameStepMilliseconds) / 1000.0f);

// Magic numbers at the start of our file types.
const int kBrpFileID = 83749;

// Largest UDP packets we attempt to send.
// (is there a definitive answer on what this should be?)
const int kMaxPacketSize = 700;

// Predeclare types we use throughout our FeatureSet so most headers can get
// away with just including this header.
class ClientControllerInterface;
class ClientInputDevice;
class ClientSession;
class SceneCollisionMesh;
class Collision;
class Connection;
class ConnectionToClient;
class ConnectionToClientUDP;
class ConnectionToHost;
class ConnectionToHostUDP;
class ConnectionSet;
class SceneV1Context;
class ContextRefSceneV1;
class Huffman;
class SceneCubeMapTexture;
class SceneDataAsset;
class Dynamics;
class SceneV1FeatureSet;
class GlobalsNode;
class HostSession;
struct JointFixedEF;
class SceneV1InputDeviceDelegate;
class MaterialAction;
class SceneMesh;
class HostActivity;
class Material;
class MaterialComponent;
class MaterialConditionNode;
class MaterialContext;
class Node;
class NodeAttribute;
class NodeAttributeConnection;
class NodeAttributeUnbound;
class NodeType;
class Part;
class Player;
class PlayerNode;
class PlayerSpec;
class PythonClassSceneDataAsset;
class PythonClassSceneCollisionMesh;
class PythonClassMaterial;
class PythonClassSceneMesh;
class PythonClassSessionPlayer;
class PythonClassSceneSound;
class PythonClassSceneTexture;
class SceneV1Python;
class ClientSessionReplay;
class RigidBody;
class SessionStream;
class Scene;
class SceneV1FeatureSet;
class Session;
class SceneSound;
class SceneTexture;
class ReplayWriter;
class InstantReplayRecorder;
class ClientSessionInstantReplay;
typedef Node* NodeCreateFunc(Scene* sg);

/// Specifies the type of time for various operations to target/use.
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
enum class TimeType : uint8_t {
  kSim,
  kBase,
  kReal,
  kLast  // Sentinel.
};

/// Standard messages to send to nodes.
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

/// Command values sent across the wire in netplay.
/// Must remain consistent across versions!
enum class SessionCommand {
  kBaseTimeStep,
  kStepSceneGraph,
  kAddSceneGraph,
  kRemoveSceneGraph,
  kAddNode,
  kNodeOnCreate,
  kSetForegroundScene,
  kRemoveNode,
  kAddMaterial,
  kRemoveMaterial,
  kAddMaterialComponent,
  kAddTexture,
  kRemoveTexture,
  kAddMesh,
  kRemoveMesh,
  kAddSound,
  kRemoveSound,
  kAddCollisionMesh,
  kRemoveCollisionMesh,
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
  kSetNodeAttrMesh,
  kSetNodeAttrMeshNull,
  kSetNodeAttrMeshes,
  kSetNodeAttrCollisionMesh,
  kSetNodeAttrCollisionMeshNull,
  kSetNodeAttrCollisionMeshes,
  kPlaySoundAtPosition,
  kPlaySound,
  kEmitBGDynamics,
  kEndOfFile,
  kDynamicsCorrection,
  kScreenMessageBottom,
  kScreenMessageTop,
  kAddData,
  kRemoveData,
  kCameraShake,
  // (protocol 39+) Declare one entry of the session's asset-package
  // table: (index, total, apverid). The full table -- the session's
  // fixed package universe -- is declared up front at the start of the
  // stream / baseline dump, in index order; wire asset/string refs
  // resolve against it by index.
  kDeclareAssetPackage,
  // (protocol 39+) Compact indexed forms of the kAdd<Asset> commands
  // for package-housed assets: (scene, id, pkg_idx, asset_idx), where
  // pkg_idx indexes the stream's declared package table and asset_idx
  // indexes the canonical sorted logical-path list of the package's
  // relevant bucket kind (portable across flavors by the D23/D24
  // identical-key-set invariant; collision meshes use the constant
  // bucket). The string kAdd<Asset> forms remain for local
  // non-package assets (and old streams).
  kAddTextureIndexed,
  kAddMeshIndexed,
  kAddSoundIndexed,
  kAddCollisionMeshIndexed,
  // (protocol 40+) Request physical feedback (rumble/haptics) for
  // whoever is controlling a player: (player_id, json_payload). Clients
  // filter to their own devices and drop the rest; a client with no
  // device on that player (including any client during replay playback)
  // ignores it entirely.
  //
  // FRAMING IS FROZEN AS OF PROTOCOL 40 AND MUST NEVER CHANGE. The
  // payload is an opaque length-prefixed string, so a client that cannot
  // make sense of its contents reads it, discards it, and stays in sync
  // with the stream -- that is the entire forward-compatibility story
  // for this feature. It only holds while this stays ONE command with
  // NO additional binary fields; everything future goes inside the json
  // dict, whose keys are all optional with client-side defaults. Adding
  // a second feedback command or a new binary field would be a hard
  // protocol break, because unrecognized commands cannot be skipped (see
  // ClientSession's command dispatch). See decisions D1/D2 in
  // docs/initiatives/controller-force-feedback.md.
  kInputDeviceFeedback
};

enum class NodeCollideAttr {
  /// Whether or not a collision should occur at all.
  /// If this is false for either node in the final context_ref,
  /// no collide events are run.
  kCollideNode
};

enum class PartCollideAttr {
  /// Whether or not a collision should occur at all.
  /// If this is false for either surface in the final context_ref,
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

enum NodeAttributeFlag {
  kNodeAttributeFlagReadOnly = 1u,
  // Lang-str-capable string attr: at protocol 39+ its wire payload is
  // a kLangStrWireTag*-tagged value (see those constants). The flag
  // set is part of the protocol contract -- re-flagging an attr after
  // a protocol ships requires a protocol bump.
  kNodeAttributeFlagLangStr = 2u,
  // Defer this attr's wire-index assignment until the node type is
  // fully constructed (NodeType::FinalizeAttrIndices). Required when
  // appending an attr to a node type that has subclasses: base-class
  // attrs construct before subclass attrs, so a plain append to a base
  // table would land mid-table in derived types and shift their attrs'
  // wire indices (the protocol-42 bomb 'fuse_length' breakage; see the
  // protocol-changes list above). Late attrs take indices after ALL
  // normally-registered attrs, in declaration order.
  kNodeAttributeFlagLateIndex = 4u,
};

// First protocol whose lang-str-flagged string slots carry tagged
// payloads (streams below this use the legacy raw-or-resource-json
// forms).
const int kProtocolVersionLangStrWire = 39;

// (protocol 39+) First byte of the payload carried by
// lang-str-flagged string slots (the text node's `text` attr and the
// screen-message session commands). Control chars, so untagged legacy
// text (attr connections, old-stream values passing through shared
// code) can never collide. A payload not starting with one of these
// is treated with legacy raw-or-resource-json semantics.
//
// INGEST CONTRACT: consumers of the kLangStrWireTagLangStr leg parse
// and evaluate wire-supplied refs with NO resolve step -- which is
// only sound at ingest points where a verified context already
// structurally guarantees the referenced packages are locally
// resolved (streams: the arrive-ready prep contract + handshake gate;
// messages: an established prepped connection). Out-of-context refs
// fail visibly (LANGSTR_ERROR); wire data must never trigger
// client-side resolve/download machinery. Any NEW ingest point must
// establish an equivalent guarantee first -- see the D28 trust model
// and D33 in docs/initiatives/strings-asset-migration.md.
inline constexpr char kLangStrWireTagLiteral = '\x01';     // verbatim text
inline constexpr char kLangStrWireTagLegacyJson = '\x02';  // legacy Lstr json
inline constexpr char kLangStrWireTagLangStr = '\x03';     // LangStr json
                                                           // (indexed refs)

// First build whose BA_JMESSAGE_SCREEN_MESSAGE receive path tolerates a
// missing legacy 'm' field (rendering the tagged 'm2' form alone). When a
// peer's reported build is at or above this, hosts send ONLY the tagged
// lang-str form; older peers get ONLY the legacy flat/resource-json 'm'.
// Build-number gating (not protocol) is correct here: this is transient
// message-layer traffic, never stored in streams/replays (see the note
// above kProtocolVersionHostMin). The tagged form's indexed refs remain
// sound because we never host below kProtocolVersionLangStrWire
// (kProtocolVersionHostMin exceeds it), so every connected client did the
// package-universe prep at join.
inline constexpr int kScreenMessageLangStrOnlyMinBuild = 22962;

// Minimum peer build for the instant-replay begin/end messages (see
// BA_MESSAGE_INSTANT_REPLAY_BEGIN). Build-number gating rather than
// protocol for the same reason as above: these are transient
// message-layer traffic, never stored in a stream, and the clip itself
// rides as ordinary session messages any client already understands.
// Older peers simply see the stream pause for the length of the clip
// and are resynced by the keyframe that follows it.
inline constexpr int kInstantReplayMinBuild = 23006;

// Which asset-package bucket kind a scene asset type's wire indices
// derive from (see the kAdd*Indexed commands). Collision meshes live
// in the flavor-invariant constant bucket (asset-packages decision
// #26); the rest each have a flavored bucket kind of their own.
enum class AssetBucketKind : uint8_t {
  kTextures,
  kAudio,
  kMeshes,
  kConstant,
};

inline auto IsLangStrWireTagged(const std::string& val) -> bool {
  return !val.empty()
         && (val[0] == kLangStrWireTagLiteral
             || val[0] == kLangStrWireTagLegacyJson
             || val[0] == kLangStrWireTagLangStr);
}

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
  kMesh,
  kMeshArray,
  kCollisionMesh,
  kCollisionMeshArray
};

// Our feature-set's globals.
// Feature-sets should NEVER directly access globals in another feature-set's
// namespace. All functionality we need from other feature-sets should be
// imported into globals in our own namespace. Generally we do this when we
// are initially imported (just as regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern SceneV1FeatureSet* g_scene_v1;

class SceneV1FeatureSet : public FeatureSetNativeComponent {
 public:
  /// Called when our associated Python module is instantiated.
  static void OnModuleExec(PyObject* module);

  /// Instantiate our FeatureSet if needed and return the single
  /// instance of it. Basically a Python import statement.
  static auto Import() -> SceneV1FeatureSet*;

  void Reset();

  void ResetRandomNames();
  // Given a full name "SomeJoyStick #3" etc, reserves/returns a persistent
  // random name for it.
  auto GetRandomName(const std::string& full_name) -> std::string;

  const auto& node_types_by_id() const { return node_types_by_id_; }
  const auto& node_message_types() const { return node_message_types_; }
  const auto& node_message_formats() const { return node_message_formats_; }
  const auto& node_types() const { return node_types_; }

  // Our subcomponents.
  SceneV1Python* const python;
  Huffman* const huffman;

  // FIXME: should be private.
  int session_count{};
  bool replay_open{};

 private:
  void SetupNodeMessageType_(const std::string& name, NodeMessageType val,
                             const std::string& format);

  SceneV1FeatureSet();
  std::unordered_map<std::string, NodeType*> node_types_;
  std::unordered_map<int, NodeType*> node_types_by_id_;
  std::unordered_map<std::string, NodeMessageType> node_message_types_;
  std::vector<std::string> node_message_formats_;
  std::unordered_map<std::string, std::string>* random_name_registry_{};
  std::list<std::string> default_names_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SCENE_V1_H_
