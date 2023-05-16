// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/math/vector3f.h"

namespace ballistica {

auto Vector3f::Dominant() const -> int {
  const float x = std::abs(v[0]);
  const float y = std::abs(v[1]);
  const float z = std::abs(v[2]);
  if (x > y && x > z) {
    return 0;
  } else {
    if (y > z) {
      return 1;
    } else {
      return 2;
    }
  }
}

auto Vector3f::Angle(const Vector3f& v1, const Vector3f& v2) -> float {
  float s = sqrtf(v1.LengthSquared() * v2.LengthSquared());
  assert(s != 0.0f);
  return (360.0f / (2.0f * kPi)) * acosf(Dot(v1, v2) / s);
}

auto Vector3f::PlaneNormal(const Vector3f& v1, const Vector3f& v2,
                           const Vector3f& v3) -> Vector3f {
  return Cross(v2 - v1, v3 - v1);
}

auto Vector3f::Polar(float lat, float longitude) -> Vector3f {
  return {cosf(lat * kPiDeg) * cosf(longitude * kPiDeg), sinf(lat * kPiDeg),
          cosf(lat * kPiDeg) * sinf(longitude * kPiDeg)};
}

void Vector3f::OrthogonalSystem(Vector3f* a, Vector3f* b, Vector3f* c) {
  a->Normalize();
  if (std::abs(a->z) > 0.8f) {
    *b = Cross(*a, kVector3fY);
    *c = Cross(*a, *b);
  } else {
    *b = Cross(*a, kVector3fZ);
    *c = Cross(*a, *b);
  }
  b->Normalize();
  c->Normalize();
}

}  // namespace ballistica
