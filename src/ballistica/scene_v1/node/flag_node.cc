// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/flag_node.h"

#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/support/area_of_interest.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::scene_v1 {

const int kFlagSizeX{5};
const int kFlagSizeY{5};

const float kFlagCanvasWidth{1.0f};
const float kFlagCanvasHeight{1.0f};

const float kFlagCanvasScaleX{kFlagCanvasWidth / kFlagSizeX};
const float kFlagCanvasScaleY{kFlagCanvasHeight / kFlagSizeY};

// NOLINTNEXTLINE(cert-err58-cpp)
const float kFlagCanvasScaleDiagonal{
    sqrtf(kFlagCanvasScaleX * kFlagCanvasScaleX
          + kFlagCanvasScaleY * kFlagCanvasScaleY)};

const float kFlagRadius{0.1f};
const float kFlagHeight{1.5f};

const float kFlagMassRadius{0.3f};
const float kFlagMassHeight{1.0f};

const float kFlagDensity{1.0f};

const float kStiffness{0.4f};
const float kWindStrength{0.002f};
const float kGravityStrength{0.0012f};
const float kDampingStrength{0.0f};
const float kDragStrength{0.1f};

class FlagNode::FullShadowSet : public Object {
 public:
  base::BGDynamicsShadow shadow_pole_bottom_;
  base::BGDynamicsShadow shadow_pole_middle_;
  base::BGDynamicsShadow shadow_pole_top_;
  base::BGDynamicsShadow shadow_flag_;
};
class FlagNode::SimpleShadowSet : public Object {
 public:
  base::BGDynamicsShadow shadow_;
};

class FlagNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS FlagNode
  BA_NODE_CREATE_CALL(CreateFlag);
  BA_BOOL_ATTR(is_area_of_interest, is_area_of_interest, SetIsAreaOfInterest);
  BA_FLOAT_ARRAY_ATTR(position, getPosition, SetPosition);
  BA_TEXTURE_ATTR(color_texture, color_texture, set_color_texture);
  BA_BOOL_ATTR(lightWeight, light_weight, SetLightWeight);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_MATERIAL_ARRAY_ATTR(materials, GetMaterials, SetMaterials);
#undef BA_NODE_TYPE_CLASS

  FlagNodeType()
      : NodeType("flag", CreateFlag),
        is_area_of_interest(this),
        position(this),
        color_texture(this),
        lightWeight(this),
        color(this),
        materials(this) {}
};

static NodeType* node_type{};

auto FlagNode::InitType() -> NodeType* {
  node_type = new FlagNodeType();
  return node_type;
}

enum FlagBodyType { kPoleBodyID };

FlagNode::FlagNode(Scene* scene) : Node(scene, node_type), part_(this) {
  body_ = Object::New<RigidBody>(
      kPoleBodyID, &part_, RigidBody::Type::kBody, RigidBody::Shape::kCapsule,
      RigidBody::kCollideActive, RigidBody::kCollideAll);
  UpdateDimensions();
  dBodySetPosition(body_->body(), 0, 1.2f, 0);
  dQuaternion iq;
  dQFromAxisAndAngle(iq, 1, 0, 0, -90.0f * (kPi / 180.0f));
  dBodySetQuaternion(body_->body(), iq);
  ResetFlagMesh();

  // Set our mesh static data and indices once.
  auto indices(Object::New<base::MeshIndexBuffer16>(6 * (kFlagSizeX - 1)
                                                    * (kFlagSizeY - 1)));
  uint16_t* index = &indices->elements[0];
  auto v_static(Object::New<base::MeshBuffer<base::VertexObjectSplitStatic>>(
      kFlagSizeX * kFlagSizeY));
  base::VertexObjectSplitStatic* vs = &v_static->elements[0];

  int x_inc = 65535 / (kFlagSizeX - 1);
  int y_inc = 65535 / (kFlagSizeY - 1);

  for (int y = 0; y < kFlagSizeY - 1; y++) {
    for (int x = 0; x < kFlagSizeX - 1; x++) {
      *index++ = static_cast_check_fit<uint16_t>(kFlagSizeX * y + x);
      *index++ = static_cast_check_fit<uint16_t>(kFlagSizeX * y + x + 1);
      *index++ = static_cast_check_fit<uint16_t>(kFlagSizeX * (y + 1) + x);
      *index++ = static_cast_check_fit<uint16_t>(kFlagSizeX * (y + 1) + x);
      *index++ = static_cast_check_fit<uint16_t>(kFlagSizeX * y + x + 1);
      *index++ = static_cast_check_fit<uint16_t>(kFlagSizeX * (y + 1) + x + 1);
    }
  }
  for (int y = 0; y < kFlagSizeY; y++) {
    for (int x = 0; x < kFlagSizeX; x++) {
      vs[kFlagSizeX * y + x].uv[0] = static_cast_check_fit<uint16_t>(x_inc * x);
      vs[kFlagSizeX * y + x].uv[1] = static_cast_check_fit<uint16_t>(y_inc * y);
    }
  }

  mesh_.SetIndexData(indices);
  mesh_.SetStaticData(v_static);
}

auto FlagNode::getPosition() const -> std::vector<float> {
  const dReal* p = dGeomGetPosition(body_->geom());
  std::vector<float> f(3);
  f[0] = p[0];
  f[1] = p[1];
  f[2] = p[2];
  return f;
}

void FlagNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;
}

void FlagNode::SetLightWeight(bool val) {
  light_weight_ = val;
  UpdateDimensions();
}

void FlagNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of length 3 for position",
                    PyExcType::kValue);
  }
  dQuaternion iq;
  dQFromAxisAndAngle(iq, 1, 0, 0, -90 * (kPi / 180.0f));
  dBodySetPosition(body_->body(), vals[0], vals[1], vals[2]);
  dBodySetQuaternion(body_->body(), iq);
  dBodySetLinearVel(body_->body(), 0, 0, 0);
  dBodySetAngularVel(body_->body(), 0, 0, 0);
  ResetFlagMesh();
}

void FlagNode::SetIsAreaOfInterest(bool val) {
  if ((val && area_of_interest_ == nullptr)
      || (!val && area_of_interest_ != nullptr)) {
    // Either make one or kill the one we had.
    if (val) {
      assert(area_of_interest_ == nullptr);
      area_of_interest_ = g_base->graphics->camera()->NewAreaOfInterest(false);
    } else {
      assert(area_of_interest_ != nullptr);
      g_base->graphics->camera()->DeleteAreaOfInterest(area_of_interest_);
      area_of_interest_ = nullptr;
    }
  }
}

auto FlagNode::GetMaterials() const -> std::vector<Material*> {
  return part_.GetMaterials();
}

void FlagNode::SetMaterials(const std::vector<Material*>& vals) {
  part_.SetMaterials(vals);
}

void FlagNode::UpdateDimensions() {
  float density_scale =
      (g_base->graphics->camera()->happy_thoughts_mode()) ? 0.3f : 1.0f;
  body_->SetDimensions(kFlagRadius, kFlagHeight - 2 * kFlagRadius, 0,
                       kFlagMassRadius, kFlagMassHeight, 0.0f,
                       kFlagDensity * density_scale);
}

FlagNode::~FlagNode() {
  if (area_of_interest_)
    g_base->graphics->camera()->DeleteAreaOfInterest(area_of_interest_);
}

void FlagNode::HandleMessage(const char* data_in) {
  const char* data = data_in;
  bool handled = true;

  switch (extract_node_message_type(&data)) {
    case NodeMessageType::kFooting: {
      footing_ += Utils::ExtractInt8(&data);
      break;
    }

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

      float force_dir_x = Utils::ExtractFloat16NBO(&data);
      float force_dir_y = Utils::ExtractFloat16NBO(&data);
      float force_dir_z = Utils::ExtractFloat16NBO(&data);

      float applied_mag = body_->ApplyImpulse(
          px, py, pz, vx, vy, vz, force_dir_x, force_dir_y, force_dir_z,
          0.2f * mag, 0.2f * velocity_mag, radius, false);

      Vector3f to_flag =
          Vector3f(px, py, pz) - Vector3f(dBodyGetPosition(body_->body()));
      to_flag *= -0.0001f * applied_mag / to_flag.Length();

      flag_impulse_add_x_ += to_flag.x;
      flag_impulse_add_y_ += to_flag.y;
      flag_impulse_add_z_ += to_flag.z;

      have_flag_impulse_ = true;
      break;
    }
    default:
      handled = false;
      break;
  }
  if (!handled) Node::HandleMessage(data_in);
}

void FlagNode::Draw(base::FrameDef* frame_def) {
  if (graphics_quality_ != frame_def->quality()) {
    graphics_quality_ = frame_def->quality();
    UpdateForGraphicsQuality(graphics_quality_);
  }

  // Flag cloth.
  {
    // Update the dynamic portion of our mesh data.
    // FIXME - should move this all to BG dynamics thread
    auto v_dynamic(
        Object::New<base::MeshBuffer<base::VertexObjectSplitDynamic>>(25));

    base::VertexObjectSplitDynamic* vd = &v_dynamic->elements[0];
    for (int i = 0; i < 25; i++) {
      vd[i].position[0] = flag_points_[i].x;
      vd[i].position[1] = flag_points_[i].y;
      vd[i].position[2] = flag_points_[i].z;
      vd[i].normal[0] = static_cast_check_fit<int16_t>(std::max(
          -32767,
          std::min(32767, static_cast<int>(flag_normals_[i].x * 32767.0f))));
      vd[i].normal[1] = static_cast_check_fit<int16_t>(std::max(
          -32767,
          std::min(32767, static_cast<int>(flag_normals_[i].y * 32767.0f))));
      vd[i].normal[2] = static_cast_check_fit<int16_t>(std::max(
          -32767,
          std::min(32767, static_cast<int>(flag_normals_[i].z * 32767.0f))));
    }
    mesh_.SetDynamicData(v_dynamic);

    // Render a subtle sharp shadow in higher quality modes.
    if (frame_def->quality() > base::GraphicsQuality::kLow) {
      base::SimpleComponent c(frame_def->light_shadow_pass());
      c.SetTransparent(true);
      c.SetColor(color_[0] * 0.1f, color_[1] * 0.1f, color_[2] * 0.1f, 0.02f);
      c.SetDoubleSided(true);
      c.DrawMesh(&mesh_);
      c.Submit();
    }

    // Now beauty pass.
    {
      base::ObjectComponent c(frame_def->beauty_pass());
      c.SetWorldSpace(true);
      c.SetColor(color_[0], color_[1], color_[2]);
      c.SetReflection(base::ReflectionType::kSoft);
      c.SetReflectionScale(0.05f, 0.05f, 0.05f);
      c.SetDoubleSided(true);
      c.SetTexture(color_texture_->texture_data());
      c.DrawMesh(&mesh_);
      c.Submit();
    }

    float s_scale, s_density;
    base::SimpleComponent c(frame_def->light_shadow_pass());
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kShadow));
    c.SetTransparent(true);

    // Update our shadow objects.
    if (!g_core->HeadlessMode()) {
      dBodyID b = body_->body();
      assert(b);
      dVector3 p;
      if (FullShadowSet* full_shadows = full_shadow_set_.Get()) {
        full_shadows->shadow_flag_.SetPosition(
            flag_points_[kFlagSizeX * (kFlagSizeY / 2) + (kFlagSizeX / 2)]);
        dBodyGetRelPointPos(b, 0, 0, kFlagHeight * -0.4f, p);
        full_shadows->shadow_pole_bottom_.SetPosition(Vector3f(p));
        full_shadows->shadow_pole_middle_.SetPosition(
            Vector3f(dBodyGetPosition(b)));
        dBodyGetRelPointPos(b, 0, 0, kFlagHeight * 0.4f, p);
        full_shadows->shadow_pole_top_.SetPosition(Vector3f(p));
        // Pole bottom.
        {
          full_shadows->shadow_pole_bottom_.GetValues(&s_scale, &s_density);
          const Vector3f& p(full_shadows->shadow_pole_bottom_.GetPosition());
          g_base->graphics->DrawBlotch(p, 0.4f * s_scale, 0, 0, 0,
                                       s_density * 0.25f);
        }

        // Pole middle.
        {
          full_shadows->shadow_pole_middle_.GetValues(&s_scale, &s_density);
          const Vector3f& p(full_shadows->shadow_pole_middle_.GetPosition());
          g_base->graphics->DrawBlotch(p, 0.4f * s_scale, 0, 0, 0,
                                       s_density * 0.25f);
        }

        // Pole top.
        {
          full_shadows->shadow_pole_middle_.GetValues(&s_scale, &s_density);
          const Vector3f& p(full_shadows->shadow_pole_top_.GetPosition());
          g_base->graphics->DrawBlotch(p, 0.4f * s_scale, 0, 0, 0,
                                       s_density * 0.25f);
        }

        // Flag center.
        {
          full_shadows->shadow_flag_.GetValues(&s_scale, &s_density);
          const Vector3f& p(full_shadows->shadow_flag_.GetPosition());
          g_base->graphics->DrawBlotch(p, 0.8f * s_scale, 0, 0, 0,
                                       s_density * 0.3f);
        }

      } else if (SimpleShadowSet* simple_shadows = simple_shadow_set_.Get()) {
        dBodyGetRelPointPos(b, 0, 0, kFlagHeight * -0.3f, p);
        simple_shadows->shadow_.SetPosition(Vector3f(p));
        simple_shadows->shadow_.GetValues(&s_scale, &s_density);
        const Vector3f& p(simple_shadows->shadow_.GetPosition());
        g_base->graphics->DrawBlotch(p, 0.8f * s_scale, 0, 0, 0,
                                     s_density * 0.5f);
      }
    }
    c.Submit();
  }

  // Flag pole.
  {
    base::ObjectComponent c(frame_def->beauty_pass());
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kFlagPole));
    c.SetReflection(base::ReflectionType::kSharp);
    c.SetReflectionScale(0.1f, 0.1f, 0.1f);
    {
      auto xf = c.ScopedTransform();
      body_->ApplyToRenderComponent(&c);
      c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kFlagPole));
    }
    c.Submit();
  }
}

void FlagNode::UpdateAreaOfInterest() {
  base::AreaOfInterest* aoi = area_of_interest_;
  if (!aoi) return;
  assert(body_.Exists());
  aoi->set_position(Vector3f(dGeomGetPosition(body_->geom())));
  aoi->SetRadius(5.0f);
}

void FlagNode::Step() {
  // On happy thoughts, keep us on the 2d plane.
  if (g_base->graphics->camera()->happy_thoughts_mode() && body_.Exists()) {
    dBodyID b;
    const dReal *p, *v;
    b = body_->body();
    p = dBodyGetPosition(b);
    float smoothing = 0.98f;
    dBodySetPosition(
        b, p[0], p[1],
        p[2] * smoothing + (1.0f - smoothing) * base::kHappyThoughtsZPlane);
    v = dBodyGetLinearVel(b);
    dBodySetLinearVel(b, v[0], v[1], v[2] * smoothing);
  }

  // update our area-of-interest if we have one
  UpdateAreaOfInterest();

  // FIXME: This should probably happen for RBDs automatically?
  body_->UpdateBlending();

  if (dBodyIsEnabled(body_->body())) {
    // Try to keep upright by pushing the top of the
    // flag to be above the bottom.
    {
      float force_mag = 40.0f;
      float force_max = 40.0f;
      float min_dist = 0.05f;

      if (light_weight_) {
        force_mag *= 0.3f;
        force_max *= 0.3f;
      }
      dVector3 bottom, top;
      dBodyGetRelPointPos(body_->body(), 0, 0, kFlagHeight / 2.0f, top);
      dBodyGetRelPointPos(body_->body(), 0, 0, -kFlagHeight / 2.0f, bottom);
      Vector3f top_v(top[0], top[1], top[2]);
      Vector3f bot_v(bottom[0], bottom[1], bottom[2]);
      Vector3f target_v(bot_v.x, bot_v.y + kFlagHeight, bot_v.z);
      if ((std::abs(target_v.x - top_v.x) > min_dist)
          || (std::abs(target_v.y - top_v.y) > min_dist)
          || (std::abs(target_v.z - top_v.z) > min_dist)) {
        dBodyEnable(body_->body());
        Vector3f fV((target_v - top_v) * force_mag);
        float mag = fV.Length();
        if (mag > force_max) fV *= force_max / mag;
        dBodyAddForceAtPos(body_->body(), fV.x, fV.y, fV.z, top_v.x, top_v.y,
                           top_v.z);
        dBodyAddForceAtPos(body_->body(), -fV.x, -fV.y, -fV.z, bot_v.x, bot_v.y,
                           bot_v.z);
      }
    }

    // Apply damping force.
    float linear_damping_x = 1.0f;
    float linear_damping_y = 1.0f;
    float linear_damping_z = 1.0f;
    float rotational_damping_x = 1.0f;
    float rotational_damping_y = 1.0f;
    float rotational_damping_z = 1.0f;

    if (light_weight_) {
      linear_damping_x *= 0.3f;
      linear_damping_y *= 0.3f;
      linear_damping_z *= 0.3f;
      rotational_damping_x *= 0.3f;
      rotational_damping_y *= 0.3f;
      rotational_damping_z *= 0.3f;
    }

    // Don't add forces if we're asleep otherwise we'll explode when we wake up.
    dMass mass;
    dBodyGetMass(body_->body(), &mass);

    const dReal* vel;
    dReal force[3];
    vel = dBodyGetAngularVel(body_->body());
    force[0] = -1 * mass.mass * vel[0] * rotational_damping_x;
    force[1] = -1 * mass.mass * vel[1] * rotational_damping_y;
    force[2] = -1 * mass.mass * vel[2] * rotational_damping_z;
    dBodyAddTorque(body_->body(), force[0], force[1], force[2]);

    vel = dBodyGetLinearVel(body_->body());
    force[0] = -1 * mass.mass * vel[0] * linear_damping_x;
    force[1] = -1 * mass.mass * vel[1] * linear_damping_y;
    force[2] = -1 * mass.mass * vel[2] * linear_damping_z;
    dBodyAddForce(body_->body(), force[0], force[1], force[2]);

    // If we're out of bounds, arrange to have ourself informed.
    {
      const dReal* p2 = dBodyGetPosition(body_->body());
      if (scene()->IsOutOfBounds(p2[0], p2[1], p2[2])) {
        scene()->AddOutOfBoundsNode(this);
      }
    }
  }
  UpdateFlagMesh();
}

auto FlagNode::GetRigidBody(int id) -> RigidBody* { return body_.Get(); }

static auto FlagPointIndex(int x, int y) -> int {
  return kFlagSizeX * (y) + (x);
}

void FlagNode::UpdateSpringPoint(int p1, int p2, float rest_length) {
  Vector3f d = flag_points_[p2] - flag_points_[p1];
  float mag = d.Length();
  if (mag > (rest_length + 0.05f)) {
    mag = rest_length + 0.05f;
  }
  Vector3f f = d / mag * kStiffness * (mag - rest_length);
  flag_velocities_[p1] += f;
  flag_velocities_[p2] -= f;
  Vector3f vd =
      kDampingStrength * (flag_velocities_[p1] - flag_velocities_[p2]);
  flag_velocities_[p1] -= vd;
  flag_velocities_[p2] += vd;
}

void FlagNode::ResetFlagMesh() {
  dVector3 up, side, top;
  dBodyGetRelPointPos(body_->body(), 0, 0, kFlagHeight / 2, top);
  dBodyVectorToWorld(body_->body(), 0, 0, 1, up);
  dBodyVectorToWorld(body_->body(), 1, 0, 0, side);
  Vector3f up_v(up);
  Vector3f side_v(side);
  Vector3f top_v(top);
  up_v *= kFlagCanvasScaleY;
  side_v *= kFlagCanvasScaleX;
  for (int y = 0; y < kFlagSizeY; y++) {
    for (int x = 0; x < kFlagSizeX; x++) {
      int i = kFlagSizeX * y + x;
      Vector3f p =
          top_v - up_v * static_cast<float>(y) + side_v * static_cast<float>(x);
      flag_points_[i].x = p.x;
      flag_points_[i].y = p.y;
      flag_points_[i].z = p.z;
      flag_velocities_[i] = kVector3f0;
    }
  }
  flag_impulse_add_x_ = flag_impulse_add_y_ = flag_impulse_add_z_ = 0;
  have_flag_impulse_ = false;
}

void FlagNode::UpdateFlagMesh() {
  dVector3 up, top;
  dBodyGetRelPointPos(body_->body(), 0, 0, kFlagHeight / 2, top);
  dBodyVectorToWorld(body_->body(), 0, 0, 1, up);
  Vector3f up_v(up);
  Vector3f top_v(top);
  up_v *= kFlagCanvasScaleY;

  // Move our attachment points into place.
  for (int y = 0; y < kFlagSizeY; y++) {
    int i = kFlagSizeX * y;
    Vector3f p = top_v - up_v * static_cast<float>(y);
    flag_points_[i].x = p.x;
    flag_points_[i].y = p.y;
    flag_points_[i].z = p.z;
    flag_velocities_[i] = kVector3f0;
  }

  // Push our flag points around.
  const dReal* flag_vel = dBodyGetLinearVel(body_->body());
  Vector3f wind_vec = {0.0f, 0.0f, 0.0f};
  bool do_wind = true;
  if (RandomFloat() > 0.85f) {
    wind_rand_x_ = 0.5f - RandomFloat();
    wind_rand_y_ = 0.5f - RandomFloat();
    if (scene()->stepnum() % 100 > 50) {
      wind_rand_z_ = RandomFloat();
    } else {
      wind_rand_z_ = -RandomFloat();
    }
    wind_rand_ = static_cast<int>(scene()->stepnum());
  }

  if (explicit_bool(do_wind)) {
    wind_vec = -2.0f * Vector3f(flag_vel[0], flag_vel[1], flag_vel[2]);

    // If the flag is moving less than 1.0, add some ambient wind.
    if (wind_vec.LengthSquared() < 1.0f) {
      wind_vec += (1.0f - wind_vec.LengthSquared()) * Vector3f(5, 0, 0);
    }
    wind_vec +=
        3.0f
        * Vector3f(0.15f * wind_rand_x_, wind_rand_y_, 1.5f * wind_rand_z_);
  }

  for (int y = 0; y < kFlagSizeY - 1; y++) {
    for (int x = 0; x < kFlagSizeX - 1; x++) {
      int top_left, top_right, bot_left, bot_right;
      top_left = FlagPointIndex(x, y);
      top_right = FlagPointIndex(x + 1, y);
      bot_left = FlagPointIndex(x, y + 1);
      bot_right = FlagPointIndex(x + 1, y + 1);
      flag_velocities_[top_left].y -= kGravityStrength;
      flag_velocities_[top_right].y -= kGravityStrength;
      flag_velocities_[top_right].x *= (1.0f - kDragStrength);
      flag_velocities_[top_right].y *= (1.0f - kDragStrength);
      flag_velocities_[top_right].z *= (1.0f - kDragStrength);
      if (have_flag_impulse_) {
        flag_velocities_[top_left].x += flag_impulse_add_x_;
        flag_velocities_[top_left].y += flag_impulse_add_y_;
        flag_velocities_[top_left].z += flag_impulse_add_z_;
        flag_velocities_[top_right].x += flag_impulse_add_x_;
        flag_velocities_[top_right].y += flag_impulse_add_y_;
        flag_velocities_[top_right].z += flag_impulse_add_z_;
      }

      // Wind.
      // FIXME - we can prolly move some of this out of the inner loop..
      if (explicit_bool(do_wind)) {
        flag_velocities_[top_right].x +=
            wind_vec.x * kWindStrength
            * (Utils::precalc_rand_1(wind_rand_ % kPrecalcRandsCount) - 0.3f);
        flag_velocities_[top_right].y +=
            wind_vec.y * kWindStrength
            * (Utils::precalc_rand_2(wind_rand_ % kPrecalcRandsCount) - 0.3f);
        flag_velocities_[top_right].z +=
            wind_vec.z * kWindStrength
            * (Utils::precalc_rand_3(wind_rand_ % kPrecalcRandsCount) - 0.3f);
      }
      UpdateSpringPoint(top_left, top_right, kFlagCanvasScaleX);
      UpdateSpringPoint(bot_left, bot_right, kFlagCanvasScaleX);
      UpdateSpringPoint(top_left, bot_left, kFlagCanvasScaleY);
      UpdateSpringPoint(top_right, bot_right, kFlagCanvasScaleY);
      UpdateSpringPoint(top_left, bot_right, kFlagCanvasScaleDiagonal);
      UpdateSpringPoint(top_right, bot_left, kFlagCanvasScaleDiagonal);
    }
  }

  flag_impulse_add_x_ = flag_impulse_add_y_ = flag_impulse_add_z_ = 0;

  // Now update positions (except pole points).
  for (int y = 0; y < kFlagSizeY; y++) {
    for (int x = 0; x < kFlagSizeX; x++) {
      int i = kFlagSizeX * y + x;
      flag_points_[i] += flag_velocities_[i];
    }
  }

  // Now calc normals.
  for (int y = 0; y < kFlagSizeY; y++) {
    for (int x = 0; x < kFlagSizeX; x++) {
      // Calc the normal for this vert.
      int xclamped = std::min(x, kFlagSizeX - 2);
      int yclamped = std::min(y, kFlagSizeY - 2);
      int i = kFlagSizeX * yclamped + xclamped;
      flag_normals_[i] =
          Vector3f::Cross(flag_points_[i + 1] - flag_points_[i],
                          flag_points_[i + kFlagSizeX] - flag_points_[i])
              .Normalized();
    }
  }
}

void FlagNode::GetRigidBodyPickupLocations(int id, float* obj, float* character,
                                           float* hand1, float* hand2) {
  obj[0] = 0;
  obj[1] = 0;
  obj[2] = -0.6f;
  character[0] = 0;
  character[1] = -0.4f;
  character[2] = 0.3f;
  hand1[0] = hand1[1] = hand1[2] = 0;
  hand2[0] = hand2[1] = hand2[2] = 0;
  hand2[0] = 0.05f;
  hand2[2] = -0.1f;
  hand1[0] = -0.05f;
  hand1[2] = -0.05f;
}

void FlagNode::UpdateForGraphicsQuality(base::GraphicsQuality quality) {
  if (!g_core->HeadlessMode()) {
    if (quality >= base::GraphicsQuality::kMedium) {
      full_shadow_set_ = Object::New<FullShadowSet>();
      simple_shadow_set_.Clear();
    } else {
      simple_shadow_set_ = Object::New<SimpleShadowSet>();
      full_shadow_set_.Clear();
    }
  }
}

}  // namespace ballistica::scene_v1
