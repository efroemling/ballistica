// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_MATH_POINT2D_H_
#define BALLISTICA_SHARED_MATH_POINT2D_H_

namespace ballistica {

// 2d point; pretty barebones at the moment..
struct Point2D {
  float x, y;
  Point2D() : x(0), y(0) {}
  Point2D(float x_in, float y_in) : x(x_in), y(y_in) {}
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_MATH_POINT2D_H_
