// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/generic/runnable.h"

namespace ballistica {

auto Runnable::GetThreadOwnership() const -> Object::ThreadOwnership {
  return ThreadOwnership::kNextReferencing;
}

}  // namespace ballistica
