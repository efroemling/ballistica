// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_GEOM_TRANSFORM_H_
#define BALLISTICA_BASE_DYNAMICS_GEOM_TRANSFORM_H_

#include "ballistica/shared/math/matrix44f.h"
#include "ode/ode_collision.h"

namespace ballistica::base {

/// Apply a transform matrix to a static (bodyless) ODE geom.
///
/// Our matrices are row-vector based (points are transformed as p*m) and
/// ODE's are column-vector based (v' = R*v), so the rotation part
/// transposes on the way across. Anything reading a transform back out of
/// ODE needs to do the same flip in reverse; see
/// RigidBody::ApplyToRenderComponent().
///
/// Note that any scale in the matrix is dropped; ODE geoms have no notion
/// of one.
inline void GeomSetTransform(dGeomID g, const Matrix44f& t) {
  dMatrix3 r;
  r[0] = t.m[0];
  r[1] = t.m[4];
  r[2] = t.m[8];
  r[3] = 0.0f;
  r[4] = t.m[1];
  r[5] = t.m[5];
  r[6] = t.m[9];
  r[7] = 0.0f;
  r[8] = t.m[2];
  r[9] = t.m[6];
  r[10] = t.m[10];
  r[11] = 0.0f;
  dGeomSetRotation(g, r);
  dGeomSetPosition(g, t.m[12], t.m[13], t.m[14]);
}

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_GEOM_TRANSFORM_H_
