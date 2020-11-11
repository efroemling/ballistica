// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_TEXTURE_H_
#define BALLISTICA_MEDIA_COMPONENT_TEXTURE_H_

#include <string>

#include "ballistica/media/component/media_component.h"
#include "ballistica/media/data/texture_data.h"

namespace ballistica {

// User-facing texture class.
class Texture : public MediaComponent {
 public:
  Texture(const std::string& name, Scene* scene);
  explicit Texture(const std::string& qr_url);
  ~Texture() override;

  // Return the TextureData currently associated with this texture.
  // Note that a texture's data can change over time as different
  // versions are spooled in/out/etc.
  auto texture_data() const -> TextureData* { return texture_data_.get(); }
  auto GetMediaComponentTypeName() const -> std::string override {
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

#endif  // BALLISTICA_MEDIA_COMPONENT_TEXTURE_H_
