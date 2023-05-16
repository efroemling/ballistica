// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_VECTOR4F_H_
#define BALLISTICA_SHARED_MATH_VECTOR4F_H_

#include "ballistica/shared/math/vector3f.h"

namespace ballistica {

class Vector4f {
 public:
  Vector4f() = default;
  // NOLINTNEXTLINE saying we don't init v but in effect we do.
  Vector4f(float x, float y, float z, float w) : x(x), y(y), z(z), w(w) {}

  auto xyz() const -> Vector3f { return {x, y, z}; }

  union {
    struct {
      float x;
      float y;
      float z;
      float w;
    };
    float v[4];
  };
};

const Vector4f kVector4f0{0.0f, 0.0f, 0.0f, 0.0f};  // NOLINT(cert-err58-cpp)

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_VECTOR4F_H_
