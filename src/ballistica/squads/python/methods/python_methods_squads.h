// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SQUADS_PYTHON_METHODS_PYTHON_METHODS_SQUADS_H_
#define BALLISTICA_SQUADS_PYTHON_METHODS_PYTHON_METHODS_SQUADS_H_

#include <vector>

#include "ballistica/squads/squads.h"

namespace ballistica::squads {

class PythonMethodsSquads {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::squads

#endif  // BALLISTICA_SQUADS_PYTHON_METHODS_PYTHON_METHODS_SQUADS_H_
