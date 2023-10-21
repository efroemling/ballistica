// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/graphics_client_context.h"

#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"

namespace ballistica::base {

GraphicsClientContext::GraphicsClientContext()
    : auto_graphics_quality{g_base->graphics_server->renderer()
                                ->GetAutoGraphicsQuality()},
      auto_texture_quality{
          g_base->graphics_server->renderer()->GetAutoTextureQuality()},
      texture_compression_types{
          g_base->graphics_server->texture_compression_types()} {}

GraphicsClientContext::GraphicsClientContext(int dummy)
    : auto_graphics_quality{GraphicsQuality::kLow},
      auto_texture_quality{TextureQuality::kLow},
      texture_compression_types{0} {}

}  // namespace ballistica::base
