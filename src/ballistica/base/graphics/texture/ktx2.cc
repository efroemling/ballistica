// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/texture/ktx2.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

// Vulkan format constants we recognize. Just the ones the asset-package
// recipes emit today; expand as new TextureProfile variants come online.
static constexpr uint32_t kVkFormatR8G8B8A8SRGB = 43;

// Translate a ``vkFormat`` to our engine's ``TextureFormat`` enum.
// Throws on anything unsupported so the caller surfaces a clear error.
static auto VkFormatToInternal(uint32_t vk_format, const std::string& file_name)
    -> TextureFormat {
  switch (vk_format) {
    case kVkFormatR8G8B8A8SRGB:
      return TextureFormat::kRGBA_8888;
    default:
      throw Exception("Unsupported KTX2 vkFormat " + std::to_string(vk_format)
                      + " in \"" + file_name + "\".");
  }
}

// Bytes per pixel for the small set of uncompressed formats we accept.
// Used to compute per-mip byte sizes when KTX2 level lengths are
// validated.
static auto BytesPerPixelForFormat(TextureFormat fmt) -> size_t {
  switch (fmt) {
    case TextureFormat::kRGBA_8888:
      return 4;
    default:
      return 0;
  }
}

void LoadKTX2(const std::string& file_name, unsigned char** buffers,
              int* widths, int* heights, TextureFormat* formats, size_t* sizes,
              TextureQuality texture_quality, int min_quality,
              int* base_level) {
  *base_level = 0;

  FILE* f = g_core->platform->FOpen(file_name.c_str(), "rb");
  if (!f) {
    throw Exception("Can't open KTX2 file: \"" + file_name + "\".");
  }

  unsigned char magic[12];
  if (fread(magic, sizeof(magic), 1, f) != 1
      || memcmp(magic, kKTX2Magic, sizeof(kKTX2Magic)) != 0) {
    fclose(f);
    throw Exception("Not a KTX2 file (bad magic): \"" + file_name + "\".");
  }

  KTX2Header hdr{};
  if (fread(&hdr, sizeof(hdr), 1, f) != 1) {
    fclose(f);
    throw Exception("Short read on KTX2 header: \"" + file_name + "\".");
  }

  if (hdr.supercompression_scheme != 0) {
    fclose(f);
    throw Exception(
        "KTX2 supercompression scheme "
        + std::to_string(hdr.supercompression_scheme)
        + " not supported (Basis/zstd not implemented; see initiative"
          " decision #12): \""
        + file_name + "\".");
  }

  // 2D-only for v1. faceCount > 1 = cube map; layerCount > 0 = array
  // texture; pixelDepth > 0 = 3D. These need separate code paths
  // (and additional ``TextureType`` enum values for arrays); not in
  // scope for the first KTX2 milestone.
  if (hdr.face_count != 1 || hdr.layer_count != 0 || hdr.pixel_depth != 0) {
    fclose(f);
    throw Exception("KTX2 cube/array/3D textures not yet supported: \""
                    + file_name + "\".");
  }

  if (hdr.level_count == 0) {
    fclose(f);
    throw Exception("KTX2 file has zero mip levels: \"" + file_name + "\".");
  }

  TextureFormat fmt = VkFormatToInternal(hdr.vk_format, file_name);
  size_t bpp = BytesPerPixelForFormat(fmt);

  std::vector<KTX2LevelIndex> level_index(hdr.level_count);
  if (fread(level_index.data(), sizeof(KTX2LevelIndex), hdr.level_count, f)
      != hdr.level_count) {
    fclose(f);
    throw Exception("Short read on KTX2 level index: \"" + file_name + "\".");
  }

  // Quality-driven base_level bump (mirrors the LoadDDS heuristic so
  // medium/low quality drop the largest 1-2 mips). Texture dimensions
  // are taken from the header — level 0 dimensions.
  int mip_count = static_cast<int>(hdr.level_count);
  if ((texture_quality == TextureQuality::kLow
       || texture_quality == TextureQuality::kMedium)
      && (min_quality < 2) && mip_count >= *base_level + 1) {
    (*base_level)++;
  }
  if (texture_quality == TextureQuality::kLow && (min_quality < 1)
      && (hdr.pixel_width > 128) && (hdr.pixel_height > 128)
      && mip_count >= *base_level + 1) {
    (*base_level)++;
  }

  // Walk levels 0..N-1 (mip-major, level 0 = largest). For each
  // level: compute width/height by halving, allocate + read bytes
  // if at-or-above base_level, otherwise leave buffer nullptr.
  auto x = static_cast<unsigned int>(hdr.pixel_width);
  auto y = static_cast<unsigned int>(hdr.pixel_height);
  for (int ix = 0; ix < mip_count; ++ix) {
    auto byte_length = static_cast<size_t>(level_index[ix].byte_length);

    // Cross-check the on-disk byte_length against what we expect from
    // the format + dimensions. Catches malformed files / mismatched
    // recipes early rather than surfacing as garbage texel data.
    if (bpp != 0) {
      size_t expected = static_cast<size_t>(x) * static_cast<size_t>(y) * bpp;
      if (expected != byte_length) {
        fclose(f);
        throw Exception("KTX2 mip " + std::to_string(ix) + " byte length "
                        + std::to_string(byte_length) + " != expected "
                        + std::to_string(expected) + " for " + std::to_string(x)
                        + "x" + std::to_string(y) + ": \"" + file_name + "\".");
      }
    }

    widths[ix] = static_cast<int>(x);
    heights[ix] = static_cast<int>(y);
    formats[ix] = fmt;
    sizes[ix] = byte_length;

    if (ix >= *base_level) {
      // fseek + fread for each level — level offsets aren't guaranteed
      // to be in file order (spec recommends smallest-mip-first
      // layout), so we can't stream sequentially.
      buffers[ix] = static_cast<unsigned char*>(malloc(byte_length));
      if (buffers[ix] == nullptr) {
        fclose(f);
        throw Exception("malloc failed for KTX2 mip " + std::to_string(ix)
                        + " (" + std::to_string(byte_length) + " bytes): \""
                        + file_name + "\".");
      }
      if (fseek(f, static_cast<long>(level_index[ix].byte_offset),  // NOLINT
                SEEK_SET)
          != 0) {
        free(buffers[ix]);
        buffers[ix] = nullptr;
        fclose(f);
        throw Exception("fseek failed on KTX2 mip " + std::to_string(ix)
                        + ": \"" + file_name + "\".");
      }
      if (fread(buffers[ix], byte_length, 1, f) != 1) {
        free(buffers[ix]);
        buffers[ix] = nullptr;
        fclose(f);
        throw Exception("Short read on KTX2 mip " + std::to_string(ix) + ": \""
                        + file_name + "\".");
      }
    } else {
      buffers[ix] = nullptr;
    }

    x = std::max(1u, x >> 1u);
    y = std::max(1u, y >> 1u);
  }

  fclose(f);
}

}  // namespace ballistica::base
