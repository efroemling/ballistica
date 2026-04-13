// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/area_of_interest.h"

#include "ballistica/base/ui/ui.h"

namespace ballistica::base {

AreaOfInterest::AreaOfInterest(bool in_focus) : in_focus_(in_focus) {}

AreaOfInterest::~AreaOfInterest() = default;

void AreaOfInterest::SetRadius(float r_in) {
  // We slightly scale this for phone situations.
  float extrascale = (g_base->ui->uiscale() == UIScale::kSmall) ? 0.85f : 1.0f;
  radius_ = r_in * extrascale;
}

}  // namespace ballistica::base
