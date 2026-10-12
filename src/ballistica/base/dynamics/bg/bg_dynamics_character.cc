// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_character.h"

#include <algorithm>
#include <atomic>
#include <cmath>

#include "ballistica/base/dynamics/bg/bg_dynamics_world_server.h"
#include "ballistica/base/dynamics/terrain_collider.h"

namespace ballistica::base {

// ---- Logic-thread handle. ----

BGDynamicsCharacterRig::BGDynamicsCharacterRig(BGDynamicsWorld* world,
                                               const Config& config)
    : world_(world) {
  assert(g_base->InLogicThread());
  slot_ = world_->channel<BGDynamicsCharacterKind>().Create(config);
}

BGDynamicsCharacterRig::~BGDynamicsCharacterRig() {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsCharacterKind>().Destroy(slot_);
}

void BGDynamicsCharacterRig::SetAnchor(int anchor, const Matrix44f& transform) {
  assert(g_base->InLogicThread());
  assert(anchor >= 0 && anchor < BGDynamicsCharacterKind::kMaxAnchors);
  auto& input = world_->channel<BGDynamicsCharacterKind>().input(slot_);
  input.anchors[anchor] = transform;
  input.have_anchors = true;
}

void BGDynamicsCharacterRig::Snap() {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsCharacterKind>().input(slot_);
  input.snap_count++;
}

void BGDynamicsCharacterRig::SetSkip(float skip) {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsCharacterKind>().input(slot_);
  input.skip = std::clamp(skip, 0.0f, 1.0f);
}

void BGDynamicsCharacterRig::SetFrozen(bool frozen) {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsCharacterKind>().input(slot_);
  input.frozen = frozen;
}

void BGDynamicsCharacterRig::SetShattered(bool shattered) {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsCharacterKind>().input(slot_);
  input.shattered = shattered;
}

void BGDynamicsCharacterRig::SetLimbJointTargets(
    const BGDynamicsCharacterKind::LimbJointTarget* targets, int count) {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsCharacterKind>().input(slot_);
  count = std::min(count, BGDynamicsCharacterKind::kMaxLimbJoints);
  for (int i = 0; i < count; ++i) {
    input.limb_joints[i] = targets[i];
  }
  input.have_limb_targets = true;
}

auto BGDynamicsCharacterRig::output() const -> const Output* {
  assert(g_base->InLogicThread());
  return world_->channel<BGDynamicsCharacterKind>().output(slot_);
}

// ---- Worker-thread sim. ----

namespace {

// Matrix44f's operator* composes left-to-right ("apply a, then b"):
// a * b is the matrix that transforms by a first and b second. Every
// composition below is written with that in mind.

// Spread rig phases across steps so rigs at the same skip value don't
// all go live on the same frames (golden-ratio sequence: low
// discrepancy for any rig count).
std::atomic<uint32_t> g_rig_phase_counter{0};

// ODE rotation (row-major 3x4) + position <-> our column-major matrix.
auto MatrixFromBody(dBodyID body) -> Matrix44f {
  const dReal* pos = dBodyGetPosition(body);
  const dReal* r = dBodyGetRotation(body);
  Matrix44f m{kMatrix44fIdentity};
  m.m[0] = static_cast<float>(r[0]);
  m.m[1] = static_cast<float>(r[4]);
  m.m[2] = static_cast<float>(r[8]);
  m.m[4] = static_cast<float>(r[1]);
  m.m[5] = static_cast<float>(r[5]);
  m.m[6] = static_cast<float>(r[9]);
  m.m[8] = static_cast<float>(r[2]);
  m.m[9] = static_cast<float>(r[6]);
  m.m[10] = static_cast<float>(r[10]);
  m.m[12] = static_cast<float>(pos[0]);
  m.m[13] = static_cast<float>(pos[1]);
  m.m[14] = static_cast<float>(pos[2]);
  return m;
}

// World-space angular velocity that carries rotation `prev` to `now`
// over `dt` (shortest arc).
auto AngularVelocityBetween(const Matrix44f& prev, const Matrix44f& now,
                            float dt) -> Vector3f {
  auto to_quat = [](const Matrix44f& m, dQuaternion q) {
    dMatrix3 r;
    r[0] = m.m[0];
    r[4] = m.m[1];
    r[8] = m.m[2];
    r[1] = m.m[4];
    r[5] = m.m[5];
    r[9] = m.m[6];
    r[2] = m.m[8];
    r[6] = m.m[9];
    r[10] = m.m[10];
    r[3] = r[7] = r[11] = 0.0f;
    dQfromR(q, r);
  };
  dQuaternion qp, qn, delta;
  to_quat(prev, qp);
  to_quat(now, qn);
  // delta = qn * conj(qp): the world-frame rotation from prev to now.
  dQuaternion qp_conj = {qp[0], -qp[1], -qp[2], -qp[3]};
  dQMultiply0(delta, qn, qp_conj);
  if (delta[0] < 0) {
    for (auto& c : delta) {
      c = -c;
    }
  }
  float w = std::clamp(static_cast<float>(delta[0]), -1.0f, 1.0f);
  float angle = 2.0f * std::acos(w);
  float s = std::sqrt(std::max(0.0f, 1.0f - w * w));
  if (s < 1e-6f || dt <= 0.0f) {
    return {0.0f, 0.0f, 0.0f};
  }
  float scale = angle / (s * dt);
  return {static_cast<float>(delta[1]) * scale,
          static_cast<float>(delta[2]) * scale,
          static_cast<float>(delta[3]) * scale};
}

void SetBodyFromMatrix(dBodyID body, const Matrix44f& m) {
  dMatrix3 r;
  r[0] = m.m[0];
  r[4] = m.m[1];
  r[8] = m.m[2];
  r[1] = m.m[4];
  r[5] = m.m[5];
  r[9] = m.m[6];
  r[2] = m.m[8];
  r[6] = m.m[9];
  r[10] = m.m[10];
  r[3] = r[7] = r[11] = 0.0f;
  dBodySetPosition(body, m.m[12], m.m[13], m.m[14]);
  dBodySetRotation(body, r);
}

// Terrain contacts for attachment segments: the same soft, low-friction
// surface the legacy hair tufts got in the main sim (stiffness 200,
// damping 10, mu 0.1), so they brush over things rather than snag.
struct TerrainCollideContext {
  BGDynamicsWorldServer* server;
  dBodyID body;
  float erp;
  float cfm;
  float friction{0.1f};
};

void TerrainCollideCallback(void* data, dGeomID geom1, dGeomID geom2) {
  auto* ctx = static_cast<TerrainCollideContext*>(data);
  constexpr int kMaxContacts{8};
  dContact contact[kMaxContacts];
  int numc =
      dCollide(geom1, geom2, kMaxContacts, &contact[0].geom, sizeof(dContact));
  for (int i = 0; i < numc; ++i) {
    contact[i].surface.mode =
        dContactSoftCFM | dContactSoftERP | dContactApprox1;
    contact[i].surface.mu = ctx->friction;
    contact[i].surface.mu2 = 0;
    contact[i].surface.soft_erp = ctx->erp;
    contact[i].surface.soft_cfm = ctx->cfm;
    dJointID constraint =
        dJointCreateContact(ctx->server->ode_world(),
                            ctx->server->ode_contact_group(), contact + i);
    dJointAttach(constraint, ctx->body, nullptr);
  }
}

// Contacts between two of the rig's own geoms: the main sim's
// self-collision treatment (soft, no friction).
void CollideOwnPair(BGDynamicsWorldServer* server, dGeomID ga, dGeomID gb,
                    float erp, float cfm) {
  constexpr int kMaxContacts{4};
  dContact contact[kMaxContacts];
  int numc = dCollide(ga, gb, kMaxContacts, &contact[0].geom, sizeof(dContact));
  for (int c = 0; c < numc; ++c) {
    contact[c].surface.mode =
        dContactSoftCFM | dContactSoftERP | dContactApprox1;
    contact[c].surface.mu = 0.0f;
    contact[c].surface.mu2 = 0;
    contact[c].surface.soft_erp = erp;
    contact[c].surface.soft_cfm = cfm;
    dJointID constraint = dJointCreateContact(
        server->ode_world(), server->ode_contact_group(), contact + c);
    dJointAttach(constraint, dGeomGetBody(ga), dGeomGetBody(gb));
  }
}

}  // namespace

BGDynamicsCharacterKind::Sim::Sim(const Config& config,
                                  BGDynamicsWorldServer* server)
    : config_(config) {
  anchor_count_ = std::clamp(config_.anchor_count, 0, kMaxAnchors);
  uint32_t n = g_rig_phase_counter.fetch_add(1);
  float phase = static_cast<float>(n) * 0.6180339887f;
  skip_acc_ = phase - std::floor(phase);
  jitter_state_ = n * 2654435761u + 1u;
}

BGDynamicsCharacterKind::Sim::~Sim() {
  for (auto& b : bodies_) {
    if (b.joint) {
      dJointDestroy(b.joint);
    }
  }
  for (auto& j : limb_joints_) {
    if (j.joint) {
      dJointDestroy(j.joint);
    }
  }
  for (auto& b : limb_bodies_) {
    if (b.geom) {
      dGeomDestroy(b.geom);
    }
    if (b.body) {
      dBodyDestroy(b.body);
    }
  }
  for (auto& b : bodies_) {
    if (b.geom) {
      dGeomDestroy(b.geom);
    }
    if (b.body) {
      dBodyDestroy(b.body);
    }
  }
  for (int i = 0; i < anchor_count_; ++i) {
    if (twin_geoms_[i]) {
      dGeomDestroy(twin_geoms_[i]);
    }
    if (twins_[i]) {
      dBodyDestroy(twins_[i]);
    }
  }
}

void BGDynamicsCharacterKind::Sim::SetInput(const Input& input) {
  input_ = input;
}

void BGDynamicsCharacterKind::Sim::CreateBodies_(
    BGDynamicsWorldServer* server) {
  assert(anchor_count_ > 0 && !twins_[0]);
  dWorldID world = server->ode_world();
  float step_seconds = server->step_seconds();

  // The twins: no gravity, and effectively immovable in the solve
  // (the anchor's mass x1000). Their poses and velocities come from
  // the feed every step, so anything the limbs or contacts did to them
  // inside a step would be thrown away; with ordinary mass that share
  // of every constraint impulse was lost each step and the limbs
  // jittered against a base that gave way and snapped back. (This ODE
  // has no kinematic bodies; huge mass is the same thing.)
  for (int i = 0; i < anchor_count_; ++i) {
    twins_[i] = dBodyCreate(world);
    dMass m;
    dMassSetSphereTotal(&m, config_.anchors[i].mass * 1000.0f, 0.28f);
    dBodySetMass(twins_[i], &m);
    dBodySetGravityMode(twins_[i], 0);
    // This world auto-sleeps slow bodies (chunks); a resting rig must
    // keep simulating or its springs freeze mid-droop.
    dBodySetAutoDisableFlag(twins_[i], 0);
    // Our island solves at the main sim's iteration count (stiff
    // springs and feet on terrain jitter at the world's light count).
    dBodySetSolverIterations(twins_[i], server->character_solver_iterations());
    SetBodyFromMatrix(twins_[i], input_.anchors[i]);
    // Its collision shape, if any (spaceless; only the targeted pairs
    // ever test against it).
    const AnchorSpec& aspec = config_.anchors[i];
    if (aspec.shape == 1) {
      twin_geoms_[i] = dCreateSphere(nullptr, aspec.dims[0]);
    } else if (aspec.shape == 2) {
      twin_geoms_[i] =
          dCreateBox(nullptr, aspec.dims[0], aspec.dims[1], aspec.dims[2]);
    }
    if (twin_geoms_[i]) {
      dGeomSetBody(twin_geoms_[i], twins_[i]);
    }
  }

  int count = std::min(config_.attachment_count, kMaxAttachments);
  for (int ai = 0; ai < count; ++ai) {
    const AttachmentSpec& aspec = config_.attachments[ai];
    int anchor = std::clamp(aspec.anchor, 0, anchor_count_ - 1);
    dBodyID parent = twins_[anchor];
    int seg_count = std::min(aspec.segment_count, kMaxSegments);
    for (int si = 0; si < seg_count; ++si) {
      const SegmentSpec& sspec = aspec.segments[si];
      Body entry;
      entry.anchor = anchor;
      entry.attachment = ai;
      entry.segment = si;
      entry.radius = sspec.geom_radius;
      entry.length = sspec.geom_length;
      entry.body = dBodyCreate(world);
      dMass sm;
      dMassSetCappedCylinderTotal(&sm, sspec.mass, 3, sspec.mass_radius,
                                  sspec.mass_length);
      dBodySetMass(entry.body, &sm);
      dBodySetAutoDisableFlag(entry.body, 0);
      dBodySetSolverIterations(entry.body,
                               server->character_solver_iterations());
      // Spaceless capsule; we hand it to the terrain collider ourselves
      // each step (no broadphase, no body-vs-body testing).
      entry.geom =
          dCreateCCylinder(nullptr, sspec.geom_radius, sspec.geom_length);
      dGeomSetBody(entry.geom, entry.body);
      // Start on the parent; the joint placement below fixes it up.
      SetBodyFromMatrix(entry.body, MatrixFromBody(parent));
      const float* a1 = (si == 0) ? aspec.position : sspec.parent_anchor;
      entry.joint = JointFixedEFCreateAnchored(
          world, parent, entry.body, step_seconds, sspec.linear_stiffness,
          sspec.linear_damping, sspec.angular_stiffness, sspec.angular_damping,
          a1, sspec.child_anchor, true);
      // Rest orientation: every joint bends by its segment's curl --
      // curl * 90 degrees about the local x axis, negative so a
      // positive curl lifts the chain toward local +y (a positive x
      // rotation would tip +z down). The root's bend sits on top of
      // the attachment rotation, in the rotated frame.
      dQuaternion curl_q;
      {
        float half = -sspec.curl * 0.25f * kPi;
        curl_q[0] = std::cos(half);
        curl_q[1] = std::sin(half);
        curl_q[2] = 0.0f;
        curl_q[3] = 0.0f;
      }
      if (si == 0) {
        dQuaternion rot_q = {aspec.rotation[0], aspec.rotation[1],
                             aspec.rotation[2], aspec.rotation[3]};
        dQMultiply0(entry.joint->qrel, rot_q, curl_q);
      } else {
        for (int qi = 0; qi < 4; ++qi) {
          entry.joint->qrel[qi] = curl_q[qi];
        }
      }
      parent = entry.body;
      bodies_.push_back(entry);
    }
  }
}

void BGDynamicsCharacterKind::Sim::CreateLimbs_(BGDynamicsWorldServer* server) {
  dWorldID world = server->ode_world();
  float step_seconds = server->step_seconds();
  int body_count = std::min(config_.limb_body_count, kMaxLimbBodies);
  for (int i = 0; i < body_count; ++i) {
    const LimbBodySpec& spec = config_.limb_bodies[i];
    LimbBody entry;
    entry.anchor = std::clamp(spec.anchor, 0, anchor_count_ - 1);
    entry.radius = spec.radius;
    entry.length = spec.length;
    entry.collide_stiffness = spec.collide_stiffness;
    entry.collide_damping = spec.collide_damping;
    entry.friction = spec.friction;
    entry.body = dBodyCreate(world);
    dMass m;
    if (spec.length > 0.0f) {
      dMassSetCappedCylinderTotal(&m, spec.mass, 3, spec.mass_radius,
                                  spec.mass_length);
      entry.geom = dCreateCCylinder(nullptr, spec.radius, spec.length);
    } else {
      dMassSetSphereTotal(&m, spec.mass, spec.mass_radius);
      entry.geom = dCreateSphere(nullptr, spec.radius);
    }
    dBodySetMass(entry.body, &m);
    dBodySetAutoDisableFlag(entry.body, 0);
    dBodySetSolverIterations(entry.body, server->character_solver_iterations());
    dGeomSetBody(entry.geom, entry.body);
    // Start on the anchor; the chain joints place it from there.
    SetBodyFromMatrix(entry.body, MatrixFromBody(twins_[entry.anchor]));
    limb_bodies_.push_back(entry);
  }
  int joint_count = std::min(config_.limb_joint_count, kMaxLimbJoints);
  for (int i = 0; i < joint_count; ++i) {
    const LimbJointSpec& spec = config_.limb_joints[i];
    const LimbJointTarget& tg = input_.limb_joints[i];
    dBodyID parent;
    if (spec.parent < 0) {
      parent = twins_[std::clamp(-1 - spec.parent, 0, anchor_count_ - 1)];
    } else {
      parent = limb_bodies_[std::clamp(spec.parent, 0, body_count - 1)].body;
    }
    dBodyID child =
        limb_bodies_[std::clamp(spec.child, 0, body_count - 1)].body;
    LimbJoint entry;
    entry.positions_child = spec.positions_child;
    entry.joint = JointFixedEFCreateAnchored(
        world, parent, child, step_seconds, tg.linear_stiffness,
        tg.linear_damping, tg.angular_stiffness, tg.angular_damping, tg.anchor1,
        spec.anchor2, spec.positions_child);
    for (int qi = 0; qi < 4; ++qi) {
      entry.joint->qrel[qi] = tg.qrel[qi];
    }
    limb_joints_.push_back(entry);
  }
}

void BGDynamicsCharacterKind::Sim::ApplyLimbTargets_() {
  int count = std::min(static_cast<int>(limb_joints_.size()), kMaxLimbJoints);
  for (int i = 0; i < count; ++i) {
    JointFixedEF* j = limb_joints_[i].joint;
    const LimbJointTarget& tg = input_.limb_joints[i];
    for (int k = 0; k < 3; ++k) {
      j->anchor1[k] = tg.anchor1[k];
    }
    // Frozen joints hold the rest rotation they latched on the way in
    // (the main sim latches *its* joints, which sit at slightly
    // different angles; taking those would snap our limbs to a foreign
    // pose). The springs still come through: the pose driver already
    // has them at their frozen values.
    if (!frozen_) {
      for (int k = 0; k < 4; ++k) {
        j->qrel[k] = tg.qrel[k];
      }
    }
    j->linearStiffness = tg.linear_stiffness;
    j->linearDamping = tg.linear_damping;
    j->angularStiffness = tg.angular_stiffness;
    j->angularDamping = tg.angular_damping;
  }
}

auto BGDynamicsCharacterKind::Sim::PairGeom_(int ref, float* stiffness,
                                             float* damping) -> dGeomID {
  if (ref < 0) {
    int anchor = -1 - ref;
    if (anchor < 0 || anchor >= anchor_count_) {
      return nullptr;
    }
    return twin_geoms_[anchor];
  }
  if (ref >= static_cast<int>(limb_bodies_.size())) {
    return nullptr;
  }
  const LimbBody& b = limb_bodies_[ref];
  *stiffness = std::max(*stiffness, b.collide_stiffness);
  *damping = std::max(*damping, b.collide_damping);
  return b.geom;
}

void BGDynamicsCharacterKind::Sim::CollideSelfPairs_(
    BGDynamicsWorldServer* server) {
  // The main sim's self-collision treatment: the limb's contact
  // softness (the stiffer of the two for limb-vs-limb) and no friction.
  // Shattered contacts harden (x100/x10) as in the main sim.
  int count = std::min(config_.collision_pair_count, kMaxCollisionPairs);
  float step_seconds = server->step_seconds();
  float stiffness_mult = shattered_ ? 100.0f : 1.0f;
  float damping_mult = shattered_ ? 10.0f : 1.0f;
  for (int i = 0; i < count; ++i) {
    const CollisionPair& pair = config_.collision_pairs[i];
    float stiffness = 0.0f;
    float damping = 0.0f;
    dGeomID ga = PairGeom_(pair.a, &stiffness, &damping);
    dGeomID gb = PairGeom_(pair.b, &stiffness, &damping);
    if (!ga || !gb || stiffness <= 0.0f) {
      continue;
    }
    float erp, cfm;
    CalcERPCFM(stiffness * stiffness_mult, damping * damping_mult, step_seconds,
               &erp, &cfm);
    CollideOwnPair(server, ga, gb, erp, cfm);
  }
  // Shattered: limbs that have broken loose also collide with the
  // twins that accept them (the main sim lets a broken part collide
  // with anything of its own character that will have it; the head
  // and torso always will). A limb is loose when its chain joint's
  // target springs have all gone to zero, which is exactly how the
  // pose driver expresses a broken joint. Limbs still attached keep
  // to the configured pairs: a hanging hand overlaps the hip, and the
  // main sim never lets those two touch.
  if (shattered_ && input_.have_limb_targets) {
    int joint_count =
        std::min(static_cast<int>(limb_joints_.size()), kMaxLimbJoints);
    for (int i = 0; i < joint_count; ++i) {
      if (!limb_joints_[i].positions_child) {
        continue;
      }
      const LimbJointTarget& tg = input_.limb_joints[i];
      bool loose = tg.linear_stiffness <= 0.0f && tg.angular_stiffness <= 0.0f
                   && tg.linear_damping <= 0.0f && tg.angular_damping <= 0.0f;
      if (!loose) {
        continue;
      }
      int child = config_.limb_joints[i].child;
      if (child < 0 || child >= static_cast<int>(limb_bodies_.size())) {
        continue;
      }
      const LimbBody& b = limb_bodies_[child];
      float erp, cfm;
      CalcERPCFM(b.collide_stiffness * stiffness_mult,
                 b.collide_damping * damping_mult, step_seconds, &erp, &cfm);
      for (int a = 0; a < anchor_count_; ++a) {
        if (twin_geoms_[a] && config_.anchors[a].collides_loose_limbs) {
          CollideOwnPair(server, b.geom, twin_geoms_[a], erp, cfm);
        }
      }
    }
  }
}

void BGDynamicsCharacterKind::Sim::PlaceOnAnchors_() {
  // Creation order is root-first within each chain, so one pass
  // resolves every chain off the (already-placed) twins.
  for (auto& b : bodies_) {
    JointFixedEFPositionBody(b.joint);
    dBodySetLinearVel(b.body, 0, 0, 0);
    dBodySetAngularVel(b.body, 0, 0, 0);
  }
  for (auto& j : limb_joints_) {
    if (j.positions_child) {
      JointFixedEFPositionBody(j.joint);
    }
  }
  for (auto& b : limb_bodies_) {
    dBodySetLinearVel(b.body, 0, 0, 0);
    dBodySetAngularVel(b.body, 0, 0, 0);
  }
}

auto BGDynamicsCharacterKind::Sim::TakeStep_() -> bool {
  float skip = input_.skip;
  if (skip <= 0.0f) {
    return true;
  }
  if (skip >= 1.0f) {
    return false;
  }
  // Error accumulator: live steps land every 1/(1-skip) steps on
  // average, evenly spaced, with +-20% jitter on the stride so no
  // repeating pattern can line up across rigs. The accumulator bounds
  // the gap, so jitter never produces bursts of skipped steps.
  jitter_state_ = jitter_state_ * 1664525u + 1013904223u;
  float u = static_cast<float>(jitter_state_ >> 8)
            / static_cast<float>(1u << 24);  // [0, 1)
  skip_acc_ += (1.0f - skip) * (0.8f + 0.4f * u);
  if (skip_acc_ >= 1.0f) {
    skip_acc_ -= 1.0f;
    return true;
  }
  return false;
}

void BGDynamicsCharacterKind::Sim::CarryWithAnchors_(const Matrix44f* deltas) {
  for (auto& b : bodies_) {
    SetBodyFromMatrix(b.body, MatrixFromBody(b.body) * deltas[b.anchor]);
  }
  for (auto& b : limb_bodies_) {
    SetBodyFromMatrix(b.body, MatrixFromBody(b.body) * deltas[b.anchor]);
  }
}

void BGDynamicsCharacterKind::Sim::SetFrozen_(bool frozen) {
  if (frozen == frozen_) {
    return;
  }
  frozen_ = frozen;
  // The main sim's frozen treatment for limbs and legacy hair: lock the
  // rest angle to the current pose and go stiff (linear x5, angular
  // x1000) with lighter damping (x0.2). Unfreezing restores the
  // configured springs; the rest angle stays wherever it was latched,
  // exactly as the main sim leaves its joints.
  //
  // Limbs: latch the chain joints (the ones the main sim freezes; the
  // toes-2 and IK joints stay live there too). Their springs arrive
  // in the targets, already scaled, and ApplyLimbTargets_ leaves the
  // latched rotation alone while frozen.
  if (frozen) {
    for (auto& j : limb_joints_) {
      if (j.positions_child) {
        JointFixedEFFreezeAngle(j.joint);
      }
    }
  }
  for (auto& b : bodies_) {
    const SegmentSpec& sspec =
        config_.attachments[b.attachment].segments[b.segment];
    if (frozen) {
      JointFixedEFFreezeAngle(b.joint);
      b.joint->linearStiffness = sspec.linear_stiffness * 5.0f;
      b.joint->linearDamping = sspec.linear_damping * 0.2f;
      b.joint->angularStiffness = sspec.angular_stiffness * 1000.0f;
      b.joint->angularDamping = sspec.angular_damping * 0.2f;
    } else {
      b.joint->linearStiffness = sspec.linear_stiffness;
      b.joint->linearDamping = sspec.linear_damping;
      b.joint->angularStiffness = sspec.angular_stiffness;
      b.joint->angularDamping = sspec.angular_damping;
    }
  }
}

void BGDynamicsCharacterKind::Sim::SetShattered_(bool shattered) {
  if (shattered == shattered_) {
    return;
  }
  shattered_ = shattered;
  if (!shattered) {
    shatter_handoff_steps_ = 0;
    return;
  }
  // The blast that shatters a character hits the main sim's limbs
  // directly; ours only hear about it through the twins, and the
  // blast's velocity reaches the twins a feed or two after the
  // shattered flag does (the main sim integrates it on its next
  // step). So for the first few steps after the edge every limb keeps
  // taking its anchor's velocity, as if still rigidly attached, and
  // only then flies free. They were moving with the body anyway; the
  // handoff is invisible, and without it the loose pieces are left
  // hanging in the air while the body rockets off.
  shatter_handoff_steps_ = 3;
}

void BGDynamicsCharacterKind::Sim::HandOffShatterVelocity_() {
  if (shatter_handoff_steps_ <= 0) {
    return;
  }
  --shatter_handoff_steps_;
  for (auto& b : limb_bodies_) {
    const dReal* v = dBodyGetLinearVel(twins_[b.anchor]);
    dBodySetLinearVel(b.body, v[0], v[1], v[2]);
  }
}

void BGDynamicsCharacterKind::Sim::ClampLimbVelocities_() {
  // The main sim's cap (SpazNode::Step): angular speed^2 400, linear
  // 300, or 100 for a shattering frozen character ("always looks too
  // fast").
  const float max_ang_sq = 400.0f;
  const float max_lin_sq = (frozen_ && shattered_) ? 100.0f : 300.0f;
  for (auto& b : limb_bodies_) {
    const dReal* av = dBodyGetAngularVel(b.body);
    float mag_sq = av[0] * av[0] + av[1] * av[1] + av[2] * av[2];
    if (mag_sq > max_ang_sq) {
      float scale = max_ang_sq / mag_sq;
      dBodySetAngularVel(b.body, av[0] * scale, av[1] * scale, av[2] * scale);
    }
    const dReal* lv = dBodyGetLinearVel(b.body);
    mag_sq = lv[0] * lv[0] + lv[1] * lv[1] + lv[2] * lv[2];
    if (mag_sq > max_lin_sq) {
      float scale = max_lin_sq / mag_sq;
      dBodySetLinearVel(b.body, lv[0] * scale, lv[1] * scale, lv[2] * scale);
    }
  }
}

void BGDynamicsCharacterKind::Sim::SetBodiesEnabled_(bool enabled) {
  if (enabled == bodies_enabled_) {
    return;
  }
  bodies_enabled_ = enabled;
  auto apply = enabled ? dBodyEnable : dBodyDisable;
  for (int i = 0; i < anchor_count_; ++i) {
    apply(twins_[i]);
  }
  for (auto& b : bodies_) {
    apply(b.body);
  }
  for (auto& b : limb_bodies_) {
    apply(b.body);
  }
}

void BGDynamicsCharacterKind::Sim::Step(BGDynamicsWorldServer* server) {
  if (!input_.have_anchors || anchor_count_ <= 0) {
    return;
  }
  bool fresh = false;
  if (!twins_[0]) {
    // Limbs need their first targets to be built; wait for them.
    if (config_.limb_joint_count > 0 && !input_.have_limb_targets) {
      return;
    }
    CreateBodies_(server);
    CreateLimbs_(server);
    fresh = true;
  }

  // Drive the twins: poses straight from the feed, linear velocities
  // from the pose deltas so the springs feel the anchors' motion. Also
  // note each anchor's motion since the last step (world space), for
  // carrying a skipped rig along.
  float step_seconds = server->step_seconds();
  bool snap = fresh || input_.snap_count != last_snap_count_;
  Matrix44f anchor_deltas[kMaxAnchors];
  for (int i = 0; i < anchor_count_; ++i) {
    const Matrix44f& anchor = input_.anchors[i];
    SetBodyFromMatrix(twins_[i], anchor);
    if (have_prev_anchors_ && !snap && step_seconds > 0.0f) {
      Vector3f vel = (anchor.GetTranslate() - prev_anchors_[i].GetTranslate())
                     / step_seconds;
      dBodySetLinearVel(twins_[i], vel.x, vel.y, vel.z);
      // And its spin, so joint damping and contacts see the anchor
      // turning (a spinning character's arms lag its torso otherwise).
      Vector3f avel =
          AngularVelocityBetween(prev_anchors_[i], anchor, step_seconds);
      dBodySetAngularVel(twins_[i], avel.x, avel.y, avel.z);
    } else {
      dBodySetLinearVel(twins_[i], 0, 0, 0);
      dBodySetAngularVel(twins_[i], 0, 0, 0);
    }
    anchor_deltas[i] = have_prev_anchors_ ? prev_anchors_[i].Inverse() * anchor
                                          : kMatrix44fIdentity;
    prev_anchors_[i] = anchor;
  }
  have_prev_anchors_ = true;

  if (snap) {
    SetBodiesEnabled_(true);
    PlaceOnAnchors_();
    last_snap_count_ = input_.snap_count;
  } else if (!input_.shattered && !TakeStep_()) {
    // Sitting this one out: ride the anchors rigidly, solve nothing.
    // (A shattered character never sits out: its loose pieces have no
    // anchor to ride and must keep falling.)
    CarryWithAnchors_(anchor_deltas);
    SetBodiesEnabled_(false);
    return;
  }
  SetBodiesEnabled_(true);
  SetFrozen_(input_.frozen);
  SetShattered_(input_.shattered);
  HandOffShatterVelocity_();
  if (input_.have_limb_targets) {
    ApplyLimbTargets_();
  }
  CollideSelfPairs_(server);

  // Terrain contacts for every segment (chunk-style: each capsule
  // against the terrain collider only).
  {
    TerrainCollideContext ctx{server, nullptr, 0.0f, 0.0f};
    CalcERPCFM(200.0f, 10.0f, step_seconds, &ctx.erp, &ctx.cfm);
    for (auto& b : bodies_) {
      ctx.body = b.body;
      server->terrain_collider()->CollideGeom(b.geom, &ctx,
                                              TerrainCollideCallback);
    }
    // Limbs: each with the main sim's contact softness for that part
    // (hardened x100/x10 once shattered, as there).
    float stiffness_mult = shattered_ ? 100.0f : 1.0f;
    float damping_mult = shattered_ ? 10.0f : 1.0f;
    for (auto& b : limb_bodies_) {
      ctx.body = b.body;
      ctx.friction = b.friction;
      CalcERPCFM(b.collide_stiffness * stiffness_mult,
                 b.collide_damping * damping_mult, step_seconds, &ctx.erp,
                 &ctx.cfm);
      server->terrain_collider()->CollideGeom(b.geom, &ctx,
                                              TerrainCollideCallback);
    }
  }

  ClampLimbVelocities_();

  // Per-attachment drag: bleed a bit of linear velocity so chains
  // trail nicely behind a moving anchor.
  for (auto& b : bodies_) {
    float drag = config_.attachments[b.attachment].drag;
    if (drag <= 0.0f) {
      continue;
    }
    float mult = 1.0f - 0.12f * drag;
    const dReal* v = dBodyGetLinearVel(b.body);
    dBodySetLinearVel(b.body, v[0] * mult, v[1] * mult, v[2] * mult);
  }
}

void BGDynamicsCharacterKind::Sim::GetOutput(Output* out) const {
  if (anchor_count_ <= 0 || !twins_[0]) {
    out->anchor_count = 0;
    out->bodies.clear();
    out->limbs.clear();
    return;
  }
  out->anchor_count = anchor_count_;
  Matrix44f anchor_inverses[kMaxAnchors];
  for (int i = 0; i < anchor_count_; ++i) {
    out->anchors[i] = MatrixFromBody(twins_[i]);
    anchor_inverses[i] = out->anchors[i].Inverse();
  }
  // (resize keeps capacity on a recycled output; see Output.)
  out->bodies.resize(bodies_.size());
  for (size_t i = 0; i < bodies_.size(); ++i) {
    const Body& b = bodies_[i];
    OutputBody& o = out->bodies[i];
    o.world = MatrixFromBody(b.body);
    o.relative = o.world * anchor_inverses[b.anchor];
    o.anchor = b.anchor;
    o.radius = b.radius;
    o.length = b.length;
  }
  out->limbs.resize(limb_bodies_.size());
  for (size_t i = 0; i < limb_bodies_.size(); ++i) {
    const LimbBody& b = limb_bodies_[i];
    OutputBody& o = out->limbs[i];
    o.world = MatrixFromBody(b.body);
    o.relative = o.world * anchor_inverses[b.anchor];
    o.anchor = b.anchor;
    o.radius = b.radius;
    o.length = b.length;
  }
}

}  // namespace ballistica::base
