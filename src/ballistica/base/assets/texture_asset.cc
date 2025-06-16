// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/texture_asset.h"

#include <algorithm>
#include <cstdio>
#include <list>
#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset_preload_data.h"
#include "ballistica/base/assets/texture_asset_renderer_data.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/graphics/text/text_packer.h"
#include "ballistica/base/graphics/texture/dds.h"
#include "ballistica/base/graphics/texture/ktx.h"
#include "ballistica/base/graphics/texture/pvr.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "external/qr_code_generator/QrCode.hpp"

namespace ballistica::base {

static void Rgba8888UnpremultiplyInPlace_(uint8_t* src, size_t cb) {
  // Compute the actual number of pixel elements in the buffer.
  size_t cpel = cb / 4;
  auto* psrc = src;
  auto* pdst = src;
  for (size_t i = 0; i < cpel; i++) {
    int r = *psrc++;
    int g = *psrc++;
    int b = *psrc++;
    int a = *psrc++;
    if (a == 0) {
      *pdst++ = 255;
      *pdst++ = 255;
      *pdst++ = 255;
      *pdst++ = 0;
    } else {
      *pdst++ = static_cast_check_fit<uint8_t>(std::min(255, r * 255 / a));
      *pdst++ = static_cast_check_fit<uint8_t>(std::min(255, g * 255 / a));
      *pdst++ = static_cast_check_fit<uint8_t>(std::min(255, b * 255 / a));
      *pdst++ = static_cast_check_fit<uint8_t>(a);
    }
  }
}

TextureAsset::TextureAsset() = default;

TextureAsset::TextureAsset(const std::string& file_in, TextureType type_in,
                           TextureMinQuality min_quality_in)
    : file_name_(file_in), type_(type_in), min_quality_(min_quality_in) {
  file_name_full_ =
      g_base->assets->FindAssetFile(Assets::FileType::kTexture, file_in);
  valid_ = true;
}

auto TextureAsset::GetAssetType() const -> AssetType {
  return AssetType::kTexture;
}

TextureAsset::TextureAsset(TextPacker* packer) : packer_(packer) {
  file_name_ = packer->hash();
  valid_ = true;
}

TextureAsset::TextureAsset(const std::string& qr_url) : is_qr_code_(true) {
  size_t hard_limit{96};
  size_t soft_limit{64};
  if (qr_url.size() > hard_limit) {
    char buffer[512];
    snprintf(buffer, sizeof(buffer),
             "QR code url byte length %zu exceeds hard-limit of %zu;"
             " please use shorter urls. (url=%s)",
             qr_url.size(), hard_limit, qr_url.c_str());
    throw Exception(buffer, PyExcType::kValue);
  } else if (qr_url.size() > soft_limit) {
    char buffer[512];
    snprintf(buffer, sizeof(buffer),
             "QR code url byte length %zu exceeds soft-limit of %zu;"
             " please use shorter urls. (url=%s)",
             qr_url.size(), soft_limit, qr_url.c_str());
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning, buffer);
  }
  file_name_ = qr_url;
  valid_ = true;
}

TextureAsset::~TextureAsset() {}

auto TextureAsset::GetName() const -> std::string {
  return (!file_name_.empty()) ? file_name_ : "invalid texture";
}

auto TextureAsset::GetNameFull() const -> std::string {
  return file_name_full();
}

void TextureAsset::DoPreload() {
  assert(valid_);

  // Make sure we're not loading without knowing what texture types we
  // support.
  // assert(g_base->graphics->has_client_context());
  // assert(g_base->graphics_server
  //        && g_base->graphics_server->texture_compression_types_are_set());

  // Figure out which LOD should be our base level based on texture quality.
  auto texture_quality = g_base->graphics->placeholder_texture_quality();

  // If we're a text-texture.
  if (packer_.exists()) {
    assert(type_ == TextureType::k2D);

    int width = packer_->texture_width();
    int height = packer_->texture_height();
    float quality_scale = 1.0f;

    if (texture_quality == TextureQuality::kMedium) {
      width /= 2;
      height /= 2;
      quality_scale *= 0.5f;
    } else if (texture_quality == TextureQuality::kLow) {
      width /= 4;
      height /= 4;
      quality_scale *= 0.25f;
    }
    float scale = packer_->text_scale() * quality_scale;

    std::vector<std::string> strings;
    std::vector<float> positions;
    std::vector<float> visible_widths;

    int index = 0;
    const std::list<TextPacker::Span>& spans = packer_->spans();
    for (const auto& span : spans) {
      strings.push_back(span.string);
      positions.push_back(span.tex_x * quality_scale);
      positions.push_back(span.tex_y * quality_scale);
      visible_widths.push_back((span.bounds.r - span.bounds.l));
      index++;
    }

    assert(!strings.empty());
    assert(strings.size() * 2 == positions.size());

    void* tex_ref{g_core->platform->CreateTextTexture(
        width, height, strings, positions, visible_widths, scale)};
    uint8_t* pixels{g_core->platform->GetTextTextureData(tex_ref)};

    assert(pixels);
    assert(tex_ref);

    // For now just copy it over to our local 32 bit buffer.
    // As an optimization we could convert it to RGBA4444 on the fly or perhaps
    // even just alpha if there's no non-white colors present.
    // NOTE: This data is also coming in premultiplied (on apple at least) so we
    // need to take care of that.
    preload_datas_.resize(1);
    assert(width >= 0 && height >= 0);
    size_t buffer_size =
        static_cast<size_t>(width) * static_cast<size_t>(height) * 4u;
    auto* buffer = static_cast<uint8_t*>(malloc(buffer_size));
    preload_datas_[0].buffers[0] = buffer;
    memcpy(buffer, pixels, buffer_size);
    Rgba8888UnpremultiplyInPlace_(buffer, buffer_size);
    preload_datas_[0].widths[0] = width;
    preload_datas_[0].heights[0] = height;
    preload_datas_[0].formats[0] = TextureFormat::kRGBA_8888;
    preload_datas_[0].base_level = 0;

    g_core->platform->FreeTextTexture(tex_ref);

    // Downsample this down to rgba4444 in-place.
    TextureAssetPreloadData::rgba8888_to_rgba4444_in_place(buffer, buffer_size);
    preload_datas_[0].formats[0] = TextureFormat::kRGBA_4444;

  } else if (is_qr_code_) {
    const qrcodegen::QrCode qr2{qrcodegen::QrCode::encodeText(
        file_name_.c_str(), qrcodegen::QrCode::Ecc::HIGH)};
    int qr_size = qr2.getSize();

    int width = 512;
    int height = 512;
    preload_datas_.resize(1);
    assert(width >= 0 && height >= 0);
    size_t buffer_size =
        static_cast<size_t>(width) * static_cast<size_t>(height) * 2u;
    auto* buffer = static_cast<uint16_t*>(malloc(buffer_size));
    for (int y = 0; y < height; y++) {
      for (int x = 0; x < width; x++) {
        float xf = static_cast<float>(x) / static_cast<float>(width);
        float yf = static_cast<float>(y) / static_cast<float>(height);
        uint16_t* dst = buffer + width * y + x;
        int x2 = static_cast<int>(
            floor((xf - 0.05f) * (static_cast<float>(qr_size) * 1.1f)));
        int y2 = static_cast<int>(
            floor((yf - 0.05f) * (static_cast<float>(qr_size) * 1.1f)));
        if (x2 >= 0 && x2 < qr_size && y2 >= 0 && y2 < qr_size
            && qr2.getModule(x2, y2)) {
          *dst = 0;
        } else {
          *dst = 0xffff;
        }
      }
    }
    preload_datas_[0].buffers[0] = reinterpret_cast<uint8_t*>(buffer);
    preload_datas_[0].widths[0] = width;
    preload_datas_[0].heights[0] = height;
    preload_datas_[0].formats[0] = TextureFormat::kRGB_565;
    preload_datas_[0].base_level = 0;
  } else {
    if (type_ == TextureType::k2D) {
      preload_datas_.resize(1);

      int file_name_size = static_cast<int>(file_name_full_.size());
      BA_PRECONDITION(file_name_size > 4);

      // Etc1 or dxt3 for non-alpha and dxt5 for alpha (.android_dds files).
      if (file_name_size > 12
          && !strcmp(file_name_full_.c_str() + file_name_size - 12,
                     ".android_dds")) {
        LoadDDS(file_name_full_, preload_datas_[0].buffers,
                preload_datas_[0].widths, preload_datas_[0].heights,
                preload_datas_[0].formats, preload_datas_[0].sizes,
                texture_quality, static_cast<uint8_t>(min_quality_),
                &preload_datas_[0].base_level);

        // We should only be loading this if we support etc1 in hardware.
        assert(g_base->graphics->placeholder_client_context()
                   ->SupportsTextureCompressionType(
                       TextureCompressionType::kETC1));

        // Decompress dxt1/dxt5 ones if we don't natively support S3TC.
        if (!g_base->graphics->placeholder_client_context()
                 ->SupportsTextureCompressionType(
                     TextureCompressionType::kS3TC)) {
          if ((preload_datas_[0].formats[preload_datas_[0].base_level]
               == TextureFormat::kDXT5)
              || (preload_datas_[0].formats[preload_datas_[0].base_level]
                  == TextureFormat::kDXT1)) {
            preload_datas_[0].ConvertToUncompressed(this);
          }
        }
      } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                         ".dds")) {
        // Dxt1 for non-alpha and dxt5 for alpha (.dds files).
        LoadDDS(file_name_full_, preload_datas_[0].buffers,
                preload_datas_[0].widths, preload_datas_[0].heights,
                preload_datas_[0].formats, preload_datas_[0].sizes,
                texture_quality, static_cast<int>(min_quality_),
                &preload_datas_[0].base_level);

        // Decompress dxt1/dxt5 if we don't natively support it.
        if (!g_base->graphics->placeholder_client_context()
                 ->SupportsTextureCompressionType(
                     TextureCompressionType::kS3TC)) {
          preload_datas_[0].ConvertToUncompressed(this);
        }
      } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                         ".ktx")) {
        // Etc2 or etc1 for non-alpha and etc2 for alpha (.ktx files).
        try {
          LoadKTX(file_name_full_, preload_datas_[0].buffers,
                  preload_datas_[0].widths, preload_datas_[0].heights,
                  preload_datas_[0].formats, preload_datas_[0].sizes,
                  texture_quality, static_cast<uint8_t>(min_quality_),
                  &preload_datas_[0].base_level);
        } catch (const std::exception& e) {
          throw Exception("Error loading file '" + file_name_full_
                          + "': " + e.what());
        }

        // Decompress etc2 if we don't natively support it.
        if (((preload_datas_[0].formats[preload_datas_[0].base_level]
              == TextureFormat::kETC2_RGB)
             || (preload_datas_[0].formats[preload_datas_[0].base_level]
                 == TextureFormat::kETC2_RGBA))
            && (!g_base->graphics->placeholder_client_context()
                     ->SupportsTextureCompressionType(
                         TextureCompressionType::kETC2))) {
          preload_datas_[0].ConvertToUncompressed(this);
        }

        // Decompress etc1 if we don't natively support it.
        if ((preload_datas_[0].formats[preload_datas_[0].base_level]
             == TextureFormat::kETC1)
            && (!g_base->graphics->placeholder_client_context()
                     ->SupportsTextureCompressionType(
                         TextureCompressionType::kETC1))) {
          preload_datas_[0].ConvertToUncompressed(this);
        }

      } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                         ".pvr")) {
        // Pvr for all (.pvr files).
        LoadPVR(file_name_full_, preload_datas_[0].buffers,
                preload_datas_[0].widths, preload_datas_[0].heights,
                preload_datas_[0].formats, preload_datas_[0].sizes,
                texture_quality, static_cast<uint8_t>(min_quality_),
                &preload_datas_[0].base_level);

        // We should only be loading this if we support pvr in hardware.
        assert(
            g_base->graphics->placeholder_client_context()
                ->SupportsTextureCompressionType(TextureCompressionType::kPVR));
      } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                         ".nop")) {
        // Dummy path for headless; nothing to do here.
      } else {
        throw Exception("Invalid texture file name: '" + file_name_full_ + "'");
      }

    } else if (type_ == TextureType::kCubeMap) {
      preload_datas_.resize(6);
      std::string name;
      int file_name_size = static_cast<int>(file_name_full_.size());
      BA_PRECONDITION(file_name_size > 4);
      for (int d = 0; d < 6; d++) {
        name = file_name_full_;
        switch (d) {
          case 0:
            name.replace(name.find('#'), 1, "_+x");
            break;
          case 1:
            name.replace(name.find('#'), 1, "_-x");
            break;
          case 2:
            name.replace(name.find('#'), 1, "_+y");
            break;
          case 3:
            name.replace(name.find('#'), 1, "_-y");
            break;
          case 4:
            name.replace(name.find('#'), 1, "_+z");
            break;
          case 5:
            name.replace(name.find('#'), 1, "_-z");
            break;
          default:
            throw Exception();
        }

        // Etc1 or dxt3 for non-alpha and dxt5 for alpha (.android_dds files).
        if (file_name_size > 12
            && !strcmp(file_name_full_.c_str() + file_name_size - 12,
                       ".android_dds")) {
          try {
            LoadDDS(name, preload_datas_[d].buffers, preload_datas_[d].widths,
                    preload_datas_[d].heights, preload_datas_[d].formats,
                    preload_datas_[d].sizes, texture_quality,
                    static_cast<uint8_t>(min_quality_),
                    &preload_datas_[d].base_level);
          } catch (const std::exception& e) {
            throw Exception("Error loading file '" + file_name_full_
                            + "': " + e.what());
          }

          // We should only be loading this if we support etc1 in hardware.
          assert(g_base->graphics->placeholder_client_context()
                     ->SupportsTextureCompressionType(
                         TextureCompressionType::kETC1));

          // Decompress dxt1/dxt5 ones if we don't natively support S3TC.
          if (!g_base->graphics->placeholder_client_context()
                   ->SupportsTextureCompressionType(
                       TextureCompressionType::kS3TC)) {
            if ((preload_datas_[d].formats[preload_datas_[d].base_level]
                 == TextureFormat::kDXT5)
                || (preload_datas_[d].formats[preload_datas_[d].base_level]
                    == TextureFormat::kDXT1)) {
              preload_datas_[d].ConvertToUncompressed(this);
            }
          }
        } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                           ".dds")) {
          // Dxt1 for non-alpha and dxt5 for alpha (.dds files).
          LoadDDS(name, preload_datas_[d].buffers, preload_datas_[d].widths,
                  preload_datas_[d].heights, preload_datas_[d].formats,
                  preload_datas_[d].sizes, texture_quality,
                  static_cast<uint8_t>(min_quality_),
                  &preload_datas_[d].base_level);

          // Decompress dxt1/dxt5 if we don't natively support it.
          if (!g_base->graphics->placeholder_client_context()
                   ->SupportsTextureCompressionType(
                       TextureCompressionType::kS3TC)) {
            preload_datas_[d].ConvertToUncompressed(this);
          }
        } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                           ".ktx")) {
          // Etc2 or etc1 for non-alpha and etc2 for alpha (.ktx files)
          LoadKTX(name, preload_datas_[d].buffers, preload_datas_[d].widths,
                  preload_datas_[d].heights, preload_datas_[d].formats,
                  preload_datas_[d].sizes, texture_quality,
                  static_cast<uint8_t>(min_quality_),
                  &preload_datas_[d].base_level);

          // Decompress etc2 ones if we don't natively support them.
          if (((preload_datas_[d].formats[preload_datas_[d].base_level]
                == TextureFormat::kETC2_RGB)
               || (preload_datas_[d].formats[preload_datas_[d].base_level]
                   == TextureFormat::kETC2_RGBA))
              && (!g_base->graphics->placeholder_client_context()
                       ->SupportsTextureCompressionType(
                           TextureCompressionType::kETC2))) {
            preload_datas_[d].ConvertToUncompressed(this);
          }

          // Decompress etc1 if we don't natively support it.
          if ((preload_datas_[d].formats[preload_datas_[d].base_level]
               == TextureFormat::kETC1)
              && (!g_base->graphics->placeholder_client_context()
                       ->SupportsTextureCompressionType(
                           TextureCompressionType::kETC1))) {
            preload_datas_[d].ConvertToUncompressed(this);
          }

        } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                           ".pvr")) {
          // Pvr for both non-alpha and alpha (.pvr files).
          try {
            LoadPVR(name, preload_datas_[d].buffers, preload_datas_[d].widths,
                    preload_datas_[d].heights, preload_datas_[d].formats,
                    preload_datas_[d].sizes, texture_quality,
                    static_cast<uint8_t>(min_quality_),
                    &preload_datas_[d].base_level);
          } catch (const std::exception& e) {
            throw Exception("Error loading file '" + file_name_full_
                            + "': " + e.what());
          }
        } else if (!strcmp(file_name_full_.c_str() + file_name_size - 4,
                           ".nop")) {
          // Dummy path for headless; nothing to do here.
        } else {
          throw Exception("Invalid texture file name: '" + file_name_full_
                          + "'");
        }
      }
    } else {
      throw Exception("unknown texture type");
    }
  }
}

void TextureAsset::DoLoad() {
  assert(g_base->app_adapter->InGraphicsContext());
  assert(!renderer_data_.exists());
  renderer_data_ = g_base->graphics_server->renderer()->NewTextureData(*this);
  assert(renderer_data_.exists());
  renderer_data_->Load();

  // Store our base-level from the preload-data so we know if we're lower than
  // full quality.
  assert(!preload_datas_.empty());
  base_level_ = preload_datas_[0].base_level;

  // If we're done, kill our preload data.
  preload_datas_.clear();
}

void TextureAsset::DoUnload() {
  assert(g_base->app_adapter->InGraphicsContext());
  assert(valid_);
  assert(renderer_data_.exists());
  renderer_data_.Clear();
  base_level_ = 0;
}

}  // namespace ballistica::base
