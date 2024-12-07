// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_BASE_2_H_
#define BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_BASE_2_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

/// Graphics related individual python methods for our module.
class PythonMethodsBase2 {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_BASE_2_H_
