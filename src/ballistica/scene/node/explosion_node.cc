// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene/node/explosion_node.h"

#include "ballistica/graphics/camera.h"
#include "ballistica/graphics/component/object_component.h"
#include "ballistica/graphics/component/post_process_component.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/scene/node/node_type.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

class ExplosionNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS ExplosionNode
  BA_NODE_CREATE_CALL(CreateExplosion);
  BA_FLOAT_ARRAY_ATTR(position, position, set_position);
  BA_FLOAT_ARRAY_ATTR(velocity, velocity, set_velocity);
  BA_FLOAT_ATTR(radius, radius, set_radius);
  BA_FLOAT_ARRAY_ATTR(color, color, set_color);
  BA_BOOL_ATTR(big, big, set_big);
#undef BA_NODE_TYPE_CLASS
  ExplosionNodeType()
      : NodeType("explosion", CreateExplosion),
        position(this),
        velocity(this),
        radius(this),
        color(this),
        big(this) {}
};

static NodeType* node_type{};

auto ExplosionNode::InitType() -> NodeType* {
  node_type = new ExplosionNodeType();
  return node_type;
}

ExplosionNode* gExplosionDistortLock = nullptr;

ExplosionNode::ExplosionNode(Scene* scene)
    : Node(scene, node_type), birth_time_(scene->time()) {}

ExplosionNode::~ExplosionNode() {
  if (draw_distortion_ && have_distortion_lock_) {
    assert(gExplosionDistortLock == this);
    gExplosionDistortLock = nullptr;
  }
}

void ExplosionNode::set_big(bool val) {
  big_ = val;

  // big explosions try to steal the distortion pointer..
  if (big_) {
    check_draw_distortion_ = true;
  }
}

void ExplosionNode::set_position(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
}

void ExplosionNode::set_velocity(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for velocity",
                    PyExcType::kValue);
  }
  velocity_ = vals;
}

void ExplosionNode::set_color(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;
}

void ExplosionNode::Step() {
  // update our position from our velocity
  if (velocity_[0] != 0.0f || velocity_[1] != 0.0f || velocity_[2] != 0.0f) {
    velocity_[0] *= 0.95f;
    velocity_[1] *= 0.95f;
    velocity_[2] *= 0.95f;
    position_[0] += velocity_[0] * kGameStepSeconds;
    position_[1] += velocity_[1] * kGameStepSeconds;
    position_[2] += velocity_[2] * kGameStepSeconds;
  }
}

void ExplosionNode::Draw(FrameDef* frame_def) {
  {
    bool high_quality = (frame_def->quality() >= GraphicsQuality::kHigh);
    // we only draw distortion if we're the only bomb..
    // (it gets expensive..)
    if (check_draw_distortion_) {
      check_draw_distortion_ = false;
      {
        if (big_) {
          // Steal distortion handle.
          if (gExplosionDistortLock != nullptr) {
            gExplosionDistortLock->draw_distortion_ = false;
            gExplosionDistortLock = this;
            have_distortion_lock_ = true;
            draw_distortion_ = true;
          }
        } else {
          // Play nice and only distort if no one else currently is.
          if (gExplosionDistortLock == nullptr) {
            draw_distortion_ = true;
            gExplosionDistortLock = this;
            have_distortion_lock_ = true;
          } else {
            draw_distortion_ = false;
          }
        }
      }
    }
    if (draw_distortion_) {
      float age = scene()->time() - static_cast<float>(birth_time_);
      float amt = (1.0f - 0.00265f * age);
      if (amt > 0.0001f) {
        amt = pow(amt, 2.2f);
        amt *= 2.0f;
        if (big_) {
          amt *= 4.0f;
        } else {
          amt *= 0.8f;
        }
        float s = 1.0f;
        if (high_quality) {
          PostProcessComponent c(frame_def->blit_pass());
          c.setNormalDistort(0.5f * amt);
          c.PushTransform();
          c.Translate(position_[0], position_[1], position_[2]);
          c.Scale(1.0f + s * 0.8f * 0.025f * age,
                  1.0f + s * 0.8f * 0.0015f * age,
                  1.0f + s * 0.8f * 0.025f * age);
          c.Scale(0.7f, 0.7f, 0.7f);
          c.DrawModel(g_media->GetModel(SystemModelID::kShockWave),
                      kModelDrawFlagNoReflection);
          c.PopTransform();
          c.Submit();
        } else {
          // simpler transparent shock wave
          // draw our distortion wave in the overlay pass
          ObjectComponent c(frame_def->beauty_pass());
          c.SetTransparent(true);
          c.SetLightShadow(LightShadowType::kNone);
          // eww hacky - the shock wave model uses color as distortion amount
          c.SetColor(1.0f, 0.7f, 0.7f, 0.06f * amt);
          c.PushTransform();
          c.Translate(position_[0], position_[1], position_[2]);
          c.Scale(1.0f + s * 0.8f * 0.025f * age,
                  1.0f + s * 0.8f * 0.0015f * age,
                  1.0f + s * 0.8f * 0.025f * age);
          c.Scale(0.7f, 0.7f, 0.7f);
          c.DrawModel(g_media->GetModel(SystemModelID::kShockWave),
                      kModelDrawFlagNoReflection);
          c.PopTransform();
          c.Submit();
        }
      }
    }
  }

  float life = 1.0f * (big_ ? 350.0f : 260.0f);
  float age = scene()->time() - static_cast<float>(birth_time_);
  if (age < life) {
    float b = 2.0f;
    if (big_) {
      b = 2.0f;
    }
    float o = age / life;
    if (big_) {
      o = pow(1.0f - o, 1.4f);
    } else {
      o = pow(1.0f - o, 0.8f);
    }
    float s = 1.0f - (age / life);
    s = 1.0f - (s * s);
    s *= radius_;
    if (big_) {
      s *= 2.0f;
    } else {
      s *= 1.2f;
    }
    s *= 0.75f;
    float cx, cy, cz;
    g_graphics->camera()->get_position(&cx, &cy, &cz);
    ObjectComponent c(frame_def->beauty_pass());
    c.SetTransparent(true);
    c.SetLightShadow(LightShadowType::kNone);
    c.SetPremultiplied(true);
    c.SetTexture(g_media->GetTexture(SystemTextureID::kExplosion));
    c.SetColor(1.3f * o * color_[0] * b, o * color_[1] * b, o * color_[2] * b,
               0.0f);
    c.PushTransform();
    Vector3f to_cam =
        Vector3f(cx - position_[0], cy - position_[1], cz - position_[2])
            .Normalized();
    Matrix44f m = Matrix44fTranslate(position_[0], position_[1], position_[2]);
    Vector3f right = Vector3f::Cross(to_cam, kVector3fY).Normalized();
    Vector3f up = Vector3f::Cross(right, to_cam).Normalized();
    Matrix44f om = Matrix44fOrient(right, to_cam, up);
    c.MultMatrix((om * m).m);
    c.Scale(0.9f * s, 0.9f * s, 0.9f * s);
    c.DrawModel(g_media->GetModel(SystemModelID::kShield),
                kModelDrawFlagNoReflection);
    c.Scale(0.6f, 0.6f, 0.6f);
    c.Rotate(33, 0, 1, 0);
    c.SetColor(o * 7.0f * color_[0], o * 7.0f * color_[1], o * 7.0f * color_[2],
               0);
    c.DrawModel(g_media->GetModel(SystemModelID::kShield),
                kModelDrawFlagNoReflection);
    c.PopTransform();
    c.Submit();
  }
}

}  // namespace ballistica
