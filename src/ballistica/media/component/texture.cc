// Released under the MIT License. See LICENSE for details.

#include "ballistica/media/component/texture.h"

#include "ballistica/game/game_stream.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/python/class/python_class_texture.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

Texture::Texture(const std::string& name, Scene* scene)
    : MediaComponent(name, scene), dead_(false) {
  assert(InLogicThread());

  // Add to the provided scene to get a numeric ID.
  if (scene) {
    if (GameStream* os = scene->GetGameStream()) {
      os->AddTexture(this);
    }
  }
  {
    Media::MediaListsLock lock;
    texture_data_ = g_media->GetTextureData(name);
  }
  assert(texture_data_.exists());
}

// qrcode version
Texture::Texture(const std::string& qr_url) : MediaComponent(qr_url, nullptr) {
  assert(InLogicThread());
  {
    Media::MediaListsLock lock;
    texture_data_ = g_media->GetTextureDataQRCode(qr_url);
  }
  assert(texture_data_.exists());
}

Texture::~Texture() { MarkDead(); }

void Texture::MarkDead() {
  if (dead_) {
    return;
  }
  if (Scene* s = scene()) {
    if (GameStream* os = s->GetGameStream()) {
      os->RemoveTexture(this);
    }
  }
  dead_ = true;
}

auto Texture::CreatePyObject() -> PyObject* {
  return PythonClassTexture::Create(this);
}

}  // namespace ballistica
