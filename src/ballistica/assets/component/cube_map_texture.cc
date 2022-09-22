// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/component/cube_map_texture.h"

#include "ballistica/assets/assets.h"

namespace ballistica {

CubeMapTexture::CubeMapTexture(const std::string& name, Scene* scene)
    : AssetComponent(name, scene) {
  assert(InLogicThread());

  // cant currently add these to scenes so nothing to do here..
  {
    Assets::AssetListLock lock;
    texture_data_ = g_assets->GetCubeMapTextureData(name);
  }
  assert(texture_data_.exists());
}

}  // namespace ballistica
