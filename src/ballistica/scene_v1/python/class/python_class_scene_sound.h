// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_SOUND_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_SOUND_H_

#include "ballistica/base/python/class/python_class_asset_ref.h"
#include "ballistica/scene_v1/assets/scene_sound.h"

namespace ballistica::scene_v1 {

class PythonClassSceneSound
    : public base::PythonClassAssetRef<PythonClassSceneSound, SceneSound> {
 public:
  static auto type_name() -> const char* { return "Sound"; }
  static constexpr const char* kTpName = "bascenev1.Sound";
  static constexpr const char* kTpDoc =
      "A reference to a sound.\n"
      "\n"
      "Use :meth:`bascenev1.getsound()` to instantiate one.";
  static constexpr const char* kFactoryCall = "bascenev1.getsound()";
  static PyMethodDef tp_methods[];

  auto GetSound(bool doraise = true) const -> SceneSound* {
    return GetAsset(doraise);
  }

 private:
  static auto Play(PythonClassSceneSound* self, PyObject* args,
                   PyObject* keywds) -> PyObject*;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_SOUND_H_
