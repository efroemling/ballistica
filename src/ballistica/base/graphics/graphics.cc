// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/graphics.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/post_process_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/component/special_component.h"
#include "ballistica/base/graphics/component/sprite_component.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/mesh/image_mesh.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/net_graph.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/event_loop.h"

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
    case ShadingType::kObjectReflectTransparent:
    case ShadingType::kObjectReflectAddTransparent:
    case ShadingType::kSimpleTextureModulatedTransparent:
    case ShadingType::kSimpleTextureModulatedTransFlatness:
    case ShadingType::kSimpleTextureModulatedTransparentDoubleSided:
    case ShadingType::kSimpleTextureModulatedTransparentColorized:
    case ShadingType::kSimpleTextureModulatedTransparentColorized2:
    case ShadingType::kSimpleTextureModulatedTransparentColorized2Masked:
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
    case ShadingType::kSimpleTextureModulatedColorized2:
    case ShadingType::kSimpleTextureModulatedColorized2Masked:
    case ShadingType::kSimpleTexture:
    case ShadingType::kObject:
    case ShadingType::kObjectReflect:
    case ShadingType::kObjectLightShadow:
    case ShadingType::kObjectReflectLightShadow:
    case ShadingType::kObjectReflectLightShadowDoubleSided:
    case ShadingType::kObjectReflectLightShadowColorized:
    case ShadingType::kObjectReflectLightShadowColorized2:
    case ShadingType::kObjectReflectLightShadowAdd:
    case ShadingType::kObjectReflectLightShadowAddColorized:
    case ShadingType::kObjectReflectLightShadowAddColorized2:
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

void Graphics::OnAppStart() { assert(g_base->InLogicThread()); }

void Graphics::OnAppSuspend() {
  assert(g_base->InLogicThread());
  SetGyroEnabled(false);
}

void Graphics::OnAppUnsuspend() {
  assert(g_base->InLogicThread());
  g_base->graphics->SetGyroEnabled(true);
}

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

  bool disable_camera_gyro =
      g_base->app_config->Resolve(AppConfig::BoolID::kDisableCameraGyro);
  set_camera_gyro_explicitly_disabled(disable_camera_gyro);

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

void Graphics::StepDisplayTime() { assert(g_base->InLogicThread()); }

void Graphics::AddCleanFrameCommand(const Object::Ref<PythonContextCall>& c) {
  assert(g_base->InLogicThread());
  clean_frame_commands_.push_back(c);
}

void Graphics::RunCleanFrameCommands() {
  assert(g_base->InLogicThread());
  for (auto&& i : clean_frame_commands_) {
    i->Run();
  }
  clean_frame_commands_.clear();
}

auto Graphics::TextureQualityFromAppConfig() -> TextureQualityRequest {
  // Texture quality.
  TextureQualityRequest texture_quality_requested;
  std::string texqualstr =
      g_base->app_config->Resolve(AppConfig::StringID::kTextureQuality);

  if (texqualstr == "Auto") {
    texture_quality_requested = TextureQualityRequest::kAuto;
  } else if (texqualstr == "High") {
    texture_quality_requested = TextureQualityRequest::kHigh;
  } else if (texqualstr == "Medium") {
    texture_quality_requested = TextureQualityRequest::kMedium;
  } else if (texqualstr == "Low") {
    texture_quality_requested = TextureQualityRequest::kLow;
  } else {
    g_core->logging->Log(
        LogName::kBaGraphics, LogLevel::kError,
        "Invalid texture quality: '" + texqualstr + "'; defaulting to low.");
    texture_quality_requested = TextureQualityRequest::kLow;
  }
  return texture_quality_requested;
}

auto Graphics::VSyncFromAppConfig() -> VSyncRequest {
  std::string v_sync =
      g_base->app_config->Resolve(AppConfig::StringID::kVerticalSync);
  if (v_sync == "Auto") {
    return VSyncRequest::kAuto;
  } else if (v_sync == "Always") {
    return VSyncRequest::kAuto;
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

void Graphics::SetGyroEnabled(bool enable) {
  // If we're turning back on, suppress gyro updates for a bit.
  if (enable && !gyro_enabled_) {
    last_suppress_gyro_time_ = g_core->AppTimeMicrosecs();
  }
  gyro_enabled_ = enable;
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

void Graphics::SetShadowRange(float lower_bottom, float lower_top,
                              float upper_bottom, float upper_top) {
  assert(lower_top >= lower_bottom && upper_bottom >= lower_top
         && upper_top >= upper_bottom);
  shadow_lower_bottom_ = lower_bottom;
  shadow_lower_top_ = lower_top;
  shadow_upper_bottom_ = upper_bottom;
  shadow_upper_top_ = upper_top;
}

auto Graphics::GetShadowDensity(float x, float y, float z) -> float {
  if (y < shadow_lower_bottom_) {
    return 0.0f;
  } else if (y < shadow_lower_top_) {
    float amt =
        (y - shadow_lower_bottom_) / (shadow_lower_top_ - shadow_lower_bottom_);
    return amt;
  } else if (y < shadow_upper_bottom_) {
    return 1.0f;
  } else if (y < shadow_upper_top_) {
    float amt =
        (y - shadow_upper_bottom_) / (shadow_upper_top_ - shadow_upper_bottom_);
    return 1.0f - amt;
  } else {
    return 0.0f;
  }
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

  screenmessages->DrawMiscOverlays(frame_def);
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

void Graphics::Reset() {
  assert(g_base->InLogicThread());
  fade_ = 0;
  fade_start_ = fade_cancel_start_ = fade_time_ = 0;

  if (!camera_.exists()) {
    camera_ = Object::New<Camera>();
  }

  screenmessages->Reset();
}

void Graphics::InitInternalComponents(FrameDef* frame_def) {
  RenderPass* pass = frame_def->GetOverlayFlatPass();

  screen_mesh_ = Object::New<ImageMesh>();

  // Let's draw a bit bigger than screen to account for tv-border-mode.
  float w = pass->virtual_width();
  float h = pass->virtual_height();
  if (g_core->vr_mode()) {
    screen_mesh_->SetPositionAndSize(
        -(0.5f * kVRBorder) * w, (-0.5f * kVRBorder) * h, kScreenMeshZDepth,
        (1.0f + kVRBorder) * w, (1.0f + kVRBorder) * h);
  } else {
    screen_mesh_->SetPositionAndSize(
        -(0.5f * kTVBorder) * w, (-0.5f * kTVBorder) * h, kScreenMeshZDepth,
        (1.0f + kTVBorder) * w, (1.0f + kTVBorder) * h);
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

    // We keep a cached copy of this value since we use it a lot.
    tv_border_ = settings_snapshot_->get()->tv_border;

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

void Graphics::UpdateGyro(microsecs_t time_microsecs,
                          microsecs_t elapsed_microsecs) {
  Vector3f tilt = gyro_vals_;

  millisecs_t elapsed_millisecs = elapsed_microsecs / 1000;

  // Our gyro vals get set from another thread and we don't use a lock,
  // so perhaps there's a chance we get corrupted float values here?..
  // Let's watch out for crazy vals just in case.
  for (float& i : tilt.v) {
    // Check for NaN and Inf:
    if (!std::isfinite(i)) {
      i = 0.0f;
    }

    // Clamp crazy big values:
    i = std::min(100.0f, std::max(-100.0f, i));
  }

  // Our math was calibrated for 60hz (16ms per frame);
  // adjust for other framerates...
  float timescale = static_cast<float>(elapsed_millisecs) / 16.0f;

  // If we've recently been told to suppress the gyro, zero these.
  // (prevents hitches when being restored, etc)
  if (!gyro_enabled_ || camera_gyro_explicitly_disabled_
      || (time_microsecs - last_suppress_gyro_time_ < 1000000)) {
    tilt = Vector3f{0.0, 0.0, 0.0};
  }

  float tilt_smoothing = 0.0f;
  tilt_smoothed_ =
      tilt_smoothing * tilt_smoothed_ + (1.0f - tilt_smoothing) * tilt;

  tilt_vel_ = tilt_smoothed_ * 3.0f;
  tilt_pos_ += tilt_vel_ * timescale;

  // Technically this will behave slightly differently at different time
  // scales, but it should be close to correct.. tilt_pos_ *= 0.991f;
  tilt_pos_ *= std::max(0.0f, 1.0f - 0.01f * timescale);

  // Some gyros seem wonky and either give us crazy big values or consistently
  // offset ones. Let's keep a running tally of magnitude that slowly drops
  // over time, and if it reaches a certain value lets just kill gyro input.
  if (gyro_broken_) {
    tilt_pos_ *= 0.0f;
  } else {
    gyro_mag_test_ += tilt_vel_.Length() * 0.01f * timescale;
    gyro_mag_test_ = std::max(0.0f, gyro_mag_test_ - 0.02f * timescale);
    if (gyro_mag_test_ > 100.0f) {
      g_base->ScreenMessage("Wonky gyro; disabling tilt.", {1, 0, 0});
      gyro_broken_ = true;
    }
  }
}

void Graphics::ApplyCamera(FrameDef* frame_def) {
  camera_->Update(frame_def->display_time_elapsed_millisecs());
  camera_->UpdatePosition();
  camera_->ApplyToFrameDef(frame_def);
}

void Graphics::DrawWorld(FrameDef* frame_def) {
  assert(!g_core->HeadlessMode());

  // Draw the world.
  overlay_node_z_depth_ = -0.95f;
  g_base->app_mode()->DrawWorld(frame_def);
  g_base->bg_dynamics->Draw(frame_def);

  // Lastly draw any blotches that have been building up.
  DrawBlotches(frame_def);

  // Add a few explicit things to a few passes.
  DrawBoxingGlovesTest(frame_def);
}

void Graphics::DrawUI(FrameDef* frame_def) {
  // Just do generic thing in our default implementation.
  // Special variants like GraphicsVR may do fancier stuff here.
  g_base->ui->Draw(frame_def);

  // We may want to see the virtual screen safe area.
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

  // g_core->logging->Log(LogName::kBa, LogLevel::kWarning, "DRAWING");

  // Keep track of when we're in here; can be useful for making sure stuff
  // doesn't muck with our lists/etc. while we're using them.
  assert(!building_frame_def_);
  building_frame_def_ = true;

  microsecs_t app_time_microsecs = g_core->AppTimeMicrosecs();

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

  // This probably should not be here. Though I guess we get the most
  // up-to-date values possible this way. But it should probably live in
  // g_input.
  UpdateGyro(app_time_microsecs, elapsed_microsecs);

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

    frame_def->set_needs_clear(!g_base->app_mode()->DoesWorldFillScreen());
    DrawWorld(frame_def);

    DrawUI(frame_def);

    // Let input draw anything it needs to (touch input graphics, etc).
    g_base->input->Draw(frame_def);

    RenderPass* overlay_pass = frame_def->overlay_pass();
    DrawMiscOverlays(frame_def);

    // Let UI draw dev console and whatever else.
    DrawDevUI(frame_def);

    // Draw our light/shadow images to the screen if desired.
    DrawDebugBuffers(overlay_pass);

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

  frame_def->Complete();

  // Include all mesh-data loads and unloads that have accumulated up to
  // this point the graphics thread will have to handle these before
  // rendering the frame_def.
  frame_def->set_mesh_data_creates(mesh_data_creates_);
  mesh_data_creates_.clear();
  frame_def->set_mesh_data_destroys(mesh_data_destroys_);
  mesh_data_destroys_.clear();

  g_base->graphics_server->EnqueueFrameDef(frame_def);

  // Clean up frame_defs awaiting deletion.
  ClearFrameDefDeleteList();

  // Clear our blotches out regardless of whether we rendered them.
  blotch_indices_.clear();
  blotch_verts_.clear();
  blotch_soft_indices_.clear();
  blotch_soft_verts_.clear();
  blotch_soft_obj_indices_.clear();
  blotch_soft_obj_verts_.clear();

  assert(building_frame_def_);
  building_frame_def_ = false;
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
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBoxingGlove));
      }
      c.Submit();
    }

    // Beauty.
    if (explicit_bool(false)) {
      ObjectComponent c(frame_def->beauty_pass());
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kBoxingGlove));
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.4f, 0.4f, 0.4f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(0.0f, 3.7f, -3.3f);
        c.Scale(10.0f, 10.0f, 10.0f);
        c.Rotate(a, 0.0f, 0.0f, 1.0f);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBoxingGlove));
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
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBoxingGlove));
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
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
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
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
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
    auto real_ms = core::CorePlatform::TimeMonotonicMillisecs();
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
      fade_cancel_last_real_ms_ = core::CorePlatform::TimeMonotonicMillisecs();
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
      float o = std::min(
          1.0f, (1.0f
                 - static_cast<float>(frame_time - progress_bar_end_time_)
                       / (static_cast<float>(kProgressBarFadeTime) * 0.5f)));
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

    // Ship this state when it changes and also every now and then just in
    // case things go wonky.
    if (new_cursor_visibility != hardware_cursor_visible_
        || app_time - last_cursor_visibility_event_time_ > 2.137) {
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
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCursor));
      {
        auto xf = c.ScopedTransform();

        // Note: we don't plug in known cursor position values here; we tell
        // the renderer to insert the latest values on its end; this can
        // lessen cursor lag substantially.
        c.CursorTranslate();
        c.Translate(csize * 0.40f, csize * -0.38f, kCursorZDepth);
        c.Scale(csize, csize);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
      }
      c.Submit();
    }
  }
}

void Graphics::DrawBlotches(FrameDef* frame_def) {
  if (!blotch_verts_.empty()) {
    if (!shadow_blotch_mesh_.exists()) {
      shadow_blotch_mesh_ = Object::New<SpriteMesh>();
    }
    shadow_blotch_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        blotch_indices_.size(), &blotch_indices_[0]));
    shadow_blotch_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        blotch_verts_.size(), &blotch_verts_[0]));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kLight));
    c.DrawMesh(shadow_blotch_mesh_.get());
    c.Submit();
  }
  if (!blotch_soft_verts_.empty()) {
    if (!shadow_blotch_soft_mesh_.exists()) {
      shadow_blotch_soft_mesh_ = Object::New<SpriteMesh>();
    }
    shadow_blotch_soft_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        blotch_soft_indices_.size(), &blotch_soft_indices_[0]));
    shadow_blotch_soft_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        blotch_soft_verts_.size(), &blotch_soft_verts_[0]));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kLightSoft));
    c.DrawMesh(shadow_blotch_soft_mesh_.get());
    c.Submit();
  }
  if (!blotch_soft_obj_verts_.empty()) {
    if (!shadow_blotch_soft_obj_mesh_.exists()) {
      shadow_blotch_soft_obj_mesh_ = Object::New<SpriteMesh>();
    }
    shadow_blotch_soft_obj_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        blotch_soft_obj_indices_.size(), &blotch_soft_obj_indices_[0]));
    shadow_blotch_soft_obj_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        blotch_soft_obj_verts_.size(), &blotch_soft_obj_verts_[0]));
    SpriteComponent c(frame_def->light_pass());
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kLightSoft));
    c.DrawMesh(shadow_blotch_soft_obj_mesh_.get());
    c.Submit();
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
  debug_draw_ = !debug_draw_;
  if (g_base->graphics_server->renderer()) {
    g_base->graphics_server->renderer()->set_debug_draw_mode(debug_draw_);
  }
}

void Graphics::ReleaseFadeEndCommand() { fade_end_call_.Clear(); }

auto Graphics::ValueTest(const std::string& arg, double* absval,
                         double* deltaval, double* outval) -> bool {
  return false;
}

void Graphics::DoDrawBlotch(std::vector<uint16_t>* indices,
                            std::vector<VertexSprite>* verts,
                            const Vector3f& pos, float size, float r, float g,
                            float b, float a) {
  assert(g_base->InLogicThread());
  assert(indices && verts);

  // Add verts.
  assert((*verts).size() < 65536);
  auto count = static_cast<uint16_t>((*verts).size());
  (*verts).resize(count + 4);
  {
    VertexSprite& p((*verts)[count]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 0;
    p.uv[1] = 0;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }
  {
    VertexSprite& p((*verts)[count + 1]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 0;
    p.uv[1] = 65535;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }
  {
    VertexSprite& p((*verts)[count + 2]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 65535;
    p.uv[1] = 0;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }
  {
    VertexSprite& p((*verts)[count + 3]);
    p.position[0] = pos.x;
    p.position[1] = pos.y;
    p.position[2] = pos.z;
    p.uv[0] = 65535;
    p.uv[1] = 65535;
    p.size = size;
    p.color[0] = r;
    p.color[1] = g;
    p.color[2] = b;
    p.color[3] = a;
  }

  // Add indices.
  {
    size_t i_count = (*indices).size();
    (*indices).resize(i_count + 6);
    uint16_t* i = &(*indices)[i_count];
    i[0] = count;
    i[1] = static_cast<uint16_t>(count + 1);
    i[2] = static_cast<uint16_t>(count + 2);
    i[3] = static_cast<uint16_t>(count + 1);
    i[4] = static_cast<uint16_t>(count + 3);
    i[5] = static_cast<uint16_t>(count + 2);
  }
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
    res_x_virtual_ = kBaseVirtualResX;
    res_y_virtual_ = kBaseVirtualResY;
  } else {
    res_x_virtual_ = res_x_;
    res_y_virtual_ = res_y_;
    CalcVirtualRes_(&res_x_virtual_, &res_y_virtual_);
  }

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
    -> SysCubeMapTextureID {
  switch (reflection_type) {
    case ReflectionType::kChar:
      return SysCubeMapTextureID::kReflectionChar;
    case ReflectionType::kPowerup:
      return SysCubeMapTextureID::kReflectionPowerup;
    case ReflectionType::kSoft:
      return SysCubeMapTextureID::kReflectionSoft;
    case ReflectionType::kSharp:
      return SysCubeMapTextureID::kReflectionSharp;
    case ReflectionType::kSharper:
      return SysCubeMapTextureID::kReflectionSharper;
    case ReflectionType::kSharpest:
      return SysCubeMapTextureID::kReflectionSharpest;
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
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kOverlayGuide));
    }
    c.Submit();
  }
}

}  // namespace ballistica::base
