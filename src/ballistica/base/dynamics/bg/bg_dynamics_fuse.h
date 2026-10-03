// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_channel.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/shared/math/matrix44f.h"

namespace ballistica::base {

// A bomb-fuse client-side handle; feed it the fuse root transform and
// remaining length and bg-dynamics simulates and draws the trailing
// fuse with sparks (in the bg-dynamics world it was made in, which it
// keeps around for as long as it exists).
class BGDynamicsFuse {
 public:
  explicit BGDynamicsFuse(BGDynamicsWorld* world);
  ~BGDynamicsFuse();
  void SetTransform(const Matrix44f& m);
  void SetLength(float l);

 private:
  Object::Ref<BGDynamicsWorld> world_;
  BGDynamicsSlot slot_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_
