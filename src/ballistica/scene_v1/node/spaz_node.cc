// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/spaz_node.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/post_process_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/area_of_interest.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/collision.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"
#include "ode/ode_collision_util.h"

namespace ballistica::scene_v1 {

// Pull a random pointer from a ref-vector.
template <class T>
auto GetRandomMedia(const std::vector<Object::Ref<T> >& list) -> T* {
  if (list.empty()) return nullptr;
  return list[rand() % list.size()].get();  // NOLINT yes I know; rand bad.
}

const float kSantaEyeScale = 0.9f;
const float kSantaEyeTranslate = 0.03f;

const float kRunJointLinearStiffness = 80.0f;
const float kRunJointLinearDamping = 2.0f;
const float kRunJointAngularStiffness = 0.2f;
const float kRunJointAngularDamping = 0.002f;

const float kRollerBallLinearStiffness = 1000.0f;
const float kRollerBallLinearDamping = 0.2f;

const float kPelvisDensity = 5.0f;
const float kPelvisLinearStiffness = 300.0f;
const float kPelvisLinearDamping = 20.0f;
const float kPelvisAngularStiffness = 1.5f;
const float kPelvisAngularDamping = 0.06f;

const float kUpperLegDensity = 2.0f;
const float kUpperLegLinearStiffness = 300.0f;
const float kUpperLegLinearDamping = 5.0f;
const float kUpperLegAngularStiffness = 0.12f;
const float kUpperLegAngularDamping = 0.004f;
const float kUpperLegCollideStiffness = 100.0f;
const float kUpperLegCollideDamping = 100.0f;

const float kLowerLegDensity = 2.0f;
const float kLowerLegLinearStiffness = 200.0f;
const float kLowerLegLinearDamping = 5.0f;
const float kLowerLegAngularStiffness = 0.12f;
const float kLowerLegAngularDamping = 0.004f;
const float kLowerLegCollideStiffness = 100.0f;
const float kLowerLegCollideDamping = 100.0f;

const float kToesDensity = 0.5f;
const float kToesLinearStiffness = 50.0f;
const float kToesLinearDamping = 1.0f;
const float kToesAngularStiffness = 0.015f;
const float kToesAngularDamping = 0.0005f;
const float kToesCollideStiffness = 10.0f;
const float kToesCollideDamping = 10.0f;

const float kUpperArmDensity = 2.0f;

const float kUpperArmLinearStiffness = 30.0f;
const float kUpperArmLinearDamping = 1.2f;
const float kUpperArmAngularStiffness = 0.08f;
const float kUpperArmAngularDamping = 0.008f;

const float kLowerArmDensity = 2.0f;
const float kLowerArmLinearStiffness = 80.0f;
const float kLowerArmLinearDamping = 1.0f;
const float kLowerArmAngularStiffness = 0.08f;
const float kLowerArmAngularDamping = 0.008f;

const float kHairFrontLeftLinearStiffness = 0.2f;
const float kHairFrontLeftLinearDamping = 0.01f;
const float kHairFrontLeftAngularStiffness = 0.00025f;
const float kHairFrontLeftAngularDamping = 0.000001f;

const float kHairFrontRightLinearStiffness = 0.2f;
const float kHairFrontRightLinearDamping = 0.01f;
const float kHairFrontRightAngularStiffness = 0.00025f;
const float kHairFrontRightAngularDamping = 0.000001f;

const float kHairPonytailTopLinearStiffness = 1.0f;
const float kHairPonytailTopLinearDamping = 0.03f;
const float kHairPonytailTopAngularStiffness = 0.0015f;
const float kHairPonytailTopAngularDamping = 0.000003f;

const float kHairPonytailBottomLinearStiffness = 0.4f;
const float kHairPonytailBottomLinearDamping = 0.02f;
const float kHairPonytailBottomAngularStiffness = 0.00025f;
const float kHairPonytailBottomAngularDamping = 0.000001f;

const int kPunchDuration = 35;
const int kPickupCooldown = 40;

const float kWingAttachX = 0.3f;
const float kWingAttachY = 0.0f;
const float kWingAttachZ = -0.45f;

const float kWingAttachFlapX = 0.55f;
const float kWingAttachFlapY = 0.0f;
const float kWingAttachFlapZ = -0.35f;

enum SpazBodyType {
  kHeadBodyID,
  kTorsoBodyID,
  kPunchBodyID,
  kPickupBodyID,
  kPelvisBodyID,
  kRollerBodyID,
  kStandBodyID,
  kUpperRightArmBodyID,
  kLowerRightArmBodyID,
  kUpperLeftArmBodyID,
  kLowerLeftArmBodyID,
  kUpperRightLegBodyID,
  kLowerRightLegBodyID,
  kUpperLeftLegBodyID,
  kLowerLeftLegBodyID,
  kLeftToesBodyID,
  kRightToesBodyID,
  kHairFrontRightBodyID,
  kHairFrontLeftBodyID,
  kHairPonyTailTopBodyID,
  kHairPonyTailBottomBodyID
};

static auto AngleBetween2DVectors(dReal x1, dReal y1, dReal x2, dReal y2)
    -> dReal {
  dReal x1_norm, y1_norm, x2_norm, y2_norm;
  dReal len1, len2;
  len1 = sqrtf(x1 * x1 + y1 * y1);
  len2 = sqrtf(x2 * x2 + y2 * y2);
  x1_norm = x1 / len1;
  y1_norm = y1 / len1;
  x2_norm = x2 / len2;
  y2_norm = y2 / len2;
  dReal angle = atanf(y1_norm / x1_norm);
  if (x1_norm < 0) {
    if (y1_norm > 0.0f) {
      angle = angle + 3.141592f;
    } else {
      angle = angle - 3.141592f;
    }
  }
  dReal angle2 = atanf(y2_norm / x2_norm);
  if (x2_norm < 0) {
    if (y2_norm > 0.0f) {
      angle2 = angle2 + 3.141592f;
    } else {
      angle2 = angle2 - 3.141592f;
    }
  }
  dReal angle_diff = angle2 - angle;
  if (angle_diff > 3.141592f) {
    angle_diff -= 3.141592f * 2.0f;
  } else if (angle_diff < -3.141592f) {
    angle_diff += 3.141592f * 2.0f;
  }
  return angle_diff;
}

static void RotationFrom2Axes(dMatrix3 r, dReal x_forward, dReal y_forward,
                              dReal z_forward, dReal x_up, dReal y_up,
                              dReal z_up) {
  Vector3f fwd(x_forward, y_forward, z_forward);
  Vector3f up = Vector3f(x_up, y_up, z_up).Normalized();
  Vector3f side = Vector3f(Vector3f::Cross(fwd, up)).Normalized();
  Vector3f forward2 = Vector3f::Cross(up, side);
  r[0] = forward2.x;
  r[4] = forward2.y;
  r[8] = forward2.z;
  r[1] = up.x;
  r[5] = up.y;
  r[9] = up.z;
  r[2] = side.x;
  r[6] = side.y;
  r[10] = side.z;
}

static void CalcERPCFM(float stiffness, float damping, float* erp, float* cfm) {
  if (stiffness <= 0.0f && damping <= 0.0f) {
    (*erp) = 0.0f;
    // (*cfm) = dInfinity;  // doesn't seem to be happy...
    (*cfm) = 9999999999.0f;
  } else {
    (*erp) = (kGameStepSeconds * stiffness)
             / ((kGameStepSeconds * stiffness) + damping);
    (*cfm) = 1.0f / ((kGameStepSeconds * stiffness) + damping);
  }
}

struct JointFixedEF : public dxJoint {
  dQuaternion qrel;  // relative rotation body1 -> body2
  dVector3 anchor1;  // anchor w.r.t first body
  dVector3 anchor2;  // anchor w.r.t second body
  float linearStiffness;
  float linearDamping;
  float angularStiffness;
  float angularDamping;
  bool linearEnabled;
  bool angularEnabled;
};

static void FixedInit_(JointFixedEF* j) {
  dSetZero(j->qrel, 4);
  dSetZero(j->anchor1, 3);
  dSetZero(j->anchor2, 3);
  j->linearStiffness = 0.0f;
  j->linearDamping = 0.0f;
  j->angularStiffness = 0.0f;
  j->angularDamping = 0.0f;

  // testing
  j->linearEnabled = true;
  j->angularEnabled = true;
}

static void _SetBall(JointFixedEF* joint, dxJoint::Info2* info,
                     dVector3 anchor1, dVector3 anchor2) {
  assert(joint->node[1].body);

  // anchor points in global coordinates with respect to body PORs.
  dVector3 a1, a2;

  int s = info->rowskip;

  // set jacobian
  info->J1l[0] = 1;
  info->J1l[s + 1] = 1;
  info->J1l[2 * s + 2] = 1;
  dMULTIPLY0_331(a1, joint->node[0].body->R, anchor1);
  dCROSSMAT(info->J1a, a1, s, -, +);
  info->J2l[0] = -1;
  info->J2l[s + 1] = -1;
  info->J2l[2 * s + 2] = -1;
  dMULTIPLY0_331(a2, joint->node[1].body->R, anchor2);
  dCROSSMAT(info->J2a, a2, s, +, -);

  // set right hand side
  dReal k = info->fps * info->erp;
  for (int j = 0; j < 3; j++) {
    info->c[j] = k
                 * (a2[j] + joint->node[1].body->pos[j] - a1[j]
                    - joint->node[0].body->pos[j]);
  }
}

// FIXME this is duplicated a few times...
static void _SetFixedOrientation(JointFixedEF* joint, dxJoint::Info2* info,
                                 dQuaternion qrel, int start_row) {
  assert(joint->node[1].body);  // we assume we're connected to 2 bodies..

  int s = info->rowskip;
  int start_index = start_row * s;

  // 3 rows to make body rotations equal
  info->J1a[start_index] = 1;
  info->J1a[start_index + s + 1] = 1;
  info->J1a[start_index + s * 2 + 2] = 1;
  info->J2a[start_index] = -1;
  info->J2a[start_index + s + 1] = -1;
  info->J2a[start_index + s * 2 + 2] = -1;

  // compute the right hand side. the first three elements will result in
  // relative angular velocity of the two bodies - this is set to bring them
  // back into alignment. the correcting angular velocity is
  //   |angular_velocity| = angle/time = erp*theta / stepsize
  //                      = (erp*fps) * theta
  //    angular_velocity  = |angular_velocity| * u
  //                      = (erp*fps) * theta * u
  // where rotation along unit length axis u by theta brings body 2's frame
  // to qrel with respect to body 1's frame. using a small angle approximation
  // for sin(), this gives
  //    angular_velocity  = (erp*fps) * 2 * v
  // where the quaternion of the relative rotation between the two bodies is
  //    q = [cos(theta/2) sin(theta/2)*u] = [s v]

  // get qerr = relative rotation (rotation error) between two bodies
  dQuaternion qerr, e;
  dQuaternion qq;
  dQMultiply1(qq, joint->node[0].body->q, joint->node[1].body->q);
  dQMultiply2(qerr, qq, qrel);
  if (qerr[0] < 0) {
    qerr[1] = -qerr[1];  // adjust sign of qerr to make theta small
    qerr[2] = -qerr[2];
    qerr[3] = -qerr[3];
  }
  dMULTIPLY0_331(e, joint->node[0].body->R, qerr + 1);  // @@@ bad SIMD padding!
  dReal k;

  k = info->fps * info->erp;
  info->c[start_row] = 2 * k * e[0];
  info->c[start_row + 1] = 2 * k * e[1];
  info->c[start_row + 2] = 2 * k * e[2];
}

static void _fixedGetInfo1(JointFixedEF* j, dxJoint::Info1* info) {
  info->m = 0;
  info->nub = 0;
  if (j->linearEnabled
      && (j->linearStiffness > 0.0f || j->linearDamping > 0.0f)) {
    info->m += 3;
    info->nub += 3;
  }
  if (j->angularEnabled
      && (j->angularStiffness > 0.0f || j->angularDamping > 0.0f)) {
    info->m += 3;
    info->nub += 3;
  }
}

static void _fixedGetInfo2(JointFixedEF* joint, dxJoint::Info2* info) {
  assert(joint
         && (joint->linearStiffness > 0.0f || joint->linearDamping > 0.0f
             || joint->angularStiffness > 0.0f
             || joint->angularDamping > 0.0f));
  dReal orig_erp = info->erp;
  bool do_linear =
      (joint->linearEnabled
       && (joint->linearStiffness > 0.0f || joint->linearDamping > 0.0f));
  bool do_angular =
      (joint->angularEnabled
       && (joint->angularStiffness > 0.0f || joint->angularDamping > 0.0f));
  int offs = 0;
  // linear component...
  if (do_linear) {
    float linear_erp = 0;
    float linear_cfm = 0;
    CalcERPCFM(joint->linearStiffness, joint->linearDamping, &linear_erp,
               &linear_cfm);
    info->erp = linear_erp;
    _SetBall(joint, info, joint->anchor1, joint->anchor2);
    info->cfm[0] = linear_cfm;
    info->cfm[1] = linear_cfm;
    info->cfm[2] = linear_cfm;
    offs += 3;
  }
  // angular component...
  if (do_angular) {
    float angular_erp;
    float angular_cfm;
    CalcERPCFM(joint->angularStiffness, joint->angularDamping, &angular_erp,
               &angular_cfm);
    info->erp = angular_erp;
    _SetFixedOrientation(joint, info, joint->qrel, offs);
    info->cfm[offs] = angular_cfm;
    info->cfm[offs + 1] = angular_cfm;
    info->cfm[offs + 2] = angular_cfm;
  }
  info->erp = orig_erp;
}

dxJoint::Vtable fixed_vtable_ = {
    sizeof(JointFixedEF), (dxJoint::init_fn*)FixedInit_,
    (dxJoint::getInfo1_fn*)_fixedGetInfo1,
    (dxJoint::getInfo2_fn*)_fixedGetInfo2, dJointTypeNone};

#if !BA_HEADLESS_BUILD
class SpazNode::FullShadowSet : public Object {
 public:
  ~FullShadowSet() override = default;
  base::BGDynamicsShadow torso_shadow_;
  base::BGDynamicsShadow head_shadow_;
  base::BGDynamicsShadow pelvis_shadow_;
  base::BGDynamicsShadow lower_left_leg_shadow_;
  base::BGDynamicsShadow lower_right_leg_shadow_;
  base::BGDynamicsShadow upper_left_leg_shadow_;
  base::BGDynamicsShadow upper_right_leg_shadow_;
  base::BGDynamicsShadow lower_left_arm_shadow_;
  base::BGDynamicsShadow lower_right_arm_shadow_;
  base::BGDynamicsShadow upper_left_arm_shadow_;
  base::BGDynamicsShadow upper_right_arm_shadow_;
};

class SpazNode::SimpleShadowSet : public Object {
 public:
  base::BGDynamicsShadow shadow_;
};
#endif  // !BA_HEADLESS_BUILD

class SpazNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS SpazNode
  BA_NODE_CREATE_CALL(CreateSpaz);
  BA_BOOL_ATTR(fly, can_fly, set_can_fly);
  BA_BOOL_ATTR(hockey, hockey, set_hockey);
  BA_MATERIAL_ARRAY_ATTR(roller_materials, GetRollerMaterials,
                         SetRollerMaterials);
  BA_MATERIAL_ARRAY_ATTR(extras_material, GetExtrasMaterials,
                         SetExtrasMaterials);
  BA_MATERIAL_ARRAY_ATTR(punch_materials, GetPunchMaterials, SetPunchMaterials);
  BA_MATERIAL_ARRAY_ATTR(pickup_materials, GetPickupMaterials,
                         SetPickupMaterials);
  BA_MATERIAL_ARRAY_ATTR(materials, GetMaterials, SetMaterials);
  BA_FLOAT_ATTR(area_of_interest_radius, area_of_interest_radius,
                set_area_of_interest_radius);
  BA_STRING_ATTR(name, name, set_name);
  BA_STRING_ATTR(counter_text, counter_text, set_counter_text);
  BA_TEXTURE_ATTR(mini_billboard_1_texture, mini_billboard_1_texture,
                  set_mini_billboard_1_texture);
  BA_TEXTURE_ATTR(mini_billboard_2_texture, mini_billboard_2_texture,
                  set_mini_billboard_2_texture);
  BA_TEXTURE_ATTR(mini_billboard_3_texture, mini_billboard_3_texture,
                  set_mini_billboard_3_texture);
  BA_INT64_ATTR(mini_billboard_1_start_time, mini_billboard_1_start_time,
                set_mini_billboard_1_start_time);
  BA_INT64_ATTR(mini_billboard_1_end_time, mini_billboard_1_end_time,
                set_mini_billboard_1_end_time);
  BA_INT64_ATTR(mini_billboard_2_start_time, mini_billboard_2_start_time,
                set_mini_billboard_2_start_time);
  BA_INT64_ATTR(mini_billboard_2_end_time, mini_billboard_2_end_time,
                set_mini_billboard_2_end_time);
  BA_INT64_ATTR(mini_billboard_3_start_time, mini_billboard_3_start_time,
                set_mini_billboard_3_start_time);
  BA_INT64_ATTR(mini_billboard_3_end_time, mini_billboard_3_end_time,
                set_mini_billboard_3_end_time);
  BA_TEXTURE_ATTR(billboard_texture, billboard_texture, set_billboard_texture);
  BA_FLOAT_ATTR(billboard_opacity, billboard_opacity, set_billboard_opacity);
  BA_TEXTURE_ATTR(counter_texture, counter_texture, set_counter_texture);
  BA_BOOL_ATTR(invincible, invincible, set_invincible);
  BA_FLOAT_ARRAY_ATTR(name_color, name_color, SetNameColor);
  BA_FLOAT_ARRAY_ATTR(highlight, highlight, set_highlight);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_FLOAT_ATTR(hurt, hurt, SetHurt);
  BA_BOOL_ATTR(boxing_gloves_flashing, boxing_gloves_flashing,
               set_boxing_gloves_flashing);
  BA_PLAYER_ATTR(source_player, source_player, set_source_player);
  BA_BOOL_ATTR(frozen, frozen, SetFrozen);
  BA_BOOL_ATTR(boxing_gloves, have_boxing_gloves, SetHaveBoxingGloves);
  BA_INT64_ATTR(curse_death_time, curse_death_time, SetCurseDeathTime);
  BA_INT_ATTR(shattered, shattered, SetShattered);
  BA_BOOL_ATTR(dead, dead, SetDead);
  BA_STRING_ATTR(style, style, SetStyle);
  BA_FLOAT_ATTR_READONLY(knockout, GetKnockout);
  BA_FLOAT_ATTR_READONLY(punch_power, punch_power);
  BA_FLOAT_ATTR_READONLY(punch_momentum_angular, GetPunchMomentumAngular);
  BA_FLOAT_ARRAY_ATTR_READONLY(punch_momentum_linear, GetPunchMomentumLinear);
  BA_FLOAT_ATTR_READONLY(damage, damage_out);
  BA_FLOAT_ATTR_READONLY(damage_smoothed, damage_smoothed);
  BA_FLOAT_ARRAY_ATTR_READONLY(punch_velocity, GetPunchVelocity);
  BA_BOOL_ATTR(is_area_of_interest, is_area_of_interest, SetIsAreaOfInterest);
  BA_FLOAT_ARRAY_ATTR_READONLY(velocity, GetVelocity);
  BA_FLOAT_ARRAY_ATTR_READONLY(position_forward, GetPositionForward);
  BA_FLOAT_ARRAY_ATTR_READONLY(position_center, GetPositionCenter);
  BA_FLOAT_ARRAY_ATTR_READONLY(punch_position, GetPunchPosition);
  BA_FLOAT_ARRAY_ATTR_READONLY(torso_position, GetTorsoPosition);
  BA_FLOAT_ARRAY_ATTR_READONLY(position, GetPosition);
  BA_INT_ATTR(hold_body, hold_body, set_hold_body);
  BA_NODE_ATTR(hold_node, hold_node, SetHoldNode);
  BA_SOUND_ARRAY_ATTR(jump_sounds, GetJumpSounds, SetJumpSounds);
  BA_SOUND_ARRAY_ATTR(attack_sounds, GetAttackSounds, SetAttackSounds);
  BA_SOUND_ARRAY_ATTR(impact_sounds, GetImpactSounds, SetImpactSounds);
  BA_SOUND_ARRAY_ATTR(death_sounds, GetDeathSounds, SetDeathSounds);
  BA_SOUND_ARRAY_ATTR(pickup_sounds, GetPickupSounds, SetPickupSounds);
  BA_SOUND_ARRAY_ATTR(fall_sounds, GetFallSounds, SetFallSounds);
  BA_TEXTURE_ATTR(color_texture, color_texture, set_color_texture);
  BA_TEXTURE_ATTR(color_mask_texture, color_mask_texture,
                  set_color_mask_texture);
  BA_MESH_ATTR(head_mesh, head_mesh, set_head_mesh);
  BA_MESH_ATTR(torso_mesh, torso_mesh, set_torso_mesh);
  BA_MESH_ATTR(pelvis_mesh, pelvis_mesh, set_pelvis_mesh);
  BA_MESH_ATTR(upper_arm_mesh, upper_arm_mesh, set_upper_arm_mesh);
  BA_MESH_ATTR(forearm_mesh, forearm_mesh, set_forearm_mesh);
  BA_MESH_ATTR(hand_mesh, hand_mesh, set_hand_mesh);
  BA_MESH_ATTR(upper_leg_mesh, upper_leg_mesh, set_upper_leg_mesh);
  BA_MESH_ATTR(lower_leg_mesh, lower_leg_mesh, set_lower_leg_mesh);
  BA_MESH_ATTR(toes_mesh, toes_mesh, set_toes_mesh);
  BA_BOOL_ATTR(billboard_cross_out, billboard_cross_out,
               set_billboard_cross_out);
  BA_BOOL_ATTR(jump_pressed, jump_pressed, SetJumpPressed);
  BA_BOOL_ATTR(punch_pressed, punch_pressed, SetPunchPressed);
  BA_BOOL_ATTR(bomb_pressed, bomb_pressed, SetBombPressed);
  BA_FLOAT_ATTR(run, run, SetRun);
  BA_BOOL_ATTR(fly_pressed, fly_pressed, SetFlyPressed);
  BA_BOOL_ATTR(pickup_pressed, pickup_pressed, SetPickupPressed);
  BA_BOOL_ATTR(hold_position_pressed, hold_position_pressed,
               SetHoldPositionPressed);
  BA_FLOAT_ATTR(move_left_right, move_left_right, SetMoveLeftRight);
  BA_FLOAT_ATTR(move_up_down, move_up_down, SetMoveUpDown);
  BA_BOOL_ATTR(demo_mode, demo_mode, set_demo_mode);
  BA_INT_ATTR(behavior_version, behavior_version, set_behavior_version);
#undef BA_NODE_TYPE_CLASS

  SpazNodeType()
      : NodeType("spaz", CreateSpaz),
        fly(this),
        hockey(this),
        roller_materials(this),
        extras_material(this),
        punch_materials(this),
        pickup_materials(this),
        materials(this),
        area_of_interest_radius(this),
        name(this),
        counter_text(this),
        mini_billboard_1_texture(this),
        mini_billboard_2_texture(this),
        mini_billboard_3_texture(this),
        mini_billboard_1_start_time(this),
        mini_billboard_1_end_time(this),
        mini_billboard_2_start_time(this),
        mini_billboard_2_end_time(this),
        mini_billboard_3_start_time(this),
        mini_billboard_3_end_time(this),
        billboard_texture(this),
        billboard_opacity(this),
        counter_texture(this),
        invincible(this),
        name_color(this),
        highlight(this),
        color(this),
        hurt(this),
        boxing_gloves_flashing(this),
        source_player(this),
        frozen(this),
        boxing_gloves(this),
        curse_death_time(this),
        shattered(this),
        dead(this),
        style(this),
        knockout(this),
        punch_power(this),
        punch_momentum_angular(this),
        punch_momentum_linear(this),
        damage(this),
        damage_smoothed(this),
        punch_velocity(this),
        is_area_of_interest(this),
        velocity(this),
        position_forward(this),
        position_center(this),
        punch_position(this),
        torso_position(this),
        position(this),
        hold_body(this),
        hold_node(this),
        jump_sounds(this),
        attack_sounds(this),
        impact_sounds(this),
        death_sounds(this),
        pickup_sounds(this),
        fall_sounds(this),
        color_texture(this),
        color_mask_texture(this),
        head_mesh(this),
        torso_mesh(this),
        pelvis_mesh(this),
        upper_arm_mesh(this),
        forearm_mesh(this),
        hand_mesh(this),
        upper_leg_mesh(this),
        lower_leg_mesh(this),
        toes_mesh(this),
        billboard_cross_out(this),
        jump_pressed(this),
        punch_pressed(this),
        bomb_pressed(this),
        run(this),
        fly_pressed(this),
        pickup_pressed(this),
        hold_position_pressed(this),
        move_left_right(this),
        move_up_down(this),
        demo_mode(this),
        behavior_version(this) {}
};

static NodeType* node_type{};

auto SpazNode::InitType() -> NodeType* {
  node_type = new SpazNodeType();
  return node_type;
}

SpazNode::SpazNode(Scene* scene)
    : Node(scene, node_type),
      birth_time_(scene->time()),
      spaz_part_(this),
      hair_part_(this),
      punch_part_(this, false),
      pickup_part_(this, false),
      extras_part_(this, false),
      roller_part_(this, true),
      limbs_part_upper_(this, true),
      limbs_part_lower_(this, true) {
  // Head
  body_head_ =
      Object::New<RigidBody>(kHeadBodyID, &spaz_part_, RigidBody::Type::kBody,
                             RigidBody::Shape::kSphere,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  body_head_->SetDimensions(0.23f, 0, 0, 0.28f, 0, 0, 1.0f);
  body_head_->AddCallback(StaticCollideCallback, this);

  // Torso
  body_torso_ =
      Object::New<RigidBody>(kTorsoBodyID, &spaz_part_, RigidBody::Type::kBody,
                             RigidBody::Shape::kSphere,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  body_torso_->SetDimensions(0.11f, 0, 0, 0.2f, 0, 0, 3.0f);
  body_torso_->AddCallback(StaticCollideCallback, this);

  // Pelvis
  body_pelvis_ =
      Object::New<RigidBody>(kPelvisBodyID, &spaz_part_, RigidBody::Type::kBody,
                             RigidBody::Shape::kBox, RigidBody::kCollideActive,
                             RigidBody::kCollideAll);
  body_pelvis_->AddCallback(StaticCollideCallback, this);

  // Roller Ball
  body_roller_ = Object::New<RigidBody>(
      kRollerBodyID, &roller_part_, RigidBody::Type::kBody,
      RigidBody::Shape::kSphere, RigidBody::kCollideActive,
      RigidBody::kCollideAll, nullptr, RigidBody::kIsRoller);

  body_roller_->SetDimensions(0.3f, 0, 0, 0, 0, 0, 0.1f);
  body_roller_->AddCallback(StaticCollideCallback, this);

  // Stand Body
  stand_body_ =
      Object::New<RigidBody>(kStandBodyID, &extras_part_,
                             RigidBody::Type::kBody, RigidBody::Shape::kSphere,
                             RigidBody::kCollideNone, RigidBody::kCollideNone);
  dBodySetGravityMode(stand_body_->body(), 0);
  stand_body_->SetDimensions(0.3f, 0, 0, 0, 0, 0, 1000.0f);

  // Upper Right Arm
  upper_right_arm_body_ =
      Object::New<RigidBody>(kUpperRightArmBodyID, &limbs_part_upper_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  upper_right_arm_body_->AddCallback(StaticCollideCallback, this);
  upper_right_arm_body_->SetDimensions(0.06f, 0.16f, 0, 0, 0, 0,
                                       kUpperArmDensity);

  // Lower Right Arm
  lower_right_arm_body_ =
      Object::New<RigidBody>(kLowerRightArmBodyID, &limbs_part_lower_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  lower_right_arm_body_->AddCallback(StaticCollideCallback, this);
  lower_right_arm_body_->SetDimensions(0.06f, 0.13f, 0, 0.06f, 0.16f, 0,
                                       kLowerArmDensity);

  // Upper Left Arm
  upper_left_arm_body_ =
      Object::New<RigidBody>(kUpperLeftArmBodyID, &limbs_part_upper_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  upper_left_arm_body_->AddCallback(StaticCollideCallback, this);
  upper_left_arm_body_->SetDimensions(0.06f, 0.16f, 0, 0, 0, 0,
                                      kUpperArmDensity);

  // Lower Left Arm
  lower_left_arm_body_ =
      Object::New<RigidBody>(kLowerLeftArmBodyID, &limbs_part_lower_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  lower_left_arm_body_->AddCallback(StaticCollideCallback, this);
  lower_left_arm_body_->SetDimensions(0.06f, 0.13f, 0, 0.06f, 0.16f, 0,
                                      kLowerArmDensity);

  // Upper Right Leg
  upper_right_leg_body_ =
      Object::New<RigidBody>(kUpperRightLegBodyID, &limbs_part_upper_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  upper_right_leg_body_->AddCallback(StaticCollideCallback, this);

  // Lower Right leg
  lower_right_leg_body_ =
      Object::New<RigidBody>(kLowerRightLegBodyID, &limbs_part_lower_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  lower_right_leg_body_->AddCallback(StaticCollideCallback, this);

  right_toes_body_ =
      Object::New<RigidBody>(kRightToesBodyID, &limbs_part_lower_,
                             RigidBody::Type::kBody, RigidBody::Shape::kSphere,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  right_toes_body_->AddCallback(StaticCollideCallback, this);
  right_toes_body_->SetDimensions(0.075f, 0, 0, 0, 0, 0, kToesDensity);

  // Upper Left Leg
  upper_left_leg_body_ =
      Object::New<RigidBody>(kUpperLeftLegBodyID, &limbs_part_upper_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  upper_left_leg_body_->AddCallback(StaticCollideCallback, this);

  // Lower Left leg
  lower_left_leg_body_ =
      Object::New<RigidBody>(kLowerLeftLegBodyID, &limbs_part_lower_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  lower_left_leg_body_->AddCallback(StaticCollideCallback, this);

  // Left Toes
  left_toes_body_ =
      Object::New<RigidBody>(kLeftToesBodyID, &limbs_part_lower_,
                             RigidBody::Type::kBody, RigidBody::Shape::kSphere,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);
  left_toes_body_->AddCallback(StaticCollideCallback, this);
  left_toes_body_->SetDimensions(0.075f, 0, 0, 0, 0, 0, kToesDensity);

  UpdateBodiesForStyle();

  Stand(0, 0, 0, 0);

  // Attach head to torso.
  neck_joint_ = CreateFixedJoint(body_head_.get(), body_torso_.get(), 1000, 1,
                                 20.0f, 0.3f);

  // Drop the y angular stiffness/damping on our neck so our head can whip
  // left/right a bit easier move connection point up away from torso a bit.
  neck_joint_->anchor1[1] += 0.2f;
  neck_joint_->anchor2[1] += 0.2f;

  // Attach torso to pelvis.
  pelvis_joint_ = CreateFixedJoint(body_pelvis_.get(), body_torso_.get(), 0,
                                   0,      // lin stiff/damp
                                   0, 0);  // ang stiff/damp

  // Move anchor down a bit from torso towards pelvis.
  pelvis_joint_->anchor1[1] -= 0.05f;
  pelvis_joint_->anchor2[1] -= 0.05f;

  // Move anchor point forward a tiny bit (like the curvature of a spine).
  pelvis_joint_->anchor2[2] += 0.05f;

  // Attach upper right arm to torso.
  upper_right_arm_joint_ = CreateFixedJoint(
      body_torso_.get(), upper_right_arm_body_.get(), 0, 0, 0, 0);

  // Move anchor to top of arm.
  upper_right_arm_joint_->anchor2[2] = -0.1f;

  // Move anchor slightly in towards torso.
  upper_right_arm_joint_->anchor2[0] += 0.02f;

  // Attach lower right arm to upper right arm.
  lower_right_arm_joint_ = CreateFixedJoint(
      upper_right_arm_body_.get(), lower_right_arm_body_.get(), 0, 0, 0, 0);

  lower_right_arm_joint_->anchor2[2] = -0.08f;

  // Attach upper left arm to torso.
  upper_left_arm_joint_ = CreateFixedJoint(
      body_torso_.get(), upper_left_arm_body_.get(), 0, 0, 0, 0);

  // Move anchor to top of arm.
  upper_left_arm_joint_->anchor2[2] = -0.1f;

  // Move anchor slightly in towards torso.
  upper_left_arm_joint_->anchor2[0] += -0.02f;

  // Attach lower arm to upper arm.
  lower_left_arm_joint_ = CreateFixedJoint(
      upper_left_arm_body_.get(), lower_left_arm_body_.get(), 0, 0, 0, 0);

  lower_left_arm_joint_->anchor2[2] = -0.08f;

  // Attach upper right leg to leg-mass.
  upper_right_leg_joint_ = CreateFixedJoint(
      body_pelvis_.get(), upper_right_leg_body_.get(), 0, 0, 0, 0);

  upper_right_leg_joint_->anchor2[2] = -0.05f;

  // Attach lower right leg to upper right leg.
  lower_right_leg_joint_ = CreateFixedJoint(
      upper_right_leg_body_.get(), lower_right_leg_body_.get(), 0, 0, 0, 0);

  lower_right_leg_joint_->anchor2[2] = -0.05f;

  // Attach bottom of lower leg to pelvis.
  right_leg_ik_joint_ = CreateFixedJoint(
      body_pelvis_.get(), lower_right_leg_body_.get(), 0.3f, 0.001f, 0, 0);
  dQFromAxisAndAngle(right_leg_ik_joint_->qrel, 1, 0, 0, 1.0f);

  // Move the anchor to the tip of our leg.
  right_leg_ik_joint_->anchor2[2] = 0.05f;

  right_leg_ik_joint_->anchor1[0] = -0.1f;
  right_leg_ik_joint_->anchor1[1] = -0.4f;
  right_leg_ik_joint_->anchor1[2] = 0.0f;

  // Attach toes to lower right foot.
  right_toes_joint_ = CreateFixedJoint(lower_right_leg_body_.get(),
                                       right_toes_body_.get(), 0, 0, 0, 0);

  right_toes_joint_->anchor1[1] += -0.0f;
  right_toes_joint_->anchor2[1] += -0.04f;

  // And an anchor off to the side to make it hinge-like.
  right_toes_joint_2_ = nullptr;
  right_toes_joint_2_ = CreateFixedJoint(lower_right_leg_body_.get(),
                                         right_toes_body_.get(), 0, 0, 0, 0);

  right_toes_joint_2_->anchor1[1] += -0.0f;
  right_toes_joint_2_->anchor2[1] += -0.04f;

  right_toes_joint_2_->anchor1[0] += -0.1f;
  right_toes_joint_2_->anchor2[0] += -0.1f;

  // Attach upper left leg to leg-mass.
  upper_left_leg_joint_ = CreateFixedJoint(
      body_pelvis_.get(), upper_left_leg_body_.get(), 0, 0, 0, 0);

  upper_left_leg_joint_->anchor2[2] = -0.05f;

  // Attach lower left leg to upper left leg.
  lower_left_leg_joint_ = CreateFixedJoint(
      upper_left_leg_body_.get(), lower_left_leg_body_.get(), 0, 0, 0, 0);

  lower_left_leg_joint_->anchor2[2] = -0.05f;

  // Attach bottom of lower leg to pelvis.
  left_leg_ik_joint_ = CreateFixedJoint(
      body_pelvis_.get(), lower_left_leg_body_.get(), 0.3f, 0.001f, 0, 0);

  dQFromAxisAndAngle(left_leg_ik_joint_->qrel, 1, 0, 0, 1.0f);

  // Move the anchor to the tip of our leg.
  left_leg_ik_joint_->anchor2[2] = 0.05f;

  left_leg_ik_joint_->anchor1[0] = 0.1f;
  left_leg_ik_joint_->anchor1[1] = -0.4f;
  left_leg_ik_joint_->anchor1[2] = 0.0f;

  // Attach toes to lower left foot.
  left_toes_joint_ = CreateFixedJoint(lower_left_leg_body_.get(),
                                      left_toes_body_.get(), 0, 0, 0, 0);

  right_toes_joint_->anchor1[1] += -0.0f;
  left_toes_joint_->anchor2[1] += -0.04f;

  // And an anchor off to the side to make it hinge-like.
  left_toes_joint_2_ = nullptr;
  left_toes_joint_2_ = CreateFixedJoint(lower_left_leg_body_.get(),
                                        left_toes_body_.get(), 0, 0, 0, 0);

  left_toes_joint_2_->anchor1[1] += -0.0f;
  left_toes_joint_2_->anchor2[1] += -0.04f;
  left_toes_joint_2_->anchor1[0] += 0.1f;
  left_toes_joint_2_->anchor2[0] += 0.1f;

  // Attach end of right arm to torso.
  right_arm_ik_joint_ =
      CreateFixedJoint(body_torso_.get(), lower_right_arm_body_.get(), 0.0f,
                       0.0f, 0, 0, -0.2f, -0.2f, 0.1f, 0, 0, 0.07f, false);

  left_arm_ik_joint_ =
      CreateFixedJoint(body_torso_.get(), lower_left_arm_body_.get(), 0.0f,
                       0.0f, 0, 0, 0.2f, -0.2f, 0.1f, 0.0f, 0.0f, 0.07f, false);

  // Roller ball joint.
  roller_ball_joint_ = CreateFixedJoint(body_torso_.get(), body_roller_.get(),
                                        kRollerBallLinearStiffness,
                                        kRollerBallLinearDamping, 0, 0);
  base_pelvis_roller_anchor_offset_ = roller_ball_joint_->anchor1[1];

  // Stand joint on our torso.
  stand_joint_ =
      CreateFixedJoint(body_torso_.get(), stand_body_.get(), 100, 1, 200, 10);

  // Roller motor.
  a_motor_roller_ = dJointCreateAMotor(scene->dynamics()->ode_world(), nullptr);
  dJointAttach(a_motor_roller_, body_roller_->body(), nullptr);
  dJointSetAMotorNumAxes(a_motor_roller_, 3);
  dJointSetAMotorAxis(a_motor_roller_, 0, 0, 1, 0, 0);
  dJointSetAMotorAxis(a_motor_roller_, 1, 0, 0, 1, 0);
  dJointSetAMotorAxis(a_motor_roller_, 2, 0, 0, 0, 1);
  dJointSetAMotorParam(a_motor_roller_, dParamFMax, 3.0f);
  dJointSetAMotorParam(a_motor_roller_, dParamFMax2, 3.0f);
  dJointSetAMotorParam(a_motor_roller_, dParamFMax3, 3.0f);
  dJointSetAMotorParam(a_motor_roller_, dParamVel, 0.0f);
  dJointSetAMotorParam(a_motor_roller_, dParamVel2, 0.0f);
  dJointSetAMotorParam(a_motor_roller_, dParamVel3, 1.0f);

  // Attach brakes between our roller ball and our leg mass.
  a_motor_brakes_ = dJointCreateAMotor(scene->dynamics()->ode_world(), nullptr);
  dJointAttach(a_motor_brakes_, body_torso_->body(), body_roller_->body());
  dJointSetAMotorMode(a_motor_brakes_, dAMotorUser);
  dJointSetAMotorNumAxes(a_motor_brakes_, 3);
  dJointSetAMotorAxis(a_motor_brakes_, 0, 1, 1, 0, 0);
  dJointSetAMotorAxis(a_motor_brakes_, 1, 1, 0, 1, 0);
  dJointSetAMotorAxis(a_motor_brakes_, 2, 1, 0, 0, 1);
  dJointSetAMotorParam(a_motor_brakes_, dParamFMax, 10.0f);
  dJointSetAMotorParam(a_motor_brakes_, dParamFMax2, 10.0f);
  dJointSetAMotorParam(a_motor_brakes_, dParamFMax3, 10.0f);
  dJointSetAMotorParam(a_motor_brakes_, dParamVel, 0);
  dJointSetAMotorParam(a_motor_brakes_, dParamVel2, 0);
  dJointSetAMotorParam(a_motor_brakes_, dParamVel3, 0);

  // Give joints initial vals.
  UpdateJoints();

  // We want to have an area of interest by default.
  SetIsAreaOfInterest(true);

  // We want to update each step.
  BA_DEBUG_CHECK_BODIES();
}

void SpazNode::SetPickupPressed(bool val) {
  if (val == pickup_pressed_) return;
  pickup_pressed_ = val;

  // Press
  if (pickup_pressed_) {
    if (frozen_ || knockout_) {
      return;
    }
    if (holding_something_) {
      Throw(false);
    } else {
      if ((pickup_ == 0) && (!knockout_) && (!frozen_))
        pickup_ = kPickupCooldown + 4;
    }
  } else {
    // Release
  }
}

void SpazNode::SetHoldPositionPressed(bool val) {
  if (val == hold_position_pressed_) return;
  hold_position_pressed_ = val;
}

void SpazNode::SetMoveLeftRight(float val) {
  if (val == move_left_right_) {
    return;
  }
  move_left_right_ = val;
  lr_ = static_cast_check_fit<int8_t>(
      std::max(-127, std::min(127, static_cast<int>(127.0f * val))));
}

void SpazNode::SetMoveUpDown(float val) {
  if (val == move_up_down_) {
    return;
  }
  move_up_down_ = val;
  ud_ = static_cast_check_fit<int8_t>(
      std::max(-127, std::min(127, static_cast<int>(127.0f * val))));
}

void SpazNode::SetFlyPressed(bool val) {
  if (val == fly_pressed_) return;
  fly_pressed_ = val;

  // Press.
  if (fly_pressed_) {
    DoFlyPress();
  } else {
    // Release.
  }
}

void SpazNode::SetRun(float val) {
  if (val == run_) {
    return;
  }
  run_ = val;
}

void SpazNode::SetBombPressed(bool val) {
  if (val == bomb_pressed_) {
    return;
  }
  bomb_pressed_ = val;
  if (bomb_pressed_) {
    if (frozen_ || knockout_) {
      return;
    }
    if (holding_something_) {
      throwing_with_bomb_button_ = true;
      Throw(true);
    }
  } else {
    // Released.
  }
}

void SpazNode::SetPunchPressed(bool val) {
  if (val == punch_pressed_) {
    return;
  }
  punch_pressed_ = val;
  if (punch_pressed_) {
    if (frozen_ || knockout_) {
      return;
    }

    // If we're holding something, throw it.
    if (holding_something_) {
      Throw(false);
    } else {
      if (!holding_something_ && (!knockout_) && (!frozen_)) {
        punch_ = kPunchDuration;

        // Left or right punch is determined by our spin.
        if (std::abs(a_vel_y_smoothed_) < 0.3f) {
          // At low rotational speeds lets do random.
          punch_right_ = (RandomFloat() > 0.5f);
        } else {
          punch_right_ = a_vel_y_smoothed_ > 0.0f;
        }
        last_punch_time_ = scene()->time();
        if (SceneSound* sound = GetRandomMedia(attack_sounds_)) {
          if (auto* source = g_base->audio->SourceBeginNew()) {
            const dReal* p_head = dGeomGetPosition(body_head_->geom());
            g_base->audio->PushSourceStopSoundCall(voice_play_id_);
            source->SetPosition(p_head[0], p_head[1], p_head[2]);
            voice_play_id_ = source->Play(sound->GetSoundData());
            source->End();
          }
        }
      }
    }
  } else {
    // Release.
  }
}

void SpazNode::SetJumpPressed(bool val) {
  if (val == jump_pressed_) {
    return;
  }
  jump_pressed_ = val;
  if (jump_pressed_) {
    if (frozen_ || knockout_) {
      return;
    }
    if (!can_fly_) {
      if (SceneSound* sound = GetRandomMedia(jump_sounds_)) {
        if (auto* source = g_base->audio->SourceBeginNew()) {
          const dReal* p_top = dGeomGetPosition(body_head_->geom());
          g_base->audio->PushSourceStopSoundCall(voice_play_id_);
          source->SetPosition(p_top[0], p_top[1], p_top[2]);
          voice_play_id_ = source->Play(sound->GetSoundData());
          source->End();
        }
      }
      if (demo_mode_) {
        jump_ = 5;
      } else {
        jump_ = 7;
      }
      last_jump_time_ = scene()->time();
    }
  } else {
    // Release.
  }
}

static void FreezeJointAngle(JointFixedEF* j) {
  dQMultiply1(j->qrel, j->node[0].body->q, j->node[1].body->q);
}

void SpazNode::UpdateJoints() {
  // (neck joint gets set every step so no update here)

  float l_still_scale = 1.0f;
  float l_damp_scale = 1.0f;
  float a_stiff_scale = 1.0f;
  float a_damp_scale = 1.0f;
  float leg_a_damp_scale = 1.0f;

  // When frozen, lock to our orientations and get more stiff.
  if (frozen_) {
    l_still_scale *= 5.0f;
    l_damp_scale *= 0.2f;
    a_stiff_scale *= 1000.0f;
    a_damp_scale *= 0.2f;
    leg_a_damp_scale *= 1.0f;

    FreezeJointAngle(pelvis_joint_);
    FreezeJointAngle(upper_right_arm_joint_);
    FreezeJointAngle(lower_right_arm_joint_);
    FreezeJointAngle(upper_left_arm_joint_);
    FreezeJointAngle(lower_left_arm_joint_);
    FreezeJointAngle(upper_right_leg_joint_);
    FreezeJointAngle(lower_right_leg_joint_);
    FreezeJointAngle(upper_left_leg_joint_);
    FreezeJointAngle(lower_left_leg_joint_);
    FreezeJointAngle(right_toes_joint_);
    FreezeJointAngle(left_toes_joint_);
    if (hair_front_right_joint_) {
      FreezeJointAngle(hair_front_right_joint_);
    }
    if (hair_front_left_joint_) {
      FreezeJointAngle(hair_front_left_joint_);
    }
    if (hair_ponytail_top_joint_) {
      FreezeJointAngle(hair_ponytail_top_joint_);
    }
    if (hair_ponytail_bottom_joint_) {
      FreezeJointAngle(hair_ponytail_bottom_joint_);
    }
  } else {
    // Not frozen; just normal setup.

    // Set normal joint angles.

    dQFromAxisAndAngle(pelvis_joint_->qrel, 1, 0.0f, 0.0f, -0.4f);

    dQFromAxisAndAngle(upper_right_arm_joint_->qrel, 1, 0.0f, -0.0f, 2.0f);
    dQFromAxisAndAngle(lower_right_arm_joint_->qrel, 1, 0, 0, -1.7f);

    dQFromAxisAndAngle(upper_left_arm_joint_->qrel, 1, -0.0f, 0.0f, 2.0f);
    dQFromAxisAndAngle(lower_left_arm_joint_->qrel, 1, 0, 0, -1.7f);

    dQFromAxisAndAngle(upper_right_leg_joint_->qrel, 1, 0.2f, 0.2f, 0.5f);
    dQFromAxisAndAngle(lower_right_leg_joint_->qrel, 1, 0, 0, 1.0f);
    dQSetIdentity(right_toes_joint_->qrel);

    dQFromAxisAndAngle(upper_left_leg_joint_->qrel, 1, -0.2f, -0.2f, 0.5f);
    dQFromAxisAndAngle(lower_left_leg_joint_->qrel, 1, 0, 0, 3.1415f / 2.0f);
    dQSetIdentity(left_toes_joint_->qrel);
  }

  pelvis_joint_->linearStiffness = kPelvisLinearStiffness * l_still_scale;
  pelvis_joint_->linearDamping = kPelvisLinearDamping * l_damp_scale;
  pelvis_joint_->angularStiffness = kPelvisAngularStiffness * a_stiff_scale;
  pelvis_joint_->angularDamping = kPelvisAngularDamping * a_damp_scale;

  upper_right_leg_joint_->linearStiffness =
      kUpperLegLinearStiffness * l_still_scale;
  upper_right_leg_joint_->linearDamping = kUpperLegLinearDamping * l_damp_scale;
  upper_right_leg_joint_->angularStiffness =
      kUpperLegAngularStiffness * a_stiff_scale;
  upper_right_leg_joint_->angularDamping =
      kUpperLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  lower_right_leg_joint_->linearStiffness =
      kLowerLegLinearStiffness * l_still_scale;
  lower_right_leg_joint_->linearDamping = kLowerLegLinearDamping * l_damp_scale;
  lower_right_leg_joint_->angularStiffness =
      kLowerLegAngularStiffness * a_stiff_scale;
  lower_right_leg_joint_->angularDamping =
      kLowerLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  right_toes_joint_->linearStiffness = kToesLinearStiffness * l_still_scale;
  right_toes_joint_->linearDamping = kToesLinearDamping * l_damp_scale;
  right_toes_joint_->angularStiffness = kToesAngularStiffness * a_stiff_scale;
  right_toes_joint_->angularDamping = kToesAngularDamping * a_damp_scale;

  right_toes_joint_2_->linearStiffness = kToesLinearStiffness * l_still_scale;
  right_toes_joint_2_->linearDamping = kToesLinearDamping * l_damp_scale;
  right_toes_joint_2_->angularStiffness = 0;
  right_toes_joint_2_->angularDamping = 0;

  upper_left_leg_joint_->linearStiffness =
      kUpperLegLinearStiffness * l_still_scale;
  upper_left_leg_joint_->linearDamping = kUpperLegLinearDamping * l_damp_scale;
  upper_left_leg_joint_->angularStiffness =
      kUpperLegAngularStiffness * a_stiff_scale;
  upper_left_leg_joint_->angularDamping =
      kUpperLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  lower_left_leg_joint_->linearStiffness =
      kLowerLegLinearStiffness * l_still_scale;
  lower_left_leg_joint_->linearDamping = kLowerLegLinearDamping * l_damp_scale;
  lower_left_leg_joint_->angularStiffness =
      kLowerLegAngularStiffness * a_stiff_scale;
  lower_left_leg_joint_->angularDamping =
      kLowerLegAngularDamping * a_damp_scale * leg_a_damp_scale;

  left_toes_joint_->linearStiffness = kToesLinearStiffness * l_still_scale;
  left_toes_joint_->linearDamping = kToesLinearDamping * l_damp_scale;
  left_toes_joint_->angularStiffness = kToesAngularStiffness * a_stiff_scale;
  left_toes_joint_->angularDamping = kToesAngularDamping * a_damp_scale;

  left_toes_joint_2_->linearStiffness = kToesLinearStiffness * l_still_scale;
  left_toes_joint_2_->linearDamping = kToesLinearDamping * l_damp_scale;
  left_toes_joint_2_->angularStiffness = 0;
  left_toes_joint_2_->angularDamping = 0;

  // Hair
  if (hair_front_right_joint_) {
    hair_front_right_joint_->linearStiffness =
        kHairFrontRightLinearStiffness * l_still_scale;
    hair_front_right_joint_->linearDamping =
        kHairFrontRightLinearDamping * l_damp_scale;
    hair_front_right_joint_->angularStiffness =
        kHairFrontRightAngularStiffness * a_stiff_scale;
    hair_front_right_joint_->angularDamping =
        kHairFrontRightAngularDamping * a_damp_scale;
  }
  if (hair_front_left_joint_) {
    hair_front_left_joint_->linearStiffness =
        kHairFrontLeftLinearStiffness * l_still_scale;
    hair_front_left_joint_->linearDamping =
        kHairFrontLeftLinearDamping * l_damp_scale;
    hair_front_left_joint_->angularStiffness =
        kHairFrontLeftAngularStiffness * a_stiff_scale;
    hair_front_left_joint_->angularDamping =
        kHairFrontLeftAngularDamping * a_damp_scale;
  }
  if (hair_ponytail_top_joint_) {
    hair_ponytail_top_joint_->linearStiffness =
        kHairPonytailTopLinearStiffness * l_still_scale;
    hair_ponytail_top_joint_->linearDamping =
        kHairPonytailTopLinearDamping * l_damp_scale;
    hair_ponytail_top_joint_->angularStiffness =
        kHairPonytailTopAngularStiffness * a_stiff_scale;
    hair_ponytail_top_joint_->angularDamping =
        kHairPonytailTopAngularDamping * a_damp_scale;
  }
  if (hair_ponytail_bottom_joint_) {
    hair_ponytail_bottom_joint_->linearStiffness =
        kHairPonytailBottomLinearStiffness * l_still_scale;
    hair_ponytail_bottom_joint_->linearDamping =
        kHairPonytailBottomLinearDamping * l_damp_scale;
    hair_ponytail_bottom_joint_->angularStiffness =
        kHairPonytailBottomAngularStiffness * a_stiff_scale;
    hair_ponytail_bottom_joint_->angularDamping =
        kHairPonytailBottomAngularDamping * a_damp_scale;
  }
}

void SpazNode::UpdateBodiesForStyle() {
  // Create hair bodies/joints if need be.
  if (female_hair_) {
    CreateHair();
  } else {
    DestroyHair();
  }

  // Adjust torso size.
  body_torso_->SetDimensions(torso_radius_, 0, 0, 0.2f, 0, 0, 3.0f);

  // Adjust hip and leg size.
  body_pelvis_->SetDimensions(0.25f, 0.16f, 0.10f, 0.25f, 0.16f, 0.16f,
                              kPelvisDensity);

  float thigh_rad = female_ ? 0.06f : 0.04f;
  upper_left_leg_body_->SetDimensions(thigh_rad, 0.12f, 0, 0.05f, 0.12f, 0,
                                      kUpperLegDensity);
  upper_right_leg_body_->SetDimensions(thigh_rad, 0.12f, 0, 0.05f, 0.12f, 0,
                                       kUpperLegDensity);

  float ankle_rad = female_ ? 0.045f : 0.07f;
  lower_left_leg_body_->SetDimensions(ankle_rad, 0.26f - ankle_rad * 2.0f, 0,
                                      0.07f, 0.12f, 0, kLowerLegDensity);
  lower_right_leg_body_->SetDimensions(ankle_rad, 0.26f - ankle_rad * 2.0f, 0,
                                       0.07f, 0.12f, 0, kLowerLegDensity);
}

static void InitObject(dObject* obj, dxWorld* w) {
  obj->world = w;
  obj->next = nullptr;
  obj->tome = nullptr;
  obj->userdata = nullptr;
  obj->tag = 0;
}

static void AddObjectToList(dObject* obj, dObject** first) {
  obj->next = *first;
  obj->tome = first;
  if (*first) (*first)->tome = &obj->next;
  (*first) = obj;
}

static void JointInit(dxWorld* w, dxJoint* j) {
  dIASSERT(w && j);
  InitObject(j, w);
  j->vtable = nullptr;
  j->flags = 0;
  j->node[0].joint = j;
  j->node[0].body = nullptr;
  j->node[0].next = nullptr;
  j->node[1].joint = j;
  j->node[1].body = nullptr;
  j->node[1].next = nullptr;
  dSetZero(j->lambda, 6);
  AddObjectToList(j, reinterpret_cast<dObject**>(&w->firstjoint));
  w->nj++;
}

static void _dJointSetFixed(JointFixedEF* joint) {
  dUASSERT(joint, "bad joint argument");
  dUASSERT(joint->vtable == &fixed_vtable_, "joint is not fixed");

  // This code is taken from sJointSetSliderAxis(), we should really put the
  // common code in its own function.
  // compute the offset between the bodies
  if (joint->node[0].body) {
    if (joint->node[1].body) {
      dQMultiply1(joint->qrel, joint->node[0].body->q, joint->node[1].body->q);
    } else {
    }
  }
}

static void _setAnchors(dxJoint* j, dReal x, dReal y, dReal z, dVector3 anchor1,
                        dVector3 anchor2) {
  if (j->node[0].body) {
    dReal q[4];
    q[0] = x - j->node[0].body->pos[0];
    q[1] = y - j->node[0].body->pos[1];
    q[2] = z - j->node[0].body->pos[2];
    q[3] = 0;
    dMULTIPLY1_331(anchor1, j->node[0].body->R, q);
    if (j->node[1].body) {
      q[0] = x - j->node[1].body->pos[0];
      q[1] = y - j->node[1].body->pos[1];
      q[2] = z - j->node[1].body->pos[2];
      q[3] = 0;
      dMULTIPLY1_331(anchor2, j->node[1].body->R, q);
    } else {
      anchor2[0] = x;
      anchor2[1] = y;
      anchor2[2] = z;
    }
  }
  anchor1[3] = 0;
  anchor2[3] = 0;
}

// Position b relative to b2 based on.
void PositionBodyForJoint(JointFixedEF* j) {
  dBodyID b1 = dJointGetBody(j, 0);
  dBodyID b2 = dJointGetBody(j, 1);
  assert(b1 && b2);
  dBodySetQuaternion(b2, dBodyGetQuaternion(b1));
  dVector3 p;
  dBodyGetRelPointPos(b1, j->anchor1[0] - j->anchor2[0],
                      j->anchor1[1] - j->anchor2[1],
                      j->anchor1[2] - j->anchor2[2], p);
  dBodySetPosition(b2, p[0], p[1], p[2]);
}

auto SpazNode::CreateFixedJoint(RigidBody* b1, RigidBody* b2, float ls,
                                float ld, float as, float ad) -> JointFixedEF* {
  JointFixedEF* j;
  j = static_cast<JointFixedEF*>(
      dAlloc(static_cast<size_t>(fixed_vtable_.size)));
  JointInit(scene()->dynamics()->ode_world(), j);
  j->vtable = &fixed_vtable_;
  if (j->vtable->init) j->vtable->init(j);
  j->feedback = nullptr;

  if (b1 && b2) {
    dJointAttach(j, b1->body(), b2->body());
    _dJointSetFixed(j);
    const dReal* p = dBodyGetPosition(b2->body());
    _setAnchors(j, p[0], p[1], p[2], j->anchor1, j->anchor2);
  }

  j->linearStiffness = ls;
  j->linearDamping = ld;
  j->angularStiffness = as;
  j->angularDamping = ad;

  return j;
}

auto SpazNode::CreateFixedJoint(RigidBody* b1, RigidBody* b2, float ls,
                                float ld, float as, float ad, float a1x,
                                float a1y, float a1z, float a2x, float a2y,
                                float a2z, bool reposition) -> JointFixedEF* {
  assert(b1 && b2);

  JointFixedEF* j;
  j = static_cast<JointFixedEF*>(
      dAlloc(static_cast<size_t>(fixed_vtable_.size)));
  JointInit(scene()->dynamics()->ode_world(), j);
  j->vtable = &fixed_vtable_;
  if (j->vtable->init) j->vtable->init(j);
  j->feedback = nullptr;

  dJointAttach(j, b1->body(), b2->body());
  dQSetIdentity(j->qrel);
  j->anchor1[0] = a1x;
  j->anchor1[1] = a1y;
  j->anchor1[2] = a1z;
  j->anchor2[0] = a2x;
  j->anchor2[1] = a2y;
  j->anchor2[2] = a2z;

  // Ok lets move the second body to line up with the joint.
  if (reposition) {
    PositionBodyForJoint(j);
  }

  j->linearStiffness = ls;
  j->linearDamping = ld;
  j->angularStiffness = as;
  j->angularDamping = ad;

  return j;
}

void SpazNode::UpdateAreaOfInterest() {
  if (area_of_interest_) {
    area_of_interest_->set_position(
        Vector3f(dGeomGetPosition(body_head_->geom())));
    area_of_interest_->set_velocity(
        Vector3f(dBodyGetLinearVel(body_head_->body())));
    area_of_interest_->SetRadius(area_of_interest_radius_);
  }
}

SpazNode::~SpazNode() {
  // If we're holding something, tell that thing it's been dropped.
  DropHeldObject();

  if (area_of_interest_) {
    g_base->graphics->camera()->DeleteAreaOfInterest(area_of_interest_);
    area_of_interest_ = nullptr;
  }

  DestroyHair();

  dJointDestroy(neck_joint_);

  dJointDestroy(upper_right_arm_joint_);
  dJointDestroy(lower_right_arm_joint_);
  dJointDestroy(upper_left_arm_joint_);
  dJointDestroy(lower_left_arm_joint_);

  dJointDestroy(upper_right_leg_joint_);
  dJointDestroy(lower_right_leg_joint_);
  dJointDestroy(right_leg_ik_joint_);
  dJointDestroy(upper_left_leg_joint_);
  dJointDestroy(lower_left_leg_joint_);
  dJointDestroy(left_leg_ik_joint_);
  dJointDestroy(right_arm_ik_joint_);
  dJointDestroy(left_arm_ik_joint_);
  dJointDestroy(left_toes_joint_);
  if (left_toes_joint_2_) {
    dJointDestroy(left_toes_joint_2_);
  }
  dJointDestroy(right_toes_joint_);
  if (right_toes_joint_2_) {
    dJointDestroy(right_toes_joint_2_);
  }

  dJointDestroy(pelvis_joint_);
  dJointDestroy(roller_ball_joint_);
  dJointDestroy(a_motor_brakes_);
  dJointDestroy(stand_joint_);
  dJointDestroy(a_motor_roller_);

  // stop any sounds that may be looping..
  if (tick_play_id_ != 0xFFFFFFFF) {
    g_base->audio->PushSourceStopSoundCall(tick_play_id_);
  }
  if (voice_play_id_ != 0xFFFFFFFF) {
    g_base->audio->PushSourceStopSoundCall(voice_play_id_);
  }
}

void SpazNode::ApplyTorque(float x, float y, float z) {
  dBodyAddTorque(body_roller_->body(), x, y, z);
}

// Given coords within a (-1,-1) to (1,1) box, convert them such that their
// length is never greater than 1.
static void BoxNormalizeToCircle(float* lr, float* ud) {
  if (std::abs((*lr)) < 0.0001f || std::abs((*ud)) < 0.0001f) {
    return;  // Not worth doing anything.
  }

  // Project them out to hit the border.
  float s;
  if (std::abs((*lr)) > std::abs((*ud))) {
    s = 1.0f / std::abs((*lr));
  } else {
    s = 1.0f / std::abs((*ud));
  }
  float proj_lr = (*lr) * s;
  float proj_ud = (*ud) * s;
  float proj_len = sqrtf(proj_lr * proj_lr + proj_ud * proj_ud);
  float fin_scale = 1.0f / proj_len;
  (*lr) *= fin_scale;
  (*ud) *= fin_scale;
}

static void BoxClampToCircle(float* lr, float* ud) {
  float len_squared = (*lr) * (*lr) + (*ud) * (*ud);
  if (len_squared > 1.0f) {
    float len = sqrtf(len_squared);
    float mult = 1.0f / len;
    (*lr) *= mult;
    (*ud) *= mult;
  }
}

void SpazNode::Throw(bool with_bomb_button) {
  throwing_with_bomb_button_ = with_bomb_button;

  if (holding_something_ && !throwing_) {
    throw_start_ = scene()->time();
    have_thrown_ = true;

    if (SceneSound* sound = GetRandomMedia(attack_sounds_)) {
      if (auto* s = g_base->audio->SourceBeginNew()) {
        const dReal* p = dGeomGetPosition(body_head_->geom());
        g_base->audio->PushSourceStopSoundCall(voice_play_id_);
        s->SetPosition(p[0], p[1], p[2]);
        voice_play_id_ = s->Play(sound->GetSoundData());
        s->End();
      }
    }

    // Our throw can't actually start until we've held the thing for our min
    // amount of time.
    float lrf = lr_smooth_;
    float udf = ud_smooth_;
    if (clamp_move_values_to_circle_) {
      BoxClampToCircle(&lrf, &udf);
    } else {
      BoxNormalizeToCircle(&lrf, &udf);
    }

    float scale = std::abs(sqrtf(lrf * lrf + udf * udf));
    throw_power_ = 0.8f * (0.6f + 0.4f * scale);

    // If we *just* picked it up, scale down our throw power slightly
    // (otherwise we'll get an extra boost from the pick-up constraint and
    // it'll fly farther than normal).
    auto since_pick_up = static_cast<float>(throw_start_ - last_pickup_time_);
    if (since_pick_up < 500.0f) {
      throw_power_ *= 0.4f + 0.6f * (since_pick_up / 500.0f);
    }

    // Lock in our throw direction. Otherwise it smooths out to the axes
    // with dpads and we lose our fuzzy in-between aiming.

    throw_lr_ = lr_smooth_;
    throw_ud_ = ud_smooth_;

    // Make ourself a note to drop the item as soon as possible with this
    // power.
    throwing_ = true;
  }
}

void SpazNode::HandleMessage(const char* data_in) {
  const char* data = data_in;
  bool handled = true;
  NodeMessageType type = extract_node_message_type(&data);
  switch (type) {
    case NodeMessageType::kScreamSound: {
      if (dead_ || invincible_) break;
      force_scream_ = true;
      last_force_scream_time_ = scene()->time();
      break;
    }
    case NodeMessageType::kPickedUp: {
      // Let's instantly lose our balance in this case.
      balance_ = 0;
      break;
    }
    case NodeMessageType::kHurtSound: {
      PlayHurtSound();
      break;
    }
    case NodeMessageType::kAttackSound: {
      if (knockout_ || frozen_) {
        break;
      }
      if (SceneSound* sound = GetRandomMedia(attack_sounds_)) {
        if (auto* source = g_base->audio->SourceBeginNew()) {
          const dReal* p_top = dGeomGetPosition(body_head_->geom());
          g_base->audio->PushSourceStopSoundCall(voice_play_id_);
          source->SetPosition(p_top[0], p_top[1], p_top[2]);
          voice_play_id_ = source->Play(sound->GetSoundData());
          source->End();
        }
      }
      break;
    }
    case NodeMessageType::kJumpSound: {
      if (knockout_ || frozen_) {
        break;
      }
      if (SceneSound* sound = GetRandomMedia(jump_sounds_)) {
        if (auto* s = g_base->audio->SourceBeginNew()) {
          const dReal* p_top = dGeomGetPosition(body_head_->geom());
          g_base->audio->PushSourceStopSoundCall(voice_play_id_);
          s->SetPosition(p_top[0], p_top[1], p_top[2]);
          voice_play_id_ = s->Play(sound->GetSoundData());
          s->End();
        }
      }
      break;
    }
    case NodeMessageType::kKnockout: {
      float amt = Utils::ExtractFloat16NBO(&data);
      knockout_ = static_cast_check_fit<uint8_t>(
          std::min(40, std::max(static_cast<int>(knockout_),
                                static_cast<int>(amt * 0.07f))));
      trying_to_fly_ = false;
      break;
    }
    case NodeMessageType::kCelebrate: {
      int duration = Utils::ExtractInt16NBO(&data);
      celebrate_until_time_left_ = celebrate_until_time_right_ =
          scene()->time() + duration;
      break;
    }
    case NodeMessageType::kCelebrateL: {
      int duration = Utils::ExtractInt16NBO(&data);
      celebrate_until_time_left_ = scene()->time() + duration;
      break;
    }
    case NodeMessageType::kCelebrateR: {
      int duration = Utils::ExtractInt16NBO(&data);
      celebrate_until_time_right_ = scene()->time() + duration;
      break;
    }
    case NodeMessageType::kImpulse: {
      last_external_impulse_time_ = scene()->time();
      float dmg = 0.0f;
      float px = Utils::ExtractFloat16NBO(&data);
      float py = Utils::ExtractFloat16NBO(&data);
      float pz = Utils::ExtractFloat16NBO(&data);
      float vx = Utils::ExtractFloat16NBO(&data);
      float vy = Utils::ExtractFloat16NBO(&data);
      float vz = Utils::ExtractFloat16NBO(&data);
      float mag = Utils::ExtractFloat16NBO(&data);
      float velocity_mag = Utils::ExtractFloat16NBO(&data);
      float radius = Utils::ExtractFloat16NBO(&data);
      auto calc_force_only = static_cast<bool>(Utils::ExtractInt16NBO(&data));
      float force_dir_x = Utils::ExtractFloat16NBO(&data);
      float force_dir_y = Utils::ExtractFloat16NBO(&data);
      float force_dir_z = Utils::ExtractFloat16NBO(&data);

      // Area of affect impulses apply to everything.
      if (radius > 0.0f) {
        last_hit_was_punch_ = false;
        float head_mag =
            5.0f
            * body_head_->ApplyImpulse(px, py, pz, vx, vy, vz, force_dir_x,
                                       force_dir_y, force_dir_z, mag,
                                       velocity_mag, radius, calc_force_only);
        dmg += head_mag;
        float torso_mag = body_torso_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += torso_mag;
        float pelvis_mag = body_pelvis_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += pelvis_mag;
        dmg += upper_right_arm_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += lower_right_arm_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += upper_left_arm_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += lower_left_arm_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += upper_right_leg_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += lower_right_leg_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += upper_left_leg_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
        dmg += lower_left_leg_body_->ApplyImpulse(
            px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z, mag,
            velocity_mag, radius, calc_force_only);
      } else {
        // single impulse..
        last_hit_was_punch_ = true;
        const dReal* head_pos = dBodyGetPosition(body_head_->body());
        const dReal* torso_pos = dBodyGetPosition(body_torso_->body());
        const dReal* pelvis_pos = dBodyGetPosition(body_pelvis_->body());
        dVector3 to_head = {px - head_pos[0], py - head_pos[1],
                            pz - head_pos[2]};
        dVector3 to_torso = {px - torso_pos[0], py - torso_pos[1],
                             pz - torso_pos[2]};
        dVector3 to_pelvis = {px - pelvis_pos[0], py - pelvis_pos[1],
                              pz - pelvis_pos[2]};
        float to_head_length = dVector3Length(to_head);
        float to_torso_length = dVector3Length(to_torso);
        float to_pelvis_length = dVector3Length(to_pelvis);
        if (to_head_length < to_torso_length
            && to_head_length < to_pelvis_length) {
          float head_mag =
              5.0f
              * body_head_->ApplyImpulse(px, py, pz, vx, vy, vz, force_dir_x,
                                         force_dir_y, force_dir_z, mag,
                                         velocity_mag, radius, calc_force_only);
          dmg += head_mag;
        } else {
          float torso_mag =
              5.0f
              * body_torso_->ApplyImpulse(
                  px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
                  mag, velocity_mag, radius, calc_force_only);
          dmg += torso_mag;
        }
      }

      // Store this in our damage attr so the user can know how much an impulse
      // hurt us.
      damage_out_ = dmg;

      // Also add it to our smoothed damage attr for things like
      // body-explosions.
      if (!calc_force_only) {
        damage_smoothed_ += dmg;
      }

      // Update knockout if we're applying this.
      if (!calc_force_only) {
        knockout_ = static_cast_check_fit<uint8_t>(
            std::min(40, std::max(static_cast<int>(knockout_),
                                  static_cast<int>(dmg * 0.02f) - 20)));
        trying_to_fly_ = false;
      }
      break;
    }
    case NodeMessageType::kStand: {
      float x = Utils::ExtractFloat16NBO(&data);
      float y = Utils::ExtractFloat16NBO(&data);
      float z = Utils::ExtractFloat16NBO(&data);
      float angle = Utils::ExtractFloat16NBO(&data);
      Stand(x, y, z, angle);
      UpdatePartBirthTimes();
      break;
    }
    case NodeMessageType::kFooting: {
      footing_ += Utils::ExtractInt8(&data);
      trying_to_fly_ = false;
      break;
    }
    case NodeMessageType::kKickback: {
      float pos_x = Utils::ExtractFloat16NBO(&data);
      float pos_y = Utils::ExtractFloat16NBO(&data);
      float pos_z = Utils::ExtractFloat16NBO(&data);
      float dir_x = Utils::ExtractFloat16NBO(&data);
      float dir_y = Utils::ExtractFloat16NBO(&data);
      float dir_z = Utils::ExtractFloat16NBO(&data);
      float mag = Utils::ExtractFloat16NBO(&data);
      Vector3f v = Vector3f(dir_x, dir_y, dir_z).Normalized() * mag;
      dBodyID b = body_torso_->body();
      dBodyEnable(b);
      dBodyAddForceAtPos(b, v.x, v.y, v.z, pos_x, pos_y, pos_z);
      break;
    }
    case NodeMessageType::kFlash: {
      flashing_ = 10;
      break;
    }
    default:
      handled = false;
      break;
  }

  if (!handled) {
    Node::HandleMessage(data_in);
  }
}

void SpazNode::DoFlyPress() {
  if (can_fly_ && !knockout_ && !frozen_) {
    fly_power_ += 25.0f;
    last_fly_time_ = scene()->time();
    trying_to_fly_ = true;

    // Keep from doing too many sparkles.
    static millisecs_t last_sparkle_time = 0;
    millisecs_t t = g_core->AppTimeMillisecs();
    if (t - last_sparkle_time > 200) {
      last_sparkle_time = t;
      auto* s = g_base->audio->SourceBeginNew();
      if (s) {
        const dReal* p_torso = dGeomGetPosition(body_torso_->geom());
        s->SetPosition(p_torso[0], p_torso[1], p_torso[2]);
        s->SetGain(0.3f);
        base::SysSoundID s_id;
        int r = rand() % 100;  // NOLINT
        if (r < 33) {
          s_id = base::SysSoundID::kSparkle;
        } else if (r < 66) {
          s_id = base::SysSoundID::kSparkle2;
        } else {
          s_id = base::SysSoundID::kSparkle3;
        }
        s->Play(g_base->assets->SysSound(s_id));
        s->End();
      }
    }
  }
}

void SpazNode::Step() {
  BA_DEBUG_CHECK_BODIES();

  // Update our body blending values.
  {
    Object::Ref<RigidBody>* bodies[] = {&body_head_,
                                        &body_torso_,
                                        &body_pelvis_,
                                        &body_roller_,
                                        &stand_body_,
                                        &upper_right_arm_body_,
                                        &lower_right_arm_body_,
                                        &upper_left_arm_body_,
                                        &lower_left_arm_body_,
                                        &upper_right_leg_body_,
                                        &lower_right_leg_body_,
                                        &upper_left_leg_body_,
                                        &lower_left_leg_body_,
                                        &left_toes_body_,
                                        &right_toes_body_,
                                        &hair_front_right_body_,
                                        &hair_front_left_body_,
                                        &hair_ponytail_top_body_,
                                        &hair_ponytail_bottom_body_};

    // for (Object::Ref<RigidBody>** body = bodies; *body != nullptr; body++) {
    for (auto* body : bodies) {
      if (RigidBody* bodyptr = body->get()) {
        bodyptr->UpdateBlending();
      }
    }
  }

  step_count_++;

  const dReal* p_head = dGeomGetPosition(body_head_->geom());
  const dReal* p_torso = dGeomGetPosition(body_torso_->geom());

  bool running_fast = false;

  // If we're associated with a player, let the game know where that player
  // is.

  // FIXME: this should simply be an attr connection established on the
  // Python layer.
  if (source_player_.exists()) {
    source_player_->SetPosition(Vector3f(p_torso));
  }

  // Move our smoothed hurt value a short time after we get hit.
  if (scene()->time() - last_hurt_change_time_ > 400) {
    if (hurt_smoothed_ < hurt_) {
      hurt_smoothed_ = std::min(hurt_, hurt_smoothed_ + 0.03f);
    } else {
      hurt_smoothed_ = std::max(hurt_, hurt_smoothed_ - 0.03f);
    }
  }

  // Update our smooth ud/lr vals.
  {
    // Let's use smoothing if all our input values are either -127, 0, or
    // 127. That implies that we're getting non-analog input where
    // smoothing is useful to have (so that we can throw bombs in
    // non-axis-aligned directions, etc.).
    float smoothing;
    if ((ud_ == -127 || ud_ == 0 || ud_ == 127)
        && (lr_ == -127 || lr_ == 0 || lr_ == 127)) {
      if (demo_mode_) {
        smoothing = 0.9f;
      } else {
        smoothing = 0.5f;
      }
    } else {
      smoothing = 0.0f;
    }
    ud_smooth_ =
        smoothing * ud_smooth_
        + (1.0f - smoothing)
              * (hold_position_pressed_ ? 0.0f
                                        : ((static_cast<float>(ud_) / 127.0f)));
    lr_smooth_ =
        smoothing * lr_smooth_
        + (1.0f - smoothing)
              * (hold_position_pressed_ ? 0.0f
                                        : ((static_cast<float>(lr_) / 127.0f)));
  }

  // Update our normalized values.
  {
    float prev_ud = ud_norm_;
    float prev_lr = lr_norm_;

    float this_ud_norm =
        (hold_position_pressed_ ? 0.0f : ((static_cast<float>(ud_) / 127.0f)));
    float this_lr_norm =
        (hold_position_pressed_ ? 0.0f : ((static_cast<float>(lr_) / 127.0f)));
    if (clamp_move_values_to_circle_) {
      BoxClampToCircle(&this_lr_norm, &this_ud_norm);
    } else {
      BoxNormalizeToCircle(&this_lr_norm, &this_ud_norm);
    }

    raw_lr_norm_ = this_lr_norm;
    raw_ud_norm_ = this_ud_norm;

    // Determine if we're running.
    running_ = ((run_ > 0.0f) && !hold_position_pressed_ && !holding_something_
                && !hockey_ && (std::abs(lr_) > 0 || std::abs(ud_) > 0)
                && (!have_thrown_ || (scene()->time() - throw_start_ > 200)));

    if (running_) {
      float run_target = sqrtf(run_);
      float mag = (lr_smooth_ * lr_smooth_ + ud_smooth_ * ud_smooth_);
      if (mag < 0.3f) {
        run_target *= (mag / 0.3f);
      }
      float smoothing = run_target > run_gas_ ? 0.95f : 0.5f;
      run_gas_ = smoothing * run_gas_ + (1.0f - smoothing) * run_target;
    } else {
      run_gas_ = std::max(0.0f, run_gas_ - 0.02f);  // 120hz update
    }

    if (holding_something_)
      run_gas_ = std::max(0.0f, run_gas_ - 0.05f);  // 120hz update

    if (!footing_) run_gas_ = std::max(0.0f, run_gas_ - 0.05f);

    // As we're running faster we simply filter our input values to prevent
    // fast adjustments.

    if (run_ > 0.05f) {
      // Strip out any component of the vector that is more than 90 degrees
      // off of our current direction. Otherwise, extreme opposite
      // directions will have a minimal effect on our actual run direction
      // (a run dir blended with its 180-degree opposite then re-normalized
      // won't really change).
      {
        dVector3 cur_dir = {ud_norm_, lr_norm_, 0};
        dVector3 new_dir = {this_ud_norm, this_lr_norm, 0};
        float dot = dDOT(new_dir, cur_dir);
        if (dot < 0.0f) {
          this_ud_norm -= run_gas_ * (ud_norm_ * dot);
          this_lr_norm -= run_gas_ * (lr_norm_ * dot);
          if (this_ud_norm == 0.0f) this_ud_norm = -0.001f;
          if (this_lr_norm == 0.0f) this_lr_norm = -0.001f;
        }
      }
      float orig_len, target_len;
      float this_ud_norm_norm = this_ud_norm;
      float this_lr_norm_norm = this_lr_norm;
      {
        // Push our input towards a length of 1 if we're holding down the
        // gas.
        orig_len = sqrtf(this_ud_norm_norm * this_ud_norm_norm
                         + this_lr_norm_norm * this_lr_norm_norm);
        target_len = run_gas_ * 1.0f + (1.0f - run_gas_) * orig_len;
        float mult = orig_len == 0.0f ? 1.0f : target_len / orig_len;
        this_ud_norm_norm *= mult;
        this_lr_norm_norm *= mult;
      }

      const dReal* vel = dBodyGetLinearVel(body_torso_->body());
      dVector3 v = {vel[0], vel[1], vel[2]};
      float speed = dVector3Length(v);

      // We use this later for looking angry and stuff.
      if (speed >= 5.0f) {
        running_fast = true;
      }

      float smoothing = 0.975f * (0.9f + 0.1f * run_gas_);
      if (speed < 2.0f) {
        smoothing *= (speed / 2.0f);
      }

      // Blend it with previous results but then re-normalize (we want to
      // prevent sudden direction changes but keep it full-speed-ahead).
      ud_norm_ = smoothing * ud_norm_ + (1.0f - smoothing) * this_ud_norm_norm;
      lr_norm_ = smoothing * lr_norm_ + (1.0f - smoothing) * this_lr_norm_norm;

      // ..and renormalize.
      float new_len = sqrtf(ud_norm_ * ud_norm_ + lr_norm_ * lr_norm_);
      float mult = new_len == 0.0f ? 1.0f : target_len / new_len;
      ud_norm_ *= mult;
      lr_norm_ *= mult;
    } else {
      // Not running; can save some calculations.
      ud_norm_ = this_ud_norm;
      lr_norm_ = this_lr_norm;
    }

    // A sharper one for walking.
    float smoothing_diff = 0.93f;
    ud_diff_smooth_ = smoothing_diff * ud_diff_smooth_
                      + (1.0f - smoothing_diff) * (ud_norm_ - prev_ud);
    lr_diff_smooth_ = smoothing_diff * lr_diff_smooth_
                      + (1.0f - smoothing_diff) * (lr_norm_ - prev_lr);

    // A softer one for running.
    float smoothering_diff = 0.983f;
    ud_diff_smoother_ = smoothering_diff * ud_diff_smoother_
                        + (1.0f - smoothering_diff) * (ud_norm_ - prev_ud);
    lr_diff_smoother_ = smoothering_diff * lr_diff_smoother_
                        + (1.0f - smoothering_diff) * (lr_norm_ - prev_lr);
  }

  float vel_length;

  // Update smoothed avels and stuff.
  {
    float avel = dBodyGetAngularVel(body_torso_->body())[1];
    float smoothing = 0.7f;
    a_vel_y_smoothed_ =
        smoothing * a_vel_y_smoothed_ + (1.0f - smoothing) * avel;
    smoothing = 0.92f;
    a_vel_y_smoothed_more_ =
        smoothing * a_vel_y_smoothed_more_ + (1.0f - smoothing) * avel;

    float abs_a_vel = std::min(25.0f, std::abs(avel));

    // Angular punch momentum; this goes up as we spin fast.
    punch_momentum_angular_d_ += abs_a_vel * 0.0004f;
    // so our up/down rate tops off at some point.
    punch_momentum_angular_d_ *= 0.965f;
    punch_momentum_angular_ += punch_momentum_angular_d_;
    // So our absolute val tops off at some point.
    punch_momentum_angular_ *= 0.92f;

    // Drop down fast if we're spinning slower than 10.
    if (abs_a_vel < 5.0f) {
      punch_momentum_angular_ *= 0.8f + 0.2f * (abs_a_vel / 5.0f);
    }

    const dReal* vel = dBodyGetLinearVel(body_torso_->body());
    vel_length = sqrtf(vel[0] * vel[0] + vel[1] * vel[1] + vel[2] * vel[2]);

    punch_momentum_linear_d_ += vel_length * 0.004f;
    punch_momentum_linear_d_ *= 0.95f;  // Suppress rate of upward change.
    punch_momentum_linear_ += punch_momentum_linear_d_;
    punch_momentum_linear_ *= 0.96f;  // Suppress absolute value.
    if (vel_length < 5.0f) {
      punch_momentum_linear_ *= 0.9f + 0.1f * (vel_length / 5.0f);
    }

    millisecs_t since_last_punch = scene()->time() - last_punch_time_;
    if (since_last_punch < 200) {
      punch_power_ = (0.5f
                      + 0.5f
                            * (sinf((static_cast<float>(since_last_punch) / 200)
                                        * (2.0f * 3.1415f)
                                    - (3.14159f * 0.5f))));
      // Let's go between 0.5f and 1 so there's a bit less variance.
      punch_power_ = 0.7f + 0.3f * punch_power_;
    } else {
      punch_power_ = 0.0f;
    }
  }

  // Update wings if we've got 'em.
  if (wings_) {
    float maxDist = 0.8f;
    Vector3f p_wing_l = {0.0f, 0.0f, 0.0f};
    Vector3f p_wing_r = {0.0f, 0.0f, 0.0f};
    float x, y, z;
    millisecs_t cur_time = scene()->time();

    // Left wing.
    if ((flapping_ || jump_ > 0 || running_) && !frozen_ && !knockout_) {
      flap_ = (cur_time % 200 < 100);
    }
    if (flap_) {
      x = kWingAttachX;
      y = kWingAttachY;
      z = kWingAttachZ;
    } else {
      x = kWingAttachFlapX;
      y = kWingAttachFlapY;
      z = kWingAttachFlapZ;
    }
    dBodyGetRelPointPos(body_torso_->body(), x, y, z, p_wing_l.v);
    Vector3f diff = (p_wing_l - wing_pos_left_);
    if (diff.LengthSquared() > maxDist * maxDist) {
      diff *= (maxDist / diff.Length());
    }
    wing_vel_left_ += diff * 0.03f;
    wing_vel_left_ *= 0.93f;
    wing_pos_left_ += wing_vel_left_;

    // Right wing.
    dBodyGetRelPointPos(body_torso_->body(), -x, y, z, p_wing_r.v);
    diff = (p_wing_r - wing_pos_right_);
    if (diff.LengthSquared() > maxDist * maxDist) {
      diff *= (maxDist / diff.Length());
    }

    // Use slightly different values from left for some variation.
    wing_vel_right_ += diff * 0.036f;
    wing_vel_right_ *= 0.95f;
    wing_pos_right_ += wing_vel_right_;
  }

  // Toggle angular components of some joints off and on for increased
  // efficiency 93 to 123.

  // Always on for punches or frozen.
  bool always_on = (frozen_ || (scene()->time() - last_punch_time_ < 500));

  if (always_on) {
    upper_left_arm_joint_->angularEnabled = true;
    upper_right_arm_joint_->angularEnabled = true;
    lower_right_arm_joint_->angularEnabled = true;
    lower_left_arm_joint_->angularEnabled = true;

    upper_right_leg_joint_->angularEnabled = true;
    upper_left_leg_joint_->angularEnabled = true;
    lower_right_leg_joint_->angularEnabled = true;
    lower_left_leg_joint_->angularEnabled = true;

    right_toes_joint_->angularEnabled = true;
    left_toes_joint_->angularEnabled = true;

    left_toes_joint_2_->linearEnabled = true;
    right_toes_joint_2_->linearEnabled = true;
  } else {
    int64_t t = scene()->stepnum();

    upper_left_arm_joint_->angularEnabled = (t % 2 == 0);
    upper_right_arm_joint_->angularEnabled = (t % 2 == 1);
    lower_right_arm_joint_->angularEnabled = (t % 2 == 1);
    lower_left_arm_joint_->angularEnabled = (t % 2 == 0);

    upper_right_leg_joint_->angularEnabled = (t % 2 == 0);
    upper_left_leg_joint_->angularEnabled = (t % 2 == 1);
    lower_right_leg_joint_->angularEnabled = (t % 2 == 1);
    lower_left_leg_joint_->angularEnabled = (t % 2 == 0);

    right_toes_joint_->angularEnabled = (t % 2 == 0);
    left_toes_joint_->angularEnabled = (t % 2 == 1);

    left_toes_joint_2_->linearEnabled = (t % 3 == 0);
    right_toes_joint_2_->linearEnabled = (t % 3 == 2);
  }

  // Update our limb-self-collide value.
  // In certain cases (such as slowly walking in a straight line)
  // we can completely skip collision tests between ourself with no
  // real visual difference. This is a nice efficiency boost.

  // (Turned this off at some point; don't remember why.)
  // We inch self-collide down if we're moving steadily, not turning too
  // fast, and not hurt or holding stuff.
  //  if (vel_length > 1.0f
  //      and (std::abs(lr_smooth_) > 0.5f or std::abs(ud_smooth_) > 0.5f)) {
  //    limb_self_collide_ -= 0.01f;
  //  } else {
  //    limb_self_collide_ += 0.1f;
  //  }

  // if (std::abs(_aVelYSmoothed) > 5.0f) limb_self_collide_ += 0.2f;
  // if (knockout_ != 0 or holding_something_) limb_self_collide_ += 0.1f;
  // limb_self_collide_ = std::min(1.0f,std::max(0.0f,limb_self_collide_));

  // Keep track of how long we're off the ground.
  if (footing_) {
    fly_time_ = 0;
  } else {
    fly_time_++;
  }

  // If we're not touching the ground and are moving fast enough, we can cause
  // damage to things we hit.
  {
    const dReal* lVel = dBodyGetLinearVel(body_torso_->body());
    float mag_squared =
        lVel[0] * lVel[0] + lVel[1] * lVel[1] + lVel[2] * lVel[2];
    bool can_damage = (mag_squared > 20 && fly_time_ > 60);
    body_torso_->set_can_cause_impact_damage(can_damage);
    body_pelvis_->set_can_cause_impact_damage(can_damage);
    body_head_->set_can_cause_impact_damage(can_damage);
  }

  // Make sure none of our bodies are spinning/moving too fast.
  {
    float max_mag_squared = 400.0f;
    float max_mag_squared_lin = 300.0f;

    // Shattering frozen dudes always looks too fast. Let's keep it down.
    if (frozen_ && shattered_) {
      max_mag_squared_lin = 100.0f;
    }

    dBodyID bodies[11];
    bodies[0] = body_head_->body();
    bodies[1] = body_torso_->body();
    bodies[2] = upper_right_arm_body_->body();
    bodies[3] = lower_right_arm_body_->body();
    bodies[4] = upper_left_arm_body_->body();
    bodies[5] = lower_left_arm_body_->body();
    bodies[6] = upper_right_leg_body_->body();
    bodies[7] = upper_left_leg_body_->body();
    bodies[8] = lower_right_leg_body_->body();
    bodies[9] = lower_left_leg_body_->body();
    bodies[10] = nullptr;

    for (dBodyID* body = bodies; *body != nullptr; body++) {
      const dReal* aVel = dBodyGetAngularVel(*body);
      float mag_squared =
          aVel[0] * aVel[0] + aVel[1] * aVel[1] + aVel[2] * aVel[2];
      if (mag_squared > max_mag_squared) {
        float scale = max_mag_squared / mag_squared;
        dBodySetAngularVel(*body, aVel[0] * scale, aVel[1] * scale,
                           aVel[2] * scale);
      }
      const dReal* lVel = dBodyGetLinearVel(*body);
      mag_squared = lVel[0] * lVel[0] + lVel[1] * lVel[1] + lVel[2] * lVel[2];
      if (mag_squared > max_mag_squared_lin) {
        float scale = max_mag_squared_lin / mag_squared;
        dBodySetLinearVel(*body, lVel[0] * scale, lVel[1] * scale,
                          lVel[2] * scale);
      }
    }

    {
      // If we've got hair bodies, apply a wee bit of drag to them so it looks
      // cool when we run
      Object::Ref<RigidBody>* bodies2[] = {
          &hair_front_right_body_, &hair_front_left_body_,
          &hair_ponytail_top_body_, &hair_ponytail_bottom_body_, nullptr};
      float drag = 0.94f;
      for (Object::Ref<RigidBody>** body = bodies2; *body != nullptr; body++) {
        if ((**body).exists()) {
          dBodyID b = (**body)->body();
          const dReal* lVel = dBodyGetLinearVel(b);
          dBodySetLinearVel(b, lVel[0] * drag, lVel[1] * drag, lVel[2] * drag);
        }
      }
    }
  }

  // Update jolt stuff. If our head jolts suddenly we may knock ourself out for
  // a bit or may shatter.
  {
    const dReal* head_vel = dBodyGetLinearVel(body_head_->body());

    // TODO(ericf): average our jolt-head-vel towards the current vel a bit for
    //  smoothing.
    dVector3 diff;
    diff[0] = head_vel[0] - jolt_head_vel_[0];
    diff[1] = head_vel[1] - jolt_head_vel_[1];
    diff[2] = head_vel[2] - jolt_head_vel_[2];
    dReal len = dVector3Length(diff);
    jolt_head_vel_[0] = head_vel[0];
    jolt_head_vel_[1] = head_vel[1];
    jolt_head_vel_[2] = head_vel[2];

    millisecs_t cur_time = scene()->time();

    // If we're jolting and have just been touched in the head and haven't been
    // pushed on by anything external recently (explosion, punch, etc), lets add
    // some shock damage to ourself.
    if (len > 3.0f && cur_time - last_pickup_time_ >= 500
        && cur_time - last_head_collide_time_ <= 30
        && cur_time - last_external_impulse_time_ >= 300
        && cur_time - last_impact_damage_dispatch_time_ > 500) {
      impact_damage_accum_ += len - 3.0f;
    } else if (impact_damage_accum_ > 0.0f) {
      // If we're no longer adding damage but have accumulated some, lets
      // dispatch it.
      DispatchImpactDamageMessage(impact_damage_accum_);
      impact_damage_accum_ = 0.0f;
      last_impact_damage_dispatch_time_ = cur_time;
    }

    // Make it difficult (but not impossible) to shatter within the first second
    // (so we hopefully survive falling over).
    float shatter_len;
    if (cur_time - last_shatter_test_time_ < 1000) {
      shatter_len = 8.0f;
    } else {
      shatter_len = 2.0f;
    }

    if (frozen_ && len > shatter_len) {
      last_shatter_test_time_ = cur_time;
      DispatchShouldShatterMessage();
    }
  }

  bool head_turning = false;

  // If we're punching.
  millisecs_t scenetime = scene()->time();
  millisecs_t since_last_punch = scenetime - last_punch_time_;

  // Breathing when not moving.
  float breath = 0.0f;
  if (!dead_ && !shattered_ && (hold_position_pressed_ || (!ud_ && !lr_))) {
    breath = sinf(static_cast<float>(scenetime) * 0.005f);
  }

  // If we're shattered we just make sure our joints are ineffective.
  if (shattered_) {
    JointFixedEF* joints[20];

    // Fill in our broken joints.
    {
      JointFixedEF** j = joints;

      *j = right_leg_ik_joint_;
      j++;
      *j = left_leg_ik_joint_;
      j++;
      *j = right_arm_ik_joint_;
      j++;
      *j = left_arm_ik_joint_;
      j++;
      if (shatter_damage_ & kUpperRightArmJointBroken) {
        *j = upper_right_arm_joint_;
        j++;
      }
      if (shatter_damage_ & kLowerRightArmJointBroken) {
        *j = lower_right_arm_joint_;
        j++;
      }
      if (shatter_damage_ & kUpperLeftArmJointBroken) {
        *j = upper_left_arm_joint_;
        j++;
      }
      if (shatter_damage_ & kLowerLeftArmJointBroken) {
        *j = lower_left_arm_joint_;
        j++;
      }
      if (shatter_damage_ & kUpperLeftLegJointBroken) {
        *j = upper_left_leg_joint_;
        j++;
      }
      if (shatter_damage_ & kLowerLeftLegJointBroken) {
        *j = lower_left_leg_joint_;
        j++;
      }
      if (shatter_damage_ & kUpperRightLegJointBroken) {
        *j = upper_right_leg_joint_;
        j++;
      }
      if (shatter_damage_ & kLowerRightLegJointBroken) {
        *j = lower_right_leg_joint_;
        j++;
      }
      if (shatter_damage_ & kNeckJointBroken) {
        *j = neck_joint_;
        j++;
      }
      if (shatter_damage_ & kPelvisJointBroken) {
        *j = pelvis_joint_;
        j++;
      }
      *j = nullptr;
    }

    for (JointFixedEF** j = joints; *j != nullptr; j++)
      (**j).linearStiffness = (**j).linearDamping = (**j).angularStiffness =
          (**j).angularDamping = 0.0f;

  } else {
    // Not shattered; do normal stuff.

    // Adjust neck strength.
    {
      JointFixedEF* j = neck_joint_;
      if (j) {
        if (knockout_) {
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
      if (knockout_ || balance_ == 0 || frozen_) {
        // flail our legs when airborn and alive
        if (!footing_ && balance_ == 0 && !dead_) {
          left_leg_ik_joint_->linearStiffness = kRunJointLinearStiffness * 0.4f;
          left_leg_ik_joint_->linearDamping = kRunJointLinearDamping * 0.2f;
          left_leg_ik_joint_->angularStiffness =
              kRunJointAngularStiffness * 0.2f;
          left_leg_ik_joint_->angularDamping = kRunJointAngularDamping * 0.2f;
          right_leg_ik_joint_->linearStiffness =
              kRunJointLinearStiffness * 0.4f;
          right_leg_ik_joint_->linearDamping = kRunJointLinearDamping * 0.2f;
          right_leg_ik_joint_->angularStiffness =
              kRunJointAngularStiffness * 0.2f;
          right_leg_ik_joint_->angularDamping = kRunJointAngularDamping * 0.2f;
          roll_amt_ -= 0.2f;
          if (roll_amt_ < (-2.0f * 3.141592f)) {
            roll_amt_ += 2.0f * 3.141592f;
          }
          float x = 0.1f;
          float y = -0.3f;
          float z = 0.22f * cosf(roll_amt_);
          left_leg_ik_joint_->anchor1[0] = x;
          left_leg_ik_joint_->anchor1[1] = y;
          left_leg_ik_joint_->anchor1[2] = z;
          right_leg_ik_joint_->anchor1[0] = -x;
          right_leg_ik_joint_->anchor1[1] = y;
          right_leg_ik_joint_->anchor1[2] = -z;
        } else {
          // we're frozen or knocked out; turn off run-joint connections...
          left_leg_ik_joint_->linearStiffness = 0.0f;
          left_leg_ik_joint_->linearDamping = 0.0f;
          left_leg_ik_joint_->angularStiffness = 0.0f;
          left_leg_ik_joint_->angularDamping = 0.0f;
          right_leg_ik_joint_->linearStiffness = 0.0f;
          right_leg_ik_joint_->linearDamping = 0.0f;
          right_leg_ik_joint_->angularStiffness = 0.0f;
          right_leg_ik_joint_->angularDamping = 0.0f;
        }
      } else {
        // Do normal running updates.

        // In hockey mode lets transfer a bit of our momentum to the direction
        // we're facing if our skates are on the ground.
        if (hockey_ && footing_) {
          const dReal* rollVel = dBodyGetLinearVel(body_roller_->body());

          dVector3 rollVelNorm = {rollVel[0], rollVel[1], rollVel[2]};
          dNormalize3(rollVelNorm);

          dVector3 forward;
          dBodyVectorToWorld(stand_body_->body(), 0, 0, 1, forward);

          float dot = dDOT(rollVelNorm, forward);

          float mag = -6.0f * std::abs(dot);

          dVector3 f = {mag * rollVel[0], mag * rollVel[1], mag * rollVel[2]};
          float fMag = dVector3Length(f);

          if (dot < 0.0f) fMag *= -1.0f;  // if we're going backwards..

          dBodyAddForce(body_roller_->body(), f[0], f[1], f[2]);
          dBodyAddForce(body_roller_->body(), forward[0] * fMag,
                        forward[1] * fMag, forward[2] * fMag);
        }

        left_leg_ik_joint_->linearStiffness = kRunJointLinearStiffness;
        left_leg_ik_joint_->linearDamping = kRunJointLinearDamping;
        left_leg_ik_joint_->angularStiffness = kRunJointAngularStiffness;
        left_leg_ik_joint_->angularDamping = kRunJointAngularDamping;
        right_leg_ik_joint_->linearStiffness = kRunJointLinearStiffness;
        right_leg_ik_joint_->linearDamping = kRunJointLinearDamping;
        right_leg_ik_joint_->angularStiffness = kRunJointAngularStiffness;
        right_leg_ik_joint_->angularDamping = kRunJointAngularDamping;

        // Tighten things up for running.
        left_leg_ik_joint_->linearStiffness *=
            2.0f * run_gas_ + (1.0f - run_gas_) * 1.0f;
        left_leg_ik_joint_->linearDamping *=
            2.0f * run_gas_ + (1.0f - run_gas_) * 1.0f;
        right_leg_ik_joint_->linearStiffness *=
            2.0f * run_gas_ + (1.0f - run_gas_) * 1.0f;
        right_leg_ik_joint_->linearDamping *=
            2.0f * run_gas_ + (1.0f - run_gas_) * 1.0f;

        if (hockey_) {
          if (hold_position_pressed_ || (!ud_ && !lr_)) {
            left_leg_ik_joint_->linearStiffness *= 0.05f;
            left_leg_ik_joint_->linearDamping *= 0.1f;
            left_leg_ik_joint_->angularStiffness *= 0.05f;
            left_leg_ik_joint_->angularDamping *= 0.1f;
            right_leg_ik_joint_->linearStiffness *= 0.05f;
            right_leg_ik_joint_->linearDamping *= 0.1f;
            right_leg_ik_joint_->angularStiffness *= 0.05f;
            right_leg_ik_joint_->angularDamping *= 0.1f;
          }
        }

        const dReal* ballAVel = dBodyGetAngularVel(body_roller_->body());
        const dReal aVelMag =
            sqrtf(ballAVel[0] * ballAVel[0] + ballAVel[1] * ballAVel[1]
                  + ballAVel[2] * ballAVel[2]);

        // When we're stopped, press our feet downward.
        float speed_stretch = std::min(
            sqrtf(lr_norm_ * lr_norm_ + ud_norm_ * ud_norm_) * 2.0f, 1.0f);

        float rollScale = hockey_ ? 0.6f : 1.0f;

        // Push towards 0.8f when running.
        rollScale = run_gas_ * 0.8f + (1.0f - run_gas_) * rollScale;

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
        float step_separation = female_ ? 0.03f : 0.08f;
        if (ninja_) {
          step_separation *= 0.7f;
        }
        {
          // Take a point relative to stand-body and then find it in the space
          // of our pelvis. *that* is our attach point for the constraint.
          dVector3 p_world;
          dVector3 p_pelvis;
          float y = -0.4f + speed_stretch * 0.14f * sinf(roll_amt_)
                    + (1.0f - speed_stretch) * -0.2f;
          if (jump_ > 0) y -= 0.3f;
          float z = 0.22f * cosf(roll_amt_);
          y += 0.06f * run_gas_;
          z *= 1.4f * run_gas_ + (1.0f - run_gas_) * 1.0f;
          dBodyGetRelPointPos(stand_body_->body(), step_separation, y, z,
                              p_world);
          assert(body_pelvis_.exists());
          dBodyGetPosRelPoint(body_pelvis_->body(), p_world[0], p_world[1],
                              p_world[2], p_pelvis);
          left_leg_ik_joint_->anchor1[0] = p_pelvis[0];
          left_leg_ik_joint_->anchor1[1] = p_pelvis[1];
          left_leg_ik_joint_->anchor1[2] = p_pelvis[2];
        }
        // RIGHT LEG
        {
          // Take a point relative to stand-body and then find it in the space
          // of our pelvis. *that* is our attach point for the constraint.
          dVector3 p_world;
          dVector3 p_pelvis;
          float y = -0.4f + speed_stretch * 0.14f * -sinf(roll_amt_)
                    + (1.0f - speed_stretch) * -0.2f;
          if (jump_ > 0) y -= 0.3f;
          float z = 0.22f * -cosf(roll_amt_);
          y += 0.05f * run_gas_;
          z *= 1.3f * run_gas_ + (1.0f - run_gas_) * 1.0f;
          dBodyGetRelPointPos(stand_body_->body(), -step_separation, y, z,
                              p_world);
          assert(body_pelvis_.exists());
          dBodyGetPosRelPoint(body_pelvis_->body(), p_world[0], p_world[1],
                              p_world[2], p_pelvis);
          right_leg_ik_joint_->anchor1[0] = p_pelvis[0];
          right_leg_ik_joint_->anchor1[1] = p_pelvis[1];
          right_leg_ik_joint_->anchor1[2] = p_pelvis[2];
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

          if (frozen_) {
            l_still_scale *= 5.0f;
            l_damp_scale *= 0.2f;
            a_stiff_scale *= 1000.0f;
            a_damp_scale *= 0.2f;
          } else {
            // Allow female arms to relax a bit more unless we're running.
            if (female_) {
              lower_arm_a_scale =
                  lower_arm_a_scale * run_gas_ + 0.2f * (1.0f - run_gas_);
            }

            // Stiffen up during punches and celebrations.
            if (since_last_punch < 500 || scenetime < celebrate_until_time_left_
                || scenetime < celebrate_until_time_right_) {
              l_still_scale *= 2.0f;
              a_stiff_scale *= 2.0f;
            }
          }

          upper_right_arm_joint_->linearStiffness =
              kUpperArmLinearStiffness * l_still_scale;
          upper_right_arm_joint_->linearDamping =
              kUpperArmLinearDamping * l_damp_scale;
          upper_right_arm_joint_->angularStiffness =
              kUpperArmAngularStiffness * a_stiff_scale;
          upper_right_arm_joint_->angularDamping =
              kUpperArmAngularDamping * a_damp_scale;

          lower_right_arm_joint_->linearStiffness =
              kLowerArmLinearStiffness * l_still_scale;
          lower_right_arm_joint_->linearDamping =
              kLowerArmLinearDamping * l_damp_scale;
          lower_right_arm_joint_->angularStiffness =
              kLowerArmAngularStiffness * a_stiff_scale * lower_arm_a_scale;
          lower_right_arm_joint_->angularDamping =
              kLowerArmAngularDamping * a_damp_scale * lower_arm_a_scale;

          upper_left_arm_joint_->linearStiffness =
              kUpperArmLinearStiffness * l_still_scale;
          upper_left_arm_joint_->linearDamping =
              kUpperArmLinearDamping * l_damp_scale;
          upper_left_arm_joint_->angularStiffness =
              kUpperArmAngularStiffness * a_stiff_scale;
          upper_left_arm_joint_->angularDamping =
              kUpperArmAngularDamping * a_damp_scale;

          lower_left_arm_joint_->linearStiffness =
              kLowerArmLinearStiffness * l_still_scale;
          lower_left_arm_joint_->linearDamping =
              kLowerArmLinearDamping * l_damp_scale;
          lower_left_arm_joint_->angularStiffness =
              kLowerArmAngularStiffness * a_stiff_scale * lower_arm_a_scale;
          lower_left_arm_joint_->angularDamping =
              kLowerArmAngularDamping * a_damp_scale * lower_arm_a_scale;
        }

        // Adjust our shoulder position.
        {
          float x = -0.15f;
          float y = 0.14f;
          float z = 0.0f;
          float leftZOffset = 0.0f;
          float rightZOffset = 0.0f;
          x += shoulder_offset_x_;
          y += shoulder_offset_y_;
          z += shoulder_offset_z_;

          if (punch_) {
            if (punch_right_) {
              leftZOffset = -0.05f;
              rightZOffset = 0.05f;
            } else {
              leftZOffset = 0.05f;
              rightZOffset = -0.05f;
            }
          }

          // Breathing if we're not moving.
          if (!frozen_) y += breath * 0.012f;

          upper_right_arm_joint_->anchor1[0] = x;
          upper_right_arm_joint_->anchor1[1] = y;
          upper_right_arm_joint_->anchor1[2] = z + rightZOffset;

          upper_left_arm_joint_->anchor1[0] = -x;
          upper_left_arm_joint_->anchor1[1] = y;
          upper_left_arm_joint_->anchor1[2] = z + leftZOffset;
        }

        // Now update ik stuff.
        // If we're frozen, turn it all off.

        if (frozen_) {
          right_arm_ik_joint_->linearStiffness = 0;
          right_arm_ik_joint_->linearDamping = 0;
          right_arm_ik_joint_->angularStiffness = 0;
          right_arm_ik_joint_->angularDamping = 0;
          left_arm_ik_joint_->linearStiffness = 0;
          left_arm_ik_joint_->linearDamping = 0;
          left_arm_ik_joint_->angularStiffness = 0;
          left_arm_ik_joint_->angularDamping = 0;
        } else {
          bool haveHeldThing = false;
          if (holding_something_ && hold_node_.exists()) {
            Node* a = hold_node_.get();
            RigidBody* b = a->GetRigidBody(hold_body_);
            if (b) {
              haveHeldThing = true;

              right_arm_ik_joint_->linearStiffness = 40.0f;
              right_arm_ik_joint_->linearDamping = 1.0f;
              left_arm_ik_joint_->linearStiffness = 40.0f;
              left_arm_ik_joint_->linearDamping = 1.0f;
              JointFixedEF* jf;

              dBodyID heldBody = b->body();

              // Find our target point relative to the held body and aim for
              // that.
              dVector3 p_world;
              dVector3 p_torso2;

              jf = right_arm_ik_joint_;
              dBodyGetRelPointPos(heldBody, hold_hand_offset_right_[0],
                                  hold_hand_offset_right_[1],
                                  hold_hand_offset_right_[2], p_world);
              assert(body_torso_.exists());
              dBodyGetPosRelPoint(body_torso_->body(), p_world[0], p_world[1],
                                  p_world[2], p_torso2);
              jf->anchor1[0] = p_torso2[0];
              jf->anchor1[1] = p_torso2[1];
              jf->anchor1[2] = p_torso2[2];
              jf = left_arm_ik_joint_;
              dBodyGetRelPointPos(heldBody, hold_hand_offset_left_[0],
                                  hold_hand_offset_left_[1],
                                  hold_hand_offset_left_[2], p_world);
              assert(body_torso_.exists());
              dBodyGetPosRelPoint(body_torso_->body(), p_world[0], p_world[1],
                                  p_world[2], p_torso2);
              jf->anchor1[0] = p_torso2[0];
              jf->anchor1[1] = p_torso2[1];
              jf->anchor1[2] = p_torso2[2];
            }
          }

          // Not holding something.
          if (!haveHeldThing) {
            // Punching.
            if (since_last_punch < 300) {
              JointFixedEF* punch_hand;
              JointFixedEF* opposite_hand;

              JointFixedEF* shoulder_joint;

              float mirror_scale;

              if (punch_right_) {
                punch_hand = right_arm_ik_joint_;
                opposite_hand = left_arm_ik_joint_;
                shoulder_joint = upper_right_arm_joint_;
                mirror_scale = -1.0f;
              } else {
                punch_hand = left_arm_ik_joint_;
                opposite_hand = right_arm_ik_joint_;
                shoulder_joint = upper_left_arm_joint_;
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
                dBodyGetRelPointPos(body_torso_->body(),
                                    shoulder_joint->anchor1[0],
                                    shoulder_joint->anchor1[1],
                                    shoulder_joint->anchor1[2], p_world);

                // Offset now that we're in world-space.
                p_world[0] += punch_dir_x_ * 0.7f;
                p_world[2] += punch_dir_z_ * 0.7f;
                p_world[1] += 0.13f;

                // Now translate back to torso space for setting our anchor.
                assert(body_torso_.exists());
                dBodyGetPosRelPoint(body_torso_->body(), p_world[0], p_world[1],
                                    p_world[2], p_torso2);

                punch_hand->anchor1[0] = p_torso2[0];
                punch_hand->anchor1[1] = p_torso2[1];
                punch_hand->anchor1[2] = p_torso2[2];
              }
            } else if (have_thrown_ && scenetime - throw_start_ < 100
                       && scenetime >= throw_start_) {
              // Pick-up gesture.
              JointFixedEF* jf;
              jf = left_arm_ik_joint_;
              jf->anchor1[0] = 0.0f;
              jf->anchor1[1] = 0.2f;
              jf->anchor1[2] = 0.8f;
              left_arm_ik_joint_->linearStiffness = 10.0f;
              left_arm_ik_joint_->linearDamping = 0.1f;

              jf = right_arm_ik_joint_;
              jf->anchor1[0] = -0.0f;
              jf->anchor1[1] = 0.2f;
              jf->anchor1[2] = 0.8f;
              right_arm_ik_joint_->linearStiffness = 10.0f;
              right_arm_ik_joint_->linearDamping = 0.1f;
            } else if (!footing_ && balance_ == 0 && !dead_) {
              // Wave arms when airborn.
              float wave_amt = static_cast<float>(scenetime) * -0.018f;

              left_arm_ik_joint_->linearStiffness = 6.0f;
              left_arm_ik_joint_->linearDamping = 0.01f;
              right_arm_ik_joint_->linearStiffness = 6.0f;
              right_arm_ik_joint_->linearDamping = 0.01f;

              float v1 = sinf(wave_amt) * 0.34f;
              float v2 = cosf(wave_amt) * 0.34f;

              JointFixedEF* jf;
              jf = left_arm_ik_joint_;
              jf->anchor1[0] = 0.4f;
              jf->anchor1[1] = v1 + 0.6f;
              jf->anchor1[2] = v2 + 0.2f;

              jf = right_arm_ik_joint_;
              jf->anchor1[0] = -0.4f;
              jf->anchor1[1] = -v1 + 0.6f;
              jf->anchor1[2] = -v2 + 0.2f;
            } else {
              // Not airborn.

              // If we're looking to pick something up, wave our arms in front
              // of us.
              if (!knockout_ && pickup_ > 20) {
                JointFixedEF* jf;
                jf = left_arm_ik_joint_;
                jf->anchor1[0] = 0.4f;
                jf->anchor1[1] = 0.5f;
                jf->anchor1[2] = 0.7f;

                jf = right_arm_ik_joint_;
                jf->anchor1[0] = -0.4f;
                jf->anchor1[1] = 0.2f;
                jf->anchor1[2] = 0.7f;

                // Swipe across.
                if (pickup_ < 30) {
                  left_arm_ik_joint_->anchor1[0] = -0.1f;
                  right_arm_ik_joint_->anchor1[0] = 0.1f;
                }

                left_arm_ik_joint_->linearStiffness = 6.0f;
                left_arm_ik_joint_->linearDamping = 0.1f;
                right_arm_ik_joint_->linearStiffness = 6.0f;
                right_arm_ik_joint_->linearDamping = 0.1f;
              } else {
                // Cursed - wave arms.
                if (!knockout_ && curse_death_time_ != 0) {
                  left_arm_ik_joint_->linearStiffness = 30.0f;
                  left_arm_ik_joint_->linearDamping = 0.08f;

                  right_arm_ik_joint_->linearStiffness = 30.0f;
                  right_arm_ik_joint_->linearDamping = 0.08f;

                  float v1 =
                      sinf(static_cast<float>(scenetime) * 0.05f) * 0.12f;
                  float v2 =
                      cosf(static_cast<float>(scenetime) * 0.04f) * 0.12f;

                  JointFixedEF* jf;
                  jf = left_arm_ik_joint_;
                  jf->anchor1[0] = 0.4f + v2;
                  jf->anchor1[1] = 0.4f;
                  jf->anchor1[2] = 0.3f + v1;

                  jf = right_arm_ik_joint_;
                  jf->anchor1[0] = -0.4f - v2;
                  jf->anchor1[1] = 0.4f;
                  jf->anchor1[2] = 0.3f + v1;
                } else if (!knockout_
                           && (scenetime < celebrate_until_time_left_
                               || scenetime < celebrate_until_time_right_)) {
                  // Celebrating - hold arms in air.
                  float v1 = sinf(static_cast<float>(scenetime) * 0.04f) * 0.1f;
                  float v2 = cosf(static_cast<float>(scenetime) * 0.03f) * 0.1f;
                  JointFixedEF* jf;
                  if (scenetime < celebrate_until_time_left_) {
                    left_arm_ik_joint_->linearStiffness = 30.0f;
                    left_arm_ik_joint_->linearDamping = 0.08f;

                    jf = left_arm_ik_joint_;
                    jf->anchor1[0] = 0.4f + v2;
                    jf->anchor1[1] = 0.5f;
                    jf->anchor1[2] = 0.2f + v1;
                  }
                  if (scenetime < celebrate_until_time_right_) {
                    right_arm_ik_joint_->linearStiffness = 30.0f;
                    right_arm_ik_joint_->linearDamping = 0.08f;

                    jf = right_arm_ik_joint_;
                    jf->anchor1[0] = -0.4f - v2;
                    jf->anchor1[1] = 0.5f;
                    jf->anchor1[2] = 0.2f + v1;
                  }
                } else if (!knockout_ && !hold_position_pressed_
                           && (ud_ || lr_)) {
                  // Sway arms gently when walking, and vigorously
                  // when running.
                  float blend = run_gas_ * run_gas_;
                  float inv_blend = 1.0f - run_gas_;
                  float wave_amt = roll_amt_;

                  left_arm_ik_joint_->linearStiffness =
                      14.0f * blend + 0.5f * inv_blend;
                  left_arm_ik_joint_->linearDamping =
                      0.08f * blend + 0.001f * inv_blend;

                  right_arm_ik_joint_->linearStiffness =
                      14.0f * blend + 0.5f * inv_blend;
                  right_arm_ik_joint_->linearDamping =
                      0.08f * blend + 0.001f * inv_blend;

                  float v1run = sinf(wave_amt + 3.1415f * 0.5f) * 0.2f;
                  float v2run = cosf(wave_amt) * 0.3f;
                  float v1 = sinf(wave_amt) * 0.05f;
                  float v2 = cosf(wave_amt) * (female_ ? 0.3f : 0.6f);

                  JointFixedEF* jf;
                  jf = left_arm_ik_joint_;
                  jf->anchor1[0] = 0.2f;
                  jf->anchor1[1] =
                      (-v1run - 0.15f) * blend + (-v1 - 0.1f) * inv_blend;
                  jf->anchor1[2] =
                      (-v2run + 0.15f) * blend + (-v2 + 0.1f) * inv_blend;

                  jf = right_arm_ik_joint_;
                  jf->anchor1[0] = -0.2f;
                  jf->anchor1[1] =
                      (v1run - 0.15f) * blend + (v1 - 0.1f) * inv_blend;
                  jf->anchor1[2] =
                      (v2run + 0.15f) * blend + (v2 + 0.1f) * inv_blend;
                } else {
                  // Hang freely.
                  left_arm_ik_joint_->linearStiffness = 0.0f;
                  left_arm_ik_joint_->linearDamping = 0.0f;
                  right_arm_ik_joint_->linearStiffness = 0.0f;
                  right_arm_ik_joint_->linearDamping = 0.0f;
                }
              }
            }
          }
        }
      }

      if (holding_something_) {
        // look up to keep out of the way of our arms
        dQFromAxisAndAngle(neck_joint_->qrel, 1, 0, 0, 0.5f);
        head_back_ = true;
      } else {
        // if our head was back from holding something, whip it forward again..
        if (head_back_) {
          dQSetIdentity(neck_joint_->qrel);
          head_back_ = false;
        }

        // if we're cursed, whip it about
        if (curse_death_time_ != 0) {
          if (scene()->stepnum() % 5 == 0 && RandomFloat() > 0.2f) {
            head_turning = true;
            dQFromAxisAndAngle(neck_joint_->qrel, RandomFloat() * 0.05f,
                               RandomFloat(), RandomFloat() * 0.08f,
                               2.3f * (RandomFloat() - 0.5f));
          }
        } else {
          int64_t gti = scene()->stepnum();

          // if we're moving or hurt, keep our head straight
          if ((!hold_position_pressed_ && (ud_ || lr_)) || knockout_
              || frozen_) {
            dQSetIdentity(neck_joint_->qrel);

            // rotate it slightly in the direction we're turning
            dQFromAxisAndAngle(
                neck_joint_->qrel, 0, 1, 0,
                std::max(-1.0f,
                         std::min(1.0f, a_vel_y_smoothed_more_ * -0.14f)));
            // dQFromAxisAndAngle(neck_joint_->qrel,
            //                    0,1,0,
            //                    std::max(-0.5f,std::min(0.5f,a_vel_y_smoothed_more_*-0.07f)));
          } else if (gti % 30 == 0
                     && Utils::precalc_rand_1((gti + stream_id() * 3 + 143)
                                              % kPrecalcRandsCount)
                            > 0.9f) {
            // otherwise, look around occasionally..
            // else if (getScene()->stepnum()%30 == 0 and
            // RandomFloat() > 0.8f) { else if (gti%30 == 0 and
            // g_utils->precalc_rands_1[(gti+stream_id_*3+143)%kPrecalcRandsCount]
            // > 0.8f) {

            head_turning = true;
            dQFromAxisAndAngle(
                neck_joint_->qrel,
                Utils::precalc_rand_1((stream_id() + gti)
                                      % (kPrecalcRandsCount - 3))
                    * 0.05f,
                Utils::precalc_rand_2((stream_id() + 42 * gti)
                                      % kPrecalcRandsCount),
                Utils::precalc_rand_3((stream_id() + 3 * gti)
                                      % (kPrecalcRandsCount - 1))
                    * 0.05f,
                1.5f
                    * (Utils::precalc_rand_2((stream_id() + gti)
                                             % kPrecalcRandsCount)
                       - 0.5f));
            // dQFromAxisAndAngle(neck_joint_->qrel,
            //                    RandomFloat()*0.05f,
            //                    RandomFloat(),
            //                    RandomFloat()*0.05f,
            //                    1.5f*(RandomFloat()-0.5f));
          }
        }
      }
    }

    // if we're flying, keep us on a 2d plane
    if (can_fly_ && !dead_) {
      // lets just force our few main bodies on to the plane we want

      dBodyID b;
      const dReal *p, *v;

      b = body_torso_->body();
      p = dBodyGetPosition(b);
      dBodySetPosition(b, p[0], p[1], base::kHappyThoughtsZPlane);
      v = dBodyGetLinearVel(b);
      dBodySetLinearVel(b, v[0], v[1], 0.0f);

      b = body_pelvis_->body();
      p = dBodyGetPosition(b);
      dBodySetPosition(b, p[0], p[1], base::kHappyThoughtsZPlane);
      v = dBodyGetLinearVel(b);
      dBodySetLinearVel(b, v[0], v[1], 0.0f);

      b = body_head_->body();
      p = dBodyGetPosition(b);
      dBodySetPosition(b, p[0], p[1], base::kHappyThoughtsZPlane);
      v = dBodyGetLinearVel(b);
      dBodySetLinearVel(b, v[0], v[1], 0.0f);
    }
  }

  // flap wings every now and then
  if (wings_) {
    if (scene()->stepnum() % 21 == 0 && RandomFloat() > 0.9f) {
      flapping_ = true;
    }
    if (scene()->stepnum() % 20 == 0 && RandomFloat() > 0.7f) {
      flapping_ = false;
    }
  }

  // update eyes..
  if (!frozen_) {
    // Dart our eyes randomly (and always do it when we're turning our head.
    bool spinning = (std::abs(a_vel_y_smoothed_) > 10.0f);

    if (scene()->stepnum() % 20 == 0 || head_turning || spinning) {
      if (RandomFloat() > 0.7f || head_turning || spinning) {
        eyes_ud_ = 20.0f * (RandomFloat() - 0.5f);

        // bias our eyes in the direction we're turning part of the time..
        float spinBias = RandomFloat() > 0.5f ? a_vel_y_smoothed_ * 0.16f : 0;
        eyes_lr_ =
            70.0f
            * std::max(-0.4f,
                       std::min(0.4f, ((RandomFloat() - 0.5f) + spinBias)));
      }
    }
    if (scene()->stepnum() % 100 == 0 || head_turning) {
      if (RandomFloat() > 0.7f || head_turning) {
        eyelid_left_ud_ = 30.0f * (RandomFloat() - 0.5f);
        eyelid_right_ud_ = 30.0f * (RandomFloat() - 0.5f);
      }
    }
    // blink every now and then
    if (scene()->stepnum() % 20 == 0 && RandomFloat() > 0.92f) {
      blink_ = 2.0f;
    }

    if (spinning) {
      blink_ = 2.0f;
    }

    // shut our eyes if we're knocked out (unless we're flying thru the air)
    // if (knockout_ and footing_) blink_ = 2.0f;
    if (knockout_) {
      blink_ = 2.0f;
    }

    if (dead_) {
      blink_ = 2.0f;
    }

    blink_ = std::max(0.0f, blink_ - 0.14f);

    blink_smooth_ += 0.25f * (std::min(1.0f, blink_) - blink_smooth_);
    eyes_ud_smooth_ += 0.3f * (eyes_ud_ - eyes_ud_smooth_);
    eyes_lr_smooth_ += 0.3f * (eyes_lr_ - eyes_lr_smooth_);
    eyelid_left_ud_smooth_ += 0.1f * (eyelid_left_ud_ - eyelid_left_ud_smooth_);
    eyelid_right_ud_smooth_ +=
        0.1f * (eyelid_right_ud_ - eyelid_right_ud_smooth_);

    // eyelid tilt (angry look)
    {
      float smooth = 0.8f;
      float this_angle;
      if (running_fast || punch_) {
        this_angle = 25.0f;
      } else {
        this_angle = default_eye_lid_angle_;
      }
      eye_lid_angle_ = smooth * eye_lid_angle_ + (1.0f - smooth) * this_angle;
    }
  }

  // if we're dead, fall over
  if (dead_ && (knockout_ == 0)) {
    knockout_ = 1;
  }

  // so we dont get stuck up in the air if something under
  // us goes away
  if (footing_ == 0) {
    dBodyEnable(body_head_->body());
  }

  // Newer behavior-versions have 'dizzy' functionality (we get knocked out if
  // we spin too long)
  if (behavior_version_ > 0) {
    // Testing: lose balance while spinning fast.
    if (std::abs(a_vel_y_smoothed_more_) > 10.0f) {
      dizzy_ += 1;
      if (dizzy_ > 120) {
        dizzy_ = 0;
        knockout_ = 40;
        PlayHurtSound();
      }
    } else {
      dizzy_ = static_cast_check_fit<uint8_t>(
          std::max(0, static_cast<int>(dizzy_) - 2));
    }
  }

  if (knockout_ > 0 || frozen_) {
    balance_ = 0;
  } else {
    if (footing_) {
      if (balance_ < 100) {  // NOLINT(bugprone-branch-clone)
        balance_ += 20;
      } else if (balance_ < 235) {
        balance_ += 20;
      } else if (balance_ < 255) {
        balance_++;
      }
    } else {
      if (balance_ > 100) {
        balance_ -= 20;
      } else if (balance_ > 10) {
        balance_ -= 5;
      } else if (balance_ > 0) {
        balance_--;
      }
    }
  }

  // knockout wears off more slowly if we're airborn
  // (prevents landing on ones feet too much)
  if (knockout_ > 0 && (scene()->stepnum() % (footing_ ? 5 : 10) == 0)
      && !dead_) {
    knockout_--;
    if (knockout_ == 0) {
      dBodyEnable(body_head_->body());
    }
  }

  // if we're wanting to throw something...
  if (throwing_) {
    throwing_ = false;
    DropHeldObject();
  }

  // if we're flying, spin based on the direction we're holding
  if (can_fly_ && trying_to_fly_ && !footing_ && !frozen_ && !knockout_) {
    const dReal* av = dBodyGetAngularVel(body_torso_->body());

    float mag_scale = sqrtf(lr_smooth_ * lr_smooth_ + ud_smooth_ * ud_smooth_);
    float mag;
    if (mag_scale > 0.1f) {
      float a = AngleBetween2DVectors(lr_smooth_, ud_smooth_,
                                      (p_head[0] - p_torso[0]),
                                      (p_head[1] - p_torso[1]));
      if (a < 0) {
        mag = mag_scale * 20.0f;
      } else {
        mag = -mag_scale * 20.0f;
      }
      if (std::abs(a) < 0.8f) {
        mag *= std::abs(a) / 0.8f;
      }
    } else {
      mag = 0.0f;
    }

    mag += av[2] * -2.0f * mag_scale;  // brakes

    dBodyAddTorque(body_torso_->body(), 0, 0, mag);

    // also slow down a bit in flight
    dBodyID b;
    const dReal* v;

    // get a velocity difference based on our speed and sub that from everything
    // ...simpler than applying forces which might be uneven and spin us
    float sub = dBodyGetLinearVel(body_torso_->body())[0] * -0.02f;

    b = body_torso_->body();
    v = dBodyGetLinearVel(b);
    dBodySetLinearVel(b, v[0] + sub, v[1], v[2]);

    b = body_head_->body();
    v = dBodyGetLinearVel(b);
    dBodySetLinearVel(b, v[0] + sub, v[1], v[2]);

    b = body_pelvis_->body();
    v = dBodyGetLinearVel(b);
    dBodySetLinearVel(b, v[0] + sub, v[1], v[2]);

    b = body_roller_->body();
    v = dBodyGetLinearVel(b);
    dBodySetLinearVel(b, v[0] + sub, v[1], v[2]);
  }

  if (fly_power_ > 0.0001f && !knockout_) {
    const dReal* p_top = dBodyGetPosition(body_torso_->body());
    const dReal* p_bot = dBodyGetPosition(body_roller_->body());
    dBodyEnable(body_torso_->body());  // wake it up
    // float mag = 550*0.004f * fly_power_;
    // float up_mag = 150*0.004f * fly_power_;
    float mag = 550.0f * 0.005f * fly_power_;     // 120hz change
    float up_mag = 150.0f * 0.005f * fly_power_;  // 120hz change
    float fx = mag * (p_top[0] - p_bot[0]);
    float fy = mag * (p_top[1] - p_bot[1]);
    float head_scale = 0.5f;
    dBodyAddForce(body_head_->body(), head_scale * fx, head_scale * fy, 0);
    dBodyAddForce(body_head_->body(), 0, head_scale * up_mag, 0);
    dBodyAddForce(body_torso_->body(), fx, fy, 0);
    dBodyAddForce(body_torso_->body(), 0, up_mag, 0);

    // also add some force to what we're holding so popping out a bomb doesnt
    // send us spiraling down to death
    if (holding_something_) {
      Node* a = hold_node_.get();
      if (a) {
        float scale = 0.2f;
        RigidBody* b = a->GetRigidBody(hold_body_);
        if (b) {
          dBodyAddForce(b->body(), fx * scale, fy * scale, 0);
          dBodyAddForce(b->body(), 0, up_mag * scale, 0);
        }
      }
    }
  }

  // torso
  {
    dBodyID b = stand_body_->body();
    const dReal* p_torso2 = dBodyGetPosition(body_torso_->body());
    const dReal* p_bot = dBodyGetPosition(body_roller_->body());
    const dReal* lv = dBodyGetLinearVel(body_torso_->body());

    dBodySetLinearVel(b, lv[0], lv[1], lv[2]);
    dBodySetAngularVel(b, 0, 0, 0);

    // Update the orientation of our stand body.
    // If we're pressing the joystick, that's the direction we use.
    // The moment we stop, though, we instead use the direction our torso is
    // pointing. (we dont wanna keep turning once we let off the joystick) The
    // only alternative is to turn off angular stiffness on the constraint but
    // then we spin and stuff.

    // Also let's calculate tilt.  For this we guesstimate how fast we wanna be
    // going given our UD/LR values and we tilt forward or back depending on
    // where we are relative to that.
    float tilt_lr, tilt_ud;
    dBodySetPosition(b, p_torso2[0], p_bot[1] + 0.2f, p_torso2[2]);

    float rotate_tilt = 0.4f;

    if (hockey_) {
      const dReal* b_vel_3 = dBodyGetLinearVel(body_roller_->body());
      float v_mag = std::max(5.0f, Vector3f(b_vel_3).Length());
      float accel_smoothing = 0.9f;
      for (int i = 0; i < 3; i++) {
        float avg_vel = (b_vel_3[i]);
        accel_[i] = accel_smoothing * accel_[i]
                    + (1.0f - accel_smoothing) * (avg_vel - prev_vel_[i]);
        prev_vel_[i] = avg_vel;
      }
      tilt_lr = std::min(1.0f, std::max(-1.0f, v_mag * accel_[0] * 1.4f));
      tilt_ud = std::min(1.0f, std::max(-1.0f, v_mag * accel_[2] * -1.4f));
    } else {
      // non-hockey

      const dReal* b_vel_3 = dBodyGetLinearVel(body_roller_->body());
      float v_mag = std::max(7.0f, Vector3f(b_vel_3).Length());
      float accel_smoothing = 0.7f;
      for (int i = 0; i < 3; i++) {
        float avg_vel = (b_vel_3[i]);
        accel_[i] = accel_smoothing * accel_[i]
                    + (1.0f - accel_smoothing) * (avg_vel - prev_vel_[i]);
        prev_vel_[i] = avg_vel;
      }
      tilt_lr = (0.2f + 0.8f * run_gas_)
                * std::min(0.9f, std::max(-0.9f, v_mag * accel_[0] * 0.3f));
      tilt_ud = (0.2f + 0.8f * run_gas_)
                * std::min(0.9f, std::max(-0.9f, v_mag * accel_[2] * -0.3f));

      float fast = std::min(1.0f, speed_smoothed_ / 5.0f);

      // A sharper tilt at low speeds (so we dont whiplash when walking).
      tilt_lr += (1.0f - fast) * (lr_diff_smooth_ * 10.0f);
      tilt_ud += (1.0f - fast) * (ud_diff_smooth_ * 10.0f);

      tilt_lr += fast * (lr_diff_smoother_ * 30.0f);
      tilt_ud += fast * (ud_diff_smoother_ * 30.0f);

      rotate_tilt *= 1.2f;
    }
    if (holding_something_) {
      rotate_tilt *= 0.5f;
    }

    // Lean less if we're spinning. Otherwise we go jumping all crazy to the
    // side.
    const dReal spin = std::abs(dBodyGetAngularVel(body_torso_->body())[1]);
    if (spin > 10.0f) {
      rotate_tilt = 0.0f;
    }

    float this_punch_dir_x{};
    float this_punch_dir_z{};

    // If we're moving, we orient our stand-body to that exact direction.
    if (lr_ || ud_) {
      // If we're holding position we can't use lr_norm_/ud_norm_ here because
      // they'll be zero (or close).  So in that case just calc a normalized
      // lr_/_ud here.

      float this_ud_norm, this_lr_norm;
      if (hold_position_pressed_) {
        this_ud_norm = (static_cast<float>(ud_) / 127.0f);
        this_lr_norm = (static_cast<float>(lr_) / 127.0f);
        if (clamp_move_values_to_circle_) {
          BoxClampToCircle(&this_lr_norm, &this_ud_norm);
        } else {
          BoxNormalizeToCircle(&this_lr_norm, &this_ud_norm);
        }
      } else {
        this_ud_norm = ud_norm_;
        this_lr_norm = lr_norm_;
      }
      dMatrix3 r;
      RotationFrom2Axes(r, -this_ud_norm, 0, -this_lr_norm,
                        rotate_tilt * tilt_lr, 1, -rotate_tilt * tilt_ud);
      dBodySetRotation(b, r);

      // Also update our punch direction.
      this_punch_dir_x = this_lr_norm;
      this_punch_dir_z = -this_ud_norm;
    } else {
      // We're not moving; orient our stand body to match our torso.
      dMatrix3 r;
      dVector3 p_forward;
      dBodyGetRelPointPos(body_torso_->body(), 1, 0, 0, p_forward);

      // Doing this repeatedly winds up turning us slowly in circles
      // ..so lets recycle previous values if we haven't changed much.
      float orientX = p_forward[0] - p_torso2[0];
      float orientZ = p_forward[2] - p_torso2[2];
      if (std::abs(orientX - last_stand_body_orient_x_) > 0.05f
          || std::abs(orientZ - last_stand_body_orient_z_) > 0.05f) {
        last_stand_body_orient_x_ = orientX;
        last_stand_body_orient_z_ = orientZ;
      }

      RotationFrom2Axes(r, last_stand_body_orient_x_, 0,
                        last_stand_body_orient_z_, rotate_tilt * tilt_lr, 1,
                        -rotate_tilt * tilt_ud);

      dBodySetRotation(b, r);

      this_punch_dir_z = (p_forward[0] - p_torso2[0]);
      this_punch_dir_x = -(p_forward[2] - p_torso2[2]);
    }

    // Update and re-normalize punch dir.
    {
      float blend = 0.5f;
      punch_dir_x_ = (1.0f - blend) * this_punch_dir_x + blend * punch_dir_x_;
      punch_dir_z_ = (1.0f - blend) * this_punch_dir_z + blend * punch_dir_z_;

      float len =
          sqrtf(punch_dir_x_ * punch_dir_x_ + punch_dir_z_ * punch_dir_z_);
      float mult = len == 0.0f ? 9999 : 1.0f / len;
      punch_dir_x_ *= mult;
      punch_dir_z_ *= mult;
    }

    // Rotate our attach-point to give some sway while running.
    {
      float angle =
          sinf(roll_amt_ - 3.141592f)
          * (run_gas_ * 0.09f + (1.0f - run_gas_) * (female_ ? 0.02f : 0.05f));
      dQFromAxisAndAngle(stand_joint_->qrel, 0, 1, 1, angle);
    }

    {
      float bal = static_cast<float>(balance_) / 255.0f;

      bal = 1.0f
            - ((1.0f - bal) * (1.0f - bal) * (1.0f - bal)
               * (1.0f - bal));  // push it towards 1
      float mult = bal;

      // Crank up our balance when we're holding something otherwise we get a
      // bit soupy.
      if (holding_something_) {
        mult *= 0.9f;
      } else {
        mult *= 0.6f;
      }

      {
        stand_joint_->linearStiffness = 0.0f;
        stand_joint_->linearDamping = 0.0f;
        stand_joint_->angularStiffness = 180.0f * mult;
        stand_joint_->angularDamping = 3.0f * mult;
      }

      // Crank down angular forces at low speeds to keep from looking too stiff.
      {
        dVector3 f = {ud_norm_, 0, lr_norm_};
        float m = dVector3Length(f);
        float blend_max = 1.0f;
        if (m < blend_max) {
          stand_joint_->angularDamping *= 0.3f + 0.7f * (m / blend_max);
          stand_joint_->angularStiffness *= 0.6f + 0.4f * (m / blend_max);
        }
      }
    }
  }

  // Resize our run-ball based on our balance.
  // (so when we're laying on the ground its not propping our legs up in the
  // air)
  {
    if (knockout_ || frozen_)
      ball_size_ = 0.0f;
    else
      ball_size_ = std::min(1.0f, ball_size_ + 0.05f);

    float sz = 0.1f + 0.9f * ball_size_;
    body_roller_->SetDimensions(
        0.3f * sz, 0, 0, 0.3f, 0,
        0,  // keep its mass the same as its full-size self though
        0.1f);
  }

  // Push our roller-ball down for jumps and retract it when we're hurt.
  {
    // Retract it up as well so when it pops back up it doesnt start
    // underground.
    float offs = (1.0f - ball_size_) * 0.3f;
    float ls_scale = 1.0f;
    float ld_scale = 1.0f;
    if (jump_ > 0 && !frozen_ && !knockout_) {
      offs -= 0.3f;
      ls_scale = 0.6f;
      ld_scale = 0.2f;
    }
    roller_ball_joint_->linearStiffness = kRollerBallLinearStiffness * ls_scale;
    roller_ball_joint_->linearDamping = kRollerBallLinearDamping * ld_scale;
    offs -= breath * 0.02f;
    roller_ball_joint_->anchor1[1] = base_pelvis_roller_anchor_offset_ + offs;
  }

  // Roll our run-ball (new).
  {
    {
      float mult;
      if (frozen_ || hold_position_pressed_) {
        mult = 0.0f;
      } else {
        mult = std::min(1.0f, static_cast<float>(balance_) / 100.0f);
      }

      // hockey..
      if (hockey_) {
        dBodyEnable(body_roller_->body());
        dJointSetAMotorParam(a_motor_roller_, dParamFMax, 30.0f * mult);
        dJointSetAMotorParam(a_motor_roller_, dParamFMax2, 10.0f * mult);
        dJointSetAMotorParam(a_motor_roller_, dParamFMax3, 30.0f * mult);
        dJointSetAMotorParam(a_motor_roller_, dParamVel,
                             -0.17f * 128.0f * ud_norm_);
        dJointSetAMotorParam(a_motor_roller_, dParamVel2, 0.0f);
        dJointSetAMotorParam(a_motor_roller_, dParamVel3,
                             -0.17f * 128.0f * lr_norm_);
      } else {
        const dReal* vel = dBodyGetLinearVel(body_roller_->body());
        dVector3 v = {vel[0], vel[1], vel[2]};

        // Old settings to keep the demo working.
        if (demo_mode_) {
          // We want to speed up faster going downhill and slower going uphill
          // (getting the base physics to do that leaves us with a
          // hard-to-control character)
          // So we fake it by skewing our smoothed speed faster on downhill
          // and slower uphill.
          float speed_scale = 1.0f;
          float walk_scale;

          // Heading downhill: speed up.
          if (v[1] < 0.0f) {
            v[1] *= 2.0f;  // just scale our downward component up to bias the
                           // speed calc
            walk_scale = 1.0f - v[1] * 0.1f;
          } else {
            // Heading uphill: slow down.
            speed_scale = std::max(0.0f, 1.0f - v[1] * 0.2f);
            walk_scale = std::max(0.0f, 1.0f - v[1] * 0.2f);
            v[1] = 0.0f;
          }

          // Our smoothed spead increases slowly and decreases fast.
          float speed = dVector3Length(v) * speed_scale;
          float speed_smoothing = (speed > speed_smoothed_) ? 0.985f : 0.7f;
          speed_smoothed_ = speed_smoothing * speed_smoothed_
                            + (1.0f - speed_smoothing) * speed;

          float gear_high = std::min(1.0f, speed_smoothed_ / 7.0f);
          float gear_low = 1.0f - gear_high;

          // As we 'shift up' in gears our max-force goes up and target velocity
          // goes down.
          float max_force = gear_low * 15.0f + gear_high * 15.0f;
          float max_vel = walk_scale * 7.68f + gear_high * run_gas_ * 15.0f;
          dBodyEnable(body_roller_->body());
          dJointSetAMotorParam(a_motor_roller_, dParamFMax,
                               max_force * mult);  // change for 120hz
          dJointSetAMotorParam(a_motor_roller_, dParamFMax2,
                               500.0f * mult);  // 120hz change
          dJointSetAMotorParam(a_motor_roller_, dParamFMax3,
                               max_force * mult);  // change for 120hz
          dJointSetAMotorParam(a_motor_roller_, dParamVel, -max_vel * ud_norm_);
          dJointSetAMotorParam(a_motor_roller_, dParamVel2, 0.0f);
          dJointSetAMotorParam(a_motor_roller_, dParamVel3,
                               -max_vel * lr_norm_);
        } else {
          // We want to speed up faster going downhill and slower going uphill
          // (getting the base physics to do that leaves us with a
          // hard-to-control character)
          // ...so we fake it by skewing our smoothed speed faster on downhill
          // and slower uphill
          float speed_scale = 1.0f;
          float walk_scale =
              1.0f;  // if we're just walking, how fast we'll go..
          // heading downhill - speed up
          if (footing_) {
            if (v[1] < 0.0f) {
              v[1] *= 2.0f;  // just scale our downward component up to bias the
                             // speed calc
              walk_scale = 1.0f - v[1] * 0.1f;
            } else {
              // heading uphill - slow down
              speed_scale = std::max(0.0f, 1.0f - v[1] * 0.2f);
              walk_scale = std::max(0.0f, 1.0f - v[1] * 0.2f);
              v[1] = 0.0f;  // also don't count upward velocity towards our
                            // speed calc..
            }
          }

          // our smoothed spead increases slowly and decreases fast
          float speed = dVector3Length(v) * speed_scale;
          float speed_smoothing = (speed > speed_smoothed_) ? 0.985f : 0.94f;
          speed_smoothed_ = speed_smoothing * speed_smoothed_
                            + (1.0f - speed_smoothing) * speed;

          float gear_high = std::min(1.0f, speed_smoothed_ / 7.0f);
          float gear_low = 1.0f - gear_high;

          // as we 'shift up' in gears our max-force goes up and target velocity
          // goes down
          float max_force = gear_low * 15.0f + gear_high * 15.0f;
          float max_vel = walk_scale * 7.68f + gear_high * run_gas_ * 15.0f;
          dBodyEnable(body_roller_->body());
          dJointSetAMotorParam(a_motor_roller_, dParamFMax,
                               max_force * mult);  // change for 120hz
          dJointSetAMotorParam(a_motor_roller_, dParamFMax2,
                               500.0f * mult);  // 120hz change
          dJointSetAMotorParam(a_motor_roller_, dParamFMax3,
                               max_force * mult);  // change for 120hz
          dJointSetAMotorParam(a_motor_roller_, dParamVel, -max_vel * ud_norm_);
          dJointSetAMotorParam(a_motor_roller_, dParamVel2, 0.0f);
          dJointSetAMotorParam(a_motor_roller_, dParamVel3,
                               -max_vel * lr_norm_);
        }
      }
    }
  }

  // Set brake motor strength.
  if (footing_ || frozen_ || dead_) {
    float amt;
    // Full brakes if frozen. Otherwise crank up as our joystick magnitude goes
    // down.
    if (frozen_ || dead_) {
      amt = 1.0f;
    } else {
      dVector3 f = {lr_norm_, 0, ud_norm_};
      amt = std::min(1.0f, dVector3Length(f) * 5.0f);
      amt = 1.0f - (amt * amt * amt);
      amt *= (1.0f - run_gas_);
      amt *= 0.4f;
    }
    dJointSetAMotorParam(a_motor_brakes_, dParamFMax, 10.0f * amt);
    dJointSetAMotorParam(a_motor_brakes_, dParamFMax2, 10.0f * amt);
    dJointSetAMotorParam(a_motor_brakes_, dParamFMax3, 10.0f * amt);
    dJointSetAMotorParam(a_motor_brakes_, dParamVel, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamVel2, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamVel3, 0.0f);
  } else {
    // if we're not on the ground we wanna just keep doing what we're doing
    dJointSetAMotorParam(a_motor_brakes_, dParamFMax, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamFMax2, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamFMax3, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamVel, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamVel2, 0.0f);
    dJointSetAMotorParam(a_motor_brakes_, dParamVel3, 0.0f);
  }

  // If we're knocked out, stop any mid-progress punch.
  if (knockout_) {
    punch_ = 0;
  }

  if (punch_ > 0) {
    if (!body_punch_.exists() && since_last_punch > 80 && !knockout_) {
      body_punch_ = Object::New<RigidBody>(
          kPunchBodyID, &punch_part_, RigidBody::Type::kGeomOnly,
          RigidBody::Shape::kSphere, RigidBody::kCollideRegion,
          RigidBody::kCollideAll);
      body_punch_->SetDimensions(0.25f);
    }

    if (body_punch_.exists()) {
      // Move the punch body to the end of our punching arm.
      dBodyID fist_body = punch_right_ ? lower_right_arm_body_->body()
                                       : lower_left_arm_body_->body();
      dVector3 p;
      dBodyGetRelPointPos(fist_body, 0, 0, 0.01f, p);

      // Move it down a tiny bit since we're often trying to punch dudes laying
      // on the ground.
      p[1] -= 0.1f;

      dGeomSetPosition(body_punch_->geom(), p[0], p[1], p[2]);
    }

  } else {
    if (body_punch_.exists()) {
      body_punch_.Clear();
    }
  }

  // If we're flying through the air really fast (preferably not on purpose),
  // scream.
  const dReal* p_head_vel = dBodyGetLinearVel(body_head_->body());
  float vel_mag_squared = p_head_vel[0] * p_head_vel[0]
                          + p_head_vel[1] * p_head_vel[1]
                          + p_head_vel[2] * p_head_vel[2];

  float scream_speed = can_fly_ ? 160.0f : 100.0f;
  if ((force_scream_ && scene()->time() - last_force_scream_time_ < 3000)
      || (scene()->time() - last_fly_time_ > 1000
          && vel_mag_squared > scream_speed && !footing_
          && std::abs(p_head_vel[1]) > 0.3f && !dead_)) {
    if (scene()->time() - last_fall_time_ > 1000) {
      // If we're not still screaming, start one up.
      if (!(voice_play_id_ == fall_play_id_
            && g_base->audio->IsSoundPlaying(fall_play_id_))) {
        if (SceneSound* sound = GetRandomMedia(fall_sounds_)) {
          if (auto* source = g_base->audio->SourceBeginNew()) {
            g_base->audio->PushSourceStopSoundCall(voice_play_id_);
            source->SetPosition(p_head[0], p_head[1], p_head[2]);
            voice_play_id_ = source->Play(sound->GetSoundData());
            fall_play_id_ = voice_play_id_;
            source->End();
          }
        }
      }
      last_fall_time_ = scene()->time();
    }
  }

  // If theres a scream going on, update its position and stop it if we've
  // slowed down alot.
  if (voice_play_id_ == fall_play_id_) {
    if ((footing_ && !force_scream_)
        || (force_scream_
            && scene()->time() - last_force_scream_time_ > 2000)) {
      g_base->audio->PushSourceStopSoundCall(voice_play_id_);
      voice_play_id_ = 0xFFFFFFFF;
    } else {
      auto* s = g_base->audio->SourceBeginExisting(fall_play_id_, 108);
      if (s) {
        s->SetPosition(p_head[0], p_head[1], p_head[2]);
        s->End();
      }
    }
  }

  // Update ticking.
  if (tick_play_id_ != 0xFFFFFFFF) {
    auto* s = g_base->audio->SourceBeginExisting(tick_play_id_, 109);
    if (s) {
      s->SetPosition(p_head[0], p_head[1], p_head[2]);
      s->End();
    }
  }

  // If we're in the process of throwing something
  // ( we need to check have_thrown_ because otherwise we'll always think
  //   we're throwing at game-time 0 since throw_start_ inits to that.)
  if (have_thrown_ && scene()->time() - throw_start_ < 50) {
    Node* a = hold_node_.get();
    if (a) {
      RigidBody* b = a->GetRigidBody(hold_body_);
      if (b) {
        dVector3 f;
        float power;
        if (throw_power_ < 0.1f) {
          power = -0.2f - 1 * (0.1f - throw_power_);
        } else {
          power = (throw_power_ - 0.1f) * 1.0f;
        }

        power *= 1.15f;  // change for 120hz
        dBodyVectorToWorld(body_torso_->body(), 0, 60, 60, f);

        // If we're pressing a direction, factor that in.
        float lrf = throw_lr_;
        float udf = throw_ud_;
        if (clamp_move_values_to_circle_) {
          BoxClampToCircle(&lrf, &udf);
        } else {
          BoxNormalizeToCircle(&lrf, &udf);
        }

        // Blend based on magnitude of our locked in throw speed.
        float d_len = sqrtf(lrf * lrf + udf * udf);
        if (d_len > 0.0f) {
          // Let's normalize our locked in throw direction.
          // 'throwPower' should be our sole magnitude determinant.
          float dist = sqrtf(throw_lr_ * throw_lr_ + throw_ud_ * throw_ud_);
          float s = 1.0f / dist;
          lrf *= s;
          udf *= s;

          float f2[3];
          f2[0] = lrf * 50.0f;
          f2[1] = 80.0f;
          f2[2] = -udf * 50.0f;
          if (d_len > 0.1f) {
            f[0] = f2[0];
            f[1] = f2[1];
            f[2] = f2[2];
          } else {
            float blend = d_len / 0.1f;
            f[0] = blend * f2[0] + (1.0f - blend) * f[0];
            f[1] = blend * f2[1] + (1.0f - blend) * f[1];
            f[2] = blend * f2[2] + (1.0f - blend) * f[2];
          }
        }

        dBodyEnable(body_torso_->body());  // wake it up
        dBodyEnable(b->body());            // wake it up
        const dReal* p = dBodyGetPosition(b->body());

        float kick_back = -0.25f;

        // Pro trick: if we throw while still holding bomb down, we throw
        // backwards lightly.
        if (bomb_pressed_ && !throwing_with_bomb_button_) {
          float neg = -0.2f;
          dBodyAddForceAtPos(b->body(), neg * power * f[0],
                             std::abs(neg * power * f[1]), neg * power * f[2],
                             p[0], p[1] - 0.1f, p[2]);
          dBodyAddForceAtPos(body_torso_->body(), -neg * power * f[0],
                             std::abs(-neg * power * f[1]), -neg * power * f[2],
                             p[0], p[1] - 0.1f, p[2]);
        } else {
          dBodyAddForceAtPos(b->body(), power * f[0], std::abs(power * f[1]),
                             power * f[2], p[0], p[1] - 0.1f, p[2]);
          dBodyAddForceAtPos(body_torso_->body(), kick_back * power * f[0],
                             kick_back * (std::abs(power * f[1])),
                             kick_back * power * f[2], p[0], p[1] - 0.1f, p[2]);
        }
      }
    }
  } else {
    // If we're no longer holding something and our throw is over, clear any ref
    // we might have.
    if (!holding_something_ && hold_node_.exists()) hold_node_.Clear();
  }

  if (pickup_ == kPickupCooldown - 4) {
    if (!body_pickup_.exists()) {
      body_pickup_ = Object::New<RigidBody>(
          kPickupBodyID, &pickup_part_, RigidBody::Type::kGeomOnly,
          RigidBody::Shape::kSphere, RigidBody::kCollideRegion,
          RigidBody::kCollideActive);
      body_pickup_->SetDimensions(0.7f);
    }
  } else {
    if (body_pickup_.exists()) {
      body_pickup_.Clear();
    }
  }

  if (body_pickup_.exists()) {
    // A unit vector forward.
    dVector3 f;
    float z = 0.3f;
    dBodyVectorToWorld(body_head_->body(), 0, 0, 1, f);
    dGeomSetPosition(body_pickup_->geom(),
                     0.5f * (p_head[0] + p_torso[0]) + z * f[0],
                     0.5f * (p_head[1] + p_torso[1]) + z * f[1],
                     0.5f * (p_head[2] + p_torso[2]) + z * f[2]);
  }

  // If we're holding something and it died, tell userland.
  if (holding_something_) {
    if (!pickup_joint_.IsAlive()) {
      holding_something_ = false;
      DispatchDropMessage();
    }
  }

  if (flashing_ > 0) {
    flashing_--;
  }

  if (jump_ > 0) {
    // *always* reduce jump even if we're holding it.
    jump_ -= 1;
    // jump_ = std::max(0, static_cast<int>(jump_) - 1);
    // enforce a 'minimum-held-time' so that an instant press/release still
    // results in a measurable jump (we tend to get these from remotes/etc)
    // cout << "DIFF " << getScene().time()-last_jump_time_ << endl;
    // if (!jump_pressed_ and (getScene().time()-last_jump_time_ >
    // 1000)) jump_ = 0.0f;
  }

  // Emit fairy dust if we're flying.
#if !BA_HEADLESS_BUILD
  if (fly_power_ > 20.0f && scene()->stepnum() % 3 == 1) {
    for (int i = 0; i < 1; i++) {
      base::BGDynamicsEmission e;
      e.emit_type = base::BGDynamicsEmitType::kFairyDust;
      e.position = Vector3f(dGeomGetPosition(body_torso_->geom()));
      e.velocity = Vector3f(dBodyGetLinearVel(body_torso_->body()));
      e.count = 1;
      e.scale = 1.0f;
      e.spread = 1.0f;
      g_base->bg_dynamics->Emit(e);
    }
  }
#endif  // !BA_HEADLESS_BUILD

  fly_power_ *= 0.95f;

  if (punch_ > 0) {
    punch_--;
  }
  if (pickup_ > 0) {
    pickup_--;
  }

  UpdateAreaOfInterest();

  // Update our recent-damage tally.
  damage_smoothed_ *= 0.8f;

  // If we're out of bounds, arrange to have ourself informed.
  if (!dead_) {
    const dReal* p = dBodyGetPosition(body_head_->body());
    if (scene()->IsOutOfBounds(p[0], p[1], p[2])) {
      scene()->AddOutOfBoundsNode(this);
      last_out_of_bounds_time_ = scene()->time();
    }
  }
  BA_DEBUG_CHECK_BODIES();
}  // NOLINT (yeah i know, this is too long)

#if !BA_HEADLESS_BUILD
static void DrawShadow(const base::BGDynamicsShadow& shadow, float radius,
                       float density, const float* shadow_color) {
  float s_scale, s_density;
  shadow.GetValues(&s_scale, &s_density);
  float d = s_density * density;
  g_base->graphics->DrawBlotch(shadow.GetPosition(), radius * s_scale * 4.0f,
                               (0.08f + 0.04f * shadow_color[0]) * d,
                               (0.07f + 0.04f * shadow_color[1]) * d,
                               (0.065f + 0.04f * shadow_color[2]) * d,
                               0.32f * d);
}
static void DrawBrightSpot(const base::BGDynamicsShadow& shadow, float radius,
                           float density, const float* shadow_color) {
  float s_scale, s_density;
  shadow.GetValues(&s_scale, &s_density);
  float d = s_density * density * 0.3f;
  g_base->graphics->DrawBlotch(shadow.GetPosition(), radius * s_scale * 4.0f,
                               shadow_color[0] * d, shadow_color[1] * d,
                               shadow_color[2] * d, 0.0f);
}
#endif  // !BA_HEADLESS_BUILD

void SpazNode::DrawEyeBalls(base::RenderComponent* c, base::ObjectComponent* oc,
                            bool shading, float death_fade, float death_scale,
                            float* add_color) {
  // Eyeballs.
  if (blink_smooth_ < 0.9f) {
    if (shading) {
      oc->SetLightShadow(base::LightShadowType::kObject);
      oc->SetTexture(g_base->assets->SysTexture(base::SysTextureID::kEye));
      oc->SetColorizeColor(eye_color_red_, eye_color_green_, eye_color_blue_);
      oc->SetColorizeTexture(
          g_base->assets->SysTexture(base::SysTextureID::kEyeTint));
      oc->SetReflection(base::ReflectionType::kSharpest);
      oc->SetReflectionScale(3, 3, 3);
      oc->SetAddColor(add_color[0], add_color[1], add_color[2]);
      oc->SetColor(eye_ball_color_red_, eye_ball_color_green_,
                   eye_ball_color_blue_);
    }
    {
      auto xf = c->ScopedTransform();

      body_head_->ApplyToRenderComponent(c);
      if (eye_scale_ != 1.0f) {
        c->Scale(eye_scale_, eye_scale_, eye_scale_);
      }
      {
        auto xf = c->ScopedTransform();
        c->Translate(eye_offset_x_, eye_offset_y_, eye_offset_z_);
        c->Rotate(-10 + eyes_ud_smooth_, 1, 0, 0);
        c->Rotate(eyes_lr_smooth_, 0, 1, 0);
        c->Scale(0.09f, 0.09f, 0.09f);
        if (death_scale != 1.0f) {
          c->Scale(death_scale, death_scale, death_scale);
        }
        if (!frosty_ && !eyeless_) {
          c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kEyeBall));
          if (shading) {
            oc->SetReflectionScale(2, 2, 2);
          }
          if (death_scale != 1.0f)
            c->Scale(death_scale, death_scale, death_scale);
          c->DrawMeshAsset(
              g_base->assets->SysMesh(base::SysMeshID::kEyeBallIris));
        }
      }

      if (!pirate_ && !frosty_ && !eyeless_) {
        if (shading) {
          oc->SetReflectionScale(3, 3, 3);
        }
        {
          auto xf = c->ScopedTransform();
          c->Translate(-eye_offset_x_, eye_offset_y_, eye_offset_z_);
          c->Rotate(-10 + eyes_ud_smooth_, 1, 0, 0);
          c->Rotate(eyes_lr_smooth_, 0, 1, 0);
          c->Scale(0.09f, 0.09f, 0.09f);
          if (death_scale != 1.0f) {
            c->Scale(death_scale, death_scale, death_scale);
          }
          c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kEyeBall));
          if (death_scale != 1.0f) {
            c->Scale(death_scale, death_scale, death_scale);
          }
          if (shading) {
            oc->SetReflectionScale(2, 2, 2);
          }
          c->DrawMeshAsset(
              g_base->assets->SysMesh(base::SysMeshID::kEyeBallIris));
        }
      }
    }
  }
}

void SpazNode::SetupEyeLidShading(base::ObjectComponent* c, float death_fade,
                                  float* add_color) {
  c->SetTexture(g_base->assets->SysTexture(base::SysTextureID::kEye));
  c->SetColorizeTexture(nullptr);
  float r, g, b;
  r = eye_lid_color_red_;
  g = eye_lid_color_green_;
  b = eye_lid_color_blue_;

  // Fade to reddish.
  if (dead_ && !frozen_) {
    r *= 0.3f + 0.7f * death_fade;
    g *= 0.2f + 0.7f * (death_fade * 0.5f);
    b *= 0.2f + 0.7f * (death_fade * 0.5f);
  }
  c->SetColor(r, g, b);
  c->SetAddColor(add_color[0], add_color[1], add_color[2]);
  c->SetReflection(base::ReflectionType::kChar);
  c->SetReflectionScale(0.05f, 0.05f, 0.05f);
}

void SpazNode::DrawEyeLids(base::RenderComponent* c, float death_fade,
                           float death_scale) {
  if (!has_eyelids_ && blink_smooth_ < 0.1f) {
    return;
  }

  {
    auto xf = c->ScopedTransform();

    body_head_->ApplyToRenderComponent(c);
    if (eye_scale_ != 1.0f) {
      c->Scale(eye_scale_, eye_scale_, eye_scale_);
    }
    c->Translate(eye_offset_x_, eye_offset_y_, eye_offset_z_);

    float a = eyelid_left_ud_smooth_ + 0.5f * eyes_ud_smooth_;
    if (blink_smooth_ > 0.001f) {
      a = blink_smooth_ * 90.0f + (1.0f - blink_smooth_) * a;
    }
    c->Rotate(eye_lid_angle_, 0, 0, 1);
    c->Rotate(a, 1, 0, 0);
    c->Scale(0.09f, 0.09f, 0.09f);

    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }

    if (!frosty_ && !eyeless_) {
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kEyeLid));
    }
  }

  // Left eyelid.
  c->FlipCullFace();
  {
    auto xf = c->ScopedTransform();

    body_head_->ApplyToRenderComponent(c);
    if (eye_scale_ != 1.0f) {
      c->Scale(eye_scale_, eye_scale_, eye_scale_);
    }
    c->Translate(-eye_offset_x_, eye_offset_y_, eye_offset_z_);
    float a = eyelid_right_ud_smooth_ + 0.5f * eyes_ud_smooth_;
    if (blink_smooth_ > 0.001f) {
      a = blink_smooth_ * 90.0f + (1.0f - blink_smooth_) * a;
    }
    c->Rotate(-eye_lid_angle_, 0, 0, 1);
    c->Rotate(a, 1, 0, 0);
    c->Scale(-0.09f, 0.09f, 0.09f);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (!pirate_ && !frosty_ && !eyeless_) {
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kEyeLid));
    }
  }
  c->FlipCullFace();  // back to normal
}

void SpazNode::DrawBodyParts(base::ObjectComponent* c, bool shading,
                             float death_fade, float death_scale,
                             float* add_color) {
  // Set up shading.
  if (shading) {
    c->SetTexture(color_texture_.exists() ? color_texture_->texture_data()
                                          : nullptr);
    c->SetColorizeTexture(color_mask_texture_.exists()
                              ? color_mask_texture_->texture_data()
                              : nullptr);
    c->SetColorizeColor(color_[0], color_[1], color_[2]);
    assert(highlight_.size() == 3);
    c->SetColorizeColor2(highlight_[0], highlight_[1], highlight_[2]);
    c->SetLightShadow(base::LightShadowType::kObject);
    c->SetAddColor(add_color[0], add_color[1], add_color[2]);

    // Tint blueish when frozen.
    if (frozen_) {
      c->SetColor(0.9f, 0.9f, 1.2f);
    } else if (dead_) {
      // Fade to reddish when dead.
      float r = 0.3f + 0.7f * death_fade;
      float g = 0.1f + 0.5f * death_fade;
      float b = 0.1f + 0.5f * death_fade;
      c->SetColor(r, g, b);
    }

    if (frozen_) {
      c->SetReflection(base::ReflectionType::kSharper);
      c->SetReflectionScale(1.5f, 1.5f, 1.5f);
    } else {
      if (dead_) {
        // Go mostly matte when dead.
        c->SetReflection(base::ReflectionType::kSoft);
        c->SetReflectionScale(0.03f, 0.03f, 0.03f);
      } else {
        c->SetReflection(base::ReflectionType::kChar);
        c->SetReflectionScale(reflection_scale_, reflection_scale_,
                              reflection_scale_);
      }
    }
  }

  // Head.
  {
    auto xf = c->ScopedTransform();
    body_head_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (head_mesh_.exists()) {
      c->DrawMeshAsset(head_mesh_->mesh_data());
    }
  }

  // Hair tuft 1.
  if (hair_front_right_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_front_right_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kHairTuft1));
    }

    // Hair tuft 1b; just reuse tuft 1 with some extra translating.
    const dReal* m = dBodyGetRotation(body_head_->body());
    {
      auto xf = c->ScopedTransform();
      float offs[] = {-0.03f, 0.0f, -0.13f};
      c->Translate(offs[0] * m[0] + offs[1] * m[1] + offs[2] * m[2],
                   offs[0] * m[4] + offs[1] * m[5] + offs[2] * m[6],
                   offs[0] * m[8] + offs[1] * m[9] + offs[2] * m[10]);
      hair_front_right_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kHairTuft1b));
    }
  }

  // Hair tuft 2.
  if (hair_front_left_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_front_left_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) c->Scale(death_scale, death_scale, death_scale);
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kHairTuft2));
    }
  }

  // Hair tuft 3.
  if (hair_ponytail_top_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_ponytail_top_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kHairTuft3));
    }
  }

  // Hair tuft 4.
  if (hair_ponytail_bottom_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_ponytail_bottom_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      c->DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kHairTuft4));
    }
  }

  // Torso.
  {
    auto xf = c->ScopedTransform();
    body_torso_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (torso_mesh_.exists()) {
      c->DrawMeshAsset(torso_mesh_->mesh_data());
    }
  }

  // Pelvis.
  {
    auto xf = c->ScopedTransform();
    body_pelvis_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (pelvis_mesh_.exists()) {
      c->DrawMeshAsset(pelvis_mesh_->mesh_data());
    }
  }

  // Get the distance between the shoulder joint socket and the fore-arm
  // socket.. we'll use this to stretch our upper-arm to fill the gap.
  float right_stretch = 1.0f;

  // Right upper arm.

  {
    auto xf = c->ScopedTransform();

    upper_right_arm_body_->ApplyToRenderComponent(c);

    if (!shattered_) {
      dVector3 p_shoulder;
      dBodyGetRelPointPos(body_torso_->body(),
                          upper_right_arm_joint_->anchor1[0],
                          upper_right_arm_joint_->anchor1[1],
                          upper_right_arm_joint_->anchor1[2], p_shoulder);
      dVector3 p_forearm;
      dBodyGetRelPointPos(lower_right_arm_body_->body(),
                          lower_right_arm_joint_->anchor2[0],
                          upper_right_arm_joint_->anchor2[1],
                          upper_right_arm_joint_->anchor2[2], p_forearm);
      right_stretch = std::min(
          1.6f, (Vector3f(p_shoulder) - Vector3f(p_forearm)).Length() / 0.192f);
    }

    // If we've got flippers instead of arms, shorten them if we've got gloves
    // on so they don't intersect as badly.
    if (flippers_ && have_boxing_gloves_) {
      right_stretch *= 0.5f;
    }

    c->Scale(1.0f, 1.0f, right_stretch);

    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (upper_arm_mesh_.exists()) {
      c->DrawMeshAsset(upper_arm_mesh_->mesh_data());
    }
  }

  // Right lower arm.
  {
    auto xf = c->ScopedTransform();

    lower_right_arm_body_->ApplyToRenderComponent(c);
    {
      auto xf = c->ScopedTransform();
      c->Translate(0, 0, 0.1f);
      c->Scale(1.0f, 1.0f, right_stretch);
      c->Translate(0.0f, 0.0f, -0.1f);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
      }
      if (forearm_mesh_.exists() && !flippers_) {
        c->DrawMeshAsset(forearm_mesh_->mesh_data());
      }
    }
    if (!have_boxing_gloves_) {
      c->Translate(0, 0, 0.04f);
      if (holding_something_) {
        c->Rotate(-50, 0, 1, 0);
      } else {
        c->Rotate(10, 0, 1, 0);
      }
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
      }
      if (hand_mesh_.exists() && !flippers_) {
        c->DrawMeshAsset(hand_mesh_->mesh_data());
      }
    }
  }

  // Right upper leg.
  {
    auto xf = c->ScopedTransform();
    upper_right_leg_body_->ApplyToRenderComponent(c);

    // Apply stretching if still intact.
    if (!shattered_) {
      dVector3 p_pelvis;
      dBodyGetRelPointPos(body_pelvis_->body(),
                          upper_right_leg_joint_->anchor1[0],
                          upper_right_leg_joint_->anchor1[1],
                          upper_right_leg_joint_->anchor1[2], p_pelvis);
      dVector3 p_lower_leg;
      dBodyGetRelPointPos(lower_right_leg_body_->body(),
                          lower_right_leg_joint_->anchor2[0],
                          upper_right_leg_joint_->anchor2[1],
                          upper_right_leg_joint_->anchor2[2], p_lower_leg);
      float stretch = std::min(
          1.6f, (Vector3f(p_pelvis) - Vector3f(p_lower_leg)).Length() / 0.20f);
      c->Scale(1.0f, 1.0f, stretch);
    }
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (upper_leg_mesh_.exists()) {
      c->DrawMeshAsset(upper_leg_mesh_->mesh_data());
    }
  }

  // Right lower leg.
  {
    auto xf = c->ScopedTransform();
    lower_right_leg_body_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (lower_leg_mesh_.exists()) {
      c->DrawMeshAsset(lower_leg_mesh_->mesh_data());
    }
  }

  {
    auto xf = c->ScopedTransform();
    right_toes_body_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (toes_mesh_.exists()) {
      c->DrawMeshAsset(toes_mesh_->mesh_data());
    }
  }

  // OK NOW LEFT SIDE LIMBS:
  c->FlipCullFace();

  float left_stretch = 1.0f;

  // Left upper arm.
  {
    auto xf = c->ScopedTransform();

    upper_left_arm_body_->ApplyToRenderComponent(c);

    // Stretch if not shattered.
    if (!shattered_) {
      dVector3 p_shoulder;
      dBodyGetRelPointPos(body_torso_->body(),
                          upper_left_arm_joint_->anchor1[0],
                          upper_left_arm_joint_->anchor1[1],
                          upper_left_arm_joint_->anchor1[2], p_shoulder);
      dVector3 p_forearm;
      dBodyGetRelPointPos(lower_left_arm_body_->body(),
                          lower_left_arm_joint_->anchor2[0],
                          upper_left_arm_joint_->anchor2[1],
                          upper_left_arm_joint_->anchor2[2], p_forearm);
      left_stretch = std::min(
          1.6f, (Vector3f(p_shoulder) - Vector3f(p_forearm)).Length() / 0.192f);
    }

    // If we've got flippers instead of arms, shorten them if we've got gloves
    // on so they don't intersect as badly.
    if (flippers_ && have_boxing_gloves_) {
      left_stretch *= 0.5f;
    }
    c->Scale(-1, 1, left_stretch);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (upper_arm_mesh_.exists()) {
      c->DrawMeshAsset(upper_arm_mesh_->mesh_data());
    }
  }

  // Left lower arm.
  {
    auto xf = c->ScopedTransform();

    lower_left_arm_body_->ApplyToRenderComponent(c);
    c->Scale(-1, 1, 1);
    {
      auto x = c->ScopedTransform();
      c->Translate(0, 0, 0.1f);
      c->Scale(1, 1, left_stretch);
      c->Translate(0, 0, -0.1f);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
      }
      if (forearm_mesh_.exists() && !flippers_) {
        c->DrawMeshAsset(forearm_mesh_->mesh_data());
      }
    }
    if (!have_boxing_gloves_) {
      c->Translate(0, 0, 0.04f);
      if (holding_something_) {
        c->Rotate(-50, 0, 1, 0);
      } else {
        c->Rotate(10, 0, 1, 0);
      }
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      if (hand_mesh_.exists() && !flippers_) {
        c->DrawMeshAsset(hand_mesh_->mesh_data());
      }
    }
  }

  // Left upper leg.
  {
    auto xf = c->ScopedTransform();

    upper_left_leg_body_->ApplyToRenderComponent(c);

    // Stretch if not shattered.
    if (!shattered_) {
      dVector3 p_pelvis;
      dBodyGetRelPointPos(body_pelvis_->body(),
                          upper_left_leg_joint_->anchor1[0],
                          upper_left_leg_joint_->anchor1[1],
                          upper_left_leg_joint_->anchor1[2], p_pelvis);
      dVector3 p_lower_leg;
      dBodyGetRelPointPos(lower_left_leg_body_->body(),
                          lower_left_leg_joint_->anchor2[0],
                          upper_left_leg_joint_->anchor2[1],
                          upper_left_leg_joint_->anchor2[2], p_lower_leg);
      float stretch = std::min(
          1.6f, (Vector3f(p_pelvis) - Vector3f(p_lower_leg)).Length() / 0.20f);
      c->Scale(-1.0f, 1.0f, stretch);
    }
    if (death_scale != 1.0f)
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    if (upper_leg_mesh_.exists())
      c->DrawMeshAsset(upper_leg_mesh_->mesh_data());
  }

  // Lower leg.
  {
    auto xf = c->ScopedTransform();
    lower_left_leg_body_->ApplyToRenderComponent(c);
    c->Scale(-1.0f, 1.0f, 1.0f);
    if (death_scale != 1.0f)
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    if (lower_leg_mesh_.exists()) {
      c->DrawMeshAsset(lower_leg_mesh_->mesh_data());
    }
  }

  // Toes.
  {
    auto xf = c->ScopedTransform();

    left_toes_body_->ApplyToRenderComponent(c);
    c->Scale(-1, 1, 1);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (toes_mesh_.exists()) {
      c->DrawMeshAsset(toes_mesh_->mesh_data());
    }
  }

  // RESTORE CULL
  c->FlipCullFace();
}

static void DrawRadialMeter(base::MeshIndexedSimpleFull* m,
                            base::SimpleComponent* c, float amt, bool flash) {
  if (flash) {
    c->SetColor(1, 1, 0.4f, 0.7f);
  } else {
    c->SetColor(1, 1, 1, 0.6f);
  }
  base::Graphics::DrawRadialMeter(m, amt);
  c->DrawMesh(m);
}

void SpazNode::Draw(base::FrameDef* frame_def) {
#if !BA_HEADLESS_BUILD

  if (graphics_quality_ != frame_def->quality()) {
    graphics_quality_ = frame_def->quality();
    UpdateForGraphicsQuality(graphics_quality_);
  }

#if BA_PLATFORM_MACOS
  if (g_base->graphics_server->renderer()->debug_draw_mode()) {
    base::SimpleComponent c(frame_def->overlay_3d_pass());
    c.SetTransparent(true);
    c.SetDoubleSided(true);
    c.SetColor(1, 0, 0, 0.5f);

    {
      auto xf = c.ScopedTransform();
      body_head_->ApplyToRenderComponent(&c);

      c.BeginDebugDrawTriangles();
      c.Vertex(0, 0.5f, 0);
      c.Vertex(0, 0, 0.5f);
      c.Vertex(0, 0, 0);
      c.End();
    }

    {
      auto xf = c.ScopedTransform();
      body_torso_->ApplyToRenderComponent(&c);
      c.BeginDebugDrawTriangles();
      c.Vertex(0, 0.2f, 0);
      c.Vertex(0, 0, 0.2f);
      c.Vertex(0, 0, 0);
      c.End();
    }

    {
      auto xf = c.ScopedTransform();
      body_pelvis_->ApplyToRenderComponent(&c);
      c.BeginDebugDrawTriangles();
      c.Vertex(0, 0.2f, 0);
      c.Vertex(0, 0, 0.2f);
      c.Vertex(0, 0, 0);
      c.End();
    }

    c.SetColor(0.4f, 1.0f, 0.4f, 0.2f);
    {
      auto xf = c.ScopedTransform();

      stand_body_->ApplyToRenderComponent(&c);
      c.BeginDebugDrawTriangles();
      c.Vertex(0, 0.2f, 0);
      c.Vertex(0, 0, 0.5f);
      c.Vertex(0, 0, 0);

      c.Vertex(0, 2.0f, 0);
      c.Vertex(0, 0, 0.1f);
      c.Vertex(0, 0, 0);

      c.Vertex(0, 0.2f, 0);
      c.Vertex(0.5f, 0, 0);
      c.Vertex(0, 0, 0);

      c.Vertex(0, 2.0f, 0);
      c.Vertex(0.1f, 0, 0.0f);
      c.Vertex(0, 0, 0);

      c.End();
    }

    // Punch direction.
    if (explicit_bool(true)) {
      c.SetColor(1, 1, 0, 0.5f);
      const dReal* p = dBodyGetPosition(body_torso_->body());
      {
        auto xf = c.ScopedTransform();
        c.Translate(p[0], p[1], p[2]);
        c.BeginDebugDrawTriangles();
        c.Vertex(0, 0, 0);
        c.Vertex(2.0f * punch_dir_x_, 0, 2.0f * punch_dir_z_);
        c.Vertex(0, 0.05f, 0);
        c.Vertex(0, 0, 0);
        c.Vertex(0, 0.05f, 0);
        c.Vertex(2.0f * punch_dir_x_, 0, 2.0f * punch_dir_z_);
        c.End();
      }
    }

    // Run joint foot attach.
    if (explicit_bool(true)) {
      c.SetColor(1, 0, 0);
      {
        auto xf = c.ScopedTransform();
        lower_left_leg_body_->ApplyToRenderComponent(&c);
        JointFixedEF* j = left_leg_ik_joint_;
        c.Translate(j->anchor2[0], j->anchor2[1], j->anchor2[2]);
        c.Rotate(90, 1, 0, 0);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.BeginDebugDrawTriangles();
        c.Vertex(0, 0.1f, 0.5f);
        c.Vertex(0, 0, 0.5f);
        c.Vertex(0, 0, 0);
        c.Vertex(0, 0, 0);
        c.Vertex(0, 0, 0.5f);
        c.Vertex(0, 0.1f, 0.5f);
        c.End();
      }
    }

    // Run joint pelvis attach.
    if (explicit_bool(true)) {
      c.SetColor(0, 0, 1);
      {
        auto xf = c.ScopedTransform();
        body_pelvis_->ApplyToRenderComponent(&c);
        JointFixedEF* j = left_leg_ik_joint_;
        c.Translate(j->anchor1[0], j->anchor1[1], j->anchor1[2]);
        c.Rotate(90, 1, 0, 0);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.BeginDebugDrawTriangles();
        c.Vertex(0, 0.1f, 0.5f);
        c.Vertex(0, 0, 0.5f);
        c.Vertex(0, 0, 0);
        c.Vertex(0, 0, 0);
        c.Vertex(0, 0, 0.5f);
        c.Vertex(0, 0.1f, 0.5f);
        c.End();
      }
    }

    c.Submit();
  }
#endif  // BA_PLATFORM_MACOS

  millisecs_t scenetime = scene()->time();
  int64_t render_frame_count = frame_def->frame_number_filtered();
  auto* beauty_pass = frame_def->beauty_pass();

  float death_fade = 1.0f;
  float death_scale = 1.0f;
  millisecs_t since_death = 0;
  float add_color[3] = {0, 0, 0};

  if (dead_) {
    since_death = scenetime - death_time_;
    if (since_death > 2000) {
      death_scale = 0.0f;
    } else if (since_death > 1750) {
      death_scale = 1.0f - (static_cast<float>(since_death - 1750) / 250.0f);
    } else {
      death_scale = 1.0f;
    }

    // Slowly fade down to black.
    if (frozen_) {
      death_fade = 1.0f;  // except when frozen..
    } else {
      if (since_death < 2000) {
        death_fade = 1.0f - (static_cast<float>(since_death) / 2000.0f);
      } else {
        death_fade = 0.0f;
      }
    }
  }

  // Invincible! flash white.
  if (invincible_) {
    if (frame_def->frame_number_filtered() % 6 < 3) {
      add_color[0] = 0.12f;
      add_color[1] = 0.22f;
      add_color[2] = 0.0f;
    }
  } else if (!dead_ && flashing_ > 0) {
    // Flashing red.
    float flash_amount =
        1.0f - std::abs(static_cast<float>(flashing_) - 5.0f) / 5.0f;
    add_color[0] = add_color[1] = 0.8f * flash_amount;
    add_color[2] = 0.0f;
  } else if (!dead_ && curse_death_time_ != 0) {
    // Cursed.
    if (scene()->stepnum() % (static_cast<int>(100.0f - (90.0f * 1.0f))) < 5) {
      if (frozen_) {
        add_color[0] = 0.2f;
        add_color[1] = 0.0f;
        add_color[2] = 0.4f;
      } else {
        add_color[0] = 0.2f;
        add_color[1] = 0.0f;
        add_color[2] = 0.1f;
      }
    } else {
      if (frozen_) {
        add_color[0] = 0.15f;
        add_color[1] = 0.15f;
        add_color[2] = 0.5f;
      } else {
        add_color[0] = add_color[1] = add_color[2] = 0.0f;
      }
    }
  } else if (!dead_ && (hurt_ > 0.0f)
             && (scene()->stepnum()
                     % (static_cast<int>(100.0f - (90.0f * hurt_)))
                 < 5)) {
    // Flash red periodically when hurt but not dead.
    if (frozen_) {
      add_color[0] = 0.33f;
      add_color[1] = 0.1f;
      add_color[2] = 0.4f;
    } else {
      add_color[0] = 0.33f;
      add_color[1] = 0.0f;
      add_color[2] = 0.0f;
    }
  } else {
    if (frozen_) {
      if (dead_) {
        // flash bright white momentarily when dying
        // ..except when falling out of bounds.. its funnier to not flash then
        // if ((since_death < 200) and (scene()->time() -
        // last_out_of_bounds_time_ > 3000)) {
        // if ((scene()->time() - last_fall_time_ < 3000) and
        // (since_death < 50)) {
        // }
        if ((since_death < 200)
            && (scene()->time() - last_out_of_bounds_time_ > 3000)) {
          // if (since_death < 200) {
          float flash = 1.0f - (static_cast<float>(since_death) / 200.0f);
          add_color[0] = 0.15f + flash * 0.9f;
          add_color[1] = 0.15f + flash * 0.9f;
          add_color[2] = 0.5f + flash * 0.6f;
        } else {
          add_color[0] = 0.15f;
          add_color[1] = 0.15f;
          add_color[2] = 0.6f;
        }
      } else {
        // not dead.. just add a bit for frozen-ness
        add_color[0] = 0.12f;
        add_color[1] = 0.12f;
        add_color[2] = 0.4f;
      }
    } else {
      // not frozen.
      if (dead_) {
        if ((since_death < 300)
            && (scene()->time() - last_out_of_bounds_time_ > 3000)) {
          float flash_r = 1.0f - (static_cast<float>(since_death) / 300.0f);
          float flash_g =
              std::max(0.0f, 1.0f - (static_cast<float>(since_death) / 250.0f));
          float flash_b =
              std::max(0.0f, 1.0f - (static_cast<float>(since_death) / 170.0f));
          add_color[0] = 2.0f * flash_r;
          add_color[1] = 0.25f * flash_g;
          add_color[2] = 0.25f * flash_b;
        }
      }
    }
  }

  const dReal* torso_pos_raw = dBodyGetPosition(body_torso_->body());
  float torso_pos[3];
  torso_pos[0] = torso_pos_raw[0] + body_torso_->blend_offset().x;
  torso_pos[1] = torso_pos_raw[1] + body_torso_->blend_offset().y;
  torso_pos[2] = torso_pos_raw[2] + body_torso_->blend_offset().z;

  // Curse time.
  if (curse_death_time_ > 0 && !dead_) {
    millisecs_t diff = (curse_death_time_ - scenetime) / 1000 + 1;
    if (diff < 9999 && diff > 0) {
      char buffer[10];
      snprintf(buffer, sizeof(buffer), "%d", static_cast<int>(diff));
      if (curse_timer_txt_ != buffer) {
        curse_timer_txt_ = buffer;
        curse_timer_text_group_.SetText(curse_timer_txt_);
      }
      float r, g, b;
      if (render_frame_count % 6 < 3) {
        r = 1.0f;
        g = 0.7f;
        b = 0.0f;
      } else {
        r = 0.5f;
        g = 0.0f;
        b = 0.0f;
      }
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      c.SetColor(r, g, b);

      int elem_count = curse_timer_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(curse_timer_text_group_.GetElementTexture(e));
        c.SetShadow(-0.004f * curse_timer_text_group_.GetElementUScale(e),
                    -0.004f * curse_timer_text_group_.GetElementVScale(e), 0.0f,
                    0.3f);
        c.SetMaskUV2Texture(
            curse_timer_text_group_.GetElementMaskUV2Texture(e));
        c.SetFlatness(1.0f);
        {
          auto xf = c.ScopedTransform();
          c.Translate(torso_pos[0] - 0.2f, torso_pos[1] + 0.8f,
                      torso_pos[2] - 0.2f);
          c.Scale(0.02f, 0.02f, 0.02f);
          c.DrawMesh(curse_timer_text_group_.GetElementMesh(e));
        }
      }
      c.Submit();
    }
  }

  // Mini billboard 1.
  if (scenetime < mini_billboard_1_end_time_ && !dead_) {
    float amt = static_cast<float>(mini_billboard_1_end_time_ - scenetime)
                / static_cast<float>(mini_billboard_1_end_time_
                                     - mini_billboard_1_start_time_);
    if (amt > 0.0001f && amt <= 1.0f) {
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      bool flash = (scenetime - mini_billboard_1_start_time_ < 200
                    && render_frame_count % 6 < 3);
      if (!flash) {
        c.SetTexture(mini_billboard_1_texture_.exists()
                         ? mini_billboard_1_texture_->texture_data()
                         : nullptr);
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0] - 0.2f, torso_pos[1] + 1.2f,
                    torso_pos[2] - 0.2f);
        c.Scale(0.08f, 0.08f, 0.08f);
        DrawRadialMeter(&billboard_1_mesh_, &c, amt, flash);
      }
      c.Submit();
    }
  }

  // Mini billboard 2.
  if (scenetime < mini_billboard_2_end_time_ && !dead_) {
    float amt = static_cast<float>(mini_billboard_2_end_time_ - scenetime)
                / static_cast<float>(mini_billboard_2_end_time_
                                     - mini_billboard_2_start_time_);
    if (amt > 0.0001f && amt <= 1.0f) {
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      bool flash = (scenetime - mini_billboard_2_start_time_ < 200
                    && render_frame_count % 6 < 3);
      if (!flash) {
        c.SetTexture(mini_billboard_2_texture_.exists()
                         ? mini_billboard_2_texture_->texture_data()
                         : nullptr);
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0], torso_pos[1] + 1.2f, torso_pos[2] - 0.2f);
        c.Scale(0.09f, 0.09f, 0.09f);
        DrawRadialMeter(&billboard_2_mesh_, &c, amt, flash);
      }
      c.Submit();
    }
  }

  // Mini billboard 3.
  if (scenetime < mini_billboard_3_end_time_ && !dead_) {
    float amt = static_cast<float>(mini_billboard_3_end_time_ - scenetime)
                / static_cast<float>(mini_billboard_3_end_time_
                                     - mini_billboard_3_start_time_);
    if (amt > 0.0001f && amt <= 1.0f) {
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      bool flash = (scenetime - mini_billboard_3_start_time_ < 200
                    && render_frame_count % 6 < 3);
      if (!flash) {
        c.SetTexture(mini_billboard_3_texture_.exists()
                         ? mini_billboard_3_texture_->texture_data()
                         : nullptr);
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0] + 0.2f, torso_pos[1] + 1.2f,
                    torso_pos[2] - 0.2f);
        c.Scale(0.08f, 0.08f, 0.08f);
        DrawRadialMeter(&billboard_3_mesh_, &c, amt, flash);
      }
      c.Submit();
    }
  }

  /// Draw our counter.
  if (!counter_text_.empty() && !dead_) {
    {  // Icon
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      c.SetTexture(counter_texture_.exists() ? counter_texture_->texture_data()
                                             : nullptr);
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0] - 0.3f, torso_pos[1] + 1.47f,
                    torso_pos[2] - 0.2f);
        c.Scale(1.5f * 0.2f, 1.5f * 0.2f, 1.5f * 0.2f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
      }
      c.Submit();
    }
    {  // Text
      if (counter_mesh_text_ != counter_text_) {
        counter_mesh_text_ = counter_text_;
        counter_text_group_.SetText(counter_mesh_text_);
      }
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      int elem_count = counter_text_group_.GetElementCount();
      for (int e = 0; e < elem_count; e++) {
        c.SetTexture(counter_text_group_.GetElementTexture(e));
        c.SetMaskUV2Texture(counter_text_group_.GetElementMaskUV2Texture(e));
        c.SetShadow(-0.004f * counter_text_group_.GetElementUScale(e),
                    -0.004f * counter_text_group_.GetElementVScale(e), 0.0f,
                    0.3f);
        c.SetFlatness(1.0f);
        {
          auto xf = c.ScopedTransform();
          c.Translate(torso_pos[0] - 0.1f, torso_pos[1] + 1.34f,
                      torso_pos[2] - 0.2f);
          c.Scale(0.01f, 0.01f, 0.01f);
          c.DrawMesh(counter_text_group_.GetElementMesh(e));
        }
      }
      c.Submit();
    }
  }

  // Draw our name.
  if (!name_.empty()) {
    auto age = static_cast<float>(scenetime - birth_time_);
    if (explicit_bool(true)) {
      if (name_mesh_txt_ != name_) {
        name_mesh_txt_ = name_;
        name_text_group_.SetText(name_mesh_txt_,
                                 base::TextMesh::HAlign::kCenter,
                                 base::TextMesh::VAlign::kCenter);
      }
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      float extra;
      if (age < 200) {
        extra = age / 200.0f;
      } else {
        extra = std::min(1.0f, std::max(0.0f, 1.0f - (age - 600.0f) / 200.0f));
      }

      // Make sure our max color channel is non-black.
      assert(name_color_.size() == 3);
      float r = name_color_[0];
      float g = name_color_[1];
      float b = name_color_[2];
      if (dead_) {
        r = 0.45f + 0.2f * r;
        g = 0.45f + 0.2f * g;
        b = 0.45f + 0.2f * b;
      }
      c.SetColor(r, g, b, dead_ ? 0.7f : 1.0f);

      int elem_count = name_text_group_.GetElementCount();
      float s_extra =
          (g_core->vr_mode() || g_base->ui->uiscale() == UIScale::kSmall)
              ? 1.2f
              : 1.0f;

      for (int e = 0; e < elem_count; e++) {
        // Gracefully skip unloaded textures.
        auto* t = name_text_group_.GetElementTexture(e);
        if (!t->preloaded()) continue;
        c.SetTexture(t);
        c.SetMaskUV2Texture(name_text_group_.GetElementMaskUV2Texture(e));
        c.SetShadow(-0.0035f * name_text_group_.GetElementUScale(e),
                    -0.0035f * name_text_group_.GetElementVScale(e), 0.0f,
                    dead_ ? 0.25f : 0.5f);
        c.SetFlatness(1.0f);
        {
          auto xf = c.ScopedTransform();
          c.Translate(torso_pos[0] - 0.0f, torso_pos[1] + 0.89f + 0.4f * extra,
                      torso_pos[2] - 0.2f);
          float s = (0.01f + 0.01f * extra) * death_scale;
          float w = g_base->text_graphics->GetStringWidth(name_.c_str());
          if (w > 100.0f) s *= (100.0f / w);
          s *= s_extra;
          c.Scale(s, s, s);
          c.DrawMesh(name_text_group_.GetElementMesh(e));
        }
      }
      c.Submit();
    }
  }

  // Draw our big billboard.
  if (billboard_opacity_ > 0.001f && !dead_) {
    float o = billboard_opacity_;
    float s = o;
    if (billboard_cross_out_) o *= (render_frame_count % 14 < 7) ? 0.8f : 0.2f;
    const dReal* pos = dBodyGetPosition(body_torso_->body());
    base::SimpleComponent c(frame_def->overlay_3d_pass());
    c.SetTransparent(true);
    c.SetColor(1, 1, 1, o);
    c.SetTexture(billboard_texture_.exists()
                     ? billboard_texture_->texture_data()
                     : nullptr);
    {
      auto xf = c.ScopedTransform();
      c.Translate(pos[0], pos[1] + 1.6f, pos[2] - 0.2f);
      c.Scale(2.3f * 0.2f * s, 2.3f * 0.2f * s, 2.3f * 0.2f * s);
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
    }
    c.Submit();

    // Draw a red cross over it if they want.
    if (billboard_cross_out_) {
      float o2 =
          billboard_opacity_ * ((render_frame_count % 14 < 7) ? 0.4f : 0.1f);
      base::SimpleComponent c2(frame_def->overlay_3d_pass());
      c2.SetTransparent(true);
      c2.SetColor(1, 0, 0, o2);
      {
        auto xf = c2.ScopedTransform();
        c2.Translate(pos[0], pos[1] + 1.6f, pos[2] - 0.2f);
        c2.Scale(2.3f * 0.2f * s, 2.3f * 0.2f * s, 2.3f * 0.2f * s);
        c2.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kCrossOut));
      }
      c2.Submit();
    }
  }

  // Draw life bar if our life has changed recently.
  {
    millisecs_t fade_time = shattered_ ? 1000 : 2000;
    float o{1.0f};
    millisecs_t since_last_hurt_change = scenetime - last_hurt_change_time_;
    if (since_last_hurt_change < fade_time) {
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      c.SetPremultiplied(true);
      {
        auto xf = c.ScopedTransform();

        o = 1.0f
            - static_cast<float>(since_last_hurt_change)
                  / static_cast<float>(fade_time);
        o *= o;
        const dReal* pos = dBodyGetPosition(body_torso_->body());

        float p_left, p_right;
        if (hurt_ < hurt_smoothed_) {
          p_left = 1.0f - hurt_smoothed_;
          p_right = 1.0f - hurt_;
        } else {
          p_right = 1.0f - hurt_smoothed_;
          p_left = 1.0f - hurt_;
        }

        // For the first moment start p_left at p_right so they can see a
        // glimpse of green before it goes away.
        if (since_last_hurt_change < 100) {
          p_left +=
              (p_right - p_left)
              * (1.0f - static_cast<float>(since_last_hurt_change) / 100.0f);
        }

        c.Translate(pos[0] - 0.25f, pos[1] + 1.35f, pos[2] - 0.2f);
        c.Scale(0.5f, 0.5f, 0.5f);

        float height = 0.1f;
        float half_height = height * 0.5f;
        c.SetColor(0, 0, 0, 0.3f * o);

        {
          auto xf = c.ScopedTransform();
          c.Translate(0.5f, half_height);
          c.Scale(1.1f, height + 0.1f);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }

        c.SetColor(0, 0.35f * o, 0, 0.3f * o);

        {
          auto xf = c.ScopedTransform();
          c.Translate(p_left * 0.5f, half_height);
          c.Scale(p_left, height);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }

        if (dead_ && scene()->stepnum() % 10 < 5) {
          c.SetColor(1 * o, 0.3f, 0.0f, 1.0f * o);
        } else {
          c.SetColor(1 * o, 0.0f * o, 0.0f * o, 1.0f * o);
        }

        {
          auto xf = c.ScopedTransform();
          c.Translate((p_left + p_right) * 0.5f, half_height);
          c.Scale(p_right - p_left, height);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }

        c.SetColor(
            (dead_ && scene()->stepnum() % 10 < 5) ? 0.55f * o : 0.01f * o, 0,
            0, 0.4f * o);

        {
          auto xf = c.ScopedTransform();
          c.Translate((p_right + 1.0f) * 0.5f, half_height);
          c.Scale(1.0f - p_right, height);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
      }
      c.Submit();
    }
  }

  // Draw all body parts with normal shading.
  {
    {
      base::ObjectComponent c(beauty_pass);
      DrawBodyParts(&c, true, death_fade, death_scale, add_color);
      SetupEyeLidShading(&c, death_fade, add_color);
      DrawEyeLids(&c, death_fade, death_scale);
      c.Submit();
    }
    {
      base::ObjectComponent c(beauty_pass);
      DrawEyeBalls(&c, &c, true, death_fade, death_scale, add_color);
      c.Submit();
    }

    // In higher-quality mode, blur our eyeballs and eyelids a bit to look more
    // fleshy.
    if (frame_def->quality() >= base::GraphicsQuality::kHigher) {
      base::PostProcessComponent c(frame_def->blit_pass());
      c.setEyes(true);
      DrawEyeLids(&c, death_fade, death_scale);
      DrawEyeBalls(&c, nullptr, false, death_fade, death_scale, add_color);
      c.Submit();
    }
  }

  // Wings.
  if (wings_) {
    base::ObjectComponent c(beauty_pass);
    c.SetTransparent(false);
    c.SetColor(1, 1, 1, 1.0f);
    c.SetReflection(base::ReflectionType::kSoft);
    c.SetReflectionScale(0.4f, 0.4f, 0.4f);
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kWings));

    // Fade to reddish on death.
    if (dead_ && !frozen_) {
      float r = 0.3f + 0.7f * death_fade;
      float g = 0.2f + 0.7f * (death_fade * 0.5f);
      float b = 0.2f + 0.7f * (death_fade * 0.5f);
      c.SetColor(r, g, b);
    }

    // DEBUGGING:
    if (explicit_bool(false)) {
      dVector3 p_wing_l, p_wing_r;

      // Draw target.
      dBodyGetRelPointPos(body_torso_->body(), kWingAttachX, kWingAttachY,
                          kWingAttachZ, p_wing_l);
      {
        auto xf = c.ScopedTransform();
        c.Translate(p_wing_l[0], p_wing_l[1], p_wing_l[2]);
        c.Scale(0.05f, 0.05f, 0.05f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kBox));
      }

      // Draw wing point.
      {
        auto xf = c.ScopedTransform();
        c.Translate(wing_pos_left_.x, wing_pos_left_.y, wing_pos_left_.z);
        c.Scale(0.1f, 0.1f, 0.1f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kBox));
      }

      // Draw target.
      dBodyGetRelPointPos(body_torso_->body(), -kWingAttachX, kWingAttachY,
                          kWingAttachZ, p_wing_r);
      {
        auto xf = c.ScopedTransform();
        c.Translate(p_wing_r[0], p_wing_r[1], p_wing_r[2]);
        c.Scale(0.05f, 0.05f, 0.05f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kBox));
      }

      // Draw wing point.
      {
        auto xf = c.ScopedTransform();
        c.Translate(wing_pos_right_.x, wing_pos_right_.y, wing_pos_right_.z);
        c.Scale(0.1f, 0.1f, 0.1f);
        c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kBox));
      }
    }

    // To draw wings, we need a matrix positioned at our torso pointing at our
    // wing points.
    Vector3f torso_pos2(dBodyGetPosition(body_torso_->body()));
    Vector3f torsoUp = {0.0f, 0.0f, 0.0f};
    dBodyGetRelPointPos(body_torso_->body(), 0.0f, 1.0f, 0.0f, torsoUp.v);
    torsoUp -= torso_pos2;  // needs to be relative to body
    torsoUp.Normalize();

    Vector3f to_left_wing = wing_pos_left_ - torso_pos2;
    to_left_wing.Normalize();
    Vector3f left_wing_side = Vector3f::Cross(to_left_wing, torsoUp);
    left_wing_side.Normalize();
    Vector3f left_wing_up = Vector3f::Cross(left_wing_side, to_left_wing);
    left_wing_up.Normalize();

    // Draw target.
    {
      auto xf = c.ScopedTransform();
      c.Translate(torso_pos2.x, torso_pos2.y, torso_pos2.z);
      c.MultMatrix(
          Matrix44fOrient(left_wing_side, left_wing_up, to_left_wing).m);
      if (death_scale != 1.0f) {
        c.Scale(death_scale, death_scale, death_scale);
      }
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kWing));
    }

    Vector3f to_right_wing = wing_pos_right_ - torso_pos2;
    to_right_wing.Normalize();
    Vector3f right_wing_side = Vector3f::Cross(to_right_wing, torsoUp);
    right_wing_side.Normalize();
    Vector3f right_wing_up = Vector3f::Cross(right_wing_side, to_right_wing);
    right_wing_up.Normalize();

    // Draw target.
    {
      auto xf = c.ScopedTransform();
      c.Translate(torso_pos2.x, torso_pos2.y, torso_pos2.z);
      c.MultMatrix(
          Matrix44fOrient(right_wing_side, right_wing_up, to_right_wing).m);
      if (death_scale != 1.0f) {
        c.Scale(death_scale, death_scale, death_scale);
      }
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kWing));
    }
    c.Submit();
  }

  // Boxing gloves.
  if (have_boxing_gloves_) {
    base::ObjectComponent c(beauty_pass);
    if (frozen_) {
      c.SetAddColor(0.1f, 0.1f, 0.4f);
      c.SetReflection(base::ReflectionType::kSharper);
      c.SetReflectionScale(1.4f, 1.4f, 1.4f);
    } else {
      c.SetReflection(base::ReflectionType::kChar);
      c.SetReflectionScale(0.6f * death_fade, 0.55f * death_fade,
                           0.55f * death_fade);

      // Add extra flash when we're new.
      if (scenetime - last_got_boxing_gloves_time_ < 200) {
        float amt =
            (static_cast<float>(scenetime - last_got_boxing_gloves_time_)
             / 2000.0f);
        amt = 1.0f - (amt * amt);
        c.SetAddColor(add_color[0] + amt * 0.4f, add_color[1] + amt * 0.4f,
                      add_color[2] + amt * 0.1f);
        c.SetColor(1.0f + amt * 6.0f, 1.0f + amt * 6.0f, 1.0f + amt * 3.0f);
      } else {
        c.SetAddColor(add_color[0], add_color[1], add_color[2]);

        if (boxing_gloves_flashing_ && render_frame_count % 6 < 2) {
          c.SetColor(2.0f, 2.0f, 2.0f);
        } else {
          c.SetColor(death_fade, death_fade, death_fade);
        }
      }
    }
    c.SetLightShadow(base::LightShadowType::kObject);
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kBoxingGlove));

    {
      auto xf = c.ScopedTransform();
      lower_right_arm_body_->ApplyToRenderComponent(&c);
      if (death_scale != 1.0f) {
        c.Scale(death_scale, death_scale, death_scale);
      }
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kBoxingGlove));
    }

    c.FlipCullFace();
    {
      auto xf = c.ScopedTransform();
      lower_left_arm_body_->ApplyToRenderComponent(&c);
      c.Scale(-1.0f, 1.0f, 1.0f);
      if (death_scale != 1.0f) {
        c.Scale(death_scale, death_scale, death_scale);
      }
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kBoxingGlove));
      c.FlipCullFace();
    }
    c.Submit();
  }

  // Light/shadows.
  {
    float sc[3] = {shadow_color_[0], shadow_color_[1], shadow_color_[2]};

    if (frozen_) {
      float freeze_color[] = {0.3f, 0.3f, 0.7f};
      float weight = 0.7f;
      sc[0] = weight * freeze_color[0] + (1.0f - weight) * sc[0];
      sc[1] = weight * freeze_color[1] + (1.0f - weight) * sc[1];
      sc[2] = weight * freeze_color[2] + (1.0f - weight) * sc[2];
    }

    // Update and draw shadows.
    if (!g_core->HeadlessMode()) {
      if (FullShadowSet* full_shadows = full_shadow_set_.get()) {
        full_shadows->torso_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_torso_->body())));
        full_shadows->head_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_head_->body())));
        full_shadows->pelvis_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_pelvis_->body())));
        full_shadows->lower_left_leg_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(lower_left_leg_body_->body())));
        full_shadows->lower_right_leg_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(lower_right_leg_body_->body())));
        full_shadows->upper_left_leg_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(upper_left_leg_body_->body())));
        full_shadows->upper_right_leg_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(upper_right_leg_body_->body())));
        full_shadows->lower_right_arm_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(lower_right_arm_body_->body())));
        full_shadows->upper_right_arm_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(upper_right_arm_body_->body())));
        full_shadows->lower_left_arm_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(lower_left_arm_body_->body())));
        full_shadows->upper_left_arm_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(upper_left_arm_body_->body())));

        DrawBrightSpot(full_shadows->lower_left_leg_shadow_, 0.3f * death_scale,
                       death_fade * (frozen_ ? 0.3f : 0.2f), sc);
        DrawBrightSpot(full_shadows->lower_right_leg_shadow_,
                       0.3f * death_scale, death_fade * (frozen_ ? 0.3f : 0.2f),
                       sc);
        DrawBrightSpot(full_shadows->head_shadow_, 0.45f * death_scale,
                       death_fade * (frozen_ ? 0.8f : 0.14f), sc);
        DrawShadow(full_shadows->torso_shadow_, 0.19f * death_scale, 0.9f, sc);
        DrawShadow(full_shadows->head_shadow_, 0.15f * death_scale, 0.7f, sc);
        DrawShadow(full_shadows->pelvis_shadow_, 0.15f * death_scale, 0.7f, sc);
        DrawShadow(full_shadows->lower_left_leg_shadow_, 0.08f * death_scale,
                   1.0f, sc);
        DrawShadow(full_shadows->lower_right_leg_shadow_, 0.08f * death_scale,
                   1.0f, sc);
        DrawShadow(full_shadows->upper_left_leg_shadow_, 0.08f * death_scale,
                   1.0f, sc);
        DrawShadow(full_shadows->upper_right_leg_shadow_, 0.08f * death_scale,
                   1.0f, sc);
        DrawShadow(full_shadows->upper_left_arm_shadow_, 0.08f * death_scale,
                   0.5f, sc);
        DrawShadow(full_shadows->lower_left_arm_shadow_, 0.08f * death_scale,
                   0.3f, sc);
        DrawShadow(full_shadows->lower_right_arm_shadow_, 0.08f * death_scale,
                   0.3f, sc);
        DrawShadow(full_shadows->upper_right_arm_shadow_, 0.08f * death_scale,
                   0.5f, sc);
      } else if (SimpleShadowSet* simple_shadows = simple_shadow_set_.get()) {
        simple_shadows->shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_pelvis_->body())));
        DrawShadow(simple_shadows->shadow_, 0.2f * death_scale, 2.0f, sc);
      }
    }
  }
#endif  // !BA_HEADLESS_BUILD
}  // NOLINT (yes i know this is too big)

void SpazNode::UpdateForGraphicsQuality(base::GraphicsQuality quality) {
#if !BA_HEADLESS_BUILD
  if (quality >= base::GraphicsQuality::kMedium) {
    full_shadow_set_ = Object::New<FullShadowSet>();
    simple_shadow_set_.Clear();
  } else {
    simple_shadow_set_ = Object::New<SimpleShadowSet>();
    full_shadow_set_.Clear();
  }
#endif  // !BA_HEADLESS_BUILD
}

auto SpazNode::IsBrokenBodyPart(int id) -> bool {
  switch (id) {
    case kHeadBodyID:
      return static_cast<bool>(shatter_damage_ & kNeckJointBroken);
    case kUpperRightArmBodyID:
      return static_cast<bool>(shatter_damage_ & kUpperRightArmJointBroken);
    case kLowerRightArmBodyID:
      return static_cast<bool>(shatter_damage_ & kLowerRightArmJointBroken);
    case kUpperLeftArmBodyID:
      return static_cast<bool>(shatter_damage_ & kUpperLeftArmJointBroken);
    case kLowerLeftArmBodyID:
      return static_cast<bool>(shatter_damage_ & kLowerLeftArmJointBroken);
    case kUpperRightLegBodyID:
      return static_cast<bool>(shatter_damage_ & kUpperRightLegJointBroken);
    case kLowerRightLegBodyID:
      return static_cast<bool>(shatter_damage_ & kLowerRightLegJointBroken);
    case kUpperLeftLegBodyID:
      return static_cast<bool>(shatter_damage_ & kUpperLeftLegJointBroken);
    case kLowerLeftLegBodyID:
      return static_cast<bool>(shatter_damage_ & kLowerLeftLegJointBroken);
    case kPelvisBodyID:
      return static_cast<bool>(shatter_damage_ & kPelvisJointBroken);
    default:
      return false;
  }
}

auto SpazNode::PreFilterCollision(RigidBody* colliding_body,
                                  RigidBody* opposing_body) -> bool {
  assert(colliding_body->part()->node() == this);
  if (opposing_body->part()->node() == this) {
    // If self-collide has gone down to zero we can just skip this completely.
    // if (!frozen_ and limb_self_collide_ < 0.01f) return false;

    int our_id = colliding_body->id();
    int their_id = opposing_body->id();

    // Special case - if we're a broken off bodypart, collide with anything.
    if (shattered_ && IsBrokenBodyPart(our_id)) {
      return true;
    }

    // Get nitpicky with our self-collisions.
    switch (our_id) {
      case kHeadBodyID:
      case kTorsoBodyID:
        // Head and torso will collide with anyone who wants to
        // (leave the decision up to them).
        return true;
        break;
      case kLowerLeftArmBodyID:
        // Lower arms collide with head, torso, and upper legs
        // and upper arms if shattered.
        switch (their_id) {
          case kHeadBodyID:
          case kTorsoBodyID:
          case kUpperLeftLegBodyID:
            return true;
          default:
            return false;
        }
        break;
      case kLowerRightArmBodyID:
        // Lower arms collide with head, torso, and upper legs.
        switch (their_id) {
          case kHeadBodyID:
          case kTorsoBodyID:
          case kUpperRightLegBodyID:
            return true;
          default:
            return false;
        }
        break;
      case kUpperLeftArmBodyID:  // NOLINT(bugprone-branch-clone)
        return false;
        break;
      case kUpperRightArmBodyID:
        return false;
        break;
      case kUpperLeftLegBodyID:
        // Collide with lower arm.
        switch (their_id) {  // NOLINT
          case kLowerLeftArmBodyID:
            return true;
          default:
            return false;
        }
        break;
      case kUpperRightLegBodyID:
        // collide with lower arm
        switch (their_id) {  // NOLINT
          case kLowerRightArmBodyID:
            return true;
          default:
            return false;
        }
        break;
      case kLowerLeftLegBodyID:
        // collide with opposite lower leg
        switch (their_id) {  // NOLINT
          case kLowerRightLegBodyID:
            return true;
          default:
            return false;
        }
        break;
      case kLowerRightLegBodyID:
        // lower right leg collides with lower left leg
        switch (their_id) {  // NOLINT
          case kLowerLeftLegBodyID:
            return true;
          default:
            return false;
        }
        break;
      default:
        // default to no collisions elsewhere
        return false;
        break;
    }
  } else {
    // Non-us opposing node.

    // We ignore bumpers if we're injured, frozen, or if a non-roller-ball part
    // of us is hitting it.
    {
      uint32_t f = opposing_body->flags();
      if (f & RigidBody::kIsBumper) {
        if ((knockout_) || (frozen_) || (balance_ < 50)
            || colliding_body->part() != &roller_part_)
          return false;
      }
    }
  }

  if (colliding_body->id() == kRollerBodyID) {
    // Never collide against shrunken roller-ball.
    if (ball_size_ <= 0.0f) {
      return false;
    }
  }
  return true;
}

auto SpazNode::CollideCallback(dContact* c, int count,
                               RigidBody* colliding_body,
                               RigidBody* opposing_body) -> bool {
  // Keep track of whether our toes are touching something besides us
  // if (colliding_body == left_toes_body_.Get() and opposingbody->getNode() !=
  // this) _toesTouchingL = true; if (colliding_body == right_toes_body_.Get()
  // and opposingbody->getNode() != this) _toesTouchingR = true; _toesTouchingL
  // = (colliding_body == left_toes_body_.Get() and opposingbody->getNode() !=
  // this); _toesTouchingR = (colliding_body == right_toes_body_.Get() and
  // opposingbody->getNode() != this);

  // hair collide with most anything but weakly..
  if (colliding_body->part() == &hair_part_
      || opposing_body->part() == &hair_part_) {
    // Hair doesnt collide with hair.
    if (colliding_body->part() == opposing_body->part()) return false;

    // ignore bumpers..
    if (opposing_body->flags() & RigidBody::kIsBumper) return false;

    // drop stiffness/damping/friction pretty low..
    float stiffness = 200.0f;
    float damping = 10.0f;

    float erp, cfm;
    CalcERPCFM(stiffness, damping, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
      c[i].surface.mu = 0.1f;
    }
    return true;
  }

  if (colliding_body->part() == &limbs_part_lower_) {
    // Drop friction if lower arms are hitting upper legs.
    if ((colliding_body == lower_left_arm_body_.get()
         || colliding_body == lower_right_arm_body_.get())
        && !shattered_) {
      for (int i = 0; i < count; i++) {
        c[i].surface.mu = 0.0f;
      }
    }

    // Now drop collision forces across the board.
    float stiffness = 10.0f;
    float damping = 1.0f;

    if (colliding_body == left_toes_body_.get()
        || colliding_body == right_toes_body_.get()) {
      stiffness *= kToesCollideStiffness;
      damping *= kToesCollideDamping;

      // Also drop friction on toes.
      for (int i = 0; i < count; i++) {
        c[i].surface.mu *= 0.1f;
      }
    }
    if (colliding_body == lower_right_leg_body_.get()
        || colliding_body == lower_left_leg_body_.get()) {
      stiffness *= kLowerLegCollideStiffness;
      damping *= kLowerLegCollideDamping;
    }
    if (shattered_) {
      stiffness *= 100.0f;
      damping *= 10.0f;
    }

    // If we're hitting ourself, drop all forces based on our self-collide
    // level.
    if (opposing_body->part()->node() == this && !frozen_) {
      for (int i = 0; i < count; i++) {
        c[i].surface.mu = 0.0f;
      }
    }

    // If we're punching, lets crank up stiffness on our punching hand
    // so it looks like its responding to stuff its hitting.
    if (punch_ && !dead_) {
      if ((colliding_body == lower_right_arm_body_.get() && punch_right_)
          || (colliding_body == lower_left_arm_body_.get() && !punch_right_)) {
        stiffness *= 200.0f;
        damping *= 20.0f;
      }
    }

    float erp, cfm;
    CalcERPCFM(stiffness, damping, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
    }
  } else if (colliding_body->part() == &limbs_part_upper_) {
    float stiffness = 10;
    float damping = 1;
    float erp, cfm;
    if (colliding_body == upper_right_leg_body_.get()
        || colliding_body == upper_left_leg_body_.get()) {
      stiffness *= kUpperLegCollideStiffness;
      damping *= kUpperLegCollideDamping;
    }

    // Keeps our arms from pushing into our head.
    stiffness *= 10.0f;
    if (shattered_) {
      stiffness *= 100.0f;
      damping *= 10.0f;
    }
    CalcERPCFM(stiffness, damping, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
    }
  }

  if (colliding_body->part() == &spaz_part_) {
    float stiffness = 5000;
    float damping = 0.001f;
    float erp, cfm;
    CalcERPCFM(stiffness, damping, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
    }
  }

  // If we're frozen and shattered, lets slide!
  if (frozen_) {
    for (int i = 0; i < count; i++) {
      c[i].surface.mu = 0.4f;
    }
  }

  // Muck with roller friction.
  if (colliding_body->id() == kRollerBodyID) {
    // For non-bumper collisions, drop collision forces on the side.
    // (we want more friction on the bottom of our roller ball than on the
    // sides).
    uint32_t f = opposing_body->flags();
    if (!(f & RigidBody::kIsBumper)) {
      for (int i = 0; i < count; i++) {
        // Let's use world-down instead.
        dVector3 down = {0, 1, 0};
        float dot = std::abs(dDOT(c[i].geom.normal, down));
        if (dot > 1) {
          dot = 1;
        } else if (dot < 0) {
          dot = 0;
        }

        if (dot < 0.6f) {
          // give our roller a kick away from vertical terrain surfaces
          if ((f & RigidBody::kIsTerrain)) {
            dBodyID b = body_roller_->body();
            dBodyAddForce(b, c[i].geom.normal[0] * 100.0f,
                          c[i].geom.normal[1] * 100.0f,
                          c[i].geom.normal[2] * 100.0f);
          }

          // Override stiffness and damping on our little parts
          float stiffness = 800.0f;
          float damping = 0.001f;
          float erp, cfm;
          CalcERPCFM(stiffness, damping, &erp, &cfm);
          c[i].surface.soft_erp = erp;
          c[i].surface.soft_cfm = cfm;
          c[i].surface.mu = 0.0f;

        } else {
          // trying to get a well-behaved floor-response...
          if (!hockey_) {
            float stiffness = 7000.0f;
            float damping = 7.0f;
            float erp, cfm;
            CalcERPCFM(stiffness, damping, &erp, &cfm);
            c[i].surface.soft_erp = erp;
            c[i].surface.soft_cfm = cfm;
            c[i].surface.mu *= 1.0f;
          }
        }
      }
    }
  } else if (colliding_body->id() != kRollerBodyID) {
    // Drop friction on all our non-roller-ball parts.
    for (int i = 0; i < count; i++) {
      c[i].surface.mu *= 0.3f;
    }
  }

  // Keep track of when stuff is hitting our head, so we know when to calc
  // damage from head whiplash.
  if (colliding_body == body_head_.get()
      && opposing_body->part()->node() != this
      && opposing_body->can_cause_impact_damage()) {
    last_head_collide_time_ = scene()->time();
  }

  return true;
}

void SpazNode::Stand(float x, float y, float z, float angle) {
  y -= 0.7f;

  // If we're getting teleported we dont wanna pull things along with us.
  DropHeldObject();
  spaz_part_.KillConstraints();
  hair_part_.KillConstraints();
  punch_part_.KillConstraints();
  pickup_part_.KillConstraints();
  extras_part_.KillConstraints();
  roller_part_.KillConstraints();
  limbs_part_upper_.KillConstraints();
  limbs_part_lower_.KillConstraints();

  // So this doesn't trip our jolt mechanisms.
  jolt_head_vel_[0] = jolt_head_vel_[1] = jolt_head_vel_[2] = 0.0f;

  dQuaternion iq;
  dQFromAxisAndAngle(iq, 0, 1, 0, angle * (kPi / 180.0f));

  dBodyID b;

  // Head
  b = body_head_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x, y + 2.25f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Torso
  b = body_torso_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x, y + 1.8f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // pelvis
  b = body_pelvis_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x, y + 1.66f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Roller
  b = body_roller_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x, y + 1.6f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Stand
  b = stand_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x, y + 1.8f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Upper Right Arm
  b = upper_right_arm_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x - 0.17f, y + 1.9f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Lower Right Arm
  b = lower_right_arm_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x - 0.17f, y + 1.9f, z + 0.07f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Upper Left Arm
  b = upper_left_arm_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x + 0.17f, y + 1.9f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Lower Left Arm
  b = lower_left_arm_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x + 0.17f, y + 1.9f, z + 0.07f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Upper Right Leg
  b = upper_right_leg_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x - 0.1f, y + 1.65f, z);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Lower Right Leg
  b = lower_right_leg_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x - 0.1f, y + 1.65f, z + 0.05f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Right Toes
  b = right_toes_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x - 0.1f, y + 1.7f, z + 0.1f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Upper Left Leg
  b = upper_left_leg_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x + 0.1f, y + 1.65f, z + 0.00f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Lower Left Leg
  b = lower_left_leg_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x + 0.1f, y + 1.65f, z + 0.05f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // Left Toes
  b = left_toes_body_->body();
  dBodyEnable(b);
  dBodySetPosition(b, x + 0.1f, y + 1.7f, z + 0.1f);
  dBodySetLinearVel(b, 0, 0, 0);
  dBodySetAngularVel(b, 0, 0, 0);
  dBodySetQuaternion(b, iq);
  dBodySetForce(b, 0, 0, 0);

  // If we have hair.
  if (hair_front_right_joint_) PositionBodyForJoint(hair_front_right_joint_);
  if (hair_front_left_joint_) PositionBodyForJoint(hair_front_left_joint_);
  if (hair_ponytail_top_joint_) PositionBodyForJoint(hair_ponytail_top_joint_);
  if (hair_ponytail_bottom_joint_)
    PositionBodyForJoint(hair_ponytail_bottom_joint_);
}

auto SpazNode::GetRigidBody(int id) -> RigidBody* {
  // Ewwww this should be automatic.
  switch (id) {
    case kHeadBodyID:
      return body_head_.get();
      break;
    case kTorsoBodyID:
      return body_torso_.get();
      break;
    case kPunchBodyID:
      return body_punch_.get();
      break;
    case kPickupBodyID:
      return body_pickup_.get();
      break;
    case kPelvisBodyID:
      return body_pelvis_.get();
      break;
    case kRollerBodyID:
      return body_roller_.get();
      break;
    case kStandBodyID:
      return stand_body_.get();
      break;
    case kUpperRightArmBodyID:
      return upper_right_arm_body_.get();
      break;
    case kLowerRightArmBodyID:
      return lower_right_arm_body_.get();
      break;
    case kUpperLeftArmBodyID:
      return upper_left_arm_body_.get();
      break;
    case kLowerLeftArmBodyID:
      return lower_left_arm_body_.get();
      break;
    case kUpperRightLegBodyID:
      return upper_right_leg_body_.get();
      break;
    case kLowerRightLegBodyID:
      return lower_right_leg_body_.get();
      break;
    case kUpperLeftLegBodyID:
      return upper_left_leg_body_.get();
      break;
    case kLowerLeftLegBodyID:
      return lower_left_leg_body_.get();
      break;
    case kLeftToesBodyID:
      return left_toes_body_.get();
      break;
    case kRightToesBodyID:
      return right_toes_body_.get();
      break;
    case kHairFrontRightBodyID:
      return hair_front_right_body_.get();
      break;
    case kHairFrontLeftBodyID:
      return hair_front_left_body_.get();
      break;
    case kHairPonyTailTopBodyID:
      return hair_ponytail_top_body_.get();
      break;
    case kHairPonyTailBottomBodyID:
      return hair_ponytail_bottom_body_.get();
      break;
    default:
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "Request for unknown spaz body: " + std::to_string(id));
      break;
  }

  return nullptr;
}

void SpazNode::GetRigidBodyPickupLocations(int id, float* obj, float* character,
                                           float* hand1, float* hand2) {
  if (id == kHeadBodyID) {
    obj[0] = 0;
    obj[1] = 0;
    obj[2] = 0;
  } else {
    obj[0] = obj[1] = obj[2] = 0;
  }

  character[0] = character[1] = character[2] = 0.0f;
  character[1] = -0.15f;
  character[2] = 0.05f;

  hand1[0] = hand1[1] = hand1[2] = 0.0f;
  hand2[0] = hand2[1] = hand2[2] = 0.0f;
}
void SpazNode::DropHeldObject() {
  if (holding_something_) {
    if (hold_node_.exists()) {
      assert(pickup_joint_.IsAlive());
      pickup_joint_.Kill();
    }
    assert(!pickup_joint_.IsAlive());

    holding_something_ = false;
    hold_body_ = 0;

    // Dispatch user messages last now that all is in place.
    if (hold_node_.exists()) {
      hold_node_->DispatchDroppedMessage(this);
    }
    DispatchDropMessage();
  }
}

void SpazNode::CreateHair() {
  // Assume all already exists in this case.
  if (hair_front_right_body_.exists()) return;

  // Front right tuft.
  hair_front_right_body_ =
      Object::New<RigidBody>(kHairFrontRightBodyID, &hair_part_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideAll, RigidBody::kCollideAll);
  hair_front_right_body_->AddCallback(StaticCollideCallback, this);
  hair_front_right_body_->SetDimensions(0.07f, 0.13f, 0, 0, 0, 0, 0.01f);

  hair_front_right_joint_ =
      CreateFixedJoint(body_head_.get(), hair_front_right_body_.get(), 0, 0, 0,
                       0, -0.17f, 0.19f, 0.18f, 0, -0.08f, -0.12f);

  // Rotate it right a bit.
  dQFromAxisAndAngle(hair_front_right_joint_->qrel, 0, 1, 0, -1.1f);

  // Front left tuft.
  hair_front_left_body_ =
      Object::New<RigidBody>(kHairFrontLeftBodyID, &hair_part_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideAll, RigidBody::kCollideAll);
  hair_front_left_body_->AddCallback(StaticCollideCallback, this);
  hair_front_left_body_->SetDimensions(0.04f, 0.13f, 0, 0.07f, 0.13f, 0, 0.01f);

  hair_front_left_joint_ =
      CreateFixedJoint(body_head_.get(), hair_front_left_body_.get(), 0, 0, 0,
                       0, 0.13f, 0.11f, 0.13f, 0, -0.08f, -0.12f);

  // Rotate it left a bit.
  dQFromAxisAndAngle(hair_front_left_joint_->qrel, 0, 1, 0, 1.1f);

  // Pony tail top.
  hair_ponytail_top_body_ =
      Object::New<RigidBody>(kHairPonyTailTopBodyID, &hair_part_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideAll, RigidBody::kCollideAll);
  hair_ponytail_top_body_->AddCallback(StaticCollideCallback, this);
  hair_ponytail_top_body_->SetDimensions(0.09f, 0.1f, 0, 0, 0, 0, 0.01f);

  hair_ponytail_top_joint_ =
      CreateFixedJoint(body_head_.get(), hair_ponytail_top_body_.get(), 0, 0, 0,
                       0, 0, 0.3f, -0.21f, 0, -0.01f, 0.1f);
  // rotate it up a bit..
  dQFromAxisAndAngle(hair_ponytail_top_joint_->qrel, 1, 0, 0, 1.1f);

  // Pony tail bottom.
  hair_ponytail_bottom_body_ =
      Object::New<RigidBody>(kHairPonyTailBottomBodyID, &hair_part_,
                             RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
                             RigidBody::kCollideNone, RigidBody::kCollideNone);
  hair_ponytail_bottom_body_->AddCallback(StaticCollideCallback, this);
  hair_ponytail_bottom_body_->SetDimensions(0.09f, 0.13f, 0, 0, 0, 0, 0.01f);

  hair_ponytail_bottom_joint_ = CreateFixedJoint(
      hair_ponytail_top_body_.get(), hair_ponytail_bottom_body_.get(), 0, 0, 0,
      0, 0, 0.01f, -0.1f, 0, -0.01f, 0.12f);

  // Set joint values.
  UpdateJoints();
}
void SpazNode::DestroyHair() {
  if (hair_front_right_joint_) dJointDestroy(hair_front_right_joint_);
  hair_front_right_joint_ = nullptr;

  if (hair_front_left_joint_) dJointDestroy(hair_front_left_joint_);
  hair_front_left_joint_ = nullptr;

  if (hair_ponytail_top_joint_) dJointDestroy(hair_ponytail_top_joint_);
  hair_ponytail_top_joint_ = nullptr;

  if (hair_ponytail_bottom_joint_) dJointDestroy(hair_ponytail_bottom_joint_);
  hair_ponytail_bottom_joint_ = nullptr;
}

auto SpazNode::GetRollerMaterials() const -> std::vector<Material*> {
  return roller_part_.GetMaterials();
}

void SpazNode::SetRollerMaterials(const std::vector<Material*>& vals) {
  roller_part_.SetMaterials(vals);
}

auto SpazNode::GetExtrasMaterials() const -> std::vector<Material*> {
  return extras_part_.GetMaterials();
}

void SpazNode::SetExtrasMaterials(const std::vector<Material*>& vals) {
  extras_part_.SetMaterials(vals);
  limbs_part_upper_.SetMaterials(vals);
  limbs_part_lower_.SetMaterials(vals);
  hair_part_.SetMaterials(vals);
}

auto SpazNode::GetPunchMaterials() const -> std::vector<Material*> {
  return punch_part_.GetMaterials();
}

void SpazNode::SetPunchMaterials(const std::vector<Material*>& vals) {
  punch_part_.SetMaterials(vals);
}

auto SpazNode::GetPickupMaterials() const -> std::vector<Material*> {
  return pickup_part_.GetMaterials();
}

void SpazNode::SetPickupMaterials(const std::vector<Material*>& vals) {
  pickup_part_.SetMaterials(vals);
}

auto SpazNode::GetMaterials() const -> std::vector<Material*> {
  return spaz_part_.GetMaterials();
}

void SpazNode::SetMaterials(const std::vector<Material*>& vals) {
  spaz_part_.SetMaterials(vals);
}

void SpazNode::SetNameColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for name_color",
                    PyExcType::kValue);
  }
  name_color_ = vals;
}

void SpazNode::set_highlight(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for highlight",
                    PyExcType::kValue);
  }
  highlight_ = vals;
}

void SpazNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;

  // If this gets changed, make sure to change shadow-color in the
  // constructor to match.
  assert(shadow_color_.size() == 3);
  shadow_color_[0] = color_[0] * 0.5f;
  shadow_color_[1] = color_[1] * 0.5f;
  shadow_color_[2] = color_[2] * 0.5f;
}

void SpazNode::SetHurt(float val) {
  float prev_hurt = hurt_;
  hurt_ = std::min(1.0f, val);
  if (prev_hurt != hurt_) {
    last_hurt_change_time_ = scene()->time();
  }
}

void SpazNode::SetFrozen(bool val) {
  frozen_ = val;

  // Hmm; dont remember why this is necessary.
  if (!frozen_) {
    dBodyEnable(body_head_->body());
  }

  // Mark the time when we're newly frozen. We don't shatter based on
  // impulse for a short time thereafter.
  last_shatter_test_time_ = scene()->time();
  UpdateJoints();
}

void SpazNode::SetHaveBoxingGloves(bool val) {
  have_boxing_gloves_ = val;

  // If we just got them (and aren't new ourself) lets flash.
  if (have_boxing_gloves_ && (scene()->time() - birth_time_ > 100)) {
    last_got_boxing_gloves_time_ = scene()->time();
  }
}

void SpazNode::SetIsAreaOfInterest(bool val) {
  // Create if need be.
  if (val && area_of_interest_ == nullptr) {
    area_of_interest_ = g_base->graphics->camera()->NewAreaOfInterest();
    UpdateAreaOfInterest();
  }

  // Destroy if need be.
  if (!val && area_of_interest_) {
    g_base->graphics->camera()->DeleteAreaOfInterest(area_of_interest_);
    area_of_interest_ = nullptr;
  }
}

void SpazNode::SetCurseDeathTime(millisecs_t val) {
  curse_death_time_ = val;

  // Start ticking sound.
  if (curse_death_time_ != 0) {
    if (tick_play_id_ == 0xFFFFFFFF) {
      base::AudioSource* s = g_base->audio->SourceBeginNew();
      if (s) {
        s->SetLooping(true);
        const dReal* p_head = dGeomGetPosition(body_head_->geom());
        s->SetPosition(p_head[0], p_head[1], p_head[2]);
        tick_play_id_ =
            s->Play(g_base->assets->SysSound(base::SysSoundID::kTickingCrazy));
        s->End();
      }
    }
  } else {
    // Stop ticking sound.
    if (tick_play_id_ != 0xFFFFFFFF) {
      g_base->audio->PushSourceStopSoundCall(tick_play_id_);
      tick_play_id_ = 0xFFFFFFFF;
    }
  }
}

void SpazNode::SetShattered(int val) {
  bool was_shattered = (shattered_ != 0);
  shattered_ = val;

  if (shattered_) {
    // Calc which parts are shattered.
    shatter_damage_ = 0;

    float shatter_neck, shatter_pelvis, shatter_upper, shatter_lower;
    // We have a few breakage patterns depending on how we died.

    // Shattering ice or curse explosions generally totally break us up.
    bool extreme = (frozen_ || (shattered_ == 2));
    if (extreme) {
      shatter_neck = 0.95f;
      shatter_pelvis = 0.95f;
      shatter_upper = 0.8f;
      shatter_lower = 0.6f;
    } else if (last_hit_was_punch_) {
      // Punches mostly take heads off or break torsos in half.
      if (Utils::precalc_rand_2((stream_id() * 31 + 112) % kPrecalcRandsCount)
          > 0.3f) {
        shatter_neck = 0.9f;
        shatter_pelvis = 0.1f;
      } else {
        shatter_neck = 0.1f;
        shatter_pelvis = 0.9f;
      }
      shatter_upper = 0.05f;
      shatter_lower = 0.025f;
    } else {
      shatter_neck = 0.9f;
      shatter_pelvis = 0.8f;
      shatter_upper = 0.4f;
      shatter_lower = 0.07f;
    }

    // in kid-friendly mode, don't shatter anything..
    if (explicit_bool(true)) {
      float rand1 =
          Utils::precalc_rand_1((stream_id() * 3 + 1) % kPrecalcRandsCount);
      float rand2 =
          Utils::precalc_rand_2((stream_id() * 2 + 111) % kPrecalcRandsCount);
      float rand3 =
          Utils::precalc_rand_3((stream_id() * 4 + 7) % kPrecalcRandsCount);
      float rand4 =
          Utils::precalc_rand_1((stream_id() * 7 + 78) % kPrecalcRandsCount);
      float rand5 = Utils::precalc_rand_3((stream_id()) % kPrecalcRandsCount);
      float rand6 =
          Utils::precalc_rand_2((stream_id() / 2 + 17) % kPrecalcRandsCount);
      float rand7 =
          Utils::precalc_rand_1((stream_id() * 10) % kPrecalcRandsCount);
      float rand8 =
          Utils::precalc_rand_3((stream_id() * 17 + 2) % kPrecalcRandsCount);
      float rand9 =
          Utils::precalc_rand_2((stream_id() * 13 + 22) % kPrecalcRandsCount);
      float rand10 =
          Utils::precalc_rand_2((stream_id() + 19) % kPrecalcRandsCount);

      // Head/mid-torso are most common losses.
      if (rand1 < shatter_neck) shatter_damage_ |= kNeckJointBroken;
      if (rand2 < shatter_pelvis) shatter_damage_ |= kPelvisJointBroken;

      // Followed by upper arm/leg attaches.
      if (rand3 < shatter_upper) shatter_damage_ |= kUpperRightArmJointBroken;
      if (rand4 < shatter_upper) shatter_damage_ |= kUpperLeftArmJointBroken;
      if (rand5 < shatter_upper) shatter_damage_ |= kUpperRightLegJointBroken;
      if (rand6 < shatter_upper) shatter_damage_ |= kUpperLeftLegJointBroken;

      // Followed by mid arm/leg attaches.
      if (rand7 < shatter_lower) shatter_damage_ |= kLowerRightArmJointBroken;
      if (rand8 < shatter_lower) shatter_damage_ |= kLowerLeftArmJointBroken;
      if (rand9 < shatter_lower) shatter_damage_ |= kLowerRightLegJointBroken;
      if (rand10 < shatter_lower) shatter_damage_ |= kLowerLeftLegJointBroken;
    }

    // Stop any sound we're making if we're shattering.
    if (!was_shattered) {
      g_base->audio->PushSourceStopSoundCall(voice_play_id_);
      if (tick_play_id_ != 0xFFFFFFFF) {
        g_base->audio->PushSourceStopSoundCall(tick_play_id_);
        tick_play_id_ = 0xFFFFFFFF;
      }
    }
  }
}

void SpazNode::SetDead(bool val) {
  bool was_dead = dead_;
  dead_ = val;
  if (dead_ && !was_dead) {
    death_time_ = scene()->time();

    // Lose our area-of-interest.
    if (area_of_interest_) {
      g_base->graphics->camera()->DeleteAreaOfInterest(area_of_interest_);
      area_of_interest_ = nullptr;
    }

    // Drop whatever we're holding.
    DropHeldObject();

    // Scream on death unless we're already doing our fall scream,
    // in which case we just keep on doing that.
    if (voice_play_id_ != fall_play_id_
        || !g_base->audio->IsSoundPlaying(fall_play_id_)) {
      g_base->audio->PushSourceStopSoundCall(voice_play_id_);

      // Only make sound if we're not shattered.
      if (!shattered_) {
        if (SceneSound* sound = GetRandomMedia(death_sounds_)) {
          if (base::AudioSource* source = g_base->audio->SourceBeginNew()) {
            const dReal* p_head = dGeomGetPosition(body_head_->geom());
            source->SetPosition(p_head[0], p_head[1], p_head[2]);
            voice_play_id_ = source->Play(sound->GetSoundData());
            source->End();
          }
        }
      }
    }
    if (tick_play_id_ != 0xFFFFFFFF) {
      g_base->audio->PushSourceStopSoundCall(tick_play_id_);
      tick_play_id_ = 0xFFFFFFFF;
    }
  }
}

void SpazNode::SetStyle(const std::string& val) {
  style_ = val;
  dull_reflection_ = (style_ == "ninja" || style_ == "kronk");
  ninja_ = (style_ == "ninja");
  fat_ = (style_ == "mel" || style_ == "pirate" || style_ == "frosty"
          || style_ == "santa");
  pirate_ = (style_ == "pirate");
  frosty_ = (style_ == "frosty");

  // Start with defaults.
  female_ = false;
  female_hair_ = false;
  eye_ball_color_red_ = 0.46f;
  eye_ball_color_green_ = 0.38f;
  eye_ball_color_blue_ = 0.36f;
  torso_radius_ = 0.15f;
  shoulder_offset_x_ = 0.0f;
  shoulder_offset_y_ = 0.0f;
  shoulder_offset_z_ = 0.0f;
  has_eyelids_ = true;
  eye_scale_ = 1.0f;
  eye_lid_color_red_ = 0.5f;
  eye_lid_color_green_ = 0.3f;
  eye_lid_color_blue_ = 0.2f;
  reflection_scale_ = 0.1f;
  default_eye_lid_angle_ = 0.0f;
  eye_offset_x_ = 0.065f;
  eye_offset_y_ = -0.036f;
  eye_offset_z_ = 0.205f;
  eye_color_red_ = 0.5f;
  eye_color_green_ = 0.5f;
  eye_color_blue_ = 1.2f;
  flippers_ = false;
  wings_ = false;

  if (style_ == "bear") {
    eye_ball_color_red_ = 0.5f;
    eye_ball_color_green_ = 0.5f;
    eye_ball_color_blue_ = 0.5f;
    eye_lid_color_red_ = 0.2f;
    eye_lid_color_green_ = 0.1f;
    eye_lid_color_blue_ = 0.1f;
    eye_color_red_ = 0.0f;
    eye_color_green_ = 0.0f;
    eye_color_blue_ = 0.0f;
    torso_radius_ = 0.25f;
    shoulder_offset_x_ = -0.02f;
    shoulder_offset_y_ = -0.01f;
    shoulder_offset_z_ = 0.01f;
    eye_scale_ = 0.73f;
    has_eyelids_ = false;
    eye_offset_y_ += 0.1f;
    reflection_scale_ = 0.05f;
  } else if (style_ == "penguin") {
    flippers_ = true;
    eye_ball_color_red_ = 0.5f;
    eye_ball_color_green_ = 0.5f;
    eye_ball_color_blue_ = 0.5f;
    eye_lid_color_red_ = 0.1f;
    eye_lid_color_green_ = 0.1f;
    eye_lid_color_blue_ = 0.1f;
    eye_color_red_ = 0.0f;
    eye_color_green_ = 0.0f;
    eye_color_blue_ = 0.0f;
    torso_radius_ = 0.25f;
    shoulder_offset_x_ = -0.02f;
    shoulder_offset_y_ = -0.01f;
    shoulder_offset_z_ = 0.00f;
    eye_scale_ = 0.65f;
    has_eyelids_ = false;
    eye_offset_y_ += 0.05f;
    eye_offset_z_ -= 0.05f;
    reflection_scale_ = 0.2f;
  } else if (style_ == "mel") {
    torso_radius_ = 0.23f;
    shoulder_offset_x_ = -0.04f;
    shoulder_offset_y_ = 0.03f;
    eye_ball_color_red_ = 0.63f;
    eye_ball_color_green_ = 0.53f;
    eye_ball_color_blue_ = 0.49f;
    eye_lid_color_red_ = 0.8f;
    eye_lid_color_green_ = 0.55f;
    eye_lid_color_blue_ = 0.45f;
    eye_offset_x_ += 0.01f;
    eye_offset_y_ += 0.01f;
    eye_offset_z_ -= 0.04f;
    eye_scale_ = 1.05f;
  } else if (style_ == "ninja") {
    eye_lid_color_red_ = 0.5f;
    eye_lid_color_green_ = 0.3f;
    eye_lid_color_blue_ = 0.2f;
    reflection_scale_ = 0.15f;
    default_eye_lid_angle_ = 20.0f;  // angry eyes
    eye_color_red_ = 0.2f;
    eye_color_green_ = 0.1f;
    eye_color_blue_ = 0.0f;
  } else if (style_ == "agent") {
    eyeless_ = true;
    reflection_scale_ = 0.2f;
  } else if (style_ == "cyborg") {
    eyeless_ = true;
    reflection_scale_ = 0.85f;
  } else if (style_ == "santa") {
    eye_scale_ = kSantaEyeScale;
    torso_radius_ = 0.2f;
    shoulder_offset_x_ = -0.04f;
    shoulder_offset_y_ = 0.03f;
    eye_lid_color_red_ = 0.5f;
    eye_lid_color_green_ = 0.4f;
    eye_lid_color_blue_ = 0.3f;
    eye_offset_y_ += 0.02f;
    eye_offset_z_ += kSantaEyeTranslate;
  } else if (style_ == "pirate") {
    torso_radius_ = 0.25f;
    shoulder_offset_x_ = -0.04f;
    shoulder_offset_y_ = 0.03f;
    eye_lid_color_red_ = 0.3f;
    eye_lid_color_green_ = 0.2f;
    eye_lid_color_blue_ = 0.15f;
  } else if (style_ == "kronk") {
    eye_scale_ = 0.8f;
    torso_radius_ = 0.2f;
    shoulder_offset_x_ = -0.03f;
    eye_lid_color_red_ = 0.3f;
    eye_lid_color_green_ = 0.2f;
    eye_lid_color_blue_ = 0.1f;
    default_eye_lid_angle_ = 20.0f;  // angry eyes
  } else if (style_ == "frosty") {
    torso_radius_ = 0.3f;
    shoulder_offset_x_ = -0.04f;
    shoulder_offset_y_ = 0.03f;
  } else if (style_ == "female") {
    female_ = true;
    female_hair_ = true;
    torso_radius_ = 0.11f;
    shoulder_offset_x_ = 0.03f;
    shoulder_offset_z_ = -0.02f;
    eye_lid_color_red_ = 0.6f;
    eye_lid_color_green_ = 0.35f;
    eye_lid_color_blue_ = 0.31f;
    default_eye_lid_angle_ = 15.0f;  // sorta angry eyes
    eye_ball_color_red_ = 0.54f;
    eye_ball_color_green_ = 0.51f;
    eye_ball_color_blue_ = 0.55f;
    eye_color_red_ = 0.55f;
    eye_color_green_ = 0.3f;
    eye_color_blue_ = 0.7f;
    eye_scale_ = 0.95f;
    eye_offset_x_ = 0.08f;
  } else if (style_ == "pixie") {
    wings_ = true;
    female_ = true;
    torso_radius_ = 0.11f;
    shoulder_offset_x_ = 0.03f;
    shoulder_offset_z_ = -0.02f;
    eye_ball_color_red_ = 0.58f;
    eye_ball_color_green_ = 0.55f;
    eye_ball_color_blue_ = 0.6f;
    eye_lid_color_red_ = 0.73f;
    eye_lid_color_green_ = 0.53f;
    eye_lid_color_blue_ = 0.6f;
    default_eye_lid_angle_ = 10.0f;  // sorta angry eyes
    eye_color_red_ = 0.1f;
    eye_color_green_ = 0.3f;
    eye_color_blue_ = 0.1f;
    eye_scale_ = 0.85f;
    eye_offset_z_ = 0.2f;
    eye_offset_y_ = 0.004f;
    eye_offset_x_ = 0.083f;
    reflection_scale_ = 0.35f;
  } else if (style_ == "bones") {
    eyeless_ = true;
    // defaults..
  } else if (style_ == "spaz") {
    // defaults..
  } else if (style_ == "ali") {
    // defaults..
    eyeless_ = true;
    torso_radius_ = 0.11f;
    shoulder_offset_x_ = 0.03f;
    shoulder_offset_y_ = -0.05f;
    reflection_scale_ = 0.25f;
  } else if (style_ == "bunny") {
    torso_radius_ = 0.13f;
    eye_scale_ = 1.2f;
    eye_offset_z_ = 0.05f;
    eye_offset_y_ = -0.08f;
    eye_offset_x_ = 0.07f;
    eye_lid_color_red_ = 0.6f;
    eye_lid_color_green_ = 0.5f;
    eye_lid_color_blue_ = 0.5f;
    eye_ball_color_red_ = 0.6f;
    eye_ball_color_green_ = 0.6f;
    eye_ball_color_blue_ = 0.6f;
    default_eye_lid_angle_ = -5.0f;  // sorta angry eyes
    shoulder_offset_x_ = 0.03f;
    shoulder_offset_y_ = -0.05f;
    reflection_scale_ = 0.02f;
  } else {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Unrecognized spaz style: '" + style_ + "'");
  }
  UpdateBodiesForStyle();
}

auto SpazNode::GetVelocity() const -> std::vector<float> {
  const dReal* v = dBodyGetLinearVel(body_torso_->body());
  std::vector<float> vv(3);
  vv[0] = v[0];
  vv[1] = v[1];
  vv[2] = v[2];
  return vv;
}

auto SpazNode::GetPositionForward() const -> std::vector<float> {
  dVector3 p_forward;
  dBodyGetRelPointPos(body_torso_->body(), 0, 0.2f, -0.2f, p_forward);
  std::vector<float> vals(3);
  vals[0] = p_forward[0] + body_torso_->blend_offset().x;
  vals[1] = p_forward[1] + body_torso_->blend_offset().y;
  vals[2] = p_forward[2] + body_torso_->blend_offset().z;
  return vals;
}

auto SpazNode::GetPositionCenter() const -> std::vector<float> {
  const dReal* p2 = dGeomGetPosition(body_torso_->geom());
  const dReal* p3 = dGeomGetPosition(body_head_->geom());
  std::vector<float> vals(3);
  if (shattered_) {
    vals[0] = p2[0] + body_torso_->blend_offset().x;
    vals[1] = p2[1] + body_torso_->blend_offset().y;
    vals[2] = p2[2] + body_torso_->blend_offset().z;
  } else {
    vals[0] = (p2[0] + body_torso_->blend_offset().x) * 0.7f
              + (p3[0] + body_head_->blend_offset().x) * 0.3f;
    vals[1] = (p2[1] + body_torso_->blend_offset().y) * 0.7f
              + (p3[1] + body_head_->blend_offset().y) * 0.3f;
    vals[2] = (p2[2] + body_torso_->blend_offset().z) * 0.7f
              + (p3[2] + body_head_->blend_offset().z) * 0.3f;
  }
  return vals;
}

auto SpazNode::GetPunchPosition() const -> std::vector<float> {
  if (!body_punch_.exists()) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: querying spaz punch_position without punch body");
    return {0.0f, 0.0f, 0.0f};
  }
  std::vector<float> vals(3);
  const dReal* p = dGeomGetPosition(body_punch_->geom());
  vals[0] = p[0];
  vals[1] = p[1];
  vals[2] = p[2];
  return vals;
}

auto SpazNode::GetPunchVelocity() const -> std::vector<float> {
  if (!body_punch_.exists()) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: querying spaz punch_velocity without punch body");
    return {0.0f, 0.0f, 0.0f};
  }
  std::vector<float> vals(3);
  const dReal* p = dGeomGetPosition(body_punch_->geom());
  dVector3 v;
  dBodyGetPointVel(
      (punch_right_ ? lower_right_arm_body_ : lower_left_arm_body_)->body(),
      p[0], p[1], p[2], v);
  vals[0] = v[0];
  vals[1] = v[1];
  vals[2] = v[2];
  return vals;
}

auto SpazNode::GetPunchMomentumLinear() const -> std::vector<float> {
  if (!body_punch_.exists()) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: querying spaz punch_velocity without punch body");
    return {0.0f, 0.0f, 0.0f};
  }
  std::vector<float> vals(3);

  // Our linear punch momentum is our base velocity with punchmomentumlinear
  // as magnitude.
  const dReal* vel = dBodyGetLinearVel(body_torso_->body());
  float vel_mag = sqrtf(vel[0] * vel[0] + vel[1] * vel[1] + vel[2] * vel[2]);
  if (vel_mag < 0.01f) {
    vals[0] = vals[1] = vals[2] = 0;
  } else {
    vel_mag = punch_momentum_linear_ / vel_mag;
    vals[0] = vel[0] * vel_mag;
    vals[1] = vel[1] * vel_mag;
    vals[2] = vel[2] * vel_mag;
  }
  return vals;
}

auto SpazNode::GetTorsoPosition() const -> std::vector<float> {
  const dReal* p = dGeomGetPosition(body_torso_->geom());
  std::vector<float> vals(3);
  vals[0] = p[0] + body_torso_->blend_offset().x;
  vals[1] = p[1] + body_torso_->blend_offset().y;
  vals[2] = p[2] + body_torso_->blend_offset().z;
  return vals;
}

auto SpazNode::GetPosition() const -> std::vector<float> {
  const dReal* p = dGeomGetPosition(body_roller_->geom());
  std::vector<float> vals(3);
  vals[0] = p[0] + body_roller_->blend_offset().x;
  vals[1] = p[1] + body_roller_->blend_offset().y;
  vals[2] = p[2] + body_roller_->blend_offset().z;
  return vals;
}

void SpazNode::SetHoldNode(Node* val) {
  // They passed a node.
  if (val != nullptr) {
    Node* a = val;
    assert(a);
    RigidBody* b = a->GetRigidBody(hold_body_);
    if (!b) {
      // Print some debugging info on the active collision.
      {
        Dynamics* dynamics = scene()->dynamics();
        assert(dynamics);
        Collision* c = dynamics->active_collision();
        if (c) {
          g_core->logging->Log(
              LogName::kBa, LogLevel::kError,
              "SRC NODE: " + ObjToString(dynamics->GetActiveCollideSrcNode()));
          g_core->logging->Log(
              LogName::kBa, LogLevel::kError,
              "OPP NODE: " + ObjToString(dynamics->GetActiveCollideDstNode()));
          g_core->logging->Log(
              LogName::kBa, LogLevel::kError,
              "SRC BODY "
                  + std::to_string(dynamics->GetCollideMessageReverseOrder()
                                       ? c->body_id_1
                                       : c->body_id_2));
          g_core->logging->Log(
              LogName::kBa, LogLevel::kError,
              "OPP BODY "
                  + std::to_string(dynamics->GetCollideMessageReverseOrder()
                                       ? c->body_id_2
                                       : c->body_id_1));
          g_core->logging->Log(
              LogName::kBa, LogLevel::kError,
              "REVERSE "
                  + std::to_string(dynamics->GetCollideMessageReverseOrder()));
        } else {
          g_core->logging->Log(LogName::kBa, LogLevel::kError,
                               "<NO ACTIVE COLLISION>");
        }
      }
      throw Exception("specified hold_body (" + std::to_string(hold_body_)
                      + ") not found on hold_node: "
                      + a->GetObjectDescription());
    }

    hold_node_ = val;
    holding_something_ = true;
    last_pickup_time_ = scene()->time();

    assert(a && b);
    {
      g_base->audio->PushSourceStopSoundCall(voice_play_id_);
      if (SceneSound* sound = GetRandomMedia(pickup_sounds_)) {
        if (auto* source = g_base->audio->SourceBeginNew()) {
          const dReal* p_head = dGeomGetPosition(body_head_->geom());
          source->SetPosition(p_head[0], p_head[1], p_head[2]);
          voice_play_id_ = source->Play(sound->GetSoundData());
          source->End();
        }
      }

      float hold_height = 1.08f;
      float hold_forward = -0.05f;
      float hold_handle[3];
      float hold_handle2[3];

      dBodyID b1 = body_torso_->body();
      dBodyID b2 = b->body();
      const dReal* p1 = dBodyGetPosition(b1);
      const dReal* p2 = dBodyGetPosition(b2);
      const dReal* q1 = dBodyGetQuaternion(b1);
      const dReal* q2 = dBodyGetQuaternion(b2);
      dReal p1_old[3];
      dReal p2_old[3];
      dReal q1_old[4];
      dReal q2_old[4];
      for (int i = 0; i < 3; i++) {
        p1_old[i] = p1[i];
        p2_old[i] = p2[i];
      }
      for (int i = 0; i < 4; i++) {
        q1_old[i] = q1[i];
        q2_old[i] = q2[i];
      }

      a->GetRigidBodyPickupLocations(hold_body_, hold_handle, hold_handle2,
                                     hold_hand_offset_right_,
                                     hold_hand_offset_left_);

      // Hand locations are relative to object pickup location.. add that
      // in.
      hold_hand_offset_right_[0] += hold_handle[0];
      hold_hand_offset_right_[1] += hold_handle[1];
      hold_hand_offset_right_[2] += hold_handle[2];
      hold_hand_offset_left_[0] += hold_handle[0];
      hold_hand_offset_left_[1] += hold_handle[1];
      hold_hand_offset_left_[2] += hold_handle[2];

      dBodySetPosition(b1, -hold_handle2[0], -hold_handle2[1],
                       -hold_handle2[2]);
      dBodySetPosition(b2, -hold_handle[0], hold_height - hold_handle[1],
                       hold_forward - hold_handle[2]);
      dQuaternion q;
      dQSetIdentity(q);
      dBodySetQuaternion(b1, q);
      dBodySetQuaternion(b2, q);
      auto* j = static_cast<dxJointFixed*>(
          dJointCreateFixed(scene()->dynamics()->ode_world(), nullptr));
      pickup_joint_.SetJoint(j, scene());

      pickup_joint_.AttachToBodies(body_torso_.get(), b);
      dJointSetFixed(j);
      dJointSetFixedSpringMode(j, 1, 1, true);
      dJointSetFixedAnchor(j, 0, hold_height, hold_forward, false);
      dJointSetFixedParam(j, dParamLinearStiffness, 180);
      dJointSetFixedParam(j, dParamLinearDamping, 10);

      dJointSetFixedParam(j, dParamAngularStiffness, 4.0f);
      dJointSetFixedParam(j, dParamAngularDamping, 0.3f);

      {
        pickup_pos_1_[0] = p1_old[0];
        pickup_pos_1_[1] = p1_old[1];
        pickup_pos_1_[2] = p1_old[2];
        pickup_pos_2_[0] = p2_old[0];
        pickup_pos_2_[1] = p2_old[1];
        pickup_pos_2_[2] = p2_old[2];
        for (int i = 0; i < 4; i++) {
          pickup_q1_[i] = q1_old[i];
          pickup_q2_[i] = q2_old[i];
        }
      }

      dBodySetPosition(b1, p1_old[0], p1_old[1], p1_old[2]);
      dBodySetPosition(b2, p2_old[0], p2_old[1], p2_old[2]);
      dBodySetQuaternion(b1, q1_old);
      dBodySetQuaternion(b2, q2_old);
    }
    // Inform userland objects that they're picking up or have been picked
    // up.
    DispatchPickUpMessage(a);
    a->DispatchPickedUpMessage(this);
  } else {
    // User is clearing hold-node; just drop whatever we're holding.
    DropHeldObject();
  }
}

auto SpazNode::GetJumpSounds() const -> std::vector<SceneSound*> {
  return RefsToPointers(jump_sounds_);
}
void SpazNode::SetJumpSounds(const std::vector<SceneSound*>& vals) {
  jump_sounds_ = PointersToRefs(vals);
}
auto SpazNode::GetAttackSounds() const -> std::vector<SceneSound*> {
  return RefsToPointers(attack_sounds_);
}
void SpazNode::SetAttackSounds(const std::vector<SceneSound*>& vals) {
  attack_sounds_ = PointersToRefs(vals);
}
auto SpazNode::GetImpactSounds() const -> std::vector<SceneSound*> {
  return RefsToPointers(impact_sounds_);
}
void SpazNode::SetImpactSounds(const std::vector<SceneSound*>& vals) {
  impact_sounds_ = PointersToRefs(vals);
}
auto SpazNode::GetDeathSounds() const -> std::vector<SceneSound*> {
  return RefsToPointers(death_sounds_);
}
void SpazNode::SetDeathSounds(const std::vector<SceneSound*>& vals) {
  death_sounds_ = PointersToRefs(vals);
}

auto SpazNode::GetPickupSounds() const -> std::vector<SceneSound*> {
  return RefsToPointers(pickup_sounds_);
}
void SpazNode::SetPickupSounds(const std::vector<SceneSound*>& vals) {
  pickup_sounds_ = PointersToRefs(vals);
}

void SpazNode::SetFallSounds(const std::vector<SceneSound*>& vals) {
  fall_sounds_ = PointersToRefs(vals);
}

auto SpazNode::GetResyncDataSize() -> int {
  // 1 float for roll_amt_
  return 4;
}

auto SpazNode::GetResyncData() -> std::vector<uint8_t> {
  std::vector<uint8_t> data(4, 0);
  char* ptr = reinterpret_cast<char*>(&(data[0]));
  Utils::EmbedFloat32(&ptr, roll_amt_);
  return data;
}

void SpazNode::ApplyResyncData(const std::vector<uint8_t>& data) {
  const char* ptr = reinterpret_cast<const char*>(&(data[0]));
  roll_amt_ = Utils::ExtractFloat32(&ptr);
}

void SpazNode::PlayHurtSound() {
  if (dead_ || invincible_) {
    return;
  }
  if (SceneSound* sound = GetRandomMedia(impact_sounds_)) {
    if (auto* source = g_base->audio->SourceBeginNew()) {
      const dReal* p_top = dGeomGetPosition(body_head_->geom());
      g_base->audio->PushSourceStopSoundCall(voice_play_id_);
      source->SetPosition(p_top[0], p_top[1], p_top[2]);
      voice_play_id_ = source->Play(sound->GetSoundData());
      source->End();
    }
  }
}

}  // namespace ballistica::scene_v1
