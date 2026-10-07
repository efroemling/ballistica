// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_DEPICTION_DISPLAY_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_DEPICTION_DISPLAY_NODE_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/depiction/depiction.h"
#include "ballistica/base/support/lang_str.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

/// Hosts a depiction (bacommon.depiction) as a 2d screen overlay in a
/// scene: the in-scene twin of ui_v1's DepictionSlot. The depiction
/// arrives as a session-level object (the 'depiction' attr), so one
/// registered name or icon can show in many places. Every machine
/// showing the node makes its own depiction from its json -- so kinds a
/// machine can't draw become its placeholder, and art a machine doesn't
/// have yet shows as a standin there until it arrives.
///
/// Layout follows the image node: 'position' is the box center in
/// virtual pixels relative to 'attach', 'scale' is the box (w, h); a
/// depiction with a shape of its own is fitted inside it by
/// 'h_align'/'v_align'. Protocol 47 (see scene_v1.h). Design:
/// docs/initiatives/depictions.md.
///
/// Since protocol 52: 'color_override' (rgb) is imposed on the
/// depiction while 'use_color_override' is set (each kind decides what
/// it applies to; see base::DepictionDrawContext), 'brightness' scales
/// everything it draws (animate it to flash), and 'suffix' (text, as a
/// text node's) trails the depiction ("(ready)" after a name), fitted
/// into the box along with it on each machine.
class DepictionDisplayNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit DepictionDisplayNode(Scene* scene);
  ~DepictionDisplayNode() override;
  void Draw(base::FrameDef* frame_def) override;
  void OnScreenSizeChange() override { dirty_ = true; }

  auto depiction() const -> SceneDepiction* { return depiction_obj_.get(); }
  void SetDepiction(SceneDepiction* val);
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& val);
  auto scale() const -> std::vector<float> { return scale_; }
  void SetScale(const std::vector<float>& val);
  auto opacity() const -> float { return opacity_; }
  void set_opacity(float val) { opacity_ = val; }
  auto GetAttach() const -> std::string;
  void SetAttach(const std::string& val);
  auto GetHAlign() const -> std::string;
  void SetHAlign(const std::string& val);
  auto GetVAlign() const -> std::string;
  void SetVAlign(const std::string& val);
  auto vr_depth() const -> float { return vr_depth_; }
  void set_vr_depth(float val) { vr_depth_ = val; }
  auto host_only() const -> bool { return host_only_; }
  void set_host_only(bool val) { host_only_ = val; }
  auto front() const -> bool { return front_; }
  void set_front(bool val) { front_ = val; }
  auto color_override() const -> std::vector<float> {
    return {color_override_[0], color_override_[1], color_override_[2]};
  }
  void SetColorOverride(const std::vector<float>& val);
  auto use_color_override() const -> bool { return use_color_override_; }
  void set_use_color_override(bool val) { use_color_override_ = val; }
  auto brightness() const -> float { return brightness_; }
  void set_brightness(float val) { brightness_ = val; }
  auto GetSuffix() const -> std::string { return suffix_raw_; }
  void SetSuffix(const std::string& val);
  void SetSuffixWire(const std::string& wire,
                     std::shared_ptr<const base::LangStr> parsed);
  auto suffix_lang_str() const -> std::shared_ptr<const base::LangStr> {
    return suffix_lang_str_;
  }
  void OnLanguageChange() override { suffix_dirty_ = true; }

 private:
  /// How suffix_raw_ is to be read (as a text node's text; see
  /// TextNode).
  enum class SuffixMode : uint8_t { kLegacy, kLiteral, kLegacyJson, kLangStr };
  void UpdateSuffix_();
  enum class Attach : uint8_t {
    kCenter,
    kTopLeft,
    kTopCenter,
    kTopRight,
    kCenterRight,
    kBottomRight,
    kBottomCenter,
    kBottomLeft,
    kCenterLeft,
  };

  void UpdateLayout_(float screen_width, float screen_height);
  Object::Ref<SceneDepiction> depiction_obj_;
  Object::Ref<base::Depiction> depiction_;
  bool dirty_{true};
  bool host_only_{};
  bool front_{};
  Attach attach_{Attach::kCenter};
  base::DepictionHAlign h_align_{base::DepictionHAlign::kCenter};
  base::DepictionVAlign v_align_{base::DepictionVAlign::kCenter};
  float vr_depth_{};
  float opacity_{1.0f};
  std::vector<float> position_{0.0f, 0.0f};
  std::vector<float> scale_{100.0f, 100.0f};
  // Laid out from the above: the box center and size.
  float center_x_{};
  float center_y_{};
  float width_{};
  float height_{};
  // See base::DepictionDrawContext.
  float color_override_[3]{1.0f, 1.0f, 1.0f};
  bool use_color_override_{};
  float brightness_{1.0f};
  std::string suffix_raw_;
  SuffixMode suffix_mode_{SuffixMode::kLegacy};
  std::shared_ptr<const base::LangStr> suffix_lang_str_;
  bool suffix_dirty_{};
  base::DepictionSuffix suffix_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_DEPICTION_DISPLAY_NODE_H_
