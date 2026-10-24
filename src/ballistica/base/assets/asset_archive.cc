// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_archive.h"

#if BA_PLATFORM_ANDROID
#include <fcntl.h>
#include <sys/resource.h>
#include <unistd.h>
#endif

#include <cstdio>
#include <cstdlib>
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
#if BA_PLATFORM_ANDROID
  // Debug: BA_DEBUG_COLD_ARCHIVE=1 (test_game_run --debug-cold-archive)
  // drops the archive's cached pages first, so launch-time costs can be
  // measured as on a cold boot without root. Pages other mappings
  // hold (dex, native libs) stay put; ours are unmapped at this point.
  if (const char* cold = getenv("BA_DEBUG_COLD_ARCHIVE");
      cold != nullptr && cold[0] == '1') {
    int fd = open(path.c_str(), O_RDONLY);
    if (fd >= 0) {
      // A just-installed apk's pages are still dirty, and dirty pages
      // can't be dropped; flush them first.
      fdatasync(fd);
      int r = posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
      close(fd);
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                           "BA_DEBUG_COLD_ARCHIVE set; evicted archive "
                           "page cache (result "
                               + std::to_string(r) + ").");
    }
  }
  struct rusage usage_start{};
  getrusage(RUSAGE_SELF, &usage_start);
#endif
  auto start_time = core::Platform::TimeMonotonicMicrosecs();

  auto archive = OpenImpl_(path);

  if (archive
      && g_core->logging->LogLevelEnabled(LogName::kBaAssets,
                                          LogLevel::kDebug)) {
    auto elapsed = core::Platform::TimeMonotonicMicrosecs() - start_time;
    std::string faults;
#if BA_PLATFORM_ANDROID
    struct rusage usage_end{};
    getrusage(RUSAGE_SELF, &usage_end);
    faults = ", " + std::to_string(usage_end.ru_majflt - usage_start.ru_majflt)
             + " major faults";
#endif
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "%.1f",
             static_cast<double>(elapsed) / 1000.0);
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kDebug,
                         "AssetArchive: indexed "
                             + std::to_string(archive->entries_.size())
                             + " entries in " + buffer + "ms" + faults + ".");
  }
  return archive;
}

auto AssetArchive::OpenImpl_(const std::string& path)
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

    // Note: we deliberately don't touch each entry's *local* header
    // here (needed for its data offset). Those are scattered across
    // the whole apk, so reading them all is one random disk read per
    // entry; on slow-storage devices doing that on the main thread at
    // launch caused ANRs. Get() reads it on demand instead, right next
    // to the data it is about to serve. The central directory itself
    // is one contiguous block.
    bool stored = (method == 0);
    if (stored && comp_size != uncomp_size) {
      return fail("stored entry size mismatch: '" + name + "'");
    }
    archive->entries_[std::move(name)] =
        Entry_{local_offset, static_cast<size_t>(comp_size), stored};

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
  const Entry_& e{entry->second};

  // The data offset comes from the *local* header's name/extra lengths
  // (its extra field can differ from the central one). Reading it is
  // stateless, so this stays lock-free.
  uint32_t local_sig{};
  uint16_t local_name_len{};
  uint16_t local_extra_len{};
  if (!ReadU32(map_base_, map_size_, e.local_header_offset, &local_sig)
      || local_sig != kLocalSignature
      || !ReadU16(map_base_, map_size_, e.local_header_offset + 26,
                  &local_name_len)
      || !ReadU16(map_base_, map_size_, e.local_header_offset + 28,
                  &local_extra_len)) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "AssetArchive: malformed local header for '"
                             + entry_name + "' ('" + path_ + "').");
    return {nullptr, 0};
  }
  size_t data_offset =
      e.local_header_offset + 30 + local_name_len + local_extra_len;

  // Stored entries must fit fully in the mapping to be servable.
  if (data_offset > map_size_ || e.size > map_size_ - data_offset) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kError,
                         "AssetArchive: stored entry out of bounds: '"
                             + entry_name + "' ('" + path_ + "').");
    return {nullptr, 0};
  }
  return {map_base_ + data_offset, e.size};
}

}  // namespace ballistica::base
