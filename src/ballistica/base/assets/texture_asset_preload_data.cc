// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/texture_asset_preload_data.h"

#if BA_OSTYPE_LINUX
#include <cstring>
#endif

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/texture/ktx.h"

namespace ballistica::base {

#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "bugprone-narrowing-conversions"

#ifndef GL_COMPRESSED_RGB8_ETC2
#define GL_COMPRESSED_RGB8_ETC2 0x9274
#endif
#ifndef GL_COMPRESSED_RGBA8_ETC2_EAC
#define GL_COMPRESSED_RGBA8_ETC2_EAC 0x9278
#endif
#ifndef GL_ETC1_RGB8_OES
#define GL_ETC1_RGB8_OES 0x8D64
#endif

void TextureAssetPreloadData::rgba8888_to_rgba4444_in_place(void* src,
                                                            size_t cb) {
  // Compute the actual number of pixel elements in the buffer.
  size_t cpel = cb / 4;
  auto* psrc = static_cast<uint32_t*>(src);
  auto* pdst = static_cast<uint16_t*>(src);

  int r_dither = 0;
  int g_dither = 0;
  int b_dither = 0;
  int a_dither = 0;

  // reset our dithering slightly randomly to reduce
  // patterns (might be a smarter way to do this)
  int d_reset = rand() % 100;  // NOLINT

  // Convert every pixel.
  for (size_t i = 0; i < cpel; i++) {
    // Read a source pixel.
    int pel = psrc[i];  // NOLINT

    // Unpack the source data as 8 bit values.
    int r = pel & 0xff;
    int g = (pel >> 8) & 0xff;
    int b = (pel >> 16) & 0xff;
    int a = (pel >> 24) & 0xff;
    r = std::min(255, std::max(0, r + r_dither));
    g = std::min(255, std::max(0, g + g_dither));
    b = std::min(255, std::max(0, b + b_dither));
    a = std::min(255, std::max(0, a + a_dither));
    // convert to 4 bit values
    int r2 = r >> 4;
    int g2 = g >> 4;
    int b2 = b >> 4;
    int a2 = a >> 4;

    r_dither = r - (r2 << 4);
    g_dither = g - (g2 << 4);
    b_dither = b - (b2 << 4);
    a_dither = a - (a2 << 4);

    d_reset--;
    if (d_reset <= 0) {
      r_dither = g_dither = b_dither = a_dither = 0;
      d_reset = rand() % 100;  // NOLINT
    }

    pdst[i] =
        static_cast_check_fit<uint16_t>(a2 | b2 << 4 | g2 << 8 | r2 << 12);
  }
}

static void rgba8888_to_rgb888_in_place(void* src, int cb) {
  int i;

  // Compute the actual number of pixel elements in the buffer.
  int cpel = cb / 4;
  auto* psrc = static_cast<uint8_t*>(src);
  auto* pdst = static_cast<uint8_t*>(src);
  for (i = 0; i < cpel; i++) {
    *pdst++ = *psrc++;  // NOLINT
    *pdst++ = *psrc++;
    *pdst++ = *psrc++;
    psrc++;
  }
}

static void rgb888_to_rgb565_in_place(void* src, size_t cb) {
  // compute the actual number of pixel elements in the buffer.
  size_t cpel = cb / 3;
  auto* psrc = static_cast<uint8_t*>(src);
  auto* pdst = static_cast<uint16_t*>(src);

  int r_dither = 0;
  int g_dither = 0;
  int b_dither = 0;

  // reset our dithering slightly randomly to reduce
  // patterns (might be a smarter way to do this)
  int d_reset = rand() % 100;  // NOLINT

  // convert every pixel
  for (size_t i = 0; i < cpel; i++) {
    // read a source pixel
    int r = *psrc++;  // NOLINT
    int g = *psrc++;
    int b = *psrc++;
    // unpack the source data as 8 bit values
    r = std::min(255, std::max(0, r + r_dither));
    g = std::min(255, std::max(0, g + g_dither));
    b = std::min(255, std::max(0, b + b_dither));

    // convert to 565
    int r2 = r >> 3;
    int g2 = g >> 2;
    int b2 = b >> 3;

    r_dither = r - (r2 << 3);
    g_dither = g - (g2 << 2);
    b_dither = b - (b2 << 3);

    d_reset--;
    if (d_reset <= 0) {
      r_dither = g_dither = b_dither = 0;
      d_reset = rand() % 100;  // NOLINT
    }

    *pdst++ = static_cast_check_fit<uint16_t>(b2 | g2 << 5 | r2 << 11);
  }
}

// -----------------------------------------------------------------------------
// S3TC DXT1 / DXT5 Texture Decompression Routines
// Author: Benjamin Dobell - http://www.glassechidna.com.au
//
// Feel free to use these methods in any open-source, freeware or commercial
// projects. It's not necessary to credit me however I would be grateful if you
// chose to do so. I'll also be very interested to hear what projects make use
// of this code. Feel free to drop me a line via the contact form on the Glass
// Echidna website.
//
// NOTE: The code was written for a little endian system where sizeof(int32_t)
// == 4.
// -----------------------------------------------------------------------------

// uint32_t PackRGBA(): Helper method that packs RGBA channels into a single 4
// byte pixel.
//
// unsigned char r:   red channel.
// unsigned char g:   green channel.
// unsigned char b:   blue channel.
// unsigned char a:   alpha channel.

static auto PackRGBA(unsigned char r, unsigned char g, unsigned char b,
                     unsigned char a) -> uint32_t {
  return ((a << 24) | (b << 16) | (g << 8) | r);
}

// void DecompressBlockDXT1(): Decompresses one block of a DXT1 texture and
// stores the resulting pixels at the appropriate offset in 'image'.
//
// uint32_t x:            x-coordinate of the
// first pixel in the block. uint32_t y: y-coordinate of the first pixel in the
// block. uint32_t width: width of the texture being decompressed. uint32_t
// height: height of the texture being decompressed. const unsigned char
// *blockStorage: pointer to the block to decompress. uint32_t *image:
// pointer to image where the decompressed pixel data should be stored.
static void DecompressBlockDXT1(uint32_t x, uint32_t y, uint32_t width,
                                uint32_t height,
                                const unsigned char* block_storage,
                                uint32_t* image) {
  uint16_t color0, color1;
  memcpy(&color0, block_storage, sizeof(color0));
  memcpy(&color1, block_storage + 2, sizeof(color1));

  uint32_t temp;

  temp = (color0 >> 11u) * 255u + 16u;
  auto r0 = (unsigned char)((temp / 32u + temp) / 32u);
  temp = ((color0 & 0x07E0u) >> 5u) * 255u + 32u;
  auto g0 = (unsigned char)((temp / 64u + temp) / 64u);
  temp = (color0 & 0x001Fu) * 255u + 16u;
  auto b0 = (unsigned char)((temp / 32 + temp) / 32);

  temp = (color1 >> 11u) * 255u + 16u;
  auto r1 = (unsigned char)((temp / 32u + temp) / 32u);
  temp = ((color1 & 0x07E0u) >> 5u) * 255u + 32u;
  auto g1 = (unsigned char)((temp / 64u + temp) / 64u);
  temp = (color1 & 0x001Fu) * 255u + 16u;
  auto b1 = (unsigned char)((temp / 32u + temp) / 32u);

  uint32_t code = *reinterpret_cast<const uint32_t*>(block_storage + 4);

  for (int j = 0; j < 4; j++) {
    for (int i = 0; i < 4; i++) {
      uint32_t final_color = 0;
      auto positionCode =
          static_cast<uint8_t>((code >> 2 * (4 * j + i)) & 0x03);

      if (color0 > color1) {
        switch (positionCode) {
          case 0:
            final_color = PackRGBA(r0, g0, b0, 255);
            break;
          case 1:
            final_color = PackRGBA(r1, g1, b1, 255);
            break;
          case 2:
            final_color =
                PackRGBA(static_cast<uint8_t>((2 * r0 + r1) / 3),
                         static_cast<uint8_t>((2 * g0 + g1) / 3),
                         static_cast<uint8_t>((2 * b0 + b1) / 3), 255);
            break;
          case 3:
            final_color =
                PackRGBA(static_cast<uint8_t>((r0 + 2 * r1) / 3),
                         static_cast<uint8_t>((g0 + 2 * g1) / 3),
                         static_cast<uint8_t>((b0 + 2 * b1) / 3), 255);
            break;
          default:
            break;
        }
      } else {
        switch (positionCode) {
          case 0:
            final_color = PackRGBA(r0, g0, b0, 255);
            break;
          case 1:
            final_color = PackRGBA(r1, g1, b1, 255);
            break;
          case 2:
            final_color = PackRGBA(static_cast<uint8_t>((r0 + r1) / 2),
                                   static_cast<uint8_t>((g0 + g1) / 2),
                                   static_cast<uint8_t>((b0 + b1) / 2), 255);
            break;
          case 3:
            final_color = PackRGBA(0, 0, 0, 255);
            break;
          default:
            break;
        }
      }
      if ((x + i < width) && (y + j < height)) {
        image[(y + j) * width + (x + i)] = final_color;
      }
    }
  }
}

// void BlockDecompressImageDXT1(): Decompresses all the blocks of a DXT1
// compressed texture and stores the resulting pixels in 'image'.
//
// uint32_t width:          Texture width.
// uint32_t height:       Texture height.
// const unsigned char *block_storage:  pointer to compressed DXT1 blocks.
// uint32_t *image:       pointer to the image where the
// decompressed pixels will be stored.

static void BlockDecompressImageDXT1(uint32_t width, uint32_t height,
                                     const unsigned char* block_storage,
                                     uint32_t* image) {
  uint32_t block_count_x = (width + 3) / 4;
  uint32_t block_count_y = (height + 3) / 4;
  // uint32_t blockWidth = (width < 4) ? width : 4;
  // uint32_t blockHeight = (height < 4) ? height : 4;

  for (uint32_t j = 0; j < block_count_y; j++) {
    for (uint32_t i = 0; i < block_count_x; i++) {
      DecompressBlockDXT1(i * 4, j * 4, width, height, block_storage + i * 8,
                          image);
    }
    block_storage += block_count_x * 8;
  }
}

// void DecompressBlockDXT5(): Decompresses one block of a DXT5 texture and
// stores the resulting pixels at the appropriate offset in 'image'.
//
// uint32_t x:            x-coordinate of the
// first pixel in the block. uint32_t y: y-coordinate of the first pixel in the
// block. uint32_t width: width of the texture being decompressed. uint32_t
// height: height of the texture being decompressed. const unsigned char
// *block_storage: pointer to the block to decompress. uint32_t *image:
// pointer to image where the decompressed pixel data should be stored.

static void DecompressBlockDXT5(uint32_t x, uint32_t y, uint32_t width,
                                uint32_t height, const uint8_t* block_storage,
                                uint32_t* image) {
  uint8_t alpha0 = *block_storage;
  uint8_t alpha1 = *(block_storage + 1);

  const uint8_t* bits = block_storage + 2;
  uint32_t alpha_code_1 =
      bits[2] | (bits[3] << 8) | (bits[4] << 16) | (bits[5] << 24);
  uint16_t alpha_code_2 = bits[0] | (bits[1] << 8);

  uint16_t color0, color1;
  memcpy(&color0, block_storage + 8, sizeof(color0));
  memcpy(&color1, block_storage + 10, sizeof(color1));

  uint32_t temp;

  temp = (color0 >> 11u) * 255u + 16u;
  auto r0 = (uint8_t)((temp / 32u + temp) / 32u);
  temp = ((color0 & 0x07E0u) >> 5u) * 255u + 32u;
  auto g0 = (uint8_t)((temp / 64u + temp) / 64u);
  temp = (color0 & 0x001Fu) * 255u + 16u;
  auto b0 = (uint8_t)((temp / 32u + temp) / 32u);

  temp = (color1 >> 11u) * 255u + 16u;
  auto r1 = (uint8_t)((temp / 32u + temp) / 32u);
  temp = ((color1 & 0x07E0u) >> 5u) * 255u + 32u;
  auto g1 = (uint8_t)((temp / 64u + temp) / 64u);
  temp = (color1 & 0x001Fu) * 255u + 16u;
  auto b1 = (uint8_t)((temp / 32u + temp) / 32u);

  uint32_t code = *reinterpret_cast<const uint32_t*>(block_storage + 12);

  for (int j = 0; j < 4; j++) {
    for (int i = 0; i < 4; i++) {
      int alpha_code_index = 3 * (4 * j + i);
      int alpha_code;

      if (alpha_code_index <= 12) {
        alpha_code = (alpha_code_2 >> alpha_code_index) & 0x07;
      } else if (alpha_code_index == 15) {
        // NOLINTNEXTLINE
        alpha_code = (alpha_code_2 >> 15) | ((alpha_code_1 << 1) & 0x06);
      } else {
        // NOLINTNEXTLINE
        alpha_code = (alpha_code_1 >> (alpha_code_index - 16)) & 0x07;
      }

      uint8_t final_alpha;
      if (alpha_code == 0) {
        final_alpha = alpha0;
      } else if (alpha_code == 1) {
        final_alpha = alpha1;
      } else {
        if (alpha0 > alpha1) {
          final_alpha = static_cast<uint8_t>(
              ((8 - alpha_code) * alpha0 + (alpha_code - 1) * alpha1) / 7);
        } else {
          if (alpha_code == 6) {
            final_alpha = 0;
          } else if (alpha_code == 7) {
            final_alpha = 255;
          } else {
            final_alpha = static_cast<uint8_t>(
                ((6 - alpha_code) * alpha0 + (alpha_code - 1) * alpha1) / 5);
          }
        }
      }

      auto colorCode = static_cast<uint8_t>((code >> 2 * (4 * j + i)) & 0x03);

      uint32_t final_color = 0;
      switch (colorCode) {
        case 0:
          final_color = PackRGBA(r0, g0, b0, final_alpha);
          break;
        case 1:
          final_color = PackRGBA(r1, g1, b1, final_alpha);
          break;
        case 2:
          final_color =
              PackRGBA(static_cast<uint8_t>((2 * r0 + r1) / 3),
                       static_cast<uint8_t>((2 * g0 + g1) / 3),
                       static_cast<uint8_t>((2 * b0 + b1) / 3), final_alpha);
          break;
        case 3:
          final_color =
              PackRGBA(static_cast<uint8_t>((r0 + 2 * r1) / 3),
                       static_cast<uint8_t>((g0 + 2 * g1) / 3),
                       static_cast<uint8_t>((b0 + 2 * b1) / 3), final_alpha);
          break;
        default:
          break;
      }

      if ((x + i < width) && (y + j < height)) {
        image[(y + j) * width + (x + i)] = final_color;
      }
    }
  }
}

static void BlockDecompressImageDXT5(uint32_t width, uint32_t height,
                                     const uint8_t* block_storage,
                                     uint32_t* image) {
  uint32_t block_count_x = (width + 3) / 4;
  uint32_t block_count_y = (height + 3) / 4;
  for (uint32_t j = 0; j < block_count_y; j++) {
    for (uint32_t i = 0; i < block_count_x; i++)
      DecompressBlockDXT5(i * 4, j * 4, width, height, block_storage + i * 16,
                          image);
    block_storage += block_count_x * 16;
  }
}

void TextureAssetPreloadData::ConvertToUncompressed(TextureAsset* texture) {
  // FIXME; we could technically get better quality on our
  //  lower mip levels by dynamically generating them in this
  //  case instead of decompressing each level.
  for (int i = 0; i < kMaxTextureLevels; i++) {
    // Convert all non-empty texture slots.
    if (formats[i] != TextureFormat::kNone) {
      if (formats[i] == TextureFormat::kDXT1) {
        // Lets go 32 bit for now.
        uint8_t* old_buffer = buffers[i];
        assert(widths[i] >= 0 && heights[i] >= 0);
        size_t b_size = static_cast<size_t>(widths[i])
                        * static_cast<size_t>(heights[i]) * 4u;
        auto* new_buffer = static_cast<uint8_t*>(malloc(b_size));
        assert(new_buffer);
        buffers[i] = new_buffer;
        formats[i] = TextureFormat::kRGBA_8888;
        BlockDecompressImageDXT1(static_cast<uint32_t>(widths[i]),
                                 static_cast<uint32_t>(heights[i]), old_buffer,
                                 reinterpret_cast<uint32_t*>(new_buffer));
        free(reinterpret_cast<char*>(old_buffer));

        // Ok; this gave us RGBA data, but we don't need the A since DXT1 has no
        // alpha..
        rgba8888_to_rgb888_in_place(buffers[i], widths[i] * heights[i] * 4);
        formats[i] = TextureFormat::kRGB_888;
      } else if (formats[i] == TextureFormat::kDXT5) {
        // lets go 32 bit for now
        uint8_t* old_buffer = buffers[i];
        assert(widths[i] >= 0 && heights[i] >= 0);
        size_t b_size = static_cast<size_t>(widths[i])
                        * static_cast<size_t>(heights[i]) * 4u;
        auto* new_buffer = static_cast<uint8_t*>(malloc(b_size));
        assert(new_buffer);
        buffers[i] = new_buffer;
        formats[i] = TextureFormat::kRGBA_8888;
        BlockDecompressImageDXT5(static_cast<uint32_t>(widths[i]),
                                 static_cast<uint32_t>(heights[i]), old_buffer,
                                 reinterpret_cast<uint32_t*>(new_buffer));
        free(reinterpret_cast<char*>(old_buffer));
      } else if (formats[i] == TextureFormat::kETC2_RGBA) {
        // Let's go 32 bit for now.
        uint8_t* old_buffer = buffers[i];
        uint8_t* new_buffer = nullptr;

        if (explicit_bool(true)) {
#if BA_ENABLE_OPENGL
          unsigned int format;
          unsigned int internal_format;
          unsigned int type;
          KTXUnpackETC(old_buffer, GL_COMPRESSED_RGBA8_ETC2_EAC,
                       static_cast<uint32_t>(widths[i]),
                       static_cast<uint32_t>(heights[i]), &new_buffer, &format,
                       &internal_format, &type, 0, false);
#else
          throw Exception();
#endif  // BA_ENABLE_OPENGL
        } else {
          assert(widths[i] >= 0 && heights[i] >= 0);
          size_t b_size = static_cast<size_t>(widths[i])
                          * static_cast<size_t>(heights[i]) * 4u;
          new_buffer = static_cast<uint8_t*>(malloc(b_size));
        }
        BA_PRECONDITION(new_buffer);
        buffers[i] = new_buffer;
        formats[i] = TextureFormat::kRGBA_8888;
        free(reinterpret_cast<char*>(old_buffer));
      } else if (formats[i] == TextureFormat::kETC2_RGB) {
        // lets go 32 bit for now
        uint8_t* old_buffer = buffers[i];
        uint8_t* new_buffer = nullptr;
#if BA_ENABLE_OPENGL
        unsigned int format;
        unsigned int internal_format;
        unsigned int type;
        if (explicit_bool(true)) {
          KTXUnpackETC(old_buffer, GL_COMPRESSED_RGB8_ETC2,
                       static_cast<uint32_t>(widths[i]),
                       static_cast<uint32_t>(heights[i]), &new_buffer, &format,
                       &internal_format, &type, 0, false);
        } else {
          assert(widths[i] >= 0 && heights[i] >= 0);
          size_t b_size = static_cast<size_t>(widths[i])
                          * static_cast<size_t>(heights[i]) * 3u;
          new_buffer = static_cast<uint8_t*>(malloc(b_size));
        }
#else
        throw Exception();
#endif  // BA_ENABLE_OPENGL
        BA_PRECONDITION(new_buffer);
        buffers[i] = new_buffer;
        formats[i] = TextureFormat::kRGB_888;
        free(reinterpret_cast<char*>(old_buffer));
      } else if (formats[i] == TextureFormat::kETC1) {
        // lets go 32 bit for now
        uint8_t* old_buffer = buffers[i];
        uint8_t* new_buffer = nullptr;
#if BA_ENABLE_OPENGL
        unsigned int format;
        unsigned int internal_format;
        unsigned int type;
        if (explicit_bool(true)) {
          KTXUnpackETC(old_buffer, GL_ETC1_RGB8_OES,
                       static_cast<uint32_t>(widths[i]),
                       static_cast<uint32_t>(heights[i]), &new_buffer, &format,
                       &internal_format, &type, 0, false);
        } else {
          assert(widths[i] >= 0 && heights[i] >= 0);
          size_t b_size = static_cast<size_t>(widths[i])
                          * static_cast<size_t>(heights[i]) * 3u;
          new_buffer = static_cast<uint8_t*>(malloc(b_size));
          memset(new_buffer, 128, b_size);
        }
#else
        throw Exception();
#endif
        BA_PRECONDITION(new_buffer);
        buffers[i] = new_buffer;
        formats[i] = TextureFormat::kRGB_888;
        free(reinterpret_cast<char*>(old_buffer));
      } else {
        throw Exception("Can't convert tex format "
                        + std::to_string(static_cast<int>(formats[i]))
                        + " to uncompressed");
      }

      // ok, for RGBA stuff let's go ahead and convert to dithered 4444 instead
      // of 8888 (the exception is cube-maps; we want to keep those as high
      // bitdepth as possible since dithering is quite noticeable in
      // reflections)
      if (formats[i] == TextureFormat::kRGBA_8888
          && texture->texture_type() != TextureType::kCubeMap) {
        assert(widths[i] >= 0 && heights[i] >= 0);
        size_t buffer_size = static_cast<size_t>(widths[i])
                             * static_cast<size_t>(heights[i]) * 4u;
        rgba8888_to_rgba4444_in_place(buffers[i], buffer_size);
        formats[i] = TextureFormat::kRGBA_4444;
      }

      // convert RGB 888 to RGB 565 to get our sizes down a bit
      // (again, make an exception for cube-maps)
      if (formats[i] == TextureFormat::kRGB_888
          && texture->texture_type() != TextureType::kCubeMap) {
        assert(widths[i] >= 0 && heights[i] >= 0);
        size_t buffer_size = static_cast<size_t>(widths[i])
                             * static_cast<size_t>(heights[i]) * 3u;
        rgb888_to_rgb565_in_place(buffers[i], buffer_size);
        formats[i] = TextureFormat::kRGB_565;
      }

      // ok; nowadays for uncompressed stuff we just load the top level
      // and generate the rest on the gpu.  This should give us nicer
      // quality than decompressed lower-level mip images would
      // and is hopefully faster too..
      // HMMM actually the quality argument may be iffy in cases where
      // we're dithering.. (or maybe not?)
      break;
    }
  }
}

TextureAssetPreloadData::~TextureAssetPreloadData() {
  for (auto& buffer : buffers) {
    if (buffer) {
      free(buffer);
    }
  }
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
