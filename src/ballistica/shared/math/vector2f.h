// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_VECTOR2F_H_
#define BALLISTICA_SHARED_MATH_VECTOR2F_H_

namespace ballistica {

class Vector2f {
 public:
  // Leaves uninitialized.
  Vector2f() {}                               // NOLINT
  Vector2f(float x, float y) : x(x), y(y) {}  // NOLINT

  union {
    struct {
      float x;
      float y;
    };
    float v[2];
  };
};

// NOLINTNEXTLINE(cert-err58-cpp)
const Vector2f kVector2f0{0.0f, 0.0f};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_VECTOR2F_H_
