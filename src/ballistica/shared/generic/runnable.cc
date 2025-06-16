// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/generic/runnable.h"

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"

namespace ballistica {

using core::g_core;

auto Runnable::GetThreadOwnership() const -> Object::ThreadOwnership {
  return ThreadOwnership::kNextReferencing;
}

void Runnable::RunAndLogErrors() {
  try {
    Run();
  } catch (const std::exception& exc) {
    std::string type_name;
    if (g_core != nullptr) {
      type_name = g_core->platform->DemangleCXXSymbol(typeid(exc).name());
    } else {
      type_name = "<type unavailable>";
    }
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        std::string("Error in Runnable: " + type_name + ": ") + exc.what());
  }
}

}  // namespace ballistica
