// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_GLOBALS_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_GLOBALS_NODE_H_

#include <string>
#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class GlobalsNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit GlobalsNode(Scene* scene);
  ~GlobalsNode() override;
  void SetAsForeground();
  auto IsCurrentGlobals() const -> bool;
  auto AppTimeMillisecs() -> millisecs_t;
  auto GetTime() -> millisecs_t;
  auto GetStep() -> int64_t;
  auto debris_friction() const -> float { return debris_friction_; }
  void SetDebrisFriction(float val);
  auto floor_reflection() const -> bool { return floor_reflection_; }
  void SetFloorReflection(bool val);
  auto debris_kill_height() const -> float { return debris_kill_height_; }
  void SetDebrisKillHeight(float val);
  auto GetCameraMode() const -> std::string;
  void SetCameraMode(const std::string& val);
  void SetHappyThoughtsMode(bool val);
  auto happy_thoughts_mode() const -> bool { return happy_thoughts_mode_; }
  auto shadow_scale() const -> const std::vector<float>& {
    return shadow_scale_;
  }
  void SetShadowScale(const std::vector<float>& vals);
  auto area_of_interest_bounds() const -> const std::vector<float>& {
    return area_of_interest_bounds_;
  }
  void set_area_of_interest_bounds(const std::vector<float>& vals);
  auto shadow_range() const -> const std::vector<float>& {
    return shadow_range_;
  }
  void SetShadowRange(const std::vector<float>& vals);
  auto shadow_offset() const -> const std::vector<float>& {
    return shadow_offset_;
  }
  void SetShadowOffset(const std::vector<float>& vals);
  auto shadow_ortho() const -> bool { return shadow_ortho_; }
  void SetShadowOrtho(bool val);
  auto tint() const -> const std::vector<float>& { return tint_; }
  void SetTint(const std::vector<float>& vals);
  auto vr_overlay_center() const -> const std::vector<float>& {
    return vr_overlay_center_;
  }
  void SetVROverlayCenter(const std::vector<float>& vals);
  auto vr_overlay_center_enabled() const -> bool {
    return vr_overlay_center_enabled_;
  }
  void SetVROverlayCenterEnabled(bool);
  auto ambient_color() const -> const std::vector<float>& {
    return ambient_color_;
  }
  void SetAmbientColor(const std::vector<float>& vals);
  auto vignette_outer() const -> const std::vector<float>& {
    return vignette_outer_;
  }
  void SetVignetteOuter(const std::vector<float>& vals);
  auto vignette_inner() const -> const std::vector<float>& {
    return vignette_inner_;
  }
  void SetVignetteInner(const std::vector<float>& vals);
  auto allow_kick_idle_players() const -> bool {
    return allow_kick_idle_players_;
  }
  void SetAllowKickIdlePlayers(bool allow);
  auto slow_motion() const -> bool { return slow_motion_; }
  void SetSlowMotion(bool val);
  auto paused() const -> bool { return paused_; }
  void SetPaused(bool val);
  auto vr_camera_offset() const -> const std::vector<float>& {
    return vr_camera_offset_;
  }
  void SetVRCameraOffset(const std::vector<float>& vals);
  auto use_fixed_vr_overlay() const -> bool { return use_fixed_vr_overlay_; }
  void SetUseFixedVROverlay(bool val);
  auto vr_near_clip() const -> float { return vr_near_clip_; }
  void SetVRNearClip(float val);
  auto music_continuous() const -> bool { return music_continuous_; }
  void set_music_continuous(bool val) { music_continuous_ = val; }
  auto music() const -> const std::string& { return music_; }
  void set_music(const std::string& val) { music_ = val; }

  // We actually change the song only when this value changes
  // (allows us to restart the same song)
  auto music_count() const -> int { return music_count_; }
  void SetMusicCount(int val);

  auto camera_mode() const { return camera_mode_; }

 private:
  base::CameraMode camera_mode_{base::CameraMode::kFollow};
  float vr_near_clip_{4.0f};
  float debris_friction_{1.0f};
  bool floor_reflection_{};
  float debris_kill_height_{-50.0f};
  bool happy_thoughts_mode_{};
  bool use_fixed_vr_overlay_{};
  int music_count_{};
  bool music_continuous_{};
  std::string music_;
  std::vector<float> vr_camera_offset_{0.0f, 0.0f, 0.0f};
  std::vector<float> shadow_scale_{1.0f, 1.0f};
  std::vector<float> area_of_interest_bounds_{-9999.0f, -9999.0f, -9999.0f,
                                              9999.0f,  9999.0f,  9999.0f};
  std::vector<float> shadow_range_{-4.0f, 0.0f, 10.0f, 15.0f};
  std::vector<float> shadow_offset_{0.0f, 0.0f, 0.0f};
  bool shadow_ortho_{};
  bool vr_overlay_center_enabled_{};
  std::vector<float> vr_overlay_center_{0.0f, 4.0f, -3.0f};
  std::vector<float> tint_{1.1f, 1.0f, 0.9f};
  std::vector<float> ambient_color_{1.0f, 1.0f, 1.0f};
  std::vector<float> vignette_outer_{0.6f, 0.6f, 0.6f};
  std::vector<float> vignette_inner_{0.95f, 0.95f, 0.95f};
  bool allow_kick_idle_players_{};
  bool slow_motion_{};
  bool paused_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_GLOBALS_NODE_H_
