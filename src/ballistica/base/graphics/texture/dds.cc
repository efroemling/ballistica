// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/texture/dds.h"

#include <algorithm>
#include <cstdio>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/exception.h"

/* DDS loader written by Jon Watte 2002 */
/* Permission granted to use freely, as long as Jon Watte */
/* is held harmless for all possible damages resulting from */
/* your use or failure to use this code. */
/* No warranty is expressed or implied. Use at your own risk, */
/* or not at all. */

namespace ballistica::base {

struct DdsLoadInfo {
  bool compressed;
  bool swap;
  bool palette;
  unsigned int divSize;
  unsigned int blockBytes;
  TextureFormat internal_format;
  int externalFormat;
  int type;
};

DdsLoadInfo loadInfoDXT1 = {true, false, false, 4, 8, TextureFormat::kDXT1};
DdsLoadInfo loadInfoDXT5 = {true, false, false, 4, 16, TextureFormat::kDXT5};
DdsLoadInfo loadInfoETC1 = {true, false, false, 4, 8, TextureFormat::kETC1};

void LoadDDS(const std::string& file_name, unsigned char** buffers, int* widths,
             int* heights, TextureFormat* formats, size_t* sizes,
             TextureQuality texture_quality, int min_quality, int* base_level) {
  (*base_level) = 0;

  FILE* f = g_core->platform->FOpen(file_name.c_str(), "rb");
  if (!f) {
    throw Exception("can't open file: \"" + file_name + "\"");
  }

  DDS_header hdr{};

  //  DDS is so simple to read, too
  BA_PRECONDITION(fread(&hdr, sizeof(hdr), 1, f) == 1);
  BA_PRECONDITION(hdr.dwMagic == DDS_MAGIC);
  BA_PRECONDITION(hdr.dwSize == 124);

  if (hdr.dwMagic != DDS_MAGIC || hdr.dwSize != 124
      || !(hdr.dwFlags & DDSD_PIXELFORMAT) || !(hdr.dwFlags & DDSD_CAPS)) {
    throw Exception("invalid DDS file: \"" + file_name + "\"");
  }

  int x_size = static_cast_check_fit<int>(hdr.dwWidth);
  int y_size = static_cast_check_fit<int>(hdr.dwHeight);

  BA_PRECONDITION(!(x_size & (x_size - 1)));
  BA_PRECONDITION(!(y_size & (y_size - 1)));

  DdsLoadInfo* li;

  if (PF_IS_DXT1(hdr.sPixelFormat)) {
    li = &loadInfoDXT1;
  } else if (PF_IS_DXT5(hdr.sPixelFormat)) {
    li = &loadInfoDXT5;
  } else if (PF_IS_EXTENDED(hdr.sPixelFormat)) {
    DDS_header_DX10 hExt;

    BA_PRECONDITION(fread(&hExt, sizeof(hExt), 1, f) == 1);

    // Format should be unknown.
    // Hmmm we have no way of determining that this is etc1 data so we just
    // assume.. ew.
    BA_PRECONDITION(hExt.dxgiFormat == 0);

    // Dimension should be tex2d(3).
    BA_PRECONDITION(hExt.resourceDimension == 3);
    BA_PRECONDITION(hExt.arraySize == 1);

    li = &loadInfoETC1;

  } else {
    throw Exception("Unsupported data type in DDS file \"" + file_name + "\"");
  }

  auto x = static_cast<unsigned int>(x_size);
  auto y = static_cast<unsigned int>(y_size);

  int mip_map_count = (hdr.dwFlags & DDSD_MIPMAPCOUNT)
                          ? static_cast<int>(hdr.dwMipMapCount)
                          : 1;

  // try dropping a level for med/low quality..
  if ((texture_quality == TextureQuality::kLow
       || texture_quality == TextureQuality::kMedium)
      && (min_quality < 2) && mip_map_count >= (*base_level) + 1)
    (*base_level)++;

  // and one more for low in some cases....
  if (texture_quality == TextureQuality::kLow && (min_quality < 1)
      && (x_size > 128) && (y_size > 128) && mip_map_count >= (*base_level) + 1)
    (*base_level)++;

  if (li->compressed) {
    size_t size = std::max(li->divSize, x) / li->divSize
                  * std::max(li->divSize, y) / li->divSize * li->blockBytes;

    for (int ix = 0; ix < mip_map_count; ++ix) {
      // Load or skip levels depending on our quality.
      if ((*base_level) <= ix) {
        sizes[ix] = static_cast<uint32_t>(size);
        buffers[ix] = (unsigned char*)malloc(size);
        BA_PRECONDITION(buffers[ix]);
        widths[ix] = static_cast<int>(x);
        heights[ix] = static_cast<int>(y);
        formats[ix] = li->internal_format;
        BA_PRECONDITION(fread(buffers[ix], size, 1, f) == 1);
      } else {
        buffers[ix] = nullptr;
        BA_PRECONDITION(fseek(f, static_cast_check_fit<long>(size),  // NOLINT
                              SEEK_CUR)
                        == 0);
      }

      x = (x + 1u) >> 1u;
      y = (y + 1u) >> 1u;
      size = std::max(li->divSize, x) / li->divSize * std::max(li->divSize, y)
             / li->divSize * li->blockBytes;
    }
  } else if (li->palette) {
    throw Exception("palette support disabled");
  } else {
    throw Exception("regular tex dds support disabled");
  }
  fclose(f);
}

}  // namespace ballistica::base
