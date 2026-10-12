// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_SPAZ_POSE_H_
#define BALLISTICA_SCENE_V1_NODE_SPAZ_POSE_H_

#include "ballistica/base/dynamics/joint_fixed_ef.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ode/ode_objects.h"

namespace ballistica::scene_v1 {

struct SpazPhysicsTuning;

/// Which of the rig's joints a shatter broke (bit flags; the pose
/// driver zeroes the springs of every broken joint).
enum SpazShatterDamage : uint32_t {
  kNeckJointBroken = 1u << 0u,
  kPelvisJointBroken = 1u << 1u,
  kUpperLeftLegJointBroken = 1u << 2u,
  kUpperRightLegJointBroken = 1u << 3u,
  kLowerLeftLegJointBroken = 1u << 4u,
  kLowerRightLegJointBroken = 1u << 5u,
  kUpperLeftArmJointBroken = 1u << 6u,
  kUpperRightArmJointBroken = 1u << 7u,
  kLowerLeftArmJointBroken = 1u << 8u,
  kLowerRightArmJointBroken = 1u << 9u
};

/// The rig's driven joints, in a fixed order shared by the pose
/// driver's target array and every limb backend.
enum SpazJoint {
  kSpazJointNeck,
  kSpazJointPelvis,
  kSpazJointUpperRightArm,
  kSpazJointLowerRightArm,
  kSpazJointUpperLeftArm,
  kSpazJointLowerLeftArm,
  kSpazJointUpperRightLeg,
  kSpazJointLowerRightLeg,
  kSpazJointUpperLeftLeg,
  kSpazJointLowerLeftLeg,
  kSpazJointRightToes,
  kSpazJointRightToes2,
  kSpazJointLeftToes,
  kSpazJointLeftToes2,
  kSpazJointRightLegIK,
  kSpazJointLeftLegIK,
  kSpazJointRightArmIK,
  kSpazJointLeftArmIK,
  kSpazJointCount
};

/// One joint's driven state: what the pose driver writes and what a
/// limb backend consumes. Field names match base::JointFixedEF so the
/// main-sim backend is a plain copy; the bg backend ships them over
/// the channel instead.
struct SpazJointTarget {
  dVector3 anchor1{};  // Body-local anchor on the parent body.
  dQuaternion qrel{1.0f, 0.0f, 0.0f, 0.0f};  // Rest rotation parent->child.
  float linearStiffness{};
  float linearDamping{};
  float angularStiffness{};
  float angularDamping{};
};

/// The spaz rig's limb and neck pose driver: every step it turns the
/// character's intent state (moving, punching, holding, knocked out,
/// frozen, ...) into joint targets and spring strengths for the legs,
/// arms and neck, plus the rest pose the limb joints hold between
/// those. It is deliberately fed only the core bodies (torso, pelvis,
/// stand, roller) and never a limb body, so the same driver can feed
/// the main-sim limb rig today and a bg-dynamics limb rig later
/// without the two ever diverging; nothing about the limbs' simulated
/// state flows back in here.
class SpazPose {
 public:
  /// The rig joints' driven state, by name. The driver only ever
  /// writes these targets; a backend applies them to real joints.
  struct Joints {
    SpazJointTarget* neck{};
    SpazJointTarget* pelvis{};
    SpazJointTarget* upper_right_arm{};
    SpazJointTarget* lower_right_arm{};
    SpazJointTarget* upper_left_arm{};
    SpazJointTarget* lower_left_arm{};
    SpazJointTarget* upper_right_leg{};
    SpazJointTarget* lower_right_leg{};
    SpazJointTarget* upper_left_leg{};
    SpazJointTarget* lower_left_leg{};
    SpazJointTarget* right_toes{};
    SpazJointTarget* right_toes_2{};
    SpazJointTarget* left_toes{};
    SpazJointTarget* left_toes_2{};
    SpazJointTarget* right_leg_ik{};
    SpazJointTarget* left_leg_ik{};
    SpazJointTarget* right_arm_ik{};
    SpazJointTarget* left_arm_ik{};
  };

  /// Everything one step of posing depends on. Plain values plus the
  /// core bodies; the held object's body (if any) is the one foreign
  /// body, for where the hands reach.
  struct StepInputs {
    // Core-joint spring strengths (the neck here); never null.
    const SpazPhysicsTuning* tuning{};
    millisecs_t scenetime{};
    int64_t stepnum{};
    int stream_id{};
    millisecs_t last_punch_time{};
    millisecs_t celebrate_until_time_left{};
    millisecs_t celebrate_until_time_right{};
    millisecs_t throw_start{};
    millisecs_t curse_death_time{};
    bool have_thrown{};
    float breath{};  // Idle breathing wave, from the node's step.
    bool dead{};
    bool shattered{};
    uint32_t shatter_damage{};
    bool hold_position_pressed{};
    int8_t ud{};
    int8_t lr{};
    float ud_norm{};
    float lr_norm{};
    uint8_t knockout{};
    uint8_t balance{};
    uint8_t jump{};
    uint8_t pickup{};
    uint8_t punch{};
    bool punch_right{};
    float punch_dir_x{};
    float punch_dir_z{};
    bool frozen{};
    int footing{};
    bool hockey{};
    float run_gas{};
    float step_separation{};
    float idle_arm_stiffness{};
    float arm_swing{};
    float shoulder_offset_x{};
    float shoulder_offset_y{};
    float shoulder_offset_z{};
    float a_vel_y_smoothed_more{};
    bool holding_something{};
    float hold_hand_offset_left[3]{};
    float hold_hand_offset_right[3]{};
    dBodyID torso{};
    dBodyID pelvis{};
    dBodyID stand{};
    dBodyID roller{};
    dBodyID held{};  // Null when not holding anything.
  };

  /// One sim step of posing. Sets head_turning when the neck got a new
  /// random look direction this step (the eyes follow it).
  void Step(const StepInputs& in, const Joints& joints, bool* head_turning);

  /// (Re)apply the limb joints' rest orientations and spring strengths:
  /// the normal standing pose, or the frozen treatment (springs go hard
  /// and the rest rotations are left alone so the backend can lock
  /// them to the joints' current angles). Called when the style or
  /// frozen state changes, not per step. The pelvis springs come from
  /// the tuning; limb springs are fixed.
  void ApplyRestPose(const Joints& joints, bool frozen,
                     const SpazPhysicsTuning& tuning);

  /// Run-cycle phase (radians, wraps); synced host-to-client with the
  /// rest of the rig state.
  auto roll_amt() const -> float { return roll_amt_; }
  void set_roll_amt(float val) { roll_amt_ = val; }

  /// The synthetic fist: where the punching hand is modelled to be
  /// this step, in world space, computed from the torso frame and the
  /// punch phase alone (no arm body). This is what the punch region
  /// follows once limbs leave the main sim; until then it is compared
  /// against the real fist. Valid while punch_active().
  auto synthetic_fist() const -> const float* { return fist_world_; }
  /// The synthetic fist's world velocity: the torso carrying it (linear
  /// and angular, so a spinning character's fist is faster than a
  /// static one's) plus the modelled swing.
  auto synthetic_fist_velocity() const -> const float* {
    return fist_world_vel_;
  }
  auto punch_active() const -> bool { return punch_active_; }
  auto synthetic_fist_target() const -> const float* { return fist_target_; }

 private:
  void UpdateSyntheticFist_(const StepInputs& in, float breath);

  float roll_amt_{};
  bool head_back_{};
  // Torso-space fist position and velocity: a spring-damper chasing
  // its target, like the real arm chases its IK anchor.
  float fist_torso_[3]{};
  float fist_vel_[3]{};
  bool fist_valid_{};
  float fist_world_[3]{};
  float fist_world_vel_[3]{};
  float fist_target_[3]{};  // Torso space; for the trace.
  bool punch_active_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_SPAZ_POSE_H_
