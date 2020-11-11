// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_SYSTEM_H_
#define BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_SYSTEM_H_

#include "ballistica/python/python_sys.h"

namespace ballistica {

/// System related individual python methods for our module.
class PythonMethodsSystem {
 public:
  static PyMethodDef methods_def[];
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_SYSTEM_H_
