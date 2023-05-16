// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_AREA_OF_INTEREST_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_AREA_OF_INTEREST_H_

#include <vector>

#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

class AreaOfInterest {
 public:
  explicit AreaOfInterest(bool in_focus);
  ~AreaOfInterest();
  void set_position(const Vector3f& position) { position_ = position; }
  void set_velocity(const Vector3f& velocity) { velocity_ = velocity; }
  auto position() const -> const Vector3f& { return position_; }
  auto velocity() const -> const Vector3f& { return velocity_; }
  void SetRadius(float r);
  auto in_focus() const -> bool { return in_focus_; }
  auto radius() const -> float { return radius_; }

 private:
  Vector3f position_ = {0.0f, 0.0f, 0.0f};
  Vector3f velocity_ = {0.0f, 0.0f, 0.0f};
  float radius_ = 1.0f;
  bool in_focus_ = false;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_AREA_OF_INTEREST_H_
