// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SQUADS_PYTHON_SQUADS_PYTHON_H_
#define BALLISTICA_SQUADS_PYTHON_SQUADS_PYTHON_H_

#include "ballistica/shared/python/python_object_set.h"
#include "ballistica/squads/squads.h"

namespace ballistica::squads {

/// General Python support class for our feature-set.
class SquadsPython {
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

}  // namespace ballistica::squads

#endif  // BALLISTICA_SQUADS_PYTHON_SQUADS_PYTHON_H_
