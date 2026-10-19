// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_SHADOW_RANGE_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_SHADOW_RANGE_H_

namespace ballistica::base {

/// The heights between which things in a world cast shadows: density
/// ramps in from lower_bottom to lower_top, is full up to upper_bottom,
/// and ramps back out by upper_top.
///
/// Plain values, so a copy can be handed to another thread (each world
/// view has one; its bg-dynamics world gets a copy with every step).
struct ShadowRange {
  float lower_bottom{-4.0f};
  float lower_top{4.0f};
  float upper_bottom{30.0f};
  float upper_top{40.0f};

  /// Shadow density (0-1) for something at a given height.
  auto GetDensity(float y) const -> float {
    if (y < lower_bottom) {
      return 0.0f;
    } else if (y < lower_top) {
      return (y - lower_bottom) / (lower_top - lower_bottom);
    } else if (y < upper_bottom) {
      return 1.0f;
    } else if (y < upper_top) {
      return 1.0f - (y - upper_bottom) / (upper_top - upper_bottom);
    } else {
      return 0.0f;
    }
  }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_SHADOW_RANGE_H_
