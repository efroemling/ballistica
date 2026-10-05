// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_SOUND_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_SOUND_H_

#include <cstdint>

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/python/class/python_class_asset_ref.h"

namespace ballistica::ui_v1 {

class PythonClassUISound
    : public base::PythonClassAssetRef<PythonClassUISound, base::SoundAsset> {
 public:
  static auto type_name() -> const char* { return "Sound"; }
  static constexpr const char* kTpName = "bauiv1.Sound";
  static constexpr const char* kTpDoc =
      "Sound asset for local user interface purposes.";
  static constexpr const char* kFactoryCall = "bauiv1.getsound()";
  static PyMethodDef tp_methods[];

  auto sound() const -> base::SoundAsset& { return asset(); }

 private:
  static auto Play(PythonClassUISound* self, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto Stop(PythonClassUISound* self, PyObject* args, PyObject* keywds)
      -> PyObject*;

  // NOTE: instances come from tp_alloc (zero-filled); C++ constructors
  // never run, so no in-class initializers here.
  bool playing_;
  uint32_t play_id_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_SOUND_H_
