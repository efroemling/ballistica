// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/renderer/render_pass.h"

#include <memory>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/core/core.h"

// Turn this off to not draw any transparent stuff.
#define DRAW_TRANSPARENT 1

namespace ballistica::base {

const float kCamNearClip = 4.0f;
const float kCamFarClip = 1000.0f;

RenderPass::RenderPass(RenderPass::Type type_in, FrameDef* frame_def_in)
    : type_(type_in), frame_def_(frame_def_in) {
  // Create/init our command buffers.
  if (UsesWorldLists()) {
    for (auto& command : commands_) {
      command = std::make_unique<RenderCommandBuffer>();

      // FIXME: Could just pass in constructor?
      command->set_frame_def(frame_def_);
    }
  } else {
    commands_flat_transparent_ = std::make_unique<RenderCommandBuffer>();
    commands_flat_transparent_->set_frame_def(frame_def_);
    commands_flat_ = std::make_unique<RenderCommandBuffer>();

    // FIXME: Could just pass in constructor?
    commands_flat_->set_frame_def(frame_def_);
  }
}

RenderPass::~RenderPass() = default;

void RenderPass::Render(RenderTarget* render_target, bool transparent) {
  assert(g_base->app_adapter->InGraphicsContext());

  if (explicit_bool(!DRAW_TRANSPARENT) && transparent) {
    return;
  }
#undef DRAW_TRANSPRENT

  Renderer* renderer = g_base->graphics_server->renderer();

  // Set up camera & depth.
  switch (type()) {
    case Type::kBeautyPass: {
      g_base->graphics_server->SetCamera(cam_pos_, cam_target_, cam_up_);
      // If this changes, make sure to change it before _drawCameraBuffer()
      // too.

      // FIXME:
      //  If we're drawing our cam into its own buffer we could technically
      //  use its full depth range ...otherwise we need to share with the
      //  other onscreen elements (but maybe its good to use the limited
      //  range regardless to make sure we can get by that way).
      renderer->SetDepthRange(kBackingDepth3, kBackingDepth4);
      SetFrustum(cam_near_clip_, cam_far_clip_);

      tex_project_matrix_ =
          g_base->graphics_server->GetModelViewProjectionMatrix();
      model_view_matrix_ = g_base->graphics_server->model_view_matrix();
      model_view_projection_matrix_ =
          g_base->graphics_server->GetModelViewProjectionMatrix();

      // Store our matrix to get things in screen space.
      tex_project_matrix_ *= Matrix44fScale(0.5f);
      tex_project_matrix_ *= Matrix44fTranslate(0.5f, 0.5f, 0);
      break;
    }
    case Type::kOverlay3DPass: {
      g_base->graphics_server->SetCamera(cam_pos_, cam_target_, cam_up_);

      // If we drew the world directly to the screen we need to use a depth
      // range that lies fully in front of that range so we don't get obscured
      // by any of the world.

      // However if we drew the world to an offscreen buffer this isn't a
      // problem; nothing exists in that range.  In that case lets draw to the
      // same range so we can do easy depth comparisons to the offscreen world's
      // depth (for overlay fog, blurs, etc)

      // Use same region as world.
      if (renderer->has_camera_render_target()) {
        // Use beauty-pass depth region
        renderer->SetDepthRange(kBackingDepth3, kBackingDepth4);
      } else {
        // Use region in front of world
        renderer->SetDepthRange(kBackingDepth2, kBackingDepth3);
      }
      SetFrustum(cam_near_clip_, cam_far_clip_);
      break;
    }
    case Type::kVRCoverPass: {
      g_base->graphics_server->SetCamera(cam_pos_, cam_target_, cam_up_);

      // We use the front depth range where the overlays would
      // live in the non-vr path.
      renderer->SetDepthRange(kBackingDepth1, kBackingDepth2);
      SetFrustum(cam_near_clip_, cam_far_clip_);
      break;
    }
    case Type::kBlitPass: {
      g_base->graphics_server->SetCamera(cam_pos_, cam_target_, cam_up_);

      // We render into a little sliver of the depth buffer in the
      // back just in front of the backing blit.
      assert(renderer->has_camera_render_target());
      renderer->SetDepthRange(kBackingDepth4, kBackingDepth5);
      SetFrustum(cam_near_clip_, cam_far_clip_);
      break;
    }
    case Type::kBeautyPassBG: {
      g_base->graphics_server->SetCamera(cam_pos_, cam_target_, cam_up_);
      renderer->SetDepthRange(kBackingDepth3, kBackingDepth4);
      SetFrustum(cam_near_clip_, cam_far_clip_);
      break;
    }
    case Type::kOverlayPass:
    case Type::kOverlayFrontPass:
    case Type::kOverlayFixedPass:
    case Type::kOverlayFlatPass: {
      // In vr mode we draw the flat-overlay into its own buffer so can use
      // the full depth range (shouldn't matter but why not?...) shouldn't.
      if (g_core->vr_mode()) {
        // In vr mode, our overlay-flat pass is ortho-projected
        // while our regular overlay is just rendered in world space using
        // the vr-overlay matrix.
        if (type() == Type::kOverlayFlatPass) {
          g_base->graphics_server->ModelViewReset();
          renderer->SetDepthRange(0, 1);  // we can use full depth range!!
          float amt = 0.5f * kVRBorder;
          float w = virtual_width();
          float h = virtual_height();
          g_base->graphics_server->SetOrthoProjection(
              -amt * w, (1.0f + amt) * w, -amt * h, (1.0f + amt) * h, -1, 1);
        } else {
          g_base->graphics_server->SetCamera(cam_pos_, cam_target_, cam_up_);
          // We set the same depth ranges as the overlay-3d pass since we're
          // essentially doing the same thing. See explanation in the
          // overlay-3d case above. The one difference is that we split the
          // range between our fixed overlay and our regular overlay passes
          // (we want fixed-overlay stuff on bottom).
          if (renderer->has_camera_render_target()) {
            if (type() == Type::kOverlayFrontPass) {
              renderer->SetDepthRange(kBackingDepth3, kBackingDepth3B);
            } else if (type() == Type::kOverlayPass) {
              renderer->SetDepthRange(kBackingDepth3B, kBackingDepth3C);
            } else {
              renderer->SetDepthRange(kBackingDepth3C, kBackingDepth4);
            }
          } else {
            if (type() == Type::kOverlayFrontPass) {
              renderer->SetDepthRange(kBackingDepth2, kBackingDepth2B);
            } else if (type() == Type::kOverlayPass) {
              renderer->SetDepthRange(kBackingDepth2B, kBackingDepth2C);
            } else {
              renderer->SetDepthRange(kBackingDepth2C, kBackingDepth3);
            }
          }
          SetFrustum(cam_near_clip_, cam_far_clip_);

          // Now move to wherever our 2d plane in space is to start with.
          if (type() == Type::kOverlayPass
              || type() == Type::kOverlayFrontPass) {
            g_base->graphics_server->MultMatrix(
                frame_def()->vr_overlay_screen_matrix());
          } else {
            assert(type() == Type::kOverlayFixedPass);
            g_base->graphics_server->MultMatrix(
                frame_def()->vr_overlay_screen_matrix_fixed());
          }
        }
      } else {
        // In non-vr mode both our overlays are just ortho projected.
        g_base->graphics_server->ModelViewReset();
        if (type() == Type::kOverlayFrontPass) {
          renderer->SetDepthRange(kBackingDepth1, kBackingDepth1B);
        } else {
          renderer->SetDepthRange(kBackingDepth1B, kBackingDepth2);
        }
        if (g_base->graphics_server->tv_border()) {
          float amt = 0.5f * kTVBorder;
          float w = virtual_width();
          float h = virtual_height();
          g_base->graphics_server->SetOrthoProjection(
              -amt * w, (1.0f + amt) * w, -amt * h, (1.0f + amt) * h, -1, 1);
        } else {
          g_base->graphics_server->SetOrthoProjection(0, virtual_width(), 0,
                                                      virtual_height(), -1, 1);
        }
      }
      break;
    }
    case Type::kLightPass:
    case Type::kLightShadowPass: {
      // Ortho shadows.
      if (renderer->shadow_ortho()) {
        g_base->graphics_server->ModelViewReset();
        g_base->graphics_server->SetOrthoProjection(-12, 12, -12, 12, 10, 100);
        g_base->graphics_server->Translate(
            Vector3f(0, 0, renderer->light_tz()));
        g_base->graphics_server->Rotate(80, Vector3f(1.0f, 0, 0));
        const Vector3f& soffs = renderer->shadow_offset();
        g_base->graphics_server->Translate(
            Vector3f(-soffs.x, -soffs.y, -soffs.z));
        g_base->graphics_server->scale(
            Vector3f(1.0f / renderer->shadow_scale_x(), 1.0f,
                     1.0f / renderer->shadow_scale_z()));
      } else {
        float fovy = 45.0f * kPi / 180.0f;
        float fovx = fovy;
        float near_val = 10;
        float far_val = 100;
        float x = near_val * tanf(fovx);
        float y = near_val * tanf(fovy);

        g_base->graphics_server->SetProjectionMatrix(
            Matrix44fFrustum(-x, x, -y, y, near_val, far_val));
        g_base->graphics_server->ModelViewReset();
        g_base->graphics_server->Translate(
            Vector3f(0.0f, 0.0f, renderer->light_tz()));
        g_base->graphics_server->Rotate(renderer->light_pitch(),
                                        Vector3f(1.0f, 0.0f, 0.0f));
        g_base->graphics_server->Rotate(renderer->light_heading(),
                                        Vector3f(0.0f, 1.0f, 0.0f));
        const Vector3f& soffs = renderer->shadow_offset();

        // Well, this is slightly terrifying; '-soffs' is causing crashes
        // here but multing by -1.000001f works (generally just on Android
        // 4.3 on atom processors).
        g_base->graphics_server->Translate(Vector3f(
            -1.000001f * soffs.x, -1.000001f * soffs.y, -1.000001f * soffs.z));
      }

      // ...now store the matrix we'll use to project this as a texture
      // FIXME: most of these calculations could be cached instead of
      // redoing them every pass
      tex_project_matrix_ =
          g_base->graphics_server->GetModelViewProjectionMatrix();
      model_view_matrix_ = g_base->graphics_server->model_view_matrix();
      model_view_projection_matrix_ =
          g_base->graphics_server->GetModelViewProjectionMatrix();
      tex_project_matrix_ *= Matrix44fScale(0.5f);
      tex_project_matrix_ *= Matrix44fTranslate(0.5f, 0.5f, 0);
      g_base->graphics_server->SetLightShadowProjectionMatrix(
          tex_project_matrix_);

      break;
    }
    default:
      throw Exception();
  }

  // Some passes draw stuff into the world bucketed by type.
  if (UsesWorldLists()) {
    // For opaque stuff, render non-reflected(above-ground),
    // then reflected(below-ground) stuff (less overdraw that way)
    // for transparent stuff we do the opposite so we get better layering.
    ReflectionSubPass reflection_sub_passes[2];
    if (transparent) {
      reflection_sub_passes[0] = ReflectionSubPass::kMirrored;
      reflection_sub_passes[1] = ReflectionSubPass::kRegular;
    } else {
      reflection_sub_passes[0] = ReflectionSubPass::kRegular;
      reflection_sub_passes[1] = ReflectionSubPass::kMirrored;
    }

    for (auto reflection_sub_pass : reflection_sub_passes) {
      bool doing_reflection = false;
      if (reflection_sub_pass == ReflectionSubPass::kMirrored) {
        // Only actually draw reflection pass if quality >= high
        // and floor-reflections are on.
        if (floor_reflection()
            && frame_def()->quality() >= GraphicsQuality::kHigher) {
          doing_reflection = true;
          renderer->set_drawing_reflection(true);
          g_base->graphics_server->PushTransform();
          Matrix44f m = Matrix44fScale(Vector3f(1, -1, 1));
          g_base->graphics_server->MultMatrix(m);
          renderer->FlipCullFace();  // Flip into reflection drawing.
        } else {
          continue;
        }
      } else {
        renderer->set_drawing_reflection(false);
      }

      // Render everything with the same material together to
      // minimize gl state changes.

      // Organize shaders that are likely to be occluding other stuff first.
      ShadingType component_types_opaque[] = {
          ShadingType::kSimpleColor,
          ShadingType::kSimpleTexture,
          ShadingType::kSimpleTextureModulated,
          ShadingType::kSimpleTextureModulatedColorized,
          ShadingType::kSimpleTextureModulatedColorized2,
          ShadingType::kSimpleTextureModulatedColorized2Masked,
          ShadingType::kObjectReflectLightShadow,
          ShadingType::kObjectLightShadow,
          ShadingType::kObjectReflect,
          ShadingType::kObject,
          ShadingType::kObjectReflectLightShadowDoubleSided,
          ShadingType::kObjectReflectLightShadowColorized,
          ShadingType::kObjectReflectLightShadowColorized2,
          ShadingType::kObjectReflectLightShadowAdd,
          ShadingType::kObjectReflectLightShadowAddColorized,
          ShadingType::kObjectReflectLightShadowAddColorized2};

      ShadingType component_types_transparent[] = {
          ShadingType::kSimpleColorTransparent,
          ShadingType::kSimpleColorTransparentDoubleSided,
          ShadingType::kObjectTransparent,
          ShadingType::kObjectLightShadowTransparent,
          ShadingType::kObjectReflectTransparent,
          ShadingType::kObjectReflectAddTransparent,
          ShadingType::kSimpleTextureModulatedTransparent,
          ShadingType::kSimpleTextureModulatedTransFlatness,
          ShadingType::kSimpleTextureModulatedTransparentDoubleSided,
          ShadingType::kSimpleTextureModulatedTransparentColorized,
          ShadingType::kSimpleTextureModulatedTransparentColorized2,
          ShadingType::kSimpleTextureModulatedTransparentColorized2Masked,
          ShadingType::kSimpleTextureModulatedTransparentShadow,
          ShadingType::kSimpleTexModulatedTransShadowFlatness,
          ShadingType::kSimpleTextureModulatedTransparentGlow,
          ShadingType::kSimpleTextureModulatedTransparentGlowMaskUV2,
          ShadingType::kSmoke,
          ShadingType::kSprite};

      ShadingType* component_types;
      int component_type_count;
      if (transparent) {
        component_types = component_types_transparent;
        component_type_count =
            (sizeof(component_types_transparent) / sizeof(ShadingType));
      } else {
        component_types = component_types_opaque;
        component_type_count =
            (sizeof(component_types_opaque) / sizeof(ShadingType));
      }

      for (int c = 0; c < component_type_count; c++) {
        renderer->ProcessRenderCommandBuffer(
            commands_[static_cast<int>(component_types[c])].get(), *this,
            render_target);
      }

      if (doing_reflection) {
        renderer->FlipCullFace();  // Flip out of reflection drawing.
        g_base->graphics_server->PopTransform();
      }
    }
    renderer->set_drawing_reflection(false);
  } else {
    // ..and some passes draw flat lists in order added.
    if (transparent) {
      renderer->ProcessRenderCommandBuffer(commands_flat_transparent_.get(),
                                           *this, render_target);
    } else {
      renderer->ProcessRenderCommandBuffer(commands_flat_.get(), *this,
                                           render_target);
    }
  }
}

void RenderPass::SetCamera(
    const Vector3f& pos, const Vector3f& target, const Vector3f& up,
    float near_clip_in, float far_clip_in, float fov_x_in, float fov_y_in,
    bool use_fov_tangents, float fov_tan_l, float fov_tan_r, float fov_tan_b,
    float fov_tan_t, const std::vector<Vector3f>& area_of_interest_points) {
  cam_pos_ = pos;
  cam_target_ = target;
  cam_up_ = up;
  cam_near_clip_ = near_clip_in;
  cam_far_clip_ = far_clip_in;
  cam_use_fov_tangents_ = use_fov_tangents;
  cam_fov_x_ = fov_x_in;
  cam_fov_y_ = fov_y_in;
  cam_fov_l_tan_ = fov_tan_l;
  cam_fov_r_tan_ = fov_tan_r;
  cam_fov_b_tan_ = fov_tan_b;
  cam_fov_t_tan_ = fov_tan_t;
  cam_area_of_interest_points_ = area_of_interest_points;
}

void RenderPass::Reset() {
  virtual_width_ = 0;
  virtual_height_ = 0;
  physical_width_ = 0;
  physical_height_ = 0;
  floor_reflection_ = false;
  cam_pos_ = {0.0f, 0.0f, 0.0f};
  cam_target_ = {0.0f, 0.0f, 1.0f};
  cam_up_ = {0.0f, 1.0f, 0.0f};
  cam_near_clip_ = kCamNearClip;
  cam_far_clip_ = kCamFarClip;
  cam_fov_x_ = -1.0f;
  cam_fov_y_ = 40.0f;
  tex_project_matrix_ = kMatrix44fIdentity;

  Renderer* renderer = g_base->graphics_server->renderer();

  // Figure our our width/height for drawing commands to reference
  // (we cant wait until the drawing is actually occurring because
  // that happens in another thread later)
  switch (type()) {
    case Type::kBeautyPass:
    case Type::kBeautyPassBG:
    case Type::kOverlay3DPass:
    case Type::kOverlayPass:
    case Type::kOverlayFrontPass:
    case Type::kOverlayFlatPass:
    case Type::kVRCoverPass:
    case Type::kOverlayFixedPass:
    case Type::kBlitPass:
      physical_width_ = g_base->graphics->screen_pixel_width();
      physical_height_ = g_base->graphics->screen_pixel_height();
      break;
    case Type::kLightPass:
      physical_width_ = physical_height_ =
          static_cast<float>(renderer->shadow_res()) / kLightResDiv;
      break;
    case Type::kLightShadowPass:
      physical_width_ = physical_height_ =
          static_cast<float>(renderer->shadow_res());
      break;
    default:
      throw Exception();
  }

  // By default, logical width matches physical width, but for overlay
  // passes it can be independent.
  switch (type()) {
    case Type::kOverlayPass:
    case Type::kOverlayFrontPass:
    case Type::kOverlayFixedPass:
    case Type::kOverlayFlatPass:
      virtual_width_ = g_base->graphics->screen_virtual_width();
      virtual_height_ = g_base->graphics->screen_virtual_height();
      break;
    default:
      virtual_width_ = physical_width_;
      virtual_height_ = physical_height_;
      break;
  }

  // Clear the command buffers this pass cares about.
  if (UsesWorldLists()) {
    for (auto& command : commands_) {
      command->Reset();
    }
  } else {
    commands_flat_->Reset();
    commands_flat_transparent_->Reset();
  }
}

void RenderPass::SetFrustum(float near_val, float far_val) {
  assert(g_base->app_adapter->InGraphicsContext());
  // If we're using fov-tangents:
  if (cam_use_fov_tangents_) {
    float l = near_val * cam_fov_l_tan_;
    float r = near_val * cam_fov_r_tan_;
    float t = near_val * cam_fov_t_tan_;
    float b = near_val * cam_fov_b_tan_;
    projection_matrix_ = Matrix44fFrustum(-l, r, -b, t, near_val, far_val);
  } else {
    // Old angle-based stuff:
    float x;
    float angle_y = (cam_fov_y_ / 2.0f) * kPi / 180.0f;
    float y = near_val * tanf(angle_y);

    // Fov-x < 0 implies to use aspect ratio.
    if (cam_fov_x_ > 0.0f) {
      float angle_x = (cam_fov_x_ / 2.0f) * kPi / 180.0f;
      x = near_val * tanf(angle_x);
    } else {
      x = y * GetPhysicalAspectRatio();
    }
    projection_matrix_ = Matrix44fFrustum(-x, x, -y, y, near_val, far_val);
  }
  g_base->graphics_server->SetProjectionMatrix(projection_matrix_);
}

void RenderPass::Complete() {
  if (UsesWorldLists()) {
    for (auto& command : commands_) {
      command->Finalize();
    }
  } else {
    commands_flat_->Finalize();
    commands_flat_transparent_->Finalize();
  }
}

auto RenderPass::HasDrawCommands() const -> bool {
  if (UsesWorldLists()) {
    throw Exception();
  } else {
    return (commands_flat_transparent_->has_draw_commands()
            || commands_flat_->has_draw_commands());
  }
}

}  // namespace ballistica::base
