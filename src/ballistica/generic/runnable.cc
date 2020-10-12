// Released under the MIT License. See LICENSE for details.

#include "ballistica/generic/runnable.h"

namespace ballistica {

auto Runnable::GetThreadOwnership() const -> Object::ThreadOwnership {
  return ThreadOwnership::kNextReferencing;
}

}  // namespace ballistica
