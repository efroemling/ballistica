// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/image_widget.h"

#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/logic/logic.h"

namespace ballistica::ui_v1 {

ImageWidget::ImageWidget()
    : birth_time_millisecs_{
        static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0)} {}

ImageWidget::~ImageWidget() = default;

auto ImageWidget::GetWidth() -> float { return width_; }
auto ImageWidget::GetHeight() -> float { return height_; }

void ImageWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  if (opacity_ < 0.001f) {
    return;
  }

  millisecs_t current_time = pass->frame_def()->display_time_millisecs();

  Vector3f tilt = tilt_scale_ * 0.01f * g_base->graphics->tilt();
  if (draw_control_parent()) tilt += 0.02f * g_base->graphics->tilt();
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  // Simple transition.
  float transition =
      (static_cast<float>(birth_time_millisecs_) + transition_delay_)
      - static_cast<float>(current_time);
  if (transition > 0) {
    extra_offs_x -= transition * 4.0f;
  }

  float l = 0;
  float r = l + width_;
  float b = 0;
  float t = b + height_;

  if (texture_.Exists()) {
    if (texture_->loaded()
        && ((!tint_texture_.Exists()) || tint_texture_->loaded())
        && ((!mask_texture_.Exists()) || mask_texture_->loaded())) {
      if (image_dirty_) {
        image_width_ = r - l;
        image_height_ = t - b;
        image_center_x_ = l + image_width_ * 0.5f;
        image_center_y_ = b + image_height_ * 0.5f;
        image_dirty_ = false;
      }

      Object::Ref<base::MeshAsset> mesh_opaque_used;
      if (mesh_opaque_.Exists()) {
        mesh_opaque_used = mesh_opaque_;
      }
      Object::Ref<base::MeshAsset> mesh_transparent_used;
      if (mesh_transparent_.Exists()) {
        mesh_transparent_used = mesh_transparent_;
      }

      bool draw_radial_opaque = false;
      bool draw_radial_transparent = false;

      // If no meshes were provided, use default image meshes.
      if ((!mesh_opaque_.Exists()) && (!mesh_transparent_.Exists())) {
        if (has_alpha_channel_) {
          if (radial_amount_ < 1.0f) {
            draw_radial_transparent = true;
          } else {
            mesh_transparent_used =
                g_base->assets->SysMesh(base::SysMeshID::kImage1x1);
          }
        } else {
          if (radial_amount_ < 1.0f) {
            draw_radial_opaque = true;
          } else {
            mesh_opaque_used =
                g_base->assets->SysMesh(base::SysMeshID::kImage1x1);
          }
        }
      }

      // Draw brightness.
      float db = 1.0f;
      if (Widget* draw_controller = draw_control_parent()) {
        db *= draw_controller->GetDrawBrightness(current_time);
      }

      // Opaque portion may get drawn transparent or opaque depending on our
      // global opacity.
      if (mesh_opaque_used.Exists() || draw_radial_opaque) {
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
          c.SetColor(color_red_ * db, color_green_ * db, color_blue_ * db,
                     opacity_);
          c.SetTexture(texture_);
          if (tint_texture_.Exists()) {
            c.SetColorizeTexture(tint_texture_.Get());
            c.SetColorizeColor(tint_color_red_, tint_color_green_,
                               tint_color_blue_);
            c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                                tint2_color_blue_);
          }
          c.SetMaskTexture(mask_texture_.Get());
          {
            auto xf = c.ScopedTransform();
            c.Translate(image_center_x_ + extra_offs_x,
                        image_center_y_ + extra_offs_y);
            c.Scale(image_width_, image_height_, 1.0f);
            if (draw_radial_opaque) {
              if (!radial_mesh_.Exists()) {
                radial_mesh_ =
                    Object::NewDeferred<base::MeshIndexedSimpleFull>();
              }
              base::Graphics::DrawRadialMeter(&(*radial_mesh_), radial_amount_);
              c.Scale(0.5f, 0.5f, 1.0f);
              c.DrawMesh(radial_mesh_.Get());
            } else {
              c.DrawMeshAsset(mesh_opaque_used.Get());
            }
          }
          c.Submit();
        }
      }

      // Always-transparent portion.
      if ((mesh_transparent_used.Exists() || draw_radial_transparent)
          && draw_transparent) {
        base::SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetColor(color_red_ * db, color_green_ * db, color_blue_ * db,
                   opacity_);
        c.SetTexture(texture_);
        if (tint_texture_.Exists()) {
          c.SetColorizeTexture(tint_texture_.Get());
          c.SetColorizeColor(tint_color_red_, tint_color_green_,
                             tint_color_blue_);
          c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                              tint2_color_blue_);
        }
        c.SetMaskTexture(mask_texture_.Get());
        {
          auto xf = c.ScopedTransform();
          c.Translate(image_center_x_ + extra_offs_x,
                      image_center_y_ + extra_offs_y);
          c.Scale(image_width_, image_height_, 1.0f);
          if (draw_radial_transparent) {
            if (!radial_mesh_.Exists()) {
              radial_mesh_ = Object::New<base::MeshIndexedSimpleFull>();
            }
            base::Graphics::DrawRadialMeter(&(*radial_mesh_), radial_amount_);
            c.Scale(0.5f, 0.5f, 1.0f);
            c.DrawMesh(radial_mesh_.Get());
          } else {
            c.DrawMeshAsset(mesh_transparent_used.Get());
          }
        }
        c.Submit();
      }
    }
  }
}

auto ImageWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  return false;
}

}  // namespace ballistica::ui_v1
