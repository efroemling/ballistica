// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/scene_viewer_context.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include "ballistica/base/graphics/support/fixed_camera.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/ui_v1/support/viewer_source.h"

namespace ballistica::scene_v1 {

// The most scene steps we'll take to catch up with display time in one
// go. Falling further behind than this means something is badly
// bogged down, and piling more steps on would only make that worse; we
// let the time go instead.
const int kSceneViewerMaxStepsPerUpdate{8};

std::vector<SceneViewerContext*> SceneViewerContext::s_viewers_;

/// Our view: a texture view whose world is our scene.
class SceneViewerContext::View : public base::RenderView {
 public:
  View(SceneViewerContext* context, base::Camera* camera, int width, int height)
      : RenderView(camera, width, height), context_(context) {}

  void DrawWorld(base::FrameDef* frame_def) override {
    if (context_ != nullptr) {
      context_->Draw(frame_def);
    }
  }

  /// Called by our context as it goes away (we can outlast it briefly
  /// if a frame that drew us is still around).
  void ClearContext() { context_ = nullptr; }

 private:
  SceneViewerContext* context_;
};

/// Us as seen by ui.
class SceneViewerContext::Source : public ui_v1::ViewerSource {
 public:
  explicit Source(SceneViewerContext* context) : context_(context) {}

  auto GetViewerTexture() -> base::TextureAsset* override {
    SceneViewerContext* context = context_.get();
    if (context == nullptr || context->shutting_down()) {
      return nullptr;
    }
    return context->view()->texture();
  }

  void SetViewerPixelSize(int width, int height) override {
    SceneViewerContext* context = context_.get();
    if (context == nullptr || context->shutting_down()) {
      return;
    }
    context->SetSize(width, height);
  }

  auto GetName() const -> std::string override {
    SceneViewerContext* context = context_.get();
    return context != nullptr ? context->GetContextDescription()
                              : "<SceneViewer (dead)>";
  }

 private:
  Object::WeakRef<SceneViewerContext> context_;
};

SceneViewerContext::SceneViewerContext(int width, int height)
    : LocalSceneContext(0, kProtocolVersionMax) {
  assert(g_base->InLogicThread());
  camera_ = Object::New<base::FixedCamera>();
  auto [fit_width, fit_height] = FitSize_(width, height);
  view_ = Object::New<View>(this, camera_.get(), fit_width, fit_height);
  source_ = Object::New<Source>(this);

  scene()->set_render_view(view_.get());
  scene()->set_silent(true);

  s_viewers_.push_back(this);
}

SceneViewerContext::~SceneViewerContext() {
  assert(g_base->InLogicThread());
  s_viewers_.erase(std::remove(s_viewers_.begin(), s_viewers_.end(), this),
                   s_viewers_.end());

  // Take our scene down while our view and camera are still here for
  // its nodes to take their leave of.
  Shutdown();
  view_->ClearContext();
}

auto SceneViewerContext::view() const -> base::RenderView* {
  assert(view_.exists());
  return view_.get();
}

auto SceneViewerContext::viewer_source() const -> ui_v1::ViewerSource* {
  assert(source_.exists());
  return source_.get();
}

auto SceneViewerContext::FitSize_(int width, int height)
    -> std::pair<int, int> {
  width = std::max(width, 1);
  height = std::max(height, 1);
  int largest = std::max(width, height);
  if (largest > kMaxSize) {
    const double scale = static_cast<double>(kMaxSize) / largest;
    width =
        std::clamp(static_cast<int>(std::round(width * scale)), 1, kMaxSize);
    height =
        std::clamp(static_cast<int>(std::round(height * scale)), 1, kMaxSize);
  }
  return {width, height};
}

void SceneViewerContext::SetSize(int width, int height) {
  assert(g_base->InLogicThread());
  std::tie(width, height) = FitSize_(width, height);
  if (width != view_->width() || height != view_->height()) {
    view_->SetSize(width, height);
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kDebug, [this] {
      return GetContextDescription() + " size is now "
             + std::to_string(view_->width()) + "x"
             + std::to_string(view_->height()) + ".";
    });
  }
}

auto SceneViewerContext::GetContextDescription() -> std::string {
  return "<SceneViewer " + std::to_string(view_->id()) + ">";
}

void SceneViewerContext::StepAllDisplayTime(millisecs_t time_advance) {
  assert(g_base->InLogicThread());

  // Work from a copy; stepping runs timers, which can run code that
  // makes or gets rid of viewers.
  std::vector<Object::Ref<SceneViewerContext>> viewers;
  viewers.reserve(s_viewers_.size());
  for (SceneViewerContext* viewer : s_viewers_) {
    viewers.emplace_back(viewer);
  }
  for (auto&& viewer : viewers) {
    viewer->StepDisplayTime_(time_advance);
  }
}

void SceneViewerContext::SetSound(bool enabled, float volume, float pan_scale) {
  assert(g_base->InLogicThread());
  sound_enabled_ = enabled;
  sound_volume_ = volume;
  sound_pan_scale_ = pan_scale;
  scene()->set_silent(!enabled);
  if (enabled) {
    UpdateAudioListener_();
  } else {
    scene()->SetAudioListenerSpace(nullptr);
  }
}

void SceneViewerContext::UpdateAudioListener_() {
  const Vector3f& pos = camera_->GetPosition();
  Vector3f forward = camera_->target() - pos;
  if (forward.LengthSquared() < 0.000001f) {
    return;
  }
  forward = forward.Normalized();
  Vector3f right = Vector3f::Cross(forward, Vector3f(0.0f, 1.0f, 0.0f));
  if (right.LengthSquared() < 0.000001f) {
    // Looking straight up or down; any sideways will do.
    right = Vector3f(1.0f, 0.0f, 0.0f);
  }
  right = right.Normalized();
  base::AudioListenerSpace space;
  space.origin = pos;
  space.right = right;
  space.up = Vector3f::Cross(right, forward);
  space.back = forward * -1.0f;
  space.pan_scale = sound_pan_scale_;
  space.gain = sound_volume_;
  scene()->SetAudioListenerSpace(&space);
}

void SceneViewerContext::StepDisplayTime_(millisecs_t time_advance) {
  if (shutting_down()) {
    return;
  }

  // Stand still while no one is looking.
  if (!view_->wanted()) {
    unstepped_time_ = 0;
    return;
  }

  // Our camera may have moved; keep what we hear matching what we
  // show.
  if (sound_enabled_) {
    UpdateAudioListener_();
  }

  unstepped_time_ += time_advance;
  int steps{};
  while (unstepped_time_ >= kGameStepMilliseconds) {
    if (steps >= kSceneViewerMaxStepsPerUpdate) {
      unstepped_time_ = 0;
      break;
    }
    unstepped_time_ -= kGameStepMilliseconds;
    base::ScopedSetContext ssc(this);
    Step();
    steps++;
    if (shutting_down()) {
      return;
    }
  }
}

}  // namespace ballistica::scene_v1
