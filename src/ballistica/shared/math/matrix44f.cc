// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/math/matrix44f.h"

namespace ballistica {

auto Matrix44fRotate(const Vector3f& axis, float angle) -> Matrix44f {
  // Page 466, Graphics Gems

  Matrix44f rotate{kMatrix44fIdentity};

  float s = sinf(-angle * kPiDeg);
  float c = cosf(-angle * kPiDeg);
  float t = 1 - c;

  Vector3f ax = axis / sqrtf(axis.LengthSquared());

  float x = ax.x;
  float y = ax.y;
  float z = ax.z;

  rotate.set(0, 0, t * x * x + c);
  rotate.set(1, 0, t * y * x + s * z);
  rotate.set(2, 0, t * z * x - s * y);

  rotate.set(0, 1, t * x * y - s * z);
  rotate.set(1, 1, t * y * y + c);
  rotate.set(2, 1, t * z * y + s * x);

  rotate.set(0, 2, t * x * z + s * y);
  rotate.set(1, 2, t * y * z - s * x);
  rotate.set(2, 2, t * z * z + c);

  return rotate;
}

auto Matrix44fRotate(float azimuth, float elevation) -> Matrix44f {
  Matrix44f rotate{kMatrix44fIdentity};

  float ca = cosf(azimuth * kPiDeg);
  float sa = sinf(azimuth * kPiDeg);
  float cb = cosf(elevation * kPiDeg);
  float sb = sinf(elevation * kPiDeg);

  rotate.set(0, 0, cb);
  rotate.set(1, 0, 0);
  rotate.set(2, 0, -sb);

  rotate.set(0, 1, -sa * sb);
  rotate.set(1, 1, ca);
  rotate.set(2, 1, -sa * cb);

  rotate.set(0, 2, ca * sb);
  rotate.set(1, 2, sa);
  rotate.set(2, 2, ca * cb);

  return rotate;
}

auto Matrix44fOrient(const Vector3f& x, const Vector3f& y, const Vector3f& z)
    -> Matrix44f {
  Matrix44f orient{kMatrix44fIdentity};

  orient.set(0, 0, x.x);
  orient.set(0, 1, x.y);
  orient.set(0, 2, x.z);

  orient.set(1, 0, y.x);
  orient.set(1, 1, y.y);
  orient.set(1, 2, y.z);

  orient.set(2, 0, z.x);
  orient.set(2, 1, z.y);
  orient.set(2, 2, z.z);

  return orient;
}

auto Matrix44fOrient(const Vector3f& direction, const Vector3f& up)
    -> Matrix44f {
  assert(direction.LengthSquared() > 0.0f);
  assert(up.LengthSquared() > 0.0f);

  Vector3f d(direction);
  d.Normalize();

  Vector3f u(up);
  u.Normalize();

  return Matrix44fOrient(Vector3f::Cross(u, d), u, d);
}

auto Matrix44fFrustum(float left, float right, float bottom, float top,
                      float nearval, float farval) -> Matrix44f {
  float m_persp[16] = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0};
  m_persp[0] = (2.0f * nearval) / (right - left);
  m_persp[5] = (2.0f * nearval) / (top - bottom);
  m_persp[10] = -(farval + nearval) / (farval - nearval);
  m_persp[8] = -(right + left) / (right - left);
  m_persp[9] = (top + bottom) / (top - bottom);
  m_persp[10] = -(farval + nearval) / (farval - nearval);
  m_persp[14] = -2 * farval * nearval / (farval - nearval);
  return Matrix44f(m_persp);
}

auto Matrix44f::Transpose() const -> Matrix44f {
  Matrix44f tmp;  // NOLINT: uninitialized on purpose.
  for (int i = 0; i < 4; i++) {
    for (int j = 0; j < 4; j++) {
      tmp.set(j, i, get(i, j));
    }
  }
  return tmp;
}

//
// From Mesa-2.2\src\glu\project.c
//

//
// Compute the inverse of a 4x4 matrix.  Contributed by scotter@lafn.org
//

static void InvertMatrixGeneral(const float* mat, float* out) {
/* NB. OpenGL Matrices are COLUMN major. */
#define MAT(m, r, c) (mat)[(c) * 4 + (r)]

/* Here's some shorthand converting standard (row,column) to index. */
#define m11 MAT(mat, 0, 0)
#define m12 MAT(mat, 0, 1)
#define m13 MAT(mat, 0, 2)
#define m14 MAT(mat, 0, 3)
#define m21 MAT(mat, 1, 0)
#define m22 MAT(mat, 1, 1)
#define m23 MAT(mat, 1, 2)
#define m24 MAT(mat, 1, 3)
#define m31 MAT(mat, 2, 0)
#define m32 MAT(mat, 2, 1)
#define m33 MAT(mat, 2, 2)
#define m34 MAT(mat, 2, 3)
#define m41 MAT(mat, 3, 0)
#define m42 MAT(mat, 3, 1)
#define m43 MAT(mat, 3, 2)
#define m44 MAT(mat, 3, 3)

  float det;
  float d12, d13, d23, d24, d34, d41;
  float tmp[16]; /* Allow out == in. */

  /* Inverse = adjoint / det. (See linear algebra texts.)*/

  /* pre-compute 2x2 dets for last two rows when computing */
  /* cofnodes of first two rows. */
  d12 = (m31 * m42 - m41 * m32);
  d13 = (m31 * m43 - m41 * m33);
  d23 = (m32 * m43 - m42 * m33);
  d24 = (m32 * m44 - m42 * m34);
  d34 = (m33 * m44 - m43 * m34);
  d41 = (m34 * m41 - m44 * m31);

  tmp[0] = (m22 * d34 - m23 * d24 + m24 * d23);
  tmp[1] = -(m21 * d34 + m23 * d41 + m24 * d13);
  tmp[2] = (m21 * d24 + m22 * d41 + m24 * d12);
  tmp[3] = -(m21 * d23 - m22 * d13 + m23 * d12);

  /* Compute determinant as early as possible using these cofnodes. */
  det = m11 * tmp[0] + m12 * tmp[1] + m13 * tmp[2] + m14 * tmp[3];

  /* Run singularity test. */
  if (det == 0.0f) {
    memcpy(out, kMatrix44fIdentity.m, 16 * sizeof(float));
  } else {
    float invDet = 1.0f / det;
    /* Compute rest of inverse. */
    tmp[0] *= invDet;
    tmp[1] *= invDet;
    tmp[2] *= invDet;
    tmp[3] *= invDet;

    tmp[4] = -(m12 * d34 - m13 * d24 + m14 * d23) * invDet;
    tmp[5] = (m11 * d34 + m13 * d41 + m14 * d13) * invDet;
    tmp[6] = -(m11 * d24 + m12 * d41 + m14 * d12) * invDet;
    tmp[7] = (m11 * d23 - m12 * d13 + m13 * d12) * invDet;

    /* Pre-compute 2x2 dets for first two rows when computing */
    /* cofnodes of last two rows. */
    d12 = m11 * m22 - m21 * m12;
    d13 = m11 * m23 - m21 * m13;
    d23 = m12 * m23 - m22 * m13;
    d24 = m12 * m24 - m22 * m14;
    d34 = m13 * m24 - m23 * m14;
    d41 = m14 * m21 - m24 * m11;

    tmp[8] = (m42 * d34 - m43 * d24 + m44 * d23) * invDet;
    tmp[9] = -(m41 * d34 + m43 * d41 + m44 * d13) * invDet;
    tmp[10] = (m41 * d24 + m42 * d41 + m44 * d12) * invDet;
    tmp[11] = -(m41 * d23 - m42 * d13 + m43 * d12) * invDet;
    tmp[12] = -(m32 * d34 - m33 * d24 + m34 * d23) * invDet;
    tmp[13] = (m31 * d34 + m33 * d41 + m34 * d13) * invDet;
    tmp[14] = -(m31 * d24 + m32 * d41 + m34 * d12) * invDet;
    tmp[15] = (m31 * d23 - m32 * d13 + m33 * d12) * invDet;

    memcpy(out, tmp, 16 * sizeof(float));
  }

#undef m11
#undef m12
#undef m13
#undef m14
#undef m21
#undef m22
#undef m23
#undef m24
#undef m31
#undef m32
#undef m33
#undef m34
#undef m41
#undef m42
#undef m43
#undef m44
#undef MAT
}

//
// Invert matrix mat.  This algorithm contributed by Stephane Rehel
// <rehel@worldnet.fr>
//

static void InvertMatrix(const float* mat, float* out) {
/* NB. OpenGL Matrices are COLUMN major. */
#define MAT(mat, r, c) (mat)[(c) * 4 + (r)]

/* Here's some shorthand converting standard (row,column) to index. */
#define m11 MAT(mat, 0, 0)
#define m12 MAT(mat, 0, 1)
#define m13 MAT(mat, 0, 2)
#define m14 MAT(mat, 0, 3)
#define m21 MAT(mat, 1, 0)
#define m22 MAT(mat, 1, 1)
#define m23 MAT(mat, 1, 2)
#define m24 MAT(mat, 1, 3)
#define m31 MAT(mat, 2, 0)
#define m32 MAT(mat, 2, 1)
#define m33 MAT(mat, 2, 2)
#define m34 MAT(mat, 2, 3)
#define m41 MAT(mat, 3, 0)
#define m42 MAT(mat, 3, 1)
#define m43 MAT(mat, 3, 2)
#define m44 MAT(mat, 3, 3)

  float det;
  float tmp[16]; /* Allow out == in. */

  if (m41 != 0.f || m42 != 0.f || m43 != 0.f || m44 != 1.f) {
    InvertMatrixGeneral(mat, out);
    return;
  }

  /* Inverse = adjoint / det. (See linear algebra texts.)*/

  tmp[0] = m22 * m33 - m23 * m32;
  tmp[1] = m23 * m31 - m21 * m33;
  tmp[2] = m21 * m32 - m22 * m31;

  /* Compute determinant as early as possible using these cofnodes. */
  det = m11 * tmp[0] + m12 * tmp[1] + m13 * tmp[2];

  /* Run singularity test. */
  if (det == 0.0f) {
    memcpy(out, kMatrix44fIdentity.m, 16 * sizeof(float));
  } else {
    float d12, d13, d23, d24, d34, d41;
    float im11, im12, im13, im14;

    det = 1.f / det;

    /* Compute rest of inverse. */
    tmp[0] *= det;
    tmp[1] *= det;
    tmp[2] *= det;
    tmp[3] = 0.f;

    im11 = m11 * det;
    im12 = m12 * det;
    im13 = m13 * det;
    im14 = m14 * det;
    tmp[4] = im13 * m32 - im12 * m33;
    tmp[5] = im11 * m33 - im13 * m31;
    tmp[6] = im12 * m31 - im11 * m32;
    tmp[7] = 0.f;

    /* Pre-compute 2x2 dets for first two rows when computing */
    /* cofnodes of last two rows. */
    d12 = im11 * m22 - m21 * im12;
    d13 = im11 * m23 - m21 * im13;
    d23 = im12 * m23 - m22 * im13;
    d24 = im12 * m24 - m22 * im14;
    d34 = im13 * m24 - m23 * im14;
    d41 = im14 * m21 - m24 * im11;

    tmp[8] = d23;
    tmp[9] = -d13;
    tmp[10] = d12;
    tmp[11] = 0.f;

    tmp[12] = -(m32 * d34 - m33 * d24 + m34 * d23);
    tmp[13] = (m31 * d34 + m33 * d41 + m34 * d13);
    tmp[14] = -(m31 * d24 + m32 * d41 + m34 * d12);
    tmp[15] = 1.f;

    memcpy(out, tmp, 16 * sizeof(float));
  }

#undef m11
#undef m12
#undef m13
#undef m14
#undef m21
#undef m22
#undef m23
#undef m24
#undef m31
#undef m32
#undef m33
#undef m34
#undef m41
#undef m42
#undef m43
#undef m44
#undef MAT
}

auto Matrix44f::Inverse() const -> Matrix44f {
  Matrix44f inv;  // NOLINT: uninitialized on purpose
  InvertMatrix(m, inv.m);
  return inv;
}

}  // namespace ballistica
