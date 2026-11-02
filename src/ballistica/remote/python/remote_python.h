// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_REMOTE_PYTHON_REMOTE_PYTHON_H_
#define BALLISTICA_REMOTE_PYTHON_REMOTE_PYTHON_H_

#include "ballistica/remote/remote.h"
#include "ballistica/shared/python/python_object_set.h"

namespace ballistica::remote {

/// General Python support class for our feature-set.
class RemotePython {
 public:
  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kLast  // Sentinel; must be at end.
  };

  void AddPythonClasses(PyObject* module);
  void ImportPythonObjs();
  const auto& objs() { return objs_; }

 private:
  PythonObjectSet<ObjID> objs_;
};

}  // namespace ballistica::remote

#endif  // BALLISTICA_REMOTE_PYTHON_REMOTE_PYTHON_H_
