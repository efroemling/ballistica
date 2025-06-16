// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/globals_node.h"

#include <string>
#include <vector>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/support/classic_soft.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/scene.h"

// FIXME: should not need this here.
#if BA_VR_BUILD
#include "ballistica/base/graphics/graphics_vr.h"
#endif

namespace ballistica::scene_v1 {

class GlobalsNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS GlobalsNode
  BA_NODE_CREATE_CALL(CreateGlobals);
  BA_INT64_ATTR_READONLY(real_time, AppTimeMillisecs);
  BA_INT64_ATTR_READONLY(time, GetTime);
  BA_INT64_ATTR_READONLY(step, GetStep);
  BA_FLOAT_ATTR(debris_friction, debris_friction, SetDebrisFriction);
  BA_BOOL_ATTR(floor_reflection, floor_reflection, SetFloorReflection);
  BA_FLOAT_ATTR(debris_kill_height, debris_kill_height, SetDebrisKillHeight);
  BA_STRING_ATTR(camera_mode, GetCameraMode, SetCameraMode);
  BA_BOOL_ATTR(happy_thoughts_mode, happy_thoughts_mode, SetHappyThoughtsMode);
  BA_FLOAT_ARRAY_ATTR(shadow_scale, shadow_scale, SetShadowScale);
  BA_FLOAT_ARRAY_ATTR(area_of_interest_bounds, area_of_interest_bounds,
                      set_area_of_interest_bounds);
  BA_FLOAT_ARRAY_ATTR(shadow_range, shadow_range, SetShadowRange);
  BA_FLOAT_ARRAY_ATTR(shadow_offset, shadow_offset, SetShadowOffset);
  BA_BOOL_ATTR(shadow_ortho, shadow_ortho, SetShadowOrtho);
  BA_FLOAT_ARRAY_ATTR(tint, tint, SetTint);
  BA_FLOAT_ARRAY_ATTR(vr_overlay_center, vr_overlay_center, SetVROverlayCenter);
  BA_BOOL_ATTR(vr_overlay_center_enabled, vr_overlay_center_enabled,
               SetVROverlayCenterEnabled);
  BA_FLOAT_ARRAY_ATTR(ambient_color, ambient_color, SetAmbientColor);
  BA_FLOAT_ARRAY_ATTR(vignette_outer, vignette_outer, SetVignetteOuter);
  BA_FLOAT_ARRAY_ATTR(vignette_inner, vignette_inner, SetVignetteInner);
  BA_BOOL_ATTR(allow_kick_idle_players, allow_kick_idle_players,
               SetAllowKickIdlePlayers);
  BA_BOOL_ATTR(slow_motion, slow_motion, SetSlowMotion);
  BA_BOOL_ATTR(paused, paused, SetPaused);
  BA_FLOAT_ARRAY_ATTR(vr_camera_offset, vr_camera_offset, SetVRCameraOffset);
  BA_BOOL_ATTR(use_fixed_vr_overlay, use_fixed_vr_overlay,
               SetUseFixedVROverlay);
  BA_FLOAT_ATTR(vr_near_clip, vr_near_clip, SetVRNearClip);
  BA_BOOL_ATTR(music_continuous, music_continuous, set_music_continuous);
  BA_STRING_ATTR(music, music, set_music);
  BA_INT_ATTR(music_count, music_count, SetMusicCount);
#undef BA_NODE_TYPE_CLASS

  GlobalsNodeType()
      : NodeType("globals", CreateGlobals),
        real_time(this),
        time(this),
        step(this),
        debris_friction(this),
        floor_reflection(this),
        debris_kill_height(this),
        camera_mode(this),
        happy_thoughts_mode(this),
        shadow_scale(this),
        area_of_interest_bounds(this),
        shadow_range(this),
        shadow_offset(this),
        shadow_ortho(this),
        tint(this),
        vr_overlay_center(this),
        vr_overlay_center_enabled(this),
        ambient_color(this),
        vignette_outer(this),
        vignette_inner(this),
        allow_kick_idle_players(this),
        slow_motion(this),
        paused(this),
        vr_camera_offset(this),
        use_fixed_vr_overlay(this),
        vr_near_clip(this),
        music_continuous(this),
        music(this),
        music_count(this) {}
};

static NodeType* node_type{};

auto GlobalsNode::InitType() -> NodeType* {
  node_type = new GlobalsNodeType();
  return node_type;
}

GlobalsNode::GlobalsNode(Scene* scene) : Node(scene, node_type) {
  // Set ourself as the current globals node for our scene.
  this->scene()->set_globals_node(this);

  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();

  // If we're being made in a host-activity, also set ourself as the current
  // globals node for our activity. (there should only be one, so complain if
  // there already is one).
  // FIXME: Need to update this for non-host activities at some point.
  if (HostActivity* ha = context_ref().GetHostActivity()) {
    if (ha->globals_node()) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kWarning,
          "More than one globals node created in HostActivity; this "
          "shouldn't happen");
    }
    ha->SetGlobalsNode(this);

    // Set some values we always drive even when not the singleton 'current'
    // globals (stuff that only affects our activity/scene).
    ha->SetGameSpeed(slow_motion_ ? 0.32f : 1.0f);
    ha->SetPaused(paused_);
    ha->set_allow_kick_idle_players(allow_kick_idle_players_);
    this->scene()->set_use_fixed_vr_overlay(use_fixed_vr_overlay_);
  }

  // If our scene is currently the game's foreground one, go ahead and
  // push our values globally.
  if (appmode->GetForegroundScene() == this->scene()) {
    SetAsForeground();
  }
}

GlobalsNode::~GlobalsNode() {
  // If we are the current globals node for our scene, clear it out.
  if (scene()->globals_node() == this) {
    scene()->set_globals_node(nullptr);
  }
}

// Called when we're being made the one foreground node and should push our
// values to the global state (since there can be multiple scenes in
// existence, there has to be a single "foreground" globals node in control).
void GlobalsNode::SetAsForeground() {
  if (g_base && g_base->bg_dynamics != nullptr) {
    g_base->bg_dynamics->SetDebrisFriction(debris_friction_);
    g_base->bg_dynamics->SetDebrisKillHeight(debris_kill_height_);
  }
  auto* cam = g_base->graphics->camera();

  g_base->graphics->set_floor_reflection(floor_reflection());
  cam->SetMode(camera_mode());
  cam->set_vr_offset(Vector3f(vr_camera_offset()));
  cam->set_happy_thoughts_mode(happy_thoughts_mode());
  g_base->graphics->set_shadow_scale(shadow_scale()[0], shadow_scale()[1]);
  cam->set_area_of_interest_bounds(
      area_of_interest_bounds_[0], area_of_interest_bounds_[1],
      area_of_interest_bounds_[2], area_of_interest_bounds_[3],
      area_of_interest_bounds_[4], area_of_interest_bounds_[5]);
  g_base->graphics->SetShadowRange(shadow_range_[0], shadow_range_[1],
                                   shadow_range_[2], shadow_range_[3]);
  g_base->graphics->set_shadow_offset(Vector3f(shadow_offset()));
  g_base->graphics->set_shadow_ortho(shadow_ortho());
  g_base->graphics->set_tint(Vector3f(tint()));

  g_base->graphics->set_ambient_color(Vector3f(ambient_color()));
  g_base->graphics->set_vignette_outer(Vector3f(vignette_outer()));
  g_base->graphics->set_vignette_inner(Vector3f(vignette_inner()));

#if BA_VR_BUILD
  if (g_core->vr_mode()) {
    auto* graphics_vr = base::GraphicsVR::get();
    graphics_vr->set_vr_near_clip(vr_near_clip());
    graphics_vr->set_vr_overlay_center(Vector3f(vr_overlay_center()));
    graphics_vr->set_vr_overlay_center_enabled(vr_overlay_center_enabled());
  }
#endif

  g_base->audio->SetSoundPitch(slow_motion_ ? 0.4f : 1.0f);

  // Tell the scripting layer to play our current music.
  if (g_base->HaveClassic()) {
    g_base->classic()->PlayMusic(music_, music_continuous_);
  } else {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                "Classic not present; music will not play.");
  }
}

auto GlobalsNode::IsCurrentGlobals() const -> bool {
  // We're current if our scene is the foreground one and we're the globals
  // node for our scene.
  auto* appmode = classic::ClassicAppMode::GetActive();
  if (appmode == nullptr) {
    BA_LOG_ERROR_NATIVE_TRACE(
        "GlobalsNode::IsCurrentGlobals() called without ClassicAppMode "
        "active.");
    return false;
  }

  Scene* scene = this->scene();
  assert(scene);
  return (appmode->GetForegroundScene() == this->scene()
          && scene->globals_node() == this);
}

auto GlobalsNode::AppTimeMillisecs() -> millisecs_t {
  // Pull this from our scene so we return consistent values throughout a step.
  return scene()->last_step_real_time();
}

auto GlobalsNode::GetTime() -> millisecs_t { return scene()->time(); }
auto GlobalsNode::GetStep() -> int64_t { return scene()->stepnum(); }

void GlobalsNode::SetDebrisFriction(float val) {
  debris_friction_ = val;
  if (IsCurrentGlobals()) {
    if (g_base && g_base->bg_dynamics != nullptr) {
      g_base->bg_dynamics->SetDebrisFriction(debris_friction_);
    }
  }
}

void GlobalsNode::SetVRNearClip(float val) {
  vr_near_clip_ = val;
#if BA_VR_BUILD
  if (g_core->vr_mode()) {
    if (IsCurrentGlobals()) {
      base::GraphicsVR::get()->set_vr_near_clip(vr_near_clip_);
    }
  }
#endif
}

void GlobalsNode::SetFloorReflection(bool val) {
  floor_reflection_ = val;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_floor_reflection(floor_reflection_);
  }
}

void GlobalsNode::SetDebrisKillHeight(float val) {
  debris_kill_height_ = val;
  if (IsCurrentGlobals()) {
    if (g_base && g_base->bg_dynamics != nullptr) {
      g_base->bg_dynamics->SetDebrisKillHeight(debris_kill_height_);
    }
  }
}

void GlobalsNode::SetHappyThoughtsMode(bool val) {
  happy_thoughts_mode_ = val;
  if (IsCurrentGlobals()) {
    g_base->graphics->camera()->set_happy_thoughts_mode(happy_thoughts_mode_);
  }
}

void GlobalsNode::SetShadowScale(const std::vector<float>& vals) {
  if (vals.size() != 2) {
    throw Exception("Expected float array of length 2 for shadow_scale",
                    PyExcType::kValue);
  }
  shadow_scale_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_shadow_scale(shadow_scale_[0], shadow_scale_[1]);
  }
}

void GlobalsNode::set_area_of_interest_bounds(const std::vector<float>& vals) {
  if (vals.size() != 6) {
    throw Exception(
        "Expected float array of length 6 for area_of_interest_bounds",
        PyExcType::kValue);
  }
  area_of_interest_bounds_ = vals;

  assert(g_base->graphics->camera());
  if (IsCurrentGlobals()) {
    g_base->graphics->camera()->set_area_of_interest_bounds(
        area_of_interest_bounds_[0], area_of_interest_bounds_[1],
        area_of_interest_bounds_[2], area_of_interest_bounds_[3],
        area_of_interest_bounds_[4], area_of_interest_bounds_[5]);
  }
}

void GlobalsNode::SetShadowRange(const std::vector<float>& vals) {
  if (vals.size() != 4) {
    throw Exception("Expected float array of length 4 for shadow_range",
                    PyExcType::kValue);
  }
  shadow_range_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->SetShadowRange(shadow_range_[0], shadow_range_[1],
                                     shadow_range_[2], shadow_range_[3]);
  }
}

void GlobalsNode::SetShadowOffset(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for shadow_offset",
                    PyExcType::kValue);
  }
  shadow_offset_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_shadow_offset(Vector3f(shadow_offset_));
  }
}

void GlobalsNode::SetVRCameraOffset(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for vr_camera_offset",
                    PyExcType::kValue);
  }
  vr_camera_offset_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->camera()->set_vr_offset(Vector3f(vr_camera_offset_));
  }
}

void GlobalsNode::SetShadowOrtho(bool val) {
  shadow_ortho_ = val;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_shadow_ortho(shadow_ortho_);
  }
}

void GlobalsNode::SetTint(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for tint",
                    PyExcType::kValue);
  }
  tint_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_tint(Vector3f(tint_[0], tint_[1], tint_[2]));
  }
}

void GlobalsNode::SetVROverlayCenter(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for vr_overlay_center",
                    PyExcType::kValue);
  }
  vr_overlay_center_ = vals;
#if BA_VR_BUILD
  if (IsCurrentGlobals()) {
    base::GraphicsVR::get()->set_vr_overlay_center(
        Vector3f(vr_overlay_center_));
  }
#endif
}

void GlobalsNode::SetVROverlayCenterEnabled(bool val) {
  vr_overlay_center_enabled_ = val;
#if BA_VR_BUILD
  if (IsCurrentGlobals()) {
    base::GraphicsVR::get()->set_vr_overlay_center_enabled(
        vr_overlay_center_enabled_);
  }
#endif
}

void GlobalsNode::SetAmbientColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for ambient_color",
                    PyExcType::kValue);
  }
  ambient_color_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_ambient_color(Vector3f(ambient_color_));
  }
}

void GlobalsNode::SetVignetteOuter(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for vignette_outer",
                    PyExcType::kValue);
  }
  vignette_outer_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_vignette_outer(Vector3f(vignette_outer_));
  }
}

void GlobalsNode::SetVignetteInner(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for vignette_inner",
                    PyExcType::kValue);
  }
  vignette_inner_ = vals;
  if (IsCurrentGlobals()) {
    g_base->graphics->set_vignette_inner(Vector3f(vignette_inner_));
  }
}

auto GlobalsNode::GetCameraMode() const -> std::string {
  switch (camera_mode_) {
    case base::CameraMode::kOrbit:
      return "rotate";
    case base::CameraMode::kFollow:
      return "follow";
  }

    // This should be unreachable, but most compilers complain about
    // control reaching the end of non-void function without it.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
  throw Exception();
#pragma clang diagnostic pop
}

void GlobalsNode::SetCameraMode(const std::string& val) {
  if (val == "rotate") {
    camera_mode_ = base::CameraMode::kOrbit;
  } else if (val == "follow") {
    camera_mode_ = base::CameraMode::kFollow;
  } else {
    throw Exception("Invalid camera mode: '" + val
                    + R"('; expected "rotate" or "follow")");
  }
  if (IsCurrentGlobals()) g_base->graphics->camera()->SetMode(camera_mode_);
}

void GlobalsNode::SetAllowKickIdlePlayers(bool val) {
  allow_kick_idle_players_ = val;

  // This only means something if we're in a host-activity.
  if (HostActivity* ha = context_ref().GetHostActivity()) {
    // Set speed on our activity even if we're not the current globals node.
    if (ha->globals_node() == this) {
      ha->set_allow_kick_idle_players(allow_kick_idle_players_);
    }
  }
}

void GlobalsNode::SetSlowMotion(bool val) {
  slow_motion_ = val;

  // This only matters if we're in a host-activity.
  // (clients are just driven by whatever steps are in the input-stream)
  if (HostActivity* ha = context_ref().GetHostActivity()) {
    // Set speed on *our* activity regardless of whether we're the current
    // globals node.
    if (ha->globals_node() == this) {
      ha->SetGameSpeed(slow_motion_ ? 0.32f : 1.0f);
    }
  }

  // Only set pitch if we are the current globals node.
  // (FIXME - need to make this per-sound or something)
  if (IsCurrentGlobals()) {
    g_base->audio->SetSoundPitch(slow_motion_ ? 0.4f : 1.0f);
  }
}

void GlobalsNode::SetPaused(bool val) {
  paused_ = val;

  // This only matters in a host-activity.
  // (clients are just driven by whatever steps are in the input-stream)
  if (HostActivity* ha = context_ref().GetHostActivity()) {
    // Set speed on our activity even if we're not the current globals node.
    if (ha->globals_node() == this) {
      ha->SetPaused(paused_);
    }
  }
}

void GlobalsNode::SetUseFixedVROverlay(bool val) {
  use_fixed_vr_overlay_ = val;

  // Always apply this value to our scene.
  scene()->set_use_fixed_vr_overlay(val);
}

void GlobalsNode::SetMusicCount(int val) {
  if (music_count_ != val && IsCurrentGlobals()) {
    // Tell the scripting layer to play our current music.
    if (g_base->HaveClassic()) {
      g_base->classic()->PlayMusic(music_, music_continuous_);
    } else {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                  "Classic not present; music will not play (b).");
    }
    // g_classic->python->PlayMusic(music_, music_continuous_);
  }
  music_count_ = val;
}

}  // namespace ballistica::scene_v1
