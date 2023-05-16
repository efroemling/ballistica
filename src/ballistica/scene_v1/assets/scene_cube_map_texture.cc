// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_cube_map_texture.h"

#include "ballistica/base/assets/assets.h"

namespace ballistica::scene_v1 {

SceneCubeMapTexture::SceneCubeMapTexture(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());

  // cant currently add these to scenes so nothing to do here..
  {
    base::Assets::AssetListLock lock;
    texture_data_ = g_base->assets->GetCubeMapTexture(name);
  }
  assert(texture_data_.Exists());
}

}  // namespace ballistica::scene_v1
