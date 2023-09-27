// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/generic/runnable.h"

namespace ballistica {

auto Runnable::GetThreadOwnership() const -> Object::ThreadOwnership {
  return ThreadOwnership::kNextReferencing;
}

void Runnable::RunAndLogErrors() {
  try {
    Run();
  } catch (const std::exception& exc) {
    Log(LogLevel::kError, std::string("Error in Runnable: ") + exc.what());
  }
}

}  // namespace ballistica
