// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_ARCHIVE_H_
#define BALLISTICA_BASE_ASSETS_ASSET_ARCHIVE_H_

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>

namespace ballistica::base {

/// A read-only zip archive (e.g. the Android apk) memory-mapped in
/// its entirety with its entries indexed, so stored (uncompressed)
/// entries can be served as zero-copy spans into the mapping.
///
/// Built once during bootstrap and immutable afterward, so lookups
/// are lock-free and thread-safe. Deflated entries are indexed but
/// not servable as spans (Get() returns nothing for them); the
/// things we serve this way (asset blobs, pycs) are packed stored
/// precisely for this purpose.
class AssetArchive {
 public:
  ~AssetArchive();

  /// Map and index an archive. Returns nullptr (with a logged
  /// error) on failure - missing file, malformed/zip64 central
  /// directory, etc.
  static auto Open(const std::string& path) -> std::unique_ptr<AssetArchive>;

  /// Look up a stored entry by its exact archive path (e.g.
  /// "assets/foo/bar.bablob"). Returns the entry's span, or
  /// (nullptr, 0) if absent or not stored uncompressed.
  auto Get(const std::string& entry_name) const
      -> std::pair<const uint8_t*, size_t>;

  auto path() const -> const std::string& { return path_; }

 private:
  AssetArchive() = default;

  struct Entry_ {
    size_t offset;
    size_t size;
    bool stored;
  };

  std::string path_;
  const uint8_t* map_base_{};
  size_t map_size_{};
  std::unordered_map<std::string, Entry_> entries_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_ARCHIVE_H_
