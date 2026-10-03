// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/joint_fixed_ef.h"

#include <cassert>

#include "ode/ode_math.h"
#include "ode/ode_objects.h"

namespace ballistica::base {

void CalcERPCFM(float stiffness, float damping, float step_seconds, float* erp,
                float* cfm) {
  if (stiffness <= 0.0f && damping <= 0.0f) {
    (*erp) = 0.0f;
    // (*cfm) = dInfinity;  // doesn't seem to be happy...
    (*cfm) = 9999999999.0f;
  } else {
    (*erp) =
        (step_seconds * stiffness) / ((step_seconds * stiffness) + damping);
    (*cfm) = 1.0f / ((step_seconds * stiffness) + damping);
  }
}

namespace {

void FixedInit_(JointFixedEF* j) {
  dSetZero(j->qrel, 4);
  dSetZero(j->anchor1, 3);
  dSetZero(j->anchor2, 3);
  j->linearStiffness = 0.0f;
  j->linearDamping = 0.0f;
  j->angularStiffness = 0.0f;
  j->angularDamping = 0.0f;
  j->linearEnabled = true;
  j->angularEnabled = true;
  j->stepSeconds = 1.0f / 60.0f;
}

void SetBall_(JointFixedEF* joint, dxJoint::Info2* info, dVector3 anchor1,
              dVector3 anchor2) {
  assert(joint->node[1].body);

  // Anchor points in global coordinates with respect to body PORs.
  dVector3 a1, a2;

  int s = info->rowskip;

  // Set jacobian.
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

  // Set right hand side.
  dReal k = info->fps * info->erp;
  for (int j = 0; j < 3; j++) {
    info->c[j] = k
                 * (a2[j] + joint->node[1].body->pos[j] - a1[j]
                    - joint->node[0].body->pos[j]);
  }
}

void SetFixedOrientation_(JointFixedEF* joint, dxJoint::Info2* info,
                          dQuaternion qrel, int start_row) {
  assert(joint->node[1].body);  // We assume we're connected to 2 bodies.

  int s = info->rowskip;
  int start_index = start_row * s;

  // 3 rows to make body rotations equal.
  info->J1a[start_index] = 1;
  info->J1a[start_index + s + 1] = 1;
  info->J1a[start_index + s * 2 + 2] = 1;
  info->J2a[start_index] = -1;
  info->J2a[start_index + s + 1] = -1;
  info->J2a[start_index + s * 2 + 2] = -1;

  // Compute the right hand side. The first three elements will result
  // in relative angular velocity of the two bodies - this is set to
  // bring them back into alignment. The correcting angular velocity is
  //   |angular_velocity| = angle/time = erp*theta / stepsize
  //                      = (erp*fps) * theta
  //    angular_velocity  = |angular_velocity| * u
  //                      = (erp*fps) * theta * u
  // where rotation along unit length axis u by theta brings body 2's
  // frame to qrel with respect to body 1's frame. Using a small angle
  // approximation for sin(), this gives
  //    angular_velocity  = (erp*fps) * 2 * v
  // where the quaternion of the relative rotation between the two
  // bodies is
  //    q = [cos(theta/2) sin(theta/2)*u] = [s v]

  // Get qerr = relative rotation (rotation error) between two bodies.
  dQuaternion qerr, e;
  dQuaternion qq;
  dQMultiply1(qq, joint->node[0].body->q, joint->node[1].body->q);
  dQMultiply2(qerr, qq, qrel);
  if (qerr[0] < 0) {
    qerr[1] = -qerr[1];  // Adjust sign of qerr to make theta small.
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

void FixedGetInfo1_(JointFixedEF* j, dxJoint::Info1* info) {
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

void FixedGetInfo2_(JointFixedEF* joint, dxJoint::Info2* info) {
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
  // Linear component.
  if (do_linear) {
    float linear_erp = 0;
    float linear_cfm = 0;
    CalcERPCFM(joint->linearStiffness, joint->linearDamping, joint->stepSeconds,
               &linear_erp, &linear_cfm);
    info->erp = linear_erp;
    SetBall_(joint, info, joint->anchor1, joint->anchor2);
    info->cfm[0] = linear_cfm;
    info->cfm[1] = linear_cfm;
    info->cfm[2] = linear_cfm;
    offs += 3;
  }
  // Angular component.
  if (do_angular) {
    float angular_erp;
    float angular_cfm;
    CalcERPCFM(joint->angularStiffness, joint->angularDamping,
               joint->stepSeconds, &angular_erp, &angular_cfm);
    info->erp = angular_erp;
    SetFixedOrientation_(joint, info, joint->qrel, offs);
    info->cfm[offs] = angular_cfm;
    info->cfm[offs + 1] = angular_cfm;
    info->cfm[offs + 2] = angular_cfm;
  }
  info->erp = orig_erp;
}

dxJoint::Vtable g_fixed_vtable = {
    sizeof(JointFixedEF), (dxJoint::init_fn*)FixedInit_,
    (dxJoint::getInfo1_fn*)FixedGetInfo1_,
    (dxJoint::getInfo2_fn*)FixedGetInfo2_, dJointTypeNone};

// ODE keeps its object-list plumbing private; these mirror the bits we
// need to register a custom joint with a world.
void InitObject_(dObject* obj, dxWorld* w) {
  obj->world = w;
  obj->next = nullptr;
  obj->tome = nullptr;
  obj->userdata = nullptr;
  obj->tag = 0;
}

void AddObjectToList_(dObject* obj, dObject** first) {
  obj->next = *first;
  obj->tome = first;
  if (*first) (*first)->tome = &obj->next;
  (*first) = obj;
}

void JointInit_(dxWorld* w, dxJoint* j) {
  dIASSERT(w && j);
  InitObject_(j, w);
  j->vtable = nullptr;
  j->flags = 0;
  j->node[0].joint = j;
  j->node[0].body = nullptr;
  j->node[0].next = nullptr;
  j->node[1].joint = j;
  j->node[1].body = nullptr;
  j->node[1].next = nullptr;
  dSetZero(j->lambda, 6);
  AddObjectToList_(j, reinterpret_cast<dObject**>(&w->firstjoint));
  w->nj++;
}

auto Alloc_(dWorldID world, float step_seconds) -> JointFixedEF* {
  auto* j = static_cast<JointFixedEF*>(
      dAlloc(static_cast<size_t>(g_fixed_vtable.size)));
  JointInit_(world, j);
  j->vtable = &g_fixed_vtable;
  if (j->vtable->init) j->vtable->init(j);
  j->feedback = nullptr;
  j->stepSeconds = step_seconds;
  return j;
}

// Set qrel from the bodies' current relative rotation.
void SetFixed_(JointFixedEF* joint) {
  dUASSERT(joint, "bad joint argument");
  dUASSERT(joint->vtable == &g_fixed_vtable, "joint is not fixed");
  if (joint->node[0].body && joint->node[1].body) {
    dQMultiply1(joint->qrel, joint->node[0].body->q, joint->node[1].body->q);
  }
}

// Express a world point as anchors in each body's local frame.
void SetAnchors_(dxJoint* j, dReal x, dReal y, dReal z, dVector3 anchor1,
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

}  // namespace

void JointFixedEFPositionBody(JointFixedEF* j) {
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

void JointFixedEFFreezeAngle(JointFixedEF* j) {
  dQMultiply1(j->qrel, j->node[0].body->q, j->node[1].body->q);
}

auto JointFixedEFCreate(dWorldID world, dBodyID b1, dBodyID b2,
                        float step_seconds, float linear_stiffness,
                        float linear_damping, float angular_stiffness,
                        float angular_damping) -> JointFixedEF* {
  JointFixedEF* j = Alloc_(world, step_seconds);
  if (b1 && b2) {
    dJointAttach(j, b1, b2);
    SetFixed_(j);
    const dReal* p = dBodyGetPosition(b2);
    SetAnchors_(j, p[0], p[1], p[2], j->anchor1, j->anchor2);
  }
  j->linearStiffness = linear_stiffness;
  j->linearDamping = linear_damping;
  j->angularStiffness = angular_stiffness;
  j->angularDamping = angular_damping;
  return j;
}

auto JointFixedEFCreateAnchored(dWorldID world, dBodyID b1, dBodyID b2,
                                float step_seconds, float linear_stiffness,
                                float linear_damping, float angular_stiffness,
                                float angular_damping, const float* anchor1,
                                const float* anchor2, bool reposition)
    -> JointFixedEF* {
  assert(b1 && b2);
  JointFixedEF* j = Alloc_(world, step_seconds);
  dJointAttach(j, b1, b2);
  dQSetIdentity(j->qrel);
  for (int i = 0; i < 3; ++i) {
    j->anchor1[i] = anchor1[i];
    j->anchor2[i] = anchor2[i];
  }
  if (reposition) {
    JointFixedEFPositionBody(j);
  }
  j->linearStiffness = linear_stiffness;
  j->linearDamping = linear_damping;
  j->angularStiffness = angular_stiffness;
  j->angularDamping = angular_damping;
  return j;
}

}  // namespace ballistica::base
