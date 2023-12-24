// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/shield_node.h"

#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/post_process_component.h"
#include "ballistica/base/graphics/component/shield_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::scene_v1 {

class ShieldNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS ShieldNode
  BA_NODE_CREATE_CALL(CreateShield);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ATTR(radius, radius, set_radius);
  BA_FLOAT_ATTR(hurt, hurt, SetHurt);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_BOOL_ATTR(always_show_health_bar, always_show_health_bar,
               set_always_show_health_bar);
#undef BA_NODE_TYPE_CLASS

  ShieldNodeType()
      : NodeType("shield", CreateShield),
        position(this),
        radius(this),
        hurt(this),
        color(this),
        always_show_health_bar(this) {}
};
static NodeType* node_type{};

auto ShieldNode::InitType() -> NodeType* {
  node_type = new ShieldNodeType();
  return node_type;
}

ShieldNode::ShieldNode(Scene* scene)
    : Node(scene, node_type)
#if !BA_HEADLESS_BUILD
      ,
      shadow_(0.2f)
#endif  // !BA_HEADLESS_BUILD
{
  last_hurt_change_time_ = scene->time();
}

ShieldNode::~ShieldNode() = default;

void ShieldNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;
}

void ShieldNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
}

void ShieldNode::SetHurt(float val) {
  float old_hurt = hurt_;
  hurt_ = val;
  if (hurt_ != old_hurt) {
    // Only flash if we change by a significant amount
    // (avoids flashing during regular drain).
    if (std::abs(hurt_ - old_hurt) > 0.05f) {
      flash_ = 1.0f;
      last_hurt_change_time_ = scene()->time();
    }
  }
}

void ShieldNode::Step() {
  float smoothing = 0.94f;
  d_r_scale_ = smoothing * d_r_scale_ + (1.0f - smoothing) * (1.0f - r_scale_);
  r_scale_ += d_r_scale_;
  d_r_scale_ *= 0.92f;

  // Move our smoothed hurt value a short time after we get hit.
  if (scene()->time() - last_hurt_change_time_ > 400) {
    if (hurt_smoothed_ < hurt_) {
      hurt_smoothed_ = std::min(hurt_, hurt_smoothed_ + 0.03f);
    } else {
      hurt_smoothed_ = std::max(hurt_, hurt_smoothed_ - 0.03f);
    }
  }

  flash_ -= 0.04f;
  if (flash_ < 0.0f) {
    flash_ = 0.0f;
  }
  hurt_rand_ = RandomFloat();
  rot_count_ = (rot_count_ + 1) % 256;

#if !BA_HEADLESS_BUILD
  shadow_.SetPosition(Vector3f(position_[0], position_[1], position_[2]));
#endif  // !BA_HEADLESS_BUILD
}

void ShieldNode::Draw(base::FrameDef* frame_def) {
#if !BA_HEADLESS_BUILD

  {
    float o = (1.0f - hurt_) * 1.0f
              + hurt_ * (1.0f * hurt_rand_ * hurt_rand_ * hurt_rand_);
    float s_density, s_scale;
    shadow_.GetValues(&s_scale, &s_density);
    float brightness = s_density * 0.8f * o;
    if (flash_ > 0.0f) {
      brightness *= (1.0f + 6.0f * flash_);
    }
    float rs = (0.6f + hurt_rand_ * 0.05f) * radius_ * s_scale * r_scale_;

    // draw our light on both terrain and objects
    g_base->graphics->DrawBlotchSoft(
        Vector3f(&position_[0]), 3.4f * rs, color_[0] * brightness,
        color_[1] * brightness, color_[2] * brightness, 0.0f);
    // draw our light on both terrain and objects
    g_base->graphics->DrawBlotchSoftObj(
        Vector3f(&position_[0]), 3.4f * rs, color_[0] * brightness * 0.4f,
        color_[1] * brightness * 0.4f, color_[2] * brightness * 0.4f, 0.0f);
  }

  // Life bar.
  {
    millisecs_t fade_time = 2000;

    millisecs_t since_last_hurt_change =
        scene()->time() - last_hurt_change_time_;

    if (since_last_hurt_change < fade_time || always_show_health_bar_) {
      base::SimpleComponent c(frame_def->overlay_3d_pass());
      c.SetTransparent(true);
      c.SetPremultiplied(true);
      {
        auto xf = c.ScopedTransform();
        float o = 1.0f
                  - static_cast<float>(since_last_hurt_change)
                        / static_cast<float>(fade_time);
        if (always_show_health_bar_) {
          o = std::max(o, 0.5f);
        }
        o *= o;
        float p_left, p_right;
        if (hurt_ < hurt_smoothed_) {
          p_left = 1.0f - hurt_smoothed_;
          p_right = 1.0f - hurt_;
        } else {
          p_right = 1.0f - hurt_smoothed_;
          p_left = 1.0f - hurt_;
        }

        // For the first moment start p_left at p_right so they can see a
        // glimpse of green before it goes away.
        if (since_last_hurt_change < 100) {
          p_left +=
              (p_right - p_left)
              * (1.0f - static_cast<float>(since_last_hurt_change) / 100.0f);
        }
        c.Translate(position_[0] - 0.25f, position_[1] + 1.25f, position_[2]);
        c.Scale(0.5f, 0.5f, 0.5f);
        float height = 0.1f;
        float half_height = height * 0.5f;
        c.SetColor(0, 0, 0.3f, 0.3f * o);
        {
          auto xf = c.ScopedTransform();
          c.Translate(0.5f, half_height);
          c.Scale(1.1f, height + 0.1f);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
        c.SetColor(0.4f * o, 0.4f * o, 0.8f * o, 0.0f * o);
        {
          auto xf = c.ScopedTransform();
          c.Translate(p_left * 0.5f, half_height);
          c.Scale(p_left, height);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
        c.SetColor(1.0f * o, 1.0f * o, 1.0f * o, 0.0f);
        {
          auto xf = c.ScopedTransform();
          c.Translate((p_left + p_right) * 0.5f, half_height);
          c.Scale(p_right - p_left, height);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
        c.SetColor(0.1f * o, 0.1f * o, 0.2f * o, 0.4f * o);
        {
          auto xf = c.ScopedTransform();
          c.Translate((p_right + 1.0f) * 0.5f, half_height);
          c.Scale(1.0f - p_right, height);
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
      }
      c.Submit();
    }
  }

  // main bubble
  float r = hurt_rand_;
  float o = (1.0f - hurt_) * 1.0f + hurt_ * (1.0f * r * r * r);
  o *= 0.3f;
  float cx, cy, cz;
  g_base->graphics->camera()->get_position(&cx, &cy, &cz);
  float col[4];
  col[0] = color_[0] * o;
  col[1] = color_[1] * o;
  col[2] = color_[2] * o;
  float distort = 0.05f + RandomFloat() * 0.06f;
  if (flash_ > 0.0f) {
    distort += 0.9f * (RandomFloat() - 0.4f) * flash_;
    col[0] += flash_;
    col[1] += flash_;
    col[2] += flash_;
  }

  {
    base::ObjectComponent c(frame_def->beauty_pass());
    c.SetTransparent(true);
    c.SetPremultiplied(true);
    c.SetLightShadow(base::LightShadowType::kNone);
    c.SetReflection(base::ReflectionType::kSharp);
    c.SetReflectionScale(0.34f * o, 0.34f * o, 0.34f * o);
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kShield));
    c.SetColor(col[0], col[1], col[2], 0.13f * o);
    Vector3f to_cam =
        Vector3f(cx - position_[0], cy - position_[1], cz - position_[2])
            .Normalized();
    Matrix44f m =
        Matrix44fTranslate(position_[0], position_[1] + 0.1f, position_[2]);
    Vector3f right = Vector3f::Cross(to_cam, kVector3fY).Normalized();
    Vector3f up = Vector3f::Cross(right, to_cam).Normalized();
    Matrix44f om = Matrix44fOrient(right, to_cam, up);
    float s = radius_ * 0.53f;
    float r2 =
        r_scale_
        * (0.97f
           + 0.05f * Utils::precalc_rand_2(rot_count_ % kPrecalcRandsCount));
    {
      auto xf = c.ScopedTransform();
      c.MultMatrix((om * m).m);
      c.Scale(s, s, s);
      c.Rotate(Utils::precalc_rand_1(rot_count_ % kPrecalcRandsCount) * 360, 0,
               1, 0);
      c.Scale(r2, r2, r2);
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kShield),
                      base::kMeshDrawFlagNoReflection);
    }
    c.Submit();

    // Nifty intersection effects in fancy graphics mode.
    if (frame_def->HasDepthTexture()) {
      base::ShieldComponent c2(frame_def->overlay_3d_pass());
      {
        auto xf = c2.ScopedTransform();
        c2.MultMatrix((om * m).m);
        c2.Scale(s, s, s);
        c2.Rotate(Utils::precalc_rand_1(rot_count_ % kPrecalcRandsCount) * 360,
                  0, 1, 0);
        c2.Scale(r2, r2, r2);
        c2.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kShield));
      }
      c2.Submit();
    }
    if (frame_def->HasDepthTexture()) {
      base::PostProcessComponent c2(frame_def->blit_pass());
      c2.SetNormalDistort(distort);
      {
        auto xf = c2.ScopedTransform();
        c2.MultMatrix((om * m).m);
        c2.Scale(s, s, s);
        c2.Rotate(Utils::precalc_rand_1(rot_count_ % kPrecalcRandsCount) * 360,
                  0, 1, 0);
        float sc = r2 * 1.1f;
        c2.Scale(sc, sc, sc);
        c2.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kShield));
      }
      c2.Submit();
    }
  }
#endif  // BA_HEADLESS_BUILD
}

}  // namespace ballistica::scene_v1
