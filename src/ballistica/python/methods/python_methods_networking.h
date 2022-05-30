// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_NETWORKING_H_
#define BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_NETWORKING_H_

#include <vector>

#include "ballistica/ballistica.h"

namespace ballistica {

/// Networking related individual python methods for our module.
class PythonMethodsNetworking {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_NETWORKING_H_
