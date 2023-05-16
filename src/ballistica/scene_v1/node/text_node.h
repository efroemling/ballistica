// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_TEXT_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_TEXT_NODE_H_

#include <string>
#include <vector>

#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class TextNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit TextNode(Scene* scene);
  ~TextNode() override;
  void Draw(base::FrameDef* frame_def) override;
  void OnLanguageChange() override;
  void OnScreenSizeChange() override;
  auto opacity() const -> float { return opacity_; }
  void set_opacity(float val) { opacity_ = val; }
  auto trail_opacity() const -> float { return trail_opacity_; }
  void set_trail_opacity(float val) { trail_opacity_ = val; }
  auto project_scale() const -> float { return project_scale_; }
  void set_project_scale(float val) { project_scale_ = val; }
  auto scale() const -> float { return scale_; }
  void set_scale(float val) { scale_ = val; }
  auto trail_project_scale() const -> float { return trail_project_scale_; }
  void set_trail_project_scale(float val) { trail_project_scale_ = val; }
  auto position() const -> const std::vector<float>& { return position_; }
  void SetPosition(const std::vector<float>& val);
  auto opacity_scales_shadow() const -> bool { return opacity_scales_shadow_; }
  void set_opacity_scales_shadow(bool val) { opacity_scales_shadow_ = val; }
  auto big() const -> bool { return big_; }
  void SetBig(bool val);
  auto trail() const -> bool { return trail_; }
  void set_trail(bool val) { trail_ = val; }
  auto getText() const -> std::string { return text_raw_; }
  void SetText(const std::string& val);
  auto GetHAlign() const -> std::string;
  void SetHAlign(const std::string& val);
  auto GetHAttach() const -> std::string;
  void SetHAttach(const std::string& val);
  auto GetVAttach() const -> std::string;
  void SetVAttach(const std::string& val);
  auto GetVAlign() const -> std::string;
  void SetVAlign(const std::string& val);
  auto color() const -> const std::vector<float>& { return color_; }
  void SetColor(const std::vector<float>& vals);
  auto trail_color() const -> std::vector<float> { return trail_color_; }
  void SetTrailColor(const std::vector<float>& vals);
  auto in_world() const -> bool { return in_world_; }
  void set_in_world(bool val) {
    in_world_ = val;
    position_final_dirty_ = true;
  }
  auto tilt_translate() const -> float { return tilt_translate_; }
  void set_tilt_translate(float val) { tilt_translate_ = val; }
  auto max_width() const -> float { return max_width_; }
  void set_max_width(float val) { max_width_ = val; }
  auto shadow() const -> float { return shadow_; }
  void set_shadow(float val) { shadow_ = val; }
  auto flatness() const -> float { return flatness_; }
  void set_flatness(float val) { flatness_ = val; }
  auto client_only() const -> bool { return client_only_; }
  void set_client_only(bool val) { client_only_ = val; }
  auto host_only() const -> bool { return host_only_; }
  void set_host_only(bool val) { host_only_ = val; }
  auto vr_depth() const -> float { return vr_depth_; }
  void set_vr_depth(float val) { vr_depth_ = val; }
  auto rotate() const -> float { return rotate_; }
  void set_rotate(float val) { rotate_ = val; }
  auto front() const -> bool { return front_; }
  void set_front(bool val) { front_ = val; }

 private:
  enum class HAlign { kLeft, kCenter, kRight };
  enum class VAlign { kNone, kTop, kCenter, kBottom };
  enum class HAttach { kLeft, kCenter, kRight };
  enum class VAttach { kTop, kCenter, kBottom };
  void Update();
  base::TextGroup text_group_;
  bool text_group_dirty_ = true;
  bool text_width_dirty_ = true;
  bool text_translation_dirty_ = true;
  bool opacity_scales_shadow_ = true;
  bool client_only_ = false;
  bool host_only_ = false;
  HAlign h_align_ = HAlign::kLeft;
  VAlign v_align_ = VAlign::kNone;
  HAttach h_attach_ = HAttach::kCenter;
  VAttach v_attach_ = VAttach::kCenter;
  float vr_depth_ = 0.0f;
  bool in_world_ = false;
  std::string text_translated_;
  std::string text_raw_;
  std::vector<float> position_ = {0.0f, 0.0f, 0.0f};
  std::vector<float> position_final_;
  bool position_final_dirty_ = true;
  float scale_ = 1.0f;
  float rotate_ = 0.0f;
  bool front_ = false;
  std::vector<float> color_ = {1.0f, 1.0f, 1.0f, 1.0f};
  std::vector<float> trail_color_ = {1.0f, 1.0f, 1.0f};
  float project_scale_ = 1.0f;
  float trail_project_scale_ = 1.0f;
  float opacity_ = 1.0f;
  float trail_opacity_ = 1.0f;
  float shadow_ = 0.0f;
  float flatness_ = 0.0f;
  bool trail_ = false;
  bool big_ = false;
  float tilt_translate_ = 0.0f;
  float max_width_ = 0.0f;
  float text_width_ = 0.0f;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_TEXT_NODE_H_
