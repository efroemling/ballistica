// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_METHODS_PYTHON_METHODS_UI_V1_H_
#define BALLISTICA_UI_V1_PYTHON_METHODS_PYTHON_METHODS_UI_V1_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::ui_v1 {

/// UI related individual python methods for our module.
class PythonMethodsUIV1 {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_METHODS_PYTHON_METHODS_UI_V1_H_
