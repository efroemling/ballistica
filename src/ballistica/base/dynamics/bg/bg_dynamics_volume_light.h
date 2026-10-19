// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_channel.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// A volume light client-side handle; feed it position/radius/color
// and it tints nearby bg-dynamics smoke (in the bg-dynamics world it
// was made in, which it keeps around for as long as it exists).
class BGDynamicsVolumeLight : public Object {
 public:
  explicit BGDynamicsVolumeLight(BGDynamicsWorld* world);
  ~BGDynamicsVolumeLight() override;
  void SetPosition(const Vector3f& pos);
  void SetRadius(float radius);
  void SetColor(float r, float g, float b);

 private:
  Object::Ref<BGDynamicsWorld> world_;
  BGDynamicsSlot slot_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_VOLUME_LIGHT_H_
