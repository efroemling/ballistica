// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_MISC_H_
#define BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_MISC_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

/// Methods that don't have a clear home. Should try to clear this out.
class PythonMethodsMisc {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_MISC_H_
