// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/graphics_settings.h"

#include <algorithm>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/support/app_config.h"

namespace ballistica::base {

GraphicsSettings::GraphicsSettings()

    : resolution{g_base->graphics->screen_pixel_width(),
                 g_base->graphics->screen_pixel_height()},
      resolution_virtual{g_base->graphics->screen_virtual_width(),
                         g_base->graphics->screen_virtual_height()},
      pixel_scale{std::clamp(
          g_base->app_config->Resolve(AppConfig::FloatID::kScreenPixelScale),
          0.1f, 1.0f)},
      graphics_quality{g_base->graphics->GraphicsQualityFromAppConfig()},
      texture_quality{g_base->graphics->TextureQualityFromAppConfig()},
      tv_border{
          g_base->app_config->Resolve(AppConfig::BoolID::kEnableTVBorder)} {}

}  // namespace ballistica::base
