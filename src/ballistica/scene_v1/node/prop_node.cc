// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/prop_node.h"

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/support/area_of_interest.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/dynamics/dynamics.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

static void _doCalcERPCFM(float stiffness, float damping, float* erp,
                          float* cfm) {
  if (stiffness <= 0.0f && damping <= 0.0f) {
    (*erp) = 0.0f;
    // (*cfm) = dInfinity;  // doesn't seem to be happy...
    (*cfm) = 9999999999.0f;
  } else {
    (*erp) = (kGameStepSeconds * stiffness)
             / ((kGameStepSeconds * stiffness) + damping);
    (*cfm) = 1.0f / ((kGameStepSeconds * stiffness) + damping);
  }
}

static NodeType* node_type{};

auto PropNode::InitType() -> NodeType* {
  node_type = new PropNodeType();
  return node_type;
}

PropNode::PropNode(Scene* scene, NodeType* override_node_type)
    : Node(scene, override_node_type ? override_node_type : node_type),
      part_(this) {}

PropNode::~PropNode() {
  if (area_of_interest_) {
    g_base->graphics->camera()->DeleteAreaOfInterest(
        static_cast<base::AreaOfInterest*>(area_of_interest_));
  }
}

void PropNode::SetExtraAcceleration(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("expected array of size 3 for extra_acceleration");
  }
  extra_acceleration_ = vals;
}

void PropNode::HandleMessage(const char* data_in) {
  const char* data = data_in;
  bool handled = true;
  switch (extract_node_message_type(&data)) {
    case NodeMessageType::kImpulse: {
      float px = Utils::ExtractFloat16NBO(&data);
      float py = Utils::ExtractFloat16NBO(&data);
      float pz = Utils::ExtractFloat16NBO(&data);
      float vx = Utils::ExtractFloat16NBO(&data);
      float vy = Utils::ExtractFloat16NBO(&data);
      float vz = Utils::ExtractFloat16NBO(&data);
      float mag = Utils::ExtractFloat16NBO(&data);
      float velocity_mag = Utils::ExtractFloat16NBO(&data);
      float radius = Utils::ExtractFloat16NBO(&data);
      Utils::ExtractInt16NBO(&data);  // calc-force-only
      float fdirx = Utils::ExtractFloat16NBO(&data);
      float fdiry = Utils::ExtractFloat16NBO(&data);
      float fdirz = Utils::ExtractFloat16NBO(&data);
      body_->ApplyImpulse(px, py, pz, vx, vy, vz, fdirx, fdiry, fdirz, mag,
                          velocity_mag, radius, false);
      break;
    }
    default:
      handled = false;
      break;
  }
  if (!handled) {
    Node::HandleMessage(data_in);
  }
}

void PropNode::SetIsAreaOfInterest(bool val) {
  if ((val && area_of_interest_ == nullptr)
      || (!val && area_of_interest_ != nullptr)) {
    // either make one or kill the one we had
    if (val) {
      assert(area_of_interest_ == nullptr);
      area_of_interest_ = g_base->graphics->camera()->NewAreaOfInterest(false);
    } else {
      assert(area_of_interest_ != nullptr);
      g_base->graphics->camera()->DeleteAreaOfInterest(
          static_cast<base::AreaOfInterest*>(area_of_interest_));
      area_of_interest_ = nullptr;
    }
  }
}

void PropNode::Draw(base::FrameDef* frame_def) {
#if !BA_HEADLESS_BUILD

  // We need a texture, mesh, and body to be present to draw.
  if ((!mesh_.exists()) || (!color_texture_.exists()) || (!body_.exists())) {
    return;
  }

  base::ObjectComponent c(frame_def->beauty_pass());
  c.SetTexture(color_texture_.exists() ? color_texture_->texture_data()
                                       : nullptr);
  c.SetLightShadow(base::LightShadowType::kObject);
  if (reflection_ != base::ReflectionType::kNone) {
    c.SetReflection(reflection_);
    c.SetReflectionScale(reflection_scale_r_, reflection_scale_g_,
                         reflection_scale_b_);
  }
  if (flashing_ && frame_def->frame_number_filtered() % 10 < 5) {
    c.SetColor(1.2f, 1.2f, 1.2f);
  }
  {
    auto xf = c.ScopedTransform();
    body_->ApplyToRenderComponent(&c);
    float s = mesh_scale_ * extra_mesh_scale_;
    c.Scale(s, s, s);
    c.DrawMeshAsset(mesh_->mesh_data());
  }
  c.Submit();

  {  // Shadow.
    assert(body_.exists());
    const dReal* pos_raw = dGeomGetPosition(body_->geom());
    float pos[3];
    pos[0] = pos_raw[0] + body_->blend_offset().x;
    pos[1] = pos_raw[1] + body_->blend_offset().y;
    pos[2] = pos_raw[2] + body_->blend_offset().z;
    float s_scale, s_density;
    shadow_.GetValues(&s_scale, &s_density);
    if (body_type_ == BodyType::PUCK) {
      s_density *= 2.4f;
      s_scale *= 0.85f;
    } else {
      s_density *= 2.3f;
    }
    s_density *= 0.34f;
    {
      base::GraphicsQuality quality = frame_def->quality();

      // fancy new cheap shadows
      {
        float rs = shadow_size_ * mesh_scale_ * extra_mesh_scale_ * s_scale;
        float d =
            (quality == base::GraphicsQuality::kLow ? 1.1f : 0.8f) * s_density;
        g_base->graphics->DrawBlotch(Vector3f(pos), rs * 2.0f, 0.22f * d,
                                     0.16f * d, 0.10f * d, d);
      }

      if (quality > base::GraphicsQuality::kLow) {
        // More sharp accurate shadow.
        if (light_mesh_.exists()) {
          base::SimpleComponent c2(frame_def->light_shadow_pass());
          c2.SetTransparent(true);
          float dd = body_type_ == BodyType::LANDMINE ? 0.5f : 1.0f;
          c2.SetColor(0.3f, 0.2f, 0.1f, 0.08f * s_density * dd);
          {
            auto x2 = c2.ScopedTransform();
            body_->ApplyToRenderComponent(&c2);
            float ss = body_type_ == BodyType::LANDMINE ? 0.9f : 1.0f;
            for (int i = 0; i < 4; i++) {
              auto xf = c2.ScopedTransform();
              float s2 = ss * mesh_scale_ * extra_mesh_scale_
                         * (1.3f - 0.08f * static_cast<float>(i));
              c2.Scale(s2, s2, s2);
              c2.DrawMeshAsset(light_mesh_->mesh_data());
            }
          }
          c2.Submit();
        }

        // In fancy-pants mode we can do a softened version of ourself
        // for fake caustic effects.
        if (light_mesh_.exists()) {
          assert(color_texture_.exists());
          base::SimpleComponent c2(frame_def->light_shadow_pass());
          c2.SetTransparent(true);
          c2.SetPremultiplied(true);
          c2.SetTexture(color_texture_.exists() ? color_texture_->texture_data()
                                                : nullptr);
          if (flashing_ && frame_def->frame_number_filtered() % 10 < 5) {
            c2.SetColor(0.026f * s_density, 0.026f * s_density,
                        0.026f * s_density, 0.0f);
          } else {
            c2.SetColor(0.022f * s_density, 0.022f * s_density,
                        0.022f * s_density, 0.0f);
          }
          {
            auto xf = c2.ScopedTransform();
            body_->ApplyToRenderComponent(&c2);
            for (int i = 0; i < 4; i++) {
              auto xf = c2.ScopedTransform();
              float s2 = mesh_scale_ * extra_mesh_scale_ * 1.7f;
              c2.Scale(s2, s2, s2);
              c2.Rotate(-50.0f + 43.0f * static_cast<float>(i), 0.2f, 0.4f,
                        0.6f);
              c2.DrawMeshAsset(light_mesh_->mesh_data());
            }
          }
          c2.Submit();
        }
      }
    }
  }
#endif  // !BA_HEADLESS_BUILD
}

auto PropNode::GetBody() const -> std::string {
  switch (body_type_) {
    case BodyType::UNSET:
      return "";
    case BodyType::BOX:
      return "box";
    case BodyType::SPHERE:
      return "sphere";
    case BodyType::CRATE:
      return "crate";
    case BodyType::LANDMINE:
      return "landMine";
    case BodyType::CAPSULE:
      return "capsule";
    case BodyType::PUCK:
      return "puck";
    default:
      throw Exception("Invalid body-type in prop-node: "
                      + std::to_string(static_cast<int>(body_type_)));
  }
}

void PropNode::SetBodyScale(float val) {
  // this can be set exactly once
  if (body_.exists()) {
    throw Exception("body_scale can't be set once body exists");
  }
  body_scale_ = std::max(0.01f, val);
}

void PropNode::SetBody(const std::string& val) {
  BodyType body_type;
  RigidBody::Shape shape;
  if (val == "box") {
    body_type = BodyType::BOX;
    shape = RigidBody::Shape::kBox;
  } else if (val == "sphere") {
    body_type = BodyType::SPHERE;
    shape = RigidBody::Shape::kSphere;
  } else if (val == "crate") {
    body_type = BodyType::CRATE;
    shape = RigidBody::Shape::kBox;
  } else if (val == "landMine") {
    body_type = BodyType::LANDMINE;
    shape = RigidBody::Shape::kBox;
  } else if (val == "capsule") {
    body_type = BodyType::CAPSULE;
    shape = RigidBody::Shape::kCapsule;
  } else if (val == "puck") {
    body_type = BodyType::PUCK;
    shape = RigidBody::Shape::kCylinder;
  } else {
    throw Exception("Invalid body type: '" + val + "'");
  }

  // we're ok with redundant sets, but complain/ignore if they try to switch..
  if (body_.exists()) {
    if (body_type_ != body_type || shape_ != shape) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "body attr can not be changed from its initial value");
      return;
    }
  }
  body_type_ = body_type;
  shape_ = shape;
  body_ =
      Object::New<RigidBody>(0, &part_, RigidBody::Type::kBody, shape_,
                             RigidBody::kCollideActive, RigidBody::kCollideAll);

  body_->set_can_cause_impact_damage(true);
  body_->AddCallback(DoCollideCallback, this);
  if (body_type_ == BodyType::LANDMINE) {
    float bs1 = 0.7f * body_scale_;
    float bs2 = 0.18f * body_scale_;
    body_->SetDimensions(bs1, bs2, bs1, bs1, bs2, bs1, 2.0f * density_);
  } else if (body_type_ == BodyType::CRATE) {
    float s = 0.7f * body_scale_;
    body_->SetDimensions(s, s, s, s, s, s, 0.7f * density_);
  } else if (body_type_ == BodyType::SPHERE) {
    float s = 0.3f * body_scale_;
    body_->SetDimensions(s, 0, 0, s, 0, 0, density_);
  } else if (body_type_ == BodyType::CAPSULE) {
    float s = 0.3f * body_scale_;
    body_->SetDimensions(s, s, 0, s, s, 0, density_);
  }

  // in case we've had a translate or velocity set already..
  dBodySetPosition(body_->body(), position_[0], position_[1], position_[2]);
  dBodySetLinearVel(body_->body(), velocity_[0], velocity_[1], velocity_[2]);

  // initial orientation:
  // put pucks upright and make them big
  if (body_type_ == BodyType::PUCK) {
    dQuaternion iq;
    dQFromAxisAndAngle(iq, 1, 0, 0, -90 * (kPi / 180.0f));
    dBodySetQuaternion(body_->body(), iq);
    body_->SetDimensions(0.7f, 0.58f, 0, 0.7f, 0.48f, 0, 0.14f * density_);
  } else {
    // give other types random start rotations..
    dQuaternion iq;
    int64_t gti = scene()->stepnum();
    dQFromAxisAndAngle(
        iq, 0.05f, 1, 0,
        Utils::precalc_rand_1((stream_id() + gti) % kPrecalcRandsCount) * 360.0f
            * (kPi / 180.0f));
    dBodySetQuaternion(body_->body(), iq);
  }
}

void PropNode::UpdateAreaOfInterest() {
  auto* aoi = static_cast<base::AreaOfInterest*>(area_of_interest_);
  if (!aoi) {
    return;
  }
  assert(body_.exists());
  aoi->set_position(Vector3f(dGeomGetPosition(body_->geom())));
  aoi->SetRadius(5.0f);
}

void PropNode::SetReflectionScale(const std::vector<float>& vals) {
  if (vals.size() != 1 && vals.size() != 3) {
    throw Exception(
        "Expected float array of length"
        " 1 or 3 for reflection_scale",
        PyExcType::kValue);
  }
  reflection_scale_ = vals;
  if (reflection_scale_.size() == 1) {
    reflection_scale_r_ = reflection_scale_g_ = reflection_scale_b_ =
        reflection_scale_[0];
  } else {
    reflection_scale_r_ = reflection_scale_[0];
    reflection_scale_g_ = reflection_scale_[1];
    reflection_scale_b_ = reflection_scale_[2];
  }
}

auto PropNode::GetReflection() const -> std::string {
  return base::Graphics::StringFromReflectionType(reflection_);
}

void PropNode::SetReflection(const std::string& val) {
  reflection_ = base::Graphics::ReflectionTypeFromString(val);
}

auto PropNode::GetMaterials() const -> std::vector<Material*> {
  return part_.GetMaterials();
}

void PropNode::SetMaterials(const std::vector<Material*>& vals) {
  part_.SetMaterials(vals);
}

auto PropNode::GetVelocity() const -> std::vector<float> {
  // if we've got a body, return its velocity
  if (body_.exists()) {
    const dReal* v = dBodyGetLinearVel(body_->body());
    std::vector<float> vv(3);
    vv[0] = v[0];
    vv[1] = v[1];
    vv[2] = v[2];
    return vv;
  }
  // otherwise if we have an internally stored value, return that.
  // (this way if we set velocity and then query it we'll get the right value
  // even if the body hasn't been made yet)
  return velocity_;
}

void PropNode::SetVelocity(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for velocity",
                    PyExcType::kValue);
  }
  // if we've got a body, apply the velocity to that
  if (body_.exists()) {
    dBodySetLinearVel(body_->body(), vals[0], vals[1], vals[2]);
  } else {
    // otherwise just store it in our internal vector in
    // case someone asks for it
    velocity_ = vals;
  }
}

auto PropNode::GetPosition() const -> std::vector<float> {
  // if we've got a body, return its position
  if (body_.exists()) {
    const dReal* p = dGeomGetPosition(body_->geom());
    std::vector<float> f(3);
    f[0] = p[0];
    f[1] = p[1];
    f[2] = p[2];
    return f;
  }
  // otherwise if we have an internally stored value, return that.
  // (this way if we set position and then query it we'll get the right value
  // even if the body hasn't been made yet)
  return position_;
}

void PropNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for position (got "
                        + std::to_string(vals.size()) + ")",
                    PyExcType::kValue);
  }
  // if we've got a body, apply the position to that
  if (body_.exists()) {
    dBodySetPosition(body_->body(), vals[0], vals[1], vals[2]);
  } else {
    // otherwise just store it in our internal vector
    // in case someone asks for it
    position_ = vals;
  }
}

void PropNode::Step() {
  if (body_type_ == BodyType::UNSET) {
    if (!reported_unset_body_type_) {
      reported_unset_body_type_ = true;
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "prop-node " + GetObjectDescription()
                               + " did not have its 'body' attr set.");
      return;
    }
  }
  BA_DEBUG_CHECK_BODIES();

  assert(body_.exists());

  // FIXME - this should probably happen for RBDs automatically?...
  body_->UpdateBlending();

  // on happy thoughts, keep us on the 2d plane..
  if (g_base->graphics->camera()->happy_thoughts_mode() && body_.exists()) {
    dBodyID b;
    const dReal *p, *v;
    b = body_->body();
    p = dBodyGetPosition(b);
    dBodySetPosition(b, p[0], p[1], base::kHappyThoughtsZPlane);
    v = dBodyGetLinearVel(b);
    dBodySetLinearVel(b, v[0], v[1], 0.0f);
  }

  // update our area-of-interest if we have one
  UpdateAreaOfInterest();

  // update our shadow input positions
  {
#if !BA_HEADLESS_BUILD
    shadow_.SetPosition(Vector3f(dBodyGetPosition(body_->body())));
#endif  // !BA_HEADLESS_BUILD
  }

  // clamp our max linear and angular velocities
  {
    dBodyID b = body_->body();
    float max_mag_squared = 400.f;
    // float max_mag_squared_lin = 300.0f;
    float max_mag_squared_lin = max_speed_ * max_speed_;
    const dReal* aVel = dBodyGetAngularVel(b);
    float mag_squared =
        aVel[0] * aVel[0] + aVel[1] * aVel[1] + aVel[2] * aVel[2];
    if (mag_squared > max_mag_squared) {
      float scale = max_mag_squared / mag_squared;
      dBodySetAngularVel(b, aVel[0] * scale, aVel[1] * scale, aVel[2] * scale);
    }
    const dReal* lVel = dBodyGetLinearVel(b);
    mag_squared = lVel[0] * lVel[0] + lVel[1] * lVel[1] + lVel[2] * lVel[2];
    if (mag_squared > max_mag_squared_lin) {
      float scale = max_mag_squared_lin / mag_squared;
      dBodySetLinearVel(b, lVel[0] * scale, lVel[1] * scale, lVel[2] * scale);
    }
  }

  // if we're out of bounds, arrange to have ourself informed
  if (body_.exists()) {
    const dReal* p = dBodyGetPosition(body_->body());
    if (scene()->IsOutOfBounds(p[0], p[1], p[2])) {
      scene()->AddOutOfBoundsNode(this);
    }
  }

  // apply damping force
  float rotationalDampingX = 0.02f;
  float rotationalDampingY = 0.02f;
  float rotationalDampingZ = 0.02f;

  // don't add forces if we're asleep otherwise we'll explode when we wake up
  if (dBodyIsEnabled(body_->body())) {
    dMass mass;
    dBodyID b = body_->body();
    dBodyGetMass(b, &mass);

    const dReal* vel;
    dReal force[3];
    vel = dBodyGetAngularVel(b);
    force[0] = -1 * mass.mass * vel[0] * rotationalDampingX;
    force[1] = -1 * mass.mass * vel[1] * rotationalDampingY;
    force[2] = -1 * mass.mass * vel[2] * rotationalDampingZ;
    dBodyAddTorque(b, force[0], force[1], force[2]);
    if (damping_ > 0.0f) {
      float damp = std::max(0.0f, 1.0f - damping_);
      const dReal* vel2 = dBodyGetLinearVel(b);
      dBodySetLinearVel(b, vel2[0] * damp, vel2[1] * damp, vel2[2] * damp);
    }
    if (extra_acceleration_[0] != 0.0f || extra_acceleration_[1] != 0.0f
        || extra_acceleration_[2] != 0.0f) {
      dBodyAddForce(b, extra_acceleration_[0] * mass.mass,
                    extra_acceleration_[1] * mass.mass,
                    extra_acceleration_[2] * mass.mass);
    }
    if (gravity_scale_ != 1.0f) {
      dVector3 grav;
      // the simplest way to do this is to just add a force to offset gravity
      // to where we want it to be for this object..
      float amt = gravity_scale_ - 1.0f;
      dWorldGetGravity(scene()->dynamics()->ode_world(), grav);
      dBodyAddForce(b, mass.mass * amt * grav[0], mass.mass * amt * grav[1],
                    mass.mass * amt * grav[2]);
    }
  }
  BA_DEBUG_CHECK_BODIES();
}

auto PropNode::GetRigidBody(int id) -> RigidBody* {
  if (id == 0) {
    return body_.get();
  }
  return nullptr;
}

auto PropNode::CollideCallback(dContact* c, int count,
                               RigidBody* colliding_body,
                               RigidBody* opposingbody) -> bool {
  if (sticky_) {
    uint32_t f = opposingbody->flags();

    // dont collide at all with rollers..
    if (f & RigidBody::kIsRoller) {
      return false;
    }
    // this should never happen, right?..
    assert(opposingbody->part()->node() != nullptr);

    if ((stick_to_owner_ || opposingbody->part()->node() != owner_.get())
        && !(f & RigidBody::kIsBumper)) {
      if (body_.exists()) {
        // stick to static stuff:
        if (opposingbody->type() == RigidBody::Type::kGeomOnly) {
          const dReal* v;
          dBodyID b = body_->body();
          v = dBodyGetLinearVel(b);
          dBodySetLinearVel(b, v[0] * 0.2f, v[1] * 0.2f, v[2] * 0.2f);
          dBodySetAngularVel(b, 0, 0, 0);
        } else {
          // stick to dynamic stuff
          dBodyID b2 = opposingbody->body();
          dBodyID b1 = body_->body();
          dBodyEnable(b1);  // wake it up
          dBodyEnable(b2);  // wake it up
          dMass m;
          dBodyGetMass(b2, &m);
          dJointID j =
              dJointCreateFixed(scene()->dynamics()->ode_world(),
                                scene()->dynamics()->ode_contact_group());
          dJointAttach(j, b1, b2);
          dJointSetFixed(j);
          dJointSetFixedSpringMode(j, 1, 1, false);
          if (m.mass < 0.2f) {
            dJointSetFixedParam(j, dParamLinearStiffness, 200);
            dJointSetFixedParam(j, dParamLinearDamping, 0.2f);
            dJointSetFixedParam(j, dParamAngularStiffness, 200);
            dJointSetFixedParam(j, dParamAngularDamping, 0.2f);
          } else {
            dJointSetFixedParam(j, dParamLinearStiffness, 2000);
            dJointSetFixedParam(j, dParamLinearDamping, 2);
            dJointSetFixedParam(j, dParamAngularStiffness, 2000);
            dJointSetFixedParam(j, dParamAngularDamping, 2);
          }

          // ...now attractive forces.
          // FIXME - currently we ignore small stuff like limb bits.
          //  We really should just vary our sticky strength based
          //  on the mass of what we're hitting though.
          if (m.mass < 0.2f) {
            return true;  // Still collide; just not sticky.
          }

          // Also exert a slight attractive force.
          {
            const dReal* p1 = dBodyGetPosition(b1);
            const dReal* p2 = dBodyGetPosition(b2);
            dReal f2[3];
            float stiffness = 200;
            f2[0] = (p1[0] - p2[0]) * stiffness;
            f2[1] = (p1[1] - p2[1]) * stiffness;
            f2[2] = (p1[2] - p2[2]) * stiffness;
            dBodyAddForce(b1, -f2[0], -f2[1], -f2[2]);
            dBodyAddForce(b2, f2[0], f2[1], f2[2]);
          }
        }
      }
    }
  }

  if (body_type_ == BodyType::CRATE) {
    // Drop stiffness/damping/friction pretty low.
    float stiffness = 800.0f;
    float damping = 1.0f;
    if (opposingbody->flags() & RigidBody::kIsTerrain) {
      damping = 10.0f;
    }
    float erp, cfm;
    _doCalcERPCFM(stiffness, damping, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
      c[i].surface.mu *= 0.7f;
    }
  } else if (body_type_ == BodyType::LANDMINE) {
    // we wanna be laying flat down; if we're standing upright, topple over
    dVector3 worldUp;
    dBodyVectorToWorld(body_->body(), 0, 1, 0, worldUp);
    if (std::abs(worldUp[1]) < 0.4f) {
      float mag = -4.0f;
      // push in the 2 horizontal axes only
      const dReal* pos = dBodyGetPosition(body_->body());
      dBodyAddForceAtPos(body_->body(), mag * worldUp[0], 0, mag * worldUp[2],
                         pos[0], pos[1] + 1.0f, pos[2]);
      dBodyAddForceAtPos(body_->body(), -mag * worldUp[0], 0, -mag * worldUp[2],
                         pos[0], pos[1] - 1.0f, pos[2]);
    }
    // drop stiffness/damping/friction pretty low..
    float stiffness = 1000.0f;
    float damping = 10.0f;
    float erp, cfm;
    _doCalcERPCFM(stiffness, damping, &erp, &cfm);

    // if we're not lying flat, kill friction
    float friction = 1.0f;
    if (std::abs(worldUp[1]) < 0.7f) friction = 0.05f;

    for (int i = 0; i < count; i++) {
      c[i].surface.mu *= friction;
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
    }

    // lets also damp our velocity a tiny bit if we're hitting terrain
    if (opposingbody->flags() & RigidBody::kIsTerrain) {
      float damp = 0.98f;
      const dReal* vel = dBodyGetLinearVel(body_->body());
      dBodySetLinearVel(body_->body(), vel[0] * damp, vel[1], vel[2] * damp);
    }
  } else {
    // drop stiffness/damping/friction pretty low..
    float stiffness = 5000.0f;
    float damping = 10.0f;
    float erp, cfm;
    _doCalcERPCFM(stiffness, damping, &erp, &cfm);
    for (int i = 0; i < count; i++) {
      c[i].surface.soft_erp = erp;
      c[i].surface.soft_cfm = cfm;
      c[i].surface.mu *= 0.2f;
    }
  }

  return true;
}

void PropNode::GetRigidBodyPickupLocations(int id, float* obj, float* character,
                                           float* hand1, float* hand2) {
  if (body_type_ == BodyType::LANDMINE) {
    obj[0] = 0;
    obj[1] = -0.1f;
    obj[2] = 0;
    character[0] = character[1] = character[2] = 0.0f;
    character[1] = -0.3f;
    character[2] = 0;
    hand1[0] = -0.15f;
    hand1[1] = 0.00f;
    hand1[2] = 0.0f;
    hand2[0] = 0.15f;
    hand2[1] = 0.00f;
    hand2[2] = 0.0f;
  } else {
    obj[0] = 0;
    obj[1] = -0.17f;
    obj[2] = 0;
    character[0] = character[1] = character[2] = 0.0f;
    character[1] = -0.27f;
    hand1[0] = -0.15f;
    hand1[1] = 0.00f;
    hand1[2] = 0.0f;
    hand2[0] = 0.15f;
    hand2[1] = 0.00f;
    hand2[2] = 0.0f;
  }
}

void PropNode::SetDensity(float val) {
  if (body_.exists()) {
    throw Exception("can't set density after body has been set");
  }
  density_ = std::max(0.01f, std::min(100.0f, val));
}

}  // namespace ballistica::scene_v1
