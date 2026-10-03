// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_JOINT_FIXED_EF_H_
#define BALLISTICA_BASE_DYNAMICS_JOINT_FIXED_EF_H_

#include "ode/ode.h"
#include "ode/ode_joint.h"

namespace ballistica::base {

/// A custom ODE joint: a "fixed" joint whose linear and angular
/// constraints are soft springs rather than rigid locks. Two anchor
/// points (one in each body's local frame) are pulled together with
/// linear stiffness/damping, and body 2's orientation is pulled toward
/// qrel relative to body 1 with angular stiffness/damping. This is the
/// joint every spaz ragdoll limb (and hair/attachment segment) hangs
/// on: rest pose lives in the joint, the springs enforce it, and
/// setting either stiffness pair to zero disables that half entirely.
///
/// Usable in any ODE world; the spring math is tuned against the
/// world's step length, which the joint carries (stepSeconds).
struct JointFixedEF : public dxJoint {
  dQuaternion qrel;  // Relative rotation body1 -> body2.
  dVector3 anchor1;  // Anchor w.r.t. first body.
  dVector3 anchor2;  // Anchor w.r.t. second body.
  float linearStiffness;
  float linearDamping;
  float angularStiffness;
  float angularDamping;
  bool linearEnabled;
  bool angularEnabled;
  float stepSeconds;
};

/// Translate a stiffness/damping pair into ODE's erp/cfm for a given
/// step length (zero/zero yields an effectively disabled constraint).
void CalcERPCFM(float stiffness, float damping, float step_seconds, float* erp,
                float* cfm);

/// Create a joint attached at the bodies' current relative pose, with
/// the anchor at body 2's current position. Either body may be null
/// (the joint is then left unattached).
auto JointFixedEFCreate(dWorldID world, dBodyID b1, dBodyID b2,
                        float step_seconds, float linear_stiffness,
                        float linear_damping, float angular_stiffness,
                        float angular_damping) -> JointFixedEF*;

/// Create a joint with explicit body-local anchor points and an
/// identity rest rotation. With reposition set, body 2 is moved so the
/// anchors line up (taking body 1's orientation).
auto JointFixedEFCreateAnchored(dWorldID world, dBodyID b1, dBodyID b2,
                                float step_seconds, float linear_stiffness,
                                float linear_damping, float angular_stiffness,
                                float angular_damping, const float* anchor1,
                                const float* anchor2, bool reposition)
    -> JointFixedEF*;

/// Move body 2 so the joint's anchors coincide, giving it body 1's
/// orientation (the rest rotation is deliberately not applied; the
/// springs take it from there).
void JointFixedEFPositionBody(JointFixedEF* j);

/// Lock the rest rotation to the bodies' current relative rotation.
void JointFixedEFFreezeAngle(JointFixedEF* j);

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_JOINT_FIXED_EF_H_
