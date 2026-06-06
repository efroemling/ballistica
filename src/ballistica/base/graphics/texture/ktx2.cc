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
static constexpr uint32_t kVkFormatBC7SRGBBlock = 146;      // DESKTOP_V1
static constexpr uint32_t kVkFormatASTC4x4SRGBBlock = 158;  // MOBILE_V1
static constexpr uint32_t kVkFormatASTC6x6SRGBBlock = 166;  // MOBILE_V1
static constexpr uint32_t kVkFormatASTC8x8SRGBBlock = 172;  // MOBILE_V1

// Translate a ``vkFormat`` to our engine's ``TextureFormat`` enum.
// Throws on anything unsupported so the caller surfaces a clear error.
static auto VkFormatToInternal(uint32_t vk_format, const std::string& file_name)
    -> TextureFormat {
  switch (vk_format) {
    case kVkFormatR8G8B8A8SRGB:
      return TextureFormat::kRGBA_8888;
    case kVkFormatBC7SRGBBlock:
      return TextureFormat::kBC7;
    case kVkFormatASTC4x4SRGBBlock:
      return TextureFormat::kASTC_4x4;
    case kVkFormatASTC6x6SRGBBlock:
      return TextureFormat::kASTC_6x6;
    case kVkFormatASTC8x8SRGBBlock:
      return TextureFormat::kASTC_8x8;
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
              int* base_level, bool* premultiplied) {
  // Asset-package textures always load every mip in the chosen flavor;
  // the legacy texture-quality mip-skip knob does not apply here (see
  // the header and initiative §7 texture-quality decoupling).
  *base_level = 0;
  *premultiplied = false;

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

  // Read the premultiplied-alpha flag from the DFD. Data-only for now —
  // the renderer does not yet consume it (asset-packages decision #23).
  // DFD section layout (see write_ktx2 in bamaster assetsv1tex.py):
  //   +0  uint32 dfdTotalSize
  //   +4  word0  (vendorId | descriptorType)
  //   +8  word1  (versionNumber | descriptorBlockSize)
  //   +12 word2  (colorModel | primaries | transfer | flags)
  // The flags byte is word2's high byte; KHR_DF_FLAG_ALPHA_PREMULTIPLIED
  // is its bit 0. KTX2 is little-endian, matching all our targets (same
  // assumption as the raw header struct read above). A malformed/missing
  // DFD just leaves *premultiplied false (straight).
  if (hdr.dfd_byte_offset != 0 && hdr.dfd_byte_length >= 16) {
    if (fseek(f, static_cast<long>(hdr.dfd_byte_offset) + 12,  // NOLINT
              SEEK_SET)
        == 0) {
      uint32_t dfd_word2{};
      if (fread(&dfd_word2, sizeof(dfd_word2), 1, f) == 1) {
        *premultiplied = ((dfd_word2 >> 24u) & 1u) != 0u;
      }
    }
  }

  // No quality-driven base_level bump: asset-package textures load all
  // mips present in the chosen flavor (regular/high is a flavor baked
  // into the bytes, not a load-time mip dropdown).

  // Walk levels 0..N-1 (mip-major, level 0 = largest). For each
  // level: compute width/height by halving, allocate + read bytes
  // if at-or-above base_level, otherwise leave buffer nullptr.
  int mip_count = static_cast<int>(hdr.level_count);
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
