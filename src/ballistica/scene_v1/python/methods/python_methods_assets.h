// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_METHODS_PYTHON_METHODS_ASSETS_H_
#define BALLISTICA_SCENE_V1_PYTHON_METHODS_PYTHON_METHODS_ASSETS_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::scene_v1 {

/// Asset related individual python methods for our module.
class PythonMethodsAssets {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_METHODS_PYTHON_METHODS_ASSETS_H_
