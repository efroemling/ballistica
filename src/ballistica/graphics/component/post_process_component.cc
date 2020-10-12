// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/component/post_process_component.h"

namespace ballistica {

void PostProcessComponent::WriteConfig() {
  if (eyes_) {
    assert(normal_distort_ == 0.0f);  // unsupported config
    ConfigForShading(ShadingType::kPostProcessEyes);
  } else {
    if (normal_distort_ != 0.0f) {
      ConfigForShading(ShadingType::kPostProcessNormalDistort);
      cmd_buffer_->PutFloat(normal_distort_);
    } else {
      ConfigForShading(ShadingType::kPostProcess);
    }
  }
}

}  // namespace ballistica
