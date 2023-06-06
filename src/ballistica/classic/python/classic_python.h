// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CLASSIC_PYTHON_CLASSIC_PYTHON_H_
#define BALLISTICA_CLASSIC_PYTHON_CLASSIC_PYTHON_H_

#include "ballistica/base/base.h"
#include "ballistica/classic/classic.h"
#include "ballistica/shared/python/python_object_set.h"

namespace ballistica::classic {

/// General Python support class for the classic feature-set.
class ClassicPython {
 public:
  ClassicPython();

  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kDoPlayMusicCall,
    kGetInputDeviceMappedValueCall,
    kLast  // Sentinel; must be at end.
  };

  void ImportPythonObjs();

  void PlayMusic(const std::string& music_type, bool continuous);
  auto GetControllerValue(base::InputDevice* device,
                          const std::string& value_name) -> int;
  auto GetControllerFloatValue(base::InputDevice* device,
                               const std::string& value_name) -> float;
  auto BuildPublicPartyStateVal() -> PyObject*;

  const auto& objs() { return objs_; }

 private:
  PythonObjectSet<ObjID> objs_;
};

}  // namespace ballistica::classic

#endif  // BALLISTICA_CLASSIC_PYTHON_CLASSIC_PYTHON_H_
