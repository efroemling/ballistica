// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/graphics.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/post_process_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/component/special_component.h"
#include "ballistica/base/graphics/component/sprite_component.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/mesh/image_mesh.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_16.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_object_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/debug_texture_view.h"
#include "ballistica/base/graphics/support/game_camera.h"
#include "ballistica/base/graphics/support/net_graph.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/thread_cpu_time.h"

namespace ballistica::base {

const float kScreenTextZDepth{-0.06f};
const float kProgressBarZDepth{0.0f};
const int kProgressBarFadeTime{250};
const float kDebugImgZDepth{-0.04f};
const float kScreenMeshZDepth{-0.05f};

auto Graphics::IsShaderTransparent(ShadingType c) -> bool {
  switch (c) {
    case ShadingType::kSimpleColorTransparent:
    case ShadingType::kSimpleColorTransparentDoubleSided:
    case ShadingType::kObjectTransparent:
    case ShadingType::kObjectLightShadowTransparent:
    case ShadingType::kObjectLightShadowFacingRatioTransparent:
    case ShadingType::kObjectReflectTransparent:
    case ShadingType::kObjectReflectAddTransparent:
    case ShadingType::kSimpleTextureModulatedTransparent:
    case ShadingType::kSimpleTextureModulatedTransFlatness:
    case ShadingType::kSimpleTextureModulatedTransparentDoubleSided:
    case ShadingType::kSimpleTextureModulatedTransparentColorized:
    case ShadingType::kSimpleTextureModulatedTransparentColorizedMasked:
    case ShadingType::kSimpleTextureModulatedTransparentShadow:
    case ShadingType::kSimpleTexModulatedTransShadowFlatness:
    case ShadingType::kSimpleTextureModulatedTransparentGlow:
    case ShadingType::kSimpleTextureModulatedTransparentGlowMaskUV2:
    case ShadingType::kSpecial:
    case ShadingType::kShield:
    case ShadingType::kSmoke:
    case ShadingType::kSmokeOverlay:
    case ShadingType::kSprite:
      return true;
    case ShadingType::kSimpleColor:
    case ShadingType::kSimpleTextureModulated:
    case ShadingType::kSimpleTextureModulatedColorized:
    case ShadingType::kSimpleTextureModulatedColorizedMasked:
    case ShadingType::kSimpleTexture:
    case ShadingType::kObject:
    case ShadingType::kObjectReflect:
    case ShadingType::kObjectLightShadow:
    case ShadingType::kObjectLightShadowFacingRatio:
    case ShadingType::kObjectReflectLightShadow:
    case ShadingType::kObjectReflectLightShadowDoubleSided:
    case ShadingType::kObjectReflectLightShadowColorized:
    case ShadingType::kObjectReflectLightShadowAdd:
    case ShadingType::kObjectReflectLightShadowAddColorized:
    case ShadingType::kPostProcess:
    case ShadingType::kPostProcessEyes:
    case ShadingType::kPostProcessNormalDistort:
      return false;
    default:
      throw Exception();  // in case we forget to add new ones here...
  }
}

Graphics::Graphics() : screenmessages{new ScreenMessages()} {}
Graphics::~Graphics() = default;

void Graphics::OnAppStart() {
  assert(g_base->InLogicThread());
  ReadVirtualBoundsABMode_();

  if (kDebugVirtualOuterRectToggleEnabled) {
    // Say so loudly; a build with this compiled in relayouts all UI
    // once per second, so a run with it on by accident should be
    // obvious.
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kWarning,
                         "USING VIRTUAL-OUTER-RECT DEBUG TOGGLE.");
  }
}

void Graphics::ReadVirtualBoundsABMode_() {
  assert(g_base->InLogicThread());

  auto envval = g_core->platform->GetEnv("BA_VIRTUAL_BOUNDS_AB");
  if (!envval.has_value()) {
    return;
  }
  const std::string& val = *envval;
  if (val == "a") {
    virtual_bounds_ab_mode_ = VirtualBoundsABMode::kA;
  } else if (val == "b") {
    virtual_bounds_ab_mode_ = VirtualBoundsABMode::kB;
  } else if (val == "toggle") {
    virtual_bounds_ab_mode_ = VirtualBoundsABMode::kToggle;
  } else {
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                         "Invalid BA_VIRTUAL_BOUNDS_AB value '" + val
                             + "'; expected a, b, or toggle.");
    return;
  }

  // Say so loudly; this deliberately mangles what gets drawn, so a run
  // that has it on by accident should be obvious.
  g_core->logging->Log(
      LogName::kBaGraphics, LogLevel::kWarning,
      "USING FORCED VIRTUAL-BOUNDS INSET (BA_VIRTUAL_BOUNDS_AB=" + val + ").");

  // Config choice feeds into rect calcs, so redo those.
  UpdateScreen_();
}

auto Graphics::CalcDebugVirtualBoundsRect_(const Rect& render_rect) -> Rect {
  // Note both A and B derive their bounds from this one call, so the two
  // configs cannot drift apart. In particular we inset the render rect
  // DIRECTLY here rather than shrinking the window and re-running
  // CalcActiveRenderRect - that would let the aspect clamp modify A's
  // rect but not B's bounds, and the resulting mismatch would look
  // exactly like a virtual-bounds bug while being the clamp correctly
  // doing its job.
  float w = render_rect.width();
  float h = render_rect.height();
  return Rect{render_rect.l + w * kDebugVirtualBoundsInsetL,
              render_rect.b + h * kDebugVirtualBoundsInsetB,
              render_rect.r - w * kDebugVirtualBoundsInsetR,
              render_rect.t - h * kDebugVirtualBoundsInsetT};
}

void Graphics::StepVirtualBoundsABToggle_() {
  assert(g_base->InLogicThread());

  if (virtual_bounds_ab_mode_ != VirtualBoundsABMode::kToggle) {
    return;
  }

  // Wall-clock rather than app time so the cadence stays a predictable
  // one second for whoever is watching the screen.
  auto now = core::Platform::TimeMonotonicMillisecs();
  if (now - virtual_bounds_ab_last_switch_time_ < kDebugVirtualBoundsABPeriod) {
    return;
  }
  virtual_bounds_ab_last_switch_time_ = now;
  virtual_bounds_ab_showing_b_ = !virtual_bounds_ab_showing_b_;
  UpdateScreen_();
}

void Graphics::OnAppSuspend() { assert(g_base->InLogicThread()); }

void Graphics::OnAppUnsuspend() { assert(g_base->InLogicThread()); }

void Graphics::OnAppShutdown() { assert(g_base->InLogicThread()); }

void Graphics::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }

void Graphics::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  // Any time we load the config we ship a new graphics-settings to the
  // graphics server since something likely changed.
  graphics_settings_dirty_ = true;

  show_fps_ = g_base->app_config->Resolve(AppConfig::BoolID::kShowFPS);
  show_ping_ = g_base->app_config->Resolve(AppConfig::BoolID::kShowPing);

  bool disable_camera_shake =
      g_base->app_config->Resolve(AppConfig::BoolID::kDisableCameraShake);
  set_camera_shake_disabled(disable_camera_shake);

  // Screen insets affect our virtual bounds and thus our virtual res;
  // recalc all that if they changed (and we know our res). Anything but
  // 'Custom' is automatic.
  bool screen_insets_custom =
      g_base->app_config->Resolve(AppConfig::StringID::kScreenInsets)
      == "Custom";
  float custom_screen_insets = std::clamp(
      g_base->app_config->Resolve(AppConfig::FloatID::kCustomScreenInsets),
      0.0f, 1.0f);
  // Likewise the aspect-ratio clamp, which shapes the active render
  // rect everything else derives from.
  bool allow_extreme_aspect_ratios =
      g_base->app_config->Resolve(AppConfig::BoolID::kAllowExtremeAspectRatios);
  if (screen_insets_custom != screen_insets_custom_
      || custom_screen_insets != custom_screen_insets_
      || allow_extreme_aspect_ratios != allow_extreme_aspect_ratios_) {
    screen_insets_custom_ = screen_insets_custom;
    custom_screen_insets_ = custom_screen_insets;
    allow_extreme_aspect_ratios_ = allow_extreme_aspect_ratios;
    if (got_screen_resolution_) {
      UpdateScreen_();
    }
  }

  // Note: the 'Disable Camera Gyro' setting is handled by the input
  // subsystem, which owns the device-motion -> tilt signal.

  applied_app_config_ = true;

  // At this point we may want to send initial graphics settings to the
  // graphics server if we haven't.
  UpdateInitialGraphicsSettingsSend_();
}

void Graphics::UpdateInitialGraphicsSettingsSend_() {
  assert(g_base->InLogicThread());
  if (sent_initial_graphics_settings_) {
    return;
  }

  // We need to send an initial graphics-settings to the server to kick
  // things off, but we need a few things to be in place first.
  auto app_config_ready = applied_app_config_;

  // At some point we may want to wait to know our actual screen res before
  // sending. This won't apply everywhere though since on some platforms the
  // screen doesn't exist until we send this.
  auto screen_resolution_ready = true;

  if (app_config_ready && screen_resolution_ready) {
    // Update/grab the current settings snapshot.
    auto* settings = GetGraphicsSettingsSnapshot();

    // We need to explicitly push settings to the graphics server to kick
    // things off. We need to keep this settings instance alive until
    // handled by the graphics context (which might be in another thread
    // where we're not allowed to muck with settings' refs from). So let's
    // explicitly increment its refcount here in the logic thread now and
    // then push a call back here to decrement it when we're done.
    settings->ObjectIncrementStrongRefCount();

    g_base->app_adapter->PushGraphicsContextCall([settings] {
      assert(g_base->app_adapter->InGraphicsContext());
      g_base->graphics_server->ApplySettings(settings->get());
      g_base->logic->event_loop()->PushCall([settings] {
        // Release our strong ref back here in the logic thread.
        assert(g_base->InLogicThread());
        settings->ObjectDecrementStrongRefCount();
      });
    });

    sent_initial_graphics_settings_ = true;
  }
}

void Graphics::StepDisplayTime() {
  assert(g_base->InLogicThread());
  StepVirtualBoundsABToggle_();
  StepVirtualOuterRectToggle_();
}

void Graphics::StepVirtualOuterRectToggle_() {
  assert(g_base->InLogicThread());

  if (!kDebugVirtualOuterRectToggleEnabled) {
    return;
  }

  // Wall-clock rather than app time so the cadence stays a predictable
  // one second for whoever is watching the screen (same as the A/B
  // toggle, whose period we share).
  auto now = core::Platform::TimeMonotonicMillisecs();
  if (now - virtual_outer_rect_toggle_last_switch_time_
      < kDebugVirtualBoundsABPeriod) {
    return;
  }
  virtual_outer_rect_toggle_last_switch_time_ = now;
  virtual_outer_rect_collapsed_ = !virtual_outer_rect_collapsed_;

  // Nothing about the real rects changes; this re-drive exists to fire
  // the screen-size-change chain so UI consumers re-query the reported
  // outer rect and reflow.
  UpdateScreen_();
}

void Graphics::AddCleanFrameCommand(const Object::Ref<PythonContextCall>& c) {
  assert(g_base->InLogicThread());
  clean_frame_commands_.push_back(c);
}

void Graphics::RunCleanFrameCommands() {
  assert(g_base->InLogicThread());
  for (auto&& i : clean_frame_commands_) {
    // Can't run immediately as we're in a frame-draw.
    i->Schedule();
  }
  clean_frame_commands_.clear();
}

auto Graphics::TextureQualityFromAppConfig() -> TextureQualityRequest {
  // Texture quality is no longer user-selectable; it only ever affected
  // legacy bare-filename textures and OS-rendered text (asset-package
  // textures pick their quality by flavor tier instead), so everyone
  // gets auto. Any stored 'Texture Quality' config value is ignored.
  return TextureQualityRequest::kAuto;
}

auto Graphics::VSyncFromAppConfig() -> VSyncRequest {
  std::string v_sync =
      g_base->app_config->Resolve(AppConfig::StringID::kVerticalSync);
  if (v_sync == "Auto") {
    return VSyncRequest::kAuto;
  } else if (v_sync == "Always") {
    return VSyncRequest::kAlways;
  } else if (v_sync == "Never") {
    return VSyncRequest::kNever;
  }
  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                       "Invalid 'Vertical Sync' value: '" + v_sync + "'");
  return VSyncRequest::kNever;
}

auto Graphics::GraphicsQualityFromAppConfig() -> GraphicsQualityRequest {
  std::string gqualstr =
      g_base->app_config->Resolve(AppConfig::StringID::kGraphicsQuality);
  GraphicsQualityRequest graphics_quality_requested;
  if (gqualstr == "Auto") {
    graphics_quality_requested = GraphicsQualityRequest::kAuto;
  } else if (gqualstr == "Higher") {
    graphics_quality_requested = GraphicsQualityRequest::kHigher;
  } else if (gqualstr == "High") {
    graphics_quality_requested = GraphicsQualityRequest::kHigh;
  } else if (gqualstr == "Medium") {
    graphics_quality_requested = GraphicsQualityRequest::kMedium;
  } else if (gqualstr == "Low") {
    graphics_quality_requested = GraphicsQualityRequest::kLow;
  } else {
    g_core->logging->Log(
        LogName::kBaGraphics, LogLevel::kError,
        "Invalid graphics quality: '" + gqualstr + "'; defaulting to auto.");
    graphics_quality_requested = GraphicsQualityRequest::kAuto;
  }
  return graphics_quality_requested;
}

void Graphics::UpdateProgressBarProgress(float target) {
  millisecs_t real_time = g_core->AppTimeMillisecs();
  float p = target;
  if (p < 0) {
    p = 0;
  }
  if (real_time - last_progress_bar_draw_time_ > 400) {
    last_progress_bar_draw_time_ = real_time - 400;
  }
  while (last_progress_bar_draw_time_ < real_time) {
    last_progress_bar_draw_time_++;
    progress_bar_progress_ += (p - progress_bar_progress_) * 0.02f;
  }
}

void Graphics::DrawProgressBar(RenderPass* pass, float opacity) {
  millisecs_t real_time = g_core->AppTimeMillisecs();
  float amount = progress_bar_progress_;
  if (amount < 0) {
    amount = 0;
  }

  SimpleComponent c(pass);
  c.SetTransparent(true);
  float o{opacity};
  float delay{};

  // Fade in for the first 2 seconds if desired.
  if (progress_bar_fade_in_) {
    auto since_start =
        static_cast<float>(real_time - last_progress_bar_start_time_);
    if (since_start < delay) {
      o = 0.0f;
    } else if (since_start < 2000.0f + delay) {
      o *= (since_start - delay) / 2000.0f;
    }
  }

  // Fade out towards the end.
  if (amount > 0.75f) {
    o *= (1.0f - amount) * 4.0f;
  }

  float b = pass->virtual_height() / 2.0f - 20.0f;
  float t = pass->virtual_height() / 2.0f + 20.0f;
  float l = 100.0f;
  float r = pass->virtual_width() - 100.0f;
  float p = 1.0f - amount;
  if (p < 0) {
    p = 0;
  } else if (p > 1.0f) {
    p = 1.0f;
  }
  p = l + (1.0f - p) * (r - l);

  progress_bar_bottom_mesh_->SetPositionAndSize(l, b, kProgressBarZDepth,
                                                (r - l), (t - b));
  progress_bar_top_mesh_->SetPositionAndSize(l, b, kProgressBarZDepth, (p - l),
                                             (t - b));

  c.SetColor(0.0f, 0.07f, 0.0f, 1 * o);
  c.DrawMesh(progress_bar_bottom_mesh_.get());
  c.Submit();

  c.SetColor(0.23f, 0.17f, 0.35f, 1 * o);
  c.DrawMesh(progress_bar_top_mesh_.get());
  c.Submit();
}

// Draw controls and things that lie on top of the action.
void Graphics::DrawMiscOverlays(FrameDef* frame_def) {
  RenderPass* pass = frame_def->overlay_pass();
  assert(g_base && g_base->InLogicThread());

  // Every now and then, update our stats.
  while (g_core->AppTimeMillisecs() >= next_stat_update_time_) {
    if (g_core->AppTimeMillisecs() - next_stat_update_time_ > 1000) {
      next_stat_update_time_ = g_core->AppTimeMillisecs() + 1000;
    } else {
      next_stat_update_time_ += 1000;
    }
    int total_frames_rendered =
        g_base->graphics_server->renderer()->total_frames_rendered();
    last_fps_ = total_frames_rendered - last_total_frames_rendered_;
    last_total_frames_rendered_ = total_frames_rendered;
  }

  float bot_left_offset{};
  if (show_fps_ || show_ping_) {
    bot_left_offset = g_base->app_mode()->GetBottomLeftEdgeHeight();
  }
  if (show_fps_) {
    char fps_str[32];
    snprintf(fps_str, sizeof(fps_str), "%d", last_fps_);
    if (fps_str != fps_string_) {
      fps_string_ = fps_str;
      if (!fps_text_group_.exists()) {
        fps_text_group_ = Object::New<TextGroup>();
      }
      fps_text_group_->SetText(fps_string_);
    }
    SimpleComponent c(pass);
    c.SetTransparent(true);
    if (g_core->vr_mode()) {
      c.SetColor(1, 1, 1, 1);
    } else {
      c.SetColor(0.8f, 0.8f, 0.8f, 1.0f);
    }
    int text_elem_count = fps_text_group_->GetElementCount();
    for (int e = 0; e < text_elem_count; e++) {
      c.SetTexture(fps_text_group_->GetElementTexture(e));
      if (g_core->vr_mode()) {
        c.SetShadow(-0.003f * fps_text_group_->GetElementUScale(e),
                    -0.003f * fps_text_group_->GetElementVScale(e), 0.0f, 1.0f);
        c.SetMaskUV2Texture(fps_text_group_->GetElementMaskUV2Texture(e));
      }
      c.SetFlatness(1.0f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(6.0f, bot_left_offset + 6.0f, kScreenTextZDepth);
        c.DrawMesh(fps_text_group_->GetElementMesh(e));
      }
    }
    c.Submit();
  }

  if (show_ping_) {
    auto ping = g_base->app_mode()->GetDisplayPing();
    if (ping.has_value()) {
      char ping_str[32];
      snprintf(ping_str, sizeof(ping_str), "%.0f ms", *ping);
      if (ping_str != ping_string_) {
        ping_string_ = ping_str;
        if (!ping_text_group_.exists()) {
          ping_text_group_ = Object::New<TextGroup>();
        }
        ping_text_group_->SetText(ping_string_);
      }
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(0.5f, 0.9f, 0.5f, 1.0f);
      if (*ping > 100.0f) {
        c.SetColor(0.8f, 0.8f, 0.0f, 1.0f);
      }
      if (*ping > 500.0f) {
        c.SetColor(0.9f, 0.2f, 0.2f, 1.0f);
      }

      int text_elem_count = ping_text_group_->GetElementCount();
      for (int e = 0; e < text_elem_count; e++) {
        c.SetTexture(ping_text_group_->GetElementTexture(e));
        c.SetFlatness(1.0f);
        {
          auto xf = c.ScopedTransform();
          c.Translate(
              6.0f, bot_left_offset + 6.0f + 1.0f + (show_fps_ ? 30.0f : 0.0f),
              kScreenTextZDepth);
          c.Scale(0.7f, 0.7f);
          c.DrawMesh(ping_text_group_->GetElementMesh(e));
        }
      }
      c.Submit();
    }
  }

  if (show_net_info_) {
    auto net_info_str{g_base->app_mode()->GetNetworkDebugString()};
    if (!net_info_str.empty()) {
      if (net_info_str != net_info_string_) {
        net_info_string_ = net_info_str;
        if (!net_info_text_group_.exists()) {
          net_info_text_group_ = Object::New<TextGroup>();
        }
        net_info_text_group_->SetText(net_info_string_);
      }
      SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(0.8f, 0.8f, 0.8f, 1.0f);
      int text_elem_count = net_info_text_group_->GetElementCount();
      for (int e = 0; e < text_elem_count; e++) {
        c.SetTexture(net_info_text_group_->GetElementTexture(e));
        c.SetFlatness(1.0f);
        {
          auto xf = c.ScopedTransform();
          c.Translate(4.0f, (show_fps_ ? 66.0f : 40.0f), kScreenTextZDepth);
          c.Scale(0.7f, 0.7f);
          c.DrawMesh(net_info_text_group_->GetElementMesh(e));
        }
      }
      c.Submit();
    }
  }

  // Draw any debug graphs.
  {
    float debug_graph_y = 50.0;
    auto now = g_core->AppTimeMillisecs();
    for (auto it = debug_graphs_.begin(); it != debug_graphs_.end();) {
      assert(it->second.exists());
      if (now - it->second->LastUsedTime() > 1000) {
        it = debug_graphs_.erase(it);
      } else {
        it->second->Draw(pass, g_base->logic->display_time() * 1000.0, 50.0f,
                         debug_graph_y, 500.0f, 100.0f);
        debug_graph_y += 110.0f;

        ++it;
      }
    }
  }
}

auto Graphics::GetDebugGraph(const std::string& name, bool smoothed)
    -> NetGraph* {
  auto out = debug_graphs_.find(name);
  if (out == debug_graphs_.end()) {
    debug_graphs_[name] = Object::New<NetGraph>();
    debug_graphs_[name]->SetLabel(name);
    debug_graphs_[name]->SetSmoothed(smoothed);
  }
  debug_graphs_[name]->SetLastUsedTime(g_core->AppTimeMillisecs());
  return debug_graphs_[name].get();
}

void Graphics::GetSafeColor(float* red, float* green, float* blue,
                            float target_intensity) {
  assert(red && green && blue);

  // Mult our color up to try and hit the target intensity.
  float intensity = 0.2989f * (*red) + 0.5870f * (*green) + 0.1140f * (*blue);
  if (intensity < target_intensity) {
    float s = target_intensity / std::max(0.001f, intensity);
    *red = std::min(1.0f, (*red) * s);
    *green = std::min(1.0f, (*green) * s);
    *blue = std::min(1.0f, (*blue) * s);
  }

  // We may still be short of our target intensity due to clamping (ie:
  // (10,0,0) will not look any brighter than (1,0,0)) if that's the case,
  // just convert the difference to a grey value and add that to all
  // channels... this *still* might not get us there so lets do it a few times
  // if need be.  (i'm sure there's a less bone-headed way to do this)
  for (int i = 0; i < 4; i++) {
    float remaining =
        (0.2989f * (*red) + 0.5870f * (*green) + 0.1140f * (*blue)) - 1.0f;
    if (remaining > 0.0f) {
      *red = std::min(1.0f, (*red) + 0.2989f * remaining);
      *green = std::min(1.0f, (*green) + 0.5870f * remaining);
      *blue = std::min(1.0f, (*blue) + 0.1140f * remaining);
    } else {
      break;
    }
  }
}

void Graphics::BrightenColor(float* rgb, float brightness) {
  assert(rgb);
  float b = std::max(0.0f, brightness);
  float m{};
  for (int i = 0; i < 3; ++i) {
    rgb[i] = std::max(0.0f, rgb[i]) * b;
    m = std::max(m, rgb[i]);
  }
  if (m <= 1.0f) {
    return;
  }
  // Past the knee: hue at full intensity, whitened by the overshoot.
  float whiten = 1.0f - 1.0f / m;
  for (int i = 0; i < 3; ++i) {
    float c = rgb[i] / m;
    rgb[i] = c + (1.0f - c) * whiten;
  }
}

auto Graphics::TeamColoringStrength() -> float {
  // The standard strength (Eric, 2026-10-07). Definitions can set
  // their own per color; see CharacterTintDef and CapsuleNameDef.
  const float kStandard{0.5f};

  // Tuning aid: BA_TEAM_COLORING_STRENGTH overrides it, re-read a few
  // times a second so it can be changed in a running game.
  static millisecs_t last_check{-1000};
  static float current{kStandard};
  millisecs_t now = g_core->AppTimeMillisecs();
  if (now - last_check >= 250) {
    last_check = now;
    current = kStandard;
    if (const char* val = getenv("BA_TEAM_COLORING_STRENGTH")) {
      if (val[0] != 0) {
        current = std::clamp(static_cast<float>(atof(val)), 0.0f, 1.0f);
      }
    }
  }
  return current;
}

void Graphics::ToneForTeamColor(const float* main_rgb, float* rgb,
                                float strength) {
  assert(main_rgb && rgb);
  float t = std::clamp(strength, 0.0f, 1.0f);
  float main_max{};
  float v{};
  for (int i = 0; i < 3; ++i) {
    main_max = std::max(main_max, main_rgb[i]);
    v = std::max(v, rgb[i]);
  }
  if (t <= 0.0f || main_max <= 0.0f || v <= 0.0f) {
    return;
  }
  // Blend toward main's own tint at this color's brightness, then put
  // the brightness (its brightest channel) back where it was: only
  // hue and saturation move.
  float blended_max{};
  for (int i = 0; i < 3; ++i) {
    float target = std::max(0.0f, main_rgb[i]) / main_max * v;
    rgb[i] = std::max(0.0f, rgb[i]) + (target - std::max(0.0f, rgb[i])) * t;
    blended_max = std::max(blended_max, rgb[i]);
  }
  if (blended_max > 0.0f) {
    for (int i = 0; i < 3; ++i) {
      rgb[i] *= v / blended_max;
    }
  }
}

void Graphics::Reset() {
  assert(g_base->InLogicThread());
  fade_ = 0;
  fade_start_ = fade_cancel_start_ = fade_time_ = 0;

  if (!camera_.exists()) {
    camera_ = Object::New<GameCamera>();
  }
  if (!main_view_.exists()) {
    main_view_ = Object::New<RenderView>(camera_.get());
  }

  screenmessages->Reset();
}

void Graphics::InitInternalComponents(FrameDef* frame_def) {
  RenderPass* pass = frame_def->GetOverlayFlatPass();

  screen_mesh_ = Object::New<ImageMesh>();

  float w = pass->virtual_width();
  float h = pass->virtual_height();
  if (g_core->vr_mode()) {
    // Draw a bit bigger than the virtual screen to cover the vr border.
    screen_mesh_->SetPositionAndSize(
        -(0.5f * kVRBorder) * w, (-0.5f * kVRBorder) * h, kScreenMeshZDepth,
        (1.0f + kVRBorder) * w, (1.0f + kVRBorder) * h);
  } else {
    // Cover everything we physically draw into, which is the active
    // render rect - the virtual screen alone is not enough once the
    // virtual bounds are inset (anything outside the render rect is
    // black borders drawn by the renderer, but the bounds margins
    // inside it are real content that fades/blotches must cover too).
    // Identical to the plain virtual screen when bounds aren't inset.
    const Rect& vout = virtual_outer_rect_;
    screen_mesh_->SetPositionAndSize(vout.l, vout.b, kScreenMeshZDepth,
                                     vout.width(), vout.height());
  }
  progress_bar_top_mesh_ = Object::New<ImageMesh>();
  progress_bar_bottom_mesh_ = Object::New<ImageMesh>();
  load_dot_mesh_ = Object::New<ImageMesh>();
  load_dot_mesh_->SetPositionAndSize(0, 0, 0, 2, 2);
}

auto Graphics::GetEmptyFrameDef() -> FrameDef* {
  assert(g_base->InLogicThread());
  FrameDef* frame_def;

  // Grab a ready-to-use recycled one if available.
  if (!recycle_frame_defs_.empty()) {
    frame_def = recycle_frame_defs_.back();
    recycle_frame_defs_.pop_back();
  } else {
    frame_def = new FrameDef();
  }
  frame_def->Reset();
  return frame_def;
}

auto Graphics::GetGraphicsSettingsSnapshot() -> Snapshot<GraphicsSettings>* {
  assert(g_base->InLogicThread());

  // If need be, ask the app-adapter to build us a new settings instance.
  if (graphics_settings_dirty_) {
    auto* new_settings = g_base->app_adapter->GetGraphicsSettings();
    new_settings->index = next_settings_index_++;
    settings_snapshot_ = Object::New<Snapshot<GraphicsSettings>>(new_settings);
    graphics_settings_dirty_ = false;

    // This can affect placeholder settings; keep those up to date.
    UpdatePlaceholderSettings();
  }
  assert(settings_snapshot_.exists());
  return settings_snapshot_.get();
}

void Graphics::ClearFrameDefDeleteList() {
  assert(g_base->InLogicThread());
  std::scoped_lock lock(frame_def_delete_list_mutex_);

  for (auto& i : frame_def_delete_list_) {
    // We recycle our frame_defs so we don't have to reallocate all those
    // buffers.
    if (recycle_frame_defs_.size() < 5) {
      recycle_frame_defs_.push_back(i);
    } else {
      delete i;
    }
  }
  frame_def_delete_list_.clear();
}

void Graphics::FadeScreen(bool to, millisecs_t time, PyObject* endcall) {
  assert(g_base->InLogicThread());
  // If there's an ourstanding fade-end command, go ahead and run it
  // (otherwise, overlapping fades can cause things to get lost).
  if (fade_end_call_.exists()) {
    if (g_buildconfig.debug_build()) {
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kWarning,
          "2 fades overlapping; running first fade-end-call early.");
    }
    fade_end_call_->Schedule();
    fade_end_call_.Clear();
  }
  set_fade_start_on_next_draw_ = true;
  fade_time_ = time;
  fade_out_ = !to;
  if (endcall) {
    fade_end_call_ = Object::New<PythonContextCall>(endcall);
  }
  fade_ = 1.0f;
}

void Graphics::DrawLoadDot(RenderPass* pass) {
  // Draw a little bugger in the corner if we're loading something.
  SimpleComponent c(pass);
  c.SetTransparent(true);

  // Draw red if we've got graphics stuff loading. Green if only other stuff
  // left.
  if (g_base->assets->GetGraphicalPendingLoadCount() > 0) {
    c.SetColor(0.2f, 0, 0, 1);
  } else {
    c.SetColor(0, 0.2f, 0, 1);
  }
  c.DrawMesh(load_dot_mesh_.get());
  c.Submit();
}

void Graphics::ApplyCamera(FrameDef* frame_def) {
  Camera* camera = main_view_->camera();
  camera->Update(frame_def->display_time_elapsed_millisecs());
  camera->UpdatePosition();
  camera->ApplyToFrameDef(frame_def);
}

void Graphics::DrawWorld(FrameDef* frame_def) {
  assert(!g_core->HeadlessMode());

  // Draw the world. Nodes that show bg-dynamics results (character
  // limbs, attachments) read them while drawing, so pull the latest in
  // first, waiting briefly for a step still in flight.
  overlay_node_z_depth_ = -0.95f;
  BGDynamicsWorld* bg_world = g_base->bg_dynamics->main_world();
  bg_world->AdoptResults(true);
  g_base->app_mode()->DrawWorld(frame_def);
  bg_world->Draw(frame_def);

  // Lastly draw any blotches that have been building up.
  main_view_->DrawBlotches(frame_def);

  // Add a few explicit things to a few passes.
  DrawBoxingGlovesTest(frame_def);
}

void Graphics::DrawUI(FrameDef* frame_def) {
  // Just do generic thing in our default implementation.
  // Special variants like GraphicsVR may do fancier stuff here.
  g_base->ui->Draw(frame_def);

  // We may want to see the virtual bounds our coord system covers,
  // and/or the safe area within it. Bounds first, and set behind in z
  // below, so the safe-area guide reads on top wherever the two touch
  // (it is the tighter constraint, so it is the one worth seeing).
  DrawVirtualBounds(frame_def->overlay_pass());
  DrawVirtualSafeAreaBounds(frame_def->overlay_pass());
}

void Graphics::DrawDevUI(FrameDef* frame_def) {
  // Just do generic thing in our default implementation.
  // Special variants like GraphicsVR may do fancier stuff here.
  g_base->ui->DrawDev(frame_def);
}

void Graphics::BuildAndPushFrameDef() {
  assert(g_base->InLogicThread());

  assert(g_base->logic->app_bootstrapping_complete());
  assert(camera_.exists());
  assert(!g_core->HeadlessMode());

  // Keep track of when we're in here; can be useful for making sure stuff
  // doesn't muck with our lists/etc. while we're using them.
  assert(!building_frame_def_);
  building_frame_def_ = true;

  microsecs_t app_time_microsecs = g_core->AppTimeMicrosecs();

  // Under BA_RENDER_PROFILE (test_game_run --render-profile) we time
  // how long frame-defs take to build. We count this thread's cpu time
  // rather than wall time so that waiting on bg-dynamics results
  // doesn't count.
  if (!render_profile_checked_) {
    render_profile_checked_ = true;
    render_profile_ = (getenv("BA_RENDER_PROFILE") != nullptr);
  }
  auto profile_now = [this] {
    return render_profile_ ? ThreadCPUTimeMillisecs() : 0.0;
  };
  double profile_start = profile_now();
  double profile_world_ms{};
  double profile_ui_ms{};

  // Store how much time this frame_def represents.
  auto display_time_microsecs = g_base->logic->display_time_microsecs();
  auto display_time_millisecs = display_time_microsecs / 1000;

  // Clamp a frame-def's elapsed time to 1/10th of a second even if it has
  // been longer than that since the last. Don't want things like
  // motion-blur to get out of control.
  microsecs_t elapsed_microsecs =
      std::min(microsecs_t{100000},
               display_time_microsecs - last_create_frame_def_time_microsecs_);
  last_create_frame_def_time_microsecs_ = display_time_microsecs;

  // We need to do a separate elapsed calculation for milliseconds. It would
  // seem that we could just calc this based on our elapsed microseconds,
  // but the problem is that at very high frame rates we wind up always
  // rounding down to 0.
  millisecs_t elapsed_millisecs =
      std::min(millisecs_t{100},
               display_time_millisecs - last_create_frame_def_time_millisecs_);
  last_create_frame_def_time_millisecs_ = display_time_millisecs;

  frame_def_count_++;

  // Update our filtered frame-number (clamped at 60hz so it can be used
  // for drawing without looking wonky at high frame rates).
  if (display_time_microsecs >= next_frame_number_filtered_increment_time_) {
    frame_def_count_filtered_ += 1;
    // Schedule the next increment for 1/60th of a second after the last (or
    // now, whichever is later).
    next_frame_number_filtered_increment_time_ =
        std::max(display_time_microsecs,
                 next_frame_number_filtered_increment_time_ + 1000000 / 60);
  }

  // The device-motion -> tilt signal lives in the input subsystem, but we
  // drive its per-frame integration from here so it uses the freshest gyro
  // sample possible right before we build this frame's draw commands (which
  // sample input->tilt() for camera/UI parallax).
  g_base->input->UpdateGyro(app_time_microsecs, elapsed_microsecs);

  FrameDef* frame_def = GetEmptyFrameDef();
  frame_def->set_app_time_microsecs(app_time_microsecs);
  frame_def->set_display_time_microsecs(
      g_base->logic->display_time_microsecs());
  frame_def->set_display_time_elapsed_microsecs(elapsed_microsecs);
  frame_def->set_display_time_elapsed_millisecs(elapsed_millisecs);
  frame_def->set_frame_number(frame_def_count_);
  frame_def->set_frame_number_filtered(frame_def_count_filtered_);

  if (!internal_components_inited_) {
    InitInternalComponents(frame_def);
    internal_components_inited_ = true;
  }

  ApplyCamera(frame_def);

  if (progress_bar_) {
    frame_def->set_needs_clear(true);
    UpdateAndDrawOnlyProgressBar(frame_def);
  } else {
    // Ok, we're drawing a real frame.

    // When the UI fully covers the screen opaquely (common in menus at
    // small ui-scale) we can skip drawing the world/scene entirely.
    // Important to sample this once, strictly before any drawing.
    bool ui_covers_screen = g_base->ui->UICoversScreenOpaquely();
    if (ui_covers_screen != ui_covered_screen_last_frame_) {
      ui_covered_screen_last_frame_ = ui_covers_screen;
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kDebug,
          ui_covers_screen
              ? "UI now covers screen opaquely; skipping world draws."
              : "UI no longer covers screen opaquely; resuming world draws.");
    }

    if (ui_covers_screen) {
      // The UI should cover any stale/undefined buffer contents behind
      // it, but clear anyway: it's near-free on mobile tilers, and if
      // our coverage calc is ever wrong it keeps the resulting artifact
      // an obvious solid color rather than confusing garbage.
      frame_def->set_needs_clear(true);
    } else {
      frame_def->set_needs_clear(!g_base->app_mode()->DoesWorldFillScreen());
      double world_start = profile_now();
      DrawWorld(frame_def);
      profile_world_ms = profile_now() - world_start;
    }

    double ui_start = profile_now();
    DrawUI(frame_def);
    profile_ui_ms = profile_now() - ui_start;

    // Let input draw anything it needs to (touch input graphics, etc).
    g_base->input->Draw(frame_def);

    RenderPass* overlay_pass = frame_def->overlay_pass();
    DrawMiscOverlays(frame_def);

    // SimpleDialogs (asset-resolve progress, dead-in-the-water errors, etc.):
    // over all game/UI but under the dev console (which DrawDevUI submits next,
    // at a depth just above ours).
    g_base->ui->DrawSimpleDialogs(frame_def);

    // Let UI draw dev console and whatever else.
    DrawDevUI(frame_def);

    // Screen-messages: submitted after simple-dialogs and the dev console
    // (and at a depth in front of both) so they stay visible over them;
    // fades and the cursor, submitted later at higher depths, still draw
    // over us.
    screenmessages->Draw(frame_def);

    // Draw our light/shadow images to the screen if desired.
    DrawDebugBuffers(overlay_pass);

    // Show our test view if asked to (test_game_run
    // --debug-texture-view).
    if (!debug_texture_view_checked_) {
      debug_texture_view_checked_ = true;
      if (getenv("BA_DEBUG_TEXTURE_VIEW") != nullptr) {
        debug_texture_view_ = Object::New<DebugTextureView>();
      }
    }
    if (debug_texture_view_.exists()) {
      debug_texture_view_->DrawToOverlay(overlay_pass);
    }

    // In high-quality modes we draw a screen-quad as a catch-all for
    // blitting the world buffer to the screen (other nodes can add their
    // own blitters such as distortion shapes which will have priority).
    if (frame_def->quality() >= GraphicsQuality::kHigh) {
      PostProcessComponent c(frame_def->blit_pass());
      c.DrawScreenQuad();
      c.Submit();
    }

    DrawFades(frame_def);
    DrawCursor(frame_def);

    // Sanity test: If we're in VR, the only reason we should have stuff in
    // the flat overlay pass is if there's windows present (we want to avoid
    // drawing/blitting the 2d UI buffer during gameplay for efficiency).
    if (g_core->vr_mode()) {
      if (frame_def->GetOverlayFlatPass()->HasDrawCommands()) {
        if (!g_base->ui->IsMainUIVisible()) {
          BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                      "Drawing in overlay pass in VR mode with no UI present; "
                      "shouldn't happen!");
        }
      }
    }

    if (g_base->assets->GetPendingLoadCount() > 0) {
      DrawLoadDot(overlay_pass);
    }

    // Lastly, if we had anything waiting to run until the progress bar was
    // gone, run it.
    RunCleanFrameCommands();
  }

  // All possible text-editing reporters have drawn by this point (or none
  // did, e.g. progress-bar-only frames); reconcile against last frame and
  // inform the app-adapter of any text-editing begin/end/moves.
  g_base->ui->ProcessTextEditReports(frame_def);

  // Everything headed for the screen has been drawn, so we know which
  // views had their textures drawn; draw those views' worlds.
  DrawTextureViews_(frame_def);

  frame_def->Complete();

  frame_def->set_view_destroys(render_view_destroys_);
  render_view_destroys_.clear();

  // Include all mesh-data loads and unloads that have accumulated up to
  // this point the graphics thread will have to handle these before
  // rendering the frame_def.
  frame_def->set_mesh_data_creates(mesh_data_creates_);
  mesh_data_creates_.clear();
  frame_def->set_mesh_data_destroys(mesh_data_destroys_);
  mesh_data_destroys_.clear();

  if (render_profile_) {
    UpdateRenderProfile_(profile_now() - profile_start, profile_world_ms,
                         profile_ui_ms);
  }

  g_base->graphics_server->EnqueueFrameDef(frame_def);

  // Clean up frame_defs awaiting deletion.
  ClearFrameDefDeleteList();

  // Clear our blotches out regardless of whether we rendered them.
  main_view_->ClearBlotches();

  assert(building_frame_def_);
  building_frame_def_ = false;
}

void Graphics::AddRenderViewDestroy(int view_id) {
  assert(g_base->InLogicThread());

  // These go out with frame-defs, which headless never builds (nor
  // does it have a renderer to tell).
  if (g_core->HeadlessMode()) {
    return;
  }
  render_view_destroys_.push_back(view_id);
}

void Graphics::DrawTextureViews_(FrameDef* frame_def) {
  // Note: we go by index since drawing a view's world can in theory
  // draw another view's texture, adding to the list as we go.
  for (size_t i = 0; i < frame_def->wanted_views().size(); i++) {
    RenderView* view = frame_def->wanted_views()[i].get();
    FrameDefView* fview = frame_def->AddTextureView(view);
    frame_def->set_current_view(fview);

    Camera* camera = view->camera();
    camera->Update(frame_def->display_time_elapsed_millisecs());
    camera->UpdatePosition();
    camera->ApplyToFrameDef(frame_def);

    view->set_last_drawn_frame_number(frame_def->frame_number());
    view->DrawWorld(frame_def);
    view->DrawBlotches(frame_def);
    view->ClearBlotches();

    // As with the main view: in high-quality modes the world is drawn
    // to a buffer first, and this is the catch-all that gets it from
    // there to where it is headed (anything in the world with a
    // blitter of its own has been in ahead of us).
    if (frame_def->quality() >= GraphicsQuality::kHigh) {
      PostProcessComponent c(frame_def->blit_pass());
      c.DrawScreenQuad();
      c.Submit();
    }

    frame_def->set_current_view(frame_def->main_view());
  }
}

void Graphics::UpdateRenderProfile_(double build_ms, double world_ms,
                                    double ui_ms) {
  render_profile_frames_++;
  render_profile_build_ms_ += build_ms;
  render_profile_world_ms_ += world_ms;
  render_profile_ui_ms_ += ui_ms;
  seconds_t now = g_core->AppTimeSeconds();
  if (render_profile_window_start_ == 0.0) {
    render_profile_window_start_ = now;
  }
  if (now - render_profile_window_start_ < 5.0) {
    return;
  }
  double frames = render_profile_frames_;
  char buffer[256];
  snprintf(buffer, sizeof(buffer),
           "render profile (logic): %d frame-defs built; cpu per"
           " frame-def: build %.0fus (world %.0fus, ui %.0fus)",
           render_profile_frames_, 1000.0 * render_profile_build_ms_ / frames,
           1000.0 * render_profile_world_ms_ / frames,
           1000.0 * render_profile_ui_ms_ / frames);
  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kInfo, buffer);
  render_profile_frames_ = 0;
  render_profile_build_ms_ = 0.0;
  render_profile_world_ms_ = 0.0;
  render_profile_ui_ms_ = 0.0;
  render_profile_window_start_ = now;
}

void Graphics::DrawBoxingGlovesTest(FrameDef* frame_def) {
  // Test: boxing glove.
  if (explicit_bool(false)) {
    float a = 0;

    // Blit.
    if (explicit_bool(true)) {
      PostProcessComponent c(frame_def->blit_pass());
      c.SetNormalDistort(0.07f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(0, 7, -3.3f);
        c.Scale(10, 10, 10);
        c.Rotate(a, 0, 0, 1);
        c.DrawMeshAsset(g_base->assets->base_assets().boxing_glove.get());
      }
      c.Submit();
    }

    // Beauty.
    if (explicit_bool(false)) {
      ObjectComponent c(frame_def->beauty_pass());
      c.SetTexture(g_base->assets->base_assets().boxing_gloves_color.get());
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.4f, 0.4f, 0.4f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(0.0f, 3.7f, -3.3f);
        c.Scale(10.0f, 10.0f, 10.0f);
        c.Rotate(a, 0.0f, 0.0f, 1.0f);
        c.DrawMeshAsset(g_base->assets->base_assets().boxing_glove.get());
      }
      c.Submit();
    }

    // Light.
    if (explicit_bool(true)) {
      SimpleComponent c(frame_def->light_shadow_pass());
      c.SetColor(0.16f, 0.11f, 0.1f, 1.0f);
      c.SetTransparent(true);
      {
        auto xf = c.ScopedTransform();
        c.Translate(0.0f, 3.7f, -3.3f);
        c.Scale(10.0f, 10.0f, 10.0f);
        c.Rotate(a, 0.0f, 0.0f, 1.0f);
        c.DrawMeshAsset(g_base->assets->base_assets().boxing_glove.get());
      }
      c.Submit();
    }
  }
}

void Graphics::DrawDebugBuffers(RenderPass* pass) {
  if (explicit_bool(false)) {
    {
      SpecialComponent c(pass, SpecialComponent::Source::kLightBuffer);
      float csize = 100;
      {
        auto xf = c.ScopedTransform();
        c.Translate(70, 400, kDebugImgZDepth);
        c.Scale(csize, csize);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
      }
      c.Submit();
    }
    {
      SpecialComponent c(pass, SpecialComponent::Source::kLightShadowBuffer);
      float csize = 100;
      {
        auto xf = c.ScopedTransform();
        c.Translate(70, 250, kDebugImgZDepth);
        c.Scale(csize, csize);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
      }
      c.Submit();
    }
  }
}

void Graphics::UpdateAndDrawOnlyProgressBar(FrameDef* frame_def) {
  RenderPass* pass = frame_def->overlay_pass();
  UpdateProgressBarProgress(
      1.0f
      - static_cast<float>(g_base->assets->GetGraphicalPendingLoadCount())
            / static_cast<float>(progress_bar_loads_));
  DrawProgressBar(pass, 1.0f);

  // If we were drawing a progress bar, see if everything is now loaded. If
  // so, start rendering normally next frame.
  int count = g_base->assets->GetGraphicalPendingLoadCount();
  if (count <= 0) {
    progress_bar_ = false;
    progress_bar_end_time_ = frame_def->app_time_millisecs();
  }
  if (g_base->assets->GetPendingLoadCount() > 0) {
    DrawLoadDot(pass);
  }
}

void Graphics::DrawFades(FrameDef* frame_def) {
  RenderPass* overlay_pass = frame_def->overlay_pass();

  millisecs_t frame_time = frame_def->display_time_millisecs();

  // We want to guard against accidental fades that never fade back in. To
  // do that, let's measure the total time we've been faded and cancel if it
  // gets too big. However, we reset this counter any time we're inactive or
  // whenever substantial clock time passes between drawing - there are
  // cases where we fade out and then show an ad or other screen before
  // becoming active again and fading back in, and we want to allow for such
  // cases.
  if (fade_ <= 0.0f && fade_out_) {
    millisecs_t cancel_time = frame_time - fade_cancel_start_;

    // Reset if a substantial amount of real time passes between frame draws.
    auto real_ms = core::Platform::TimeMonotonicMillisecs();
    if (real_ms - fade_cancel_last_real_ms_ > 1000) {
      fade_cancel_start_ = frame_time;
    }
    fade_cancel_last_real_ms_ = real_ms;

    // Also reset any time we're inactive (we may still be technically
    // drawing behind some foreground thing).
    if (!g_base->app_active()) {
      fade_cancel_start_ = frame_time;
    }

    // g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
    //                      "DOING FADE " + std::to_string(cancel_time));

    if (cancel_time > 15000) {
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                           "FORCE-ENDING STUCK FADE");
      fade_out_ = false;
      fade_ = 1.0f;
      fade_time_ = 1000;
      fade_start_ = frame_time;
    }
  }

  // Update fade values.
  if (fade_ > 0) {
    if (set_fade_start_on_next_draw_) {
      set_fade_start_on_next_draw_ = false;
      fade_start_ = frame_time;
      // Calc when we should start counting for force-ending.
      fade_cancel_start_ = fade_start_ + fade_time_;
      fade_cancel_last_real_ms_ = core::Platform::TimeMonotonicMillisecs();
    }
    bool was_done = fade_ <= 0;
    if (frame_time <= fade_start_) {
      fade_ = 1;
    } else if ((frame_time - fade_start_) < fade_time_) {
      fade_ = 1.0f
              - (static_cast<float>(frame_time - fade_start_)
                 / static_cast<float>(fade_time_));
      if (fade_ <= 0) {
        fade_ = 0.00001f;
      }
    } else {
      fade_ = 0;
      if (!was_done && fade_end_call_.exists()) {
        fade_end_call_->Schedule();
        fade_end_call_.Clear();
      }
    }
  }

  // Draw a fade if we're either in a fade or fading back in from a
  // progress-bar screen.
  if (fade_ > 0.00001f || fade_out_
      || (frame_time - progress_bar_end_time_ < kProgressBarFadeTime)) {
    float a = fade_out_ ? 1 - fade_ : fade_;
    if (frame_time - progress_bar_end_time_ < kProgressBarFadeTime) {
      a = 1.0f * a
          + (1.0f
             - static_cast<float>(frame_time - progress_bar_end_time_)
                   / static_cast<float>(kProgressBarFadeTime))
                * (1.0f - a);
    }

    DoDrawFade(frame_def, a);

    // If we're doing a progress-bar fade, throw in the fading progress bar.
    if (frame_time - progress_bar_end_time_ < kProgressBarFadeTime * 0.5) {
      //      float o = std::min(
      //          1.0f, (1.0f
      //                 - static_cast<float>(frame_time -
      //                 progress_bar_end_time_)
      //                       / (static_cast<float>(kProgressBarFadeTime) *
      //                       0.5f)));
      UpdateProgressBarProgress(1.0f);
      DrawProgressBar(overlay_pass, 1.0);
    }
  }
}

void Graphics::DoDrawFade(FrameDef* frame_def, float amt) {
  SimpleComponent c(frame_def->overlay_front_pass());
  c.SetTransparent(amt < 1.0f);
  c.SetColor(0, 0, 0, amt);
  {
    // Draw this at the front of this overlay pass; should never really
    // need stuff covering this methinks.
    auto xf = c.ScopedTransform();
    c.Translate(0.0f, 0.0f, 1.0f);
    c.DrawMesh(screen_mesh_.get());
  }
  c.Submit();
}

void Graphics::DrawCursor(FrameDef* frame_def) {
  assert(g_base->InLogicThread());

  auto app_time = frame_def->app_time();

  auto can_show_cursor = g_base->app_adapter->ShouldUseCursor();
  auto should_show_cursor =
      camera_->manual() || g_base->input->IsCursorVisible();

  if (g_base->app_adapter->HasHardwareCursor()) {
    // If we're using a hardware cursor, ship hardware cursor visibility
    // updates to the app thread periodically.
    bool new_cursor_visibility = false;
    if (can_show_cursor && should_show_cursor) {
      new_cursor_visibility = true;
    }

    // As of macOS 15.6.1 there seems to be a bug where moving the cursor down
    // from the top portion of a fullscreen window flips it back to the arrow
    // cursor. Should submit a bug to Apple if this is still the case in macOS
    // 16, but for now am just forcing cursor resets at a higher frequency there
    // to hide that.
    seconds_t fudge_secs =
        (g_buildconfig.platform_macos() && g_buildconfig.xcode_build()) ? 0.235
                                                                        : 2.345;

    // Ship this state when it changes and also every now and then just in
    // case things go wonky.
    if (new_cursor_visibility != hardware_cursor_visible_
        || app_time - last_cursor_visibility_event_time_ > fudge_secs) {
      hardware_cursor_visible_ = new_cursor_visibility;
      last_cursor_visibility_event_time_ = app_time;
      g_base->app_adapter->PushMainThreadCall([this] {
        assert(g_core && g_core->InMainThread());
        g_base->app_adapter->SetHardwareCursorVisible(hardware_cursor_visible_);
      });
    }
  } else {
    // Draw software cursor.
    if (can_show_cursor && should_show_cursor) {
      SimpleComponent c(frame_def->overlay_front_pass());
      c.SetTransparent(true);
      float csize = 50.0f;
      c.SetTexture(
          g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesCursor));
      {
        auto xf = c.ScopedTransform();

        // Note: we don't plug in known cursor position values here; we tell
        // the renderer to insert the latest values on its end; this can
        // lessen cursor lag substantially.
        c.CursorTranslate();
        c.Translate(csize * 0.40f, csize * -0.38f, kCursorZDepth);
        c.Scale(csize, csize);
        c.DrawMeshAsset(
            g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
      }
      c.Submit();
    }
  }
}

void Graphics::ReturnCompletedFrameDef(FrameDef* frame_def) {
  std::scoped_lock lock(frame_def_delete_list_mutex_);
  g_base->graphics->frame_def_delete_list_.push_back(frame_def);
}

void Graphics::AddMeshDataCreate(MeshData* d) {
  assert(g_base->InLogicThread());
  assert(g_base->graphics);

  // Add this to our list of new-mesh-datas. We'll include this with our
  // next frame_def to have the graphics thread load before it processes the
  // frame_def.
  mesh_data_creates_.push_back(d);
}

void Graphics::AddMeshDataDestroy(MeshData* d) {
  assert(g_base->InLogicThread());
  assert(g_base->graphics);

  // Add this to our list of delete-mesh-datas; we'll include this with our
  // next frame_def to have the graphics thread kill before it processes the
  // frame_def.
  mesh_data_destroys_.push_back(d);
}

void Graphics::EnableProgressBar(bool fade_in) {
  assert(g_base->InLogicThread());
  progress_bar_loads_ = g_base->assets->GetGraphicalPendingLoadCount();
  assert(progress_bar_loads_ >= 0);
  if (progress_bar_loads_ > 0) {
    progress_bar_ = true;
    progress_bar_fade_in_ = fade_in;
    last_progress_bar_draw_time_ = g_core->AppTimeMillisecs();
    last_progress_bar_start_time_ = last_progress_bar_draw_time_;
    progress_bar_progress_ = 0.0f;
  }
}

void Graphics::ToggleManualCamera() {
  assert(g_base->InLogicThread());
  camera_->SetManual(!camera_->manual());
  if (camera_->manual()) {
    g_base->ScreenMessage("Manual Camera On");
  } else {
    g_base->ScreenMessage("Manual Camera Off");
  }
}

void Graphics::LocalCameraShake(float mag) {
  assert(g_base->InLogicThread());
  if (camera_.exists()) {
    camera_->Shake(mag);
  }
}

void Graphics::ToggleNetworkDebugDisplay() {
  assert(g_base->InLogicThread());
  network_debug_display_enabled_ = !network_debug_display_enabled_;
  if (network_debug_display_enabled_) {
    g_base->ScreenMessage("Network Debug Display Enabled");
  } else {
    g_base->ScreenMessage("Network Debug Display Disabled");
  }
}

void Graphics::ToggleDebugDraw() {
  assert(g_base->InLogicThread());
  set_debug_draw(!debug_draw_);
}

void Graphics::set_debug_draw(bool val) {
  assert(g_base->InLogicThread());
  debug_draw_ = val;
  if (g_base->graphics_server->renderer()) {
    g_base->graphics_server->renderer()->set_debug_draw_mode(debug_draw_);
  }
}

namespace {

/// Append one flat triangle (3 unshared verts sharing the face normal)
/// to object-split buffers being assembled for a debug primitive. The
/// primitives here are all convex and centered on the origin, so the
/// winding is flipped as needed to face outward (these draw
/// single-sided).
void AppendFlatTri(std::vector<VertexObjectSplitStatic>* v_static,
                   std::vector<VertexObjectSplitDynamic>* v_dynamic,
                   const Vector3f& p0, const Vector3f& p1, const Vector3f& p2) {
  Vector3f n = Vector3f::Cross(p1 - p0, p2 - p0);
  if (n.LengthSquared() > 0.0f) {
    n = n.Normalized();
  } else {
    n = Vector3f(0.0f, 1.0f, 0.0f);
  }
  const Vector3f* pts[3] = {&p0, &p1, &p2};
  Vector3f centroid = (p0 + p1 + p2) * (1.0f / 3.0f);
  if (n.Dot(centroid) < 0.0f) {
    n = -n;
    std::swap(pts[1], pts[2]);
  }
  for (const Vector3f* p : pts) {
    v_static->push_back({{0, 0}});
    VertexObjectSplitDynamic vd{};
    vd.position[0] = p->x;
    vd.position[1] = p->y;
    vd.position[2] = p->z;
    vd.normal[0] = static_cast<int16_t>(n.x * 32767.0f);
    vd.normal[1] = static_cast<int16_t>(n.y * 32767.0f);
    vd.normal[2] = static_cast<int16_t>(n.z * 32767.0f);
    v_dynamic->push_back(vd);
  }
}

/// Build a MeshIndexedObjectSplit from assembled flat-tri buffers
/// (sequential 16-bit indices).
auto MakeDebugMesh(const std::vector<VertexObjectSplitStatic>& v_static_in,
                   const std::vector<VertexObjectSplitDynamic>& v_dynamic_in)
    -> Object::Ref<MeshIndexedObjectSplit> {
  size_t count = v_static_in.size();
  assert(count == v_dynamic_in.size() && count > 0 && count <= 65535);
  auto v_static = Object::New<MeshBuffer<VertexObjectSplitStatic>>(
      count, v_static_in.data());
  auto v_dynamic = Object::New<MeshBuffer<VertexObjectSplitDynamic>>(
      count, v_dynamic_in.data());
  auto indices = Object::New<MeshIndexBuffer16>(count);
  for (size_t i = 0; i < count; ++i) {
    indices->elements[i] = static_cast<uint16_t>(i);
  }
  auto mesh = Object::New<MeshIndexedObjectSplit>();
  mesh->SetIndexData(indices);
  mesh->SetStaticData(v_static);
  mesh->SetDynamicData(v_dynamic);
  return mesh;
}

}  // namespace

auto Graphics::debug_sphere_mesh() -> MeshIndexedObjectSplit* {
  assert(g_base->InLogicThread());
  if (debug_sphere_mesh_.exists()) {
    return debug_sphere_mesh_.get();
  }
  // Lat/long sphere; every triangle gets its own verts + face normal so
  // it shades flat. Pole rows collapse to single triangles.
  const int stacks = 6;
  const int slices = 12;
  std::vector<VertexObjectSplitStatic> v_static;
  std::vector<VertexObjectSplitDynamic> v_dynamic;
  auto pt = [](int stack, int slice) {
    float phi = kPi * static_cast<float>(stack) / stacks;  // 0..pi
    float theta = 2.0f * kPi * static_cast<float>(slice) / slices;
    return Vector3f(sinf(phi) * cosf(theta), cosf(phi),
                    sinf(phi) * sinf(theta));
  };
  for (int i = 0; i < stacks; ++i) {
    for (int j = 0; j < slices; ++j) {
      Vector3f a = pt(i, j);
      Vector3f b = pt(i + 1, j);
      Vector3f c = pt(i + 1, j + 1);
      Vector3f d = pt(i, j + 1);
      if (i != 0) {
        AppendFlatTri(&v_static, &v_dynamic, a, c, d);
      }
      if (i != stacks - 1) {
        AppendFlatTri(&v_static, &v_dynamic, a, b, c);
      }
    }
  }
  debug_sphere_mesh_ = MakeDebugMesh(v_static, v_dynamic);
  return debug_sphere_mesh_.get();
}

auto Graphics::debug_hemisphere_mesh() -> MeshIndexedObjectSplit* {
  assert(g_base->InLogicThread());
  if (debug_hemisphere_mesh_.exists()) {
    return debug_hemisphere_mesh_.get();
  }
  // Top half of the debug sphere's lat/long layout, with the axis along
  // z so it caps a z-aligned (ODE convention) capsule.
  const int stacks = 3;  // Half of the sphere's 6.
  const int slices = 12;
  std::vector<VertexObjectSplitStatic> v_static;
  std::vector<VertexObjectSplitDynamic> v_dynamic;
  auto pt = [](int stack, int slice) {
    float phi = 0.5f * kPi * static_cast<float>(stack) / stacks;  // 0..pi/2
    float theta = 2.0f * kPi * static_cast<float>(slice) / slices;
    return Vector3f(sinf(phi) * cosf(theta), sinf(phi) * sinf(theta),
                    cosf(phi));
  };
  for (int i = 0; i < stacks; ++i) {
    for (int j = 0; j < slices; ++j) {
      Vector3f a = pt(i, j);
      Vector3f b = pt(i + 1, j);
      Vector3f c = pt(i + 1, j + 1);
      Vector3f d = pt(i, j + 1);
      if (i != 0) {
        AppendFlatTri(&v_static, &v_dynamic, a, c, d);
      }
      AppendFlatTri(&v_static, &v_dynamic, a, b, c);
    }
  }
  debug_hemisphere_mesh_ = MakeDebugMesh(v_static, v_dynamic);
  return debug_hemisphere_mesh_.get();
}

auto Graphics::debug_cylinder_mesh() -> MeshIndexedObjectSplit* {
  assert(g_base->InLogicThread());
  if (debug_cylinder_mesh_.exists()) {
    return debug_cylinder_mesh_.get();
  }
  const int slices = 12;
  std::vector<VertexObjectSplitStatic> v_static;
  std::vector<VertexObjectSplitDynamic> v_dynamic;
  auto ring = [](int slice, float z) {
    float theta = 2.0f * kPi * static_cast<float>(slice) / slices;
    return Vector3f(cosf(theta), sinf(theta), z);
  };
  for (int j = 0; j < slices; ++j) {
    Vector3f a = ring(j, 0.5f);
    Vector3f b = ring(j, -0.5f);
    Vector3f c = ring(j + 1, -0.5f);
    Vector3f d = ring(j + 1, 0.5f);
    AppendFlatTri(&v_static, &v_dynamic, a, c, d);
    AppendFlatTri(&v_static, &v_dynamic, a, b, c);
  }
  debug_cylinder_mesh_ = MakeDebugMesh(v_static, v_dynamic);
  return debug_cylinder_mesh_.get();
}

auto Graphics::debug_box_mesh() -> MeshIndexedObjectSplit* {
  assert(g_base->InLogicThread());
  if (debug_box_mesh_.exists()) {
    return debug_box_mesh_.get();
  }
  // 6 faces x 4 unshared verts so each face carries its own normal.
  const float h = 0.5f;
  struct Face {
    float n[3];
    float u[3];  // First in-plane axis.
    float v[3];  // Second in-plane axis.
  };
  const Face faces[6] = {
      {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}, {{-1, 0, 0}, {0, 0, 1}, {0, 1, 0}},
      {{0, 1, 0}, {0, 0, 1}, {1, 0, 0}}, {{0, -1, 0}, {1, 0, 0}, {0, 0, 1}},
      {{0, 0, 1}, {1, 0, 0}, {0, 1, 0}}, {{0, 0, -1}, {0, 1, 0}, {1, 0, 0}},
  };
  auto v_static = Object::New<MeshBuffer<VertexObjectSplitStatic>>(24);
  auto v_dynamic = Object::New<MeshBuffer<VertexObjectSplitDynamic>>(24);
  auto indices = Object::New<MeshIndexBuffer16>(36);
  const float corners[4][2] = {{-1, -1}, {1, -1}, {1, 1}, {-1, 1}};
  for (int f = 0; f < 6; ++f) {
    const Face& face = faces[f];
    for (int c = 0; c < 4; ++c) {
      auto& vs = v_static->elements[f * 4 + c];
      vs.uv[0] = vs.uv[1] = 0;
      auto& vd = v_dynamic->elements[f * 4 + c];
      for (int k = 0; k < 3; ++k) {
        vd.position[k] = h * face.n[k] + h * corners[c][0] * face.u[k]
                         + h * corners[c][1] * face.v[k];
        vd.normal[k] = static_cast<int16_t>(face.n[k] * 32767.0f);
      }
      vd.padding[0] = vd.padding[1] = 0;
    }
    uint16_t base = static_cast<uint16_t>(f * 4);
    uint16_t* idx = &indices->elements[f * 6];
    idx[0] = base;
    idx[1] = static_cast<uint16_t>(base + 1);
    idx[2] = static_cast<uint16_t>(base + 2);
    idx[3] = base;
    idx[4] = static_cast<uint16_t>(base + 2);
    idx[5] = static_cast<uint16_t>(base + 3);
  }
  debug_box_mesh_ = Object::New<MeshIndexedObjectSplit>();
  debug_box_mesh_->SetIndexData(indices);
  debug_box_mesh_->SetStaticData(v_static);
  debug_box_mesh_->SetDynamicData(v_dynamic);
  return debug_box_mesh_.get();
}

void Graphics::ReleaseFadeEndCommand() { fade_end_call_.Clear(); }

auto Graphics::ValueTest(const std::string& arg, double* absval,
                         double* deltaval, double* outval) -> bool {
  return false;
}

void Graphics::DrawRadialMeter(MeshIndexedSimpleFull* m, float amt) {
  // FIXME - we're updating this every frame so we should use pure dynamic
  //  data; not a mix of static and dynamic.

  if (amt >= 0.999f) {
    uint16_t indices[] = {0, 1, 2, 1, 3, 2};
    VertexSimpleFull vertices[] = {
        {-1, -1, 0, 0, 65535},
        {1, -1, 0, 65535, 65535},
        {-1, 1, 0, 0, 0},
        {1, 1, 0, 65535, 0},
    };
    m->SetIndexData(Object::New<MeshIndexBuffer16>(6, indices));
    m->SetData(Object::New<MeshBuffer<VertexSimpleFull>>(4, vertices));

  } else {
    bool flipped = true;
    uint16_t indices[15];
    VertexSimpleFull v[15];
    float x = -tanf(amt * (3.141592f * 2.0f));
    uint16_t i = 0;

    // First 45 degrees past 12:00.
    if (amt > 0.875f) {
      if (flipped) {
        v[i].uv[0] = 0;
        v[i].uv[1] = 0;
        v[i].position[0] = -1;
        v[i].position[1] = 1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * 0.5f);
        v[i].uv[1] = static_cast<uint16_t>(65535 * 0.5f);
        v[i].position[0] = 0;
        v[i].position[1] = 0;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * (0.5f + x * 0.5f));
        v[i].uv[1] = 0;
        v[i].position[0] = -x;
        v[i].position[1] = 1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
      }
    }

    // Top right down to bot-right.
    if (amt > 0.625f) {
      float y = (amt > 0.875f ? -1.0f : 1.0f / tanf(amt * (3.141592f * 2.0f)));
      if (flipped) {
        v[i].uv[0] = 0;
        v[i].uv[1] = static_cast<uint16_t>(65535 * (0.5f + y * 0.5f));
        v[i].position[0] = -1;
        v[i].position[1] = -y;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
        v[i].uv[0] = 0;
        v[i].uv[1] = 65535;
        v[i].position[0] = -1;
        v[i].position[1] = -1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * 0.5f);
        v[i].uv[1] = static_cast<uint16_t>(65535 * 0.5f);
        v[i].position[0] = 0;
        v[i].position[1] = 0;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
      }
    }

    // Bot right to bot left.
    if (amt > 0.375f) {
      float x2 = (amt > 0.625f ? 1.0f : tanf(amt * (3.141592f * 2.0f)));
      if (flipped) {
        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * (0.5f + x2 * 0.5f));
        v[i].uv[1] = 65535;
        v[i].position[0] = -x2;
        v[i].position[1] = -1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;

        v[i].uv[0] = 65535;
        v[i].uv[1] = 65535;
        v[i].position[0] = 1;
        v[i].position[1] = -1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;

        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * 0.5f);
        v[i].uv[1] = static_cast<uint16_t>(65535 * 0.5f);
        v[i].position[0] = 0;
        v[i].position[1] = 0;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
      }
    }

    // Bot left to top left.
    if (amt > 0.125f) {
      float y = (amt > 0.375f ? -1.0f : 1.0f / tanf(amt * (3.141592f * 2.0f)));

      if (flipped) {
        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * 0.5f);
        v[i].uv[1] = static_cast<uint16_t>(65535 * 0.5f);
        v[i].position[0] = 0;
        v[i].position[1] = 0;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;

        v[i].uv[0] = 65535;
        v[i].uv[1] = static_cast<uint16_t>(65535 * (0.5f - 0.5f * y));
        v[i].position[0] = 1;
        v[i].position[1] = y;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;

        v[i].uv[0] = 65535;
        v[i].uv[1] = 0;
        v[i].position[0] = 1;
        v[i].position[1] = 1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
      }
    }

    // Top left to top mid.
    {
      float x2 = (amt > 0.125f ? 1.0f : tanf(amt * (3.141592f * 2.0f)));
      if (flipped) {
        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * 0.5f);
        v[i].uv[1] = static_cast<uint16_t>(65535 * 0.5f);
        v[i].position[0] = 0;
        v[i].position[1] = 0;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;

        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * (0.5f - x2 * 0.5f));
        v[i].uv[1] = 0;
        v[i].position[0] = x2;
        v[i].position[1] = 1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;

        v[i].uv[0] = static_cast<uint16_t>(65535 - 65535 * 0.5f);
        v[i].uv[1] = 0;
        v[i].position[0] = 0;
        v[i].position[1] = 1;
        v[i].position[2] = 0;
        indices[i] = i;
        i++;
      }
    }
    m->SetIndexData(Object::New<MeshIndexBuffer16>(i, indices));
    m->SetData(Object::New<MeshBuffer<VertexSimpleFull>>(i, v));
  }
}

void Graphics::OnScreenSizeChange() {}

void Graphics::GetBaseVirtualRes(float* x, float* y) {
  assert(x);
  assert(y);
  float base_virtual_res_x;
  float base_virtual_res_y;
  // if (g_base->ui->scale() == UIScale::kSmall) {
  //   base_virtual_res_x = kBaseVirtualResSmallX;
  //   base_virtual_res_y = kBaseVirtualResSmallY;
  // } else {
  base_virtual_res_x = kBaseVirtualResX;
  base_virtual_res_y = kBaseVirtualResY;
  // }
  *x = base_virtual_res_x;
  *y = base_virtual_res_y;
}

void Graphics::CalcVirtualRes_(float* x, float* y) {
  assert(g_base);
  float base_virtual_res_x;
  float base_virtual_res_y;
  GetBaseVirtualRes(&base_virtual_res_x, &base_virtual_res_y);

  float x_in = *x;
  float y_in = *y;
  if (*x / *y > static_cast<float>(base_virtual_res_x)
                    / static_cast<float>(base_virtual_res_y)) {
    *y = base_virtual_res_y;
    *x = *y * (x_in / y_in);
  } else {
    *x = base_virtual_res_x;
    *y = *x * (y_in / x_in);
  }
}

auto Graphics::CalcActiveRenderRect(float res_x, float res_y) const -> Rect {
  Rect rect{0.0f, 0.0f, res_x, res_y};

  // Clamp aspect ratio, keeping the largest centered sub-rect that
  // satisfies our bounds (unless the user has opted out of the clamp;
  // the virtual res then simply follows the window's shape).
  if (!allow_extreme_aspect_ratios_ && rect.width() > 0.0f
      && rect.height() > 0.0f) {
    float aspect = rect.width() / rect.height();
    if (aspect < kMinAspectRatio) {
      float trim = (rect.height() - rect.width() / kMinAspectRatio) * 0.5f;
      rect.b += trim;
      rect.t -= trim;
    } else if (aspect > kMaxAspectRatio) {
      float trim = (rect.width() - rect.height() * kMaxAspectRatio) * 0.5f;
      rect.l += trim;
      rect.r -= trim;
    }
  }
  return rect;
}

void Graphics::SetScreenResolution(float x, float y) {
  assert(g_base->InLogicThread());

  // Ignore redundant sets.
  if (res_x_ == x && res_y_ == y) {
    return;
  }

  res_x_ = x;
  res_y_ = y;

  UpdateScreen_();
}

void Graphics::SetOSSafeAreaInsets(float l, float r, float b, float t) {
  assert(g_base->InLogicThread());

  // Ignore redundant sets; platform layers are free to call this on
  // every insets callback without worrying about churn.
  if (os_inset_l_ == l && os_inset_r_ == r && os_inset_b_ == b
      && os_inset_t_ == t) {
    return;
  }
  os_inset_l_ = l;
  os_inset_r_ = r;
  os_inset_b_ = b;
  os_inset_t_ = t;

  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kDebug,
                       "OS safe-area insets now l=" + std::to_string(l) + " r="
                           + std::to_string(r) + " b=" + std::to_string(b)
                           + " t=" + std::to_string(t) + ".");

  UpdateScreen_();
}

auto Graphics::CalcVirtualBoundsRect(const Rect& render_rect, float res_x,
                                     float res_y, float inset_l, float inset_r,
                                     float inset_b, float inset_t, float bleed)
    -> Rect {
  float width = render_rect.width();
  float height = render_rect.height();
  if (width <= 0.0f || height <= 0.0f || res_x <= 0.0f || res_y <= 0.0f) {
    return render_rect;
  }

  // Left/right only for now; see the header. inset_b/inset_t are
  // deliberately unused rather than absent, so honoring them later is
  // a change here and nowhere else.
  (void)inset_b;
  (void)inset_t;

  // Fractions are of the whole screen, so resolve them against that and
  // work in absolute coords, then intersect. A render rect already
  // sitting inside the obscured strip has nothing further to give up.
  float unobscured_l = inset_l * res_x;
  float unobscured_r = res_x - inset_r * res_x;

  Rect out{std::max(render_rect.l, unobscured_l), render_rect.b,
           std::min(render_rect.r, unobscured_r), render_rect.t};

  // Clamp what we actually give up per edge, measured against the
  // render rect. A device reporting something absurd (or a unit mix-up
  // in a platform layer, which has happened) should cost a clipped
  // corner, not the play area.
  float maxinset = width * kMaxVirtualBoundsInsetFraction;
  out.l = std::min(out.l, render_rect.l + maxinset);
  out.r = std::max(out.r, render_rect.r - maxinset);

  // Let content bleed back out a little; see kVirtualBoundsBleed. The
  // bleed is in virtual units, so resolve it through this rect's own
  // virtual scale.
  //
  // Note that is well-defined rather than circular, but only just: the
  // scale comes from CalcVirtualRes_, which pins *height* to the base
  // res whenever the rect is wider than the base aspect -- and we only
  // ever inset left/right, so the dimension the scale depends on is
  // one the bleed never touches. In the narrow case it pins width
  // instead and the two would feed each other, so measure the scale
  // off the pre-bleed rect and be done.
  if (bleed > 0.0f && out.width() > 0.0f && out.height() > 0.0f) {
    float virtual_w = out.width();
    float virtual_h = out.height();
    CalcVirtualRes_(&virtual_w, &virtual_h);
    if (virtual_h > 0.0f) {
      float px_per_virtual_unit = out.height() / virtual_h;
      float bleed_px = bleed * px_per_virtual_unit;

      // Never past the render rect: bleeding beyond what we actually
      // draw into would put the bounds outside the screen.
      out.l = std::max(render_rect.l, out.l - bleed_px);
      out.r = std::min(render_rect.r, out.r + bleed_px);
    }
  }

  // Degenerate insets would take the bounds inside-out.
  if (out.width() <= 0.0f) {
    return render_rect;
  }
  return out;
}

auto Graphics::CalcMaxMarginsVirtualBoundsRect(const Rect& render_rect,
                                               float base_virtual_res_x,
                                               float base_virtual_res_y,
                                               float margin_x, float margin_y)
    -> Rect {
  float width = render_rect.width();
  float height = render_rect.height();
  if (width <= 0.0f || height <= 0.0f || base_virtual_res_x <= 0.0f
      || base_virtual_res_y <= 0.0f || margin_x < 0.0f || margin_y < 0.0f) {
    return render_rect;
  }

  // With the margins in place, the outer rect spans (base-res +
  // 2 * margin) virtual units along whichever axis CalcVirtualRes_
  // pins to the base res, so pixels-per-virtual-unit is the render
  // size over that span. The pinned axis is the one yielding the
  // smaller scale: the other axis then ends up with more virtual
  // units than its base span, which is exactly the condition
  // CalcVirtualRes_ pins by.
  float scale = std::min(width / (base_virtual_res_x + 2.0f * margin_x),
                         height / (base_virtual_res_y + 2.0f * margin_y));

  // Margins can never invert the rect: each pair takes at most
  // 2 * margin / (base-res + 2 * margin) of its axis.
  return Rect{
      render_rect.l + margin_x * scale, render_rect.b + margin_y * scale,
      render_rect.r - margin_x * scale, render_rect.t - margin_y * scale};
}

auto Graphics::BlendScreenInsetsRect(const Rect& os_bounds,
                                     const Rect& max_bounds, float amount)
    -> Rect {
  amount = std::clamp(amount, 0.0f, 1.0f);
  auto lerp = [amount](float a, float b) { return a + (b - a) * amount; };

  // Never give back any of what the OS asked for; a deep enough
  // obstruction can reach past the max margins.
  return Rect{std::max(os_bounds.l, lerp(os_bounds.l, max_bounds.l)),
              std::max(os_bounds.b, lerp(os_bounds.b, max_bounds.b)),
              std::min(os_bounds.r, lerp(os_bounds.r, max_bounds.r)),
              std::min(os_bounds.t, lerp(os_bounds.t, max_bounds.t))};
}

auto Graphics::AutoScreenInsetAmount() const -> float {
  assert(g_base->InLogicThread());
  if (g_core->platform->IsRunningOnTV()) {
    return kAutoScreenInsetAmountTV;
  }
  switch (g_base->ui->uiscale()) {
    case UIScale::kSmall:
      return kAutoScreenInsetAmountSmall;
    case UIScale::kMedium:
      return kAutoScreenInsetAmountMedium;
    case UIScale::kLarge:
      return kAutoScreenInsetAmountLarge;
    case UIScale::kLast:
      break;
  }
  BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
              "Unhandled uiscale in AutoScreenInsetAmount.");
  return 0.0f;
}

auto Graphics::ScreenInsetAmount() const -> float {
  assert(g_base->InLogicThread());
  return screen_insets_custom_ ? custom_screen_insets_
                               : AutoScreenInsetAmount();
}

void Graphics::SetForceMaxVirtualBoundsMargins(bool val) {
  assert(g_base->InLogicThread());
  if (val == force_max_virtual_bounds_margins_) {
    return;
  }
  force_max_virtual_bounds_margins_ = val;

  if (val) {
    // Say so loudly, same as the A/B knob: this deliberately mangles
    // what gets drawn, so a run with it on should be obvious.
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kWarning,
                         "USING FORCED MAX-MARGIN VIRTUAL BOUNDS.");
  }

  // Feeds into rect calcs, so redo those.
  UpdateScreen_();
}

auto Graphics::CalcVirtualBoundsRect_(const Rect& render_rect) -> Rect {
  assert(g_base->InLogicThread());

  // TVs ignore OS insets; their automatic screen-inset amount covers
  // overscan (see kAutoScreenInsetAmountTV), and honoring an OS inset
  // as well would compensate twice for the same thing.
  if (g_core->platform->IsRunningOnTV()) {
    return render_rect;
  }

  Rect out = CalcVirtualBoundsRect(
      render_rect, res_x_, res_y_, os_inset_l_, os_inset_r_, os_inset_b_,
      os_inset_t_, kVirtualBoundsBleedEnabled ? kVirtualBoundsBleed : 0.0f);

  float maxinset = render_rect.width() * kMaxVirtualBoundsInsetFraction;
  if (out.l - render_rect.l >= maxinset || render_rect.r - out.r >= maxinset) {
    BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kWarning,
                "Clamped an OS side inset (l=" + std::to_string(os_inset_l_)
                    + " r=" + std::to_string(os_inset_r_)
                    + " as screen fractions) to " + std::to_string(maxinset)
                    + "px of a " + std::to_string(render_rect.width())
                    + "px rect.");
  }

  // Stay aware of any device out in the wild whose *applied* margins
  // (post-clamp, post-bleed) exceed the max-margins calibration target
  // (kMaxVirtualBoundsMarginX/Y) - UIs are calibrated against
  // those values, so such a device would be seeing layouts nothing was
  // ever tested at.
  if (out.width() > 0.0f && out.height() > 0.0f) {
    float virtual_w = out.width();
    float virtual_h = out.height();
    CalcVirtualRes_(&virtual_w, &virtual_h);
    if (virtual_h > 0.0f) {
      float px_per_virtual_unit = out.height() / virtual_h;
      float margin_l = (out.l - render_rect.l) / px_per_virtual_unit;
      float margin_r = (render_rect.r - out.r) / px_per_virtual_unit;
      float margin_b = (out.b - render_rect.b) / px_per_virtual_unit;
      float margin_t = (render_rect.t - out.t) / px_per_virtual_unit;
      if (margin_l > kMaxVirtualBoundsMarginX
          || margin_r > kMaxVirtualBoundsMarginX
          || margin_b > kMaxVirtualBoundsMarginY
          || margin_t > kMaxVirtualBoundsMarginY) {
        BA_LOG_ONCE(
            LogName::kBaGraphics, LogLevel::kWarning,
            "OS-derived virtual-bounds margins (l="
                + std::to_string(margin_l) + " r=" + std::to_string(margin_r)
                + " b=" + std::to_string(margin_b)
                + " t=" + std::to_string(margin_t)
                + " virtual units) exceed the max-margins calibration"
                  " target ("
                + std::to_string(kMaxVirtualBoundsMarginX) + "/"
                + std::to_string(kMaxVirtualBoundsMarginY)
                + "); UIs are not calibrated for this much margin.");
      }
    }
  }
  return out;
}

void Graphics::OnUIScaleChange() {
  // UIScale affects our virtual res calculations. Redo those.
  UpdateScreen_();
}

void Graphics::UpdateScreen_() {
  assert(g_base->InLogicThread());

  // We'll need to ship a new settings to the server with this change.
  graphics_settings_dirty_ = true;

  // Calc virtual res. In vr mode our virtual res is independent of our
  // screen size (since it gets drawn to an overlay).
  if (g_core->vr_mode()) {
    active_render_rect_ = Rect{0.0f, 0.0f, res_x_, res_y_};
    virtual_bounds_rect_ = active_render_rect_;
    res_x_virtual_ = kBaseVirtualResX;
    res_y_virtual_ = kBaseVirtualResY;
  } else {
    // Drawing extends across our active render rect (the window minus
    // aspect-ratio limiting)...
    active_render_rect_ = CalcActiveRenderRect(res_x_, res_y_);
    if (active_render_rect_.width() <= 0.0f
        || active_render_rect_.height() <= 0.0f) {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                  "Active render rect is degenerate ("
                      + std::to_string(active_render_rect_.width()) + "x"
                      + std::to_string(active_render_rect_.height())
                      + " for window " + std::to_string(res_x_) + "x"
                      + std::to_string(res_y_) + ").");
    }

    // ...but what our drawing coords *mean* comes from the virtual
    // bounds within that rect. We draw as if the bounds were the render
    // rect; anything beyond simply keeps drawing out to the render rect
    // edge.
    virtual_bounds_rect_ = CalcVirtualBoundsRect_(active_render_rect_);

    float base_virtual_res_x;
    float base_virtual_res_y;
    GetBaseVirtualRes(&base_virtual_res_x, &base_virtual_res_y);
    Rect max_margins_rect = CalcMaxMarginsVirtualBoundsRect(
        active_render_rect_, base_virtual_res_x, base_virtual_res_y,
        kMaxVirtualBoundsMarginX, kMaxVirtualBoundsMarginY);

    // Pull the bounds further in per the screen-insets setting.
    float screen_inset_amount = ScreenInsetAmount();
    if (screen_inset_amount > 0.0f) {
      virtual_bounds_rect_ = BlendScreenInsetsRect(
          virtual_bounds_rect_, max_margins_rect, screen_inset_amount);
    }

    // The debug knobs replace any OS-derived inset (and the bleed and
    // screen-insets setting) rather than stacking on them: each exists
    // to produce a known rect, and adding a device's own inset on top
    // would make it something other than what it claims. Max-margins
    // takes precedence over the A/B knob when both are somehow on; the
    // dev-console toggle is the more immediate intent.
    if (force_max_virtual_bounds_margins_) {
      virtual_bounds_rect_ = max_margins_rect;
    } else if (virtual_bounds_ab_mode_ != VirtualBoundsABMode::kDisabled) {
      // Both configs share this one bounds rect; they differ only in
      // whether the render rect shrinks to meet it (A - black outside)
      // or stays put (B - drawn content outside). Everything inside the
      // bounds must therefore look identical in the two, which is the
      // whole point of the exercise.
      Rect inset_rect = CalcDebugVirtualBoundsRect_(active_render_rect_);
      virtual_bounds_rect_ = inset_rect;
      bool use_a = virtual_bounds_ab_mode_ == VirtualBoundsABMode::kA
                   || (virtual_bounds_ab_mode_ == VirtualBoundsABMode::kToggle
                       && !virtual_bounds_ab_showing_b_);
      if (use_a) {
        active_render_rect_ = inset_rect;
      }
    }
    if (virtual_bounds_rect_.width() <= 0.0f
        || virtual_bounds_rect_.height() <= 0.0f) {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                  "Virtual bounds rect is degenerate ("
                      + std::to_string(virtual_bounds_rect_.width()) + "x"
                      + std::to_string(virtual_bounds_rect_.height())
                      + " for window " + std::to_string(res_x_) + "x"
                      + std::to_string(res_y_) + ").");
    }
    res_x_virtual_ = virtual_bounds_rect_.width();
    res_y_virtual_ = virtual_bounds_rect_.height();
    CalcVirtualRes_(&res_x_virtual_, &res_y_virtual_);
  }
  virtual_outer_rect_ =
      CalcVirtualOuterRect(active_render_rect_, virtual_bounds_rect_,
                           res_x_virtual_, res_y_virtual_);

  // Need to rebuild internal components (some are sized to the screen).
  internal_components_inited_ = false;

  // This may trigger us sending initial graphics settings to the
  // graphics-server to kick off drawing.
  got_screen_resolution_ = true;
  UpdateInitialGraphicsSettingsSend_();

  // Inform all our logic thread buddies of virtual/physical res changes.
  g_base->logic->OnScreenSizeChange(res_x_virtual_, res_y_virtual_, res_x_,
                                    res_y_);
}

auto Graphics::CubeMapFromReflectionType(ReflectionType reflection_type)
    -> TextureAsset* {
  const auto& assets = g_base->assets->base_assets();
  switch (reflection_type) {
    case ReflectionType::kChar:
      return assets.reflection_char.get();
    case ReflectionType::kPowerup:
      return assets.reflection_powerup.get();
    case ReflectionType::kSoft:
      return assets.reflection_soft.get();
    case ReflectionType::kSharp:
      return assets.reflection_sharp.get();
    case ReflectionType::kSharper:
      return assets.reflection_sharper.get();
    case ReflectionType::kSharpest:
      return assets.reflection_sharpest.get();
    default:
      throw Exception();
  }
}

auto Graphics::StringFromReflectionType(ReflectionType r) -> std::string {
  switch (r) {
    case ReflectionType::kSoft:
      return "soft";
      break;
    case ReflectionType::kChar:
      return "char";
      break;
    case ReflectionType::kPowerup:
      return "powerup";
      break;
    case ReflectionType::kSharp:
      return "sharp";
      break;
    case ReflectionType::kSharper:
      return "sharper";
      break;
    case ReflectionType::kSharpest:
      return "sharpest";
      break;
    case ReflectionType::kNone:
      return "none";
      break;
    default:
      throw Exception("Invalid reflection value: "
                      + std::to_string(static_cast<int>(r)));
      break;
  }
}

auto Graphics::ReflectionTypeFromString(const std::string& s)
    -> ReflectionType {
  ReflectionType r;
  if (s == "soft") {
    r = ReflectionType::kSoft;
  } else if (s == "char") {
    r = ReflectionType::kChar;
  } else if (s == "powerup") {
    r = ReflectionType::kPowerup;
  } else if (s == "sharp") {
    r = ReflectionType::kSharp;
  } else if (s == "sharper") {
    r = ReflectionType::kSharper;
  } else if (s == "sharpest") {
    r = ReflectionType::kSharpest;
  } else if (s.empty() || s == "none") {
    r = ReflectionType::kNone;
  } else {
    throw Exception("invalid reflection type: '" + s + "'");
  }
  return r;
}

void Graphics::LanguageChanged() {
  assert(g_base && g_base->InLogicThread());
  if (building_frame_def_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "Graphics::LanguageChanged() called during draw; should not happen.");
  }
  screenmessages->ClearScreenMessageTranslations();
}

auto Graphics::GraphicsQualityFromRequest(GraphicsQualityRequest request,
                                          GraphicsQuality auto_val)
    -> GraphicsQuality {
  switch (request) {
    case GraphicsQualityRequest::kLow:
      return GraphicsQuality::kLow;
    case GraphicsQualityRequest::kMedium:
      return GraphicsQuality::kMedium;
    case GraphicsQualityRequest::kHigh:
      return GraphicsQuality::kHigh;
    case GraphicsQualityRequest::kHigher:
      return GraphicsQuality::kHigher;
    case GraphicsQualityRequest::kAuto:
      return auto_val;
    default:
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "Unhandled GraphicsQualityRequest value: "
                               + std::to_string(static_cast<int>(request)));
      return GraphicsQuality::kLow;
  }
}

auto Graphics::TextureQualityFromRequest(TextureQualityRequest request,
                                         TextureQuality auto_val)
    -> TextureQuality {
  switch (request) {
    case TextureQualityRequest::kLow:
      return TextureQuality::kLow;
    case TextureQualityRequest::kMedium:
      return TextureQuality::kMedium;
    case TextureQualityRequest::kHigh:
      return TextureQuality::kHigh;
    case TextureQualityRequest::kAuto:
      return auto_val;
    default:
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                           "Unhandled TextureQualityRequest value: "
                               + std::to_string(static_cast<int>(request)));
      return TextureQuality::kLow;
  }
}

void Graphics::set_client_context(Snapshot<GraphicsClientContext>* context) {
  assert(g_base->InLogicThread());

  // Currently we only expect this to be set once. That will change once we
  // support renderer swapping/etc.
  assert(!g_base->logic->graphics_ready());
  assert(!client_context_snapshot_.exists());
  client_context_snapshot_ = context;

  // Placeholder settings are affected by client context, so update them
  // when it changes.
  UpdatePlaceholderSettings();

  // Let the logic system know its free to proceed beyond bootstrapping.
  g_base->logic->OnGraphicsReady();
}

// This call exists for the graphics-server to call when they've changed
void Graphics::UpdatePlaceholderSettings() {
  assert(g_base->InLogicThread());

  // Need both of these in place.
  if (!settings_snapshot_.exists() || !has_client_context()) {
    return;
  }

  texture_quality_placeholder_ = TextureQualityFromRequest(
      settings()->texture_quality, client_context()->auto_texture_quality);
}

void Graphics::DrawVirtualSafeAreaBounds(RenderPass* pass) {
  // We can optionally draw a guide to show the edges of the overlay pass
  if (draw_virtual_safe_area_bounds_) {
    SimpleComponent c(pass);
    c.SetColor(1, 0, 0);
    {
      auto xf = c.ScopedTransform();

      float width, height;

      GetBaseVirtualRes(&width, &height);

      // Slight offset in z to reduce z fighting.
      c.Translate(0.5f * pass->virtual_width(), 0.5f * pass->virtual_height(),
                  0.0f);
      c.Scale(width, height, 0.01f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesOverlayGuide));
    }
    c.Submit();
  }
}

void Graphics::ExtendFrustumToRenderRect(const Rect& render_rect,
                                         const Rect& bounds_rect, float* l,
                                         float* r, float* b, float* t) {
  float bw = bounds_rect.width();
  float bh = bounds_rect.height();
  if (bw <= 0.0f || bh <= 0.0f) {
    return;  // Degenerate; callers log those separately.
  }

  // How far past the bounds we physically reach on each edge, as a
  // fraction of the bounds.
  float ext_l = (bounds_rect.l - render_rect.l) / bw;
  float ext_r = (render_rect.r - bounds_rect.r) / bw;
  float ext_b = (bounds_rect.b - render_rect.b) / bh;
  float ext_t = (render_rect.t - bounds_rect.t) / bh;

  // Push each edge out by its own margin, scaled by the frustum's full
  // extent in that axis.
  float width = *l + *r;
  float height = *b + *t;
  *l += width * ext_l;
  *r += width * ext_r;
  *b += height * ext_b;
  *t += height * ext_t;
}

void Graphics::DrawVirtualBounds(RenderPass* pass) {
  // Optionally show where our virtual coord system ends. With no cutout
  // inset this lands right at the edge of the drawn area; inset, it
  // pulls in and whatever sits between it and the edge is margin we
  // keep drawing into (backgrounds and whatnot) but that UI should stay
  // out of. Green so it reads distinctly from the red safe-area guide
  // when both are on.
  if (draw_virtual_bounds_) {
    SimpleComponent c(pass);
    c.SetColor(0, 1, 0);
    {
      auto xf = c.ScopedTransform();

      // The virtual bounds are exactly our virtual rect by definition,
      // so this is the plain (0, 0)-(virtual-res) box. It only *looks*
      // inset once the bounds are, since our projections then extend
      // out past it.
      float width = pass->virtual_width();
      float height = pass->virtual_height();

      // Slight offset in z to reduce z fighting, negative so we sit
      // behind the safe-area guide where the two coincide.
      c.Translate(0.5f * width, 0.5f * height, -0.02f);
      c.Scale(width, height, 0.01f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesOverlayGuide));
    }
    c.Submit();
  }
}

}  // namespace ballistica::base
