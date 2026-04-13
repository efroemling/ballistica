// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/dynamics/rigid_body.h"

#include "ballistica/base/graphics/component/render_component.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/dynamics/part.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"
#include "ode/ode_collision_util.h"

namespace ballistica::scene_v1 {

// whether to send our net states as half float format
#define USE_HALF_FLOATS 1

#define EMBED_POS_FLOAT Utils::EmbedFloat32
#define EXTRACT_POS_FLOAT Utils::ExtractFloat32
#define POS_FLOAT_DATA_SIZE 4

#if USE_HALF_FLOATS
#define FLOAT_DATA_SIZE 2
#define EMBED_FLOAT Utils::EmbedFloat16NBO
#define EXTRACT_FLOAT Utils::ExtractFloat16NBO
#else
#define FLOAT_DATA_SIZE 4
#define EMBED_FLOAT Utils::EmbedFloat32
#define EXTRACT_FLOAT Utils::ExtractFloat32
#endif

#define ABSOLUTE_EPSILON 0.001f

RigidBody::RigidBody(int id_in, Part* part_in, Type type_in, Shape shape_in,
                     uint32_t collide_type_in, uint32_t collide_mask_in,
                     SceneCollisionMesh* collision_mesh_in, uint32_t flags)
    : type_(type_in),
      id_(id_in),
      creation_time_(part_in->node()->scene()->time()),
      shape_(shape_in),
      part_(part_in),
      collision_mesh_(collision_mesh_in),
      collide_type_(collide_type_in),
      collide_mask_(collide_mask_in),
      flags_(flags) {
  blend_time_ = creation_time_;

#if BA_DEBUG_BUILD
  for (int i = 0; i < 3; i++) {
    prev_pos_[i] = prev_vel_[i] = prev_a_vel_[i] = 0.0f;
  }
#endif  // BA_DEBUG_BUILD

  assert(part_.exists());
  birth_time_ = part_->node()->scene()->stepnum();
  dynamics_ = part_->node()->scene()->dynamics();

  // Add ourself to the part.
  part_->AddBody(this);

  // Create the geom(s).
  switch (shape_) {
    case Shape::kSphere: {
      dimensions_[0] = dimensions_[1] = dimensions_[2] = 0.3f;
      geoms_.resize(1);
      geoms_[0] = dCreateSphere(dynamics_->ode_space(), dimensions_[0]);
      break;
    }

    case Shape::kBox: {
      dimensions_[0] = dimensions_[1] = dimensions_[2] = 0.6f;
      geoms_.resize(1);
      geoms_[0] = dCreateBox(dynamics_->ode_space(), dimensions_[0],
                             dimensions_[1], dimensions_[2]);
      break;
    }

    case Shape::kCapsule: {
      dimensions_[0] = dimensions_[1] = 0.3f;
      geoms_.resize(1);
      geoms_[0] = dCreateCCylinder(dynamics_->ode_space(), dimensions_[0],
                                   dimensions_[1]);
      break;
    }

    case Shape::kCylinder: {
      int sphere_count = 8;
      float inc = 360.0f / static_cast<float>(sphere_count);

      // Transform geom and sphere.
      geoms_.resize(static_cast<uint32_t>(2 * sphere_count + 1));
      dimensions_[0] = dimensions_[1] = 0.3f;
      float sub_rad = dimensions_[1] * 0.5f;
      float offset = dimensions_[0] - sub_rad;
      for (int i = 0; i < sphere_count; i++) {
        Vector3f p =
            Matrix44fRotate(Vector3f(0, 1, 0), static_cast<float>(i) * inc)
            * Vector3f(offset, 0, 0);
        geoms_[i * 2] = dCreateGeomTransform(dynamics_->ode_space());
        geoms_[i * 2 + 1] = dCreateSphere(nullptr, sub_rad);
        dGeomTransformSetGeom(geoms_[i * 2], geoms_[i * 2 + 1]);
        dGeomSetPosition(geoms_[i * 2 + 1], p.v[0], p.v[1], p.v[2]);
      }

      // One last center sphere to keep stuff from getting stuck in our middle.
      geoms_[geoms_.size() - 1] =
          dCreateSphere(dynamics_->ode_space(), sub_rad);

      break;
    }

    case Shape::kTrimesh: {
      // NOTE - we don't add trimeshes do the collision space - we handle them
      // specially..
      dimensions_[0] = dimensions_[1] = dimensions_[2] = 0.6f;
      assert(collision_mesh_.exists());
      collision_mesh_->collision_mesh_data()->Load();
      dGeomID g = dCreateTriMesh(
          nullptr, collision_mesh_->collision_mesh_data()->GetMeshData(),
          nullptr, nullptr, nullptr);
      geoms_.push_back(g);
      dynamics_->AddTrimesh(g);
      break;
    }

    default:
      throw Exception();
  }

  for (auto&& i : geoms_) {
    dGeomSetData(i, this);
  }

  if (type_ == Type::kBody) {
    assert(body_ == nullptr);
    body_ = dBodyCreate(dynamics_->ode_world());

    // For cylinders we only set the transform geoms, not the spheres.
    if (shape_ == Shape::kCylinder) {
      for (size_t i = 0; i < geoms_.size(); i += 2) {
        dGeomSetBody(geoms_[i], body_);
      }
      // Our center sphere.
      dGeomSetBody(geoms_[geoms_.size() - 1], body_);
    } else {
      dGeomSetBody(geoms_[0], body_);
    }
  }
  SetDimensions(dimensions_[0], dimensions_[1], dimensions_[2]);
}

void RigidBody::ApplyToRenderComponent(base::RenderComponent* c) {
  const dReal* pos_in;
  const dReal* r_in;
  auto geom = geoms_[0];
  if (type() == scene_v1::RigidBody::Type::kBody) {
    pos_in = dBodyGetPosition(body_);
    r_in = dBodyGetRotation(body_);
  } else {
    pos_in = dGeomGetPosition(geom);
    r_in = dGeomGetRotation(geom);
  }
  float pos[3];
  float r[12];
  for (int x = 0; x < 3; x++) {
    pos[x] = pos_in[x];
  }
  pos[0] += blend_offset().x;
  pos[1] += blend_offset().y;
  pos[2] += blend_offset().z;
  for (int x = 0; x < 12; x++) {
    r[x] = r_in[x];
  }
  float matrix[16];
  matrix[0] = r[0];
  matrix[1] = r[4];
  matrix[2] = r[8];
  matrix[3] = 0;
  matrix[4] = r[1];
  matrix[5] = r[5];
  matrix[6] = r[9];
  matrix[7] = 0;
  matrix[8] = r[2];
  matrix[9] = r[6];
  matrix[10] = r[10];
  matrix[11] = 0;
  matrix[12] = pos[0];
  matrix[13] = pos[1];
  matrix[14] = pos[2];
  matrix[15] = 1;
  c->MultMatrix(matrix);
}

void RigidBody::Check() {
  if (type_ == Type::kBody) {
    const dReal* p = dBodyGetPosition(body_);
    const dReal* q = dBodyGetQuaternion(body_);
    const dReal* lv = dBodyGetLinearVel(body_);
    const dReal* av = dBodyGetAngularVel(body_);
    bool err = false;
    for (int i = 0; i < 3; i++) {
      if (std::isnan(p[i]) || std::isnan(q[i]) || std::isnan(lv[i])
          || std::isnan(av[i])) {
        err = true;
        break;
      }
      if (std::abs(p[i]) > 9999) err = true;
      if (std::abs(lv[i]) > 99999) err = true;
      if (std::abs(av[i]) > 9999) err = true;
    }
    if (std::isnan(q[3])) err = true;

    if (err) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "Got error in rbd values!");
    }
#if BA_DEBUG_BUILD
    for (int i = 0; i < 3; i++) {
      prev_pos_[i] = p[i];
      prev_vel_[i] = lv[i];
      prev_a_vel_[i] = av[i];
    }
#endif  // BA_DEBUG_BUILD
  }
}

RigidBody::~RigidBody() {
  if (shape_ == Shape::kTrimesh) {
    assert(geoms_.size() == 1);
    dynamics_->RemoveTrimesh(geoms_[0]);
  }

  // if we have any joints attached, kill them
  KillConstraints();

  // remove ourself from our parent part if we have one
  if (part_.exists()) {
    part_->RemoveBody(this);
  }
  if (type_ == Type::kBody) {
    assert(body_);
    dBodyDestroy(body_);
    body_ = nullptr;
  }
  assert(!geoms_.empty());
  for (auto&& i : geoms_) {
    dGeomDestroy(i);
  }
}

void RigidBody::KillConstraints() {
  while (joints_.begin() != joints_.end()) {
    (**joints_.begin()).Kill();
  }
}

auto RigidBody::GetEmbeddedSizeFull() -> int {
  assert(type_ == Type::kBody);

  const dReal* lv = dBodyGetLinearVel(body_);
  const dReal* av = dBodyGetAngularVel(body_);

  // always have 3 position, 4 quaternion, and 1 flag
  int full_size = 3 * POS_FLOAT_DATA_SIZE + FLOAT_DATA_SIZE * 4 + 1;

  // we  only send velocity values that are non-zero - calculate how many of
  // them we have
  for (int i = 0; i < 3; i++) {
    full_size += FLOAT_DATA_SIZE * (std::abs(lv[i] - 0) > ABSOLUTE_EPSILON);
    full_size += FLOAT_DATA_SIZE * (std::abs(av[i] - 0) > ABSOLUTE_EPSILON);
  }
  return full_size;
}

// store a body to a buffer
// FIXME - theoretically we should embed birth-time
// as this can affect collisions with this object
void RigidBody::EmbedFull(char** buffer) {
  assert(type_ == Type::kBody);

  const dReal* p = dBodyGetPosition(body_);
  const dReal* q = dBodyGetQuaternion(body_);
  const dReal* lv = dBodyGetLinearVel(body_);
  const dReal* av = dBodyGetAngularVel(body_);
  bool enabled = static_cast<bool>(dBodyIsEnabled(body_));
  bool lv_changed[3];
  bool av_changed[3];

  // only send velocities that are non-zero.
  // we always send position/rotation since that's not likely to be zero
  for (int i = 0; i < 3; i++) {
    lv_changed[i] = (std::abs(lv[i] - 0) > ABSOLUTE_EPSILON);
    av_changed[i] = (std::abs(av[i] - 0) > ABSOLUTE_EPSILON);
  }

  // embed a byte containing our enabled state as well as what velocities need
  // to be sent
  Utils::EmbedBools(buffer, lv_changed[0], lv_changed[1], lv_changed[2],
                    av_changed[0], av_changed[1], av_changed[2], enabled);

  EMBED_POS_FLOAT(buffer, p[0]);
  EMBED_POS_FLOAT(buffer, p[1]);
  EMBED_POS_FLOAT(buffer, p[2]);

  EMBED_FLOAT(buffer, q[0]);
  EMBED_FLOAT(buffer, q[1]);
  EMBED_FLOAT(buffer, q[2]);
  EMBED_FLOAT(buffer, q[3]);

  for (int i = 0; i < 3; i++) {
    if (lv_changed[i]) {
      EMBED_FLOAT(buffer, lv[i]);
    }
    if (av_changed[i]) {
      EMBED_FLOAT(buffer, av[i]);
    }
  }
}

// Position a body from buffer data.
void RigidBody::ExtractFull(const char** buffer) {
  assert(type_ == Type::kBody);

  dReal p[3], lv[3], av[3];
  dQuaternion q;

  bool lv_changed[3];
  bool av_changed[3];
  bool enabled;

  // Extract our byte telling which velocities are contained here as well as our
  // enable state.
  Utils::ExtractBools(buffer, &lv_changed[0], &lv_changed[1], &lv_changed[2],
                      &av_changed[0], &av_changed[1], &av_changed[2], &enabled);

  p[0] = EXTRACT_POS_FLOAT(buffer);
  p[1] = EXTRACT_POS_FLOAT(buffer);
  p[2] = EXTRACT_POS_FLOAT(buffer);

  q[0] = EXTRACT_FLOAT(buffer);
  q[1] = EXTRACT_FLOAT(buffer);
  q[2] = EXTRACT_FLOAT(buffer);
  q[3] = EXTRACT_FLOAT(buffer);

  for (int i = 0; i < 3; i++) {
    if (lv_changed[i]) {
      lv[i] = EXTRACT_FLOAT(buffer);
    } else {
      lv[i] = 0;
    }

    if (av_changed[i]) {
      av[i] = EXTRACT_FLOAT(buffer);
    } else {
      av[i] = 0;
    }
  }

  dBodySetPosition(body_, p[0], p[1], p[2]);
  dBodySetQuaternion(body_, q);
  dBodySetLinearVel(body_, lv[0], lv[1], lv[2]);
  dBodySetAngularVel(body_, av[0], av[1], av[2]);

  if (enabled) {
    dBodyEnable(body_);
  } else {
    dBodyDisable(body_);
  }
}

void RigidBody::Draw(base::RenderPass* pass, bool shaded) {
  assert(pass);
  base::RenderPass::Type pass_type = pass->type();
  // only passes we draw in are light_shadow and beauty
  if (pass_type != base::RenderPass::Type::kLightShadowPass
      && pass_type != base::RenderPass::Type::kBeautyPass) {
    return;
  }
  // assume trimeshes are landscapes and shouldn't be in shadow passes..
  if (shape_ == Shape::kTrimesh
      && (pass_type != base::RenderPass::Type::kBeautyPass)) {
    return;
  }
}

void RigidBody::AddCallback(CollideCallbackFunc callbackIn, void* data_in) {
  CollideCallback c{};
  c.callback = callbackIn;
  c.data = data_in;
  collide_callbacks_.push_back(c);
}

auto RigidBody::CallCollideCallbacks(dContact* contacts, int count,
                                     RigidBody* opposingbody) -> bool {
  // NOLINTNEXTLINE(readability-use-anyofallof)
  for (auto&& i : collide_callbacks_) {
    if (!i.callback(contacts, count, this, opposingbody, i.data)) {
      return false;
    }
  }
  return true;
}

void RigidBody::SetDimensions(float d1, float d2, float d3, float m1, float m2,
                              float m3, float density_mult) {
  dimensions_[0] = d1;
  dimensions_[1] = d2;
  dimensions_[2] = d3;

  if (m1 == 0.0f) m1 = d1;
  if (m2 == 0.0f) m2 = d2;
  if (m3 == 0.0f) m3 = d3;

  float density = 5.0f * density_mult;

  switch (shape_) {
    case Shape::kSphere:
      dGeomSphereSetRadius(geoms_[0], dimensions_[0]);
      break;
    case Shape::kBox:
      dGeomBoxSetLengths(geoms_[0], dimensions_[0], dimensions_[1],
                         dimensions_[2]);
      break;
    case Shape::kCapsule:
      dGeomCCylinderSetParams(geoms_[0], dimensions_[0], dimensions_[1]);
      break;
    case Shape::kCylinder: {
      int sphere_count = static_cast<int>(geoms_.size() / 2);
      float inc = 360.0f / static_cast<float>(sphere_count);
      float sub_rad = dimensions_[1] * 0.5f;
      float offset = dimensions_[0] - sub_rad;
      for (int i = 0; i < sphere_count; i++) {
        Vector3f p =
            Matrix44fRotate(Vector3f(0, 0, 1), static_cast<float>(i) * inc)
            * Vector3f(offset, 0, 0);
        dGeomSphereSetRadius(geoms_[i * 2 + 1], sub_rad);
        dGeomSetPosition(geoms_[i * 2 + 1], p.v[0], p.v[1], p.v[2]);
      }
      // Resize our center sphere.
      dGeomSphereSetRadius(geoms_[geoms_.size() - 1], sub_rad);
    }
    // A cylinder is really just a bunch of spheres - we just need to set the
    // length of their offsets.
    // dGeomBoxSetLengths(geoms[0],dimensions[0],dimensions[0],dimensions[1]);
    break;
    case Shape::kTrimesh:
      break;
    default:
      throw Exception();
  }

  // Create the body and set mass properties.
  if (type_ == Type::kBody) {
    dMass m;
    switch (shape_) {
      case Shape::kSphere:
        dMassSetSphere(&m, density, m1);
        break;
      case Shape::kBox:
        dMassSetBox(&m, density, m1, m2, m3);
        break;
      case Shape::kCapsule:
        dMassSetCappedCylinder(&m, density, 3, m1, m2);
        break;
      case Shape::kCylinder:
        dMassSetCylinder(&m, density, 3, m1, m2);
        break;
      case Shape::kTrimesh:  // NOLINT(bugprone-branch-clone)
        // Trimesh bodies not supported yet.
        throw Exception();
    }

    // Need to handle groups here.
    assert(geoms_.size() == 1 || shape_ == Shape::kCylinder);
    dBodySetMass(body_, &m);
  }
}

auto RigidBody::ApplyImpulse(float px, float py, float pz, float vx, float vy,
                             float vz, float fdirx, float fdiry, float fdirz,
                             float mag, float v_mag, float radius,
                             bool calc_only) -> float {
  assert(body_);
  float total_mag = 0.0f;

  dMass mass;
  dBodyGetMass(body_, &mass);

  bool horizontal_only = false;

  // FIXME - some hard-coded tweaks for the hockey-puck
  if (shape_ == Shape::kCylinder) {
    py -= 0.3f;
    if (v_mag > 0.0f) {
      v_mag *= 0.06f;  // punches
    } else {
      mag *= 3.0f;  // amp up explosions
    }
    horizontal_only = true;
  }

  if (radius <= 0.0f) {
    // Damage based on velocity difference.. lets just plug in our
    // center-of-mass velocity (otherwise we might get crazy large velocity
    // diffs due to spinning).

    // Ok for now we're not taking our velocity into account.
    dVector3 our_velocity = {0, 0, 0};

    dVector3 v_diff = {vx - our_velocity[0], vy - our_velocity[1],
                       vz - our_velocity[2]};

    dVector3 f = {fdirx, fdiry, fdirz};

    // normalize..
    float fDirLen = sqrtf(fdirx * fdirx + fdiry * fdiry + fdirz * fdirz);
    if (fDirLen > 0.0f) {
      f[0] /= fDirLen;
      f[1] /= fDirLen;
      f[2] /= fDirLen;
    } else {
      f[0] = 1.0f;  // just use (1,0,0)
    }

    // Lets only take large velocity diffs into account.
    // float vLen = std::max(0.0f,dVector3Length(v_diff)-2.0f);
    float vLen = dVector3Length(v_diff);

    total_mag = mag + vLen * v_mag;

    f[0] *= total_mag;
    f[1] *= total_mag;
    f[2] *= total_mag;

    // Exaggerate the force we apply in y (but don't count it towards damage).
    f[1] *= 2.0f;

    // General scale up.
    f[0] *= 1.8f;
    f[1] *= 1.8f;
    f[2] *= 1.8f;

    if (horizontal_only) {
      f[1] = 0.0f;
      py = dBodyGetPosition(body_)[1];
    }

    if (!calc_only) {
      dBodyEnable(body_);
      dBodyAddForceAtPos(body_, f[0], f[1], f[2], px, py, pz);
    }

  } else {
    // With radius.
    Vector3f us(dBodyGetPosition(body_));
    Vector3f them(px, py, pz);
    if (them == us) {
      them = us + Vector3f(0.0f, 0.001f, 0.0f);
    }
    Vector3f diff = them - us;
    float len = (them - us).Length();
    if (len == 0.0f) {
      len = 0.0001f;
    }

    if (len < radius) {
      float amt = 1.0f - (len / radius);

      if (v_mag > 0.0f) {
        throw Exception("FIXME - handle vmag for radius>0 case");
      }

      // Factor in our mass so a given impulse affects various sized things
      // equally.
      float this_mag = (mag * amt) * mass.mass;

      // amt *= amt;  // squared falloff..
      // amt = pow(amt, 1.5f);  // biased falloff

      total_mag += this_mag;

      Vector3f f = diff * (-this_mag / len);

      // Randomize applied force a bit to keep things from looking too clean and
      // simple.
      const dReal* pos = dBodyGetPosition(body_);
      dReal apply_pos[3] = {pos[0] + 0.6f * (RandomFloat() - 0.5f),
                            pos[1] + 0.6f * (RandomFloat() - 0.5f),
                            pos[2] + 0.6f * (RandomFloat() - 0.5f)};

      if (horizontal_only) {
        f.y = 0.0f;
        apply_pos[1] = us.y;
      }

      // Exaggerate up/down component.
      f.x *= 0.5f;
      if (f.y > 0.0f) {
        f.y *= 2.0f;
      }
      f.z *= 0.5f;

      if (!calc_only) {
        dBodyEnable(body_);
        dBodyAddForceAtPos(body_, f.x, f.y, f.z, apply_pos[0], apply_pos[1],
                           apply_pos[2]);
      }
    }
  }
  return total_mag;
}

void RigidBody::ApplyGlobalImpulse(float px, float py, float pz, float fx,
                                   float fy, float fz) {
  if (type_ != Type::kBody) {
    return;
  }
  dBodyEnable(body_);
  dBodyAddForceAtPos(body_, fx / kGameStepSeconds, fy / kGameStepSeconds,
                     fz / kGameStepSeconds, px, py, pz);
}

RigidBody::Joint::Joint() = default;

void RigidBody::Joint::SetJoint(dxJointFixed* id_in, Scene* scene) {
  Kill();
  creation_time_ = scene->time();
  id_ = id_in;
}

RigidBody::Joint::~Joint() { Kill(); }

void RigidBody::Joint::AttachToBodies(RigidBody* b1_in, RigidBody* b2_in) {
  assert(id_);
  b1_ = b1_in;
  b2_ = b2_in;
  dBodyID b_id_1 = nullptr;
  dBodyID b_id_2 = nullptr;
  if (b1_) {
    b1_->Wake();
    b1_->AddJoint(this);
    b_id_1 = b1_->body();
  }
  if (b2_) {
    b2_->Wake();
    b2_->AddJoint(this);
    b_id_2 = b2_->body();
  }
  dJointAttach(id_, b_id_1, b_id_2);
}

void RigidBody::Joint::Kill() {
  if (id_) {
    if (b1_) {
      b1_->RemoveJoint(this);

      // Also wake the body (this joint could be suspending it motionless).
      assert(b1_->body());
      dBodyEnable(b1_->body());
    }
    if (b2_) {
      b2_->RemoveJoint(this);

      // Also wake the body (this joint could be suspending it motionless).
      assert(b2_->body());
      dBodyEnable(b2_->body());
    }
    dJointDestroy(id_);
    id_ = nullptr;
    b1_ = b2_ = nullptr;
  }
}

auto RigidBody::GetTransform() -> Matrix44f {
  Matrix44f matrix{kMatrix44fIdentity};
  const dReal* pos_in;
  const dReal* r_in;
  if (type() == RigidBody::Type::kBody) {
    pos_in = dBodyGetPosition(body());
    r_in = dBodyGetRotation(body());
  } else {
    pos_in = dGeomGetPosition(geom());
    r_in = dGeomGetRotation(geom());
  }
  float pos[3];
  float r[12];
  for (int x = 0; x < 3; x++) {
    pos[x] = pos_in[x];
  }
  pos[0] += blend_offset().x;
  pos[1] += blend_offset().y;
  pos[2] += blend_offset().z;
  for (int x = 0; x < 12; x++) {
    r[x] = r_in[x];
  }
  matrix.m[0] = r[0];
  matrix.m[1] = r[4];
  matrix.m[2] = r[8];
  matrix.m[3] = 0;
  matrix.m[4] = r[1];
  matrix.m[5] = r[5];
  matrix.m[6] = r[9];
  matrix.m[7] = 0;
  matrix.m[8] = r[2];
  matrix.m[9] = r[6];
  matrix.m[10] = r[10];
  matrix.m[11] = 0;
  matrix.m[12] = pos[0];
  matrix.m[13] = pos[1];
  matrix.m[14] = pos[2];
  matrix.m[15] = 1;
  return matrix;
}

void RigidBody::AddBlendOffset(float x, float y, float z) {
  //  blend_offset_.x += x;
  //  blend_offset_.y += y;
  //  blend_offset_.z += z;
}

void RigidBody::UpdateBlending() {
  // FIXME - this seems broken. We never update blend_time_ currently
  //  and its also set to time whereas we're comparing it with steps.
  //  Should revisit.
  //  millisecs_t diff = part()->node()->scene()->stepnum() - blend_time_;
  //  diff = std::min(millisecs_t{10}, diff);
  //  for (millisecs_t i = 0; i < diff; i++) {
  //    blend_offset_.x *= 0.995f;
  //    blend_offset_.y *= 0.995f;
  //    blend_offset_.z *= 0.995f;
  //  }
}

}  // namespace ballistica::scene_v1
