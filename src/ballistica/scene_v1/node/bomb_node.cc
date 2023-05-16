// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/bomb_node.h"

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

const float kFuseOffset = 0.35f;

// Returns noise value between 0 and 1.
// TODO(ericf): Need to interpolate between 2 values.
static auto SimpleNoise(uint32_t x) -> float {
  x = (x << 13u) ^ x;
  return (0.5f
          * static_cast<float>((x * (x * x * 15731u + 789221u) + 1376312589u)
                               & 0x7fffffffu)
          / 1073741824.0f);
}

class BombNodeType : public PropNodeType {
 public:
#define BA_NODE_TYPE_CLASS BombNode
  BA_NODE_CREATE_CALL(CreateBomb);
  BA_FLOAT_ATTR(fuse_length, fuse_length, set_fuse_length);
#undef BA_NODE_TYPE_CLASS

  BombNodeType() : PropNodeType("bomb", CreateBomb), fuse_length(this) {}
};

static NodeType* node_type{};

auto BombNode::InitType() -> NodeType* {
  node_type = new BombNodeType();
  return node_type;
}

BombNode::BombNode(Scene* scene) : PropNode(scene, node_type) {}

void BombNode::OnCreate() {
  // We can't do this in our constructor because
  // it would prevent the user from setting density/etc. attrs.
  // (user attrs get applied after constructors fire)
  SetBody("sphere");
}

void BombNode::Step() {
  PropNode::Step();
  if (body_.Exists()) {
    // Update our fuse and light position.
    dVector3 fuse_tip_pos;
    dGeomGetRelPointPos(body_->geom(), 0, (fuse_length_ + kFuseOffset), 0,
                        fuse_tip_pos);
    light_translate_.x = fuse_tip_pos[0] + body_->blend_offset().x;
    light_translate_.y = fuse_tip_pos[1] + body_->blend_offset().y;
    light_translate_.z = fuse_tip_pos[2] + body_->blend_offset().z;
#if !BA_HEADLESS_BUILD
    fuse_.SetTransform(Matrix44fTranslate(0, kFuseOffset * mesh_scale_, 0)
                       * body_->GetTransform());
    fuse_.SetLength(fuse_length_);
#endif  // !BA_HEADLESS_BUILD
  }
}

void BombNode::Draw(base::FrameDef* frame_def) {
#if !BA_HEADLESS_BUILD
  PropNode::Draw(frame_def);
  float s_scale, s_density;
  shadow_.GetValues(&s_scale, &s_density);
  float intensity = SimpleNoise(static_cast<uint32_t>(id() + scene()->time()))
                    * s_density * 0.2f;
  float s = 4.0f * s_scale;
  float r = 1.5f * intensity;
  float g = 0.1f * intensity;
  float b = 0.1f * intensity;
  float a = 0.0f;
  g_base->graphics->DrawBlotchSoft(light_translate_, s, r, g, b, a);
  g_base->graphics->DrawBlotchSoftObj(light_translate_, s, r, g, b, a);
#endif  // !BA_HEADLESS_BUILD
}

}  // namespace ballistica::scene_v1
