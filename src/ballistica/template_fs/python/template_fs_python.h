// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_TEMPLATE_FS_PYTHON_TEMPLATE_FS_PYTHON_H_
#define BALLISTICA_TEMPLATE_FS_PYTHON_TEMPLATE_FS_PYTHON_H_

#include "ballistica/shared/python/python_object_set.h"
#include "ballistica/template_fs/template_fs.h"

namespace ballistica::template_fs {

/// General Python support class for our feature-set.
class TemplateFsPython {
 public:
  /// Call our hello-world call we grabbed from Python.
  void HelloWorld();

  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kHelloWorldCall,
    kLast  // Sentinel; must be at end.
  };

  void AddPythonClasses(PyObject* module);
  void ImportPythonObjs();
  const auto& objs() { return objs_; }

 private:
  PythonObjectSet<ObjID> objs_;
};

}  // namespace ballistica::template_fs

#endif  // BALLISTICA_TEMPLATE_FS_PYTHON_TEMPLATE_FS_PYTHON_H_
