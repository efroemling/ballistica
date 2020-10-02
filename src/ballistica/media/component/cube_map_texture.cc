// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/media/component/cube_map_texture.h"

#include "ballistica/media/media.h"

namespace ballistica {

CubeMapTexture::CubeMapTexture(const std::string& name, Scene* scene)
    : MediaComponent(name, scene) {
  assert(InGameThread());

  // cant currently add these to scenes so nothing to do here..
  {
    Media::MediaListsLock lock;
    texture_data_ = g_media->GetCubeMapTextureData(name);
  }
  assert(texture_data_.exists());
}

}  // namespace ballistica
