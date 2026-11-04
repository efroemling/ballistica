// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_REMOTE_PYTHON_METHODS_PYTHON_METHODS_REMOTE_H_
#define BALLISTICA_REMOTE_PYTHON_METHODS_PYTHON_METHODS_REMOTE_H_

#include <vector>

#include "ballistica/remote/remote.h"

namespace ballistica::remote {

class PythonMethodsRemote {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::remote

#endif  // BALLISTICA_REMOTE_PYTHON_METHODS_PYTHON_METHODS_REMOTE_H_
