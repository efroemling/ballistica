// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_DATA_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_DATA_H_

#include <algorithm>

#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::base {

const int kFusePointCount = 4;

struct BGDynamicsFuseData {
  void Synchronize() {
    transform_worker_ = transform_client_;
    have_transform_worker_ = have_transform_client_;
    length_worker_ = length_client_;
  }

  void Update(BGDynamicsServer* dyn) {
    // Do nothing if we haven't received an initial transform.
    if (!have_transform_worker_) {
      return;
    }
    seg_len_ = 0.2f * std::max(0.01f, length_worker_);

    if (!initial_position_set_) {
      // Snap all our stuff into place on the initial transform.
      Vector3f pt = transform_worker_.GetTranslate();
      target_pts_[0] = dyn_pts_[0] = pt;
      auto up = Vector3f(&transform_worker_.m[4]);
      for (int i = 1; i < kFusePointCount; i++) {
        target_pts_[i] = target_pts_[i - 1] + up * seg_len_;
        dyn_pts_[i] = target_pts_[i];
        up = (target_pts_[i] - target_pts_[i - 1]).Normalized();
      }
      initial_position_set_ = true;
    } else {
      // ...otherwise dynamically update it.
      Vector3f pt = transform_worker_.GetTranslate();
      target_pts_[0] = dyn_pts_[0] = pt;
      auto up = Vector3f(&transform_worker_.m[4]);
      auto back = Vector3f(&transform_worker_.m[8]);
      up = (up + -0.03f * back).Normalized();
      float bAmt = 0.0f;
      Vector3f oldTipPos = dyn_pts_[kFusePointCount - 1];
      for (int i = 1; i < kFusePointCount; i++) {
        target_pts_[i] = dyn_pts_[i - 1] + up * seg_len_;
        float thisFollowAmt = (i == 1 ? 0.5f : 0.2f);
        dyn_pts_[i] += thisFollowAmt * (target_pts_[i] - dyn_pts_[i]);
        dyn_pts_[i] += Vector3f(0, -0.014f * 0.2f * length_worker_, 0);
        up = (dyn_pts_[i] - dyn_pts_[i - 1] - bAmt * back).Normalized();
        dyn_pts_[i] = dyn_pts_[i - 1] + up * seg_len_;
        bAmt += 0.01f * length_worker_;
      }

      // Spit out a spark.
      float r, g, b, a;
      if (length_worker_ > 0.66f) {
        r = 1.6f;
        g = 1.5f;
        b = 0.4f;
        a = 0.5f;
      } else if (length_worker_ > 0.33f) {
        r = 2.0f;
        g = 0.7f;
        b = 0.3f;
        a = 0.2f;
      } else {
        r = 3.0f;
        g = 0.5f;
        b = 0.4f;
        a = 0.3f;
      }
      int count = 2;
      if (dyn->graphics_quality() <= GraphicsQuality::kLow) {
        count = 1;
      }

      for (int i = 0; i < count; i++) {
        float rand_f = RandomFloat();
        float d_life = -0.08f;
        float d_size = 0.000f + 0.04f * rand_f * rand_f;

        dyn->spark_particles()->Emit(dyn_pts_[kFusePointCount - 1],
                                     dyn_pts_[kFusePointCount - 1] - oldTipPos,
                                     r, g, b, a, d_life, 0.02f, d_size,
                                     0.8f);  // Flicker.
      }
    }
  }

  bool client_dead_{};
  float seg_len_{};
  Vector3f target_pts_[kFusePointCount]{};
  Vector3f dyn_pts_[kFusePointCount]{};
  float length_client_{1.0f};
  float length_worker_{1.0f};

  // Values owned by the client.
  Matrix44f transform_client_{kMatrix44fIdentity};

  // Values owned by the worker thread.
  Matrix44f transform_worker_{kMatrix44fIdentity};
  bool have_transform_client_{};
  bool have_transform_worker_{};
  bool initial_position_set_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_DATA_H_
