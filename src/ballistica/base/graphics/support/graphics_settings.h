// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_GRAPHICS_SETTINGS_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_GRAPHICS_SETTINGS_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/math/vector2f.h"

namespace ballistica::base {

/// A set of settings for graphics, covering things like screen
/// resolution, texture quality, etc. These are filled out by the
/// AppAdapter in the logic thread and passed up to the GraphicsServer
/// either through standalone calls or attached to a FrameDef. Generally
/// AppAdapters define their own subclass of this containing additional
/// settings specific to themselves or the renderer(s) they use.
struct GraphicsSettings {
  GraphicsSettings();
  // Each new settings instance will be assigned a unique incrementing index.
  int index{-1};

  // Some standard settings used by most renderers.
  Vector2f resolution;
  Vector2f resolution_virtual;
  float pixel_scale;
  GraphicsQualityRequest graphics_quality;
  TextureQualityRequest texture_quality;
  bool tv_border;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_GRAPHICS_SETTINGS_H_
