// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_DATA_MODEL_RENDERER_DATA_H_
#define BALLISTICA_ASSETS_DATA_MODEL_RENDERER_DATA_H_

#include "ballistica/core/object.h"

namespace ballistica {

// Renderer-specific data (gl display list, etc)
// this is provided by the renderer
class ModelRendererData : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
    return ThreadIdentifier::kMain;
  }
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_DATA_MODEL_RENDERER_DATA_H_
