// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/image_widget.h"

#include <algorithm>
#include <memory>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/ui_v1/widget/container_widget.h"
#include "ballistica/ui_v1/widget/depiction_slot.h"

namespace ballistica::ui_v1 {

ImageWidget::ImageWidget()
    : birth_time_millisecs_{
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)} {}

ImageWidget::~ImageWidget() = default;

auto ImageWidget::GetWidth() -> float { return width_; }
auto ImageWidget::GetHeight() -> float { return height_; }

auto ImageWidget::GetDepictionSlot() -> DepictionSlot& {
  if (!depiction_slot_) {
    depiction_slot_ = std::make_unique<DepictionSlot>();
  }
  return *depiction_slot_;
}

auto ImageWidget::DrawBrightness_(millisecs_t current_time) const -> float {
  float db = 1.0f;
  if (Widget* draw_controller = draw_control_parent()) {
    db *= (draw_controller_mult_
           * draw_controller->GetDrawBrightness(current_time))
          + (1.0f - draw_controller_mult_) * 1.0f;
  }
  // Direct parent only (cheap); callers parent us to the window.
  if (match_backing_glow_) {
    if (ContainerWidget* parent = parent_widget()) {
      db *= parent->GetBackingGlowMult();
    }
  }
  return db;
}

void ImageWidget::DrawDepiction_(base::RenderPass* pass, bool transparent,
                                 float offs_x, float offs_y,
                                 float transition_scale,
                                 millisecs_t current_time) {
  assert(depiction_slot_);
  DepictionSlot::DrawArgs args;
  args.owner = this;
  args.pass = pass;
  args.transparent = transparent;
  args.width = width_;
  args.height = height_;
  args.offset_x = offs_x;
  args.offset_y = offs_y;
  args.scale = transition_scale;
  args.brightness = DrawBrightness_(current_time);
  args.opacity = opacity_;
  if (Widget* draw_controller = draw_control_parent()) {
    args.disabled = draw_controller->IsDrawDisabled();
  }
  args.mask_texture = mask_texture_.get();
  depiction_slot_->Draw(args);
}

void ImageWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  if (opacity_ < 0.001f) {
    return;
  }

  millisecs_t current_time = pass->frame_def()->display_time_millisecs();

  Vector3f tilt = tilt_scale_ * 0.01f * g_base->input->tilt();
  if (draw_control_parent()) tilt += 0.02f * g_base->input->tilt();
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  // Simple transition.
  float transition =
      (static_cast<float>(birth_time_millisecs_) + transition_delay_)
      - static_cast<float>(current_time);
  float transition_scale = 1.0f;
  if (transition > 0) {
    if (transition_type_ == TransitionType::kScale) {
      // Fixed 150ms scale-up at the tail of the transition window
      // (quadratic ease-out; decelerates as it settles at 1.0).
      constexpr float kScaleDurationMs = 150.0f;
      float t = std::max(0.0f, 1.0f - transition / kScaleDurationMs);
      transition_scale = 1.0f - (1.0f - t) * (1.0f - t);
    } else {
      extra_offs_x -= transition * 4.0f;
    }
  }

  // A depiction stands in for our texture.
  if (depiction_slot_ && depiction_slot_->active()) {
    DrawDepiction_(pass, draw_transparent, extra_offs_x, extra_offs_y,
                   transition_scale, current_time);
    return;
  }

  float l = 0;
  float r = l + width_;
  float b = 0;
  float t = b + height_;

  if (texture_.exists()) {
    if (texture_->loaded()
        && ((!tint_texture_.exists()) || tint_texture_->loaded())
        && ((!mask_texture_.exists()) || mask_texture_->loaded())) {
      if (image_dirty_) {
        image_width_ = r - l;
        image_height_ = t - b;
        image_center_x_ = l + image_width_ * 0.5f;
        image_center_y_ = b + image_height_ * 0.5f;
        image_dirty_ = false;
      }

      Object::Ref<base::MeshAsset> mesh_opaque_used;
      if (mesh_opaque_.exists()) {
        mesh_opaque_used = mesh_opaque_;
      }
      Object::Ref<base::MeshAsset> mesh_transparent_used;
      if (mesh_transparent_.exists()) {
        mesh_transparent_used = mesh_transparent_;
      }

      bool draw_radial_opaque = false;
      bool draw_radial_transparent = false;

      // If no meshes were provided, use default image meshes.
      if ((!mesh_opaque_.exists()) && (!mesh_transparent_.exists())) {
        if (has_alpha_channel_) {
          if (radial_amount_ < 1.0f) {
            draw_radial_transparent = true;
          } else {
            mesh_transparent_used = g_ui_v1->assets().image1x1.get();
          }
        } else {
          if (radial_amount_ < 1.0f) {
            draw_radial_opaque = true;
          } else {
            mesh_opaque_used = g_ui_v1->assets().image1x1.get();
          }
        }
      }

      float db = DrawBrightness_(current_time);

      // Premultiply rgb by opacity for premultiplied textures so faded icons
      // composite 'over' under premult blend instead of staying full-brightness
      // (premult blend adds rgb directly rather than weighting it by alpha).
      // Straight-alpha textures keep raw rgb and fade via alpha as before.
      float omul =
          (texture_.exists() && texture_->premultiplied()) ? opacity_ : 1.0f;

      // Opaque portion may get drawn transparent or opaque depending on our
      // global opacity.
      if (mesh_opaque_used.exists() || draw_radial_opaque) {
        bool should_draw = false;
        bool should_draw_transparent = false;

        // Draw our opaque mesh in the opaque pass.
        if (!draw_transparent && opacity_ > 0.999f) {
          should_draw = true;
          should_draw_transparent = false;
        } else if (draw_transparent && opacity_ <= 0.999f) {
          // Draw our opaque mesh in the transparent pass.
          should_draw = true;
          should_draw_transparent = true;
        }

        if (should_draw) {
          base::SimpleComponent c(pass);
          c.SetTransparent(should_draw_transparent);
          c.SetColor(color_red_ * db * omul, color_green_ * db * omul,
                     color_blue_ * db * omul, opacity_);
          c.SetTexture(texture_);
          if (flatness_ != 0.0f) {
            c.SetFlatness(flatness_);
          }
          if (tint_texture_.exists()) {
            c.SetColorizeTexture(tint_texture_.get());
            c.SetColorizeColor(tint_color_red_, tint_color_green_,
                               tint_color_blue_);
            c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                                tint2_color_blue_);
          }
          if (rotate_ != 0.0f) {
            c.Rotate(rotate_, 0, 0, 1);
          }
          c.SetMaskTexture(mask_texture_.get());
          {
            auto xf = c.ScopedTransform();
            c.Translate(image_center_x_ + extra_offs_x,
                        image_center_y_ + extra_offs_y);
            c.Scale(image_width_ * transition_scale,
                    image_height_ * transition_scale, 1.0f);
            if (draw_radial_opaque) {
              if (!radial_mesh_.exists()) {
                radial_mesh_ =
                    Object::NewDeferred<base::MeshIndexedSimpleFull>();
              }
              base::Graphics::DrawRadialMeter(&(*radial_mesh_), radial_amount_);
              c.Scale(0.5f, 0.5f, 1.0f);
              c.DrawMesh(radial_mesh_.get());
            } else {
              c.DrawMeshAsset(mesh_opaque_used.get());
            }
          }
          c.Submit();
        }
      }

      // Always-transparent portion.
      if ((mesh_transparent_used.exists() || draw_radial_transparent)
          && draw_transparent) {
        base::SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetColor(color_red_ * db * omul, color_green_ * db * omul,
                   color_blue_ * db * omul, opacity_);
        c.SetTexture(texture_);
        if (flatness_ != 0.0f) {
          c.SetFlatness(flatness_);
        }
        if (rotate_ != 0.0f) {
          c.Rotate(rotate_, 0, 0, 1);
        }
        if (tint_texture_.exists()) {
          c.SetColorizeTexture(tint_texture_.get());
          c.SetColorizeColor(tint_color_red_, tint_color_green_,
                             tint_color_blue_);
          c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                              tint2_color_blue_);
        }
        c.SetMaskTexture(mask_texture_.get());
        {
          auto xf = c.ScopedTransform();
          c.Translate(image_center_x_ + extra_offs_x,
                      image_center_y_ + extra_offs_y);
          c.Scale(image_width_ * transition_scale,
                  image_height_ * transition_scale, 1.0f);
          if (draw_radial_transparent) {
            if (!radial_mesh_.exists()) {
              radial_mesh_ = Object::New<base::MeshIndexedSimpleFull>();
            }
            base::Graphics::DrawRadialMeter(&(*radial_mesh_), radial_amount_);
            c.Scale(0.5f, 0.5f, 1.0f);
            c.DrawMesh(radial_mesh_.get());
          } else {
            c.DrawMeshAsset(mesh_transparent_used.get());
          }
        }
        c.Submit();
      }
    }
  }
}

auto ImageWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  // Only a depiction ever takes input (and only if allowed to).
  if (depiction_slot_) {
    return depiction_slot_->HandleMessage(m, width_, height_);
  }
  return false;
}

}  // namespace ballistica::ui_v1
