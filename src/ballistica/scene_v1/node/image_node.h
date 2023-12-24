// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_IMAGE_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_IMAGE_NODE_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

// Node used to draw 2d image overlays on-screen.
class ImageNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit ImageNode(Scene* scene);
  ~ImageNode() override;
  void Draw(base::FrameDef* frame_def) override;
  auto scale() const -> std::vector<float> { return scale_; }
  void SetScale(const std::vector<float>& scale);
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& val);
  auto opacity() const -> float { return opacity_; }
  void set_opacity(float val) { opacity_ = val; }
  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& val);
  auto tint_color() const -> std::vector<float> { return tint_color_; }
  void SetTintColor(const std::vector<float>& val);
  auto tint2_color() const -> std::vector<float> { return tint2_color_; }
  void SetTint2Color(const std::vector<float>& val);
  auto fill_screen() const -> bool { return fill_screen_; }
  void SetFillScreen(bool val);
  auto has_alpha_channel() const -> bool { return has_alpha_channel_; }
  void set_has_alpha_channel(bool val) { has_alpha_channel_ = val; }
  auto absolute_scale() const -> bool { return absolute_scale_; }
  void set_absolute_scale(bool val) {
    absolute_scale_ = val;
    dirty_ = true;
  }
  auto tilt_translate() const -> float { return tilt_translate_; }
  void set_tilt_translate(float val) { tilt_translate_ = val; }
  auto rotate() const -> float { return rotate_; }
  void set_rotate(float val) { rotate_ = val; }
  auto premultiplied() const -> bool { return premultiplied_; }
  void set_premultiplied(bool val) { premultiplied_ = val; }
  auto GetAttach() const -> std::string;
  void SetAttach(const std::string& val);
  auto texture() const -> SceneTexture* { return texture_.Get(); }
  void set_texture(SceneTexture* t) { texture_ = t; }
  auto tint_texture() const -> SceneTexture* { return tint_texture_.Get(); }
  void set_tint_texture(SceneTexture* t) { tint_texture_ = t; }
  auto mask_texture() const -> SceneTexture* { return mask_texture_.Get(); }
  void set_mask_texture(SceneTexture* t) { mask_texture_ = t; }
  auto mesh_opaque() const -> SceneMesh* { return mesh_opaque_.Get(); }
  void set_mesh_opaque(SceneMesh* m) { mesh_opaque_ = m; }
  auto mesh_transparent() const -> SceneMesh* {
    return mesh_transparent_.Get();
  }
  void set_mesh_transparent(SceneMesh* m) {
    mesh_transparent_ = m;
    dirty_ = true;
  }
  auto vr_depth() const -> float { return vr_depth_; }
  void set_vr_depth(float val) { vr_depth_ = val; }
  void OnScreenSizeChange() override;
  auto host_only() const -> bool { return host_only_; }
  void set_host_only(bool val) { host_only_ = val; }
  auto front() const -> bool { return front_; }
  void set_front(bool val) { front_ = val; }

 private:
  enum class Attach : uint8_t {
    CENTER,
    TOP_LEFT,
    TOP_CENTER,
    TOP_RIGHT,
    CENTER_RIGHT,
    BOTTOM_RIGHT,
    BOTTOM_CENTER,
    BOTTOM_LEFT,
    CENTER_LEFT
  };

  bool host_only_{};
  bool front_{};
  bool absolute_scale_{true};
  bool premultiplied_{};
  bool fill_screen_{};
  bool has_alpha_channel_{true};
  bool dirty_{true};
  Attach attach_{Attach::CENTER};

  float vr_depth_{};
  float opacity_{1.0f};
  float center_x_{};
  float center_y_{};
  float width_{};
  float height_{};
  float tilt_translate_{};
  float rotate_{};
  float red_{1.0f};
  float green_{1.0f};
  float blue_{1.0f};
  float alpha_{1.0f};
  float tint_red_{1.0f};
  float tint_green_{1.0f};
  float tint_blue_{1.0f};
  float tint2_red_{1.0f};
  float tint2_green_{1.0f};
  float tint2_blue_{1.0f};
  std::vector<float> scale_{1.0f, 1.0f};
  std::vector<float> position_{0.0f, 0.0f};
  std::vector<float> color_{1.0f, 1.0f, 1.0f};
  std::vector<float> tint_color_{1.0f, 1.0f, 1.0f};
  std::vector<float> tint2_color_{1.0f, 1.0f, 1.0f};
  Object::Ref<SceneTexture> texture_;
  Object::Ref<SceneTexture> tint_texture_;
  Object::Ref<SceneTexture> mask_texture_;
  Object::Ref<SceneMesh> mesh_opaque_;
  Object::Ref<SceneMesh> mesh_transparent_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_IMAGE_NODE_H_
