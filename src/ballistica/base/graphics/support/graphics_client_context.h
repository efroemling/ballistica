// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_GRAPHICS_CLIENT_CONTEXT_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_GRAPHICS_CLIENT_CONTEXT_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Represents a valid graphics setup delivered by the graphics server to
/// the logic thread. It contains various info about concrete graphics
/// settings and capabilities.
struct GraphicsClientContext {
  GraphicsClientContext();

  /// Special constructor to create a dummy context (used by headless builds).
  explicit GraphicsClientContext(int dummy);

  auto SupportsTextureCompressionType(TextureCompressionType t) const -> bool {
    return ((texture_compression_types & (0x01u << static_cast<uint32_t>(t)))
            != 0u);
  }

  GraphicsQuality auto_graphics_quality;
  TextureQuality auto_texture_quality;
  uint32_t texture_compression_types;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_GRAPHICS_CLIENT_CONTEXT_H_
