// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_TEST_H_
#define BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_TEST_H_

#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

/// Python methods for running C++ self-tests via _babase.
class PythonMethodsTest {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_METHODS_PYTHON_METHODS_TEST_H_
