// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DATA_ASSET_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DATA_ASSET_H_

#include "ballistica/base/python/class/python_class_asset_ref.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"

namespace ballistica::scene_v1 {

class PythonClassSceneDataAsset
    : public base::PythonClassAssetRef<PythonClassSceneDataAsset,
                                       SceneDataAsset> {
 public:
  static auto type_name() -> const char* { return "Data"; }
  static constexpr const char* kTpName = "bascenev1.Data";
  static constexpr const char* kTpDoc =
      "A reference to a data object.\n"
      "\n"
      "Use :meth:`bascenev1.getdata()` to instantiate one.";
  static constexpr const char* kFactoryCall = "bascenev1.getdata()";
  static PyMethodDef tp_methods[];

  auto GetData(bool doraise = true) const -> SceneDataAsset* {
    return GetAsset(doraise);
  }

 private:
  static auto GetValue(PythonClassSceneDataAsset* self) -> PyObject*;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_DATA_ASSET_H_
