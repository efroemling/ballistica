// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_APP_H_
#define BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_APP_H_

#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

/// App related individual python methods for our module.
class PythonMethodsApp {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica
#endif  // BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_APP_H_
