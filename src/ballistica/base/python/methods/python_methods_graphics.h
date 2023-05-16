// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_GRAPHICS_H_
#define BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_GRAPHICS_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

/// Graphics related individual python methods for our module.
class PythonMethodsGraphics {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_GRAPHICS_H_
