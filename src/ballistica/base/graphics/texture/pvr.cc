// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/texture/pvr.h"

#include <algorithm>
#include <cstdio>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/exception.h"

namespace ballistica::base {

#define PVR_TEXTURE_FLAG_TYPE_MASK 0xffu

enum { kPVRTextureFlagTypePVRTC_2 = 24, kPVRTextureFlagTypePVRTC_4 };

typedef struct _PVRTexHeader {
  uint32_t headerLength;
  uint32_t height;
  uint32_t width;
  uint32_t numMipmaps;
  uint32_t flags;
  uint32_t dataLength;
  uint32_t bpp;
  uint32_t bitmaskRed;
  uint32_t bitmaskGreen;
  uint32_t bitmaskBlue;
  uint32_t bitmaskAlpha;
  uint32_t pvrTag;
  uint32_t num_surfs;
} PVRTexHeader;

typedef struct _PVRTexHeader2 {
  uint32_t version;
  uint32_t flags;
  uint64_t pixel_format;
  uint32_t color_space;
  uint32_t channel_type;
  uint32_t height;
  uint32_t width;
  uint32_t depth;
  uint32_t num_surfs;
  uint32_t num_faces;
  uint32_t numMipmaps;
  uint32_t metaSize;
} PVRTexHeader2;

void LoadPVR(const std::string& file_name, unsigned char** buffers, int* widths,
             int* heights, TextureFormat* formats, size_t* sizes,
             TextureQuality texture_quality, int min_quality, int* base_level) {
  (*base_level) = 0;

  FILE* f = g_core->platform->FOpen(file_name.c_str(), "rb");
  if (!f) throw Exception("can't open file: \"" + file_name + "\"");

  TextureFormat internal_format;

  uint32_t block_size, width_blocks, height_blocks;
  uint32_t width, height, bpp, format_flags;

  if (explicit_bool(true)) {
    _PVRTexHeader2 hdr2{};

    BA_PRECONDITION(fread(&hdr2, 52, 1, f) == 1);
    BA_PRECONDITION(hdr2.version == 0x03525650);
    BA_PRECONDITION(hdr2.flags == 0);
    BA_PRECONDITION(hdr2.color_space == 0);   // linear RGB
    BA_PRECONDITION(hdr2.channel_type == 0);  // unsigned byte normalized
    BA_PRECONDITION(hdr2.pixel_format == 2
                    || hdr2.pixel_format == 3);  // PVRTC 4pp RGB/RGBA
    BA_PRECONDITION(hdr2.num_surfs == 1);
    BA_PRECONDITION(hdr2.num_faces == 1);
    BA_PRECONDITION(hdr2.depth == 1);

    internal_format = TextureFormat::kPVR4;

    // Skip over metadata.
    BA_PRECONDITION(fseek(f,
                          static_cast_check_fit<long>(hdr2.metaSize),  // NOLINT
                          SEEK_CUR)
                    == 0);

    width = hdr2.width;
    height = hdr2.height;

    int mip_map_count = static_cast_check_fit<int>(hdr2.numMipmaps);

    // Try dropping a level for med/low quality.
    if ((texture_quality == TextureQuality::kLow
         || texture_quality == TextureQuality::kMedium)
        && (min_quality < 2)
        && static_cast_check_fit<int>(mip_map_count) >= (*base_level) + 1)
      (*base_level)++;

    // And one more for low in some cases.
    if (texture_quality == TextureQuality::kLow && (min_quality < 1)
        && (width > 128) && (height > 128)
        && mip_map_count >= (*base_level) + 1)
      (*base_level)++;

    // Calculate the data size for each texture level and respect the minimum
    // number of blocks
    for (int ix = 0; ix < mip_map_count; ix++) {
      {
        block_size = 4 * 4;  // Pixel by pixel block size for 4bpp
        width_blocks = width / 4;
        height_blocks = height / 4;
        bpp = 4;
      }

      // Clamp to minimum number of blocks
      if (width_blocks < 2) {
        width_blocks = 2;
      }
      if (height_blocks < 2) {
        height_blocks = 2;
      }

      uint32_t data_size{width_blocks * height_blocks
                         * ((block_size * bpp) / 8)};

      // Load or skip levels depending on our quality.
      if ((*base_level) <= ix) {
        sizes[ix] = data_size;
        buffers[ix] = (unsigned char*)malloc(data_size);
        BA_PRECONDITION(buffers[ix]);
        widths[ix] = width;
        heights[ix] = height;
        formats[ix] = internal_format;
        BA_PRECONDITION(fread(buffers[ix], data_size, 1, f) == 1);
      } else {
        buffers[ix] = nullptr;
        BA_PRECONDITION(fseek(f,
                              static_cast_check_fit<long>(data_size),  // NOLINT
                              SEEK_CUR)
                        == 0);
      }
      width = std::max(width >> 1u, 1u);
      height = std::max(height >> 1u, 1u);
    }
  } else {
    uint32_t pvrTag;

    uint32_t data_offset = 0;

    _PVRTexHeader hdr{};

    BA_PRECONDITION(fread(&hdr, sizeof(hdr), 1, f) == 1);
    BA_PRECONDITION(hdr.headerLength == sizeof(_PVRTexHeader));

    pvrTag = hdr.pvrTag;
    if (gPVRTexIdentifier[0] != ((pvrTag >> 0u) & 0xffu)
        || gPVRTexIdentifier[1] != ((pvrTag >> 8u) & 0xffu)
        || gPVRTexIdentifier[2] != ((pvrTag >> 16u) & 0xffu)
        || gPVRTexIdentifier[3] != ((pvrTag >> 24u) & 0xffu)) {
      throw Exception("Invalid PVR file: \"" + file_name + "\"");
    }

    format_flags = hdr.flags & PVR_TEXTURE_FLAG_TYPE_MASK;

    if (format_flags != kPVRTextureFlagTypePVRTC_4
        && format_flags != kPVRTextureFlagTypePVRTC_2)
      throw Exception("Invalid PVR format in file: \"" + file_name + "\"");

    if (format_flags == kPVRTextureFlagTypePVRTC_4) {
      internal_format = TextureFormat::kPVR4;
    } else if (explicit_bool(format_flags == kPVRTextureFlagTypePVRTC_2)) {
      internal_format = TextureFormat::kPVR2;
    } else {
      throw Exception();
    }

    uint32_t data_length{hdr.dataLength};

    width = hdr.width;
    height = hdr.height;

    int mip_map_count = static_cast_check_fit<int>(hdr.numMipmaps + 1);

    // Try dropping a level for med/low quality.
    if ((texture_quality == TextureQuality::kLow
         || texture_quality == TextureQuality::kMedium)
        && (min_quality < 2) && mip_map_count >= (*base_level) + 1) {
      (*base_level)++;
    }

    // And one more for low in some cases.
    if (texture_quality == TextureQuality::kLow && (min_quality < 1)
        && (width > 128) && (height > 128)
        && mip_map_count >= (*base_level) + 1)
      (*base_level)++;

    // Calculate the data size for each texture level and respect the minimum
    // number of blocks
    int ix = 0;
    while (data_offset < data_length) {
      if (format_flags == kPVRTextureFlagTypePVRTC_4) {
        block_size = 4 * 4;  // Pixel by pixel block size for 4bpp
        width_blocks = width / 4;
        height_blocks = height / 4;
        bpp = 4;
      } else {
        block_size = 8 * 4;  // Pixel by pixel block size for 2bpp
        width_blocks = width / 8;
        height_blocks = height / 4;
        bpp = 2;
      }

      // Clamp to minimum number of blocks.
      if (width_blocks < 2) {
        width_blocks = 2;
      }
      if (height_blocks < 2) {
        height_blocks = 2;
      }

      uint32_t data_size{width_blocks * height_blocks
                         * ((block_size * bpp) / 8)};

      // Load or skip levels depending on our quality.
      if ((*base_level) <= ix) {
        sizes[ix] = data_size;
        buffers[ix] = (unsigned char*)malloc(data_size);
        BA_PRECONDITION(buffers[ix]);
        widths[ix] = width;
        heights[ix] = height;
        formats[ix] = internal_format;
        BA_PRECONDITION(fread(buffers[ix], data_size, 1, f) == 1);
      } else {
        buffers[ix] = nullptr;
        BA_PRECONDITION(fseek(f,
                              static_cast_check_fit<long>(data_size),  // NOLINT
                              SEEK_CUR)
                        == 0);
      }
      data_offset += data_size;

      width = std::max(width >> 1u, 1u);
      height = std::max(height >> 1u, 1u);
      ix++;
    }
    BA_PRECONDITION(ix == mip_map_count);
  }
  fclose(f);
}

}  // namespace ballistica::base
