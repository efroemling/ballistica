// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/spaz_pose.h"

#include <algorithm>
#include <cmath>

#include "ballistica/scene_v1/generated/spaz_rig.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"
#include "ode/ode_collision_util.h"

namespace ballistica::scene_v1 {

// Joint springs for the rig. The classic tuning; body densities and
// contact stiffnesses live with the bodies in spaz_node.cc.
const float kRunJointLinearStiffness = 80.0f;
const float kRunJointLinearDamping = 2.0f;
const float kRunJointAngularStiffness = 0.2f;
const float kRunJointAngularDamping = 0.002f;

const float kPelvisLinearStiffness = 300.0f;
const float kPelvisLinearDamping = 20.0f;
const float kPelvisAngularStiffness = 1.5f;
const float kPelvisAngularDamping = 0.06f;

const float kUpperLegLinearStiffness = 300.0f;
const float kUpperLegLinearDamping = 5.0f;
const float kUpperLegAngularStiffness = 0.12f;
const float kUpperLegAngularDamping = 0.004f;

const float kLowerLegLinearStiffness = 200.0f;
const float kLowerLegLinearDamping = 5.0f;
const float kLowerLegAngularStiffness = 0.12f;
const float kLowerLegAngularDamping = 0.004f;

const float kToesLinearStiffness = 50.0f;
const float kToesLinearDamping = 1.0f;
const float kToesAngularStiffness = 0.015f;
const float kToesAngularDamping = 0.0005f;

const float kUpperArmLinearStiffness = 30.0f;
const float kUpperArmLinearDamping = 1.2f;
const float kUpperArmAngularStiffness = 0.08f;
const float kUpperArmAngularDamping = 0.008f;

const float kLowerArmLinearStiffness = 80.0f;
const float kLowerArmLinearDamping = 1.0f;
const float kLowerArmAngularStiffness = 0.08f;
const float kLowerArmAngularDamping = 0.008f;

void SpazPose::ApplyRestPose(const Joints& joints, bool frozen) {
  // (neck joint gets set every step so no update here)

  float l_still_scale = 1.0f;
  float l_damp_scale = 1.0f;
  float a_stiff_scale = 1.0f;
  float a_damp_scale = 1.0f;
  float leg_a_damp_scale = 1.0f;

  // When frozen, lock to our orientations and get more stiff.
  if (frozen) {
    l_still_scale *= 5.0f;
    l_damp_scale *= 0.2f;
    a_stiff_scale *= 1000.0f;
    a_damp_scale *= 0.2f;
    leg_a_damp_scale *= 1.0f;
    // (The backend locks each joint's rest rotation to its current
    // angle on the way into frozen; rest rotations are not touched
    // here.)
  } else {
    // Not frozen; just normal setup.

    // Set normal joint angles.

    dQFromAxisAndAngle(joints.pelvis->qrel, 1, 0.0f, 0.0f, -0.4f);

    dQFromAxisAndAngle(joints.upper_right_arm->qrel, 1, 0.0f, -0.0f, 2.0f);
    dQFromAxisAndAngle(joints.lower_right_arm->qrel, 1, 0, 0, -1.7f);

    dQFromAxisAndAngle(joints.upper_left_arm->qrel, 1, -0.0f, 0.0f, 2.0f);
    dQFromAxisAndAngle(joints.lower_left_arm->qrel, 1, 0, 0, -1.7f);

    dQFromAxisAndAngle(joints.upper_right_leg->qrel, 1, 0.2f, 0.2f, 0.5f);
    dQFromAxisAndAngle(joints.lower_right_leg->qrel, 1, 0, 0, 1.0f);
    dQSetIdentity(joints.right_toes->qrel);

    dQFromAxisAndAngle(joints.upper_left_leg->qrel, 1, -0.2f, -0.2f, 0.5f);
    dQFromAxisAndAngle(joints.lower_left_leg->qrel, 1, 0, 0, 3.1415f / 2.0f);
    dQSetIdentity(joints.left_toes->qrel);
  }

  joints.pelvis->linearStiffness = kPelvisLinearStiffness * l_still_scale;
  joints.pelvis->linearDamping = kPelvisLinearDamping * l_damp_scale;
  joints.pelvis->angularStiffness = kPelvisAngularStiffness * a_stiff_scale;
  joints.pelvis->angularDamping = kPelvisAngularDamping * a_damp_scale;

  joints.upper_right_leg->linearStiffness =
      kUpperLegLinearStiffness * l_still_scale;
  joints.upper_right_leg->linearDamping = kUpperLegLinearDamping * l_damp_scale;
  joints.upper_right_leg->angularStiffness =
      kUpperLegAngularStiffness * a_stiff_scale;
  joints.upper_right_leg->angularDamping =
      kUpperLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  joints.lower_right_leg->linearStiffness =
      kLowerLegLinearStiffness * l_still_scale;
  joints.lower_right_leg->linearDamping = kLowerLegLinearDamping * l_damp_scale;
  joints.lower_right_leg->angularStiffness =
      kLowerLegAngularStiffness * a_stiff_scale;
  joints.lower_right_leg->angularDamping =
      kLowerLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  joints.right_toes->linearStiffness = kToesLinearStiffness * l_still_scale;
  joints.right_toes->linearDamping = kToesLinearDamping * l_damp_scale;
  joints.right_toes->angularStiffness = kToesAngularStiffness * a_stiff_scale;
  joints.right_toes->angularDamping = kToesAngularDamping * a_damp_scale;

  joints.right_toes_2->linearStiffness = kToesLinearStiffness * l_still_scale;
  joints.right_toes_2->linearDamping = kToesLinearDamping * l_damp_scale;
  joints.right_toes_2->angularStiffness = 0;
  joints.right_toes_2->angularDamping = 0;

  joints.upper_left_leg->linearStiffness =
      kUpperLegLinearStiffness * l_still_scale;
  joints.upper_left_leg->linearDamping = kUpperLegLinearDamping * l_damp_scale;
  joints.upper_left_leg->angularStiffness =
      kUpperLegAngularStiffness * a_stiff_scale;
  joints.upper_left_leg->angularDamping =
      kUpperLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  joints.lower_left_leg->linearStiffness =
      kLowerLegLinearStiffness * l_still_scale;
  joints.lower_left_leg->linearDamping = kLowerLegLinearDamping * l_damp_scale;
  joints.lower_left_leg->angularStiffness =
      kLowerLegAngularStiffness * a_stiff_scale;
  joints.lower_left_leg->angularDamping =
      kLowerLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  joints.left_toes->linearStiffness = kToesLinearStiffness * l_still_scale;
  joints.left_toes->linearDamping = kToesLinearDamping * l_damp_scale;
  joints.left_toes->angularStiffness = kToesAngularStiffness * a_stiff_scale;
  joints.left_toes->angularDamping = kToesAngularDamping * a_damp_scale;

  joints.left_toes_2->linearStiffness = kToesLinearStiffness * l_still_scale;
  joints.left_toes_2->linearDamping = kToesLinearDamping * l_damp_scale;
  joints.left_toes_2->angularStiffness = 0;
  joints.left_toes_2->angularDamping = 0;
}

// Synthetic fist model. The real fist is the lower-arm body chasing the
// arm IK anchor through a spring; here the fist position (torso space)
// chases per-phase targets through a per-step spring-damper so it
// lands where the arm does without simulating the arm. Fitted against
// the real fist from BA_PUNCH_TRACE runs (build/tmp/punch_fit2.py; rms
// 0.012 over a punch, overshoot included): the arm never reaches the
// IK anchors, so the targets here are where it actually settles.
const float kFistSpring = 0.16f;  // Gap fraction added to velocity/step.
const float kFistDamping = 0.3f;  // Velocity fraction bled per step.
// Anticipation pose (punch start to 80ms): hand pulled back beside
// the hip, torso space, x mirrored for the right hand.
const float kFistAnticipate[3] = {0.32f, 0.06f, 0.04f};
// Extension (80ms to the end of the punch): from the shoulder, this
// far along the punch direction, lifted, and pulled in toward center.
const float kFistReach = 0.53f;
const float kFistLift = 0.09f;
const float kFistInward = 0.025f;
// Hanging hand between punches.
const float kFistRest[3] = {0.2f, -0.12f, 0.12f};

void SpazPose::UpdateSyntheticFist_(const StepInputs& in, float breath) {
  millisecs_t since_last_punch = in.scenetime - in.last_punch_time;
  float mirror = in.punch_right ? -1.0f : 1.0f;
  float target[3];
  // The real arm's anchor switches at 80ms but the arm only starts
  // moving a step later.
  if (in.punch && since_last_punch < 88) {
    // Anticipation: hand pulled back.
    target[0] = kFistAnticipate[0] * mirror;
    target[1] = kFistAnticipate[1];
    target[2] = kFistAnticipate[2];
  } else if (in.punch) {
    // Extended, and held there for the rest of the punch (the real
    // arm's IK anchor stays put after 200ms too). Inward is toward
    // x = 0, so it opposes the shoulder's own side.
    float sx = (kSpazRigShoulderOnTorso[0] + in.shoulder_offset_x) * -mirror
               + kFistInward * mirror;
    float sy = kSpazRigShoulderOnTorso[1] + in.shoulder_offset_y
               + breath * 0.012f + kFistLift;
    float sz = in.shoulder_offset_z + 0.05f;
    dVector3 p_world;
    dBodyGetRelPointPos(in.torso, sx, sy, sz, p_world);
    p_world[0] += in.punch_dir_x * kFistReach;
    p_world[2] += in.punch_dir_z * kFistReach;
    dVector3 p_torso;
    dBodyGetPosRelPoint(in.torso, p_world[0], p_world[1], p_world[2], p_torso);
    target[0] = p_torso[0];
    target[1] = p_torso[1];
    target[2] = p_torso[2];
  } else {
    // Hanging.
    target[0] = kFistRest[0] * mirror;
    target[1] = kFistRest[1];
    target[2] = kFistRest[2];
  }
  for (int i = 0; i < 3; ++i) {
    fist_target_[i] = target[i];
  }
  if (!fist_valid_) {
    for (int i = 0; i < 3; ++i) {
      fist_torso_[i] = target[i];
      fist_vel_[i] = 0.0f;
    }
    fist_valid_ = true;
  } else {
    for (int i = 0; i < 3; ++i) {
      fist_vel_[i] += (target[i] - fist_torso_[i]) * kFistSpring;
      fist_vel_[i] *= 1.0f - kFistDamping;
      fist_torso_[i] += fist_vel_[i];
    }
  }
  dVector3 w;
  dBodyGetRelPointPos(in.torso, fist_torso_[0], fist_torso_[1], fist_torso_[2],
                      w);
  fist_world_[0] = w[0];
  fist_world_[1] = w[1];
  fist_world_[2] = w[2];
  // Velocity: the torso's motion at the fist point (carry, including
  // spin) plus the swing, rotated into world space.
  dVector3 carry;
  dBodyGetPointVel(in.torso, w[0], w[1], w[2], carry);
  dVector3 swing;
  dBodyVectorToWorld(in.torso, fist_vel_[0], fist_vel_[1], fist_vel_[2], swing);
  for (int i = 0; i < 3; ++i) {
    fist_world_vel_[i] = carry[i] + swing[i] / kGameStepSeconds;
  }
  punch_active_ = in.punch > 0;
}

void SpazPose::Step(const StepInputs& in, const Joints& joints,
                    bool* head_turning) {
  millisecs_t scenetime = in.scenetime;
  millisecs_t since_last_punch = scenetime - in.last_punch_time;
  float breath = in.breath;

  UpdateSyntheticFist_(in, breath);

  // If we're shattered we just make sure our joints are ineffective.
  if (in.shattered) {
    SpazJointTarget* broken[20];

    // Fill in our broken joints.
    {
      SpazJointTarget** j = broken;

      *j = joints.right_leg_ik;
      j++;
      *j = joints.left_leg_ik;
      j++;
      *j = joints.right_arm_ik;
      j++;
      *j = joints.left_arm_ik;
      j++;
      if (in.shatter_damage & kUpperRightArmJointBroken) {
        *j = joints.upper_right_arm;
        j++;
      }
      if (in.shatter_damage & kLowerRightArmJointBroken) {
        *j = joints.lower_right_arm;
        j++;
      }
      if (in.shatter_damage & kUpperLeftArmJointBroken) {
        *j = joints.upper_left_arm;
        j++;
      }
      if (in.shatter_damage & kLowerLeftArmJointBroken) {
        *j = joints.lower_left_arm;
        j++;
      }
      if (in.shatter_damage & kUpperLeftLegJointBroken) {
        *j = joints.upper_left_leg;
        j++;
      }
      if (in.shatter_damage & kLowerLeftLegJointBroken) {
        *j = joints.lower_left_leg;
        j++;
      }
      if (in.shatter_damage & kUpperRightLegJointBroken) {
        *j = joints.upper_right_leg;
        j++;
      }
      if (in.shatter_damage & kLowerRightLegJointBroken) {
        *j = joints.lower_right_leg;
        j++;
      }
      if (in.shatter_damage & kNeckJointBroken) {
        *j = joints.neck;
        j++;
      }
      if (in.shatter_damage & kPelvisJointBroken) {
        *j = joints.pelvis;
        j++;
      }
      *j = nullptr;
    }

    for (SpazJointTarget** j = broken; *j != nullptr; j++)
      (**j).linearStiffness = (**j).linearDamping = (**j).angularStiffness =
          (**j).angularDamping = 0.0f;

    return;
  }

  // Not shattered; do normal stuff.

  // Adjust neck strength.
  {
    SpazJointTarget* j = joints.neck;
    if (j) {
      if (in.knockout) {
        j->linearStiffness = 400.0f;
        j->linearDamping = 1.0f;
        j->angularStiffness = 5.0f;
        j->angularDamping = 0.3f;
      } else {
        j->linearStiffness = 500.0f;
        j->linearDamping = 1.0f;
        j->angularStiffness = 13.0f;
        j->angularDamping = 0.8f;
      }
    }
  }

  // Update legs.
  {
    // Whether our feet are following the run ball or just hanging free.
    if (in.knockout || in.balance == 0 || in.frozen) {
      // flail our legs when airborn and alive
      if (!in.footing && in.balance == 0 && !in.dead) {
        joints.left_leg_ik->linearStiffness = kRunJointLinearStiffness * 0.4f;
        joints.left_leg_ik->linearDamping = kRunJointLinearDamping * 0.2f;
        joints.left_leg_ik->angularStiffness = kRunJointAngularStiffness * 0.2f;
        joints.left_leg_ik->angularDamping = kRunJointAngularDamping * 0.2f;
        joints.right_leg_ik->linearStiffness = kRunJointLinearStiffness * 0.4f;
        joints.right_leg_ik->linearDamping = kRunJointLinearDamping * 0.2f;
        joints.right_leg_ik->angularStiffness =
            kRunJointAngularStiffness * 0.2f;
        joints.right_leg_ik->angularDamping = kRunJointAngularDamping * 0.2f;
        roll_amt_ -= 0.2f;
        if (roll_amt_ < (-2.0f * 3.141592f)) {
          roll_amt_ += 2.0f * 3.141592f;
        }
        float x = 0.1f;
        float y = -0.3f;
        float z = 0.22f * cosf(roll_amt_);
        joints.left_leg_ik->anchor1[0] = x;
        joints.left_leg_ik->anchor1[1] = y;
        joints.left_leg_ik->anchor1[2] = z;
        joints.right_leg_ik->anchor1[0] = -x;
        joints.right_leg_ik->anchor1[1] = y;
        joints.right_leg_ik->anchor1[2] = -z;
      } else {
        // we're frozen or knocked out; turn off run-joint connections...
        joints.left_leg_ik->linearStiffness = 0.0f;
        joints.left_leg_ik->linearDamping = 0.0f;
        joints.left_leg_ik->angularStiffness = 0.0f;
        joints.left_leg_ik->angularDamping = 0.0f;
        joints.right_leg_ik->linearStiffness = 0.0f;
        joints.right_leg_ik->linearDamping = 0.0f;
        joints.right_leg_ik->angularStiffness = 0.0f;
        joints.right_leg_ik->angularDamping = 0.0f;
      }
    } else {
      // Do normal running updates.

      // In hockey mode lets transfer a bit of our momentum to the direction
      // we're facing if our skates are on the ground.
      // (Locomotion, strictly; it rides here because it shares the
      // run-cycle branch. Move it out with the locomotion split.)
      if (in.hockey && in.footing) {
        const dReal* rollVel = dBodyGetLinearVel(in.roller);

        dVector3 rollVelNorm = {rollVel[0], rollVel[1], rollVel[2]};
        dNormalize3(rollVelNorm);

        dVector3 forward;
        dBodyVectorToWorld(in.stand, 0, 0, 1, forward);

        float dot = dDOT(rollVelNorm, forward);

        float mag = -6.0f * std::abs(dot);

        dVector3 f = {mag * rollVel[0], mag * rollVel[1], mag * rollVel[2]};
        float fMag = dVector3Length(f);

        if (dot < 0.0f) fMag *= -1.0f;  // if we're going backwards..

        dBodyAddForce(in.roller, f[0], f[1], f[2]);
        dBodyAddForce(in.roller, forward[0] * fMag, forward[1] * fMag,
                      forward[2] * fMag);
      }

      joints.left_leg_ik->linearStiffness = kRunJointLinearStiffness;
      joints.left_leg_ik->linearDamping = kRunJointLinearDamping;
      joints.left_leg_ik->angularStiffness = kRunJointAngularStiffness;
      joints.left_leg_ik->angularDamping = kRunJointAngularDamping;
      joints.right_leg_ik->linearStiffness = kRunJointLinearStiffness;
      joints.right_leg_ik->linearDamping = kRunJointLinearDamping;
      joints.right_leg_ik->angularStiffness = kRunJointAngularStiffness;
      joints.right_leg_ik->angularDamping = kRunJointAngularDamping;

      // Tighten things up for running.
      joints.left_leg_ik->linearStiffness *=
          2.0f * in.run_gas + (1.0f - in.run_gas) * 1.0f;
      joints.left_leg_ik->linearDamping *=
          2.0f * in.run_gas + (1.0f - in.run_gas) * 1.0f;
      joints.right_leg_ik->linearStiffness *=
          2.0f * in.run_gas + (1.0f - in.run_gas) * 1.0f;
      joints.right_leg_ik->linearDamping *=
          2.0f * in.run_gas + (1.0f - in.run_gas) * 1.0f;

      if (in.hockey) {
        if (in.hold_position_pressed || (!in.ud && !in.lr)) {
          joints.left_leg_ik->linearStiffness *= 0.05f;
          joints.left_leg_ik->linearDamping *= 0.1f;
          joints.left_leg_ik->angularStiffness *= 0.05f;
          joints.left_leg_ik->angularDamping *= 0.1f;
          joints.right_leg_ik->linearStiffness *= 0.05f;
          joints.right_leg_ik->linearDamping *= 0.1f;
          joints.right_leg_ik->angularStiffness *= 0.05f;
          joints.right_leg_ik->angularDamping *= 0.1f;
        }
      }

      const dReal* ballAVel = dBodyGetAngularVel(in.roller);
      const dReal aVelMag =
          sqrtf(ballAVel[0] * ballAVel[0] + ballAVel[1] * ballAVel[1]
                + ballAVel[2] * ballAVel[2]);

      // When we're stopped, press our feet downward.
      float speed_stretch = std::min(
          sqrtf(in.lr_norm * in.lr_norm + in.ud_norm * in.ud_norm) * 2.0f,
          1.0f);

      float rollScale = in.hockey ? 0.6f : 1.0f;

      // Push towards 0.8f when running.
      rollScale = in.run_gas * 0.8f + (1.0f - in.run_gas) * rollScale;

      // Clamp extremely low values so noise doesnt keep our feet moving
      roll_amt_ -= rollScale * 0.021f * std::max(aVelMag - 0.1f, 0.0f);

      if (roll_amt_ < (-2.0f * 3.141592f)) {
        roll_amt_ += 2.0f * 3.141592f;
      }

      // We move our feet in a circle that is calculated
      // relative to our stand-body; *not* our pelvis.
      // this way our pelvis is free to sway and rotate and stuff
      // in response to our feet without affecting their target arcs

      // LEFT LEG
      float step_separation = in.step_separation;
      {
        // Take a point relative to stand-body and then find it in the space
        // of our pelvis. *that* is our attach point for the constraint.
        dVector3 p_world;
        dVector3 p_pelvis;
        float y = -0.4f + speed_stretch * 0.14f * sinf(roll_amt_)
                  + (1.0f - speed_stretch) * -0.2f;
        if (in.jump > 0) y -= 0.3f;
        float z = 0.22f * cosf(roll_amt_);
        y += 0.06f * in.run_gas;
        z *= 1.4f * in.run_gas + (1.0f - in.run_gas) * 1.0f;
        dBodyGetRelPointPos(in.stand, step_separation, y, z, p_world);
        assert(in.pelvis);
        dBodyGetPosRelPoint(in.pelvis, p_world[0], p_world[1], p_world[2],
                            p_pelvis);
        joints.left_leg_ik->anchor1[0] = p_pelvis[0];
        joints.left_leg_ik->anchor1[1] = p_pelvis[1];
        joints.left_leg_ik->anchor1[2] = p_pelvis[2];
      }
      // RIGHT LEG
      {
        // Take a point relative to stand-body and then find it in the space
        // of our pelvis. *that* is our attach point for the constraint.
        dVector3 p_world;
        dVector3 p_pelvis;
        float y = -0.4f + speed_stretch * 0.14f * -sinf(roll_amt_)
                  + (1.0f - speed_stretch) * -0.2f;
        if (in.jump > 0) y -= 0.3f;
        float z = 0.22f * -cosf(roll_amt_);
        y += 0.05f * in.run_gas;
        z *= 1.3f * in.run_gas + (1.0f - in.run_gas) * 1.0f;
        dBodyGetRelPointPos(in.stand, -step_separation, y, z, p_world);
        assert(in.pelvis);
        dBodyGetPosRelPoint(in.pelvis, p_world[0], p_world[1], p_world[2],
                            p_pelvis);
        joints.right_leg_ik->anchor1[0] = p_pelvis[0];
        joints.right_leg_ik->anchor1[1] = p_pelvis[1];
        joints.right_leg_ik->anchor1[2] = p_pelvis[2];
      }
    }

    // Arms.
    {
      // Adjust our joint strengths.
      {
        float l_still_scale = 1.0f;
        float l_damp_scale = 1.0f;
        float a_stiff_scale = 1.0f;
        float a_damp_scale = 1.0f;
        float lower_arm_a_scale = 1.0f;

        if (in.frozen) {
          l_still_scale *= 5.0f;
          l_damp_scale *= 0.2f;
          a_stiff_scale *= 1000.0f;
          a_damp_scale *= 0.2f;
        } else {
          // Blend lower-arm stiffness toward the character's idle
          // value while standing (1.0 = fully rigid = a no-op).
          lower_arm_a_scale = lower_arm_a_scale * in.run_gas
                              + in.idle_arm_stiffness * (1.0f - in.run_gas);

          // Stiffen up during punches and celebrations.
          if (since_last_punch < 500 || scenetime < in.celebrate_until_time_left
              || scenetime < in.celebrate_until_time_right) {
            l_still_scale *= 2.0f;
            a_stiff_scale *= 2.0f;
          }
        }

        joints.upper_right_arm->linearStiffness =
            kUpperArmLinearStiffness * l_still_scale;
        joints.upper_right_arm->linearDamping =
            kUpperArmLinearDamping * l_damp_scale;
        joints.upper_right_arm->angularStiffness =
            kUpperArmAngularStiffness * a_stiff_scale;
        joints.upper_right_arm->angularDamping =
            kUpperArmAngularDamping * a_damp_scale;

        joints.lower_right_arm->linearStiffness =
            kLowerArmLinearStiffness * l_still_scale;
        joints.lower_right_arm->linearDamping =
            kLowerArmLinearDamping * l_damp_scale;
        joints.lower_right_arm->angularStiffness =
            kLowerArmAngularStiffness * a_stiff_scale * lower_arm_a_scale;
        joints.lower_right_arm->angularDamping =
            kLowerArmAngularDamping * a_damp_scale * lower_arm_a_scale;

        joints.upper_left_arm->linearStiffness =
            kUpperArmLinearStiffness * l_still_scale;
        joints.upper_left_arm->linearDamping =
            kUpperArmLinearDamping * l_damp_scale;
        joints.upper_left_arm->angularStiffness =
            kUpperArmAngularStiffness * a_stiff_scale;
        joints.upper_left_arm->angularDamping =
            kUpperArmAngularDamping * a_damp_scale;

        joints.lower_left_arm->linearStiffness =
            kLowerArmLinearStiffness * l_still_scale;
        joints.lower_left_arm->linearDamping =
            kLowerArmLinearDamping * l_damp_scale;
        joints.lower_left_arm->angularStiffness =
            kLowerArmAngularStiffness * a_stiff_scale * lower_arm_a_scale;
        joints.lower_left_arm->angularDamping =
            kLowerArmAngularDamping * a_damp_scale * lower_arm_a_scale;
      }

      // Adjust our shoulder position.
      {
        float x = kSpazRigShoulderOnTorso[0];
        float y = kSpazRigShoulderOnTorso[1];
        float z = kSpazRigShoulderOnTorso[2];
        float leftZOffset = 0.0f;
        float rightZOffset = 0.0f;
        x += in.shoulder_offset_x;
        y += in.shoulder_offset_y;
        z += in.shoulder_offset_z;

        if (in.punch) {
          if (in.punch_right) {
            leftZOffset = -0.05f;
            rightZOffset = 0.05f;
          } else {
            leftZOffset = 0.05f;
            rightZOffset = -0.05f;
          }
        }

        // Breathing if we're not moving.
        if (!in.frozen) y += breath * 0.012f;

        joints.upper_right_arm->anchor1[0] = x;
        joints.upper_right_arm->anchor1[1] = y;
        joints.upper_right_arm->anchor1[2] = z + rightZOffset;

        joints.upper_left_arm->anchor1[0] = -x;
        joints.upper_left_arm->anchor1[1] = y;
        joints.upper_left_arm->anchor1[2] = z + leftZOffset;
      }

      // Now update ik stuff.
      // If we're frozen, turn it all off.

      if (in.frozen) {
        joints.right_arm_ik->linearStiffness = 0;
        joints.right_arm_ik->linearDamping = 0;
        joints.right_arm_ik->angularStiffness = 0;
        joints.right_arm_ik->angularDamping = 0;
        joints.left_arm_ik->linearStiffness = 0;
        joints.left_arm_ik->linearDamping = 0;
        joints.left_arm_ik->angularStiffness = 0;
        joints.left_arm_ik->angularDamping = 0;
      } else {
        bool haveHeldThing = false;
        if (in.holding_something && in.held) {
          haveHeldThing = true;

          joints.right_arm_ik->linearStiffness = 40.0f;
          joints.right_arm_ik->linearDamping = 1.0f;
          joints.left_arm_ik->linearStiffness = 40.0f;
          joints.left_arm_ik->linearDamping = 1.0f;
          SpazJointTarget* jf;

          dBodyID heldBody = in.held;

          // Find our target point relative to the held body and aim for
          // that.
          dVector3 p_world;
          dVector3 p_torso2;

          jf = joints.right_arm_ik;
          dBodyGetRelPointPos(heldBody, in.hold_hand_offset_right[0],
                              in.hold_hand_offset_right[1],
                              in.hold_hand_offset_right[2], p_world);
          assert(in.torso);
          dBodyGetPosRelPoint(in.torso, p_world[0], p_world[1], p_world[2],
                              p_torso2);
          jf->anchor1[0] = p_torso2[0];
          jf->anchor1[1] = p_torso2[1];
          jf->anchor1[2] = p_torso2[2];
          jf = joints.left_arm_ik;
          dBodyGetRelPointPos(heldBody, in.hold_hand_offset_left[0],
                              in.hold_hand_offset_left[1],
                              in.hold_hand_offset_left[2], p_world);
          assert(in.torso);
          dBodyGetPosRelPoint(in.torso, p_world[0], p_world[1], p_world[2],
                              p_torso2);
          jf->anchor1[0] = p_torso2[0];
          jf->anchor1[1] = p_torso2[1];
          jf->anchor1[2] = p_torso2[2];
        }

        // Not holding something.
        if (!haveHeldThing) {
          // Punching.
          if (since_last_punch < 300) {
            SpazJointTarget* punch_hand;
            SpazJointTarget* opposite_hand;

            SpazJointTarget* shoulder_joint;

            float mirror_scale;

            if (in.punch_right) {
              punch_hand = joints.right_arm_ik;
              opposite_hand = joints.left_arm_ik;
              shoulder_joint = joints.upper_right_arm;
              mirror_scale = -1.0f;
            } else {
              punch_hand = joints.left_arm_ik;
              opposite_hand = joints.right_arm_ik;
              shoulder_joint = joints.upper_left_arm;
              mirror_scale = 1.0f;
            }

            punch_hand->linearStiffness = 100.0f;
            punch_hand->linearDamping = 1.0f;
            opposite_hand->linearStiffness = 30.0f;
            opposite_hand->linearDamping = 0.1f;

            // pull non-punch hand back..
            opposite_hand->anchor1[0] = -0.2f * mirror_scale;
            opposite_hand->anchor1[1] = 0.1f;
            opposite_hand->anchor1[2] = -0.0f;

            // anticipation
            if (since_last_punch < 80) {
              punch_hand->anchor1[0] = 0.4f * mirror_scale;
              punch_hand->anchor1[1] = 0.0f;
              punch_hand->anchor1[2] = -0.1f;
            } else if (since_last_punch < 200) {
              // Offset our punch-direction from our punch shoulder; that's
              // our target point for our fist.
              dVector3 p_world;
              dVector3 p_torso2;
              dBodyGetRelPointPos(in.torso, shoulder_joint->anchor1[0],
                                  shoulder_joint->anchor1[1],
                                  shoulder_joint->anchor1[2], p_world);

              // Offset now that we're in world-space.
              p_world[0] += in.punch_dir_x * 0.7f;
              p_world[2] += in.punch_dir_z * 0.7f;
              p_world[1] += 0.13f;

              // Now translate back to torso space for setting our anchor.
              assert(in.torso);
              dBodyGetPosRelPoint(in.torso, p_world[0], p_world[1], p_world[2],
                                  p_torso2);

              punch_hand->anchor1[0] = p_torso2[0];
              punch_hand->anchor1[1] = p_torso2[1];
              punch_hand->anchor1[2] = p_torso2[2];
            }
          } else if (in.have_thrown && scenetime - in.throw_start < 100
                     && scenetime >= in.throw_start) {
            // Pick-up gesture.
            SpazJointTarget* jf;
            jf = joints.left_arm_ik;
            jf->anchor1[0] = 0.0f;
            jf->anchor1[1] = 0.2f;
            jf->anchor1[2] = 0.8f;
            joints.left_arm_ik->linearStiffness = 10.0f;
            joints.left_arm_ik->linearDamping = 0.1f;

            jf = joints.right_arm_ik;
            jf->anchor1[0] = -0.0f;
            jf->anchor1[1] = 0.2f;
            jf->anchor1[2] = 0.8f;
            joints.right_arm_ik->linearStiffness = 10.0f;
            joints.right_arm_ik->linearDamping = 0.1f;
          } else if (!in.footing && in.balance == 0 && !in.dead) {
            // Wave arms when airborn.
            float wave_amt = static_cast<float>(scenetime) * -0.018f;

            joints.left_arm_ik->linearStiffness = 6.0f;
            joints.left_arm_ik->linearDamping = 0.01f;
            joints.right_arm_ik->linearStiffness = 6.0f;
            joints.right_arm_ik->linearDamping = 0.01f;

            float v1 = sinf(wave_amt) * 0.34f;
            float v2 = cosf(wave_amt) * 0.34f;

            SpazJointTarget* jf;
            jf = joints.left_arm_ik;
            jf->anchor1[0] = 0.4f;
            jf->anchor1[1] = v1 + 0.6f;
            jf->anchor1[2] = v2 + 0.2f;

            jf = joints.right_arm_ik;
            jf->anchor1[0] = -0.4f;
            jf->anchor1[1] = -v1 + 0.6f;
            jf->anchor1[2] = -v2 + 0.2f;
          } else {
            // Not airborn.

            // If we're looking to pick something up, wave our arms in front
            // of us.
            if (!in.knockout && in.pickup > 20) {
              SpazJointTarget* jf;
              jf = joints.left_arm_ik;
              jf->anchor1[0] = 0.4f;
              jf->anchor1[1] = 0.5f;
              jf->anchor1[2] = 0.7f;

              jf = joints.right_arm_ik;
              jf->anchor1[0] = -0.4f;
              jf->anchor1[1] = 0.2f;
              jf->anchor1[2] = 0.7f;

              // Swipe across.
              if (in.pickup < 30) {
                joints.left_arm_ik->anchor1[0] = -0.1f;
                joints.right_arm_ik->anchor1[0] = 0.1f;
              }

              joints.left_arm_ik->linearStiffness = 6.0f;
              joints.left_arm_ik->linearDamping = 0.1f;
              joints.right_arm_ik->linearStiffness = 6.0f;
              joints.right_arm_ik->linearDamping = 0.1f;
            } else {
              // Cursed - wave arms.
              if (!in.knockout && in.curse_death_time != 0) {
                joints.left_arm_ik->linearStiffness = 30.0f;
                joints.left_arm_ik->linearDamping = 0.08f;

                joints.right_arm_ik->linearStiffness = 30.0f;
                joints.right_arm_ik->linearDamping = 0.08f;

                float v1 = sinf(static_cast<float>(scenetime) * 0.05f) * 0.12f;
                float v2 = cosf(static_cast<float>(scenetime) * 0.04f) * 0.12f;

                SpazJointTarget* jf;
                jf = joints.left_arm_ik;
                jf->anchor1[0] = 0.4f + v2;
                jf->anchor1[1] = 0.4f;
                jf->anchor1[2] = 0.3f + v1;

                jf = joints.right_arm_ik;
                jf->anchor1[0] = -0.4f - v2;
                jf->anchor1[1] = 0.4f;
                jf->anchor1[2] = 0.3f + v1;
              } else if (!in.knockout
                         && (scenetime < in.celebrate_until_time_left
                             || scenetime < in.celebrate_until_time_right)) {
                // Celebrating - hold arms in air.
                float v1 = sinf(static_cast<float>(scenetime) * 0.04f) * 0.1f;
                float v2 = cosf(static_cast<float>(scenetime) * 0.03f) * 0.1f;
                SpazJointTarget* jf;
                if (scenetime < in.celebrate_until_time_left) {
                  joints.left_arm_ik->linearStiffness = 30.0f;
                  joints.left_arm_ik->linearDamping = 0.08f;

                  jf = joints.left_arm_ik;
                  jf->anchor1[0] = 0.4f + v2;
                  jf->anchor1[1] = 0.5f;
                  jf->anchor1[2] = 0.2f + v1;
                }
                if (scenetime < in.celebrate_until_time_right) {
                  joints.right_arm_ik->linearStiffness = 30.0f;
                  joints.right_arm_ik->linearDamping = 0.08f;

                  jf = joints.right_arm_ik;
                  jf->anchor1[0] = -0.4f - v2;
                  jf->anchor1[1] = 0.5f;
                  jf->anchor1[2] = 0.2f + v1;
                }
              } else if (!in.knockout && !in.hold_position_pressed
                         && (in.ud || in.lr)) {
                // Sway arms gently when walking, and vigorously
                // when running.
                float blend = in.run_gas * in.run_gas;
                float inv_blend = 1.0f - in.run_gas;
                float wave_amt = roll_amt_;

                joints.left_arm_ik->linearStiffness =
                    14.0f * blend + 0.5f * inv_blend;
                joints.left_arm_ik->linearDamping =
                    0.08f * blend + 0.001f * inv_blend;

                joints.right_arm_ik->linearStiffness =
                    14.0f * blend + 0.5f * inv_blend;
                joints.right_arm_ik->linearDamping =
                    0.08f * blend + 0.001f * inv_blend;

                float v1run = sinf(wave_amt + 3.1415f * 0.5f) * 0.2f;
                float v2run = cosf(wave_amt) * 0.3f;
                float v1 = sinf(wave_amt) * 0.05f;
                float v2 = cosf(wave_amt) * in.arm_swing;

                SpazJointTarget* jf;
                jf = joints.left_arm_ik;
                jf->anchor1[0] = 0.2f;
                jf->anchor1[1] =
                    (-v1run - 0.15f) * blend + (-v1 - 0.1f) * inv_blend;
                jf->anchor1[2] =
                    (-v2run + 0.15f) * blend + (-v2 + 0.1f) * inv_blend;

                jf = joints.right_arm_ik;
                jf->anchor1[0] = -0.2f;
                jf->anchor1[1] =
                    (v1run - 0.15f) * blend + (v1 - 0.1f) * inv_blend;
                jf->anchor1[2] =
                    (v2run + 0.15f) * blend + (v2 + 0.1f) * inv_blend;
              } else {
                // Hang freely.
                joints.left_arm_ik->linearStiffness = 0.0f;
                joints.left_arm_ik->linearDamping = 0.0f;
                joints.right_arm_ik->linearStiffness = 0.0f;
                joints.right_arm_ik->linearDamping = 0.0f;
              }
            }
          }
        }
      }
    }

    if (in.holding_something) {
      // look up to keep out of the way of our arms
      dQFromAxisAndAngle(joints.neck->qrel, 1, 0, 0, 0.5f);
      head_back_ = true;
    } else {
      // if our head was back from holding something, whip it forward again..
      if (head_back_) {
        dQSetIdentity(joints.neck->qrel);
        head_back_ = false;
      }

      // if we're cursed, whip it about
      if (in.curse_death_time != 0) {
        if (in.stepnum % 5 == 0 && RandomFloat() > 0.2f) {
          *head_turning = true;
          dQFromAxisAndAngle(joints.neck->qrel, RandomFloat() * 0.05f,
                             RandomFloat(), RandomFloat() * 0.08f,
                             2.3f * (RandomFloat() - 0.5f));
        }
      } else {
        int64_t gti = in.stepnum;

        // if we're moving or hurt, keep our head straight
        if ((!in.hold_position_pressed && (in.ud || in.lr)) || in.knockout
            || in.frozen) {
          dQSetIdentity(joints.neck->qrel);

          // rotate it slightly in the direction we're turning
          dQFromAxisAndAngle(
              joints.neck->qrel, 0, 1, 0,
              std::max(-1.0f,
                       std::min(1.0f, in.a_vel_y_smoothed_more * -0.14f)));
        } else if (gti % 30 == 0
                   && Utils::precalc_rand_1((gti + in.stream_id * 3 + 143)
                                            % kPrecalcRandsCount)
                          > 0.9f) {
          // otherwise, look around occasionally..
          *head_turning = true;
          dQFromAxisAndAngle(joints.neck->qrel,
                             Utils::precalc_rand_1((in.stream_id + gti)
                                                   % (kPrecalcRandsCount - 3))
                                 * 0.05f,
                             Utils::precalc_rand_2((in.stream_id + 42 * gti)
                                                   % kPrecalcRandsCount),
                             Utils::precalc_rand_3((in.stream_id + 3 * gti)
                                                   % (kPrecalcRandsCount - 1))
                                 * 0.05f,
                             1.5f
                                 * (Utils::precalc_rand_2((in.stream_id + gti)
                                                          % kPrecalcRandsCount)
                                    - 0.5f));
        }
      }
    }
  }
}

}  // namespace ballistica::scene_v1
