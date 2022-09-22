// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_WIDGET_IMAGE_WIDGET_H_
#define BALLISTICA_UI_WIDGET_IMAGE_WIDGET_H_

#include <string>

#include "ballistica/assets/component/model.h"
#include "ballistica/assets/component/texture.h"
#include "ballistica/ui/widget/widget.h"

namespace ballistica {

class ImageWidget : public Widget {
 public:
  ImageWidget();
  ~ImageWidget() override;
  void Draw(RenderPass* pass, bool transparent) override;
  auto HandleMessage(const WidgetMessage& m) -> bool override;
  void set_width(float width) {
    image_dirty_ = true;
    width_ = width;
  }
  void set_height(float val) {
    image_dirty_ = true;
    height_ = val;
  }
  auto GetWidth() -> float override;
  auto GetHeight() -> float override;
  void set_has_alpha_channel(bool val) { has_alpha_channel_ = val; }
  void set_color(float r, float g, float b) {
    color_red_ = r;
    color_green_ = g;
    color_blue_ = b;
  }
  void set_tint_color(float r, float g, float b) {
    tint_color_red_ = r;
    tint_color_green_ = g;
    tint_color_blue_ = b;
  }
  void set_tint2_color(float r, float g, float b) {
    tint2_color_red_ = r;
    tint2_color_green_ = g;
    tint2_color_blue_ = b;
  }
  void set_opacity(float o) { opacity_ = o; }
  void SetTexture(Texture* val) {
    if (val && !val->IsFromUIContext())
      throw Exception("texture is not from the UI context: "
                      + val->GetObjectDescription());
    texture_ = val;
  }
  void SetTintTexture(Texture* val) {
    if (val && !val->IsFromUIContext())
      throw Exception("texture is not from the UI context: "
                      + val->GetObjectDescription());
    tint_texture_ = val;
  }
  void SetMaskTexture(Texture* val) {
    if (val && !val->IsFromUIContext()) {
      throw Exception("texture is not from the UI context: "
                      + val->GetObjectDescription());
    }
    mask_texture_ = val;
  }
  void SetModelTransparent(Model* val) {
    if (val && !val->IsFromUIContext()) {
      throw Exception("model_transparent is not from UI context");
    }
    image_dirty_ = true;
    model_transparent_ = val;
  }
  void SetModelOpaque(Model* val) {
    if (val && !val->IsFromUIContext()) {
      throw Exception("model_opaque is not from UI context");
    }
    image_dirty_ = true;
    model_opaque_ = val;
  }
  auto GetWidgetTypeName() -> std::string override { return "image"; }
  void set_transition_delay(float val) { transition_delay_ = val; }
  void set_tilt_scale(float s) { tilt_scale_ = s; }
  void set_radial_amount(float val) { radial_amount_ = val; }

 private:
  float tilt_scale_{1.0f};
  float transition_delay_{};
  millisecs_t birth_time_{};
  Object::Ref<Texture> texture_;
  Object::Ref<Texture> tint_texture_;
  Object::Ref<Texture> mask_texture_;
  Object::Ref<Model> model_transparent_;
  Object::Ref<Model> model_opaque_;
  Object::Ref<MeshIndexedSimpleFull> radial_mesh_;
  float image_width_{};
  float image_height_{};
  float image_center_x_{};
  float image_center_y_{};
  float radial_amount_{1.0f};
  bool image_dirty_{true};
  float width_{50.0f};
  float height_{30.0f};
  bool has_alpha_channel_{true};
  float color_red_{1.0f};
  float color_green_{1.0f};
  float color_blue_{1.0f};
  float tint_color_red_{1.0f};
  float tint_color_green_{1.0f};
  float tint_color_blue_{1.0f};
  float tint2_color_red_{1.0f};
  float tint2_color_green_{1.0f};
  float tint2_color_blue_{1.0f};
  float opacity_{1.0f};
};

}  // namespace ballistica

#endif  // BALLISTICA_UI_WIDGET_IMAGE_WIDGET_H_
