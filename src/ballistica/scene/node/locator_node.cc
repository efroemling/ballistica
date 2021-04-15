// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene/node/locator_node.h"

#include "ballistica/graphics/component/simple_component.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/scene/node/node_type.h"

namespace ballistica {

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

void LocatorNode::Draw(FrameDef* frame_def) {
  SystemModelID model;
  if (shape_ == Shape::kBox) {
    model = SystemModelID::kLocatorBox;
  } else if (shape_ == Shape::kCircle) {
    model = SystemModelID::kLocatorCircle;
  } else if (shape_ == Shape::kCircleOutline) {
    model = SystemModelID::kLocatorCircleOutline;
  } else {
    model = SystemModelID::kLocator;
  }

  SystemTextureID texture;
  if (shape_ == Shape::kCircle) {
    texture =
        additive_ ? SystemTextureID::kCircleNoAlpha : SystemTextureID::kCircle;
  } else if (shape_ == Shape::kCircleOutline) {
    texture = additive_ ? SystemTextureID::kCircleOutlineNoAlpha
                        : SystemTextureID::kCircleOutline;
  } else {
    texture = SystemTextureID::kRGBStripes;
  }

  bool transparent = false;
  if (shape_ == Shape::kCircle || shape_ == Shape::kCircleOutline) {
    transparent = true;
  }

  // beauty
  if (draw_beauty_) {
    SimpleComponent c(frame_def->beauty_pass());
    if (transparent) {
      c.SetTransparent(true);
    }
    c.SetColor(color_[0], color_[1], color_[2], opacity_);
    c.SetTexture(g_media->GetTexture(texture));
    c.PushTransform();
    c.Translate(position_[0], position_[1], position_[2]);
    c.Scale(size_[0], size_[1], size_[2]);
    c.DrawModel(g_media->GetModel(model));
    c.PopTransform();
    c.Submit();
  }

  if (draw_shadow_) {
    // colored shadow for circle
    if (shape_ == Shape::kCircle || shape_ == Shape::kCircleOutline) {
      SimpleComponent c(frame_def->light_shadow_pass());
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
      c.SetTexture(g_media->GetTexture(texture));
      c.PushTransform();
      c.Translate(position_[0], position_[1], position_[2]);
      c.Scale(size_[0], size_[1], size_[2]);
      c.DrawModel(g_media->GetModel(model));
      c.PopTransform();
      c.Submit();
    } else {
      // simple black shadow for locator/box
      SimpleComponent c(frame_def->light_shadow_pass());
      c.SetTransparent(true);
      c.SetColor(0.4f, 0.4f, 0.4f, 0.7f);
      c.PushTransform();
      c.Translate(position_[0], position_[1], position_[2]);
      c.Scale(size_[0], size_[1], size_[2]);
      c.DrawModel(g_media->GetModel(model));
      c.PopTransform();
      c.Submit();
    }
  }
}

}  // namespace ballistica
