// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_MATRIX44F_H_
#define BALLISTICA_SHARED_MATH_MATRIX44F_H_

#include <cstring>  // for memcpy

#include "ballistica/shared/math/vector3f.h"

namespace ballistica {

class Matrix44f {
 public:
  // Stop linter complaints about uninitialized members.
  // (It seems our union might be confusing it, and in some cases
  // we want to leave things uninited).
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-use-equals-default"
#pragma ide diagnostic ignored "cppcoreguidelines-pro-type-member-init"

  // Default constructor (leaves uninitialized)
  Matrix44f() = default;

  Matrix44f(float m00, float m01, float m02, float m03, float m10, float m11,
            float m12, float m13, float m20, float m21, float m22, float m23,
            float m30, float m31, float m32, float m33)
      : m00(m00),
        m01(m01),
        m02(m02),
        m03(m03),
        m10(m10),
        m11(m11),
        m12(m12),
        m13(m13),
        m20(m20),
        m21(m21),
        m22(m22),
        m23(m23),
        m30(m30),
        m31(m31),
        m32(m32),
        m33(m33) {}

  // Construct from array.
  explicit Matrix44f(const float* matrix) { memcpy(m, matrix, sizeof(m)); }

  // Construct from array.
  explicit Matrix44f(const double* matrix) {
    float* i = m;
    const double* j = matrix;
    for (int k = 0; k < 16; i++, j++, k++) {
      *i = static_cast<float>(*j);
    }
  }

#pragma clang diagnostic pop

  // Matrix multiplication.
  auto operator*(const Matrix44f& other) const -> Matrix44f {
    Matrix44f prod;  // NOLINT: uninitialized on purpose.
    for (int c = 0; c < 4; c++) {
      for (int r = 0; r < 4; r++) {
        prod.set(c, r,
                 get(c, 0) * other.get(0, r) + get(c, 1) * other.get(1, r)
                     + get(c, 2) * other.get(2, r)
                     + get(c, 3) * other.get(3, r));
      }
    }
    return prod;
  }

  auto tx() const -> float { return m[12]; }
  auto ty() const -> float { return m[13]; }
  auto tz() const -> float { return m[14]; }

  void set_tx(float v) { m[12] = v; }
  void set_ty(float v) { m[13] = v; }
  void set_tz(float v) { m[14] = v; }

  auto GetTranslate() const -> Vector3f { return {tx(), ty(), tz()}; }

  auto LocalXAxis() const -> Vector3f { return {m[0], m[1], m[2]}; }
  auto LocalYAxis() const -> Vector3f { return {m[4], m[5], m[6]}; }
  auto LocalZAxis() const -> Vector3f { return {m[8], m[9], m[10]}; }

  // In-place matrix multiplication.
  auto operator*=(const Matrix44f& other) -> Matrix44f& {
    return (*this) = (*this) * other;
  }

  // Matrix transformation of 3D vector.
  auto operator*(const Vector3f& vec) const -> Vector3f {
    float prod[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    for (int r = 0; r < 4; r++) {
      for (int c = 0; c < 3; c++) prod[r] += vec.v[c] * get(c, r);
      prod[r] += get(3, r);
    }
    float div = 1.0f / prod[3];
    return {prod[0] * div, prod[1] * div, prod[2] * div};
  }

  // Rotate/scale a 3d vector.
  auto TransformAsNormal(const Vector3f& val) const -> Vector3f {
    // There's probably a smarter way to do this via 3x3 matrices?..
    Matrix44f m2{*this};
    m2.set_tx(0);
    m2.set_ty(0);
    m2.set_tz(0);
    return m2 * val;
  }

  // Equality operator.
  auto operator==(const Matrix44f& other) const -> bool {
    return !memcmp(m, other.m, sizeof(m));
  }

  // Not-equal operator.
  auto operator!=(const Matrix44f& other) const -> bool {
    return memcmp(m, other.m, sizeof(m)) != 0;
  }

  // Calculate matrix inverse.
  auto Inverse() const -> Matrix44f;

  // Calculate matrix transpose.
  auto Transpose() const -> Matrix44f;

  union {
    struct {
      float m00, m10, m20, m30;
      float m01, m11, m21, m31;
      float m02, m12, m22, m32;
      float m03, m13, m23, m33;
    };
    float m[16];
  };

  void set(const int col, const int row, const float val) {
    m[col * 4 + row] = val;
  }

  auto get(const int col, const int row) const -> float {
    return m[col * 4 + row];
  }

  auto element(const int col, const int row) -> float& {
    return m[col * 4 + row];
  }
};

// NOLINTNEXTLINE(cert-err58-cpp)
const Matrix44f kMatrix44fIdentity{1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f,
                                   0.0f, 0.0f, 0.0f, 0.0f, 1.0f, 0.0f,
                                   0.0f, 0.0f, 0.0f, 1.0f};

inline auto Matrix44fTranslate(const Vector3f& trans) -> Matrix44f {
  Matrix44f translate{kMatrix44fIdentity};
  translate.set(3, 0, trans.v[0]);
  translate.set(3, 1, trans.v[1]);
  translate.set(3, 2, trans.v[2]);
  return translate;
}

inline auto Matrix44fTranslate(const float x, const float y, const float z)
    -> Matrix44f {
  Matrix44f translate{kMatrix44fIdentity};
  translate.set(3, 0, x);
  translate.set(3, 1, y);
  translate.set(3, 2, z);
  return translate;
}

inline auto Matrix44fScale(const float sf) -> Matrix44f {
  Matrix44f mat{kMatrix44fIdentity};
  mat.set(0, 0, sf);
  mat.set(1, 1, sf);
  mat.set(2, 2, sf);
  return mat;
}

inline auto Matrix44fScale(const Vector3f& sf) -> Matrix44f {
  Matrix44f scale{kMatrix44fIdentity};
  scale.set(0, 0, sf.v[0]);
  scale.set(1, 1, sf.v[1]);
  scale.set(2, 2, sf.v[2]);
  return scale;
}

auto Matrix44fRotate(const Vector3f& axis, float angle) -> Matrix44f;
auto Matrix44fRotate(float azimuth, float elevation) -> Matrix44f;
auto Matrix44fOrient(const Vector3f& x, const Vector3f& y, const Vector3f& z)
    -> Matrix44f;

// Note: direction and up need to be perpendicular and normalized here.
auto Matrix44fOrient(const Vector3f& direction, const Vector3f& up)
    -> Matrix44f;
auto Matrix44fFrustum(float left, float right, float bottom, float top,
                      float near, float far) -> Matrix44f;

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_MATRIX44F_H_
