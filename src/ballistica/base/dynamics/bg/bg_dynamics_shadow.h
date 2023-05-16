// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SHADOW_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SHADOW_H_

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

// A utility class for client use which uses ray-testing and
// BG collision terrains to create a variably dense/soft shadow
// based on how high it is above terrain.
// Clients should give their current position information to the shadow
// at update time and then at render time it'll be all set to go.
// (shadows update in the bg dynamics stepping process)
class BGDynamicsShadow {
 public:
  explicit BGDynamicsShadow(float height_scaling = 1.0f);
  ~BGDynamicsShadow();
  void SetPosition(const Vector3f& pos);
  auto GetPosition() const -> const Vector3f&;

  // Return scale and density for the shadow.
  // this also takes into account the height based shadow density
  // (g_graphics->GetShadowDensity()) so you don't have to.
  void GetValues(float* scale, float* density) const;

 private:
  BGDynamicsShadowData* data_{};
  BA_DISALLOW_CLASS_COPIES(BGDynamicsShadow);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SHADOW_H_
