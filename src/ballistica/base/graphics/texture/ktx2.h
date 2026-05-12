// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_TEXTURE_KTX2_H_
#define BALLISTICA_BASE_GRAPHICS_TEXTURE_KTX2_H_

#include <cstddef>
#include <cstdint>
#include <string>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// KTX 2.0 magic bytes (12 bytes): ``«KTX 20»\r\n\x1A\n`` — identifier
/// 0xAB / "KTX 20" / 0xBB / CR LF SUB LF.
constexpr unsigned char kKTX2Magic[12] = {0xAB, 0x4B, 0x54, 0x58, 0x20, 0x32,
                                          0x30, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A};

/// KTX 2.0 file header — 68 bytes total following the 12-byte magic.
/// See https://registry.khronos.org/KTX/specs/2.0/ktxspec.v2.html.
///
/// Packed so the two trailing ``uint64_t`` fields don't get the
/// natural 4-byte padding the compiler would otherwise insert after
/// the 13 ``uint32_t`` fields (which sit at file offset 52, not
/// 8-aligned). All our targets (x86_64, ARM64) handle unaligned
/// loads transparently. ``#pragma pack`` is the portable form —
/// clang/gcc honor it identically to ``__attribute__((packed))``
/// and MSVC requires it.
#pragma pack(push, 1)
struct KTX2Header {
  uint32_t vk_format;
  uint32_t type_size;
  uint32_t pixel_width;
  uint32_t pixel_height;
  uint32_t pixel_depth;
  uint32_t layer_count;
  uint32_t face_count;
  uint32_t level_count;
  uint32_t supercompression_scheme;
  uint32_t dfd_byte_offset;
  uint32_t dfd_byte_length;
  uint32_t kvd_byte_offset;
  uint32_t kvd_byte_length;
  uint64_t sgd_byte_offset;
  uint64_t sgd_byte_length;
};
static_assert(sizeof(KTX2Header) == 68,
              "KTX2Header must be tightly 68 bytes per spec");

/// Per-level entry in the KTX 2.0 level index — 24 bytes each, one
/// entry per mip level in mip-major order (entry 0 = largest mip).
struct KTX2LevelIndex {
  uint64_t byte_offset;
  uint64_t byte_length;
  uint64_t uncompressed_byte_length;
};
static_assert(sizeof(KTX2LevelIndex) == 24,
              "KTX2LevelIndex must be tightly 24 bytes per spec");
#pragma pack(pop)

/// Load a KTX 2.0 file into the engine's mip-buffer representation.
/// Matches the signature shape of :func:`LoadDDS` / :func:`LoadKTX` so
/// callers in ``texture_asset.cc`` can dispatch uniformly.
///
/// ``buffers[i]`` is malloc'd for ``i >= *base_level``; entries below
/// ``*base_level`` are left ``nullptr`` (skipped for quality
/// dropdowns). ``widths`` / ``heights`` / ``formats`` / ``sizes`` are
/// populated for every level. ``*base_level`` indicates the starting
/// (largest) mip level the caller should sample from.
///
/// Throws on parse error, unsupported ``vkFormat``, or
/// non-zero ``supercompressionScheme`` (BasisU/zstd not implemented
/// for v1 — see initiative decision #12).
void LoadKTX2(const std::string& file_name, unsigned char** buffers,
              int* widths, int* heights, TextureFormat* formats, size_t* sizes,
              TextureQuality texture_quality, int min_quality, int* base_level);

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_TEXTURE_KTX2_H_
