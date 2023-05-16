// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CLASSIC_PYTHON_METHODS_PYTHON_METHODS_CLASSIC_H_
#define BALLISTICA_CLASSIC_PYTHON_METHODS_PYTHON_METHODS_CLASSIC_H_

#include <vector>

#include "ballistica/classic/classic.h"

namespace ballistica::classic {

class PythonMethodsClassic {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::classic

#endif  // BALLISTICA_CLASSIC_PYTHON_METHODS_PYTHON_METHODS_CLASSIC_H_
