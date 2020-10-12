// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/component/special_component.h"

namespace ballistica {

void SpecialComponent::WriteConfig() {
  ConfigForShading(ShadingType::kSpecial);
  cmd_buffer_->PutInt(static_cast<int>(source_));
}

}  // namespace ballistica
