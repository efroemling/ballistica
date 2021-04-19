// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/area_of_interest.h"

namespace ballistica {

AreaOfInterest::AreaOfInterest(bool in_focus) : in_focus_(in_focus) {}

AreaOfInterest::~AreaOfInterest() = default;

void AreaOfInterest::SetRadius(float r_in) {
  // We slightly scale this for phone situations.
  float extrascale = (GetUIScale() == UIScale::kSmall) ? 0.85f : 1.0f;
  radius_ = r_in * extrascale;
}

}  // namespace ballistica
