// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_LOCATOR_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_LOCATOR_NODE_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class LocatorNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit LocatorNode(Scene* scene);

  void Draw(base::FrameDef* frame_def) override;

  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& vals);

  auto visibility() const -> bool { return visibility_; }
  void set_visibility(bool val) { visibility_ = val; }

  auto size() const -> std::vector<float> { return size_; }
  void SetSize(const std::vector<float>& vals);

  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& vals);

  auto opacity() const -> float { return opacity_; }
  void set_opacity(float val) { opacity_ = val; }

  auto draw_beauty() const -> bool { return draw_beauty_; }
  void set_draw_beauty(bool val) { draw_beauty_ = val; }

  auto getDrawShadow() const -> bool { return draw_shadow_; }
  void setDrawShadow(bool val) { draw_shadow_ = val; }

  auto getShape() const -> std::string;
  void SetShape(const std::string& val);

  auto getAdditive() const -> bool { return additive_; }
  void setAdditive(bool val) { additive_ = val; }

 private:
  enum class Shape { kLocator, kBox, kCircle, kCircleOutline };

  Shape shape_ = Shape::kLocator;
  bool additive_ = false;
  std::vector<float> position_ = {0.0f, 0.0f, 0.0f};
  std::vector<float> size_ = {1.0f, 1.0f, 1.0f};
  std::vector<float> color_ = {1.0f, 1.0f, 1.0f};
  bool visibility_ = true;
  float opacity_ = 1.0f;
  bool draw_beauty_ = true;
  bool draw_shadow_ = true;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_LOCATOR_NODE_H_
