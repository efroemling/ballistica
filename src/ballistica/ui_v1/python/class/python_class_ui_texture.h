// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_TEXTURE_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_TEXTURE_H_

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/python/class/python_class_asset_ref.h"

namespace ballistica::ui_v1 {

class PythonClassUITexture
    : public base::PythonClassAssetRef<PythonClassUITexture,
                                       base::TextureAsset> {
 public:
  static auto type_name() -> const char* { return "Texture"; }
  static constexpr const char* kTpName = "bauiv1.Texture";
  static constexpr const char* kTpDoc =
      "Texture asset for local user interface purposes.";
  static constexpr const char* kFactoryCall = "bauiv1.gettexture()";

  auto texture() const -> base::TextureAsset& { return asset(); }
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_TEXTURE_H_
