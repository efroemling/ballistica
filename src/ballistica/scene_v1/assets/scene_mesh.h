// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_MESH_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_MESH_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/assets/mesh_asset_renderer_data.h"
#include "ballistica/scene_v1/assets/scene_asset.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// Usage of a mesh in a scene.
class SceneMesh : public SceneAsset {
 public:
  SceneMesh(const std::string& name, Scene* scene);
  ~SceneMesh() override;

  auto mesh_data() const -> base::MeshAsset* { return mesh_data_.Get(); }
  auto GetAssetTypeName() const -> std::string override { return "Mesh"; }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  Object::Ref<base::MeshAsset> mesh_data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_MESH_H_
