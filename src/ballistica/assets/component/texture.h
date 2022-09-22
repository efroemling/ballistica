// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_COMPONENT_TEXTURE_H_
#define BALLISTICA_ASSETS_COMPONENT_TEXTURE_H_

#include <string>

#include "ballistica/assets/component/asset_component.h"
#include "ballistica/assets/data/texture_data.h"

namespace ballistica {

// User-facing texture class.
class Texture : public AssetComponent {
 public:
  Texture(const std::string& name, Scene* scene);
  explicit Texture(const std::string& qr_url);
  ~Texture() override;

  // Return the TextureData currently associated with this texture.
  // Note that a texture's data can change over time as different
  // versions are spooled in/out/etc.
  auto texture_data() const -> TextureData* { return texture_data_.get(); }
  auto GetAssetComponentTypeName() const -> std::string override {
    return "Texture";
  }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  bool dead_ = false;
  Object::Ref<TextureData> texture_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_COMPONENT_TEXTURE_H_
