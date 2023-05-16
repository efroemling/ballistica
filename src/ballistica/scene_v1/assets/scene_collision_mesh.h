// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_COLLISION_MESH_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_COLLISION_MESH_H_

#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/collision_mesh_asset.h"
#include "ballistica/scene_v1/assets/scene_asset.h"

namespace ballistica::scene_v1 {

// Usage of a collision-mesh in a scene.
class SceneCollisionMesh : public SceneAsset {
 public:
  SceneCollisionMesh(const std::string& name, Scene* scene);
  ~SceneCollisionMesh() override;

  auto collision_mesh_data() const -> base::CollisionMeshAsset* {
    return collision_mesh_data_.Get();
  }
  auto GetAssetTypeName() const -> std::string override {
    return "CollisionMesh";
  }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  Object::Ref<base::CollisionMeshAsset> collision_mesh_data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_COLLISION_MESH_H_
