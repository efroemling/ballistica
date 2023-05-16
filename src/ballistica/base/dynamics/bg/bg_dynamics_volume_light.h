// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Client-controlled lights for bg smoke.
class BGDynamicsVolumeLight : public Object {
 public:
  BGDynamicsVolumeLight();
  ~BGDynamicsVolumeLight() override;
  void SetPosition(const Vector3f& pos);
  void SetRadius(float radius);
  void SetColor(float r, float g, float b);

 private:
  BGDynamicsVolumeLightData* data_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_
