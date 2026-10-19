// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/camera.h"

#include "ballistica/shared/foundation/exception.h"

namespace ballistica::base {

Camera::Camera() = default;
Camera::~Camera() = default;

void Camera::Update(millisecs_t elapsed) {}

void Camera::UpdatePosition() {}

auto Camera::mode() const -> CameraMode { return CameraMode::kFollow; }

void Camera::SetMode(CameraMode mode) {}

void Camera::SetAreaOfInterestBounds(float min_x, float min_y, float min_z,
                                     float max_x, float max_y, float max_z) {}

void Camera::SetVROffset(const Vector3f& val) {}

auto Camera::NewAreaOfInterest(bool in_focus) -> AreaOfInterest* {
  assert(g_base->InLogicThread());
  areas_of_interest_.emplace_back(in_focus);
  return &areas_of_interest_.back();
}

void Camera::DeleteAreaOfInterest(AreaOfInterest* a) {
  assert(g_base->InLogicThread());
  for (auto i = areas_of_interest_.begin(); i != areas_of_interest_.end();
       ++i) {
    if (&(*i) == a) {
      areas_of_interest_.erase(i);
      return;
    }
  }
  throw Exception("Area-of-interest not found");
}

}  // namespace ballistica::base
