// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_MESH_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_MESH_H_

#include "ballistica/base/python/class/python_class_asset_ref.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"

namespace ballistica::scene_v1 {

class PythonClassSceneMesh
    : public base::PythonClassAssetRef<PythonClassSceneMesh, SceneMesh> {
 public:
  static auto type_name() -> const char* { return "Mesh"; }
  static constexpr const char* kTpName = "bascenev1.Mesh";
  static constexpr const char* kTpDoc =
      "A reference to a mesh.\n"
      "\n"
      "Meshes are used for drawing.\n"
      "Use :meth:`bascenev1.getmesh()` to instantiate one.";
  static constexpr const char* kFactoryCall = "bascenev1.getmesh()";

  auto GetMesh(bool doraise = true) const -> SceneMesh* {
    return GetAsset(doraise);
  }
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_MESH_H_
