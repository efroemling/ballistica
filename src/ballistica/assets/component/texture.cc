// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/component/texture.h"

#include "ballistica/graphics/renderer.h"
#include "ballistica/python/class/python_class_texture.h"
#include "ballistica/scene/scene.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

Texture::Texture(const std::string& name, Scene* scene)
    : AssetComponent(name, scene), dead_(false) {
  assert(InLogicThread());

  // Add to the provided scene to get a numeric ID.
  if (scene) {
    if (SceneStream* os = scene->GetSceneStream()) {
      os->AddTexture(this);
    }
  }
  {
    Assets::AssetListLock lock;
    texture_data_ = g_assets->GetTextureData(name);
  }
  assert(texture_data_.exists());
}

// qrcode version
Texture::Texture(const std::string& qr_url) : AssetComponent(qr_url, nullptr) {
  assert(InLogicThread());
  {
    Assets::AssetListLock lock;
    texture_data_ = g_assets->GetTextureDataQRCode(qr_url);
  }
  assert(texture_data_.exists());
}

Texture::~Texture() { MarkDead(); }

void Texture::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (SceneStream* os = s->GetSceneStream()) {
      os->RemoveTexture(this);
    }
  }
  dead_ = true;
}

auto Texture::CreatePyObject() -> PyObject* {
  return PythonClassTexture::Create(this);
}

}  // namespace ballistica
