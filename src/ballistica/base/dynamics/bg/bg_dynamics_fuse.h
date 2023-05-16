// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

// Client controlled fuse.
class BGDynamicsFuse {
 public:
  BGDynamicsFuse();
  ~BGDynamicsFuse();
  void SetTransform(const Matrix44f& m);
  void SetLength(float l);

 private:
  BGDynamicsFuseData* data_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_
