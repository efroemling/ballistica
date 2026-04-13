// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/image_node.h"

#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

class ImageNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS ImageNode
  BA_NODE_CREATE_CALL(CreateImage);
  BA_FLOAT_ARRAY_ATTR(scale, scale, SetScale);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ATTR(opacity, opacity, set_opacity);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_FLOAT_ARRAY_ATTR(tint_color, tint_color, SetTintColor);
  BA_FLOAT_ARRAY_ATTR(tint2_color, tint2_color, SetTint2Color);
  BA_BOOL_ATTR(fill_screen, fill_screen, SetFillScreen);
  BA_BOOL_ATTR(has_alpha_channel, has_alpha_channel, set_has_alpha_channel);
  BA_BOOL_ATTR(absolute_scale, absolute_scale, set_absolute_scale);
  BA_FLOAT_ATTR(tilt_translate, tilt_translate, set_tilt_translate);
  BA_FLOAT_ATTR(rotate, rotate, set_rotate);
  BA_BOOL_ATTR(premultiplied, premultiplied, set_premultiplied);
  BA_STRING_ATTR(attach, GetAttach, SetAttach);
  BA_TEXTURE_ATTR(texture, texture, set_texture);
  BA_TEXTURE_ATTR(tint_texture, tint_texture, set_tint_texture);
  BA_TEXTURE_ATTR(mask_texture, mask_texture, set_mask_texture);
  BA_MESH_ATTR(mesh_opaque, mesh_opaque, set_mesh_opaque);
  BA_MESH_ATTR(mesh_transparent, mesh_transparent, set_mesh_transparent);
  BA_FLOAT_ATTR(vr_depth, vr_depth, set_vr_depth);
  BA_BOOL_ATTR(host_only, host_only, set_host_only);
  BA_BOOL_ATTR(front, front, set_front);
#undef BA_NODE_TYPE_CLASS

  ImageNodeType()
      : NodeType("image", CreateImage),
        scale(this),
        position(this),
        opacity(this),
        color(this),
        tint_color(this),
        tint2_color(this),
        fill_screen(this),
        has_alpha_channel(this),
        absolute_scale(this),
        tilt_translate(this),
        rotate(this),
        premultiplied(this),
        attach(this),
        texture(this),
        tint_texture(this),
        mask_texture(this),
        mesh_opaque(this),
        mesh_transparent(this),
        vr_depth(this),
        host_only(this),
        front(this) {}
};
static NodeType* node_type{};

auto ImageNode::InitType() -> NodeType* {
  node_type = new ImageNodeType();
  return node_type;
}

ImageNode::ImageNode(Scene* scene) : Node(scene, node_type) {}

ImageNode::~ImageNode() {
  if (fill_screen_) {
    scene()->decrement_bg_cover_count();
  }
}

auto ImageNode::GetAttach() const -> std::string {
  switch (attach_) {
    case Attach::CENTER:
      return "center";
    case Attach::TOP_LEFT:
      return "topLeft";
    case Attach::TOP_CENTER:
      return "topCenter";
    case Attach::TOP_RIGHT:
      return "topRight";
    case Attach::CENTER_RIGHT:
      return "centerRight";
    case Attach::BOTTOM_RIGHT:
      return "bottomRight";
    case Attach::BOTTOM_CENTER:
      return "bottomCenter";
    case Attach::BOTTOM_LEFT:
      return "bottomLeft";
    case Attach::CENTER_LEFT:
      return "centerLeft";
  }

    // This should be unreachable, but most compilers complain about
    // control reaching the end of non-void function without it.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
  throw Exception();
#pragma clang diagnostic pop
}

void ImageNode::SetAttach(const std::string& val) {
  dirty_ = true;
  if (val == "center") {
    attach_ = Attach::CENTER;
  } else if (val == "topLeft") {
    attach_ = Attach::TOP_LEFT;
  } else if (val == "topCenter") {
    attach_ = Attach::TOP_CENTER;
  } else if (val == "topRight") {
    attach_ = Attach::TOP_RIGHT;
  } else if (val == "centerRight") {
    attach_ = Attach::CENTER_RIGHT;
  } else if (val == "bottomRight") {
    attach_ = Attach::BOTTOM_RIGHT;
  } else if (val == "bottomCenter") {
    attach_ = Attach::BOTTOM_CENTER;
  } else if (val == "bottomLeft") {
    attach_ = Attach::BOTTOM_LEFT;
  } else if (val == "centerLeft") {
    attach_ = Attach::CENTER_LEFT;
  } else {
    throw Exception("Invalid attach value for ImageNode: " + val);
  }
}

void ImageNode::SetTint2Color(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for tint2_color",
                    PyExcType::kValue);
  }
  tint2_color_ = vals;
  tint2_red_ = tint2_color_[0];
  tint2_green_ = tint2_color_[1];
  tint2_blue_ = tint2_color_[2];
}

void ImageNode::SetTintColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("Expected float array of size 3 for tint_color",
                    PyExcType::kValue);
  }
  tint_color_ = vals;
  tint_red_ = tint_color_[0];
  tint_green_ = tint_color_[1];
  tint_blue_ = tint_color_[2];
}

void ImageNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3 && vals.size() != 4) {
    throw Exception("Got " + std::to_string(vals.size())
                    + " values for 'color'; expected 3 or 4.");
  }
  red_ = vals[0];
  green_ = vals[1];
  blue_ = vals[2];
  if (vals.size() == 4) {
    alpha_ = vals[3];
  } else {
    alpha_ = 1.0f;
  }
  color_ = vals;
}

void ImageNode::SetScale(const std::vector<float>& vals) {
  if (vals.size() != 1 && vals.size() != 2) {
    throw Exception("Expected float array of length 1 or 2 for scale",
                    PyExcType::kValue);
  }
  dirty_ = true;
  scale_ = vals;
}

void ImageNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 2) {
    throw Exception("Expected float array of length 2 for position",
                    PyExcType::kValue);
  }
  dirty_ = true;
  position_ = vals;
}

void ImageNode::OnScreenSizeChange() { dirty_ = true; }

void ImageNode::SetFillScreen(bool val) {
  bool old = fill_screen_;
  fill_screen_ = val;
  dirty_ = true;

  // Help the scene keep track of stuff that covers the whole background
  // (so it knows it doesnt have to clear).
  if (!old && fill_screen_) {
    scene()->increment_bg_cover_count();
  }
  if (old && !fill_screen_) {
    scene()->decrement_bg_cover_count();
  }

  // We keep track of how many full-screen images are present at any given time.
  // vr-mode uses this to lock down the overlay layer's position in that case.
}

void ImageNode::Draw(base::FrameDef* frame_def) {
  if (host_only_ && !context_ref().GetHostSession()) {
    return;
  }
  bool vr = g_core->vr_mode();

  // In vr mode we use the fixed overlay position if our scene
  // is set for that.
  bool vr_use_fixed = scene()->use_fixed_vr_overlay();

  // Currently front and vr-fixed are mutually-exclusive.. need to fix.
  if (front_) {
    vr_use_fixed = false;
  }

  base::RenderPass& pass(*(vr_use_fixed ? frame_def->GetOverlayFixedPass()
                           : front_     ? frame_def->overlay_front_pass()
                                        : frame_def->overlay_pass()));

  // If the pass we're drawing into changes dimensions, recalc.
  // Otherwise we break if a window is resized.
  float screen_width = pass.virtual_width();
  float screen_height = pass.virtual_height();
  if (dirty_) {
    float width = absolute_scale_ ? scale_[0] : screen_height * scale_[0];
    float height =
        (scale_.size() > 1)
            ? (absolute_scale_ ? scale_[1] : screen_height * scale_[1])
            : width;
    float center_x, center_y;
    float scale_mult_x = absolute_scale_ ? 1.0f : screen_width;
    float scale_mult_y = absolute_scale_ ? 1.0f : screen_height;
    float screen_center_x = screen_width / 2;
    float screen_center_y = screen_height / 2;
    float tx = position_[0];
    float ty = position_[1];
    if (!absolute_scale_) {
      tx *= scale_mult_x;
      ty *= scale_mult_y;
    }
    switch (attach_) {
      case Attach::BOTTOM_LEFT:
      case Attach::BOTTOM_CENTER:
      case Attach::BOTTOM_RIGHT: {
        center_y = ty;
        break;
      }
      case Attach::TOP_LEFT:
      case Attach::TOP_CENTER:
      case Attach::TOP_RIGHT: {
        center_y = screen_height + ty;
        break;
      }
      case Attach::CENTER_LEFT:
      case Attach::CENTER_RIGHT:
      case Attach::CENTER: {
        center_y = screen_center_y + ty;
        break;
      }
    }

    switch (attach_) {
      case Attach::TOP_LEFT:
      case Attach::CENTER_LEFT:
      case Attach::BOTTOM_LEFT: {
        center_x = tx;
        break;
      }
      case Attach::TOP_CENTER:
      case Attach::CENTER:
      case Attach::BOTTOM_CENTER: {
        center_x = screen_center_x + tx;
        break;
      }
      case Attach::TOP_RIGHT:
      case Attach::CENTER_RIGHT:
      case Attach::BOTTOM_RIGHT: {
        center_x = screen_width + tx;
        break;
      }
    }
    if (fill_screen_) {
      width_ = screen_width;
      height_ = screen_height;
      center_x_ = width_ * 0.5f;
      center_y_ = height_ * 0.5f;
    } else {
      center_x_ = center_x;
      center_y_ = center_y;
      width_ = width;
      height_ = height;
    }
    dirty_ = false;
  }
  float fin_center_x = center_x_;
  float fin_center_y = center_y_;
  float fin_width = width_;
  float fin_height = height_;

  // Tilt-translate doesn't happen in vr mode.
  if (tilt_translate_ != 0.0f && !vr) {
    Vector3f tilt = g_base->graphics->tilt();
    fin_center_x -= tilt.y * tilt_translate_;
    fin_center_y += tilt.x * tilt_translate_;

    // If we're fullscreen and are tilting, crank our dimensions up
    // slightly to account for tiltage.
#if BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID
    if (fill_screen_) {
      float s = 1.0f - tilt_translate_ * 0.2f;
      fin_width *= s;
      fin_height *= s;
    }
#endif  // BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID
  }

  bool has_alpha_channel = has_alpha_channel_;
  float alpha = opacity_ * alpha_;
  if (alpha < 0) {
    alpha = 0;
  }
  base::MeshAsset* mesh_opaque_used = nullptr;
  if (mesh_opaque_.exists()) mesh_opaque_used = mesh_opaque_->mesh_data();
  base::MeshAsset* mesh_transparent_used = nullptr;
  if (mesh_transparent_.exists()) {
    mesh_transparent_used = mesh_transparent_->mesh_data();
  }

  // If no meshes were provided, use default image meshes.
  if (!mesh_opaque_.exists() && !mesh_transparent_.exists()) {
    if (vr && fill_screen_) {
#if BA_VR_BUILD
      mesh_opaque_used =
          g_base->assets->SysMesh(base::SysMeshID::kImage1x1VRFullScreen);
#else
      throw Exception();
#endif  // BA_VR_BUILD
    } else {
      base::SysMeshID m = fill_screen_ ? base::SysMeshID::kImage1x1FullScreen
                                       : base::SysMeshID::kImage1x1;
      if (has_alpha_channel) {
        mesh_transparent_used = g_base->assets->SysMesh(m);
      } else {
        mesh_opaque_used = g_base->assets->SysMesh(m);
      }
    }
  }

  // Draw opaque portion either opaque or transparent depending on our
  // global opacity.
  if (mesh_opaque_used) {
    // Draw in opaque pass if possible.
    base::SimpleComponent c(&pass);
    bool draw_transparent = (alpha < 0.999f);

    // Stuff in the fixed vr overlay pass may inadvertently
    // obscure the non-fixed overlay pass, so lets just always draw
    // transparent to avoid that.
    c.SetTransparent(draw_transparent);
    c.SetPremultiplied(premultiplied_);
    c.SetTexture(texture_.exists() ? texture_->texture_data() : nullptr);
    c.SetColor(red_, green_, blue_, alpha);
    if (tint_texture_.exists()) {
      c.SetColorizeTexture(tint_texture_->texture_data());
      c.SetColorizeColor(tint_red_, tint_green_, tint_blue_);
      c.SetColorizeColor2(tint2_red_, tint2_green_, tint2_blue_);
    }
    c.SetMaskTexture(mask_texture_.exists() ? mask_texture_->texture_data()
                                            : nullptr);
    {
      auto xf = c.ScopedTransform();
      c.Translate(fin_center_x, fin_center_y,
                  vr ? vr_depth_ : g_base->graphics->overlay_node_z_depth());
      if (rotate_ != 0.0f) {
        c.Rotate(rotate_, 0, 0, 1);
      }
      c.Scale(fin_width, fin_height, fin_width);
      c.DrawMeshAsset(mesh_opaque_used);
    }
    c.Submit();
  }
  // Transparent portion.
  if (mesh_transparent_used) {
    base::SimpleComponent c(&pass);
    c.SetTransparent(true);
    c.SetPremultiplied(premultiplied_);
    c.SetTexture(texture_.exists() ? texture_->texture_data() : nullptr);
    c.SetColor(red_, green_, blue_, alpha);
    if (tint_texture_.exists()) {
      c.SetColorizeTexture(tint_texture_->texture_data());
      c.SetColorizeColor(tint_red_, tint_green_, tint_blue_);
      c.SetColorizeColor2(tint2_red_, tint2_green_, tint2_blue_);
    }
    c.SetMaskTexture(mask_texture_.exists() ? mask_texture_->texture_data()
                                            : nullptr);
    {
      auto xf = c.ScopedTransform();
      c.Translate(fin_center_x, fin_center_y,
                  vr ? vr_depth_ : g_base->graphics->overlay_node_z_depth());
      if (rotate_ != 0.0f) {
        c.Rotate(rotate_, 0, 0, 1);
      }
      c.Scale(fin_width, fin_height, fin_width);
      c.DrawMeshAsset(mesh_transparent_used);
    }
    c.Submit();
  }
}

}  // namespace ballistica::scene_v1
