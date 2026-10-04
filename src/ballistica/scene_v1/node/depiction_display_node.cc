// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/depiction_display_node.h"

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/scene_depiction.h"

namespace ballistica::scene_v1 {

class DepictionDisplayNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS DepictionDisplayNode
  BA_NODE_CREATE_CALL(CreateDepictionDisplay);
  BA_DEPICTION_ATTR(depiction, depiction, SetDepiction);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ARRAY_ATTR(scale, scale, SetScale);
  BA_FLOAT_ATTR(opacity, opacity, set_opacity);
  BA_STRING_ATTR(attach, GetAttach, SetAttach);
  BA_STRING_ATTR(h_align, GetHAlign, SetHAlign);
  BA_STRING_ATTR(v_align, GetVAlign, SetVAlign);
  BA_FLOAT_ATTR(vr_depth, vr_depth, set_vr_depth);
  BA_BOOL_ATTR(host_only, host_only, set_host_only);
  BA_BOOL_ATTR(front, front, set_front);
#undef BA_NODE_TYPE_CLASS

  DepictionDisplayNodeType()
      : NodeType("depictiondisplay", CreateDepictionDisplay),
        depiction(this),
        position(this),
        scale(this),
        opacity(this),
        attach(this),
        h_align(this),
        v_align(this),
        vr_depth(this),
        host_only(this),
        front(this) {}
};

static NodeType* node_type{};

auto DepictionDisplayNode::InitType() -> NodeType* {
  node_type = new DepictionDisplayNodeType();
  return node_type;
}

DepictionDisplayNode::DepictionDisplayNode(Scene* scene)
    : Node(scene, node_type) {}

DepictionDisplayNode::~DepictionDisplayNode() = default;

void DepictionDisplayNode::SetDepiction(SceneDepiction* val) {
  depiction_obj_ = val;
  // Headless machines draw nothing, so don't bother making one there.
  if (g_core->HeadlessMode() || !val) {
    depiction_.Clear();
    return;
  }
  depiction_ = base::DepictionRegistry::Create(val->json(),
                                               base::DepictionHost::kScene, "");
}

void DepictionDisplayNode::SetPosition(const std::vector<float>& val) {
  if (val.size() != 2) {
    throw Exception("Expected float array of size 2 for position",
                    PyExcType::kValue);
  }
  position_ = val;
  dirty_ = true;
}

void DepictionDisplayNode::SetScale(const std::vector<float>& val) {
  if (val.empty() || val.size() > 2) {
    throw Exception("Expected float array of size 1 or 2 for scale",
                    PyExcType::kValue);
  }
  scale_ = val;
  dirty_ = true;
}

auto DepictionDisplayNode::GetAttach() const -> std::string {
  switch (attach_) {
    case Attach::kCenter:
      return "center";
    case Attach::kTopLeft:
      return "topLeft";
    case Attach::kTopCenter:
      return "topCenter";
    case Attach::kTopRight:
      return "topRight";
    case Attach::kCenterRight:
      return "centerRight";
    case Attach::kBottomRight:
      return "bottomRight";
    case Attach::kBottomCenter:
      return "bottomCenter";
    case Attach::kBottomLeft:
      return "bottomLeft";
    case Attach::kCenterLeft:
      return "centerLeft";
  }
  throw Exception();
}

void DepictionDisplayNode::SetAttach(const std::string& val) {
  dirty_ = true;
  if (val == "center") {
    attach_ = Attach::kCenter;
  } else if (val == "topLeft") {
    attach_ = Attach::kTopLeft;
  } else if (val == "topCenter") {
    attach_ = Attach::kTopCenter;
  } else if (val == "topRight") {
    attach_ = Attach::kTopRight;
  } else if (val == "centerRight") {
    attach_ = Attach::kCenterRight;
  } else if (val == "bottomRight") {
    attach_ = Attach::kBottomRight;
  } else if (val == "bottomCenter") {
    attach_ = Attach::kBottomCenter;
  } else if (val == "bottomLeft") {
    attach_ = Attach::kBottomLeft;
  } else if (val == "centerLeft") {
    attach_ = Attach::kCenterLeft;
  } else {
    throw Exception("Invalid attach value for DepictionDisplayNode: " + val,
                    PyExcType::kValue);
  }
}

auto DepictionDisplayNode::GetHAlign() const -> std::string {
  switch (h_align_) {
    case base::DepictionHAlign::kLeft:
      return "left";
    case base::DepictionHAlign::kCenter:
      return "center";
    case base::DepictionHAlign::kRight:
      return "right";
  }
  throw Exception();
}

void DepictionDisplayNode::SetHAlign(const std::string& val) {
  if (val == "left") {
    h_align_ = base::DepictionHAlign::kLeft;
  } else if (val == "center") {
    h_align_ = base::DepictionHAlign::kCenter;
  } else if (val == "right") {
    h_align_ = base::DepictionHAlign::kRight;
  } else {
    throw Exception("Invalid h_align value for DepictionDisplayNode: " + val,
                    PyExcType::kValue);
  }
}

auto DepictionDisplayNode::GetVAlign() const -> std::string {
  switch (v_align_) {
    case base::DepictionVAlign::kBottom:
      return "bottom";
    case base::DepictionVAlign::kCenter:
      return "center";
    case base::DepictionVAlign::kTop:
      return "top";
  }
  throw Exception();
}

void DepictionDisplayNode::SetVAlign(const std::string& val) {
  if (val == "bottom") {
    v_align_ = base::DepictionVAlign::kBottom;
  } else if (val == "center") {
    v_align_ = base::DepictionVAlign::kCenter;
  } else if (val == "top") {
    v_align_ = base::DepictionVAlign::kTop;
  } else {
    throw Exception("Invalid v_align value for DepictionDisplayNode: " + val,
                    PyExcType::kValue);
  }
}

void DepictionDisplayNode::UpdateLayout_(float screen_width,
                                         float screen_height) {
  width_ = scale_[0];
  height_ = scale_.size() > 1 ? scale_[1] : scale_[0];
  float tx = position_[0];
  float ty = position_[1];
  switch (attach_) {
    case Attach::kBottomLeft:
    case Attach::kBottomCenter:
    case Attach::kBottomRight:
      center_y_ = ty;
      break;
    case Attach::kTopLeft:
    case Attach::kTopCenter:
    case Attach::kTopRight:
      center_y_ = screen_height + ty;
      break;
    case Attach::kCenterLeft:
    case Attach::kCenterRight:
    case Attach::kCenter:
      center_y_ = screen_height * 0.5f + ty;
      break;
  }
  switch (attach_) {
    case Attach::kTopLeft:
    case Attach::kCenterLeft:
    case Attach::kBottomLeft:
      center_x_ = tx;
      break;
    case Attach::kTopCenter:
    case Attach::kCenter:
    case Attach::kBottomCenter:
      center_x_ = screen_width * 0.5f + tx;
      break;
    case Attach::kTopRight:
    case Attach::kCenterRight:
    case Attach::kBottomRight:
      center_x_ = screen_width + tx;
      break;
  }
  dirty_ = false;
}

void DepictionDisplayNode::Draw(base::FrameDef* frame_def) {
  if (!depiction_.exists()) {
    return;
  }
  if (host_only_ && !context_ref().GetHostSession()) {
    return;
  }
  // Media retries etc. run on scene time, like everything else here.
  depiction_->MarkShown();
  depiction_->Update(static_cast<millisecs_t>(scene()->time()));

  bool vr = g_core->vr_mode();
  bool vr_use_fixed = vr && scene()->use_fixed_vr_overlay();
  if (front_) {
    vr_use_fixed = false;
  }
  base::RenderPass& pass(*(vr_use_fixed ? frame_def->GetOverlayFixedPass()
                           : front_     ? frame_def->overlay_front_pass()
                                        : frame_def->overlay_pass()));
  if (dirty_) {
    UpdateLayout_(pass.virtual_width(), pass.virtual_height());
  }

  base::DepictionDrawContext context;
  context.pass = &pass;
  context.transparent = true;
  context.box = base::FitDepictionBox(
      {center_x_ - width_ * 0.5f, center_y_ - height_ * 0.5f, width_, height_},
      *depiction_, h_align_, v_align_);
  context.z = vr ? vr_depth_ : g_base->graphics->overlay_node_z_depth();
  context.opacity = std::max(0.0f, opacity_);
  // Overlay units are virtual screen units.
  float virtual_width = g_base->graphics->screen_virtual_width();
  context.pixels_per_unit =
      virtual_width > 0.0f
          ? g_base->graphics->virtual_bounds_rect().width() / virtual_width
          : 1.0f;
  depiction_->Draw(context);
}

}  // namespace ballistica::scene_v1
