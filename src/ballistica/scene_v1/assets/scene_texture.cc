// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/assets/scene_texture.h"

#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/scene_v1/python/class/python_class_scene_texture.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"

namespace ballistica::scene_v1 {

SceneTexture::SceneTexture(const std::string& name, Scene* scene)
    : SceneAsset(name, scene) {
  assert(g_base->InLogicThread());

  // Add to the provided scene to get a numeric ID.
  if (scene) {
    if (SessionStream* os = scene->GetSceneStream()) {
      os->AddTexture(this);
    }
  }
  {
    base::Assets::AssetListLock lock;
    texture_data_ = g_base->assets->GetTexture(name);
  }
  assert(texture_data_.Exists());
}

// qrcode version
SceneTexture::SceneTexture(const std::string& qr_url)
    : SceneAsset(qr_url, nullptr) {
  assert(g_base->InLogicThread());
  {
    base::Assets::AssetListLock lock;
    texture_data_ = g_base->assets->GetQRCodeTexture(qr_url);
  }
  assert(texture_data_.Exists());
}

SceneTexture::~SceneTexture() { MarkDead(); }

void SceneTexture::MarkDead() {
  if (dead()) {
    return;
  }
  set_dead(true);

  if (Scene* s = scene()) {
    if (SessionStream* os = s->GetSceneStream()) {
      os->RemoveTexture(this);
    }
  }

  // If we've created a Python ref, it's likewise holding a ref
  // to us, which is a dependency loop. Break the loop to allow us
  // to go down cleanly.
  ReleasePyObj();
}

auto SceneTexture::CreatePyObject() -> PyObject* {
  return PythonClassSceneTexture::Create(this);
}

}  // namespace ballistica::scene_v1
