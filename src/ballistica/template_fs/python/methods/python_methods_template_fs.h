// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_TEMPLATE_FS_PYTHON_METHODS_PYTHON_METHODS_TEMPLATE_FS_H_
#define BALLISTICA_TEMPLATE_FS_PYTHON_METHODS_PYTHON_METHODS_TEMPLATE_FS_H_

#include <vector>

#include "ballistica/template_fs/template_fs.h"

namespace ballistica::template_fs {

class PythonMethodsTemplateFs {
 public:
  static auto GetMethods() -> std::vector<PyMethodDef>;
};

}  // namespace ballistica::template_fs

#endif  // BALLISTICA_TEMPLATE_FS_PYTHON_METHODS_PYTHON_METHODS_TEMPLATE_FS_H_
