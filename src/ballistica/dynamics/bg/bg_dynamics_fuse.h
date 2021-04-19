// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_
#define BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_

#include "ballistica/ballistica.h"

namespace ballistica {

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

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_FUSE_H_
