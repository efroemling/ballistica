// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_LERP_H_
#define BALLISTICA_SHARED_MATH_LERP_H_

#include <algorithm>
#include <concepts>

// Lerp functionality
namespace ballistica {

template <std::floating_point T>
[[nodiscard]] constexpr T inv_lerp_clamped(T a, T b, T x) noexcept {
  if (a == b) {
    return T{0};
  }
  T t = (x - a) / (b - a);
  return std::clamp(t, T{0}, T{1});
}

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_LERP_H_
