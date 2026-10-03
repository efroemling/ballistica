// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SCENE_V1_H_
#define BALLISTICA_SCENE_V1_SCENE_V1_H_

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/scene_v1/generated/scene_asset_set.h"
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
namespace ballistica::ui_v1 {
class UIV1FeatureSet;
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
const int kProtocolVersionHostMin = 50;

// Oldest protocol version we can act as a client to. This can generally be
// left as-is as long as only new nodes/attrs/commands are added and old
// behavior remains the same when not using the new stuff.
const int kProtocolVersionClientMin = 24;

// Newest protocol version we can act as a client OR host for.
const int kProtocolVersionMax = 50;

// The 1.8 development protocols (38 through the one before 1.8's
// final). Only pre-1.8 protocols (37 and below) and the one 1.8 ships
// on are supported (Eric, 2026-10-01); these intermediate ones' streams
// are no longer decoded (47 redid much of what they carried), so a
// leftover dev host or replay on one is refused like any unsupported
// version rather than mis-decoded. Raise the max alongside
// kProtocolVersionMax for any further bump before 1.8 ships.
const int kProtocolVersionDevGapMin = 38;
const int kProtocolVersionDevGapMax = 49;
static_assert(kProtocolVersionDevGapMax == kProtocolVersionMax - 1,
              "Every 1.8 dev protocol below the current one is in the gap.");

/// Whether we can act as a client to (or play a replay of) a stream
/// protocol.
inline auto IsJoinableHostProtocol(int version) -> bool {
  return version >= kProtocolVersionClientMin && version <= kProtocolVersionMax
         && !(version >= kProtocolVersionDevGapMin
              && version <= kProtocolVersionDevGapMax);
}

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
//
// 44: On-the-fly character skins (docs/initiatives/character-skins.md).
//     Session-level Character definitions -- new kAddCharacter /
//     kRemoveCharacter commands carrying an opaque json string, with the
//     same add/remove/baseline lifecycle as materials -- and a new spaz-
//     node 'character' attr of a new attr type (kCharacter, plus the
//     kSetNodeAttrCharacter[Null] commands), appended last so no existing
//     index moves (spaz has no subclasses so no late-index flag needed).
//     When set it replaces the explicit mesh/texture/sound attrs, style,
//     and highlight entirely: physique and look both come from the
//     definition, with the app-mode-supplied standin (standard spaz)
//     drawn until the definition's media is local. Hosts at 44+ can
//     therefore hand a joiner any character it brings, so a client that
//     joins a host below kProtocolVersionCharacterSkins shows a one-time
//     yellow warning that some newer characters may render as older
//     ones there (see ConnectionToHost). The hosting floor rises with
//     the max as usual so every host we run is on the far side of that
//     line.
//
//     Also under 44: the 'characterdisplay' node type (appended last), a 2d
//     overlay drawing a Character's icon and/or name -- the in-scene twin
//     of ui_v1's character widget (lobby choosers, scoreboards).
//
//     Also under 44 (landed before it reached public builds): the
//     'localdisplay' node type, appended last in the node-type table so
//     no existing type id moves. It carries a json 'config' string and a
//     'visible' bool; every machine that receives it (host included)
//     runs its own LocalDisplayContext -- a private stream-less scene
//     driven by a Python bascenev1.LocalDisplay built from the config --
//     so one streamed node yields per-machine content (the controls
//     guide showing each player their own controller's button names).
//
//     Also under 44 (same reason): the spaz punch region and
//     punch_velocity come from a synthetic fist -- a spring-damper model
//     of the punching hand driven by the torso frame and the punch
//     phase (SpazPose) -- instead of the lower-arm body, so nothing in
//     gameplay reads a limb body any more (the first step toward
//     simulating limbs on the bg-dynamics thread). Older protocols keep
//     the arm-attached form; a scene's protocol_version() picks.
//
//     Also under 44 (same reason): spaz limbs live on the bg-dynamics
//     rig instead of the main sim (no limb bodies there at all), and a
//     globals-node bool 'legacy_spaz_limbs', appended last, lets an
//     activity keep the old main-sim limbs for content calibrated
//     against them (the tutorial's recorded input script).
//
//     Also under 44 (same reason): compact stream framing
//     (docs/initiatives/bandwidth.md). Session-command messages were
//     [u16 length][cmd][int32 args...] with every integer a full int32
//     (node ids, attr indices, counts, bools, string lengths, the 8ms
//     time delta): eleven bytes of framing around a four-byte float,
//     nine bytes for a time step. Now the command length prefix and
//     every integer field are LEB128 varints (integers zigzag-encoded,
//     so small negatives stay one byte); floats and raw chars are
//     unchanged and command ids/order are untouched. Roughly halves
//     the command stream on an 8-bot stress test. Streams declare
//     their protocol (handshake / replay header), so older streams
//     still decode with the fixed layout: SessionStream::compact_ and
//     ClientSession::compact_stream() are the two switches
//     (kProtocolVersionCompactStream). Dev replays recorded under 44
//     before this landed no longer play.
//
//     Also under 44 (same reason): zstd game-packet compression with a
//     trained dictionary (docs/design/packet-compression.md) replaces
//     the per-byte huffman between 44+ peers: ~0.70 vs ~0.90 on a
//     stress test at the same CPU. Per packet, not per stream: a
//     receiver tells raw / huffman / zstd apart from the first byte,
//     so the handshake (sent before a peer's version is known) stays
//     huffman and everything after switches. The dictionary is
//     bacommon's packets_v1.zstddict; a new dictionary means a new
//     protocol version, since both ends must hold the same bytes
//     (kProtocolVersionZstdPackets). Older peers keep huffman.
//
//     Also under 44: compact physics corrections
//     (kProtocolVersionCompactCorrections). Per body: a flag byte,
//     position as 3 x int24 millimetres, orientation as a packed
//     smallest-three quaternion (4 bytes), f16 for each non-zero
//     velocity component; node ids / counts / resync lengths are
//     varints and the per-body length prefix is gone (the flag byte
//     fixes the size). ~36 -> ~26 bytes per moving body plus ~8 per
//     node. Writer: Scene::GetCorrectionMessageCompact_ /
//     RigidBody::EmbedCompact; reader: ClientSession's
//     kDynamicsCorrection compact branch / RigidBody::ExtractCompact.
//     Older streams keep the f32/f16 layout.
//
//     Also under 44: unreliable multipart packets
//     (BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART,
//     kProtocolVersionUnreliableParts), which is what lets physics
//     corrections go unreliable. A correction is split into <= 32
//     parts sharing one unreliable number; the receiver keeps one
//     partial at a time and applies a message only once every part is
//     in (all-or-nothing: correcting some bodies but not others is a
//     sim explosion), only after it has processed the reliable
//     messages that preceded it, and at most 2 reliable messages
//     (~16ms) behind. A lost part means that correction is simply
//     superseded by the next one instead of stalling the in-order
//     reliable stream for a resend round trip. Older peers keep
//     reliable corrections. Dev aids: test_game_run --packet-loss N
//     and --reliable-corrections (the A/B switch).
//
//     Also under 44: wide acks (kProtocolVersionWideAcks). Every game
//     packet carries the receiver's next-wanted reliable number plus a
//     have-bitfield for the messages after it; that field grows from 8
//     to 32 bits (256ms of stream at 125 msgs/s instead of 64ms), so
//     several gaps get resent in one round trip instead of one per
//     round trip. Self-describing per packet (kPacketWideAcksFlag on
//     the type byte), so no handshake ordering issues. Alongside, two
//     protocol-neutral fixes: a receiver with a gap acks within 20ms
//     instead of riding the 100ms keepalive, and a sender resends a
//     message the peer has evidently lost (they have later ones) on a
//     short fuse instead of the doubling backoff. Before this a client
//     fell ~130 messages/s behind at 20% loss and was pruned.
//
//     Also under 44: bigger packets (kProtocolVersionBigPackets,
//     kMaxPacketSizeBig = 1200 vs the huffman-era 700, and reliable
//     multipart chunks sized to it instead of 480). Fewer packets per
//     correction and per big command message; ~6% fewer packets on the
//     8-bot stress test.
//
//     Also under 44: kStepSceneGraphAndTime (kProtocolVersionMergedStep)
//     folds a scene step and the time step right behind it into one
//     command. Encoding-only: the client runs the same two operations
//     in the same order at the same time, and pacing sees one time
//     step of the same delta in the same packet. ~0.5 KB/s raw on the
//     8-bot stress test.
//
//     Also under 44: kAddAnimCurve (kProtocolVersionAnimCurveCommand)
//     carries a whole bs.animate() -- node add, four attr sets,
//     OnCreate, two connects -- as one command. The host still performs
//     all of those itself; the writer just holds their commands aside
//     (SessionStream::BeginFold) and writes the one command instead
//     (or replays them if anything throws). Encoding-only.
//
//     Also under 44 (kProtocolVersionPackedCommands): two wire-only
//     packings the client expands back into the original commands on
//     receipt, so nothing downstream can tell: kTimeStepSceneGraphAndTime
//     (the time step opening a message + the first scene step + its
//     time step) and kAddNodeWithAttrs (newnode(attrs): add, attr sets,
//     OnCreate).
//
// 45: Depictions (docs/initiatives/depictions.md). The
//     'depictiondisplay' node type (appended last), a 2d overlay hosting a
//     bacommon.depiction from its json string ('depiction' attr) -- the
//     in-scene twin of ui_v1's DepictionSlot; every machine makes its
//     own depiction from the json, so a kind it can't draw is its
//     placeholder. A new *kind* on the stream therefore also needs a
//     protocol bump; new tiers within a kind don't. 44's
//     'characterdisplay' stays (it is still how 44 hosts draw), but
//     nothing new uses it.
//
// 46: Numeric asset-package ids (efrohome
//     docs/global_initiatives/numeric-package-ids.md). Packages are
//     named by their version's numeric id everywhere on the stream --
//     kDeclareAssetPackage, qualified asset refs ('145:textures/foo'),
//     depiction and character json -- where 45 used string ids
//     ('a-0.babuiltinassets.260927'). No wire shape changed; the bump
//     just keeps the two naming schemes from ever meeting in one game.
//
// 47: Character parts as independent scene objects (depictions.md,
//     2026-10-01). A character is only a delivery bundle now; the
//     scene holds its parts. kAddSpazDef (44's kAddCharacter, same
//     command) carries a spaz block alone rather than a whole character.
//     New session-level depiction objects (kAddDepiction /
//     kRemoveDepiction / kSetNodeAttrDepiction[Null],
//     NodeAttributeType::kDepiction) let a name or icon be registered
//     once and referenced by id from any node; depictiondisplay's
//     'depiction' attr takes one (it took a json string at 45/46). The
//     characterdisplay node type is gone. Also from here on: only
//     pre-1.8 protocols (37 and below) and the final 1.8 one are
//     supported as a client (kProtocolVersionDevGapMin/Max, Eric,
//     2026-10-01), so nothing above keeps decode paths for 38-46 alone.
//
// 48: Player icons as depictions in screen messages (cloud-profiles
//     icon sites, 2026-10-01). kScreenMessageTopDepiction (appended
//     last) carries a top message's icon as a session-level depiction
//     id, so kill/score announcements show a cloud profile's own icon;
//     kScreenMessageTop's texture pair stays for legacy icons.
//
//     Also under 48 -- third tint colors (2026-10-02; two parallel
//     sessions both opened 48 before either went public, so they
//     share it). Image nodes gain 'tint3_color' (appended so existing
//     indices hold), and kScreenMessageTop carries a third icon tint
//     (12 floats, was 9; kProtocolVersionTint3). Characters get theirs
//     only from their definitions ('hl2' in spaz/icon json -- the
//     color mask's blue channel); there is no spaz node attr, since
//     legacy masks carry stray blue data. Every third tint defaults to
//     white, the colorize no-op, so anything not setting one -- older
//     hosts included -- draws exactly as before.
//
// 49: Spaz-def colors as an explicit choice (character-skins.md,
//     2026-10-03). Spaz nodes gain 'use_spaz_def_color' and
//     'use_spaz_def_highlight' (appended, default false): when on, a
//     definition-form spaz draws its definition's own color/highlight;
//     otherwise the color/highlight attrs, which now apply to highlight
//     too (48 ignored the highlight attr in definition form). The
//     color/highlight getters now read back the attrs rather than the
//     drawn values, so late-joiner dumps reproduce the node exactly
//     (48 baked whatever the host was drawing into the attr).
//
//     Also under 49 -- shield nodes gain 'health_bar_display' (an int,
//     appended; bascenev1.HealthBarDisplay), from community PR #966
//     reworked to sit alongside the legacy 'always_show_health_bar'
//     bool, which it defers to while 0 (DEFAULT). Unknown values count
//     as DEFAULT.
//
// 50: Prop nodes (and so bombs) gain 'stickiness' (a float, clamped to
//     0.01-10.0, default 1.0): scales how strongly a 'sticky' prop
//     sticks. Registered late-index like 'rotate' (see 43) so bomb's
//     'fuse_length' keeps its index. Host-side physics only; clients
//     just carry the value, and older hosts never set it.
//
//     Also under 50 -- spaz nodes gain boxing-glove look overrides
//     (appended): 'boxing_gloves_mesh', 'boxing_gloves_color_texture'
//     (unset means the stock gloves), 'boxing_gloves_color' (a
//     multiply tint, default white) and 'boxing_gloves_scale' (default
//     1.0). Visual only; punch reach is unchanged.
//
//     Also under 50 -- globals nodes gain 'legacy_spaz_punch'
//     (appended): spazzes created with legacy limbs under it also keep
//     the pre-44 arm-attached punch region. With 'legacy_spaz_limbs'
//     that is the old spaz physics in full, which the server config's
//     'legacy_spaz_physics' turns on for every activity (for the
//     'bomb-jump' trick, at a bandwidth cost).

// First protocol with the compact (varint) stream framing; see the 44
// entry above.
const int kProtocolVersionCompactStream = 44;

// First protocol whose peers compress game packets with zstd and the
// bacommon packets_v1 dictionary (see the 44 entry above). A peer at or
// above this gets zstd once the handshake has established its version.
const int kProtocolVersionZstdPackets = 44;

// First protocol with the compact physics-correction encoding (see the
// 44 entry above): varint framing, int24-mm positions, packed
// smallest-three quaternions.
const int kProtocolVersionCompactCorrections = 44;

// First protocol whose peers accept unreliable multipart packets
// (BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART; see the 44 entry above).
// Physics corrections go unreliable to such peers.
const int kProtocolVersionUnreliableParts = 44;

// First protocol whose peers understand the 32-bit ack have-bitfield
// (kPacketWideAcksFlag on the packet type; see the 44 entry above).
const int kProtocolVersionWideAcks = 44;

// First protocol whose peers accept packets up to kMaxPacketSizeBig
// (the huffman-era decoder capped at kMaxPacketSize; 44+ peers decode
// zstd/raw with no such cap). Reliable multipart chunks and unreliable
// parts to such peers are sized to it.
const int kProtocolVersionBigPackets = 44;

// First protocol whose streams may carry kStepSceneGraphAndTime (a
// scene step and the time step that follows it as one command).
const int kProtocolVersionMergedStep = 44;

// First protocol whose streams may carry kAddAnimCurve (a bs.animate as
// one command; SessionStream's fold scope).
const int kProtocolVersionAnimCurveCommand = 44;

// First protocol whose streams may carry kTimeStepSceneGraphAndTime and
// kAddNodeWithAttrs (wire-only packings expanded on receipt).
const int kProtocolVersionPackedCommands = 44;

// First protocol whose hosts can supply character skins on the fly;
// joining anything older gets the older-host character warning.
const int kProtocolVersionCharacterSkins = 44;

// First protocol whose spaz punch region follows the synthetic fist
// (SpazPose) rather than the lower-arm body.
//
// Where to gate on protocol: stream encoding/decoding, handshakes and
// replay files key off the session/connection/file protocol they
// already hold (ClientSession::stream_protocol, ConnectionToHost,
// ReplayWriter); anything the *sim* does differently -- node behavior
// like this punch change -- keys off Scene::protocol_version(), which
// those owners stamp on every scene they create.
const int kProtocolVersionSyntheticPunch = 44;
// Same bump: with the punch region on the synthetic fist, the arms and
// legs no longer feed any game logic and can live on the bg-dynamics
// rig instead of the main sim (SpazNode::UseBgLimbs_).
const int kProtocolVersionBgLimbs = kProtocolVersionSyntheticPunch;

// Sim step size in milliseconds.
const int kGameStepMilliseconds = 8;

// Sim step size in seconds.
const float kGameStepSeconds =
    (static_cast<float>(kGameStepMilliseconds) / 1000.0f);

// Magic numbers at the start of our file types.
const int kBrpFileID = 83749;

// Largest UDP packets we attempt to send to legacy peers (and the
// largest a huffman-era receiver decodes); see kMaxPacketSizeBig.
const int kMaxPacketSize = 700;

// Largest packets to kProtocolVersionBigPackets peers. 1200 bytes is the
// widely-tested path floor (QUIC's minimum initial datagram; IPv6's
// 1280 minimum MTU minus headers), so it avoids IP fragmentation
// without path-MTU discovery. Compression only ever shrinks a packet
// (raw fallback otherwise), so this bounds the wire size too. An
// 8-player correction (~1.15 KB) fits in one packet at this size.
const int kMaxPacketSizeBig = 1200;

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
class ZstdPacketCodec;
class HostSession;
class SceneV1InputDeviceDelegate;
class MaterialAction;
class SceneMesh;
class HostActivity;
class LocalDisplayContext;
class LocalDisplayNode;
class LocalSceneContext;
class SceneViewerContext;
class Material;
class SpazDef;
class SceneDepiction;
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
  // Never written (data assets are host-only; see SceneDataAsset); kept
  // because command values are positional.
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
  kInputDeviceFeedback,

  // (protocol 44+) Session-level spaz definitions (see
  // docs/initiatives/character-skins.md). kAddSpazDef carries
  // (scene-id, spaz-def-id) plus a length-prefixed json string that
  // is parsed natively and never interpreted by the stream layer: a
  // spaz block (44-46 called this kAddCharacter and sent whole
  // characters); the spaz node's typed 'spaz_def' attr references one
  // by id.
  kAddSpazDef,
  kRemoveSpazDef,
  kSetNodeAttrSpazDef,
  kSetNodeAttrSpazDefNull,

  // (protocol 44+) A kStepSceneGraph immediately followed by a
  // kBaseTimeStep, folded into one command (scene-id, step-ms): the
  // client performs exactly those two operations in that order, so it
  // is encoding-only (2 bytes of framing per sim step). ~96% of scene
  // steps are directly followed by a time step, so the writer folds
  // nearly all of them (SessionStream::SetTime).
  kStepSceneGraphAndTime,

  // (protocol 44+) One bs.animate(): the animcurve node's creation, its
  // times/offset/values/loop, its OnCreate and the two attribute
  // connections (globals.time -> curve.in, curve.out -> target.attr) as
  // a single command. Ints: scene, node-type, curve id, globals id,
  // time attr, in attr, out attr, target id, target attr, offset, loop,
  // count, times[count]; then floats values[count]. The client performs
  // exactly the eight operations the separate commands would have, in
  // the same order (encoding-only; ~60% fewer raw bytes per curve).
  kAddAnimCurve,

  // (protocol 44+) A kBaseTimeStep, a kStepSceneGraph and the
  // kBaseTimeStep after it as one command (pre-delta, scene-id,
  // post-delta). Pure wire encoding: the client expands it back into
  // kBaseTimeStep + kStepSceneGraphAndTime on receipt
  // (ClientSession::ExpandPackedCommand_), so execution, pending
  // release and pacing are byte-for-byte what the separate commands
  // gave. Folds the time step that opens nearly every message.
  kTimeStepSceneGraphAndTime,

  // (protocol 44+) One newnode(attrs): kAddNode, its initial attr sets
  // and kNodeOnCreate as one command: scene, type, id, count, then per
  // attr set [cmd byte][its body minus the node id]. Also pure wire
  // encoding, expanded on receipt into the original commands (the
  // client re-splits the attr bodies from a per-command value layout
  // table; only commands in that table are packed, see
  // SessionStream::CommitFoldAddNode / kPackableAttrCommands).
  kAddNodeWithAttrs,

  // (protocol 47+) Session-level depiction objects (see
  // docs/initiatives/depictions.md): a bacommon.depiction json
  // registered once and referenced by id from node attrs
  // (NodeAttributeType::kDepiction). Same shape and lifecycle as the
  // spaz-def commands: kAddDepiction carries (scene-id, depiction-id)
  // plus a length-prefixed json string.
  kAddDepiction,
  kRemoveDepiction,
  kSetNodeAttrDepiction,
  kSetNodeAttrDepictionNull,

  // (protocol 48+) A top screen-message whose icon is a session-level
  // depiction (a player's cloud icon) rather than kScreenMessageTop's
  // texture pair: (depiction-id), the message string, then its rgb.
  kScreenMessageTopDepiction
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

// First protocol whose kScreenMessageTop carries a third icon tint
// (12 floats rather than 9; see the 48 entry above).
const int kProtocolVersionTint3 = 48;

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
  kCollisionMeshArray,
  // (protocol 44+) A session-level SpazDef reference.
  kSpazDef,
  // (protocol 47+) A session-level SceneDepiction reference.
  kDepiction
};

// Our feature-set's globals.
// Feature-sets should NEVER directly access globals in another feature-set's
// namespace. All functionality we need from other feature-sets should be
// imported into globals in our own namespace. Generally we do this when we
// are initially imported (just as regular Python modules do).
extern core::CoreFeatureSet* g_core;
extern base::BaseFeatureSet* g_base;
extern SceneV1FeatureSet* g_scene_v1;
extern ui_v1::UIV1FeatureSet* g_ui_v1;

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

  /// The assets our node layer draws itself with, supplied by the
  /// active app-mode (see bascenev1.set_scene_asset_set). Nodes only
  /// exist within sessions, which only exist under an activated
  /// app-mode, so drawing code can rely on every member being
  /// present. Asserts in debug builds if that ordering ever breaks.
  auto assets() -> const SceneV1AssetSet& {
    assert(scene_assets_.complete());
    return scene_assets_;
  }

  /// Do we currently hold a complete asset set?
  auto have_assets() const -> bool { return scene_assets_.complete(); }

  /// Supply the art for as long as the current app-mode is active.
  /// The Python layer wipes it via clear_assets() at each app-mode
  /// switch (SceneV1AppSubsystem.reset()), so an incoming app-mode
  /// can never inherit the outgoing one's art.
  void set_assets(const SceneV1AssetSet& assets) { scene_assets_ = assets; }

  /// Drop any app-mode-supplied art. Called at app-mode switches.
  void clear_assets() { scene_assets_ = SceneV1AssetSet(); }

  const auto& node_types_by_id() const { return node_types_by_id_; }
  const auto& node_message_types() const { return node_message_types_; }
  const auto& node_message_formats() const { return node_message_formats_; }
  const auto& node_types() const { return node_types_; }

  // Our subcomponents.
  SceneV1Python* const python;
  Huffman* const huffman;
  // zstd game-packet codec; installed from Python at app start
  // (bascenev1's app subsystem hands over the dictionary). Null until
  // then, in which case connections stay on huffman.
  ZstdPacketCodec* zstd_packets{};

  // FIXME: should be private.
  int session_count{};
  bool replay_open{};

 private:
  void SetupNodeMessageType_(const std::string& name, NodeMessageType val,
                             const std::string& format);

  SceneV1FeatureSet();
  SceneV1AssetSet scene_assets_;
  std::unordered_map<std::string, NodeType*> node_types_;
  std::unordered_map<int, NodeType*> node_types_by_id_;
  std::unordered_map<std::string, NodeMessageType> node_message_types_;
  std::vector<std::string> node_message_formats_;
  std::unordered_map<std::string, std::string>* random_name_registry_{};
  std::list<std::string> default_names_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SCENE_V1_H_
