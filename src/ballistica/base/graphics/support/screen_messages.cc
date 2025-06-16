// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/screen_messages.h"

#include <algorithm>
#include <string>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/base/graphics/text/text_graphics.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

const float kScreenMessageZDepth{-0.06f};

class ScreenMessages::ScreenMessageEntry {
 public:
  ScreenMessageEntry(std::string text, bool top_style, uint32_t c,
                     const Vector3f& color, TextureAsset* texture,
                     TextureAsset* tint_texture, const Vector3f& tint,
                     const Vector3f& tint2)
      : top_style(top_style),
        creation_time(c),
        s_raw(std::move(text)),
        color(color),
        texture(texture),
        tint_texture(tint_texture),
        tint(tint),
        tint2(tint2) {}
  auto GetText() -> TextGroup&;
  void UpdateTranslation();
  bool top_style;
  uint32_t creation_time;
  Vector3f color;
  Vector3f tint;
  Vector3f tint2;
  std::string s_raw;
  std::string s_translated;
  float str_width{};
  float str_height{};
  Object::Ref<TextureAsset> texture;
  Object::Ref<TextureAsset> tint_texture;
  float v_smoothed{};
  bool translation_dirty{true};
  bool mesh_dirty{true};
  millisecs_t smooth_time{};
  Object::Ref<NinePatchMesh> shadow_mesh_;

 private:
  Object::Ref<TextGroup> s_mesh_;
};

ScreenMessages::ScreenMessages() = default;

void ScreenMessages::DrawMiscOverlays(FrameDef* frame_def) {
  RenderPass* pass = frame_def->overlay_pass();

  // Screen messages (bottom).
  {
    // Delete old ones.
    if (!screen_messages_.empty()) {
      millisecs_t cutoff;
      if (g_core->AppTimeMillisecs() > 5000) {
        cutoff = g_core->AppTimeMillisecs() - 5000;
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
      bool vr = g_core->vr_mode();

      // These are less disruptive in the middle for menus but at the bottom
      // during gameplay.
      float start_v = g_base->graphics->screen_virtual_height() * 0.05f;
      float scale;
      switch (g_base->ui->uiscale()) {
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
        c.SetTexture(
            // g_base->assets->SysTexture(SysTextureID::kSoftRectVertical));
            g_base->assets->SysTexture(SysTextureID::kShadowSharp));

        float screen_width = g_base->graphics->screen_virtual_width();

        float v = start_v;

        millisecs_t youngest_age = 9999;

        for (auto i = screen_messages_.rbegin(); i != screen_messages_.rend();
             i++) {
          // Update the translation if need be.
          i->UpdateTranslation();

          // Don't actually need the text just yet but need shadow mesh
          // which is calculated as part of it.
          i->GetText();

          millisecs_t age = g_core->AppTimeMillisecs() - i->creation_time;
          youngest_age = std::min(youngest_age, age);
          float s_extra = 1.0f;
          if (age < 100) {
            s_extra = std::min(1.2f, 1.2f * (static_cast<float>(age) / 100.0f));
          } else if (age < 150) {
            s_extra =
                1.2f - 0.2f * ((150.0f - static_cast<float>(age)) / 50.0f);
          }

          float a;
          if (age > 3000) {
            a = 1.0f - static_cast<float>(age - 3000) / 2000;
          } else {
            a = 1;
          }
          a *= 0.7f;

          // if (vr) {
          //   a *= 0.8f;
          // }

          if (i->translation_dirty) {
            BA_LOG_ONCE(
                LogName::kBaGraphics, LogLevel::kWarning,
                "Found dirty translation on screenmessage draw pass 1; raw="
                    + i->s_raw);
          }

          float str_height = i->str_height;
          float str_width = i->str_width;

          if ((str_width * scale) > (screen_width - 40)) {
            s_extra *= ((screen_width - 40) / (str_width * scale));
          }

          float r = i->color.x;
          float g = i->color.y;
          float b = i->color.z;
          Graphics::GetSafeColor(&r, &g, &b);

          float v_extra = scale * (static_cast<float>(youngest_age) * 0.01f);

          float fade;
          if (age < 100) {
            fade = 1.0f;
          } else {
            // Don't fade ALL the way to black; leaves a tiny bit of color
            // showing which looks nice.
            fade = std::max(0.07f, (200.0f - static_cast<float>(age)) / 100.0f);
          }
          c.SetColor(r * fade, g * fade, b * fade, a);

          {
            auto xf = c.ScopedTransform();

            // This logic needs to run at a fixed hz or it breaks on high frame
            // rates.
            auto now_millisecs = pass->frame_def()->display_time_millisecs();
            i->smooth_time = std::max(i->smooth_time, now_millisecs - 100);
            while (i->smooth_time < now_millisecs) {
              i->smooth_time += 1000 / 60;
              if (i->v_smoothed == 0.0f) {
                i->v_smoothed = v + v_extra;
              } else {
                float smoothing = 0.8f;
                i->v_smoothed = smoothing * i->v_smoothed
                                + (1.0f - smoothing) * (v + v_extra);
              }
            }

            c.Translate(screen_width * 0.5f, i->v_smoothed,
                        vr ? 60 : kScreenMessageZDepth);

            // if (vr) {
            //   // Let's drop down a bit in vr mode.
            //   // c.Translate(0, -10.0f, 0);
            //   // c.Scale((str_width + 60) * scale * s_extra,
            //   //         (str_height + 20) * scale * s_extra);
            //   c.Scale(scale * s_extra, scale * s_extra);

            //   // Align our bottom with where we just scaled from.
            //   c.Translate(0, 0.5f, 0);
            {
              // c.Scale((str_width + 110) * scale * s_extra,
              //         (str_height + 40) * scale * s_extra);
              c.Scale(scale * s_extra, scale * s_extra);
              c.Translate(0, 20);

              // Align our bottom with where we just scaled from.
              c.Translate(0, 0.5f, 0);
            }
            // c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
            assert(i->shadow_mesh_.exists());
            c.DrawMesh(i->shadow_mesh_.get());
          }

          v += scale * (36 + str_height);
          if (v > g_base->graphics->screen_virtual_height() + 30) {
            break;
          }
        }
        c.Submit();
      }

      // Now the strings themselves.
      {
        SimpleComponent c(pass);
        c.SetTransparent(true);

        float screen_width = g_base->graphics->screen_virtual_width();
        float v = start_v;
        millisecs_t youngest_age = 9999;

        for (auto i = screen_messages_.rbegin(); i != screen_messages_.rend();
             i++) {
          millisecs_t age = g_core->AppTimeMillisecs() - i->creation_time;
          youngest_age = std::min(youngest_age, age);
          float s_extra = 1.0f;
          if (age < 100) {
            s_extra = std::min(1.2f, 1.2f * (static_cast<float>(age) / 100.0f));
          } else if (age < 150) {
            s_extra =
                1.2f - 0.2f * ((150.0f - static_cast<float>(age)) / 50.0f);
          }
          float a;
          if (age > 3000) {
            a = 1.0f - static_cast<float>(age - 3000) / 2000;
          } else {
            a = 1;
          }
          if (i->translation_dirty) {
            BA_LOG_ONCE(
                LogName::kBaGraphics, LogLevel::kWarning,
                "Found dirty translation on screenmessage draw pass 2; raw="
                    + i->s_raw);
          }
          float str_height = i->str_height;
          float str_width = i->str_width;

          if ((str_width * scale) > (screen_width - 40)) {
            s_extra *= ((screen_width - 40) / (str_width * scale));
          }
          float r = i->color.x;
          float g = i->color.y;
          float b = i->color.z;
          Graphics::GetSafeColor(&r, &g, &b, 0.85f);

          int elem_count = i->GetText().GetElementCount();
          for (int e = 0; e < elem_count; e++) {
            // Gracefully skip unloaded textures.
            TextureAsset* t = i->GetText().GetElementTexture(e);
            if (!t->preloaded()) {
              continue;
            }
            c.SetTexture(t);
            if (i->GetText().GetElementCanColor(e)) {
              c.SetColor(r, g, b, a);
            } else {
              c.SetColor(1, 1, 1, a);
            }
            c.SetFlatness(i->GetText().GetElementMaxFlatness(e));
            {
              auto xf = c.ScopedTransform();
              c.Translate(screen_width * 0.5f, i->v_smoothed,
                          vr ? 150 : kScreenMessageZDepth);
              c.Scale(scale * s_extra, scale * s_extra);
              c.Translate(0, 20);
              c.DrawMesh(i->GetText().GetElementMesh(e));
            }
          }

          v += scale * (36 + str_height);
          if (v > g_base->graphics->screen_virtual_height() + 30) {
            break;
          }
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
      if (g_core->AppTimeMillisecs() > 5000) {
        cutoff = g_core->AppTimeMillisecs() - 5000;
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
      float v = g_base->graphics->screen_virtual_height() - 50.0f;

      float v_base = g_base->graphics->screen_virtual_height();
      float last_v = -999.0f;

      float min_spacing = 25.0f;

      for (auto i = screen_messages_top_.rbegin();
           i != screen_messages_top_.rend(); i++) {
        // Update the translation if need be.
        i->UpdateTranslation();

        millisecs_t age = g_core->AppTimeMillisecs() - i->creation_time;
        float s_extra = 1.0f;
        if (age < 100) {
          s_extra = std::min(1.1f, 1.1f * (static_cast<float>(age) / 100.0f));
        } else if (age < 150) {
          s_extra = 1.1f - 0.1f * ((150.0f - static_cast<float>(age)) / 50.0f);
        }

        float a;
        if (age > 3000) {
          a = 1.0f - static_cast<float>(age - 3000) / 2000;
        } else {
          a = 1;
        }

        // This logic needs to run at a fixed hz or it breaks on high frame
        // rates.
        auto now_millisecs = pass->frame_def()->display_time_millisecs();
        i->smooth_time = std::max(i->smooth_time, now_millisecs - 100);
        while (i->smooth_time < now_millisecs) {
          i->smooth_time += 1000 / 60;
          i->v_smoothed += 0.1f;
          if (i->v_smoothed - last_v < min_spacing) {
            i->v_smoothed +=
                8.0f * (1.0f - ((i->v_smoothed - last_v) / min_spacing));
          }
        }
        last_v = i->v_smoothed;

        // Draw the image if they provided one.
        if (i->texture.exists()) {
          c.Submit();

          SimpleComponent c2(pass);
          c2.SetTransparent(true);
          c2.SetTexture(i->texture);
          if (i->tint_texture.exists()) {
            c2.SetColorizeTexture(i->tint_texture.get());
            c2.SetColorizeColor(i->tint.x, i->tint.y, i->tint.z);
            c2.SetColorizeColor2(i->tint2.x, i->tint2.y, i->tint2.z);
            c2.SetMaskTexture(
                g_base->assets->SysTexture(SysTextureID::kCharacterIconMask));
          }
          c2.SetColor(1, 1, 1, a);
          {
            auto xf = c2.ScopedTransform();
            c2.Translate(h - 14, v_base + 10 + i->v_smoothed,
                         kScreenMessageZDepth);
            c2.Scale(22.0f * s_extra, 22.0f * s_extra);
            c2.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
          }
          c2.Submit();
        }

        float r = i->color.x;
        float g = i->color.y;
        float b = i->color.z;
        Graphics::GetSafeColor(&r, &g, &b);

        int elem_count = i->GetText().GetElementCount();
        for (int e = 0; e < elem_count; e++) {
          // Gracefully skip unloaded textures.
          TextureAsset* t = i->GetText().GetElementTexture(e);
          if (!t->preloaded()) {
            continue;
          }
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
          {
            auto xf = c.ScopedTransform();
            c.Translate(h, v_base + 2 + i->v_smoothed, kScreenMessageZDepth);
            c.Scale(0.6f * s_extra, 0.6f * s_extra);
            c.DrawMesh(i->GetText().GetElementMesh(e));
          }
        }
        assert(!i->translation_dirty);
        v -= g_base->text_graphics->GetStringHeight(i->s_translated.c_str())
                 * 0.6f
             + 8.0f;
      }
      c.Submit();
    }
  }
}

void ScreenMessages::AddScreenMessage(const std::string& msg,
                                      const Vector3f& color, bool top,
                                      TextureAsset* texture,
                                      TextureAsset* tint_texture,
                                      const Vector3f& tint,
                                      const Vector3f& tint2) {
  assert(g_base->InLogicThread());

  // So we know we're always dealing with valid utf8.
  std::string m = Utils::GetValidUTF8(msg.c_str(), "ga9msg");

  if (top) {
    float start_v = -40.0f;
    if (!screen_messages_top_.empty()) {
      start_v = std::min(
          start_v,
          std::max(-100.0f, screen_messages_top_.back().v_smoothed - 25.0f));
    }
    screen_messages_top_.emplace_back(m, true, g_core->AppTimeMillisecs(),
                                      color, texture, tint_texture, tint,
                                      tint2);
    screen_messages_top_.back().v_smoothed = start_v;
  } else {
    screen_messages_.emplace_back(m, false, g_core->AppTimeMillisecs(), color,
                                  texture, tint_texture, tint, tint2);
  }
}

void ScreenMessages::Reset() {
  // Wipe out top screen messages since they might be using textures that are
  // being reset. Bottom ones are ok since they have no textures.
  screen_messages_top_.clear();
}

void ScreenMessages::ClearScreenMessageTranslations() {
  assert(g_base && g_base->InLogicThread());
  for (auto&& i : screen_messages_) {
    i.translation_dirty = true;
  }
  for (auto&& i : screen_messages_top_) {
    i.translation_dirty = true;
  }
}

auto ScreenMessages::ScreenMessageEntry::GetText() -> TextGroup& {
  if (translation_dirty) {
    BA_LOG_ONCE(
        LogName::kBaGraphics, LogLevel::kWarning,
        "Found dirty translation on screenmessage GetText; raw=" + s_raw);
  }
  if (!s_mesh_.exists()) {
    s_mesh_ = Object::New<TextGroup>();
    mesh_dirty = true;
  }
  if (mesh_dirty) {
    s_mesh_->SetText(
        s_translated,
        top_style ? TextMesh::HAlign::kLeft : TextMesh::HAlign::kCenter,
        TextMesh::VAlign::kBottom);

    str_width = g_base->text_graphics->GetStringWidth(s_translated.c_str());
    str_height = g_base->text_graphics->GetStringHeight(s_translated.c_str());

    if (!top_style) {
      float x_extend = 40.0f;
      float y_extend = 40.0f;
      float y_offset = -5.0f;
      float corner_radius = 60.0f;
      float width_fin = str_width + x_extend * 2.0f;
      float height_fin = str_height + y_extend * 2.0f;
      float x_border =
          NinePatchMesh::BorderForRadius(corner_radius, width_fin, height_fin);
      float y_border =
          NinePatchMesh::BorderForRadius(corner_radius, height_fin, width_fin);
      shadow_mesh_ = Object::New<NinePatchMesh>(
          -0.5f * width_fin, -y_extend + y_offset, 0.0f, width_fin, height_fin,
          x_border, y_border, x_border, y_border);
    }

    mesh_dirty = false;
  }
  return *s_mesh_;
}

void ScreenMessages::ScreenMessageEntry::UpdateTranslation() {
  if (translation_dirty) {
    s_translated = g_base->assets->CompileResourceString(s_raw);
    translation_dirty = false;
    mesh_dirty = true;
  }
}

}  // namespace ballistica::base
