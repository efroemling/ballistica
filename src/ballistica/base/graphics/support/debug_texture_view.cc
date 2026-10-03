// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/debug_texture_view.h"

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/support/fixed_camera.h"
#include "ballistica/base/graphics/support/frame_def.h"

namespace ballistica::base {

const int kDebugTextureViewSize{256};

// Where we show up on screen (virtual coords) and how big.
const float kDebugTextureViewScreenX{150.0f};
const float kDebugTextureViewScreenY{150.0f};
const float kDebugTextureViewScreenSize{256.0f};
const float kDebugTextureViewZDepth{-0.04f};

static auto NewDebugTextureViewCamera() -> Object::Ref<FixedCamera> {
  auto camera = Object::New<FixedCamera>();
  camera->set_position(Vector3f(0.0f, 2.0f, 8.0f));
  camera->set_target(Vector3f(0.0f, 0.0f, 0.0f));
  camera->set_field_of_view_y(30.0f);
  camera->SetClip(1.0f, 50.0f);
  return camera;
}

DebugTextureView::DebugTextureView()
    : RenderView(NewDebugTextureViewCamera().get(), kDebugTextureViewSize,
                 kDebugTextureViewSize) {
  set_max_quality(GraphicsQuality::kMedium);
  set_clear_color(Vector3f(0.2f, 0.25f, 0.35f));
}

DebugTextureView::~DebugTextureView() = default;

void DebugTextureView::DrawWorld(FrameDef* frame_def) {
  auto angle = static_cast<float>(frame_def->display_time() * 60.0);

  {
    ObjectComponent c(frame_def->beauty_pass());
    c.SetTexture(g_base->assets->base_assets().boxing_gloves_color.get());
    c.SetReflection(ReflectionType::kSoft);
    c.SetReflectionScale(0.4f, 0.4f, 0.4f);
    c.SetLightShadow(LightShadowType::kObject);
    {
      auto xf = c.ScopedTransform();

      // Sit up and to the right of center, so that a texture drawn
      // flipped or mirrored shows.
      c.Translate(1.0f, 0.8f, 0.0f);
      c.Scale(6.0f, 6.0f, 6.0f);
      c.Rotate(angle, 0.0f, 1.0f, 0.0f);
      c.DrawMeshAsset(g_base->assets->base_assets().boxing_glove.get());
    }
    c.Submit();
  }

  // A light of our own, passing by on one side, to show that light and
  // shadow here are ours and not the main world's.
  DrawBlotchSoftObj(Vector3f(3.0f * sinf(angle * 0.03f), 0.0f, 1.0f), 4.0f,
                    0.4f, 0.3f, 0.1f, 0.0f);
}

void DebugTextureView::DrawToOverlay(RenderPass* pass) {
  SimpleComponent c(pass);
  c.SetTexture(texture());
  {
    auto xf = c.ScopedTransform();
    c.Translate(kDebugTextureViewScreenX, kDebugTextureViewScreenY,
                kDebugTextureViewZDepth);
    c.Scale(kDebugTextureViewScreenSize, kDebugTextureViewScreenSize);
    c.DrawMeshAsset(
        g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
  }
  c.Submit();
}

}  // namespace ballistica::base
