// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/locator_node.h"

#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class LocatorNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS LocatorNode
  BA_NODE_CREATE_CALL(CreateLocator);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_BOOL_ATTR(visibility, visibility, set_visibility);
  BA_FLOAT_ARRAY_ATTR(size, size, SetSize);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_FLOAT_ATTR(opacity, opacity, set_opacity);
  BA_BOOL_ATTR(draw_beauty, draw_beauty, set_draw_beauty);
  BA_BOOL_ATTR(drawShadow, getDrawShadow, setDrawShadow);
  BA_STRING_ATTR(shape, getShape, SetShape);
  BA_BOOL_ATTR(additive, getAdditive, setAdditive);
#undef BA_NODE_TYPE_CLASS
  LocatorNodeType()
      : NodeType("locator", CreateLocator),
        position(this),
        visibility(this),
        size(this),
        color(this),
        opacity(this),
        draw_beauty(this),
        drawShadow(this),
        shape(this),
        additive(this) {}
};
static NodeType* node_type{};

auto LocatorNode::InitType() -> NodeType* {
  node_type = new LocatorNodeType();
  return node_type;
}

LocatorNode::LocatorNode(Scene* scene) : Node(scene, node_type) {}

auto LocatorNode::getShape() const -> std::string {
  switch (shape_) {
    case Shape::kBox:
      return "box";
    case Shape::kCircle:
      return "circle";
    case Shape::kCircleOutline:
      return "circleOutline";
    case Shape::kLocator:
      return "locator";
  }

    // This should be unreachable, but most compilers complain about
    // control reaching the end of non-void function without it.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
  throw Exception();
#pragma clang diagnostic pop
}

void LocatorNode::SetShape(const std::string& val) {
  if (val == "box") {
    shape_ = Shape::kBox;
  } else if (val == "circle") {
    shape_ = Shape::kCircle;
  } else if (val == "circleOutline") {
    shape_ = Shape::kCircleOutline;
  } else if (val == "locator") {
    shape_ = Shape::kLocator;
  } else {
    throw Exception("invalid locator shape: " + val);
  }
}

void LocatorNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for color",
                    PyExcType::kValue);
  }
  color_ = vals;
}

void LocatorNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for position",
                    PyExcType::kValue);
  }
  position_ = vals;
}

void LocatorNode::SetSize(const std::vector<float>& vals) {
  if (vals.size() != 1 && vals.size() != 3) {
    throw Exception("Expected float array of size 1 or 3 for size",
                    PyExcType::kValue);
  }
  size_ = vals;
  if (size_.size() == 1) {
    size_.push_back(size_[0]);
    size_.push_back(size_[0]);
  }
}

void LocatorNode::Draw(base::FrameDef* frame_def) {
  base::SysMeshID mesh;
  if (shape_ == Shape::kBox) {
    mesh = base::SysMeshID::kLocatorBox;
  } else if (shape_ == Shape::kCircle) {
    mesh = base::SysMeshID::kLocatorCircle;
  } else if (shape_ == Shape::kCircleOutline) {
    mesh = base::SysMeshID::kLocatorCircleOutline;
  } else {
    mesh = base::SysMeshID::kLocator;
  }

  base::SysTextureID texture;
  if (shape_ == Shape::kCircle) {
    texture = additive_ ? base::SysTextureID::kCircleNoAlpha
                        : base::SysTextureID::kCircle;
  } else if (shape_ == Shape::kCircleOutline) {
    texture = additive_ ? base::SysTextureID::kCircleOutlineNoAlpha
                        : base::SysTextureID::kCircleOutline;
  } else {
    texture = base::SysTextureID::kRGBStripes;
  }

  bool transparent = false;
  if (shape_ == Shape::kCircle || shape_ == Shape::kCircleOutline) {
    transparent = true;
  }

  // beauty
  if (draw_beauty_) {
    base::SimpleComponent c(frame_def->beauty_pass());
    if (transparent) {
      c.SetTransparent(true);
    }
    c.SetColor(color_[0], color_[1], color_[2], opacity_);
    c.SetTexture(g_base->assets->SysTexture(texture));
    {
      auto xf = c.ScopedTransform();
      c.Translate(position_[0], position_[1], position_[2]);
      c.Scale(size_[0], size_[1], size_[2]);
      c.DrawMeshAsset(g_base->assets->SysMesh(mesh));
    }
    c.Submit();
  }

  if (draw_shadow_) {
    // colored shadow for circle
    if (shape_ == Shape::kCircle || shape_ == Shape::kCircleOutline) {
      base::SimpleComponent c(frame_def->light_shadow_pass());
      assert(transparent);
      c.SetTransparent(true);
      if (additive_) {
        c.SetPremultiplied(true);
      }
      if (additive_) {
        c.SetColor(color_[0] * opacity_, color_[1] * opacity_,
                   color_[2] * opacity_, 0.0f);
      } else {
        c.SetColor(color_[0], color_[1], color_[2], opacity_);
      }
      c.SetTexture(g_base->assets->SysTexture(texture));
      {
        auto xf = c.ScopedTransform();
        c.Translate(position_[0], position_[1], position_[2]);
        c.Scale(size_[0], size_[1], size_[2]);
        c.DrawMeshAsset(g_base->assets->SysMesh(mesh));
      }
      c.Submit();
    } else {
      // simple black shadow for locator/box
      base::SimpleComponent c(frame_def->light_shadow_pass());
      c.SetTransparent(true);
      c.SetColor(0.4f, 0.4f, 0.4f, 0.7f);
      {
        auto xf = c.ScopedTransform();
        c.Translate(position_[0], position_[1], position_[2]);
        c.Scale(size_[0], size_[1], size_[2]);
        c.DrawMeshAsset(g_base->assets->SysMesh(mesh));
      }
      c.Submit();
    }
  }
}

}  // namespace ballistica::scene_v1
