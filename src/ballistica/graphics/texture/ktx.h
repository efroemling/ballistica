// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_TEXTURE_KTX_H_
#define BALLISTICA_GRAPHICS_TEXTURE_KTX_H_

#include <string>

#include "ballistica/ballistica.h"

// currently need gl for this stuff.. probably not necessary.
#if BA_ENABLE_OPENGL

namespace ballistica {

void LoadKTX(const std::string& file_name, unsigned char** buffers, int* widths,
             int* heights, TextureFormat* formats, size_t* sizes,
             TextureQuality texture_quality, int min_quality, int* base_level);

void KTXUnpackETC(const uint8_t* src_etc, unsigned int src_format,
                  uint32_t active_width, uint32_t active_height,
                  uint8_t** dst_image, unsigned int* format,
                  unsigned int* internal_format, unsigned int* type,
                  int r16_formats, bool supports_srgb);

}  // namespace ballistica

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_GRAPHICS_TEXTURE_KTX_H_
