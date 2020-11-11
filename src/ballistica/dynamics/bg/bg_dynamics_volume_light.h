// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_
#define BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_

#include "ballistica/core/object.h"

namespace ballistica {

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

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_
