// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_GRAPHICS_H_
#define BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_GRAPHICS_H_

#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

/// Graphics related individual python methods for our module.
class PythonMethodsGraphics {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica
#endif  // BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_GRAPHICS_H_
