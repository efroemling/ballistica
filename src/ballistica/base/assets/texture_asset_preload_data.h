// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_PRELOAD_DATA_H_
#define BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_PRELOAD_DATA_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

// Determined by the biggest tex dimension we support (current 4096).
// FIXME: Should define that dimension as a constant somewhere.
const int kMaxTextureLevels = 14;

// Temporary data that is passed along to the renderer when creating
// renderer-data. This may include things like sdl surfaces and/or
// compressed buffers.
class TextureAssetPreloadData {
 public:
  static void rgba8888_to_rgba4444_in_place(void* src, size_t cb);

  TextureAssetPreloadData() {
    // There isn't a way to do this in bracket-init, is there?
    // (aside from writing out all values manually I mean).
    for (auto& format : formats) {
      format = TextureFormat::kNone;
    }
  }
  ~TextureAssetPreloadData();
  void ConvertToUncompressed(TextureAsset* texture);

  uint8_t* buffers[kMaxTextureLevels]{};
  size_t sizes[kMaxTextureLevels]{};
  TextureFormat formats[kMaxTextureLevels]{};
  int widths[kMaxTextureLevels]{};
  int heights[kMaxTextureLevels]{};
  int base_level{};

  // Whether the texture's RGB is premultiplied by its alpha, read from
  // the KTX2 DFD's KHR_DF_FLAG_ALPHA_PREMULTIPLIED flag at load
  // (asset-packages decision #23). Fed in now but NOT yet consumed by
  // the GPU upload / blend path — it's a hook for a future
  // premult-aware renderer. Legacy loaders (DDS/KTX/PVR) leave it false.
  bool premultiplied{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_PRELOAD_DATA_H_
