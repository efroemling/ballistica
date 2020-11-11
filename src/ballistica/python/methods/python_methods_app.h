// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_APP_H_
#define BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_APP_H_

#include "ballistica/python/python_sys.h"

namespace ballistica {

/// App related individual python methods for our module.
class PythonMethodsApp {
 public:
  static PyMethodDef methods_def[];
};

}  // namespace ballistica
#endif  // BALLISTICA_PYTHON_METHODS_PYTHON_METHODS_APP_H_
