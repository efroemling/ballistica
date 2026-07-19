// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_MESH_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_MESH_H_

#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/python/class/python_class_asset_ref.h"

namespace ballistica::ui_v1 {

class PythonClassUIMesh
    : public base::PythonClassAssetRef<PythonClassUIMesh, base::MeshAsset> {
 public:
  static auto type_name() -> const char* { return "Mesh"; }
  static constexpr const char* kTpName = "bauiv1.Mesh";
  static constexpr const char* kTpDoc =
      "Mesh asset for local user interface purposes.";
  static constexpr const char* kFactoryCall = "bauiv1.getmesh()";

  auto mesh() const -> base::MeshAsset& { return asset(); }
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_MESH_H_
