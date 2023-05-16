// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_VECTOR3F_H_
#define BALLISTICA_SHARED_MATH_VECTOR3F_H_

#include <cmath>
#include <cstring>  // for memcpy
#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica {

class Vector3f {
 public:
  // Default constructor (leaves uninitialized)
  Vector3f() = default;

  // Constructor.
  Vector3f(float x, float y, float z) : x(x), y(y), z(z) {}  // NOLINT

  // Constructor.
  explicit Vector3f(const float* vals) {  // NOLINT
    memcpy(v, vals, sizeof(v));
  }  // NOLINT

  // Constructor.
  explicit Vector3f(const std::vector<float>& vals) {  // NOLINT
    assert(vals.size() == 3);
    memcpy(v, vals.data(), sizeof(v));
  }

  auto Normalized() const -> Vector3f {
    Vector3f v2(*this);
    v2.Normalize();
    return v2;
  }

  // Equality operator.
  auto operator==(const Vector3f& other) const -> bool {
    return x == other.x && y == other.y && z == other.z;
  }

  // Inequality operator.
  auto operator!=(const Vector3f& other) const -> bool {
    return x != other.x || y != other.y || z != other.z;
  }

  // Equality operator: x==a && y==a && z==a/
  auto operator==(const float& a) const -> bool {
    return x == a && y == a && z == a;
  }

  // Less-than comparison.
  auto operator<(const Vector3f& other) const -> bool {
    if (x != other.x) return x < other.x;
    if (y != other.y) return y < other.y;
    return z < other.z;
  }

  // Greater-than comparison.
  auto operator>(const Vector3f& other) const -> bool {
    if (x != other.x) return x > other.x;
    if (y != other.y) return y > other.y;
    return z > other.z;
  }

  // Assignment operator.
  auto operator=(const float* vals) -> Vector3f& {
    memcpy(v, vals, sizeof(v));
    return *this;
  }

  // Assignment operator.
  auto operator=(const double* vals) -> Vector3f& {
    x = static_cast<float>(vals[0]);
    y = static_cast<float>(vals[1]);
    z = static_cast<float>(vals[2]);
    return *this;
  }

  // Addition in place.
  auto operator+=(const Vector3f& other) -> Vector3f& {
    x += other.x;
    y += other.y;
    z += other.z;
    return *this;
  }

  // Subtraction in place.
  auto operator-=(const Vector3f& other) -> Vector3f& {
    x -= other.x;
    y -= other.y;
    z -= other.z;
    return *this;
  }

  auto AsStdVector() const -> std::vector<float> { return {x, y, z}; }

  auto Dot(const Vector3f& other) const -> float {
    return x * other.x + y * other.y + z * other.z;
  }

  // Multiply in place.
  auto operator*=(float val) -> Vector3f& {
    x *= val;
    y *= val;
    z *= val;
    return *this;
  }

  // Negative.
  auto operator-() const -> Vector3f { return {-x, -y, -z}; }

  auto operator/(float val) const -> Vector3f {
    assert(val != 0.0f);
    float inv = 1.0f / val;
    return {x * inv, y * inv, z * inv};
  }

  auto operator*(float val) const -> Vector3f {
    return {val * x, val * y, val * z};
  }
  // (allow NUM * VEC order)
  friend auto operator*(float val, const Vector3f& vec) -> Vector3f {
    return vec * val;
  }
  auto operator+(const Vector3f& other) const -> Vector3f {
    return {x + other.x, y + other.y, z + other.z};
  }
  auto operator-(const Vector3f& other) const -> Vector3f {
    return {x - other.x, y - other.y, z - other.z};
  }

  void Scale(const Vector3f& val) {
    x *= val.x;
    y *= val.y;
    z *= val.z;
  }

  // Normalise the vector: |x| = 1.0.
  void Normalize() {
    const float mag = sqrtf(LengthSquared());
    if (mag == 0.0f) return;
    const float mag_inv = 1.0f / mag;
    x *= mag_inv;
    y *= mag_inv;
    z *= mag_inv;
  }

  // Make x, y and z positive.
  void MakeAbs() {
    x = std::abs(x);
    y = std::abs(y);
    z = std::abs(z);
  }

  // Find the dominant component: x, y or z.
  auto Dominant() const -> int;

  // Squared length of vector.
  auto LengthSquared() const -> float { return ((*this).Dot(*this)); }

  // Length of vector.
  auto Length() const -> float { return sqrtf((*this).Dot(*this)); }

  union {
    struct {
      float x;
      float y;
      float z;
    };
    float v[3];
  };

  static auto Cross(const Vector3f& v1, const Vector3f& v2) -> Vector3f {
    return {v1.v[1] * v2.v[2] - v1.v[2] * v2.v[1],
            v1.v[2] * v2.v[0] - v1.v[0] * v2.v[2],
            v1.v[0] * v2.v[1] - v1.v[1] * v2.v[0]};
  }

  static auto PlaneNormal(const Vector3f& v1, const Vector3f& v2,
                          const Vector3f& v3) -> Vector3f;
  static auto Polar(float lat, float longitude) -> Vector3f;

  static void OrthogonalSystem(Vector3f* a, Vector3f* b, Vector3f* c);

  static auto Dot(const Vector3f& v1, const Vector3f& v2) -> float {
    return (v1.x * v2.x + v1.y * v2.y + v1.z * v2.z);
  }
  static auto Angle(const Vector3f& v1, const Vector3f& v2) -> float;
};

const Vector3f kVector3fX{1.0f, 0.0f, 0.0f};  // NOLINT(cert-err58-cpp)
const Vector3f kVector3fY{0.0f, 1.0f, 0.0f};  // NOLINT(cert-err58-cpp)
const Vector3f kVector3fZ{0.0f, 0.0f, 1.0f};  // NOLINT(cert-err58-cpp)
const Vector3f kVector3f0{0.0f, 0.0f, 0.0f};  // NOLINT(cert-err58-cpp)
const Vector3f kVector3f1{1.0f, 1.0f, 1.0f};  // NOLINT(cert-err58-cpp)

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_VECTOR3F_H_
