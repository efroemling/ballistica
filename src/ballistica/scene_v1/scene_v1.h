// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SCENE_V1_H_
#define BALLISTICA_SCENE_V1_SCENE_V1_H_

#include <list>
#include <unordered_map>
#include <vector>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/feature_set_native_component.h"
#include "ballistica/shared/python/python_ref.h"

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
// (new/removed/changed nodes, attrs, data files, behavior, etc.)

// Note that the packet/gamepacket/message layer can vary more organically
// based on build-numbers of connected clients/servers since none of that
// data is stored; this just needs to be observed for all the scene stuff
// that goes into replays since a single stream can get played/replayed on
// different builds (as long as they support that protocol version).
const int kProtocolVersion = 33;

// Oldest protocol version we can act as a client to. This can generally be
// left as-is as long as only new nodes/attrs/commands are added and
// existing stuff is unchanged.
const int kProtocolVersionMin = 24;

// FIXME: We should separate out connection protocol from scene protocol. We
//  want to be able to watch really old replays if possible but being able
//  to connect to old clients is much less important (and slows progress).

// Protocol additions:
// 25: added a few new achievement graphics and new node attrs for displaying
// stuff in front of the UI
// 26: added penguin
// 27: added templates for LOTS of characters
// 28: added cyborg and enabled fallback sounds and textures
// 29: added bunny and eggs
// 30: added support for resource-strings in text-nodes and screen-messages
// 31: added support for short-form resource-strings, time-display-node, and
// string-to-string attr connections
// 32: added json based player profiles message, added shield
//     alwaysShowHealthBar attr
// 33: handshake/handshake-response now send json dicts instead of
//     just player-specs
// 34: new image_node enums, data assets.

// Sim step size in milliseconds.
const int kGameStepMilliseconds = 8;

// Sim step size in seconds.
const float kGameStepSeconds =
    (static_cast<float>(kGameStepMilliseconds) / 1000.0f);

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
class SceneV1AppMode;
class SceneV1FeatureSet;
class Session;
class SceneSound;
class SceneTexture;
typedef Node* NodeCreateFunc(Scene* sg);

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
  kRemoveData
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

 private:
  void SetupNodeMessageType(const std::string& name, NodeMessageType val,
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
