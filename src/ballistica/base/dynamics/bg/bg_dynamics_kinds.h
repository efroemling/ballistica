// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_KINDS_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_KINDS_H_

#include <tuple>
#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics_channel.h"
#include "ballistica/base/dynamics/joint_fixed_ef.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// Shadow-caster entity: feed a world position each step, get back a
/// scale and density derived from its height above the bg terrain
/// (via the worker's height cache), smoothed so a caster crossing an
/// edge doesn't pop.
struct BGDynamicsShadowKind {
  // How far above terrain a shadow reaches max size and min density.
  static constexpr float kMaxGrowDist{3.0f};
  // How far behind something a caster has to be to go transparent.
  static constexpr float kOccludeDistance{0.5f};
  // How big the shadow gets at its max dist.
  static constexpr float kMaxScale{3.0f};

  struct Config {
    float height_scaling{1.0f};
  };
  struct Input {
    Vector3f position{0.0f, 0.0f, 0.0f};
  };
  struct Output {
    float scale{1.0f};
    float density{0.0f};
  };
  class Sim {
   public:
    Sim(const Config& config, BGDynamicsWorldServer* server);
    void SetInput(const Input& input);
    void Step(BGDynamicsWorldServer* server);
    void GetOutput(Output* out) const;

   private:
    float height_scaling_{1.0f};
    Vector3f position_{0.0f, 0.0f, 0.0f};
    float scale_{1.0f};
    float density_{0.0f};
  };
};

/// Volume light: a colored glow sphere that tints nearby smoke
/// tendrils. Input-only; the worker just keeps the latest values for
/// the tendril update to sample.
struct BGDynamicsVolumeLightKind {
  struct Config {};
  struct Input {
    Vector3f position{0.0f, 0.0f, 0.0f};
    float radius{};
    float r{};
    float g{};
    float b{};
  };
  struct Output {};
  class Sim {
   public:
    Sim(const Config& config, BGDynamicsWorldServer* server) {}
    void SetInput(const Input& input) { input_ = input; }
    void Step(BGDynamicsWorldServer* server) {}
    void GetOutput(Output* out) const {}
    auto input() const -> const Input& { return input_; }

   private:
    Input input_;
  };
};

/// Points along a fuse, root first.
const int kFusePointCount = 4;

/// Bomb fuse: feed the fuse's root transform and remaining length;
/// the worker runs a cheap constraint-relaxation chain of points
/// trailing off it, spits sparks from the tip, and builds the fuse
/// geometry into the draw snapshot. Input-only.
struct BGDynamicsFuseKind {
  struct Config {};
  struct Input {
    Matrix44f transform{kMatrix44fIdentity};
    bool have_transform{};
    float length{1.0f};
  };
  struct Output {};
  class Sim {
   public:
    Sim(const Config& config, BGDynamicsWorldServer* server) {}
    void SetInput(const Input& input) { input_ = input; }
    void Step(BGDynamicsWorldServer* server);
    void GetOutput(Output* out) const {}
    /// False until the first transform has landed and the chain has
    /// been snapped into place.
    auto initialized() const -> bool { return initial_position_set_; }
    auto point(int i) const -> const Vector3f& { return dyn_pts_[i]; }

   private:
    Input input_;
    float seg_len_{};
    Vector3f target_pts_[kFusePointCount]{};
    Vector3f dyn_pts_[kFusePointCount]{};
    bool initial_position_set_{};
  };
};

/// Jointed cosmetic attachments (hair tufts, antennas, ...) hung off
/// an anchor body that lives in the main sim. Feed the anchor's
/// transform each step; a no-collision twin body in the bg world
/// carries spring-jointed (JointFixedEF) segment chains, and every
/// body's simmed world pose comes back. The rig is anchor-agnostic --
/// it never knows what a head is; a character definition is just one
/// feeder. Segments collide softly against terrain only (chunk-style:
/// each segment capsule tested against the terrain collider, never
/// against each other or the twin); the twin has no collision
/// geometry at all.
/// One character's cosmetic rig: every definition attachment (hair,
/// antennae, ...) hanging off its anchor bodies (head/torso/pelvis),
/// simulated together as one island so parts of a character can
/// interact, skip, freeze and snap as a unit. The anchors are fed as
/// kinematic twins each step; nothing here ever flows back into
/// gameplay (see docs/initiatives/bg-dynamics-channels.md).
struct BGDynamicsCharacterKind {
  static constexpr int kMaxAnchors{3};
  static constexpr int kMaxAttachmentsPerAnchor{10};
  static constexpr int kMaxAttachments{kMaxAnchors * kMaxAttachmentsPerAnchor};
  static constexpr int kMaxSegments{4};
  static constexpr int kMaxBodies{kMaxAttachments * kMaxSegments};

  struct SegmentSpec {
    float geom_radius{0.04f};
    float geom_length{0.13f};
    float mass_radius{0.07f};
    float mass_length{0.13f};
    // Total mass. Fixed per kind; the mass capsule dims above only
    // shape the inertia, so radius/length dials don't change weight.
    float mass{0.001f};
    // In the previous segment's frame (unused for segment 0, which
    // anchors at the attachment's position on the anchor body).
    float parent_anchor[3]{};
    float child_anchor[3]{};
    float linear_stiffness{};
    float linear_damping{};
    float angular_stiffness{};
    float angular_damping{};
    // Rest bend at this segment's joint, -1 to 1 (x 90 degrees toward
    // the attachment's local +y). The root's bend is applied on top of
    // the attachment rotation.
    float curl{};
  };
  struct AttachmentSpec {
    int anchor{};                               // Index into Config::anchors.
    float position[3]{};                        // Anchor-local.
    float rotation[4]{1.0f, 0.0f, 0.0f, 0.0f};  // (w,x,y,z) rest rotation.
    float drag{};  // Per-step linear-velocity bleed fraction (0-1).
    int segment_count{};
    SegmentSpec segments[kMaxSegments];
  };
  struct AnchorSpec {
    // The twin takes the anchor body's mass so the joint mass ratios
    // match the main sim (where these springs were tuned).
    float mass{0.46f};
    // Optional collision shape riding on the twin (kinematic: it
    // pushes, nothing pushes it), for the targeted self-collision
    // pairs below. 0 = none, 1 = sphere (dims[0] radius), 2 = box
    // (dims = full side lengths).
    int shape{};
    float dims[3]{};
    // Once the character has shattered, limbs that have broken loose
    // (their chain joint slackened to nothing) also collide with this
    // twin's shape (the main sim's head and torso accept any broken
    // part of their own character).
    bool collides_loose_limbs{};
  };
  // A targeted self-collision test between two of this character's
  // geoms (no broadphase or space: the exact pairs the main sim
  // checks, every step). Each side is a limb body index, or
  // -1 - anchor_index for an anchor twin's shape.
  static constexpr int kMaxCollisionPairs{16};
  struct CollisionPair {
    int a{};
    int b{};
  };

  // Limbs: the character's arms and legs simulated here instead of in
  // the main sim (cosmetic; nothing reads them back). Bodies hang off
  // the anchor twins through joints whose rest state is driven every
  // step from the owner's pose driver (LimbJointTarget in Input).
  static constexpr int kMaxLimbBodies{10};
  static constexpr int kMaxLimbJoints{16};
  struct LimbBodySpec {
    float radius{};
    float length{};  // 0 = sphere.
    float mass_radius{};
    float mass_length{};
    float mass{};
    int anchor{};  // Which anchor twin it belongs with (carry/relative).
    // Terrain contact softness (the main sim's per-limb values).
    float collide_stiffness{10.0f};
    float collide_damping{1.0f};
    float friction{0.5f};
  };
  struct LimbJointSpec {
    // Parent: a limb body index, or -1 - anchor_index for a twin.
    int parent{};
    int child{};  // Limb body index.
    float anchor2[3]{};
    // The chain joint that places the child at creation/snap (extra
    // joints such as IK pulls don't).
    bool positions_child{};
  };
  struct LimbJointTarget {
    float anchor1[3]{};
    float qrel[4]{1.0f, 0.0f, 0.0f, 0.0f};
    float linear_stiffness{};
    float linear_damping{};
    float angular_stiffness{};
    float angular_damping{};
  };

  struct Config {
    int anchor_count{};
    AnchorSpec anchors[kMaxAnchors];
    int attachment_count{};
    AttachmentSpec attachments[kMaxAttachments];
    int limb_body_count{};
    LimbBodySpec limb_bodies[kMaxLimbBodies];
    int limb_joint_count{};
    LimbJointSpec limb_joints[kMaxLimbJoints];
    int collision_pair_count{};
    CollisionPair collision_pairs[kMaxCollisionPairs];
  };
  struct Input {
    Matrix44f anchors[kMaxAnchors]{kMatrix44fIdentity, kMatrix44fIdentity,
                                   kMatrix44fIdentity};
    bool have_anchors{};
    // Teleport: bumped each time the anchors jump, so the rig is
    // re-placed on them instead of springing across the map. A counter
    // (not a flag) so a snap survives skipped feeds and never
    // lingers: the Sim acts once per change.
    uint32_t snap_count{};
    // Load shedding, 0-1: the fraction of sim steps this rig sits out.
    // On a skipped step every body is carried rigidly along with its
    // anchor (current droop preserved, nothing solved or collided);
    // the dynamics just run at a reduced rate. 0 = full rate, 1 =
    // frozen. Steps are spread deterministically (error accumulator
    // with a per-rig phase and a little jitter), not thrown out at
    // random, so rigs don't all skip the same frames. One value per
    // character: its parts always sim together.
    float skip{};
    // The character is frozen (ice): on the way in every joint latches
    // its rest angle to the current pose and stiffens hard (the main
    // sim's frozen-limb treatment); on the way out the springs return
    // to their configured values.
    bool frozen{};
    // The character has shattered (ice or curse death). The pose
    // driver's targets already slacken the broken joints; the rig
    // stops load-shedding (debris falls on every step; nothing is
    // carried), hardens its contacts the way the main sim does, and
    // lets loose limbs collide with the twins that accept them
    // (AnchorSpec::collides_loose_limbs) so the pieces don't pass
    // through the body they just left.
    bool shattered{};
    // Per-step limb joint state from the owner's pose driver, in
    // Config::limb_joints order. Applied verbatim each step.
    bool have_limb_targets{};
    LimbJointTarget limb_joints[kMaxLimbJoints];
  };
  // One simmed body's output.
  struct OutputBody {
    // World pose as simmed (debug draw shows exactly this).
    Matrix44f world;
    // The same pose relative to the body's own anchor. Display meshes
    // compose this onto the anchor's *current* transform, so a rig
    // that is a step or two stale, or being skipped, still rides the
    // anchor rigidly instead of trailing it.
    Matrix44f relative;
    int anchor{};
    float radius{};
    float length{};  // 0 = sphere.
  };
  struct Output {
    int anchor_count{};
    Matrix44f anchors[kMaxAnchors];  // The twins' simmed poses.
    // Attachment segment bodies, and limb bodies in Config::limb_bodies
    // order. Sized to the live counts, not the kMax* ceilings; output
    // bundles are recycled (BGDynamicsWorldServer::RecycleBundle) so these
    // keep their capacity from step to step and normally never
    // allocate.
    std::vector<OutputBody> bodies;
    std::vector<OutputBody> limbs;
  };
  class Sim {
   public:
    Sim(const Config& config, BGDynamicsWorldServer* server);
    ~Sim();
    void SetInput(const Input& input);
    void Step(BGDynamicsWorldServer* server);
    void GetOutput(Output* out) const;

   private:
    void CreateBodies_(BGDynamicsWorldServer* server);
    void CreateLimbs_(BGDynamicsWorldServer* server);
    void PlaceOnAnchors_();
    void ApplyLimbTargets_();
    void CollideSelfPairs_(BGDynamicsWorldServer* server);
    auto PairGeom_(int ref, float* stiffness, float* damping) -> dGeomID;
    // Decide whether this step is live for the rig (see Input::skip).
    auto TakeStep_() -> bool;
    // Skipped step: move every body by its anchor's motion since the
    // last step so the rig's relative configuration is untouched.
    void CarryWithAnchors_(const Matrix44f* deltas);
    // Disabled bodies are invisible to the island solver, which is
    // where a skipped rig's savings come from.
    void SetBodiesEnabled_(bool enabled);
    void SetFrozen_(bool frozen);
    void SetShattered_(bool shattered);
    void HandOffShatterVelocity_();
    // The main sim's per-step speed cap on limbs.
    void ClampLimbVelocities_();

    Config config_;
    Input input_;
    int anchor_count_{};
    dBodyID twins_[kMaxAnchors]{};
    dGeomID twin_geoms_[kMaxAnchors]{};
    uint32_t last_snap_count_{};
    bool have_prev_anchors_{};
    Matrix44f prev_anchors_[kMaxAnchors]{kMatrix44fIdentity, kMatrix44fIdentity,
                                         kMatrix44fIdentity};
    float skip_acc_{};
    uint32_t jitter_state_{};
    bool bodies_enabled_{true};
    bool frozen_{};
    bool shattered_{};
    // Steps left in the post-shatter velocity handoff (see
    // SetShattered_).
    int shatter_handoff_steps_{};
    struct Body {
      dBodyID body{};
      dGeomID geom{};  // Spaceless capsule; we hand it to the terrain collider.
      JointFixedEF* joint{};
      int anchor{};
      int attachment{};
      int segment{};
      float radius{};
      float length{};
    };
    std::vector<Body> bodies_;
    struct LimbBody {
      dBodyID body{};
      dGeomID geom{};
      int anchor{};
      float radius{};
      float length{};
      float collide_stiffness{};
      float collide_damping{};
      float friction{};
    };
    std::vector<LimbBody> limb_bodies_;
    struct LimbJoint {
      JointFixedEF* joint{};
      bool positions_child{};
    };
    std::vector<LimbJoint> limb_joints_;
  };
};

/// Every channel kind, in a fixed order; the per-kind tuples below
/// (step payloads, outputs, logic channels, worker states) are all
/// shaped from this one list, so adding a kind means adding it here.
using BGDynamicsKinds =
    std::tuple<BGDynamicsShadowKind, BGDynamicsVolumeLightKind,
               BGDynamicsFuseKind, BGDynamicsCharacterKind>;

template <template <typename> class Wrapper, typename Kinds>
struct BGDynamicsWrapKinds;
template <template <typename> class Wrapper, typename... Kinds>
struct BGDynamicsWrapKinds<Wrapper, std::tuple<Kinds...>> {
  using type = std::tuple<Wrapper<Kinds>...>;
};

using BGDynamicsChannelStepDataTuple =
    BGDynamicsWrapKinds<BGDynamicsChannelStepData, BGDynamicsKinds>::type;
using BGDynamicsChannelOutputsTuple =
    BGDynamicsWrapKinds<BGDynamicsChannelOutputs, BGDynamicsKinds>::type;
using BGDynamicsChannelTuple =
    BGDynamicsWrapKinds<BGDynamicsChannel, BGDynamicsKinds>::type;
using BGDynamicsChannelWorkerTuple =
    BGDynamicsWrapKinds<BGDynamicsChannelWorker, BGDynamicsKinds>::type;

/// Everything the worker hands back after one step: each channel's
/// outputs, stamped with the bg step they came from. Built worker-side,
/// pointer-passed to the logic thread, adopted whole.
struct BGDynamicsOutputBundle {
  int step_count{};
  BGDynamicsChannelOutputsTuple channels;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_KINDS_H_
