// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/component/special_component.h"

namespace ballistica::base {

void SpecialComponent::WriteConfig() {
  ConfigForShading(ShadingType::kSpecial);
  cmd_buffer_->PutInt(static_cast<int>(source_));
}

}  // namespace ballistica::base
