// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/spaz_node.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_package_registry.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/post_process_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_object_split.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/area_of_interest.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/collision.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/node/globals_node.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"
#include "ode/ode_collision_util.h"

namespace ballistica::scene_v1 {

// Base load-shedding skip for definition attachment rigs (fraction of
// sim steps skipped; see BGDynamicsCharacterKind::Input::skip). The
// engine's emergency lever (BGDynamics::load_skip) adds to this.
const float kBGAttachmentSkip = 0.0f;

// Prototype bg limbs switch (defined with the rig config builder below).
// Limb body indices, as laid out by BuildLimbRigConfig_.
enum LimbIndex {
  kLimbUpperRightArm,
  kLimbLowerRightArm,
  kLimbUpperLeftArm,
  kLimbLowerLeftArm,
  kLimbUpperRightLeg,
  kLimbLowerRightLeg,
  kLimbUpperLeftLeg,
  kLimbLowerLeftLeg,
  kLimbRightToes,
  kLimbLeftToes,
  kLimbCount
};
// Points on the lower limb that the upper limb's mesh stretches to
// reach (the lower joint's anchor2; the main-sim rig's construction
// values).
const Vector3f kArmStretchPoint{0.0f, 0.0f, -0.1f};
const Vector3f kLegStretchPoint{0.0f, 0.0f, -0.05f};

// Initial limb joint targets when there are no main-sim limb joints to
// read them from (bg limbs): what the constructor's joint creation
// produces from the Stand() placement (anchor1 = the child's origin in
// the parent's frame, plus the explicit tweaks made there), in
// SpazJoint order from kSpazJointUpperRightArm. Debug builds check
// this table against the real joints whenever they do exist.
struct LimbJointSeed {
  float anchor1[3];
  float qrel_x_angle;  // Rest rotation about x (0 = identity).
  float linear_stiffness;
  float linear_damping;
};
const int kLimbJointSeedCount = kSpazJointCount - kSpazJointUpperRightArm;
const LimbJointSeed kLimbJointSeeds[kLimbJointSeedCount] = {
    {{-0.17f, 0.1f, 0.0f}, 0.0f, 0.0f, 0.0f},    // upper right arm
    {{0.0f, 0.0f, 0.07f}, 0.0f, 0.0f, 0.0f},     // lower right arm
    {{0.17f, 0.1f, 0.0f}, 0.0f, 0.0f, 0.0f},     // upper left arm
    {{0.0f, 0.0f, 0.07f}, 0.0f, 0.0f, 0.0f},     // lower left arm
    {{-0.1f, -0.01f, 0.0f}, 0.0f, 0.0f, 0.0f},   // upper right leg
    {{0.0f, 0.0f, 0.05f}, 0.0f, 0.0f, 0.0f},     // lower right leg
    {{0.1f, -0.01f, 0.0f}, 0.0f, 0.0f, 0.0f},    // upper left leg
    {{0.0f, 0.0f, 0.05f}, 0.0f, 0.0f, 0.0f},     // lower left leg
    {{0.0f, 0.05f, 0.05f}, 0.0f, 0.0f, 0.0f},    // right toes
    {{-0.1f, 0.05f, 0.05f}, 0.0f, 0.0f, 0.0f},   // right toes 2
    {{0.0f, 0.05f, 0.05f}, 0.0f, 0.0f, 0.0f},    // left toes
    {{0.1f, 0.05f, 0.05f}, 0.0f, 0.0f, 0.0f},    // left toes 2
    {{-0.1f, -0.4f, 0.0f}, 1.0f, 0.3f, 0.001f},  // right leg ik
    {{0.1f, -0.4f, 0.0f}, 1.0f, 0.3f, 0.001f},   // left leg ik
    {{-0.2f, -0.2f, 0.1f}, 0.0f, 0.0f, 0.0f},    // right arm ik
    {{0.2f, -0.2f, 0.1f}, 0.0f, 0.0f, 0.0f},     // left arm ik
};

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

// Pull a random pointer from a ref-vector.
template <class T>
auto GetRandomMedia(const std::vector<Object::Ref<T> >& list) -> T* {
  if (list.empty()) return nullptr;
  return list[rand() % list.size()].get();  // NOLINT yes I know; rand bad.
}

const float kSantaEyeScale = 0.9f;
const float kSantaEyeTranslate = 0.03f;

const float kRollerBallLinearStiffness = 1000.0f;
const float kRollerBallLinearDamping = 0.2f;

const float kPelvisDensity = 5.0f;

const float kUpperLegDensity = 2.0f;
const float kUpperLegCollideStiffness = 100.0f;
const float kUpperLegCollideDamping = 100.0f;

const float kLowerLegDensity = 2.0f;
const float kLowerLegCollideStiffness = 100.0f;
const float kLowerLegCollideDamping = 100.0f;

const float kToesDensity = 0.5f;
const float kToesCollideStiffness = 10.0f;
const float kToesCollideDamping = 10.0f;

const float kUpperArmDensity = 2.0f;

const float kLowerArmDensity = 2.0f;

// bg-limbs mode (protocol 44+): the arm and leg bodies live on the
// bg-dynamics rig, so the main-sim core carries their mass instead.
// The old rig totalled 1.392 (arms 0.109, legs + toes 0.104); the arms'
// share goes to the torso via density, the legs' to a taller pelvis
// mass box (0.16 -> 0.264; same 0.25 x 0.16 footprint, mass 0.160 ->
// 0.264), which also restores some tipping inertia. Mass also scales
// area-blast damage (RigidBody::ApplyImpulse), so this closes part of
// the missing-limb damage gap too. Main-sim-limbs mode keeps the old
// values byte-for-byte; these only apply under !main_sim_limbs_.
const float kBgLimbsTorsoDensity = 3.65f;
const float kBgLimbsPelvisMassHeight = 0.264f;
// Wider pelvis collision box (0.25 -> 0.32; mass box unchanged) so a
// ragdoll lying on it rolls less. Collision only: mass and inertia
// come from the mass triple above.
const float kBgLimbsPelvisWidth = 0.35f;

// bg-limbs mode: the roller ball doubles as the leg surrogate when the
// character is knocked out or frozen. The old rig let the ball vanish
// (size 0, retracted 0.3 up, contacts rejected) and the main-sim legs
// took over as what the body landed on: a frozen character sank onto
// locked legs and toppled, a ragdoll landed legs-first. The rig's legs
// are display-only, so instead the ball only shrinks to this size
// (0.4 -> radius 0.138) and is placed so its bottom sits
// kBgLimbsDownBallBottomLift above the standing ball's bottom instead
// of retracting (0.108 is where a 0.6 ball with no offset sat, the
// first tuning that felt right), and its floor contacts go soft so it
// cushions the drop and
// then sinks under body weight instead of propping a lying ragdoll's
// hips up. Not meant to keep anyone upright: freezing zeroes balance_,
// so the statue topples naturally like it used to. Main-sim-limbs mode
// keeps the old behavior byte-for-byte.
const float kBgLimbsDownBallSize = 0.4f;
const float kBgLimbsDownBallBottomLift = 0.108f;
const float kBgLimbsDownBallStiffness = 400.0f;
const float kBgLimbsDownBallDamping = 2.0f;
// Lock the ball to the torso (full brakes) while knocked out; tried
// and set aside 2026-09-08 (the free ball read better).
const bool kBgLimbsDownBallBrakes = false;

// Per-attachment-type physique: capsule dims, mass, joint anchors,
// spring stiffness/damping, and collision behavior. These are sim
// state -- every peer derives identical bodies from a definition --
// and the values are exactly the classic Zoe hair rig's, so
// definition-form hair matches the legacy bool-driven rig body for
// body. Mirrors AttachmentType in bamaster baserver/character.py.
struct AttachmentSegmentSpec {
  float geom_radius;
  float geom_length;
  float mass_radius;  // 0 = geom value.
  float mass_length;  // 0 = geom value.
  float density;
  // In the previous segment's frame (segment 0 anchors at the
  // attachment's head-local position instead).
  float parent_anchor[3];
  float child_anchor[3];
  float linear_stiffness;
  float linear_damping;
  float angular_stiffness;
  float angular_damping;
  uint32_t collide;
};
struct AttachmentTypeSpec {
  int segment_count;
  AttachmentSegmentSpec segments[4];
};
const AttachmentTypeSpec kAttachmentTypeSpecs[] = {
    // kLegacyTuftLarge (the classic front-right tuft).
    {1,
     {{0.07f,
       0.13f,
       0.0f,
       0.0f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, -0.08f, -0.12f},
       0.2f,
       0.01f,
       0.00025f,
       0.000001f,
       RigidBody::kCollideAll}}},
    // kLegacyTuftMedium (capsule midway between large and small; mass and
    // springs are identical across the tuft sizes).
    {1,
     {{0.055f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, -0.08f, -0.12f},
       0.2f,
       0.01f,
       0.00025f,
       0.000001f,
       RigidBody::kCollideAll}}},
    // kLegacyTuftSmall (front-left; smaller capsule, same mass).
    {1,
     {{0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, -0.08f, -0.12f},
       0.2f,
       0.01f,
       0.00025f,
       0.000001f,
       RigidBody::kCollideAll}}},
    // kLegacyPonytail2 (stiffer root + floppy tip that collides with
    // nothing; the tip chains off the root, so rotating the whole
    // attachment carries the chain with it).
    {2,
     {{0.09f,
       0.1f,
       0.0f,
       0.0f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, -0.01f, 0.1f},
       1.0f,
       0.03f,
       0.0015f,
       0.000003f,
       RigidBody::kCollideAll},
      {0.09f,
       0.13f,
       0.0f,
       0.0f,
       0.01f,
       {0.0f, 0.01f, -0.1f},
       {0.0f, -0.01f, 0.12f},
       0.4f,
       0.02f,
       0.00025f,
       0.000001f,
       RigidBody::kCollideNone}}},
    // kAntenna (antennas, ears, horns: the kLegacyTuftSmall body with 8x
    // the tuft linear/angular spring stiffness, so it mostly holds
    // its pose with a little life). Unlike the tufts' hair-shaped
    // child anchor, the base sits squarely at the capsule's root end
    // so the capsule extends straight out along the attachment's aim
    // from wherever it is anchored.
    {1,
     {{0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll}}},
    // kAntenna2 (two-segment kAntenna chain; each joint hinges at the
    // center of the touching end-cap spheres, so the chain reads as a
    // string of balls-and-rods).
    {2,
     {{0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll},
      {0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.065f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll}}},
    // kAntenna3 (three-segment kAntenna chain; see kAntenna2).
    {3,
     {{0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll},
      {0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.065f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll},
      {0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.065f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll}}},
    // kAntenna4 (four-segment kAntenna chain; see kAntenna2).
    {4,
     {{0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.0f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll},
      {0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.065f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll},
      {0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.065f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll},
      {0.04f,
       0.13f,
       0.07f,
       0.13f,
       0.01f,
       {0.0f, 0.0f, 0.065f},
       {0.0f, 0.0f, -0.065f},
       0.8f,
       0.0005f,
       0.00001f,
       0.00000001f,
       RigidBody::kCollideAll}}},
};

const int kPunchDuration = 35;
const int kPickupCooldown = 40;
const int kPickupHitboxDelay = 4;

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

#if !BA_HEADLESS_BUILD
class SpazNode::FullShadowSet : public Object {
 public:
  explicit FullShadowSet(base::BGDynamicsWorld* world)
      : torso_shadow_(world),
        head_shadow_(world),
        pelvis_shadow_(world),
        lower_left_leg_shadow_(world),
        lower_right_leg_shadow_(world),
        upper_left_leg_shadow_(world),
        upper_right_leg_shadow_(world),
        lower_left_arm_shadow_(world),
        lower_right_arm_shadow_(world),
        upper_left_arm_shadow_(world),
        upper_right_arm_shadow_(world) {}
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
  explicit SimpleShadowSet(base::BGDynamicsWorld* world) : shadow_(world) {}
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
  BA_BOOL_ATTR_READONLY(pickup_before_hitbox, get_pickup_before_hitbox);
  BA_FLOAT_ATTR_READONLY(pickup_release_time_ms, get_pickup_release_time_ms);
  // (protocol 44) Appended last per the standing wire-index rule.
  BA_SPAZ_DEF_ATTR(spaz_def, spaz_def, SetSpazDef);
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
        behavior_version(this),
        pickup_before_hitbox(this),
        pickup_release_time_ms(this),
        spaz_def(this) {}
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
  // Limb backend, fixed for our lifetime: main-sim limb bodies, or
  // none at all with the bg rig carrying them.
  main_sim_limbs_ = !UseBgLimbs_();

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

  if (main_sim_limbs_) {
    // Upper Right Arm
    upper_right_arm_body_ = Object::New<RigidBody>(
        kUpperRightArmBodyID, &limbs_part_upper_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    upper_right_arm_body_->AddCallback(StaticCollideCallback, this);
    upper_right_arm_body_->SetDimensions(0.06f, 0.16f, 0, 0, 0, 0,
                                         kUpperArmDensity);

    // Lower Right Arm
    lower_right_arm_body_ = Object::New<RigidBody>(
        kLowerRightArmBodyID, &limbs_part_lower_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    lower_right_arm_body_->AddCallback(StaticCollideCallback, this);
    lower_right_arm_body_->SetDimensions(0.06f, 0.13f, 0, 0.06f, 0.16f, 0,
                                         kLowerArmDensity);

    // Upper Left Arm
    upper_left_arm_body_ = Object::New<RigidBody>(
        kUpperLeftArmBodyID, &limbs_part_upper_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    upper_left_arm_body_->AddCallback(StaticCollideCallback, this);
    upper_left_arm_body_->SetDimensions(0.06f, 0.16f, 0, 0, 0, 0,
                                        kUpperArmDensity);

    // Lower Left Arm
    lower_left_arm_body_ = Object::New<RigidBody>(
        kLowerLeftArmBodyID, &limbs_part_lower_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    lower_left_arm_body_->AddCallback(StaticCollideCallback, this);
    lower_left_arm_body_->SetDimensions(0.06f, 0.13f, 0, 0.06f, 0.16f, 0,
                                        kLowerArmDensity);

    // Upper Right Leg
    upper_right_leg_body_ = Object::New<RigidBody>(
        kUpperRightLegBodyID, &limbs_part_upper_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    upper_right_leg_body_->AddCallback(StaticCollideCallback, this);

    // Lower Right leg
    lower_right_leg_body_ = Object::New<RigidBody>(
        kLowerRightLegBodyID, &limbs_part_lower_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    lower_right_leg_body_->AddCallback(StaticCollideCallback, this);

    right_toes_body_ = Object::New<RigidBody>(
        kRightToesBodyID, &limbs_part_lower_, RigidBody::Type::kBody,
        RigidBody::Shape::kSphere, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    right_toes_body_->AddCallback(StaticCollideCallback, this);
    right_toes_body_->SetDimensions(0.075f, 0, 0, 0, 0, 0, kToesDensity);

    // Upper Left Leg
    upper_left_leg_body_ = Object::New<RigidBody>(
        kUpperLeftLegBodyID, &limbs_part_upper_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    upper_left_leg_body_->AddCallback(StaticCollideCallback, this);

    // Lower Left leg
    lower_left_leg_body_ = Object::New<RigidBody>(
        kLowerLeftLegBodyID, &limbs_part_lower_, RigidBody::Type::kBody,
        RigidBody::Shape::kCapsule, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    lower_left_leg_body_->AddCallback(StaticCollideCallback, this);

    // Left Toes
    left_toes_body_ = Object::New<RigidBody>(
        kLeftToesBodyID, &limbs_part_lower_, RigidBody::Type::kBody,
        RigidBody::Shape::kSphere, RigidBody::kCollideActive,
        RigidBody::kCollideAll);
    left_toes_body_->AddCallback(StaticCollideCallback, this);
    left_toes_body_->SetDimensions(0.075f, 0, 0, 0, 0, 0, kToesDensity);
  }

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

  if (main_sim_limbs_) {
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

    left_arm_ik_joint_ = CreateFixedJoint(
        body_torso_.get(), lower_left_arm_body_.get(), 0.0f, 0.0f, 0, 0, 0.2f,
        -0.2f, 0.1f, 0.0f, 0.0f, 0.07f, false);
  }

  // Every driven joint now exists; seed the targets from them.
  InitJointTargets_();

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
      if ((pickup_ == 0) && (!knockout_) && (!frozen_)) {
        pickup_ = kPickupCooldown + kPickupHitboxDelay;
        pickup_before_hitbox_ = true;
      }
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
        if (base::SoundAsset* sound = RandomAttackSound_()) {
          if (auto* source = scene()->NewAudioSource()) {
            const dReal* p_head = dGeomGetPosition(body_head_->geom());
            g_base->audio->PushSourceStopSoundCall(voice_play_id_);
            source->SetPosition(p_head[0], p_head[1], p_head[2]);
            voice_play_id_ = source->Play(sound);
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
      if (base::SoundAsset* sound = RandomJumpSound_()) {
        if (auto* source = scene()->NewAudioSource()) {
          const dReal* p_top = dGeomGetPosition(body_head_->geom());
          g_base->audio->PushSourceStopSoundCall(voice_play_id_);
          source->SetPosition(p_top[0], p_top[1], p_top[2]);
          voice_play_id_ = source->Play(sound);
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

static void FreezeJointAngle(base::JointFixedEF* j) {
  base::JointFixedEFFreezeAngle(j);
}

auto SpazNode::PoseJoints_() -> SpazPose::Joints {
  SpazPose::Joints j;
  SpazJointTarget* tg = joint_targets_;
  j.neck = &tg[kSpazJointNeck];
  j.pelvis = &tg[kSpazJointPelvis];
  j.upper_right_arm = &tg[kSpazJointUpperRightArm];
  j.lower_right_arm = &tg[kSpazJointLowerRightArm];
  j.upper_left_arm = &tg[kSpazJointUpperLeftArm];
  j.lower_left_arm = &tg[kSpazJointLowerLeftArm];
  j.upper_right_leg = &tg[kSpazJointUpperRightLeg];
  j.lower_right_leg = &tg[kSpazJointLowerRightLeg];
  j.upper_left_leg = &tg[kSpazJointUpperLeftLeg];
  j.lower_left_leg = &tg[kSpazJointLowerLeftLeg];
  j.right_toes = &tg[kSpazJointRightToes];
  j.right_toes_2 = &tg[kSpazJointRightToes2];
  j.left_toes = &tg[kSpazJointLeftToes];
  j.left_toes_2 = &tg[kSpazJointLeftToes2];
  j.right_leg_ik = &tg[kSpazJointRightLegIK];
  j.left_leg_ik = &tg[kSpazJointLeftLegIK];
  j.right_arm_ik = &tg[kSpazJointRightArmIK];
  j.left_arm_ik = &tg[kSpazJointLeftArmIK];
  return j;
}

auto SpazNode::SimJoint_(int joint) -> base::JointFixedEF* {
  switch (joint) {
    case kSpazJointNeck:
      return neck_joint_;
    case kSpazJointPelvis:
      return pelvis_joint_;
    case kSpazJointUpperRightArm:
      return upper_right_arm_joint_;
    case kSpazJointLowerRightArm:
      return lower_right_arm_joint_;
    case kSpazJointUpperLeftArm:
      return upper_left_arm_joint_;
    case kSpazJointLowerLeftArm:
      return lower_left_arm_joint_;
    case kSpazJointUpperRightLeg:
      return upper_right_leg_joint_;
    case kSpazJointLowerRightLeg:
      return lower_right_leg_joint_;
    case kSpazJointUpperLeftLeg:
      return upper_left_leg_joint_;
    case kSpazJointLowerLeftLeg:
      return lower_left_leg_joint_;
    case kSpazJointRightToes:
      return right_toes_joint_;
    case kSpazJointRightToes2:
      return right_toes_joint_2_;
    case kSpazJointLeftToes:
      return left_toes_joint_;
    case kSpazJointLeftToes2:
      return left_toes_joint_2_;
    case kSpazJointRightLegIK:
      return right_leg_ik_joint_;
    case kSpazJointLeftLegIK:
      return left_leg_ik_joint_;
    case kSpazJointRightArmIK:
      return right_arm_ik_joint_;
    case kSpazJointLeftArmIK:
      return left_arm_ik_joint_;
    default:
      return nullptr;
  }
}

void SpazNode::InitJointTargets_() {
  for (int i = 0; i < kSpazJointCount; ++i) {
    base::JointFixedEF* j = SimJoint_(i);
    SpazJointTarget& tg = joint_targets_[i];
    if (!j) {
      // No main-sim joint (bg limbs): seed what its creation would
      // have produced.
      assert(i >= kSpazJointUpperRightArm);
      const LimbJointSeed& seed = kLimbJointSeeds[i - kSpazJointUpperRightArm];
      for (int k = 0; k < 3; ++k) {
        tg.anchor1[k] = seed.anchor1[k];
      }
      dQFromAxisAndAngle(tg.qrel, 1, 0, 0, seed.qrel_x_angle);
      tg.linearStiffness = seed.linear_stiffness;
      tg.linearDamping = seed.linear_damping;
      tg.angularStiffness = 0.0f;
      tg.angularDamping = 0.0f;
      continue;
    }
    for (int k = 0; k < 3; ++k) {
      tg.anchor1[k] = j->anchor1[k];
    }
    for (int k = 0; k < 4; ++k) {
      tg.qrel[k] = j->qrel[k];
    }
    tg.linearStiffness = j->linearStiffness;
    tg.linearDamping = j->linearDamping;
    tg.angularStiffness = j->angularStiffness;
    tg.angularDamping = j->angularDamping;
#if BA_DEBUG_BUILD
    // Keep the bg-limbs seed table honest against the real thing.
    if (i >= kSpazJointUpperRightArm) {
      const LimbJointSeed& seed = kLimbJointSeeds[i - kSpazJointUpperRightArm];
      dQuaternion q;
      dQFromAxisAndAngle(q, 1, 0, 0, seed.qrel_x_angle);
      for (int k = 0; k < 3; ++k) {
        assert(std::abs(tg.anchor1[k] - seed.anchor1[k]) < 1e-4f);
      }
      for (int k = 0; k < 4; ++k) {
        assert(std::abs(tg.qrel[k] - q[k]) < 1e-4f);
      }
      assert(std::abs(tg.linearStiffness - seed.linear_stiffness) < 1e-6f);
      assert(std::abs(tg.linearDamping - seed.linear_damping) < 1e-6f);
      assert(tg.angularStiffness == 0.0f && tg.angularDamping == 0.0f);
    }
#endif
  }
}

void SpazNode::ApplyJointTargets_() {
  for (int i = 0; i < kSpazJointCount; ++i) {
    base::JointFixedEF* j = SimJoint_(i);
    if (!j) {
      continue;  // bg limbs: the rig applies these.
    }
    const SpazJointTarget& tg = joint_targets_[i];
    for (int k = 0; k < 3; ++k) {
      j->anchor1[k] = tg.anchor1[k];
    }
    for (int k = 0; k < 4; ++k) {
      j->qrel[k] = tg.qrel[k];
    }
    j->linearStiffness = tg.linearStiffness;
    j->linearDamping = tg.linearDamping;
    j->angularStiffness = tg.angularStiffness;
    j->angularDamping = tg.angularDamping;
  }
}

void SpazNode::UpdateJoints() {
  // Limb rest pose and springs (or the frozen lock-down).
  pose_.ApplyRestPose(PoseJoints_(), frozen_);
  if (frozen_) {
    // Lock each limb joint's rest rotation to its current angle, and
    // keep the targets in step so the per-step apply doesn't undo it.
    const int frozen_joints[] = {
        kSpazJointPelvis,        kSpazJointUpperRightArm,
        kSpazJointLowerRightArm, kSpazJointUpperLeftArm,
        kSpazJointLowerLeftArm,  kSpazJointUpperRightLeg,
        kSpazJointLowerRightLeg, kSpazJointUpperLeftLeg,
        kSpazJointLowerLeftLeg,  kSpazJointRightToes,
        kSpazJointLeftToes};
    for (int i : frozen_joints) {
      base::JointFixedEF* j = SimJoint_(i);
      if (!j) {
        continue;  // bg limbs: the rig latches its own joints.
      }
      FreezeJointAngle(j);
      for (int k = 0; k < 4; ++k) {
        joint_targets_[i].qrel[k] = j->qrel[k];
      }
    }
  }
  ApplyJointTargets_();

  // Legacy hair rig: same frozen treatment.
  float l_still_scale = 1.0f;
  float l_damp_scale = 1.0f;
  float a_stiff_scale = 1.0f;
  float a_damp_scale = 1.0f;
  if (frozen_) {
    l_still_scale *= 5.0f;
    l_damp_scale *= 0.2f;
    a_stiff_scale *= 1000.0f;
    a_damp_scale *= 0.2f;
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
  }
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

  if (main_sim_limbs_) {
    // Adjust torso size.
    body_torso_->SetDimensions(torso_radius_, 0, 0, 0.2f, 0, 0, 3.0f);

    // Adjust hip and leg size.
    body_pelvis_->SetDimensions(0.25f, 0.16f, 0.10f, 0.25f, 0.16f, 0.16f,
                                kPelvisDensity);
  } else {
    // Same collision shapes; the core carries the limbs' mass (see the
    // kBgLimbs* constants).
    body_torso_->SetDimensions(torso_radius_, 0, 0, 0.2f, 0, 0,
                               kBgLimbsTorsoDensity);
    body_pelvis_->SetDimensions(kBgLimbsPelvisWidth, 0.16f, 0.10f, 0.25f,
                                kBgLimbsPelvisMassHeight, 0.16f,
                                kPelvisDensity);
  }

  // (Re)build definition attachment rigs if their config changed. After
  // the core bodies are sized: the rig's twins copy their shapes and
  // masses.
  UpdateAttachments_();

  // (bg limbs take the physique through the rig config instead.)
  if (!main_sim_limbs_) {
    return;
  }
  float thigh_rad = thigh_radius_;
  upper_left_leg_body_->SetDimensions(thigh_rad, 0.12f, 0, 0.05f, 0.12f, 0,
                                      kUpperLegDensity);
  upper_right_leg_body_->SetDimensions(thigh_rad, 0.12f, 0, 0.05f, 0.12f, 0,
                                       kUpperLegDensity);

  float ankle_rad = ankle_radius_;
  lower_left_leg_body_->SetDimensions(ankle_rad, 0.26f - ankle_rad * 2.0f, 0,
                                      0.07f, 0.12f, 0, kLowerLegDensity);
  lower_right_leg_body_->SetDimensions(ankle_rad, 0.26f - ankle_rad * 2.0f, 0,
                                       0.07f, 0.12f, 0, kLowerLegDensity);
}

auto SpazNode::CreateFixedJoint(RigidBody* b1, RigidBody* b2, float ls,
                                float ld, float as, float ad)
    -> base::JointFixedEF* {
  return base::JointFixedEFCreate(
      scene()->dynamics()->ode_world(), b1 ? b1->body() : nullptr,
      b2 ? b2->body() : nullptr, kGameStepSeconds, ls, ld, as, ad);
}

auto SpazNode::CreateFixedJoint(RigidBody* b1, RigidBody* b2, float ls,
                                float ld, float as, float ad, float a1x,
                                float a1y, float a1z, float a2x, float a2y,
                                float a2z, bool reposition)
    -> base::JointFixedEF* {
  assert(b1 && b2);
  const float anchor1[3] = {a1x, a1y, a1z};
  const float anchor2[3] = {a2x, a2y, a2z};
  return base::JointFixedEFCreateAnchored(
      scene()->dynamics()->ode_world(), b1->body(), b2->body(),
      kGameStepSeconds, ls, ld, as, ad, anchor1, anchor2, reposition);
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
    scene()->render_view()->camera()->DeleteAreaOfInterest(area_of_interest_);
    area_of_interest_ = nullptr;
  }

  DestroyHair();

  dJointDestroy(neck_joint_);

  // Limb joints (none with bg limbs).
  for (int i = kSpazJointUpperRightArm; i < kSpazJointCount; ++i) {
    if (base::JointFixedEF* j = SimJoint_(i)) {
      dJointDestroy(j);
    }
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

    if (base::SoundAsset* sound = RandomAttackSound_()) {
      if (auto* s = scene()->NewAudioSource()) {
        const dReal* p = dGeomGetPosition(body_head_->geom());
        g_base->audio->PushSourceStopSoundCall(voice_play_id_);
        s->SetPosition(p[0], p[1], p[2]);
        voice_play_id_ = s->Play(sound);
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
      if (base::SoundAsset* sound = RandomAttackSound_()) {
        if (auto* source = scene()->NewAudioSource()) {
          const dReal* p_top = dGeomGetPosition(body_head_->geom());
          g_base->audio->PushSourceStopSoundCall(voice_play_id_);
          source->SetPosition(p_top[0], p_top[1], p_top[2]);
          voice_play_id_ = source->Play(sound);
          source->End();
        }
      }
      break;
    }
    case NodeMessageType::kJumpSound: {
      if (knockout_ || frozen_) {
        break;
      }
      if (base::SoundAsset* sound = RandomJumpSound_()) {
        if (auto* s = scene()->NewAudioSource()) {
          const dReal* p_top = dGeomGetPosition(body_head_->geom());
          g_base->audio->PushSourceStopSoundCall(voice_play_id_);
          s->SetPosition(p_top[0], p_top[1], p_top[2]);
          voice_play_id_ = s->Play(sound);
          s->End();
        }
      }
      break;
    }
    case NodeMessageType::kKnockout: {
      float amt = Utils::ExtractFloat16NBO(&data);
      // Clamped conversion, not a plain cast: `amt` is decoded straight
      // off the wire, so a hostile or buggy host can hand us NaN or a
      // huge value here -- and casting either to an int is undefined
      // behavior.
      knockout_ = static_cast_check_fit<uint8_t>(
          std::min(40, std::max(static_cast<int>(knockout_),
                                clamped_float_to_int<int>(amt * 0.07f))));
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
        // (bg limbs: no limb bodies to hit; see the damage scalar note
        // in the bg-dynamics-channels journal.)
        if (main_sim_limbs_) {
          dmg += upper_right_arm_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += lower_right_arm_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += upper_left_arm_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += lower_left_arm_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += upper_right_leg_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += lower_right_leg_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += upper_left_leg_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
          dmg += lower_left_leg_body_->ApplyImpulse(
              px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
              mag, velocity_mag, radius, calc_force_only);
        }
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
        // Newer behavior - versions have less punishing stun
        if (behavior_version_ >= 2) {
          knockout_ = static_cast_check_fit<uint8_t>(
              std::min(26, std::max(static_cast<int>(knockout_),
                                    static_cast<int>(dmg * 0.02f) - 24)));
        } else {
          knockout_ = static_cast_check_fit<uint8_t>(
              std::min(40, std::max(static_cast<int>(knockout_),
                                    static_cast<int>(dmg * 0.02f) - 20)));
        }
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
      auto* s = scene()->NewAudioSource();
      if (s) {
        const dReal* p_torso = dGeomGetPosition(body_torso_->geom());
        s->SetPosition(p_torso[0], p_torso[1], p_torso[2]);
        s->SetGain(0.3f);
        base::SoundAsset* sparkle;
        int r = rand() % 100;  // NOLINT
        if (r < 33) {
          sparkle = g_scene_v1->assets().sparkle01.get();
        } else if (r < 66) {
          sparkle = g_scene_v1->assets().sparkle02.get();
        } else {
          sparkle = g_scene_v1->assets().sparkle03.get();
        }
        s->Play(sparkle);
        s->End();
      }
    }
  }
}

void SpazNode::Step() {
  // Standin -> real look upgrade (character form): re-attempt the
  // definition's media the moment the registry moved (a background
  // acquisition landed), plus on a slow cadence to keep the missing
  // packages noted as wanted; physique never changes here, only the
  // look fields ApplyCharacterDef_ derives (character-skins.md).
  if (spaz_def_.exists() && spaz_def_->def().has_spaz()
      && !spaz_def_->def().spaz_media_ready()) {
    auto now = static_cast<millisecs_t>(scene()->time());
    if (media_retry_pacer_.Due(spaz_def_->def().media_pending(), now)
        && spaz_def_->RetryMedia()) {
      ApplyCharacterDef_();
    }
  }

  // Feed the character rig every anchor body's transform (results come
  // back a step or two later and draw relative to the bodies).
  if (attachment_rig_) {
    for (int ti = 0; ti < base::kCharacterAttachTargetCount; ++ti) {
      RigidBody* body =
          AttachTargetBody_(static_cast<base::CharacterAttachTarget>(ti));
      if (body) {
        attachment_rig_->SetAnchor(ti, body->GetTransform());
      }
    }
    if (rig_snap_) {
      attachment_rig_->Snap();
      rig_snap_ = false;
    }
    // Our base skip plus the engine's emergency load-shedding.
    attachment_rig_->SetSkip(kBGAttachmentSkip
                             + scene()->bg_dynamics_world()->load_skip());
    attachment_rig_->SetFrozen(frozen_);
    attachment_rig_->SetShattered(shattered_ != 0);
  }
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
                                        &right_toes_body_};

    // for (Object::Ref<RigidBody>** body = bodies; *body != nullptr; body++) {
    for (auto* body : bodies) {
      if (RigidBody* bodyptr = body->get()) {
        bodyptr->UpdateBlending();
      }
    }
    Object::Ref<RigidBody>* hair_bodies[] = {
        &hair_front_right_body_, &hair_front_left_body_,
        &hair_ponytail_top_body_, &hair_ponytail_bottom_body_};
    for (auto* body : hair_bodies) {
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

  if (!main_sim_limbs_) {
    // (No limb joints here; the bg rig runs its own at full rate.)
  } else if (always_on) {
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
    int body_count = 0;
    bodies[body_count++] = body_head_->body();
    bodies[body_count++] = body_torso_->body();
    if (main_sim_limbs_) {
      bodies[body_count++] = upper_right_arm_body_->body();
      bodies[body_count++] = lower_right_arm_body_->body();
      bodies[body_count++] = upper_left_arm_body_->body();
      bodies[body_count++] = lower_left_arm_body_->body();
      bodies[body_count++] = upper_right_leg_body_->body();
      bodies[body_count++] = upper_left_leg_body_->body();
      bodies[body_count++] = lower_right_leg_body_->body();
      bodies[body_count++] = lower_left_leg_body_->body();
    }
    bodies[body_count] = nullptr;

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

  // Limb and neck joint targets for this step.
  {
    SpazPose::StepInputs in;
    in.scenetime = scenetime;
    in.stepnum = scene()->stepnum();
    in.stream_id = stream_id();
    in.last_punch_time = last_punch_time_;
    in.celebrate_until_time_left = celebrate_until_time_left_;
    in.celebrate_until_time_right = celebrate_until_time_right_;
    in.throw_start = throw_start_;
    in.curse_death_time = curse_death_time_;
    in.have_thrown = have_thrown_;
    in.breath = breath;
    in.dead = dead_;
    in.shattered = shattered_;
    in.shatter_damage = shatter_damage_;
    in.hold_position_pressed = hold_position_pressed_;
    in.ud = ud_;
    in.lr = lr_;
    in.ud_norm = ud_norm_;
    in.lr_norm = lr_norm_;
    in.knockout = knockout_;
    in.balance = balance_;
    in.jump = jump_;
    in.pickup = pickup_;
    in.punch = punch_;
    in.punch_right = punch_right_;
    in.punch_dir_x = punch_dir_x_;
    in.punch_dir_z = punch_dir_z_;
    in.frozen = frozen_;
    in.footing = footing_;
    in.hockey = hockey_;
    in.run_gas = run_gas_;
    in.step_separation = step_separation_;
    in.idle_arm_stiffness = idle_arm_stiffness_;
    in.arm_swing = arm_swing_;
    in.shoulder_offset_x = shoulder_offset_x_;
    in.shoulder_offset_y = shoulder_offset_y_;
    in.shoulder_offset_z = shoulder_offset_z_;
    in.a_vel_y_smoothed_more = a_vel_y_smoothed_more_;
    in.holding_something = holding_something_;
    for (int i = 0; i < 3; ++i) {
      in.hold_hand_offset_left[i] = hold_hand_offset_left_[i];
      in.hold_hand_offset_right[i] = hold_hand_offset_right_[i];
    }
    in.torso = body_torso_->body();
    in.pelvis = body_pelvis_->body();
    in.stand = stand_body_->body();
    in.roller = body_roller_->body();
    if (holding_something_ && hold_node_.exists()) {
      Node* a = hold_node_.get();
      if (RigidBody* b = a->GetRigidBody(hold_body_)) {
        in.held = b->body();
      }
    }
    pose_.Step(in, PoseJoints_(), &head_turning);
    ApplyJointTargets_();
  }
  if (attachment_rig_ && rig_has_limbs_) {
    // The bg limb backend: the same targets, over the channel.
    base::BGDynamicsCharacterKind::LimbJointTarget targets[16];
    for (int i = 0; i < 16; ++i) {
      const SpazJointTarget& src = joint_targets_[kSpazJointUpperRightArm + i];
      base::BGDynamicsCharacterKind::LimbJointTarget& dst = targets[i];
      for (int k = 0; k < 3; ++k) {
        dst.anchor1[k] = src.anchor1[k];
      }
      for (int k = 0; k < 4; ++k) {
        dst.qrel[k] = src.qrel[k];
      }
      dst.linear_stiffness = src.linearStiffness;
      dst.linear_damping = src.linearDamping;
      dst.angular_stiffness = src.angularStiffness;
      dst.angular_damping = src.angularDamping;
    }
    attachment_rig_->SetLimbJointTargets(targets, 16);

    // Dev aid (BA_BG_LIMBS_TRACE): each bg limb's pose relative to
    // its anchor twin next to the main-sim limb's relative to the
    // same body, a few times a second; the gap is the fidelity.
    static const bool s_limb_trace = getenv("BA_BG_LIMBS_TRACE") != nullptr;
    static int s_limb_tick = 0;
    if (s_limb_trace) {
      if (s_limb_trace && main_sim_limbs_) {
        RigidBody* sim_bodies[10] = {
            upper_right_arm_body_.get(), lower_right_arm_body_.get(),
            upper_left_arm_body_.get(),  lower_left_arm_body_.get(),
            upper_right_leg_body_.get(), lower_right_leg_body_.get(),
            upper_left_leg_body_.get(),  lower_left_leg_body_.get(),
            right_toes_body_.get(),      left_toes_body_.get()};
        const int anchors[10] = {1, 1, 1, 1, 2, 2, 2, 2, 2, 2};
        // Record this step's main-sim limb poses.
        limb_rel_hist_head_ = (limb_rel_hist_head_ + 1) % 4;
        for (int i = 0; i < 10; ++i) {
          RigidBody* anchor_body = AttachTargetBody_(
              static_cast<base::CharacterAttachTarget>(anchors[i]));
          const dReal* sp = dBodyGetPosition(sim_bodies[i]->body());
          dVector3 rel;
          dBodyGetPosRelPoint(anchor_body->body(), sp[0], sp[1], sp[2], rel);
          for (int k = 0; k < 3; ++k) {
            limb_rel_hist_[limb_rel_hist_head_][i][k] =
                static_cast<float>(rel[k]);
          }
        }
        if ((++s_limb_tick % 15) == 0) {
          if (const auto* out = attachment_rig_->output()) {
            for (int i = 0; i < static_cast<int>(out->limbs.size()) && i < 10;
                 ++i) {
              Vector3f rig_rel = out->limbs[i].relative.GetTranslate();
              const float* now = limb_rel_hist_[limb_rel_hist_head_][i];
              // Gap against the current pose, and the best gap against
              // the last few steps (the rig's output is a step or two
              // behind; this separates lag from real disagreement).
              float gap_now = 0.0f;
              float gap_best = 1e9f;
              for (int lag = 0; lag < 4; ++lag) {
                const float* p =
                    limb_rel_hist_[(limb_rel_hist_head_ + 4 - lag) % 4][i];
                float dx = rig_rel.x - p[0];
                float dy = rig_rel.y - p[1];
                float dz = rig_rel.z - p[2];
                float g = std::sqrt(dx * dx + dy * dy + dz * dz);
                if (lag == 0) {
                  gap_now = g;
                }
                gap_best = std::min(gap_best, g);
              }
              printf(
                  "LIMBTRACE %d %d sim %.3f %.3f %.3f rig %.3f %.3f %.3f"
                  " gap %.3f lagged %.3f\n",
                  static_cast<int>(scene()->time()), i, now[0], now[1], now[2],
                  rig_rel.x, rig_rel.y, rig_rel.z, gap_now, gap_best);
              // World space too (loose debris has no meaningful
              // anchor-relative pose).
              const dReal* wp = dBodyGetPosition(sim_bodies[i]->body());
              Vector3f rig_world = out->limbs[i].world.GetTranslate();
              printf("LIMBWORLD %d %d sim %.3f %.3f %.3f rig %.3f %.3f %.3f\n",
                     static_cast<int>(scene()->time()), i,
                     static_cast<float>(wp[0]), static_cast<float>(wp[1]),
                     static_cast<float>(wp[2]), rig_world.x, rig_world.y,
                     rig_world.z);
            }
          }
        }
      }
    }
  }

  // if we're flying, keep us on a 2d plane
  if (!shattered_ && can_fly_ && !dead_) {
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
      float angle = sinf(pose_.roll_amt() - 3.141592f)
                    * (run_gas_ * 0.09f + (1.0f - run_gas_) * idle_sway_);
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
    if (knockout_ || frozen_) {
      if (main_sim_limbs_) {
        ball_size_ = 0.0f;
      } else {
        // Leg surrogate (see kBgLimbsDownBallSize): shrink to the down
        // size, or keep growing toward it if we were caught mid-recovery.
        ball_size_ = std::min(kBgLimbsDownBallSize, ball_size_ + 0.05f);
      }
    } else {
      ball_size_ = std::min(1.0f, ball_size_ + 0.05f);
    }

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
    if (!main_sim_limbs_) {
      // Leg surrogate: put the down-state ball's bottom
      // kBgLimbsDownBallBottomLift above the standing ball's bottom
      // whatever its size (a smaller ball hangs lower), blending back
      // to no offset as it regrows.
      float r_down = 0.3f * (0.1f + 0.9f * kBgLimbsDownBallSize);
      float offs_down = kBgLimbsDownBallBottomLift - (0.3f - r_down);
      float t = std::clamp((1.0f - ball_size_) / (1.0f - kBgLimbsDownBallSize),
                           0.0f, 1.0f);
      offs = t * offs_down;
    }
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
  // bg limbs: the ball is the leg surrogate while knocked out, so lock
  // it to the torso like when frozen instead of letting the ragdoll
  // roll around on it (kBgLimbsDownBallSize).
  bool down_brakes =
      kBgLimbsDownBallBrakes && !main_sim_limbs_ && knockout_ > 0;
  if (footing_ || frozen_ || dead_ || down_brakes) {
    float amt;
    // Full brakes if frozen. Otherwise crank up as our joystick magnitude goes
    // down.
    if (frozen_ || dead_ || down_brakes) {
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
      dVector3 p;
      if (UseSyntheticPunch_() || !main_sim_limbs_) {
        // The synthetic fist (no arm body involved).
        const float* s = pose_.synthetic_fist();
        p[0] = s[0];
        p[1] = s[1];
        p[2] = s[2];
      } else {
        // Classic: the end of our punching arm.
        dBodyID fist_body = punch_right_ ? lower_right_arm_body_->body()
                                         : lower_left_arm_body_->body();
        dBodyGetRelPointPos(fist_body, 0, 0, 0.01f, p);
      }

      // Move it down a tiny bit since we're often trying to punch dudes laying
      // on the ground.
      p[1] -= 0.1f;

      dGeomSetPosition(body_punch_->geom(), p[0], p[1], p[2]);

      // Dev aid (BA_PUNCH_TRACE): dump the real fist and the synthetic
      // one per step, torso space, for fitting the synthetic model.
      static const bool s_trace = getenv("BA_PUNCH_TRACE") != nullptr;
      if (s_trace && main_sim_limbs_) {
        // "real" is always the classic arm-attached fist (the arm body
        // still exists in the main sim), whichever form the punch
        // region itself is using.
        const float* s = pose_.synthetic_fist();
        dVector3 arm_p, real_t, synth_t;
        dBodyGetRelPointPos(punch_right_ ? lower_right_arm_body_->body()
                                         : lower_left_arm_body_->body(),
                            0, 0, 0.01f, arm_p);
        dBodyGetPosRelPoint(body_torso_->body(), arm_p[0], arm_p[1], arm_p[2],
                            real_t);
        dBodyGetPosRelPoint(body_torso_->body(), s[0], s[1], s[2], synth_t);
        std::vector<float> rv = GetPunchVelocity();
        const float* sv = pose_.synthetic_fist_velocity();
        const dReal* tav = dBodyGetAngularVel(body_torso_->body());
        const float* st = pose_.synthetic_fist_target();
        printf(
            "PUNCHTRACE %d %d real %.4f %.4f %.4f synth %.4f %.4f %.4f"
            " vel %.3f %.3f %.3f svel %.3f %.3f %.3f tav %.2f dir %.2f %.2f"
            " stgt %.3f %.3f %.3f\n",
            static_cast<int>(since_last_punch), punch_right_ ? 1 : 0, real_t[0],
            real_t[1], real_t[2], synth_t[0], synth_t[1], synth_t[2], rv[0],
            rv[1], rv[2], sv[0], sv[1], sv[2], tav[1], punch_dir_x_,
            punch_dir_z_, st[0], st[1], st[2]);
      }
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
        if (base::SoundAsset* sound = RandomFallSound_()) {
          if (auto* source = scene()->NewAudioSource()) {
            g_base->audio->PushSourceStopSoundCall(voice_play_id_);
            source->SetPosition(p_head[0], p_head[1], p_head[2]);
            voice_play_id_ = source->Play(sound);
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

  if (pickup_ == kPickupCooldown - kPickupHitboxDelay) {
    if (!body_pickup_.exists()) {
      pickup_before_hitbox_ = false;
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
      scene()->bg_dynamics_world()->Emit(e);
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
static void DrawShadow(base::RenderView* view,
                       const base::BGDynamicsShadow& shadow, float radius,
                       float density, const float* shadow_color) {
  float s_scale, s_density;
  shadow.GetValues(&s_scale, &s_density);
  float d = s_density * density;
  view->DrawBlotch(shadow.GetPosition(), radius * s_scale * 4.0f,
                   (0.08f + 0.04f * shadow_color[0]) * d,
                   (0.07f + 0.04f * shadow_color[1]) * d,
                   (0.065f + 0.04f * shadow_color[2]) * d, 0.32f * d);
}
static void DrawBrightSpot(base::RenderView* view,
                           const base::BGDynamicsShadow& shadow, float radius,
                           float density, const float* shadow_color) {
  float s_scale, s_density;
  shadow.GetValues(&s_scale, &s_density);
  float d = s_density * density * 0.3f;
  view->DrawBlotch(shadow.GetPosition(), radius * s_scale * 4.0f,
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
      oc->SetTexture(g_scene_v1->assets().eye_color.get());
      oc->SetColorizeColor(eye_color_red_, eye_color_green_, eye_color_blue_);
      oc->SetColorizeTexture(g_scene_v1->assets().eye_color_tint_mask.get());
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
        // (+x is the character's right eye; his left is on the
        // viewer's right when he faces the camera.)
        if (eye_style_right_ != base::CharacterEyeStyle::kNone) {
          c->DrawMeshAsset(g_scene_v1->assets().eye_ball.get());
          if (shading) {
            oc->SetReflectionScale(2, 2, 2);
          }
          if (death_scale != 1.0f)
            c->Scale(death_scale, death_scale, death_scale);
          c->DrawMeshAsset(g_scene_v1->assets().eye_ball_iris.get());
        }
      }

      if (eye_style_left_ != base::CharacterEyeStyle::kNone) {
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
          c->DrawMeshAsset(g_scene_v1->assets().eye_ball.get());
          if (death_scale != 1.0f) {
            c->Scale(death_scale, death_scale, death_scale);
          }
          if (shading) {
            oc->SetReflectionScale(2, 2, 2);
          }
          c->DrawMeshAsset(g_scene_v1->assets().eye_ball_iris.get());
        }
      }
    }
  }
}

void SpazNode::SetupEyeLidShading(base::ObjectComponent* c, float death_fade,
                                  float* add_color) {
  c->SetTexture(g_scene_v1->assets().eye_color.get());
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
  // A regular eye's lid always draws (resting angle + blinks); a
  // lidless eye's appears only mid-blink; an absent eye's never.
  bool blinking = blink_smooth_ >= 0.1f;
  auto lid_draws = [blinking](base::CharacterEyeStyle style) {
    return style == base::CharacterEyeStyle::kRegular
           || (style == base::CharacterEyeStyle::kLidless && blinking);
  };
  bool draw_right = lid_draws(eye_style_right_);
  bool draw_left = lid_draws(eye_style_left_);
  if (!draw_right && !draw_left) {
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

    if (draw_right) {
      c->DrawMeshAsset(g_scene_v1->assets().eye_lid.get());
    }
  }

  // Left eyelid (the -x one; see the eyeball-draw side note).
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
    if (draw_left) {
      c->DrawMeshAsset(g_scene_v1->assets().eye_lid.get());
    }
  }
  c->FlipCullFace();  // back to normal
}

void SpazNode::DrawBodyParts(base::ObjectComponent* c, bool shading,
                             float death_fade, float death_scale,
                             float* add_color) {
  // Set up shading.
  if (shading) {
    c->SetTexture(ColorTextureData_());
    c->SetColorizeTexture(ColorMaskTextureData_());
    c->SetColorizeColor(color_[0], color_[1], color_[2]);
    assert(highlight_.size() == 3);
    c->SetColorizeColor2(highlight_[0], highlight_[1], highlight_[2]);
    assert(highlight2_.size() == 3);
    c->SetColorizeColor3(highlight2_[0], highlight2_[1], highlight2_[2]);
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
    if (auto* mesh = HeadMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Hair tuft 1.
  if (draw_hair_ && hair_front_right_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_front_right_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      c->DrawMeshAsset(g_scene_v1->assets().hair_tuft1.get());
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
      c->DrawMeshAsset(g_scene_v1->assets().hair_tuft1b.get());
    }
  }

  // Hair tuft 2.
  if (hair_front_left_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_front_left_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) c->Scale(death_scale, death_scale, death_scale);
      c->DrawMeshAsset(g_scene_v1->assets().hair_tuft2.get());
    }
  }

  // Hair tuft 3.
  if (draw_hair_ && hair_ponytail_top_body_.exists()) {
    {
      auto xf = c->ScopedTransform();
      hair_ponytail_top_body_->ApplyToRenderComponent(c);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, death_scale);
      }
      c->DrawMeshAsset(g_scene_v1->assets().hair_tuft3.get());
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
      c->DrawMeshAsset(g_scene_v1->assets().hair_tuft4.get());
    }
  }

  // Definition attachments (bg-simulated, drawn relative to their
  // target bodies).
  DrawAttachments_(c, shading, death_scale);

  // Torso.
  {
    auto xf = c->ScopedTransform();
    body_torso_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (auto* mesh = TorsoMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Pelvis.
  {
    auto xf = c->ScopedTransform();
    body_pelvis_->ApplyToRenderComponent(c);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (auto* mesh = PelvisMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Limb transforms, whichever backend simulates them.
  Matrix44f limb_m[kLimbCount];
  bool limb_ok[kLimbCount];
  for (int i = 0; i < kLimbCount; ++i) {
    limb_ok[i] = LimbRenderMatrix_(i, &limb_m[i]);
  }
  // Upper limb meshes stretch to fill the gap between their root
  // socket on the core body and their socket on the lower limb.
  auto limb_stretch = [&](int lower, RigidBody* root, const float* root_anchor,
                          const Vector3f& lower_point, float rest) -> float {
    if (shattered_ || !limb_ok[lower]) {
      return 1.0f;
    }
    Vector3f p_root = root->GetTransform() * Vector3f(root_anchor);
    Vector3f p_lower = limb_m[lower] * lower_point;
    return std::min(1.6f, (p_root - p_lower).Length() / rest);
  };

  // Right upper arm.
  float right_stretch =
      limb_stretch(kLimbLowerRightArm, body_torso_.get(),
                   joint_targets_[kSpazJointUpperRightArm].anchor1,
                   kArmStretchPoint, 0.192f);
  // If we've got flippers instead of arms, shorten them if we've got gloves
  // on so they don't intersect as badly.
  if (flippers_ && have_boxing_gloves_) {
    right_stretch *= 0.5f;
  }
  if (limb_ok[kLimbUpperRightArm]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbUpperRightArm].m);
    c->Scale(1.0f, 1.0f, right_stretch);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (auto* mesh = UpperArmMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Right lower arm.
  if (limb_ok[kLimbLowerRightArm]) {
    auto xf = c->ScopedTransform();

    c->MultMatrix(limb_m[kLimbLowerRightArm].m);
    {
      auto xf = c->ScopedTransform();
      c->Translate(0, 0, 0.1f);
      c->Scale(1.0f, 1.0f, right_stretch);
      c->Translate(0.0f, 0.0f, -0.1f);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
      }
      if (auto* mesh = ForearmMeshData_(); mesh && !flippers_) {
        c->DrawMeshAsset(mesh);
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
      if (auto* mesh = HandMeshData_(); mesh && !flippers_) {
        c->DrawMeshAsset(mesh);
      }
    }
  }

  // Right upper leg.
  if (limb_ok[kLimbUpperRightLeg]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbUpperRightLeg].m);
    float stretch =
        limb_stretch(kLimbLowerRightLeg, body_pelvis_.get(),
                     joint_targets_[kSpazJointUpperRightLeg].anchor1,
                     kLegStretchPoint, 0.20f);
    c->Scale(1.0f, 1.0f, stretch);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (auto* mesh = UpperLegMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Right lower leg.
  if (limb_ok[kLimbLowerRightLeg]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbLowerRightLeg].m);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (auto* mesh = LowerLegMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  if (limb_ok[kLimbRightToes]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbRightToes].m);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (auto* mesh = ToesMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // OK NOW LEFT SIDE LIMBS:
  c->FlipCullFace();

  // Left upper arm.
  float left_stretch = limb_stretch(
      kLimbLowerLeftArm, body_torso_.get(),
      joint_targets_[kSpazJointUpperLeftArm].anchor1, kArmStretchPoint, 0.192f);
  // If we've got flippers instead of arms, shorten them if we've got gloves
  // on so they don't intersect as badly.
  if (flippers_ && have_boxing_gloves_) {
    left_stretch *= 0.5f;
  }
  if (limb_ok[kLimbUpperLeftArm]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbUpperLeftArm].m);
    c->Scale(-1, 1, left_stretch);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    }
    if (auto* mesh = UpperArmMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Left lower arm.
  if (limb_ok[kLimbLowerLeftArm]) {
    auto xf = c->ScopedTransform();

    c->MultMatrix(limb_m[kLimbLowerLeftArm].m);
    c->Scale(-1, 1, 1);
    {
      auto x = c->ScopedTransform();
      c->Translate(0, 0, 0.1f);
      c->Scale(1, 1, left_stretch);
      c->Translate(0, 0, -0.1f);
      if (death_scale != 1.0f) {
        c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
      }
      if (auto* mesh = ForearmMeshData_(); mesh && !flippers_) {
        c->DrawMeshAsset(mesh);
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
      if (auto* mesh = HandMeshData_(); mesh && !flippers_) {
        c->DrawMeshAsset(mesh);
      }
    }
  }

  // Left upper leg.
  if (limb_ok[kLimbUpperLeftLeg]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbUpperLeftLeg].m);
    float stretch = limb_stretch(kLimbLowerLeftLeg, body_pelvis_.get(),
                                 joint_targets_[kSpazJointUpperLeftLeg].anchor1,
                                 kLegStretchPoint, 0.20f);
    c->Scale(-1.0f, 1.0f, stretch);
    if (death_scale != 1.0f)
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    if (auto* mesh = UpperLegMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Lower leg.
  if (limb_ok[kLimbLowerLeftLeg]) {
    auto xf = c->ScopedTransform();
    c->MultMatrix(limb_m[kLimbLowerLeftLeg].m);
    c->Scale(-1.0f, 1.0f, 1.0f);
    if (death_scale != 1.0f)
      c->Scale(death_scale, death_scale, 0.5f + death_scale * 0.5f);
    if (auto* mesh = LowerLegMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // Toes.
  if (limb_ok[kLimbLeftToes]) {
    auto xf = c->ScopedTransform();

    c->MultMatrix(limb_m[kLimbLeftToes].m);
    c->Scale(-1, 1, 1);
    if (death_scale != 1.0f) {
      c->Scale(death_scale, death_scale, death_scale);
    }
    if (auto* mesh = ToesMeshData_()) {
      c->DrawMeshAsset(mesh);
    }
  }

  // RESTORE CULL
  c->FlipCullFace();
}

static void DrawRadialMeter(base::MeshIndexedSimpleFull* m,
                            base::SimpleComponent* c, float amt, bool flash,
                            bool premult_tex) {
  // For a premultiplied texture drawn with a faded straight color,
  // premultiply rgb by alpha ourselves (see
  // docs/design/premultiplied-alpha.md).
  float a = flash ? 0.7f : 0.6f;
  float cmul = premult_tex ? a : 1.0f;
  if (flash) {
    c->SetColor(cmul, cmul, 0.4f * cmul, a);
  } else {
    c->SetColor(cmul, cmul, cmul, a);
  }
  base::Graphics::DrawRadialMeter(m, amt);
  c->DrawMesh(m);
}

// Whether debug-draw mode includes the stand body (the large sphere a
// standing spaz balances on). Off by default since it hides most of the
// legs; flip on when debugging stand/balance behavior.
const bool kDebugDrawStandBody = false;
// The bg-dynamics twin anchor body (cyan) sits on top of the real head
// and mostly just z-fights with it; its offset is the bg staleness, so
// flip this on when that's what you want to see.
const bool kDebugDrawBGAttachmentAnchor = false;
// Roller-ball debug alpha; below 1 it draws lit-translucent so the limb
// bodies inside stay visible.
const float kDebugDrawRollerAlpha = 0.5f;

void SpazNode::DrawAttachments_(base::ObjectComponent* c, bool shading,
                                float death_scale) {
  const base::BasicSpazMedia* media = nullptr;
  if (spaz_def_.exists() && spaz_def_->def().spaz_media_ready()) {
    media = &spaz_def_->def().spaz_media();
  }
  bool textures_overridden = false;
  const base::BGDynamicsCharacterRig::Output* out =
      attachment_rig_ ? attachment_rig_->output() : nullptr;
  for (int ti = 0; ti < base::kCharacterAttachTargetCount; ++ti) {
    auto& target = attachment_targets_[ti];
    if (target.defs.empty()) {
      continue;
    }
    RigidBody* body =
        AttachTargetBody_(static_cast<base::CharacterAttachTarget>(ti));
    if (!body) {
      continue;
    }
    // Dynamic segments index the rig output flat, in definition order,
    // starting where this target's run begins.
    int flat = target.body_start;
    for (size_t ai = 0; ai < target.defs.size(); ++ai) {
      const auto& adef = target.defs[ai];
      bool is_static = adef.type == base::CharacterAttachmentType::kStatic;
      for (size_t si = 0; si < adef.segments.size(); ++si) {
        int body_index = flat;
        if (!is_static) {
          flat++;
        }
        const auto& sdef = adef.segments[si];
        // Definition art, drawn only once the media is local.
        if (!media || ai >= media->attachments[ti].size()
            || si >= media->attachments[ti][ai].segments.size()) {
          continue;
        }
        const auto& smedia = media->attachments[ti][ai].segments[si];
        base::MeshAsset* mesh = smedia.mesh.get();
        base::TextureAsset* tex = smedia.texture.get();
        base::TextureAsset* tint = smedia.tint_texture.get();
        if (!mesh) {
          continue;
        }
        if (!is_static
            && (!out || body_index >= static_cast<int>(out->bodies.size()))) {
          continue;
        }
        if (shading) {
          // Per-segment texture overrides; absent = the character's
          // own color/colorize maps, which are already bound.
          if (tex || tint) {
            c->SetTexture(tex ? tex : ColorTextureData_());
            c->SetColorizeTexture(tint ? tint : ColorMaskTextureData_());
            textures_overridden = true;
          } else if (textures_overridden) {
            c->SetTexture(ColorTextureData_());
            c->SetColorizeTexture(ColorMaskTextureData_());
            textures_overridden = false;
          }
        }
        auto xf = c->ScopedTransform();
        body->ApplyToRenderComponent(c);
        if (!is_static) {
          c->MultMatrix(out->bodies[body_index].relative.m);
        }
        if (sdef.has_offset) {
          c->MultMatrix(sdef.offset.m);
        }
        if (death_scale != 1.0f) {
          c->Scale(death_scale, death_scale, death_scale);
        }
        c->DrawMeshAsset(mesh);
      }
    }
  }
  if (shading && textures_overridden) {
    // Body parts draw after us and expect the defaults.
    c->SetTexture(ColorTextureData_());
    c->SetColorizeTexture(ColorMaskTextureData_());
  }
}

void SpazNode::DrawDebugBodies_(base::FrameDef* frame_def) {
  // Debug-draw mode: our rigid bodies as flat facing-ratio shapes (object
  // lighting, no shadows) in place of the display meshes. Colors group the
  // bodies by role so the skeleton reads at a glance.
  auto* pass = frame_def->beauty_pass();
  struct Entry {
    RigidBody* body;
    float r, g, b;
    float a{1.0f};
  };
  const float ar = 0.8f, ag = 0.8f, ab = 1.0f;
  const float lr = 0.8f, lg = 1.0f, lb = 0.8f;
  // Main-sim limbs draw as bodies below; bg limbs draw from the rig
  // output further down, in the same role colors pulled toward blue
  // (BGDynamicsDebugTint) like everything else bg-simulated.
  const bool bg_limbs = UseBgLimbs_();
  const Entry entries[] = {
      // Core.
      {body_head_.get(), 1.0f, 1.0f, 1.0f},
      {body_torso_.get(), 1.0f, 1.0f, 1.0f},
      {body_pelvis_.get(), 1.0f, 1.0f, 1.0f},
      // Limbs.
      {bg_limbs ? nullptr : upper_right_arm_body_.get(), ar, ag, ab},
      {bg_limbs ? nullptr : lower_right_arm_body_.get(), ar, ag, ab},
      {bg_limbs ? nullptr : upper_left_arm_body_.get(), ar, ag, ab},
      {bg_limbs ? nullptr : lower_left_arm_body_.get(), ar, ag, ab},
      {bg_limbs ? nullptr : upper_right_leg_body_.get(), lr, lg, lb},
      {bg_limbs ? nullptr : lower_right_leg_body_.get(), lr, lg, lb},
      {bg_limbs ? nullptr : upper_left_leg_body_.get(), lr, lg, lb},
      {bg_limbs ? nullptr : lower_left_leg_body_.get(), lr, lg, lb},
      {bg_limbs ? nullptr : left_toes_body_.get(), lr, lg, lb},
      {bg_limbs ? nullptr : right_toes_body_.get(), lr, lg, lb},
      // Locomotion / interaction volumes.
      // Translucent so the limb bodies it encloses stay visible (grey,
      // not blue: blue is the bg-simulated tint).
      {body_roller_.get(), 0.85f, 0.85f, 0.85f, kDebugDrawRollerAlpha},
      {kDebugDrawStandBody ? stand_body_.get() : nullptr, 0.5f, 1.0f, 0.5f},
      {body_punch_.get(), 1.0f, 1.0f, 0.3f},
      {body_pickup_.get(), 0.3f, 1.0f, 1.0f},
      // Legacy hair.
      {hair_front_right_body_.get(), 1.0f, 0.6f, 0.9f},
      {hair_front_left_body_.get(), 1.0f, 0.6f, 0.9f},
      {hair_ponytail_top_body_.get(), 1.0f, 0.6f, 0.9f},
      {hair_ponytail_bottom_body_.get(), 1.0f, 0.6f, 0.9f},
  };
  for (const Entry& e : entries) {
    if (e.body != nullptr) {
      e.body->DrawDebug(pass, e.r, e.g, e.b, e.a);
    }
  }

  // Under older protocols, the synthetic fist (magenta) beside the
  // arm-attached punch body (yellow): the two should coincide. Under
  // the current protocol the punch body *is* the synthetic fist.
  if (pose_.punch_active() && body_punch_.exists() && !UseSyntheticPunch_()) {
    base::ObjectComponent c(pass);
    c.SetFacingRatio(true);
    c.SetLightShadow(base::LightShadowType::kObject);
    c.SetColor(1.0f, 0.2f, 1.0f);
    const float* s = pose_.synthetic_fist();
    auto xf = c.ScopedTransform();
    c.Translate(s[0], s[1] - 0.1f, s[2]);
    c.Scale(0.25f, 0.25f, 0.25f);
    c.DrawMesh(g_base->graphics->debug_sphere_mesh());
    c.Submit();
  }

  // BG-simulated definition attachments, at their true simmed poses:
  // the twin anchors (cyan; their offset from the target bodies is the
  // bg staleness) and the segment capsules (orange).
  if (attachment_rig_) {
    if (const auto* out = attachment_rig_->output()) {
      if (kDebugDrawBGAttachmentAnchor) {
        base::ObjectComponent c(pass);
        c.SetFacingRatio(true);
        c.SetLightShadow(base::LightShadowType::kObject);
        c.SetColor(0.3f, 0.9f, 1.0f);
        for (int i = 0; i < out->anchor_count; ++i) {
          auto xf = c.ScopedTransform();
          c.MultMatrix(out->anchors[i].m);
          c.Scale(0.23f, 0.23f, 0.23f);
          c.DrawMesh(g_base->graphics->debug_sphere_mesh());
        }
        c.Submit();
      }
      // bg limbs, exactly where their display meshes draw.
      if (bg_limbs && static_cast<int>(out->limbs.size()) > 0) {
        base::ObjectComponent c(pass);
        c.SetFacingRatio(true);
        c.SetLightShadow(base::LightShadowType::kObject);
        for (int i = 0;
             i < static_cast<int>(out->limbs.size()) && i < kLimbCount; ++i) {
          Matrix44f m;
          if (!LimbRenderMatrix_(i, &m)) {
            continue;
          }
          // bg-simulated: blue-tinted like every other bg body.
          float r = i < kLimbUpperRightLeg ? ar : lr;
          float g = i < kLimbUpperRightLeg ? ag : lg;
          float b = i < kLimbUpperRightLeg ? ab : lb;
          base::BGDynamicsDebugTint(&r, &g, &b);
          c.SetColor(r, g, b);
          auto xf = c.ScopedTransform();
          c.MultMatrix(m.m);
          float radius = out->limbs[i].radius;
          float length = out->limbs[i].length;
          if (length <= 0.0f) {
            c.Scale(radius, radius, radius);
            c.DrawMesh(g_base->graphics->debug_sphere_mesh());
            continue;
          }
          {
            auto xf2 = c.ScopedTransform();
            c.Scale(radius, radius, length);
            c.DrawMesh(g_base->graphics->debug_cylinder_mesh());
          }
          {
            auto xf2 = c.ScopedTransform();
            c.Translate(0.0f, 0.0f, 0.5f * length);
            c.Scale(radius, radius, radius);
            c.DrawMesh(g_base->graphics->debug_hemisphere_mesh());
          }
          {
            auto xf2 = c.ScopedTransform();
            c.Translate(0.0f, 0.0f, -0.5f * length);
            c.Rotate(180.0f, 1.0f, 0.0f, 0.0f);
            c.Scale(radius, radius, radius);
            c.DrawMesh(g_base->graphics->debug_hemisphere_mesh());
          }
        }
        c.Submit();
      }
      base::ObjectComponent c(pass);
      c.SetFacingRatio(true);
      c.SetLightShadow(base::LightShadowType::kObject);
      {
        // Attachment segments: orange role color, bg-tinted.
        float r = 1.0f, g = 0.6f, b = 0.2f;
        base::BGDynamicsDebugTint(&r, &g, &b);
        c.SetColor(r, g, b);
      }
      for (int i = 0; i < static_cast<int>(out->bodies.size()); ++i) {
        auto xf = c.ScopedTransform();
        c.MultMatrix(out->bodies[i].world.m);
        float radius = out->bodies[i].radius;
        float length = out->bodies[i].length;
        {
          auto xf2 = c.ScopedTransform();
          c.Scale(radius, radius, length);
          c.DrawMesh(g_base->graphics->debug_cylinder_mesh());
        }
        {
          auto xf2 = c.ScopedTransform();
          c.Translate(0.0f, 0.0f, 0.5f * length);
          c.Scale(radius, radius, radius);
          c.DrawMesh(g_base->graphics->debug_hemisphere_mesh());
        }
        {
          auto xf2 = c.ScopedTransform();
          c.Translate(0.0f, 0.0f, -0.5f * length);
          c.Rotate(180.0f, 1.0f, 0.0f, 0.0f);
          c.Scale(radius, radius, radius);
          c.DrawMesh(g_base->graphics->debug_hemisphere_mesh());
        }
      }
      c.Submit();
    }
  }

  // Fins. Debug triangles get both windings at flush time, so one
  // triangle each is enough.
  {
    base::ObjectComponent c(pass);
    c.SetFacingRatio(true);
    c.SetLightShadow(base::LightShadowType::kObject);

    // Orientation fins on the head, torso, and pelvis: a triangle in each
    // body's local up/forward (+y/+z) plane, since a sphere or capsule
    // doesn't show which way it's facing.
    c.SetColor(1, 0, 0);
    const std::pair<RigidBody*, float> fins[] = {
        {body_head_.get(), 0.5f},
        {body_torso_.get(), 0.2f},
        {body_pelvis_.get(), 0.2f},
    };
    for (const auto& [body, size] : fins) {
      auto xf = c.ScopedTransform();
      body->ApplyToRenderComponent(&c);
      c.BeginDebugDrawTriangles();
      c.Vertex(0, size, 0);
      c.Vertex(0, 0, size);
      c.Vertex(0, 0, 0);
      c.End();
    }

    // Stand body: tall thin fins along its local +z and +x.
    c.SetColor(0.4f, 1.0f, 0.4f);
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

    // Punch direction as a thin yellow fin from the torso.
    c.SetColor(1, 1, 0);
    const dReal* p = dBodyGetPosition(body_torso_->body());
    {
      auto xf = c.ScopedTransform();
      c.Translate(p[0], p[1], p[2]);
      c.BeginDebugDrawTriangles();
      c.Vertex(0, 0, 0);
      c.Vertex(2.0f * punch_dir_x_, 0, 2.0f * punch_dir_z_);
      c.Vertex(0, 0.05f, 0);
      c.End();
    }

    // Left-leg IK joint anchors: foot attach (red) on the lower leg and
    // pelvis attach (blue) on the pelvis (main-sim limbs only).
    if (base::JointFixedEF* j = left_leg_ik_joint_) {
      const struct {
        RigidBody* body;
        const dReal* anchor;
        float r, g, b;
      } anchors[] = {
          {lower_left_leg_body_.get(), j->anchor2, 1, 0, 0},
          {body_pelvis_.get(), j->anchor1, 0, 0, 1},
      };
      for (const auto& a : anchors) {
        c.SetColor(a.r, a.g, a.b);
        auto xf = c.ScopedTransform();
        a.body->ApplyToRenderComponent(&c);
        c.Translate(a.anchor[0], a.anchor[1], a.anchor[2]);
        c.Rotate(90, 1, 0, 0);
        c.Scale(0.5f, 0.5f, 0.5f);
        c.BeginDebugDrawTriangles();
        c.Vertex(0, 0.1f, 0.5f);
        c.Vertex(0, 0, 0.5f);
        c.Vertex(0, 0, 0);
        c.End();
      }
    }
    c.Submit();
  }
}

void SpazNode::Draw(base::FrameDef* frame_def) {
#if !BA_HEADLESS_BUILD

  if (graphics_quality_ != frame_def->quality()) {
    graphics_quality_ = frame_def->quality();
    UpdateForGraphicsQuality(graphics_quality_);
  }

  bool debug_draw = g_base->graphics->debug_draw();
  if (debug_draw) {
    DrawDebugBodies_(frame_def);
  }

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
      bool premult_tex{};
      if (!flash) {
        auto* tex = mini_billboard_1_texture_.exists()
                        ? mini_billboard_1_texture_->texture_data()
                        : nullptr;
        c.SetTexture(tex);
        premult_tex = tex != nullptr && tex->premultiplied();
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0] - 0.2f, torso_pos[1] + 1.2f,
                    torso_pos[2] - 0.2f);
        c.Scale(0.08f, 0.08f, 0.08f);
        DrawRadialMeter(&billboard_1_mesh_, &c, amt, flash, premult_tex);
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
      bool premult_tex{};
      if (!flash) {
        auto* tex = mini_billboard_2_texture_.exists()
                        ? mini_billboard_2_texture_->texture_data()
                        : nullptr;
        c.SetTexture(tex);
        premult_tex = tex != nullptr && tex->premultiplied();
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0], torso_pos[1] + 1.2f, torso_pos[2] - 0.2f);
        c.Scale(0.09f, 0.09f, 0.09f);
        DrawRadialMeter(&billboard_2_mesh_, &c, amt, flash, premult_tex);
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
      bool premult_tex{};
      if (!flash) {
        auto* tex = mini_billboard_3_texture_.exists()
                        ? mini_billboard_3_texture_->texture_data()
                        : nullptr;
        c.SetTexture(tex);
        premult_tex = tex != nullptr && tex->premultiplied();
      }
      {
        auto xf = c.ScopedTransform();
        c.Translate(torso_pos[0] + 0.2f, torso_pos[1] + 1.2f,
                    torso_pos[2] - 0.2f);
        c.Scale(0.08f, 0.08f, 0.08f);
        DrawRadialMeter(&billboard_3_mesh_, &c, amt, flash, premult_tex);
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
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesImage1x1));
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
      int elem_count = name_text_group_.GetElementCount();

      // Dead players' names draw faded; OS-rendered text is premultiplied
      // so premultiply rgb by alpha ourselves (see
      // docs/design/premultiplied-alpha.md). Live names are opaque (no-op).
      float name_a = dead_ ? 0.7f : 1.0f;
      float name_cmul =
          (elem_count > 0
           && name_text_group_.GetElementTexture(0)->premultiplied())
              ? name_a
              : 1.0f;
      c.SetColor(r * name_cmul, g * name_cmul, b * name_cmul, name_a);

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
          // Non-stalling measure; by the time our name group has
          // elements to draw, spans are warm and this succeeds (a
          // cache-evicted miss just skips the squish for a frame).
          float w = g_base->text_graphics->TryGetStringWidth(name_.c_str())
                        .value_or(0.0f);
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
    auto* bb_tex = billboard_texture_.exists()
                       ? billboard_texture_->texture_data()
                       : nullptr;
    // Premultiplied texture + straight faded color; premultiply rgb by alpha
    // ourselves (see docs/design/premultiplied-alpha.md).
    float bb_cmul = (bb_tex != nullptr && bb_tex->premultiplied()) ? o : 1.0f;
    c.SetColor(bb_cmul, bb_cmul, bb_cmul, o);
    c.SetTexture(bb_tex);
    {
      auto xf = c.ScopedTransform();
      c.Translate(pos[0], pos[1] + 1.6f, pos[2] - 0.2f);
      c.Scale(2.3f * 0.2f * s, 2.3f * 0.2f * s, 2.3f * 0.2f * s);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesImage1x1));
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
        c2.DrawMeshAsset(g_scene_v1->assets().cross_out.get());
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
          c.DrawMeshAsset(g_base->assets->BuiltinMesh(
              base::BuiltinMeshID::kMeshesImage1x1));
        }

        c.SetColor(0, 0.35f * o, 0, 0.3f * o);

        {
          auto xf = c.ScopedTransform();
          c.Translate(p_left * 0.5f, half_height);
          c.Scale(p_left, height);
          c.DrawMeshAsset(g_base->assets->BuiltinMesh(
              base::BuiltinMeshID::kMeshesImage1x1));
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
          c.DrawMeshAsset(g_base->assets->BuiltinMesh(
              base::BuiltinMeshID::kMeshesImage1x1));
        }

        c.SetColor(
            (dead_ && scene()->stepnum() % 10 < 5) ? 0.55f * o : 0.01f * o, 0,
            0, 0.4f * o);

        {
          auto xf = c.ScopedTransform();
          c.Translate((p_right + 1.0f) * 0.5f, half_height);
          c.Scale(1.0f - p_right, height);
          c.DrawMeshAsset(g_base->assets->BuiltinMesh(
              base::BuiltinMeshID::kMeshesImage1x1));
        }
      }
      c.Submit();
    }
  }

  // FOOTTRACE (dev aid, BA_BG_LIMBS_TRACE): per rendered frame, each
  // toe's drawn position and the pelvis, for jitter analysis of what
  // actually reaches the screen.
  {
    static const bool s_foot_trace = getenv("BA_BG_LIMBS_TRACE") != nullptr;
    static int64_t s_foot_frame = 0;
    if (s_foot_trace) {
      ++s_foot_frame;
      const dReal* pp = dBodyGetPosition(body_pelvis_->body());
      for (int i = kLimbRightToes; i <= kLimbLeftToes; ++i) {
        Matrix44f m;
        if (!LimbRenderMatrix_(i, &m)) {
          continue;
        }
        Vector3f d = m.GetTranslate();
        // The rig's own world pose for the toe (bg limbs); the drawn
        // point differs from it by the anchor's motion over the
        // output's lag, so this measures that lag directly.
        Vector3f w = d;
        if (const auto* out =
                attachment_rig_ ? attachment_rig_->output() : nullptr) {
          if (!main_sim_limbs_ && i < static_cast<int>(out->limbs.size())) {
            w = out->limbs[i].world.GetTranslate();
          }
        }
        printf(
            "FOOTTRACE %d %d drawn %.4f %.4f %.4f pelvis %.4f %.4f %.4f"
            " world %.4f %.4f %.4f\n",
            static_cast<int>(s_foot_frame), i, d.x, d.y, d.z,
            static_cast<float>(pp[0]), static_cast<float>(pp[1]),
            static_cast<float>(pp[2]), w.x, w.y, w.z);
      }
    }
  }

  // Draw all body parts with normal shading (debug mode draws our rigid
  // bodies instead; see DrawDebugBodies_).
  if (!debug_draw) {
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
  if (wings_ && !debug_draw) {
    base::ObjectComponent c(beauty_pass);
    c.SetTransparent(false);
    c.SetColor(1, 1, 1, 1.0f);
    c.SetReflection(base::ReflectionType::kSoft);
    c.SetReflectionScale(0.4f, 0.4f, 0.4f);
    c.SetTexture(WingTextureData_());
    c.SetColorizeTexture(WingTintTextureData_());
    c.SetColorizeColor(color_[0], color_[1], color_[2]);
    c.SetColorizeColor2(highlight_[0], highlight_[1], highlight_[2]);
    c.SetColorizeColor3(highlight2_[0], highlight2_[1], highlight2_[2]);

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
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesBox));
      }

      // Draw wing point.
      {
        auto xf = c.ScopedTransform();
        c.Translate(wing_pos_left_.x, wing_pos_left_.y, wing_pos_left_.z);
        c.Scale(0.1f, 0.1f, 0.1f);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesBox));
      }

      // Draw target.
      dBodyGetRelPointPos(body_torso_->body(), -kWingAttachX, kWingAttachY,
                          kWingAttachZ, p_wing_r);
      {
        auto xf = c.ScopedTransform();
        c.Translate(p_wing_r[0], p_wing_r[1], p_wing_r[2]);
        c.Scale(0.05f, 0.05f, 0.05f);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesBox));
      }

      // Draw wing point.
      {
        auto xf = c.ScopedTransform();
        c.Translate(wing_pos_right_.x, wing_pos_right_.y, wing_pos_right_.z);
        c.Scale(0.1f, 0.1f, 0.1f);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesBox));
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
      c.DrawMeshAsset(WingMeshData_());
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
      c.DrawMeshAsset(WingMeshData_());
    }
    c.Submit();
  }

  // Boxing gloves.
  if (have_boxing_gloves_ && !debug_draw) {
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
    c.SetTexture(g_base->assets->base_assets().boxing_gloves_color.get());

    Matrix44f m;
    if (LimbRenderMatrix_(kLimbLowerRightArm, &m)) {
      auto xf = c.ScopedTransform();
      c.MultMatrix(m.m);
      if (death_scale != 1.0f) {
        c.Scale(death_scale, death_scale, death_scale);
      }
      c.DrawMeshAsset(g_base->assets->base_assets().boxing_glove.get());
    }

    c.FlipCullFace();
    if (LimbRenderMatrix_(kLimbLowerLeftArm, &m)) {
      auto xf = c.ScopedTransform();
      c.MultMatrix(m.m);
      c.Scale(-1.0f, 1.0f, 1.0f);
      if (death_scale != 1.0f) {
        c.Scale(death_scale, death_scale, death_scale);
      }
      c.DrawMeshAsset(g_base->assets->base_assets().boxing_glove.get());
    }
    c.FlipCullFace();
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
      base::RenderView* view = scene()->render_view();
      if (FullShadowSet* full_shadows = full_shadow_set_.get()) {
        full_shadows->torso_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_torso_->body())));
        full_shadows->head_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_head_->body())));
        full_shadows->pelvis_shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_pelvis_->body())));
        // Limb shadows follow the drawn limbs (whichever backend).
        const std::pair<int, base::BGDynamicsShadow*> limb_shadows[] = {
            {kLimbLowerLeftLeg, &full_shadows->lower_left_leg_shadow_},
            {kLimbLowerRightLeg, &full_shadows->lower_right_leg_shadow_},
            {kLimbUpperLeftLeg, &full_shadows->upper_left_leg_shadow_},
            {kLimbUpperRightLeg, &full_shadows->upper_right_leg_shadow_},
            {kLimbLowerRightArm, &full_shadows->lower_right_arm_shadow_},
            {kLimbUpperRightArm, &full_shadows->upper_right_arm_shadow_},
            {kLimbLowerLeftArm, &full_shadows->lower_left_arm_shadow_},
            {kLimbUpperLeftArm, &full_shadows->upper_left_arm_shadow_},
        };
        for (const auto& [limb, shadow] : limb_shadows) {
          Matrix44f m;
          if (LimbRenderMatrix_(limb, &m)) {
            shadow->SetPosition(m.GetTranslate());
          }
        }

        DrawBrightSpot(view, full_shadows->lower_left_leg_shadow_,
                       0.3f * death_scale, death_fade * (frozen_ ? 0.3f : 0.2f),
                       sc);
        DrawBrightSpot(view, full_shadows->lower_right_leg_shadow_,
                       0.3f * death_scale, death_fade * (frozen_ ? 0.3f : 0.2f),
                       sc);
        DrawBrightSpot(view, full_shadows->head_shadow_, 0.45f * death_scale,
                       death_fade * (frozen_ ? 0.8f : 0.14f), sc);
        DrawShadow(view, full_shadows->torso_shadow_, 0.19f * death_scale, 0.9f,
                   sc);
        DrawShadow(view, full_shadows->head_shadow_, 0.15f * death_scale, 0.7f,
                   sc);
        DrawShadow(view, full_shadows->pelvis_shadow_, 0.15f * death_scale,
                   0.7f, sc);
        DrawShadow(view, full_shadows->lower_left_leg_shadow_,
                   0.08f * death_scale, 1.0f, sc);
        DrawShadow(view, full_shadows->lower_right_leg_shadow_,
                   0.08f * death_scale, 1.0f, sc);
        DrawShadow(view, full_shadows->upper_left_leg_shadow_,
                   0.08f * death_scale, 1.0f, sc);
        DrawShadow(view, full_shadows->upper_right_leg_shadow_,
                   0.08f * death_scale, 1.0f, sc);
        DrawShadow(view, full_shadows->upper_left_arm_shadow_,
                   0.08f * death_scale, 0.5f, sc);
        DrawShadow(view, full_shadows->lower_left_arm_shadow_,
                   0.08f * death_scale, 0.3f, sc);
        DrawShadow(view, full_shadows->lower_right_arm_shadow_,
                   0.08f * death_scale, 0.3f, sc);
        DrawShadow(view, full_shadows->upper_right_arm_shadow_,
                   0.08f * death_scale, 0.5f, sc);
      } else if (SimpleShadowSet* simple_shadows = simple_shadow_set_.get()) {
        simple_shadows->shadow_.SetPosition(
            Vector3f(dBodyGetPosition(body_pelvis_->body())));
        DrawShadow(view, simple_shadows->shadow_, 0.2f * death_scale, 2.0f, sc);
      }
    }
  }
#endif  // !BA_HEADLESS_BUILD
}  // NOLINT (yes i know this is too big)

void SpazNode::UpdateForGraphicsQuality(base::GraphicsQuality quality) {
#if !BA_HEADLESS_BUILD
  if (quality >= base::GraphicsQuality::kMedium) {
    full_shadow_set_ = Object::New<FullShadowSet>(scene()->bg_dynamics_world());
    simple_shadow_set_.Clear();
  } else {
    simple_shadow_set_ =
        Object::New<SimpleShadowSet>(scene()->bg_dynamics_world());
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
    base::CalcERPCFM(stiffness, damping, kGameStepSeconds, &erp, &cfm);
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
    base::CalcERPCFM(stiffness, damping, kGameStepSeconds, &erp, &cfm);
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
    base::CalcERPCFM(stiffness, damping, kGameStepSeconds, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
    }
  }

  if (colliding_body->part() == &spaz_part_) {
    float stiffness = 5000;
    float damping = 0.001f;
    float erp, cfm;
    base::CalcERPCFM(stiffness, damping, kGameStepSeconds, &erp, &cfm);
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
    // bg limbs: the ball is the leg surrogate while down (see
    // kBgLimbsDownBallSize): soft floor contacts, no wall kick.
    bool down_ball = !main_sim_limbs_ && (knockout_ || frozen_);
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
          if ((f & RigidBody::kIsTerrain) && !down_ball) {
            dBodyID b = body_roller_->body();
            dBodyAddForce(b, c[i].geom.normal[0] * 100.0f,
                          c[i].geom.normal[1] * 100.0f,
                          c[i].geom.normal[2] * 100.0f);
          }

          // Override stiffness and damping on our little parts
          float stiffness = 800.0f;
          float damping = 0.001f;
          float erp, cfm;
          base::CalcERPCFM(stiffness, damping, kGameStepSeconds, &erp, &cfm);
          c[i].surface.soft_erp = erp;
          c[i].surface.soft_cfm = cfm;
          c[i].surface.mu = 0.0f;

        } else {
          // trying to get a well-behaved floor-response...
          if (!hockey_) {
            float stiffness = down_ball ? kBgLimbsDownBallStiffness : 7000.0f;
            float damping = down_ball ? kBgLimbsDownBallDamping : 7.0f;
            float erp, cfm;
            base::CalcERPCFM(stiffness, damping, kGameStepSeconds, &erp, &cfm);
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

  if (main_sim_limbs_) {
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
  }

  // Definition attachment rigs (and bg limbs) re-place themselves on
  // their bodies.
  SnapAttachments_();
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

    pickup_release_time_ms_ = scene()->time();
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

  hair_front_right_body_.Clear();
  hair_front_left_body_.Clear();
  hair_ponytail_top_body_.Clear();
  hair_ponytail_bottom_body_.Clear();
}

static auto AttachmentRefsEqual(const base::CharacterAssetRef& a,
                                const base::CharacterAssetRef& b) -> bool {
  return a.apverid == b.apverid && a.name == b.name && a.index == b.index;
}

static auto AttachmentDefsEqual(
    const std::vector<base::BasicSpazDef::AttachmentDef>& a,
    const std::vector<base::BasicSpazDef::AttachmentDef>& b) -> bool {
  if (a.size() != b.size()) {
    return false;
  }
  for (size_t i = 0; i < a.size(); ++i) {
    const auto& x = a[i];
    const auto& y = b[i];
    if (x.type != y.type || x.segments.size() != y.segments.size()
        || x.stiffness != y.stiffness || x.damping != y.damping
        || x.drag != y.drag || x.curl != y.curl || x.length != y.length
        || x.radius != y.radius || x.curl_change != y.curl_change
        || x.length_change != y.length_change
        || x.radius_change != y.radius_change
        || x.stiffness_change != y.stiffness_change
        || x.damping_change != y.damping_change) {
      return false;
    }
    for (int j = 0; j < 3; ++j) {
      if (x.position[j] != y.position[j]) {
        return false;
      }
    }
    for (int j = 0; j < 4; ++j) {
      if (x.rotation[j] != y.rotation[j]) {
        return false;
      }
    }
    for (size_t j = 0; j < x.segments.size(); ++j) {
      const auto& sx = x.segments[j];
      const auto& sy = y.segments[j];
      if (!AttachmentRefsEqual(sx.mesh, sy.mesh)
          || !AttachmentRefsEqual(sx.texture, sy.texture)
          || !AttachmentRefsEqual(sx.tint_texture, sy.tint_texture)
          || sx.has_offset != sy.has_offset
          || (sx.has_offset && sx.offset != sy.offset)) {
        return false;
      }
    }
  }
  return true;
}

auto SpazNode::AttachTargetBody_(base::CharacterAttachTarget target)
    -> RigidBody* {
  switch (target) {
    case base::CharacterAttachTarget::kHead:
      return body_head_.get();
    case base::CharacterAttachTarget::kTorso:
      return body_torso_.get();
    case base::CharacterAttachTarget::kPelvis:
      return body_pelvis_.get();
  }
  return nullptr;
}

void SpazNode::SnapAttachments_() { rig_snap_ = true; }

// Append one target's dynamic attachment defs to a character rig
// config, hung off anchor index `anchor`: the per-kind physique from
// the spec table, the definition's placement/rotation/drag, and the
// calibration dials mapped onto the springs (kAntenna kinds: geometric,
// see the table comments). Returns the number of bodies appended.
static auto AppendAttachmentsToRigConfig(
    const std::vector<base::BasicSpazDef::AttachmentDef>& defs, int anchor,
    base::BGDynamicsCharacterKind::Config* config) -> int {
  using Kind = base::BGDynamicsCharacterKind;
  int bodies = 0;
  for (const auto& adef : defs) {
    if (adef.type == base::CharacterAttachmentType::kStatic
        || config->attachment_count >= Kind::kMaxAttachments) {
      continue;
    }
    const auto& spec = kAttachmentTypeSpecs[static_cast<int>(adef.type)];
    Kind::AttachmentSpec& aspec =
        config->attachments[config->attachment_count++];
    aspec.anchor = anchor;
    for (int i = 0; i < 3; ++i) {
      aspec.position[i] = adef.position[i];
    }
    for (int i = 0; i < 4; ++i) {
      aspec.rotation[i] = adef.rotation[i];
    }
    aspec.drag = adef.drag;
    aspec.segment_count = std::min(spec.segment_count, Kind::kMaxSegments);
    bodies += aspec.segment_count;
    bool antenna = adef.type == base::CharacterAttachmentType::kAntenna
                   || adef.type == base::CharacterAttachmentType::kAntenna2
                   || adef.type == base::CharacterAttachmentType::kAntenna3
                   || adef.type == base::CharacterAttachmentType::kAntenna4;
    // Per-segment dials: segment i uses value + i * change, clamped to
    // the dial's range. Length: 0 -> half the tabulated capsule length,
    // 1 -> 1.5x, along the chain axis (local z) for the capsule, the
    // mass capsule and the joint anchors so segments still meet end to
    // end. Radius: 0 -> tabulated, 1 -> 3x. Curl: bend at the segment's
    // joint.
    auto dial = [](float base, float change, int i, float lo, float hi) {
      return std::clamp(base + change * static_cast<float>(i), lo, hi);
    };
    auto length_scale_at = [&](int i) {
      return 0.5f + dial(adef.length, adef.length_change, i, 0.0f, 1.0f);
    };
    for (int si = 0; si < aspec.segment_count; ++si) {
      const auto& sspec = spec.segments[si];
      Kind::SegmentSpec& bspec = aspec.segments[si];
      float length_scale = length_scale_at(si);
      float radius_scale =
          1.0f + 2.0f * dial(adef.radius, adef.radius_change, si, 0.0f, 1.0f);
      // Curl bends every joint, the root's on top of the attachment
      // rotation: joints of an ANTENNA_4 with curl 0 / change -0.4 bend
      // 0, -0.4, -0.8, -1.0.
      bspec.curl = dial(adef.curl, adef.curl_change, si, -1.0f, 1.0f);
      float base_mass_radius =
          sspec.mass_radius > 0.0f ? sspec.mass_radius : sspec.geom_radius;
      float base_mass_length =
          sspec.mass_length > 0.0f ? sspec.mass_length : sspec.geom_length;
      bspec.geom_radius = sspec.geom_radius * radius_scale;
      bspec.geom_length = sspec.geom_length * length_scale;
      bspec.mass_radius = base_mass_radius * radius_scale;
      bspec.mass_length = base_mass_length * length_scale;
      // Total mass is the kind's, from the tabulated (unscaled) mass
      // capsule; the dials reshape the inertia but never the weight.
      // (x5: the bg rig has always run these densities at 5x.)
      {
        dMass m;
        dMassSetCappedCylinder(&m, sspec.density * 5.0f, 3, base_mass_radius,
                               base_mass_length);
        bspec.mass = static_cast<float>(m.mass);
      }
      for (int i = 0; i < 3; ++i) {
        bspec.parent_anchor[i] = sspec.parent_anchor[i];
        bspec.child_anchor[i] = sspec.child_anchor[i];
      }
      // The parent anchor lives in the previous segment's frame, so it
      // follows that segment's length; the child anchor is our own.
      bspec.parent_anchor[2] *= (si > 0) ? length_scale_at(si - 1) : 1.0f;
      bspec.child_anchor[2] *= length_scale;
      bspec.linear_stiffness = sspec.linear_stiffness;
      bspec.linear_damping = sspec.linear_damping;
      bspec.angular_stiffness = sspec.angular_stiffness;
      bspec.angular_damping = sspec.angular_damping;
      if (antenna) {
        // Stiffness/damping drift counts from the root joint, so a
        // chain can be rigid at the base and floppy at the tip.
        float stiffness =
            dial(adef.stiffness, adef.stiffness_change, si, 0.0f, 1.0f);
        float damping = dial(adef.damping, adef.damping_change, si, 0.0f, 1.0f);
        bspec.linear_stiffness *= std::pow(10.0f, stiffness);
        bspec.linear_damping *= std::pow(10.0f, damping);
        bspec.angular_stiffness *= std::pow(800.0f, stiffness);
        bspec.angular_damping *= std::pow(8000.0f, damping);
      }
    }
  }
  return bodies;
}

// Dev aid (BA_BG_RIG_TEST_ANTENNAS; test_game_run --bg-rig-test-antennas):
// every definition-form character grows one ANTENNA_3 on each attach
// target, sticking straight out of the body, so the bg rig's anchor feed
// can be eyeballed in debug-draw mode from a known rest pose. No art; the
// debug view draws the sim capsules exactly.
static auto BgRigTestAntennasEnabled() -> bool {
  static const bool enabled = getenv("BA_BG_RIG_TEST_ANTENNAS") != nullptr;
  return enabled;
}

static void AppendBgRigTestAntenna(
    base::CharacterAttachTarget target,
    std::vector<base::BasicSpazDef::AttachmentDef>* defs) {
  base::BasicSpazDef::AttachmentDef adef;
  adef.type = base::CharacterAttachmentType::kAntenna3;
  // Head: straight up. Torso/pelvis: straight back (180 about y turns
  // the +z chain around).
  if (target == base::CharacterAttachTarget::kHead) {
    const float pos[3] = {0.0f, 0.23f, 0.0f};
    const float rot[4] = {0.707107f, -0.707107f, 0.0f, 0.0f};
    std::copy(pos, pos + 3, adef.position);
    std::copy(rot, rot + 4, adef.rotation);
  } else {
    const float pos[3] = {
        0.0f, 0.0f,
        target == base::CharacterAttachTarget::kTorso ? -0.15f : -0.12f};
    const float rot[4] = {0.0f, 0.0f, 1.0f, 0.0f};
    std::copy(pos, pos + 3, adef.position);
    std::copy(rot, rot + 4, adef.rotation);
  }
  // Stiff enough to hold pose with a little sag and a slight curl, so
  // both the anchor transform and the joint chain are visible.
  adef.stiffness = 0.8f;
  adef.damping = 0.7f;
  adef.drag = 0.5f;
  adef.curl = 0.2f;
  adef.length = 0.5f;
  adef.segments.resize(3);
  defs->push_back(std::move(adef));
}

// Prototype (BA_BG_LIMBS; test_game_run --bg-limbs): every spaz's
// character rig also simulates its arms and legs on the bg thread,
// driven by the same joint targets as the main-sim limbs, which stay
// on. Debug draw shows the bg set in green offset in x beside the
// main-sim ragdoll for a side-by-side comparison.
void SpazNode::BuildLimbRigConfig_(
    base::BGDynamicsCharacterKind::Config* config) {
  using Kind = base::BGDynamicsCharacterKind;
  const int torso = static_cast<int>(base::CharacterAttachTarget::kTorso);
  const int pelvis = static_cast<int>(base::CharacterAttachTarget::kPelvis);
  // Bodies, in the fixed limb order (see the joint list below).
  auto add_body = [&](int anchor, float radius, float length, float mass_radius,
                      float mass_length, float density_mult,
                      float collide_stiffness, float collide_damping,
                      float friction) {
    assert(config->limb_body_count < Kind::kMaxLimbBodies);
    Kind::LimbBodySpec& b = config->limb_bodies[config->limb_body_count++];
    b.anchor = anchor;
    b.radius = radius;
    b.length = length;
    b.mass_radius = mass_radius > 0.0f ? mass_radius : radius;
    b.mass_length = mass_length > 0.0f ? mass_length : length;
    // RigidBody::SetDimensions runs densities at 5x too.
    dMass m;
    if (length > 0.0f) {
      dMassSetCappedCylinder(&m, 5.0f * density_mult, 3, b.mass_radius,
                             b.mass_length);
    } else {
      dMassSetSphere(&m, 5.0f * density_mult, b.mass_radius);
    }
    b.mass = static_cast<float>(m.mass);
    b.collide_stiffness = collide_stiffness;
    b.collide_damping = collide_damping;
    b.friction = friction;
  };
  // Contact softness mirrors CollideCallback: upper limbs 10x10 (arms)
  // with the upper-leg scaling on top; lower arms 10/1; lower legs and
  // toes with their own scalings; toes also get a tenth the friction.
  float ankle_len = 0.26f - ankle_radius_ * 2.0f;
  add_body(torso, 0.06f, 0.16f, 0.0f, 0.0f, kUpperArmDensity, 100.0f, 1.0f,
           0.5f);  // 0 upper right arm
  add_body(torso, 0.06f, 0.13f, 0.06f, 0.16f, kLowerArmDensity, 10.0f, 1.0f,
           0.5f);  // 1 lower right arm
  add_body(torso, 0.06f, 0.16f, 0.0f, 0.0f, kUpperArmDensity, 100.0f, 1.0f,
           0.5f);  // 2 upper left arm
  add_body(torso, 0.06f, 0.13f, 0.06f, 0.16f, kLowerArmDensity, 10.0f, 1.0f,
           0.5f);  // 3 lower left arm
  add_body(pelvis, thigh_radius_, 0.12f, 0.05f, 0.12f, kUpperLegDensity,
           10.0f * kUpperLegCollideStiffness * 10.0f,
           1.0f * kUpperLegCollideDamping, 0.5f);  // 4 upper right leg
  add_body(pelvis, ankle_radius_, ankle_len, 0.07f, 0.12f, kLowerLegDensity,
           10.0f * kLowerLegCollideStiffness, 1.0f * kLowerLegCollideDamping,
           0.5f);  // 5 lower right leg
  add_body(pelvis, thigh_radius_, 0.12f, 0.05f, 0.12f, kUpperLegDensity,
           10.0f * kUpperLegCollideStiffness * 10.0f,
           1.0f * kUpperLegCollideDamping, 0.5f);  // 6 upper left leg
  add_body(pelvis, ankle_radius_, ankle_len, 0.07f, 0.12f, kLowerLegDensity,
           10.0f * kLowerLegCollideStiffness, 1.0f * kLowerLegCollideDamping,
           0.5f);  // 7 lower left leg
  add_body(pelvis, 0.075f, 0.0f, 0.0f, 0.0f, kToesDensity,
           10.0f * kToesCollideStiffness, 1.0f * kToesCollideDamping,
           0.05f);  // 8 right toes
  add_body(pelvis, 0.075f, 0.0f, 0.0f, 0.0f, kToesDensity,
           10.0f * kToesCollideStiffness, 1.0f * kToesCollideDamping,
           0.05f);  // 9 left toes

  // Joints, in SpazJoint order from kSpazJointUpperRightArm on (the
  // neck and pelvis joints stay main-sim). Parents: -1 - anchor index
  // for a twin. anchor2 values are the construction-time tweaks from
  // the main-sim rig; anchor1 and everything else come from the
  // targets.
  const int t_parent = -1 - torso;
  const int p_parent = -1 - pelvis;
  auto add_joint = [&](int parent, int child, float a2x, float a2y, float a2z,
                       bool positions_child) {
    assert(config->limb_joint_count < Kind::kMaxLimbJoints);
    Kind::LimbJointSpec& j = config->limb_joints[config->limb_joint_count++];
    j.parent = parent;
    j.child = child;
    j.anchor2[0] = a2x;
    j.anchor2[1] = a2y;
    j.anchor2[2] = a2z;
    j.positions_child = positions_child;
  };
  add_joint(t_parent, 0, 0.02f, 0.0f, -0.1f, true);   // upper right arm
  add_joint(0, 1, 0.0f, 0.0f, -0.08f, true);          // lower right arm
  add_joint(t_parent, 2, -0.02f, 0.0f, -0.1f, true);  // upper left arm
  add_joint(2, 3, 0.0f, 0.0f, -0.08f, true);          // lower left arm
  add_joint(p_parent, 4, 0.0f, 0.0f, -0.05f, true);   // upper right leg
  add_joint(4, 5, 0.0f, 0.0f, -0.05f, true);          // lower right leg
  add_joint(p_parent, 6, 0.0f, 0.0f, -0.05f, true);   // upper left leg
  add_joint(6, 7, 0.0f, 0.0f, -0.05f, true);          // lower left leg
  add_joint(5, 8, 0.0f, -0.04f, 0.0f, true);          // right toes
  add_joint(5, 8, -0.1f, -0.04f, 0.0f, false);        // right toes 2
  add_joint(7, 9, 0.0f, -0.04f, 0.0f, true);          // left toes
  add_joint(7, 9, 0.1f, -0.04f, 0.0f, false);         // left toes 2
  add_joint(p_parent, 5, 0.0f, 0.0f, 0.05f, false);   // right leg ik
  add_joint(p_parent, 7, 0.0f, 0.0f, 0.05f, false);   // left leg ik
  add_joint(t_parent, 1, 0.0f, 0.0f, 0.07f, false);   // right arm ik
  add_joint(t_parent, 3, 0.0f, 0.0f, 0.07f, false);   // left arm ik
  static_assert(kSpazJointLeftArmIK - kSpazJointUpperRightArm + 1 == 16,
                "limb joint list must cover every SpazJoint after pelvis");

  // Targeted self-collision, mirroring PreFilterCollision: lower arms
  // against the head, torso and their own side's upper leg; lower
  // legs against each other.
  const int head = -1 - static_cast<int>(base::CharacterAttachTarget::kHead);
  auto add_pair = [&](int a, int b) {
    assert(config->collision_pair_count < Kind::kMaxCollisionPairs);
    Kind::CollisionPair& pair =
        config->collision_pairs[config->collision_pair_count++];
    pair.a = a;
    pair.b = b;
  };
  add_pair(1, head);      // lower right arm vs head
  add_pair(1, t_parent);  // lower right arm vs torso
  add_pair(1, 4);         // lower right arm vs upper right leg
  add_pair(3, head);      // lower left arm vs head
  add_pair(3, t_parent);  // lower left arm vs torso
  add_pair(3, 6);         // lower left arm vs upper left leg
  add_pair(5, 7);         // lower legs vs each other
}

void SpazNode::UpdateAttachments_() {
  bool changed = false;
  bool want_limbs = UseBgLimbs_();
  // (The twins copy the torso's shape and mass, so a torso resize
  // rebuilds too.)
  if (want_limbs != rig_has_limbs_ || rig_torso_radius_ != torso_radius_
      || (want_limbs
          && (rig_limb_thigh_radius_ != thigh_radius_
              || rig_limb_ankle_radius_ != ankle_radius_))) {
    changed = true;
  }
  for (int ti = 0; ti < base::kCharacterAttachTargetCount; ++ti) {
    auto& target = attachment_targets_[ti];
    std::vector<base::BasicSpazDef::AttachmentDef> desired;
    if (CharacterForm_() && spaz_def_->def().has_spaz()) {
      desired = spaz_def_->def().spaz().attachments[ti];
      if (BgRigTestAntennasEnabled()) {
        AppendBgRigTestAntenna(static_cast<base::CharacterAttachTarget>(ti),
                               &desired);
      }
    }
    if (AttachmentDefsEqual(desired, target.defs)) {
      continue;
    }
    target.defs = std::move(desired);
    changed = true;
  }
  if (!changed) {
    return;
  }
  // Any change rebuilds the whole rig: it is one island, and its flat
  // body order follows target order.
  attachment_rig_.reset();
  if (scene()->bg_dynamics_world() == nullptr) {
    return;
  }
  base::BGDynamicsCharacterKind::Config config;
  int bodies = 0;
  for (int ti = 0; ti < base::kCharacterAttachTargetCount; ++ti) {
    auto& target = attachment_targets_[ti];
    target.body_start = bodies;
    RigidBody* body =
        AttachTargetBody_(static_cast<base::CharacterAttachTarget>(ti));
    if (!body) {
      continue;
    }
    dMass mass;
    dBodyGetMass(body->body(), &mass);
    config.anchors[ti].mass = static_cast<float>(mass.mass);
    // The twin's collision shape: the body's own geom, for the rig's
    // targeted self-collision pairs.
    {
      auto& aspec = config.anchors[ti];
      const float* dims = body->dimensions();
      if (body->shape() == RigidBody::Shape::kBox) {
        aspec.shape = 2;
        aspec.dims[0] = dims[0];
        aspec.dims[1] = dims[1];
        aspec.dims[2] = dims[2];
      } else {
        aspec.shape = 1;
        aspec.dims[0] = dims[0];
      }
      // PreFilterCollision: head and torso collide with any broken-off
      // part of us; the pelvis does not.
      aspec.collides_loose_limbs =
          (ti == static_cast<int>(base::CharacterAttachTarget::kHead)
           || ti == static_cast<int>(base::CharacterAttachTarget::kTorso));
    }
    bodies += AppendAttachmentsToRigConfig(target.defs, ti, &config);
  }
  config.anchor_count = base::kCharacterAttachTargetCount;
  rig_has_limbs_ = false;
  if (want_limbs) {
    BuildLimbRigConfig_(&config);
    rig_has_limbs_ = true;
    rig_limb_thigh_radius_ = thigh_radius_;
    rig_limb_ankle_radius_ = ankle_radius_;
  }
  rig_torso_radius_ = torso_radius_;
  if (bodies > 0 || want_limbs) {
    attachment_rig_ = std::make_unique<base::BGDynamicsCharacterRig>(
        scene()->bg_dynamics_world(), config);
    rig_snap_ = true;
  }
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

void SpazNode::set_name(const std::string& val) {
  name_ = val;
  // Kick any needed background OS-span measures for the name right at
  // set-time rather than waiting for its first draw; warm-font
  // measures usually land before that draw, avoiding a blank first
  // frame for the name tag. Fully async.
  g_base->text_graphics->WarmUpStringAsync(name_);
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
  highlight_attr_ = vals;
  // In character form the definition owns highlight.
  if (!CharacterForm_()) {
    highlight_ = vals;
  }
}
void SpazNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for color",
                    PyExcType::kValue);
  }
  color_attr_ = vals;
  color_attr_set_ = true;
  SetDrawColor_(vals);
}

void SpazNode::SetDrawColor_(const std::vector<float>& vals) {
  assert(vals.size() == 3);
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
    area_of_interest_ = scene()->render_view()->camera()->NewAreaOfInterest();
    UpdateAreaOfInterest();
  }

  // Destroy if need be.
  if (!val && area_of_interest_) {
    scene()->render_view()->camera()->DeleteAreaOfInterest(area_of_interest_);
    area_of_interest_ = nullptr;
  }
}

void SpazNode::SetCurseDeathTime(millisecs_t val) {
  curse_death_time_ = val;

  // Start ticking sound.
  if (curse_death_time_ != 0) {
    if (tick_play_id_ == 0xFFFFFFFF) {
      base::AudioSource* s = scene()->NewAudioSource();
      if (s) {
        s->SetLooping(true);
        const dReal* p_head = dGeomGetPosition(body_head_->geom());
        s->SetPosition(p_head[0], p_head[1], p_head[2]);
        tick_play_id_ = s->Play(g_scene_v1->assets().ticking_crazy.get());
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
      scene()->render_view()->camera()->DeleteAreaOfInterest(area_of_interest_);
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
        if (base::SoundAsset* sound = RandomDeathSound_()) {
          if (base::AudioSource* source = scene()->NewAudioSource()) {
            const dReal* p_head = dGeomGetPosition(body_head_->geom());
            source->SetPosition(p_head[0], p_head[1], p_head[2]);
            voice_play_id_ = source->Play(sound);
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
  ApplyStyle_();
}

void SpazNode::ApplyStyle_() {
  // Character form: the definition supplies physique and look; style
  // is ignored entirely.
  if (CharacterForm_()) {
    ApplyCharacterDef_();
    UpdateBodiesForStyle();
    return;
  }

  // Legacy form: the style preset supplies both.
  ninja_ = (style_ == "ninja");
  pirate_ = (style_ == "pirate");
  frosty_ = (style_ == "frosty");

  // Start with defaults.
  female_ = false;
  female_hair_ = false;
  eyeless_ = false;
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

  // The legacy presets fold their gait tweaks into two flags; express
  // them as the same numeric slots a character definition carries so
  // the sim code has a single vocabulary.
  thigh_radius_ = female_ ? 0.06f : 0.04f;
  ankle_radius_ = female_ ? 0.045f : 0.07f;
  step_separation_ = (female_ ? 0.03f : 0.08f) * (ninja_ ? 0.7f : 1.0f);
  idle_arm_stiffness_ = female_ ? 0.2f : 1.0f;
  arm_swing_ = female_ ? 0.3f : 0.6f;
  idle_sway_ = female_ ? 0.02f : 0.05f;
  draw_hair_ = female_hair_;
  SetDrawColor_(color_attr_);
  highlight_ = highlight_attr_;
  // Only definitions carry a third color; legacy masks have stray blue
  // data, so style form keeps it at white (the no-op).
  highlight2_ = {1.0f, 1.0f, 1.0f};

  // Fold the legacy eye flags into the per-eye styles the draw code
  // consumes (character definitions set these directly).
  base::CharacterEyeStyle both =
      (eyeless_ || frosty_)
          ? base::CharacterEyeStyle::kNone
          : (has_eyelids_ ? base::CharacterEyeStyle::kRegular
                          : base::CharacterEyeStyle::kLidless);
  eye_style_right_ = both;
  eye_style_left_ = pirate_ ? base::CharacterEyeStyle::kNone : both;

  UpdateBodiesForStyle();
}

void SpazNode::ApplyCharacterDef_() {
  assert(spaz_def_.exists());
  // A definition this build can't use (no representation we
  // understand) is the standard spaz in every respect; a usable one
  // supplies physique unconditionally and its look only once its media
  // is local (the standin look until then -- physics must never wait
  // on media).
  static const base::BasicSpazDef kStandardSpaz;
  const base::BasicSpazDef& d =
      spaz_def_->def().has_spaz() ? spaz_def_->def().spaz() : kStandardSpaz;
  const bool look_ready =
      spaz_def_->def().has_spaz() && spaz_def_->def().spaz_media_ready();
  const base::BasicSpazDef& look = look_ready ? d : kStandardSpaz;

  // Physique.
  torso_radius_ = d.torso_radius;
  shoulder_offset_x_ = d.shoulder_offset[0];
  shoulder_offset_y_ = d.shoulder_offset[1];
  shoulder_offset_z_ = d.shoulder_offset[2];
  thigh_radius_ = d.thigh_radius;
  ankle_radius_ = d.ankle_radius;
  // Hair comes only from the attachments list in definition form (the
  // legacy female-hair rig belongs to the style path alone).
  female_hair_ = false;
  step_separation_ = d.step_separation;
  idle_arm_stiffness_ = d.idle_arm_stiffness;
  arm_swing_ = d.arm_swing;
  idle_sway_ = d.idle_sway;

  // Look. Our color attr, once set, overrides the definition's color.
  if (color_attr_set_ || !look.has_color) {
    SetDrawColor_(color_attr_);
  } else {
    SetDrawColor_({look.color[0], look.color[1], look.color[2]});
  }
  highlight_ = {look.highlight[0], look.highlight[1], look.highlight[2]};
  highlight2_ = {look.highlight2[0], look.highlight2[1], look.highlight2[2]};
  eye_style_left_ = look.eye_style_left;
  eye_style_right_ = look.eye_style_right;
  eye_scale_ = look.eye_scale;
  eye_offset_x_ = look.eye_offset[0];
  eye_offset_y_ = look.eye_offset[1];
  eye_offset_z_ = look.eye_offset[2];
  eye_color_red_ = look.eye_color[0];
  eye_color_green_ = look.eye_color[1];
  eye_color_blue_ = look.eye_color[2];
  eye_ball_color_red_ = look.eyeball_color[0];
  eye_ball_color_green_ = look.eyeball_color[1];
  eye_ball_color_blue_ = look.eyeball_color[2];
  eye_lid_color_red_ = look.eyelid_color[0];
  eye_lid_color_green_ = look.eyelid_color[1];
  eye_lid_color_blue_ = look.eyelid_color[2];
  default_eye_lid_angle_ = look.eyelid_angle;
  reflection_scale_ = look.reflection_scale;
  flippers_ = look.flippers;
  // Winged iff the definition supplies a wing mesh (mesh presence is
  // the switch; the standin look has no wings).
  wings_ = !look.wing_mesh.name.empty();
  draw_hair_ = false;
}

void SpazNode::SetSpazDef(SpazDef* val) {
  spaz_def_ = val;
  if (val) {
    // Media loads lazily; we display, so load now (before the look
    // is derived below).
    val->RetryMedia();
  }
  // Physique and look both come from the definition now (or the
  // legacy style path again if it was cleared).
  ApplyStyle_();
}

// Effective-media resolution. The two forms never mix: with a character
// set, the explicit media attrs are ignored outright (future characters
// may use entirely different mesh topologies); what we draw/play is the
// definition's media once local, and the standin until then.

auto SpazNode::MeshData_(
    const Object::Ref<SceneMesh>& explicit_mesh,
    const Object::Ref<base::MeshAsset>& standin,
    Object::Ref<base::MeshAsset> base::BasicSpazMedia::* def_field) const
    -> base::MeshAsset* {
  if (CharacterForm_()) {
    if (spaz_def_->def().spaz_media_ready()) {
      return (spaz_def_->def().spaz_media().*def_field).get();
    }
    return standin.get();
  }
  return explicit_mesh.exists() ? explicit_mesh->mesh_data() : nullptr;
}

auto SpazNode::TextureData_(
    const Object::Ref<SceneTexture>& explicit_texture,
    const Object::Ref<base::TextureAsset>& standin,
    Object::Ref<base::TextureAsset> base::BasicSpazMedia::* def_field) const
    -> base::TextureAsset* {
  if (CharacterForm_()) {
    if (spaz_def_->def().spaz_media_ready()) {
      return (spaz_def_->def().spaz_media().*def_field).get();
    }
    return standin.get();
  }
  return explicit_texture.exists() ? explicit_texture->texture_data() : nullptr;
}

auto SpazNode::RandomSoundData_(
    const std::vector<Object::Ref<SceneSound> >& explicit_sounds,
    std::initializer_list<const Object::Ref<base::SoundAsset>*> standin,
    std::vector<Object::Ref<base::SoundAsset> > base::BasicSpazMedia::*
        def_field) const -> base::SoundAsset* {
  if (CharacterForm_()) {
    if (spaz_def_->def().spaz_media_ready()) {
      const auto& list = spaz_def_->def().spaz_media().*def_field;
      if (list.empty()) {
        return nullptr;
      }
      // NOLINTNEXTLINE yes I know; rand bad.
      return list[rand() % list.size()].get();
    }
    if (standin.size() == 0) {
      return nullptr;
    }
    // NOLINTNEXTLINE yes I know; rand bad.
    return (*(standin.begin() + (rand() % standin.size())))->get();
  }
  SceneSound* sound = GetRandomMedia(explicit_sounds);
  return sound ? sound->GetSoundData() : nullptr;
}

auto SpazNode::HeadMeshData_() const -> base::MeshAsset* {
  return MeshData_(head_mesh_, g_scene_v1->assets().standin_head,
                   &base::BasicSpazMedia::head_mesh);
}
auto SpazNode::TorsoMeshData_() const -> base::MeshAsset* {
  return MeshData_(torso_mesh_, g_scene_v1->assets().standin_torso,
                   &base::BasicSpazMedia::torso_mesh);
}
auto SpazNode::PelvisMeshData_() const -> base::MeshAsset* {
  return MeshData_(pelvis_mesh_, g_scene_v1->assets().standin_pelvis,
                   &base::BasicSpazMedia::pelvis_mesh);
}
auto SpazNode::UpperArmMeshData_() const -> base::MeshAsset* {
  return MeshData_(upper_arm_mesh_, g_scene_v1->assets().standin_upper_arm,
                   &base::BasicSpazMedia::upper_arm_mesh);
}
auto SpazNode::ForearmMeshData_() const -> base::MeshAsset* {
  return MeshData_(forearm_mesh_, g_scene_v1->assets().standin_forearm,
                   &base::BasicSpazMedia::forearm_mesh);
}
auto SpazNode::HandMeshData_() const -> base::MeshAsset* {
  return MeshData_(hand_mesh_, g_scene_v1->assets().standin_hand,
                   &base::BasicSpazMedia::hand_mesh);
}
auto SpazNode::UpperLegMeshData_() const -> base::MeshAsset* {
  return MeshData_(upper_leg_mesh_, g_scene_v1->assets().standin_upper_leg,
                   &base::BasicSpazMedia::upper_leg_mesh);
}
auto SpazNode::LowerLegMeshData_() const -> base::MeshAsset* {
  return MeshData_(lower_leg_mesh_, g_scene_v1->assets().standin_lower_leg,
                   &base::BasicSpazMedia::lower_leg_mesh);
}
auto SpazNode::ToesMeshData_() const -> base::MeshAsset* {
  return MeshData_(toes_mesh_, g_scene_v1->assets().standin_toes,
                   &base::BasicSpazMedia::toes_mesh);
}
auto SpazNode::ColorTextureData_() const -> base::TextureAsset* {
  return TextureData_(color_texture_, g_scene_v1->assets().standin_color,
                      &base::BasicSpazMedia::color_texture);
}
auto SpazNode::ColorMaskTextureData_() const -> base::TextureAsset* {
  return TextureData_(color_mask_texture_,
                      g_scene_v1->assets().standin_color_mask,
                      &base::BasicSpazMedia::color_mask_texture);
}
auto SpazNode::RandomJumpSound_() const -> base::SoundAsset* {
  const auto& a = g_scene_v1->assets();
  return RandomSoundData_(jump_sounds_,
                          {&a.standin_jump01, &a.standin_jump02,
                           &a.standin_jump03, &a.standin_jump04},
                          &base::BasicSpazMedia::jump_sounds);
}
auto SpazNode::RandomAttackSound_() const -> base::SoundAsset* {
  const auto& a = g_scene_v1->assets();
  return RandomSoundData_(attack_sounds_,
                          {&a.standin_attack01, &a.standin_attack02,
                           &a.standin_attack03, &a.standin_attack04},
                          &base::BasicSpazMedia::attack_sounds);
}
auto SpazNode::RandomImpactSound_() const -> base::SoundAsset* {
  const auto& a = g_scene_v1->assets();
  return RandomSoundData_(impact_sounds_,
                          {&a.standin_impact01, &a.standin_impact02,
                           &a.standin_impact03, &a.standin_impact04},
                          &base::BasicSpazMedia::impact_sounds);
}
auto SpazNode::RandomDeathSound_() const -> base::SoundAsset* {
  const auto& a = g_scene_v1->assets();
  return RandomSoundData_(death_sounds_, {&a.standin_death01},
                          &base::BasicSpazMedia::death_sounds);
}
auto SpazNode::RandomPickupSound_() const -> base::SoundAsset* {
  const auto& a = g_scene_v1->assets();
  return RandomSoundData_(pickup_sounds_, {&a.standin_pickup01},
                          &base::BasicSpazMedia::pickup_sounds);
}
auto SpazNode::WingMeshData_() const -> base::MeshAsset* {
  if (CharacterForm_() && spaz_def_->def().spaz_media_ready()) {
    return spaz_def_->def().spaz_media().wing_mesh.get();
  }
  return g_scene_v1->assets().wing.get();
}
auto SpazNode::WingTextureData_() const -> base::TextureAsset* {
  if (CharacterForm_() && spaz_def_->def().spaz_media_ready()) {
    if (auto* tex = spaz_def_->def().spaz_media().wing_texture.get()) {
      return tex;
    }
    // No wing texture in the definition: wings share the character's
    // own color texture, so a custom winged character can lay its wing
    // UVs into its one atlas. (A definition wanting the stock wing art
    // references it explicitly, as the legacy winged styles do.)
    return spaz_def_->def().spaz_media().color_texture.get();
  }
  // Legacy bool-driven wings always wear the stock art.
  return g_scene_v1->assets().wings.get();
}
auto SpazNode::WingTintTextureData_() const -> base::TextureAsset* {
  if (CharacterForm_() && spaz_def_->def().spaz_media_ready()) {
    if (auto* tex = spaz_def_->def().spaz_media().wing_tint_texture.get()) {
      return tex;
    }
    // No wing tint mask in the definition: share the character's own
    // color mask, same one-atlas rule as the wing color texture.
    return spaz_def_->def().spaz_media().color_mask_texture.get();
  }
  // Legacy bool-driven wings: solid black mask, so color/highlight
  // leave the stock wing art untouched (the historical look).
  return g_scene_v1->assets().black.get();
}
auto SpazNode::RandomFallSound_() const -> base::SoundAsset* {
  const auto& a = g_scene_v1->assets();
  return RandomSoundData_(fall_sounds_, {&a.standin_fall01},
                          &base::BasicSpazMedia::fall_sounds);
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
  if (UseSyntheticPunch_() || !main_sim_limbs_) {
    const float* v = pose_.synthetic_fist_velocity();
    vals[0] = v[0];
    vals[1] = v[1];
    vals[2] = v[2];
    return vals;
  }
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

auto SpazNode::UseSyntheticPunch_() const -> bool {
  return scene()->protocol_version() >= kProtocolVersionSyntheticPunch;
}

auto SpazNode::UseBgLimbs_() const -> bool {
  static const int s_override = [] {
    const char* v = getenv("BA_SPAZ_LIMBS");
    if (v == nullptr) {
      return -1;
    }
    std::string_view sv{v};
    if (sv == "bg") {
      return 1;
    }
    if (sv == "main") {
      return 0;
    }
    g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                         "BA_SPAZ_LIMBS should be 'main' or 'bg'; ignoring.");
    return -1;
  }();
  if (s_override >= 0) {
    return s_override == 1;
  }
  // An activity can keep the old dynamics for its spazzes (the
  // tutorial's recorded input script is calibrated against them).
  if (GlobalsNode* globals = scene()->globals_node()) {
    if (globals->legacy_spaz_limbs()) {
      return false;
    }
  }
  return scene()->protocol_version() >= kProtocolVersionBgLimbs;
}

auto SpazNode::LimbRenderMatrix_(int limb, Matrix44f* m) -> bool {
  assert(limb >= 0 && limb < kLimbCount);
  if (UseBgLimbs_()) {
    const base::BGDynamicsCharacterRig::Output* out =
        attachment_rig_ ? attachment_rig_->output() : nullptr;
    if (!out || limb >= static_cast<int>(out->limbs.size())) {
      return false;
    }
    if (shattered_) {
      *m = out->limbs[limb].world;
      return true;
    }
    RigidBody* anchor = AttachTargetBody_(
        static_cast<base::CharacterAttachTarget>(out->limbs[limb].anchor));
    if (!anchor) {
      return false;
    }
    // (Row-vector convention: relative first, then the anchor.)
    *m = out->limbs[limb].relative * anchor->GetTransform();
    return true;
  }
  RigidBody* bodies[kLimbCount] = {
      upper_right_arm_body_.get(), lower_right_arm_body_.get(),
      upper_left_arm_body_.get(),  lower_left_arm_body_.get(),
      upper_right_leg_body_.get(), lower_right_leg_body_.get(),
      upper_left_leg_body_.get(),  lower_left_leg_body_.get(),
      right_toes_body_.get(),      left_toes_body_.get()};
  if (!bodies[limb]) {
    return false;
  }
  *m = bodies[limb]->GetTransform();
  return true;
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
      if (base::SoundAsset* sound = RandomPickupSound_()) {
        if (auto* source = scene()->NewAudioSource()) {
          const dReal* p_head = dGeomGetPosition(body_head_->geom());
          source->SetPosition(p_head[0], p_head[1], p_head[2]);
          voice_play_id_ = source->Play(sound);
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
  // 1 float for the run-cycle phase (pose roll_amt)
  return 4;
}

auto SpazNode::GetResyncData() -> std::vector<uint8_t> {
  std::vector<uint8_t> data(4, 0);
  char* ptr = reinterpret_cast<char*>(&(data[0]));
  Utils::EmbedFloat32(&ptr, pose_.roll_amt());
  return data;
}

void SpazNode::ApplyResyncData(const std::vector<uint8_t>& data) {
  const char* ptr = reinterpret_cast<const char*>(&(data[0]));
  pose_.set_roll_amt(Utils::ExtractFloat32(&ptr));
}

void SpazNode::PlayHurtSound() {
  if (dead_ || invincible_) {
    return;
  }
  if (base::SoundAsset* sound = RandomImpactSound_()) {
    if (auto* source = scene()->NewAudioSource()) {
      const dReal* p_top = dGeomGetPosition(body_head_->geom());
      g_base->audio->PushSourceStopSoundCall(voice_play_id_);
      source->SetPosition(p_top[0], p_top[1], p_top[2]);
      voice_play_id_ = source->Play(sound);
      source->End();
    }
  }
}

}  // namespace ballistica::scene_v1
