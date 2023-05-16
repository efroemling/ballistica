// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SHADOW_DATA_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SHADOW_DATA_H_

namespace ballistica::base {

struct BGDynamicsShadowData {
  explicit BGDynamicsShadowData(float height_scaling)
      : height_scaling(height_scaling) {}

  void UpdateClientData() {
    // Copy data over with a bit of smoothing
    // (so our shadow doesn't jump instantly when we go over and edge/etc.)
    float smoothing{0.8f};
    shadow_scale_client = smoothing * shadow_scale_client
                          + (1.0f - smoothing) * shadow_scale_worker;
    shadow_density_client = smoothing * shadow_density_client
                            + (1.0f - smoothing) * shadow_density_worker;
  }

  void Synchronize() { pos_worker = pos_client; }

  bool client_dead{};
  float height_scaling{};

  // For use by worker:

  // position value owned by the client (write-only).
  Vector3f pos_client{0.0f, 0.0f, 0.0f};

  // Position value owned by the worker thread (read-only).
  Vector3f pos_worker{0.0f, 0.0f, 0.0f};

  // Calculated values owned by the worker thread (write-only).
  float shadow_scale_worker{1.0f};
  float shadow_density_worker{0.0f};

  // Result values owned by the client (read-only).
  float shadow_scale_client{1.0f};
  float shadow_density_client{0.0f};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SHADOW_DATA_H_
