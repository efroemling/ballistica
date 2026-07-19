// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_TEXTURE_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_TEXTURE_H_

#include "ballistica/base/python/class/python_class_asset_ref.h"
#include "ballistica/scene_v1/assets/scene_texture.h"

namespace ballistica::scene_v1 {

class PythonClassSceneTexture
    : public base::PythonClassAssetRef<PythonClassSceneTexture, SceneTexture> {
 public:
  static auto type_name() -> const char* { return "Texture"; }
  static constexpr const char* kTpName = "bascenev1.Texture";
  static constexpr const char* kTpDoc =
      "A reference to a texture.\n"
      "\n"
      "Use :meth:`bascenev1.gettexture()` to instantiate one.";
  static constexpr const char* kFactoryCall = "bascenev1.gettexture()";

  auto GetTexture(bool doraise = true) const -> SceneTexture* {
    return GetAsset(doraise);
  }
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_TEXTURE_H_
