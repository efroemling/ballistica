// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_SIMPLE_SOUND_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_SIMPLE_SOUND_H_

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/python/class/python_class_asset_ref.h"

namespace ballistica::base {

class PythonClassSimpleSound
    : public PythonClassAssetRef<PythonClassSimpleSound, SoundAsset> {
 public:
  static auto type_name() -> const char* { return "SimpleSound"; }
  static constexpr const char* kTpName = "babase.SimpleSound";
  static constexpr const char* kTpDoc =
      "A simple sound wrapper for internal use.\n"
      "\n"
      "Do not use for gameplay code as it will only play locally.\n"
      "\n"
      ":meta private:";
  static constexpr const char* kFactoryCall = "babase.getsimplesound()";
  static PyMethodDef tp_methods[];

  auto sound() const -> SoundAsset& { return asset(); }

 private:
  static auto Play(PythonClassSimpleSound* self, PyObject* args,
                   PyObject* keywds) -> PyObject*;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_SIMPLE_SOUND_H_
