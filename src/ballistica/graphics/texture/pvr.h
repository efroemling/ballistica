// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_TEXTURE_PVR_H_
#define BALLISTICA_GRAPHICS_TEXTURE_PVR_H_

#include <string>

#include "ballistica/ballistica.h"

namespace ballistica {

static char gPVRTexIdentifier[5] = "PVR!";

void LoadPVR(const std::string& file_name, unsigned char** buffers, int* widths,
             int* heights, TextureFormat* formats, size_t* sizes,
             TextureQuality texture_quality, int min_quality, int* base_level);

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_TEXTURE_PVR_H_
