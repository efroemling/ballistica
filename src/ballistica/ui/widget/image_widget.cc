// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui/widget/image_widget.h"

#include "ballistica/game/game.h"
#include "ballistica/graphics/component/simple_component.h"

namespace ballistica {

ImageWidget::ImageWidget() : birth_time_{g_game->master_time()} {}

ImageWidget::~ImageWidget() = default;

auto ImageWidget::GetWidth() -> float { return width_; }
auto ImageWidget::GetHeight() -> float { return height_; }

void ImageWidget::Draw(RenderPass* pass, bool draw_transparent) {
  if (opacity_ < 0.001f) {
    return;
  }

  millisecs_t current_time = pass->frame_def()->base_time();

  Vector3f tilt = tilt_scale_ * 0.01f * g_graphics->tilt();
  if (draw_control_parent()) tilt += 0.02f * g_graphics->tilt();
  float extra_offs_x = -tilt.y;
  float extra_offs_y = tilt.x;

  // Simple transition.
  float transition = (birth_time_ + transition_delay_) - current_time;
  if (transition > 0) {
    extra_offs_x -= transition * 4.0f;
  }

  float l = 0;
  float r = l + width_;
  float b = 0;
  float t = b + height_;

  if (texture_.exists()) {
    if (texture_->texture_data()->loaded()
        && ((!tint_texture_.exists())
            || tint_texture_->texture_data()->loaded())
        && ((!mask_texture_.exists())
            || mask_texture_->texture_data()->loaded())) {
      if (image_dirty_) {
        image_width_ = r - l;
        image_height_ = t - b;
        image_center_x_ = l + image_width_ * 0.5f;
        image_center_y_ = b + image_height_ * 0.5f;
        image_dirty_ = false;
      }

      Object::Ref<ModelData> model_opaque_used;
      if (model_opaque_.exists()) {
        model_opaque_used = model_opaque_->model_data();
      }
      Object::Ref<ModelData> model_transparent_used;
      if (model_transparent_.exists()) {
        model_transparent_used = model_transparent_->model_data();
      }

      bool draw_radial_opaque = false;
      bool draw_radial_transparent = false;

      // if no meshes were provided, use default image models
      if ((!model_opaque_.exists()) && (!model_transparent_.exists())) {
        if (has_alpha_channel_) {
          if (radial_amount_ < 1.0f) {
            draw_radial_transparent = true;
          } else {
            model_transparent_used =
                g_assets->GetModel(SystemModelID::kImage1x1);
          }
        } else {
          if (radial_amount_ < 1.0f) {
            draw_radial_opaque = true;
          } else {
            model_opaque_used = g_assets->GetModel(SystemModelID::kImage1x1);
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
      if (model_opaque_used.exists() || draw_radial_opaque) {
        bool should_draw = false;
        bool should_draw_transparent = false;

        // Draw our opaque model in the opaque pass.
        if (!draw_transparent && opacity_ > 0.999f) {
          should_draw = true;
          should_draw_transparent = false;
        } else if (draw_transparent && opacity_ <= 0.999f) {
          // Draw our opaque model in the transparent pass.
          should_draw = true;
          should_draw_transparent = true;
        }

        if (should_draw) {
          SimpleComponent c(pass);
          c.SetTransparent(should_draw_transparent);
          c.SetColor(color_red_ * db, color_green_ * db, color_blue_ * db,
                     opacity_);
          c.SetTexture(texture_);
          if (tint_texture_.exists()) {
            c.SetColorizeTexture(tint_texture_);
            c.SetColorizeColor(tint_color_red_, tint_color_green_,
                               tint_color_blue_);
            c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                                tint2_color_blue_);
          }
          c.SetMaskTexture(mask_texture_);
          c.PushTransform();
          c.Translate(image_center_x_ + extra_offs_x,
                      image_center_y_ + extra_offs_y);
          c.Scale(image_width_, image_height_, 1.0f);
          if (draw_radial_opaque) {
            if (!radial_mesh_.exists()) {
              radial_mesh_ = Object::NewDeferred<MeshIndexedSimpleFull>();
            }
            Graphics::DrawRadialMeter(&(*radial_mesh_), radial_amount_);
            c.Scale(0.5f, 0.5f, 1.0f);
            c.DrawMesh(radial_mesh_.get());
          } else {
            c.DrawModel(model_opaque_used.get());
          }
          c.PopTransform();
          c.Submit();
        }
      }

      // Always-transparent portion.
      if ((model_transparent_used.exists() || draw_radial_transparent)
          && draw_transparent) {
        SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetColor(color_red_ * db, color_green_ * db, color_blue_ * db,
                   opacity_);
        c.SetTexture(texture_);
        if (tint_texture_.exists()) {
          c.SetColorizeTexture(tint_texture_);
          c.SetColorizeColor(tint_color_red_, tint_color_green_,
                             tint_color_blue_);
          c.SetColorizeColor2(tint2_color_red_, tint2_color_green_,
                              tint2_color_blue_);
        }
        c.SetMaskTexture(mask_texture_);
        c.PushTransform();
        c.Translate(image_center_x_ + extra_offs_x,
                    image_center_y_ + extra_offs_y);
        c.Scale(image_width_, image_height_, 1.0f);
        if (draw_radial_transparent) {
          if (!radial_mesh_.exists()) {
            radial_mesh_ = Object::New<MeshIndexedSimpleFull>();
          }
          Graphics::DrawRadialMeter(&(*radial_mesh_), radial_amount_);
          c.Scale(0.5f, 0.5f, 1.0f);
          c.DrawMesh(radial_mesh_.get());
        } else {
          c.DrawModel(model_transparent_used.get());
        }
        c.PopTransform();
        c.Submit();
      }
    }
  }
}

auto ImageWidget::HandleMessage(const WidgetMessage& m) -> bool {
  return false;
}

}  // namespace ballistica
