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
static constexpr uint32_t kVkFormatBC7SRGBBlock = 146;        // DESKTOP_V1
static constexpr uint32_t kVkFormatASTC4x4SRGBBlock = 158;    // MOBILE_V1
static constexpr uint32_t kVkFormatASTC5x5SRGBBlock = 162;    // MOBILE_V1
static constexpr uint32_t kVkFormatASTC6x6SRGBBlock = 166;    // MOBILE_V1
static constexpr uint32_t kVkFormatASTC8x8SRGBBlock = 172;    // MOBILE_V1
static constexpr uint32_t kVkFormatASTC10x10SRGBBlock = 180;  // MOBILE_V1
static constexpr uint32_t kVkFormatASTC12x12SRGBBlock = 184;  // MOBILE_V1

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
    case kVkFormatASTC5x5SRGBBlock:
      return TextureFormat::kASTC_5x5;
    case kVkFormatASTC10x10SRGBBlock:
      return TextureFormat::kASTC_10x10;
    case kVkFormatASTC12x12SRGBBlock:
      return TextureFormat::kASTC_12x12;
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

// Key/value keys carrying our per-axis wrapping (written by
// ``_kvd_section`` in bamaster assetsv1tex.py). ``KTX``/``ktx`` is
// reserved by the spec for its own keys, so ours take a ``ba`` prefix.
// Wire values -- never rename.
static const char* kKvdKeyWrapH = "baTextureWrappingH";
static const char* kKvdKeyWrapV = "baTextureWrappingV";

// Map a wrapping wire string to its enum. Unknown values (a newer
// pipeline emitting a mode this build predates) fall back to clamp,
// which is the safe default: it can only ever look wrong on a texture
// that was meant to tile, never break one that wasn't.
static auto WrappingFromString(const char* val) -> TextureWrapping {
  if (!strcmp(val, "repeat")) {
    return TextureWrapping::kRepeat;
  }
  if (!strcmp(val, "mirrored_repeat")) {
    return TextureWrapping::kMirroredRepeat;
  }
  return TextureWrapping::kClamp;
}

// Read our wrapping keys out of a KTX2 key/value data section.
//
// Layout per entry (spec 3.11): uint32 keyAndValueByteLength, then a
// NUL-terminated UTF-8 key followed by the value, then zero padding to
// the next 4-byte boundary. We only emit KVD for non-clamp wrapping, so
// the overwhelmingly common case is kvd_byte_length == 0 and this is a
// no-op. Anything malformed leaves the defaults rather than throwing --
// wrapping is a rendering nicety, not worth failing a texture load over.
static void ReadWrappingFromKVD(FILE* f, const KTX2Header& hdr,
                                TextureWrapping* wrap_h,
                                TextureWrapping* wrap_v) {
  // Sanity-bound the section so a corrupt header can't make us allocate
  // wildly. Our own sections are a few dozen bytes.
  const uint32_t kMaxKVDBytes = 64 * 1024;
  if (hdr.kvd_byte_offset == 0 || hdr.kvd_byte_length == 0
      || hdr.kvd_byte_length > kMaxKVDBytes) {
    return;
  }
  // fseek takes a long by definition; same cast the DFD read above uses.
  auto kvd_offset = static_cast<long>(hdr.kvd_byte_offset);  // NOLINT
  if (fseek(f, kvd_offset, SEEK_SET) != 0) {
    return;
  }
  std::vector<uint8_t> kvd(hdr.kvd_byte_length);
  if (fread(kvd.data(), 1, kvd.size(), f) != kvd.size()) {
    return;
  }

  size_t pos{};
  while (pos + 4 <= kvd.size()) {
    uint32_t entry_len{};
    memcpy(&entry_len, kvd.data() + pos, sizeof(entry_len));
    pos += 4;
    if (entry_len == 0 || pos + entry_len > kvd.size()) {
      return;  // Malformed; keep whatever we have.
    }
    // The entry must be a NUL-terminated key followed by a
    // NUL-terminated value for us to read it as strings.
    const char* key = reinterpret_cast<const char*>(kvd.data() + pos);
    size_t keylen = strnlen(key, entry_len);
    if (keylen + 1 < entry_len) {
      const char* val = key + keylen + 1;
      size_t vallen = strnlen(val, entry_len - keylen - 1);
      if (vallen + keylen + 1 < entry_len) {  // value is NUL-terminated
        if (!strcmp(key, kKvdKeyWrapH)) {
          *wrap_h = WrappingFromString(val);
        } else if (!strcmp(key, kKvdKeyWrapV)) {
          *wrap_v = WrappingFromString(val);
        }
      }
    }
    pos += entry_len;
    pos += (4 - (entry_len % 4)) % 4;  // padding to 4-byte alignment
  }
}

// Shared loader core for 2D (1 face) and cube-map (6 face) KTX2 files.
// ``targets`` must hold ``expected_face_count`` entries; each face gets
// the full mip chain. Within a level, faces are tightly packed
// equal-size slices in spec face order (+X,-X,+Y,-Y,+Z,-Z).
static void LoadKTX2Impl(const std::string& file_name,
                         uint32_t expected_face_count,
                         KTX2FaceTarget* targets) {
  // Asset-package textures always load every mip in the chosen flavor;
  // the legacy texture-quality mip-skip knob does not apply here (see
  // the header and initiative §7 texture-quality decoupling).
  bool premultiplied{};
  TextureWrapping wrap_h{TextureWrapping::kClamp};
  TextureWrapping wrap_v{TextureWrapping::kClamp};
  for (uint32_t fi = 0; fi < expected_face_count; ++fi) {
    *targets[fi].base_level = 0;
    *targets[fi].premultiplied = false;
    *targets[fi].wrap_h = TextureWrapping::kClamp;
    *targets[fi].wrap_v = TextureWrapping::kClamp;
  }

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

  // 2D + cube-map only. layerCount > 0 = array texture; pixelDepth > 0
  // = 3D — those would need additional ``TextureType`` enum values and
  // separate code paths; not in scope. A face-count mismatch (2D file
  // through the cube path or vice versa) is a recipe/loader bug.
  if (hdr.face_count != expected_face_count || hdr.layer_count != 0
      || hdr.pixel_depth != 0) {
    fclose(f);
    throw Exception("KTX2 layout unsupported (faceCount="
                    + std::to_string(hdr.face_count) + " expected "
                    + std::to_string(expected_face_count)
                    + "; arrays/3D unsupported): \"" + file_name + "\".");
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
  // DFD just leaves premultiplied false (straight).
  if (hdr.dfd_byte_offset != 0 && hdr.dfd_byte_length >= 16) {
    if (fseek(f, static_cast<long>(hdr.dfd_byte_offset) + 12,  // NOLINT
              SEEK_SET)
        == 0) {
      uint32_t dfd_word2{};
      if (fread(&dfd_word2, sizeof(dfd_word2), 1, f) == 1) {
        premultiplied = ((dfd_word2 >> 24u) & 1u) != 0u;
      }
    }
  }
  // Per-axis wrapping from the key/value data. Absent (the common case
  // -- we only emit KVD for non-clamp wrapping) leaves both clamped.
  ReadWrappingFromKVD(f, hdr, &wrap_h, &wrap_v);

  for (uint32_t fi = 0; fi < expected_face_count; ++fi) {
    *targets[fi].premultiplied = premultiplied;
    *targets[fi].wrap_h = wrap_h;
    *targets[fi].wrap_v = wrap_v;
  }

  // No quality-driven base_level bump: asset-package textures load all
  // mips present in the chosen flavor (regular/high is a flavor baked
  // into the bytes, not a load-time mip dropdown).

  // Walk levels 0..N-1 (mip-major, level 0 = largest). For each
  // level: compute width/height by halving, then allocate + read each
  // face's equal-size slice of the level data.
  int mip_count = static_cast<int>(hdr.level_count);
  auto x = static_cast<unsigned int>(hdr.pixel_width);
  auto y = static_cast<unsigned int>(hdr.pixel_height);
  for (int ix = 0; ix < mip_count; ++ix) {
    auto byte_length = static_cast<size_t>(level_index[ix].byte_length);

    if (byte_length % expected_face_count != 0) {
      fclose(f);
      throw Exception("KTX2 mip " + std::to_string(ix) + " byte length "
                      + std::to_string(byte_length) + " not divisible by "
                      + std::to_string(expected_face_count) + " faces: \""
                      + file_name + "\".");
    }
    size_t face_bytes = byte_length / expected_face_count;

    // Cross-check the on-disk byte_length against what we expect from
    // the format + dimensions. Catches malformed files / mismatched
    // recipes early rather than surfacing as garbage texel data.
    if (bpp != 0) {
      size_t expected = static_cast<size_t>(x) * static_cast<size_t>(y) * bpp;
      if (expected != face_bytes) {
        fclose(f);
        throw Exception("KTX2 mip " + std::to_string(ix)
                        + " per-face byte length " + std::to_string(face_bytes)
                        + " != expected " + std::to_string(expected) + " for "
                        + std::to_string(x) + "x" + std::to_string(y) + ": \""
                        + file_name + "\".");
      }
    }

    for (uint32_t fi = 0; fi < expected_face_count; ++fi) {
      auto&& target = targets[fi];
      target.widths[ix] = static_cast<int>(x);
      target.heights[ix] = static_cast<int>(y);
      target.formats[ix] = fmt;
      target.sizes[ix] = face_bytes;

      // fseek + fread for each face slice — level offsets aren't
      // guaranteed to be in file order (spec recommends
      // smallest-mip-first layout), so we can't stream sequentially.
      target.buffers[ix] = static_cast<unsigned char*>(malloc(face_bytes));
      if (target.buffers[ix] == nullptr) {
        fclose(f);
        throw Exception("malloc failed for KTX2 mip " + std::to_string(ix)
                        + " (" + std::to_string(face_bytes) + " bytes): \""
                        + file_name + "\".");
      }
      auto offset = static_cast<long>(level_index[ix].byte_offset  // NOLINT
                                      + static_cast<uint64_t>(fi) * face_bytes);
      if (fseek(f, offset, SEEK_SET) != 0) {
        free(target.buffers[ix]);
        target.buffers[ix] = nullptr;
        fclose(f);
        throw Exception("fseek failed on KTX2 mip " + std::to_string(ix)
                        + ": \"" + file_name + "\".");
      }
      if (fread(target.buffers[ix], face_bytes, 1, f) != 1) {
        free(target.buffers[ix]);
        target.buffers[ix] = nullptr;
        fclose(f);
        throw Exception("Short read on KTX2 mip " + std::to_string(ix) + ": \""
                        + file_name + "\".");
      }
    }

    x = std::max(1u, x >> 1u);
    y = std::max(1u, y >> 1u);
  }

  fclose(f);
}

void LoadKTX2(const std::string& file_name, unsigned char** buffers,
              int* widths, int* heights, TextureFormat* formats, size_t* sizes,
              int* base_level, bool* premultiplied, TextureWrapping* wrap_h,
              TextureWrapping* wrap_v) {
  KTX2FaceTarget target{buffers,    widths,        heights, formats, sizes,
                        base_level, premultiplied, wrap_h,  wrap_v};
  LoadKTX2Impl(file_name, 1, &target);
}

void LoadKTX2CubeMap(const std::string& file_name, KTX2FaceTarget* faces) {
  LoadKTX2Impl(file_name, 6, faces);
}

}  // namespace ballistica::base
