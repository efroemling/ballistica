// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_RECT_H_
#define BALLISTICA_SHARED_MATH_RECT_H_

// A Generic 2d rect.
namespace ballistica {

class Rect {
 public:
  float l{}, r{}, b{}, t{};
  Rect() = default;
  Rect(float l_in, float b_in, float r_in, float t_in)
      : l(l_in), r(r_in), b(b_in), t(t_in) {}
  auto width() const -> float { return r - l; }
  auto height() const -> float { return t - b; }
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_RECT_H_
