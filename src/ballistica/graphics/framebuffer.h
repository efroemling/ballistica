// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_FRAMEBUFFER_H_
#define BALLISTICA_GRAPHICS_FRAMEBUFFER_H_

#include "ballistica/core/object.h"

namespace ballistica {

class Framebuffer : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
    return ThreadIdentifier::kMain;
  }
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_FRAMEBUFFER_H_
