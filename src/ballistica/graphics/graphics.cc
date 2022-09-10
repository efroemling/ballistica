// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/graphics.h"

#include "ballistica/app/app.h"
#include "ballistica/app/app_flavor.h"
#include "ballistica/dynamics/bg/bg_dynamics.h"
#include "ballistica/game/connection/connection_set.h"
#include "ballistica/game/connection/connection_to_client.h"
#include "ballistica/game/connection/connection_to_host.h"
#include "ballistica/game/session/session.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/camera.h"
#include "ballistica/graphics/component/empty_component.h"
#include "ballistica/graphics/component/object_component.h"
#include "ballistica/graphics/component/post_process_component.h"
#include "ballistica/graphics/component/simple_component.h"
#include "ballistica/graphics/component/special_component.h"
#include "ballistica/graphics/component/sprite_component.h"
#include "ballistica/graphics/gl/renderer_gl.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/net_graph.h"
#include "ballistica/graphics/text/text_graphics.h"
#include "ballistica/input/input.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_context_call.h"
#include "ballistica/scene/node/globals_node.h"
#include "ballistica/scene/scene.h"
#include "ballistica/ui/console.h"
#include "ballistica/ui/root_ui.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/root_widget.h"

namespace ballistica {

const float kScreenMessageZDepth{-0.06f};
const float kScreenMeshZDepth{-0.05f};
const float kProgressBarZDepth{0.0f};
const int kProgressBarFadeTime{500};
const float kDebugImgZDepth{-0.04f};
const float kCursorZDepth{-0.1f};

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

Graphics::Graphics() = default;
Graphics::~Graphics() = default;

void Graphics::SetGyroEnabled(bool enable) {
  // If we're turning back on, suppress gyro updates for a bit.
  if (enable && !gyro_enabled_) {
    last_suppress_gyro_time_ = GetRealTime();
  }
  gyro_enabled_ = enable;
}

void Graphics::UpdateProgressBarProgress(float target) {
  millisecs_t real_time = GetRealTime();
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
  millisecs_t real_time = GetRealTime();
  float amount = progress_bar_progress_;
  if (amount < 0) amount = 0;

  SimpleComponent c(pass);
  c.SetTransparent(true);
  float o = opacity;
  float delay = 0;

  // Fade in for the first 2 seconds if desired.
  if (progress_bar_fade_in_) {
    millisecs_t since_start = real_time - last_progress_bar_start_time_;
    if (since_start < delay) {
      o = 0.0f;
    } else if (since_start < 2000 + delay) {
      o *= (since_start - delay) / 2000.0f;
    }
  }

  // Fade out at the end.
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
  if (y < shadow_lower_bottom_) {  // NOLINT(bugprone-branch-clone)
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

class Graphics::ScreenMessageEntry {
 public:
  ScreenMessageEntry(std::string s_in, bool align_left_in, uint32_t c,
                     const Vector3f& color_in, Texture* texture_in,
                     Texture* tint_texture_in, const Vector3f& tint_in,
                     const Vector3f& tint2_in)
      : align_left(align_left_in),
        creation_time(c),
        s_raw(std::move(s_in)),
        color(color_in),
        texture(texture_in),
        tint_texture(tint_texture_in),
        tint(tint_in),
        tint2(tint2_in),
        v_smoothed(0.0f),
        translation_dirty(true),
        mesh_dirty(true) {}
  auto GetText() -> TextGroup&;
  void UpdateTranslation();
  bool align_left;
  uint32_t creation_time;
  Vector3f color;
  Vector3f tint;
  Vector3f tint2;
  std::string s_raw;
  std::string s_translated;
  Object::Ref<Texture> texture;
  Object::Ref<Texture> tint_texture;
  float v_smoothed;
  bool translation_dirty;
  bool mesh_dirty;

 private:
  Object::Ref<TextGroup> s_mesh_;
};

// Draw controls and things that lie on top of the action.
void Graphics::DrawMiscOverlays(RenderPass* pass) {
  // Every now and then, update our stats.
  while (GetRealTime() >= next_stat_update_time_) {
    if (GetRealTime() - next_stat_update_time_ > 1000) {
      next_stat_update_time_ = GetRealTime() + 1000;
    } else {
      next_stat_update_time_ += 1000;
    }
    int total_frames_rendered =
        g_graphics_server->renderer()->total_frames_rendered();
    last_fps_ = total_frames_rendered - last_total_frames_rendered_;
    last_total_frames_rendered_ = total_frames_rendered;
  }
  float v{};

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
    if (IsVRMode()) {
      c.SetColor(1, 1, 1, 1);
    } else {
      c.SetColor(0.8f, 0.8f, 0.8f, 1.0f);
    }
    int text_elem_count = fps_text_group_->GetElementCount();
    for (int e = 0; e < text_elem_count; e++) {
      c.SetTexture(fps_text_group_->GetElementTexture(e));
      if (IsVRMode()) {
        c.SetShadow(-0.003f * fps_text_group_->GetElementUScale(e),
                    -0.003f * fps_text_group_->GetElementVScale(e), 0.0f, 1.0f);
        c.SetMaskUV2Texture(fps_text_group_->GetElementMaskUV2Texture(e));
      }
      c.SetFlatness(1.0f);
      c.DrawMesh(fps_text_group_->GetElementMesh(e));
    }
    c.Submit();
  }

  if (show_net_info_) {
    char net_info_str[128];
    int64_t in_count = 0;
    int64_t in_size = 0;
    int64_t in_size_compressed = 0;
    int64_t outCount = 0;
    int64_t out_size = 0;
    int64_t out_size_compressed = 0;
    int64_t resends = 0;
    int64_t resends_size = 0;
    bool do_ping = false;
    float ping{};
    bool show = false;

    // Add in/out data for any host connection.
    if (ConnectionToHost* connection_to_host =
            g_game->connections()->connection_to_host()) {
      if (connection_to_host->can_communicate()) show = true;
      in_size += connection_to_host->GetBytesInPerSecond();
      in_size_compressed += connection_to_host->GetBytesInPerSecondCompressed();
      in_count += connection_to_host->GetMessagesInPerSecond();
      out_size += connection_to_host->GetBytesOutPerSecond();
      out_size_compressed +=
          connection_to_host->GetBytesOutPerSecondCompressed();
      outCount += connection_to_host->GetMessagesOutPerSecond();
      resends += connection_to_host->GetMessageResendsPerSecond();
      resends_size += connection_to_host->GetBytesResentPerSecond();
      ping = connection_to_host->average_ping();
    } else {
      int connected_count = 0;
      for (auto&& i : g_game->connections()->connections_to_clients()) {
        ConnectionToClient* client = i.second.get();
        if (client->can_communicate()) {
          show = true;
          connected_count += 1;
        }
        in_size += client->GetBytesInPerSecond();
        in_size_compressed += client->GetBytesInPerSecondCompressed();
        in_count += client->GetMessagesInPerSecond();
        out_size += client->GetBytesOutPerSecond();
        out_size_compressed += client->GetBytesOutPerSecondCompressed();
        outCount += client->GetMessagesOutPerSecond();
        resends += client->GetMessageResendsPerSecond();
        resends_size += client->GetBytesResentPerSecond();
        ping += client->average_ping();
      }

      // We want an average for ping.
      if (connected_count > 0) {
        ping /= static_cast<float>(connected_count);
      }
    }

    if (show) {
      if (do_ping) {
        snprintf(net_info_str, sizeof(net_info_str),
                 "ping: %f\nin:   %d/%d/%d\nout: %d/%d/%d\nrpt: "
                 "%d/%d",
                 ping, static_cast_check_fit<int>(in_size),
                 static_cast_check_fit<int>(in_size_compressed),
                 static_cast_check_fit<int>(in_count),
                 static_cast_check_fit<int>(out_size),
                 static_cast_check_fit<int>(out_size_compressed),
                 static_cast_check_fit<int>(outCount),
                 static_cast_check_fit<int>(resends_size),
                 static_cast_check_fit<int>(resends));
      } else {
        snprintf(net_info_str, sizeof(net_info_str),
                 "in:   %d/%d/%d\nout: %d/%d/%d\nrpt: %d/%d",
                 static_cast_check_fit<int>(in_size),
                 static_cast_check_fit<int>(in_size_compressed),
                 static_cast_check_fit<int>(in_count),
                 static_cast_check_fit<int>(out_size),
                 static_cast_check_fit<int>(out_size_compressed),
                 static_cast_check_fit<int>(outCount),
                 static_cast_check_fit<int>(resends_size),
                 static_cast_check_fit<int>(resends));
      }
      net_info_str[sizeof(net_info_str) - 1] = 0;  // in case we overran..
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
        c.PushTransform();
        c.Translate(4.0f,
                    (show_fps_ ? 66.0f : 40.0f) + (do_ping ? 17.0f : 0.0f),
                    kScreenMessageZDepth);
        c.Scale(0.7f, 0.7f);
        c.DrawMesh(net_info_text_group_->GetElementMesh(e));
        c.PopTransform();
      }
      c.Submit();
    }
  }

  // Draw any debug graphs.
  {
    float debug_graph_y = 50.0;
    auto now = GetRealTime();
    for (auto it = debug_graphs_.begin(); it != debug_graphs_.end();) {
      assert(it->second.exists());
      if (now - it->second->LastUsedTime() > 1000) {
        it = debug_graphs_.erase(it);
      } else {
        it->second->Draw(pass, GetRealTime(), 50.0f, debug_graph_y, 500.0f,
                         100.0f);
        debug_graph_y += 110.0f;

        ++it;
      }
    }
  }

  // Screen messages (bottom).
  {
    // Delete old ones.
    if (!screen_messages_.empty()) {
      millisecs_t cutoff;
      if (GetRealTime() > 5000) {
        cutoff = GetRealTime() - 5000;
        for (auto i = screen_messages_.begin(); i != screen_messages_.end();) {
          if (i->creation_time < cutoff) {
            auto next = i;
            next++;
            screen_messages_.erase(i);
            i = next;
          } else {
            i++;
          }
        }
      }
    }

    // Delete if we have too many.
    while ((screen_messages_.size()) > 4) {
      screen_messages_.erase(screen_messages_.begin());
    }

    // Draw all existing.
    if (!screen_messages_.empty()) {
      bool vr = IsVRMode();

      // These are less disruptive in the middle for menus but at the bottom
      // during gameplay.
      float start_v = g_graphics->screen_virtual_height() * 0.05f;
      float scale;
      switch (g_ui->scale()) {
        case UIScale::kSmall:
          scale = 1.5f;
          break;
        case UIScale::kMedium:
          scale = 1.2f;
          break;
        default:
          scale = 1.0f;
          break;
      }

      // Shadows.
      {
        SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetTexture(g_assets->GetTexture(SystemTextureID::kSoftRectVertical));

        float screen_width = g_graphics->screen_virtual_width();

        v = start_v;

        millisecs_t youngest_age = 9999;

        for (auto i = screen_messages_.rbegin(); i != screen_messages_.rend();
             i++) {
          // Update the translation if need be.
          i->UpdateTranslation();

          millisecs_t age = GetRealTime() - i->creation_time;
          youngest_age = std::min(youngest_age, age);
          float s_extra = 1.0f;
          if (age < 100) {
            s_extra = std::min(1.2f, 1.2f * (age / 100.0f));
          } else if (age < 150) {
            s_extra = 1.2f - 0.2f * ((150.0f - age) / 50.0f);
          }

          float a;
          if (age > 3000) {
            a = 1.0f - static_cast<float>(age - 3000) / 2000;
          } else {
            a = 1;
          }
          a *= 0.8f;

          if (vr) {
            a *= 0.8f;
          }

          assert(!i->translation_dirty);
          float str_height =
              g_text_graphics->GetStringHeight(i->s_translated.c_str());
          float str_width =
              g_text_graphics->GetStringWidth(i->s_translated.c_str());

          if ((str_width * scale) > (screen_width - 40)) {
            s_extra *= ((screen_width - 40) / (str_width * scale));
          }

          float r = i->color.x;
          float g = i->color.y;
          float b = i->color.z;
          GetSafeColor(&r, &g, &b);

          float v_extra = scale * (youngest_age * 0.01f);

          float fade;
          if (age < 100) {
            fade = 1.0f;
          } else {
            fade = std::max(0.0f, (200.0f - age) / 100.0f);
          }
          c.SetColor(r * fade, g * fade, b * fade, a);

          c.PushTransform();
          if (i->v_smoothed == 0.0f) {
            i->v_smoothed = v + v_extra;
          } else {
            float smoothing = 0.8f;
            i->v_smoothed =
                smoothing * i->v_smoothed + (1.0f - smoothing) * (v + v_extra);
          }
          c.Translate(screen_width * 0.5f, i->v_smoothed,
                      vr ? 60 : kScreenMessageZDepth);
          if (vr) {
            // Let's drop down a bit in vr mode.
            c.Translate(0, -10.0f, 0);
            c.Scale((str_width + 60) * scale * s_extra,
                    (str_height + 20) * scale * s_extra);

            // Align our bottom with where we just scaled from.
            c.Translate(0, 0.5f, 0);
          } else {
            c.Scale((str_width + 110) * scale * s_extra,
                    (str_height + 40) * scale * s_extra);

            // Align our bottom with where we just scaled from.
            c.Translate(0, 0.5f, 0);
          }
          c.DrawModel(g_assets->GetModel(SystemModelID::kImage1x1));
          c.PopTransform();

          v += scale * (36 + str_height);
          if (v > g_graphics->screen_virtual_height() + 30) {
            break;
          }
        }
        c.Submit();
      }

      // Now the strings themselves.
      {
        SimpleComponent c(pass);
        c.SetTransparent(true);

        float screen_width = g_graphics->screen_virtual_width();
        v = start_v;
        millisecs_t youngest_age = 9999;

        for (auto i = screen_messages_.rbegin(); i != screen_messages_.rend();
             i++) {
          millisecs_t age = GetRealTime() - i->creation_time;
          youngest_age = std::min(youngest_age, age);
          float s_extra = 1.0f;
          if (age < 100) {
            s_extra = std::min(1.2f, 1.2f * (age / 100.0f));
          } else if (age < 150) {
            s_extra = 1.2f - 0.2f * ((150.0f - age) / 50.0f);
          }
          float a;
          if (age > 3000) {
            a = 1.0f - static_cast<float>(age - 3000) / 2000;
          } else {
            a = 1;
          }
          assert(!i->translation_dirty);
          float str_height =
              g_text_graphics->GetStringHeight(i->s_translated.c_str());
          float str_width =
              g_text_graphics->GetStringWidth(i->s_translated.c_str());

          if ((str_width * scale) > (screen_width - 40)) {
            s_extra *= ((screen_width - 40) / (str_width * scale));
          }
          float r = i->color.x;
          float g = i->color.y;
          float b = i->color.z;
          GetSafeColor(&r, &g, &b, 0.85f);

          int elem_count = i->GetText().GetElementCount();
          for (int e = 0; e < elem_count; e++) {
            // Gracefully skip unloaded textures.
            TextureData* t = i->GetText().GetElementTexture(e);
            if (!t->preloaded()) continue;
            c.SetTexture(t);
            if (i->GetText().GetElementCanColor(e)) {
              c.SetColor(r, g, b, a);
            } else {
              c.SetColor(1, 1, 1, a);
            }
            c.SetFlatness(i->GetText().GetElementMaxFlatness(e));
            c.PushTransform();
            c.Translate(screen_width * 0.5f, i->v_smoothed,
                        vr ? 150 : kScreenMessageZDepth);
            c.Scale(scale * s_extra, scale * s_extra);
            c.Translate(0, 20);
            c.DrawMesh(i->GetText().GetElementMesh(e));
            c.PopTransform();
          }

          v += scale * (36 + str_height);
          if (v > g_graphics->screen_virtual_height() + 30) break;
        }
        c.Submit();
      }
    }
  }

  // Screen messages (top).
  {
    // Delete old ones.
    if (!screen_messages_top_.empty()) {
      millisecs_t cutoff;
      if (GetRealTime() > 5000) {
        cutoff = GetRealTime() - 5000;
        for (auto i = screen_messages_top_.begin();
             i != screen_messages_top_.end();) {
          if (i->creation_time < cutoff) {
            auto next = i;
            next++;
            screen_messages_top_.erase(i);
            i = next;
          } else {
            i++;
          }
        }
      }
    }

    // Delete if we have too many.
    while ((screen_messages_top_.size()) > 6) {
      screen_messages_top_.erase(screen_messages_top_.begin());
    }

    if (!screen_messages_top_.empty()) {
      SimpleComponent c(pass);
      c.SetTransparent(true);

      // Draw all existing.
      float h = pass->virtual_width() - 300.0f;
      v = g_graphics->screen_virtual_height() - 50.0f;

      float v_base = g_graphics->screen_virtual_height();
      float last_v = -999.0f;

      float min_spacing = 25.0f;

      for (auto i = screen_messages_top_.rbegin();
           i != screen_messages_top_.rend(); i++) {
        // Update the translation if need be.
        i->UpdateTranslation();

        millisecs_t age = GetRealTime() - i->creation_time;
        float s_extra = 1.0f;
        if (age < 100) {
          s_extra = std::min(1.1f, 1.1f * (age / 100.0f));
        } else if (age < 150) {
          s_extra = 1.1f - 0.1f * ((150.0f - age) / 50.0f);
        }

        float a;
        if (age > 3000) {
          a = 1.0f - static_cast<float>(age - 3000) / 2000;
        } else {
          a = 1;
        }

        i->v_smoothed += 0.1f;
        if (i->v_smoothed - last_v < min_spacing) {
          i->v_smoothed +=
              8.0f * (1.0f - ((i->v_smoothed - last_v) / min_spacing));
        }
        last_v = i->v_smoothed;

        // Draw the image if they provided one.
        if (i->texture.exists()) {
          c.Submit();

          SimpleComponent c2(pass);
          c2.SetTransparent(true);
          c2.SetTexture(i->texture);
          if (i->tint_texture.exists()) {
            c2.SetColorizeTexture(i->tint_texture);
            c2.SetColorizeColor(i->tint.x, i->tint.y, i->tint.z);
            c2.SetColorizeColor2(i->tint2.x, i->tint2.y, i->tint2.z);
            c2.SetMaskTexture(
                g_assets->GetTexture(SystemTextureID::kCharacterIconMask));
          }
          c2.SetColor(1, 1, 1, a);
          c2.PushTransform();
          c2.Translate(h - 14, v_base + 10 + i->v_smoothed,
                       kScreenMessageZDepth);
          c2.Scale(22.0f * s_extra, 22.0f * s_extra);
          c2.DrawModel(g_assets->GetModel(SystemModelID::kImage1x1));
          c2.PopTransform();
          c2.Submit();
        }

        float r = i->color.x;
        float g = i->color.y;
        float b = i->color.z;
        GetSafeColor(&r, &g, &b);

        int elem_count = i->GetText().GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          // Gracefully skip unloaded textures.
          TextureData* t = i->GetText().GetElementTexture(e);
          if (!t->preloaded()) continue;
          c.SetTexture(t);
          if (i->GetText().GetElementCanColor(e)) {
            c.SetColor(r, g, b, a);
          } else {
            c.SetColor(1, 1, 1, a);
          }
          c.SetShadow(-0.003f * i->GetText().GetElementUScale(e),
                      -0.003f * i->GetText().GetElementVScale(e), 0.0f,
                      1.0f * a);
          c.SetFlatness(i->GetText().GetElementMaxFlatness(e));
          c.SetMaskUV2Texture(i->GetText().GetElementMaskUV2Texture(e));
          c.PushTransform();
          c.Translate(h, v_base + 2 + i->v_smoothed, kScreenMessageZDepth);
          c.Scale(0.6f * s_extra, 0.6f * s_extra);
          c.DrawMesh(i->GetText().GetElementMesh(e));
          c.PopTransform();
        }
        assert(!i->translation_dirty);
        v -= g_text_graphics->GetStringHeight(i->s_translated.c_str()) * 0.6f
             + 8.0f;
      }
      c.Submit();
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
  debug_graphs_[name]->SetLastUsedTime(GetRealTime());
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

  // We may still be short of our target intensity due to clamping (ie: (10,0,0)
  // will not look any brighter than (1,0,0)) if that's the case, just convert
  // the difference to a grey value and add that to all channels... this *still*
  // might not get us there so lets do it a few times if need be.  (i'm sure
  // there's a less bone-headed way to do this)
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

void Graphics::AddScreenMessage(const std::string& msg, const Vector3f& color,
                                bool top, Texture* texture,
                                Texture* tint_texture, const Vector3f& tint,
                                const Vector3f& tint2) {
  // So we know we're always dealing with valid utf8.
  std::string m = Utils::GetValidUTF8(msg.c_str(), "ga9msg");

  assert(InLogicThread());
  if (top) {
    float start_v = -40.0f;
    if (!screen_messages_top_.empty()) {
      start_v = std::min(
          start_v,
          std::max(-100.0f, screen_messages_top_.back().v_smoothed - 25.0f));
    }
    screen_messages_top_.emplace_back(m, true, GetRealTime(), color, texture,
                                      tint_texture, tint, tint2);
    screen_messages_top_.back().v_smoothed = start_v;
  } else {
    screen_messages_.emplace_back(m, false, GetRealTime(), color, texture,
                                  tint_texture, tint, tint2);
  }
}

void Graphics::Reset() {
  fade_ = 0;
  fade_start_ = 0;

  if (!camera_.exists()) {
    camera_ = Object::New<Camera>();
  }

  // Wipe out top screen messages since they might be using textures that are
  // being reset. Bottom ones are ok since they have no textures.
  screen_messages_top_.clear();
}

void Graphics::InitInternalComponents(FrameDef* frame_def) {
  RenderPass* pass = frame_def->GetOverlayFlatPass();

  screen_mesh_ = Object::New<ImageMesh>();

  // Let's draw a bit bigger than screen to account for tv-border-mode.
  float w = pass->virtual_width();
  float h = pass->virtual_height();
  if (IsVRMode()) {
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
  assert(InLogicThread());
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

void Graphics::ClearFrameDefDeleteList() {
  assert(InLogicThread());
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
  // If there's an ourstanding fade-end command, go ahead and run it.
  // (otherwise, overlapping fades can cause things to get lost)
  if (fade_end_call_.exists()) {
    if (g_buildconfig.debug_build()) {
      Log("WARNING: 2 fades overlapping; running first fade-end-call early");
    }
    g_game->PushPythonCall(fade_end_call_);
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
  if (g_assets->GetGraphicalPendingLoadCount() > 0) {
    c.SetColor(0.2f, 0, 0, 1);
  } else {
    c.SetColor(0, 0.2f, 0, 1);
  }
  c.DrawMesh(load_dot_mesh_.get());
  c.Submit();
}

void Graphics::UpdateGyro(millisecs_t real_time, millisecs_t elapsed) {
  Vector3f tilt = gyro_vals_;

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
  float timescale = static_cast<float>(elapsed) / 16.0f;

  // If we've recently been told to suppress the gyro, zero these.
  // (prevents hitches when being restored, etc)
  if (!gyro_enabled_ || camera_gyro_explicitly_disabled_
      || (real_time - last_suppress_gyro_time_ < 1000)) {
    tilt = Vector3f{0.0, 0.0, 0.0};
  }

  float tilt_smoothing = 0.0f;
  tilt_smoothed_ =
      tilt_smoothing * tilt_smoothed_ + (1.0f - tilt_smoothing) * tilt;

  tilt_vel_ = tilt_smoothed_ * 3.0f;
  tilt_pos_ += tilt_vel_ * timescale;

  // Technically this will behave slightly differently at different time scales,
  // but it should be close to correct..
  // tilt_pos_ *= 0.991f;
  tilt_pos_ *= std::max(0.0, 1.0f - 0.01 * timescale);

  // Some gyros seem wonky and either give us crazy big values or consistently
  // offset ones. Let's keep a running tally of magnitude that slowly drops over
  // time, and if it reaches a certain value lets just kill gyro input.
  if (gyro_broken_) {
    tilt_pos_ *= 0.0f;
  } else {
    gyro_mag_test_ += tilt_vel_.Length() * 0.01f * timescale;
    gyro_mag_test_ = std::max(0.0f, gyro_mag_test_ - 0.02f * timescale);
    if (gyro_mag_test_ > 100.0f) {
      ScreenMessage("Wonky gyro; disabling tilt.", {1, 0, 0});
      gyro_broken_ = true;
    }
  }
}

void Graphics::ApplyCamera(FrameDef* frame_def) {
  camera_->Update(frame_def->base_time_elapsed());
  camera_->UpdatePosition();
  camera_->ApplyToFrameDef(frame_def);
}

void Graphics::DrawWorld(Session* session, FrameDef* frame_def) {
  // Draw all session contents (nodes, etc.)
  overlay_node_z_depth_ = -0.95f;
  if (session) {
    session->Draw(frame_def);
    frame_def->set_benchmark_type(session->benchmark_type());
  }
  if (!HeadlessMode()) {
    g_bg_dynamics->Draw(frame_def);
  }

  // Lastly draw any blotches that have been building up.
  DrawBlotches(frame_def);

  // Add a few explicit things to a few passes.
  DrawBoxingGlovesTest(frame_def);
}

void Graphics::BuildAndPushFrameDef() {
  assert(InLogicThread());
  assert(camera_.exists());

  // We should not be building/pushing any frames until after
  // app-launch-commands have been run..
  BA_PRECONDITION_FATAL(g_game->ran_app_launch_commands());

  // This should no longer be necessary..
  WaitForRendererToExist();

  Session* session = g_game->GetForegroundSession();
  bool session_fills_screen = session ? session->DoesFillScreen() : false;
  millisecs_t real_time = GetRealTime();

  // Store how much time this frame_def represents.
  millisecs_t net_time = g_game->master_time();
  millisecs_t elapsed =
      std::min(millisecs_t{50}, net_time - last_create_frame_def_time_);
  last_create_frame_def_time_ = net_time;

  UpdateGyro(real_time, elapsed);

  FrameDef* frame_def = GetEmptyFrameDef();
  frame_def->set_real_time(real_time);
  frame_def->set_base_time(g_game->master_time());
  frame_def->set_base_time_elapsed(elapsed);
  frame_def->set_frame_number(frame_def_count_++);

  if (!internal_components_inited_) {
    InitInternalComponents(frame_def);
    internal_components_inited_ = true;
  }

  ApplyCamera(frame_def);

  // Clear to black for either progress bar or when we've got no meaningful
  // session to draw.
  frame_def->set_needs_clear(progress_bar_ || !session_fills_screen);

  if (progress_bar_) {
    UpdateAndDrawProgressBar(frame_def, real_time);
  } else {
    // Ok, we're drawing a real frame.

    DrawWorld(session, frame_def);

    // Now some overlay stuff.
    RenderPass* overlay_pass = frame_def->overlay_pass();

    DrawUI(frame_def);

    // Let input draw anything it needs to. (touch input graphics, etc)
    g_input->Draw(frame_def);

    DrawMiscOverlays(overlay_pass);

    // Draw console.
    if (!HeadlessMode() && g_app->console) {
      g_app->console->Draw(overlay_pass);
    }

    DrawCursor(overlay_pass, real_time);

    // Draw our light/shadow images to the screen if desired.
    DrawDebugBuffers(overlay_pass);

    // In high-quality modes we draw a screen-quad as a catch-all for blitting
    // the world buffer to the screen (other nodes can add their own blitters
    // such as distortion shapes which will have priority).
    if (frame_def->quality() >= GraphicsQuality::kHigh) {
      PostProcessComponent c(frame_def->blit_pass());
      c.DrawScreenQuad();
      c.Submit();
    }

    DrawFades(frame_def, real_time);

    // Sanity test: If we're in VR, the only reason we should have stuff in the
    // flat overlay pass is if there's windows present (we want to avoid
    // drawing/blitting the 2d UI buffer during gameplay for efficiency).
    if (IsVRMode()) {
      if (frame_def->GetOverlayFlatPass()->HasDrawCommands()) {
        if (!g_ui->IsWindowPresent()) {
          BA_LOG_ONCE(
              "Drawing in overlay pass in VR mode without UI; shouldn't "
              "happen!");
        }
      }
    }

    if (g_assets->GetPendingLoadCount() > 0) {
      DrawLoadDot(overlay_pass);
    }

    // Lastly, if we had anything waiting to run until the progress bar was
    // gone, run it.
    g_python->RunCleanFrameCommands();
  }

  frame_def->Finalize();

  // Include all mesh-data loads and unloads that have accumulated up to this
  // point the graphics thread will have to handle these before rendering the
  // frame_def.
  frame_def->set_mesh_data_creates(mesh_data_creates_);
  mesh_data_creates_.clear();
  frame_def->set_mesh_data_destroys(mesh_data_destroys_);
  mesh_data_destroys_.clear();

  g_graphics_server->SetFrameDef(frame_def);

  // Clean up frame_defs awaiting deletion.
  ClearFrameDefDeleteList();

  // Clear our blotches out regardless of whether we rendered them.
  blotch_indices_.clear();
  blotch_verts_.clear();
  blotch_soft_indices_.clear();
  blotch_soft_verts_.clear();
  blotch_soft_obj_indices_.clear();
  blotch_soft_obj_verts_.clear();
}

auto Graphics::DrawUI(FrameDef* frame_def) -> void { g_ui->Draw(frame_def); }

void Graphics::DrawBoxingGlovesTest(FrameDef* frame_def) {
  // Test: boxing glove.
  if (explicit_bool(false)) {
    float a = 0;

    // Blit.
    if (explicit_bool(true)) {
      PostProcessComponent c(frame_def->blit_pass());
      c.setNormalDistort(0.07f);
      c.PushTransform();
      c.Translate(0, 7, -3.3f);
      c.Scale(10, 10, 10);
      c.Rotate(a, 0, 0, 1);
      c.DrawModel(g_assets->GetModel(SystemModelID::kBoxingGlove));
      c.PopTransform();
      c.Submit();
    }

    // Beauty.
    if (explicit_bool(false)) {
      ObjectComponent c(frame_def->beauty_pass());
      c.SetTexture(g_assets->GetTexture(SystemTextureID::kBoxingGlove));
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.4f, 0.4f, 0.4f);
      c.PushTransform();
      c.Translate(0.0f, 3.7f, -3.3f);
      c.Scale(10.0f, 10.0f, 10.0f);
      c.Rotate(a, 0.0f, 0.0f, 1.0f);
      c.DrawModel(g_assets->GetModel(SystemModelID::kBoxingGlove));
      c.PopTransform();
      c.Submit();
    }

    // Light.
    if (explicit_bool(true)) {
      SimpleComponent c(frame_def->light_shadow_pass());
      c.SetColor(0.16f, 0.11f, 0.1f, 1.0f);
      c.SetTransparent(true);
      c.PushTransform();
      c.Translate(0.0f, 3.7f, -3.3f);
      c.Scale(10.0f, 10.0f, 10.0f);
      c.Rotate(a, 0.0f, 0.0f, 1.0f);
      c.DrawModel(g_assets->GetModel(SystemModelID::kBoxingGlove));
      c.PopTransform();
      c.Submit();
    }
  }
}

void Graphics::DrawDebugBuffers(RenderPass* pass) {
  if (explicit_bool(false)) {
    {
      SpecialComponent c(pass, SpecialComponent::Source::kLightBuffer);
      float csize = 100;
      c.PushTransform();
      c.Translate(70, 400, kDebugImgZDepth);
      c.Scale(csize, csize);
      c.DrawModel(g_assets->GetModel(SystemModelID::kImage1x1));
      c.PopTransform();
      c.Submit();
    }
    {
      SpecialComponent c(pass, SpecialComponent::Source::kLightShadowBuffer);
      float csize = 100;
      c.PushTransform();
      c.Translate(70, 250, kDebugImgZDepth);
      c.Scale(csize, csize);
      c.DrawModel(g_assets->GetModel(SystemModelID::kImage1x1));
      c.PopTransform();
      c.Submit();
    }
  }
}

void Graphics::UpdateAndDrawProgressBar(FrameDef* frame_def,
                                        millisecs_t real_time) {
  RenderPass* pass = frame_def->overlay_pass();
  UpdateProgressBarProgress(
      1.0f
      - static_cast<float>(g_assets->GetGraphicalPendingLoadCount())
            / static_cast<float>(progress_bar_loads_));
  DrawProgressBar(pass, 1.0f);

  // If we were drawing a progress bar, see if everything is now loaded.. if
  // so, start rendering normally next frame.
  int count = g_assets->GetGraphicalPendingLoadCount();
  if (count <= 0) {
    progress_bar_ = false;
    progress_bar_end_time_ = real_time;
  }
  if (g_assets->GetPendingLoadCount() > 0) {
    DrawLoadDot(pass);
  }
}

void Graphics::DrawFades(FrameDef* frame_def, millisecs_t real_time) {
  RenderPass* overlay_pass = frame_def->overlay_pass();

  // Guard against accidental fades that never fade back in.
  if (fade_ <= 0.0f && fade_out_) {
    millisecs_t faded_time = real_time - (fade_start_ + fade_time_);
    if (faded_time > 15000) {
      Log("FORCE-ENDING STUCK FADE");
      fade_out_ = false;
      fade_ = 1.0f;
      fade_time_ = 1000;
      fade_start_ = real_time;
    }
  }

  // Update fade values.
  if (fade_ > 0) {
    if (set_fade_start_on_next_draw_) {
      set_fade_start_on_next_draw_ = false;
      fade_start_ = real_time;
    }
    bool was_done = fade_ <= 0;
    if (real_time <= fade_start_) {
      fade_ = 1;
    } else if ((real_time - fade_start_) < fade_time_) {
      fade_ = 1.0f
              - (static_cast<float>(real_time - fade_start_)
                 / static_cast<float>(fade_time_));
      if (fade_ <= 0) fade_ = 0.00001f;
    } else {
      fade_ = 0;
      if (!was_done && fade_end_call_.exists()) {
        g_game->PushPythonCall(fade_end_call_);
        fade_end_call_.Clear();
      }
    }
  }

  // Draw a fade if we're either in a fade or fading back in from a
  // progress-bar screen.
  if (fade_ > 0.00001f || fade_out_
      || (real_time - progress_bar_end_time_ < kProgressBarFadeTime)) {
    float a = fade_out_ ? 1 - fade_ : fade_;
    if (real_time - progress_bar_end_time_ < kProgressBarFadeTime) {
      a = 1.0f * a
          + (1.0f
             - static_cast<float>(real_time - progress_bar_end_time_)
                   / static_cast<float>(kProgressBarFadeTime))
                * (1.0f - a);
    }
    if (IsVRMode()) {
#if BA_VR_BUILD
      SimpleComponent c(frame_def->vr_cover_pass());
      c.SetTransparent(false);
      Vector3f cam_pt = {0.0f, 0.0f, 0.0f};
      Vector3f cam_target_pt = {0.0f, 0.0f, 0.0f};
      cam_pt =
          Vector3f(frame_def->cam_original().x, frame_def->cam_original().y,
                   frame_def->cam_original().z);
      // in vr follow-mode the cam point gets tweaked.. (fixme should probably
      // just do this on the camera end)
      if (frame_def->camera_mode() == CameraMode::kOrbit) {
        // fudge this one up a bit; looks better that way..
        cam_target_pt = Vector3f(frame_def->cam_target_original().x,
                                 frame_def->cam_target_original().y + 6.0f,
                                 frame_def->cam_target_original().z);
      } else {
        cam_target_pt = Vector3f(frame_def->cam_target_original().x,
                                 frame_def->cam_target_original().y,
                                 frame_def->cam_target_original().z);
      }
      Vector3f diff = cam_target_pt - cam_pt;
      diff.Normalize();
      Vector3f side = Vector3f::Cross(diff, Vector3f(0.0f, 1.0f, 0.0f));
      Vector3f up = Vector3f::Cross(diff, side);
      c.SetColor(0, 0, 0);
      c.PushTransform();
      // we start in vr-overlay screen space; get back to world..
      c.Translate(cam_pt.x, cam_pt.y, cam_pt.z);
      c.MultMatrix(Matrix44fOrient(diff, up).m);
      // at the very end we stay turned around so we get 100% black
      if (a < 0.98f) {
        c.Translate(0, 0, 40.0f * a);
        c.Rotate(180, 1, 0, 0);
      }
      float inv_a = 1.0f - a;
      float s = 100.0f * inv_a + 5.0f * a;
      c.Scale(s, s, s);
      c.DrawModel(g_assets->GetModel(SystemModelID::kVRFade));
      c.PopTransform();
      c.Submit();
#else   // BA_VR_BUILD
      throw Exception();
#endif  // BA_VR_BUILD
    } else {
      SimpleComponent c(overlay_pass);
      c.SetTransparent(a < 1.0f);
      c.SetColor(0, 0, 0, a);
      c.DrawMesh(screen_mesh_.get());
      c.Submit();
    }

    // If we're doing a progress-bar fade, throw in the fading progress bar.
    if (real_time - progress_bar_end_time_ < kProgressBarFadeTime / 2) {
      float o = (1.0f
                 - static_cast<float>(real_time - progress_bar_end_time_)
                       / (static_cast<float>(kProgressBarFadeTime) * 0.5f));
      UpdateProgressBarProgress(1.0f);
      DrawProgressBar(overlay_pass, o);
    }
  }
}

void Graphics::DrawCursor(RenderPass* pass, millisecs_t real_time) {
  assert(InLogicThread());

  bool can_show_cursor = g_platform->IsRunningOnDesktop();
  bool should_show_cursor = camera_->manual() || g_input->IsCursorVisible();

  if (g_buildconfig.hardware_cursor()) {
    // If we're using a hardware cursor, ship hardware cursor visibility
    // updates to the app thread periodically.
    bool new_cursor_visibility = false;
    if (can_show_cursor && should_show_cursor) {
      new_cursor_visibility = true;
    }

    // Ship this state when it changes and also every now and then just in
    // case things go wonky.
    if (new_cursor_visibility != hardware_cursor_visible_
        || real_time - last_cursor_visibility_event_time_ > 2000) {
      hardware_cursor_visible_ = new_cursor_visibility;
      last_cursor_visibility_event_time_ = real_time;
      g_app_flavor->PushCursorUpdate(hardware_cursor_visible_);
    }
  } else {
    // Draw software cursor.
    if (can_show_cursor && should_show_cursor) {
      SimpleComponent c(pass);
      c.SetTransparent(true);
      float csize = 50.0f;
      c.SetTexture(g_assets->GetTexture(SystemTextureID::kCursor));
      c.PushTransform();

      // Note: we don't plug in known cursor position values here; we tell the
      // renderer to insert the latest values on its end; this lessens cursor
      // lag substantially.
      c.CursorTranslate();
      c.Translate(csize * 0.44f, csize * -0.44f, kCursorZDepth);
      c.Scale(csize, csize);
      c.DrawModel(g_assets->GetModel(SystemModelID::kImage1x1));
      c.PopTransform();
      c.Submit();
    }
  }
}

void Graphics::DrawBlotches(FrameDef* frame_def) {
  if (!this->blotch_verts_.empty()) {
    if (!this->shadow_blotch_mesh_.exists())
      this->shadow_blotch_mesh_ = Object::New<SpriteMesh>();
    this->shadow_blotch_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        this->blotch_indices_.size(), &this->blotch_indices_[0]));
    this->shadow_blotch_mesh_->SetData(Object::New<MeshBuffer<VertexSprite>>(
        this->blotch_verts_.size(), &this->blotch_verts_[0]));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_assets->GetTexture(SystemTextureID::kLight));
    c.DrawMesh(this->shadow_blotch_mesh_.get());
    c.Submit();
  }
  if (!this->blotch_soft_verts_.empty()) {
    if (!this->shadow_blotch_soft_mesh_.exists())
      this->shadow_blotch_soft_mesh_ = Object::New<SpriteMesh>();
    this->shadow_blotch_soft_mesh_->SetIndexData(Object::New<MeshIndexBuffer16>(
        this->blotch_soft_indices_.size(), &this->blotch_soft_indices_[0]));
    this->shadow_blotch_soft_mesh_->SetData(
        Object::New<MeshBuffer<VertexSprite>>(this->blotch_soft_verts_.size(),
                                              &this->blotch_soft_verts_[0]));
    SpriteComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_assets->GetTexture(SystemTextureID::kLightSoft));
    c.DrawMesh(this->shadow_blotch_soft_mesh_.get());
    c.Submit();
  }
  if (!this->blotch_soft_obj_verts_.empty()) {
    if (!this->shadow_blotch_soft_obj_mesh_.exists()) {
      this->shadow_blotch_soft_obj_mesh_ = Object::New<SpriteMesh>();
    }
    this->shadow_blotch_soft_obj_mesh_->SetIndexData(
        Object::New<MeshIndexBuffer16>(this->blotch_soft_obj_indices_.size(),
                                       &this->blotch_soft_obj_indices_[0]));
    this->shadow_blotch_soft_obj_mesh_->SetData(
        Object::New<MeshBuffer<VertexSprite>>(
            this->blotch_soft_obj_verts_.size(),
            &this->blotch_soft_obj_verts_[0]));
    SpriteComponent c(frame_def->light_pass());
    c.SetTexture(g_assets->GetTexture(SystemTextureID::kLightSoft));
    c.DrawMesh(this->shadow_blotch_soft_obj_mesh_.get());
    c.Submit();
  }
}

void Graphics::SetSupportsHighQualityGraphics(bool s) {
  supports_high_quality_graphics_ = s;
  has_supports_high_quality_graphics_value_ = true;
}

void Graphics::ClearScreenMessageTranslations() {
  for (auto&& i : screen_messages_) {
    i.translation_dirty = true;
  }
  for (auto&& i : screen_messages_top_) {
    i.translation_dirty = true;
  }
}

void Graphics::ReturnCompletedFrameDef(FrameDef* frame_def) {
  std::scoped_lock lock(frame_def_delete_list_mutex_);
  g_graphics->frame_def_delete_list_.push_back(frame_def);
}

void Graphics::AddMeshDataCreate(MeshData* d) {
  assert(InLogicThread());
  assert(g_graphics);

  // Add this to our list of new-mesh-datas. We'll include this with our
  // next frame_def to have the graphics thread load before it processes
  // the frame_def.
  mesh_data_creates_.push_back(d);
}

void Graphics::AddMeshDataDestroy(MeshData* d) {
  assert(InLogicThread());
  assert(g_graphics);

  // Add this to our list of delete-mesh-datas; we'll include this with our
  // next frame_def to have the graphics thread kill before it processes
  // the frame_def.
  mesh_data_destroys_.push_back(d);
}

void Graphics::EnableProgressBar(bool fade_in) {
  assert(InLogicThread());
  progress_bar_loads_ = g_assets->GetGraphicalPendingLoadCount();
  assert(progress_bar_loads_ >= 0);
  if (progress_bar_loads_ > 0) {
    progress_bar_ = true;
    progress_bar_fade_in_ = fade_in;
    last_progress_bar_draw_time_ = GetRealTime();
    last_progress_bar_start_time_ = last_progress_bar_draw_time_;
    progress_bar_progress_ = 0.0f;
  }
}

void Graphics::ToggleManualCamera() {
  assert(InLogicThread());
  camera_->SetManual(!camera_->manual());
  if (camera_->manual()) {
    ScreenMessage("Manual Camera On");
  } else {
    ScreenMessage("Manual Camera Off");
  }
}

void Graphics::LocalCameraShake(float mag) {
  assert(InLogicThread());
  if (camera_.exists()) {
    camera_->Shake(mag);
  }
}

void Graphics::ToggleNetworkDebugDisplay() {
  assert(InLogicThread());
  network_debug_display_enabled_ = !network_debug_display_enabled_;
  if (network_debug_display_enabled_) {
    ScreenMessage("Network Debug Display Enabled");
  } else {
    ScreenMessage("Network Debug Display Disabled");
  }
}

void Graphics::ToggleDebugDraw() {
  assert(InLogicThread());
  debug_draw_ = !debug_draw_;
  if (g_graphics_server->renderer()) {
    g_graphics_server->renderer()->set_debug_draw_mode(debug_draw_);
  }
}

void Graphics::ReleaseFadeEndCommand() { fade_end_call_.Clear(); }

void Graphics::WaitForRendererToExist() {
  // Conceivably we could hit this point before our graphics thread has created
  // the renderer. In that case lets wait a moment.
  int sleep_count = 0;
  while (g_graphics_server == nullptr
         || g_graphics_server->renderer() == nullptr) {
    BA_LOG_ONCE(
        "BuildAndPushFrameDef() called before renderer is up; spinning...");
    Platform::SleepMS(100);
    sleep_count++;
    if (sleep_count > 100) {
      throw Exception(
          "Aborting waiting for renderer to come up in BuildAndPushFrameDef()");
    }
  }
}

auto Graphics::ValueTest(const std::string& arg, double* absval,
                         double* deltaval, double* outval) -> bool {
  return false;
}

void Graphics::DoDrawBlotch(std::vector<uint16_t>* indices,
                            std::vector<VertexSprite>* verts,
                            const Vector3f& pos, float size, float r, float g,
                            float b, float a) {
  assert(InLogicThread());
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
  // FIXME - we're updating this every frame so we should use pure dynamic data;
  //  not a mix of static and dynamic.

  if (amt >= 0.999f) {
    // clang-format off
    uint16_t indices[] = {0, 1, 2, 1, 3, 2};
    VertexSimpleFull vertices[] = {
        {-1, -1, 0, 0, 65535},
        {1, -1, 0, 65535, 65535},
        {-1, 1, 0, 0, 0},
        {1, 1, 0, 65535, 0,
        }
    };
    // clang-format on
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

auto Graphics::ScreenMessageEntry::GetText() -> TextGroup& {
  assert(!translation_dirty);
  if (!s_mesh_.exists()) {
    s_mesh_ = Object::New<TextGroup>();
    mesh_dirty = true;
  }
  if (mesh_dirty) {
    s_mesh_->SetText(
        s_translated,
        align_left ? TextMesh::HAlign::kLeft : TextMesh::HAlign::kCenter,
        TextMesh::VAlign::kBottom);
    mesh_dirty = false;
  }
  return *s_mesh_;
}

void Graphics::ScreenResize(float virtual_width, float virtual_height,
                            float pixel_width, float pixel_height) {
  assert(InLogicThread());
  res_x_virtual_ = virtual_width;
  res_y_virtual_ = virtual_height;
  res_x_ = pixel_width;
  res_y_ = pixel_height;

  // Need to rebuild internal components (some are sized to the screen).
  internal_components_inited_ = false;
}

void Graphics::ScreenMessageEntry::UpdateTranslation() {
  if (translation_dirty) {
    s_translated = g_game->CompileResourceString(
        s_raw, "Graphics::ScreenMessageEntry::UpdateTranslation");
    translation_dirty = false;
    mesh_dirty = true;
  }
}

auto Graphics::CubeMapFromReflectionType(ReflectionType reflection_type)
    -> SystemCubeMapTextureID {
  switch (reflection_type) {
    case ReflectionType::kChar:
      return SystemCubeMapTextureID::kReflectionChar;
    case ReflectionType::kPowerup:
      return SystemCubeMapTextureID::kReflectionPowerup;
    case ReflectionType::kSoft:
      return SystemCubeMapTextureID::kReflectionSoft;
    case ReflectionType::kSharp:
      return SystemCubeMapTextureID::kReflectionSharp;
    case ReflectionType::kSharper:
      return SystemCubeMapTextureID::kReflectionSharper;
    case ReflectionType::kSharpest:
      return SystemCubeMapTextureID::kReflectionSharpest;
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

auto Graphics::ApplyGlobals(GlobalsNode* globals) -> void {
  set_floor_reflection(globals->floor_reflection());
  camera()->SetMode(globals->camera_mode());
  camera()->set_vr_offset(Vector3f(globals->vr_camera_offset()));
  camera()->set_happy_thoughts_mode(globals->happy_thoughts_mode());
  set_shadow_scale(globals->shadow_scale()[0], globals->shadow_scale()[1]);
  auto&& area_of_interest_bounds{globals->area_of_interest_bounds()};
  camera()->set_area_of_interest_bounds(
      area_of_interest_bounds[0], area_of_interest_bounds[1],
      area_of_interest_bounds[2], area_of_interest_bounds[3],
      area_of_interest_bounds[4], area_of_interest_bounds[5]);
  auto&& shadow_range{globals->shadow_range()};
  SetShadowRange(shadow_range[0], shadow_range[1], shadow_range[2],
                 shadow_range[3]);
  set_shadow_offset(Vector3f(globals->shadow_offset()));
  set_shadow_ortho(globals->shadow_ortho());
  set_tint(Vector3f(globals->tint()));

  set_ambient_color(Vector3f(globals->ambient_color()));
  set_vignette_outer(Vector3f(globals->vignette_outer()));
  set_vignette_inner(Vector3f(globals->vignette_inner()));
}

}  // namespace ballistica
