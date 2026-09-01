// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_archive.h"

#include <cstring>
#include <memory>
#include <string>
#include <utility>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::base {

// Zip format constants (all little-endian; matches every platform we
// ship on, same assumption our asset formats already make).
static constexpr uint32_t kEOCDSignature = 0x06054b50;
static constexpr uint32_t kCentralSignature = 0x02014b50;
static constexpr uint32_t kLocalSignature = 0x04034b50;
static constexpr size_t kEOCDBaseSize = 22;
// EOCD must live in the last (comment-max + base) bytes.
static constexpr size_t kEOCDMaxScan = 65535 + kEOCDBaseSize;

// Bounds-checked little-endian field reads out of the mapping.
static auto ReadU16(const uint8_t* base, size_t size, size_t offset,
                    uint16_t* out) -> bool {
  if (offset + 2 > size) {
    return false;
  }
  memcpy(out, base + offset, 2);
  return true;
}
static auto ReadU32(const uint8_t* base, size_t size, size_t offset,
                    uint32_t* out) -> bool {
  if (offset + 4 > size) {
    return false;
  }
  memcpy(out, base + offset, 4);
  return true;
}

AssetArchive::~AssetArchive() {
  if (map_base_) {
    g_core->platform->UnmapFile(map_base_, map_size_);
  }
}

auto AssetArchive::Open(const std::string& path)
    -> std::unique_ptr<AssetArchive> {
  auto fail = [&path](const std::string& msg) -> std::unique_ptr<AssetArchive> {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "AssetArchive: " + msg + " ('" + path + "').");
    return nullptr;
  };

  size_t map_size{};
  const void* map_base_raw = g_core->platform->MapFileReadOnly(path, &map_size);
  if (!map_base_raw) {
    return fail("unable to map archive");
  }
  // Own the mapping from here on so error paths release it.
  auto archive = std::unique_ptr<AssetArchive>(new AssetArchive());
  archive->path_ = path;
  archive->map_base_ = static_cast<const uint8_t*>(map_base_raw);
  archive->map_size_ = map_size;
  const uint8_t* base = archive->map_base_;

  // Find the end-of-central-directory record: scan back from the end
  // for its signature (bounded by the max comment length).
  if (map_size < kEOCDBaseSize) {
    return fail("archive too small");
  }
  size_t scan_floor =
      map_size > kEOCDMaxScan ? map_size - kEOCDMaxScan : size_t{0};
  size_t eocd = 0;
  bool found = false;
  for (size_t pos = map_size - kEOCDBaseSize + 1; pos-- > scan_floor;) {
    uint32_t sig{};
    if (ReadU32(base, map_size, pos, &sig) && sig == kEOCDSignature) {
      eocd = pos;
      found = true;
      break;
    }
  }
  if (!found) {
    return fail("no end-of-central-directory record");
  }

  uint16_t entry_count{};
  uint32_t cd_size{};
  uint32_t cd_offset{};
  if (!ReadU16(base, map_size, eocd + 10, &entry_count)
      || !ReadU32(base, map_size, eocd + 12, &cd_size)
      || !ReadU32(base, map_size, eocd + 16, &cd_offset)) {
    return fail("truncated end-of-central-directory record");
  }
  // Zip64 sentinel values; apks stay far under these limits, so
  // treat hitting one as a build problem to surface, not to support.
  if (entry_count == 0xFFFF || cd_size == 0xFFFFFFFF
      || cd_offset == 0xFFFFFFFF) {
    return fail("zip64 archive not supported");
  }

  // Walk the central directory.
  size_t pos = cd_offset;
  archive->entries_.reserve(entry_count);
  for (uint16_t i = 0; i < entry_count; ++i) {
    uint32_t sig{};
    uint16_t method{};
    uint32_t comp_size{};
    uint32_t uncomp_size{};
    uint16_t name_len{};
    uint16_t extra_len{};
    uint16_t comment_len{};
    uint32_t local_offset{};
    if (!ReadU32(base, map_size, pos, &sig) || sig != kCentralSignature
        || !ReadU16(base, map_size, pos + 10, &method)
        || !ReadU32(base, map_size, pos + 20, &comp_size)
        || !ReadU32(base, map_size, pos + 24, &uncomp_size)
        || !ReadU16(base, map_size, pos + 28, &name_len)
        || !ReadU16(base, map_size, pos + 30, &extra_len)
        || !ReadU16(base, map_size, pos + 32, &comment_len)
        || !ReadU32(base, map_size, pos + 42, &local_offset)) {
      return fail("malformed central-directory entry");
    }
    if (pos + 46 + name_len > map_size) {
      return fail("truncated central-directory entry name");
    }
    std::string name(reinterpret_cast<const char*>(base + pos + 46), name_len);

    // Data offset requires the *local* header's name/extra lengths
    // (its extra field can differ from the central one).
    uint32_t local_sig{};
    uint16_t local_name_len{};
    uint16_t local_extra_len{};
    if (!ReadU32(base, map_size, local_offset, &local_sig)
        || local_sig != kLocalSignature
        || !ReadU16(base, map_size, local_offset + 26, &local_name_len)
        || !ReadU16(base, map_size, local_offset + 28, &local_extra_len)) {
      return fail("malformed local header for '" + name + "'");
    }
    size_t data_offset = static_cast<size_t>(local_offset) + 30 + local_name_len
                         + local_extra_len;
    // Stored entries must fit fully in the mapping to be servable.
    bool stored = (method == 0);
    if (stored
        && (data_offset > map_size || comp_size > map_size - data_offset
            || comp_size != uncomp_size)) {
      return fail("stored entry out of bounds: '" + name + "'");
    }
    archive->entries_[std::move(name)] =
        Entry_{data_offset, static_cast<size_t>(comp_size), stored};

    pos += 46 + static_cast<size_t>(name_len) + extra_len + comment_len;
  }
  return archive;
}

auto AssetArchive::Get(const std::string& entry_name) const
    -> std::pair<const uint8_t*, size_t> {
  auto entry = entries_.find(entry_name);
  if (entry == entries_.end() || !entry->second.stored) {
    return {nullptr, 0};
  }
  return {map_base_ + entry->second.offset, entry->second.size};
}

}  // namespace ballistica::base
