// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_DATA_TEXTURE_PRELOAD_DATA_H_
#define BALLISTICA_MEDIA_DATA_TEXTURE_PRELOAD_DATA_H_

#include "ballistica/ballistica.h"

namespace ballistica {

// Determined by the biggest tex dimension we support (current 4096).
// FIXME: Should define that dimension as a constant somewhere.
const int kMaxTextureLevels = 14;

// Temporary data that is passed along to the renderer when creating
// rendererdata. This may include sdl surfaces and/or compressed buffers.
class TexturePreloadData {
 public:
  static void rgba8888_to_rgba4444_in_place(void* src, size_t cb);

  TexturePreloadData() {
    // There isn't a way to do this in bracket-init, is there?
    // (aside from writing out all values manually I mean).
    for (auto& format : formats) {
      format = TextureFormat::kNone;
    }
  }
  ~TexturePreloadData();
  void ConvertToUncompressed(TextureData* texture);

  uint8_t* buffers[kMaxTextureLevels]{};
  size_t sizes[kMaxTextureLevels]{};
  TextureFormat formats[kMaxTextureLevels]{};
  int widths[kMaxTextureLevels]{};
  int heights[kMaxTextureLevels]{};
  int base_level{};
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_DATA_TEXTURE_PRELOAD_DATA_H_
