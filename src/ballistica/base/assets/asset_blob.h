// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_BLOB_H_
#define BALLISTICA_BASE_ASSETS_ASSET_BLOB_H_

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace ballistica::base {

class AssetArchive;

/// A read-only span of asset data plus ownership of its backing.
///
/// This is the universal currency for asset loading: parsers take a
/// blob's (data, size) span and never care where the bytes live.
/// Backings are: *mapped* (a whole-file memory-map; clean evictable
/// pages, released on destruction), *heap* (owned bytes; fallback for
/// unmappable files), and *borrowed* (a span into memory owned by
/// someone longer-lived, such as the boot-time apk mapping on
/// Android). Movable, non-copyable. See
/// docs/initiatives/android-apk-direct-ba-data.md for the design.
///
/// Parsers consuming blobs must treat the span as byte data with no
/// alignment guarantees (borrowed spans into archives are aligned to
/// 4 bytes at best) - read multi-byte fields via memcpy-style
/// accesses, never by casting interior pointers to struct/int types.
class AssetBlob {
 public:
  AssetBlob() = default;
  ~AssetBlob() { Release_(); }

  AssetBlob(AssetBlob&& other) noexcept { *this = std::move(other); }
  auto operator=(AssetBlob&& other) noexcept -> AssetBlob& {
    if (this != &other) {
      Release_();
      data_ = other.data_;
      size_ = other.size_;
      backing_ = other.backing_;
      heap_ = std::move(other.heap_);
      other.data_ = nullptr;
      other.size_ = 0;
      other.backing_ = Backing_::kNone;
    }
    return *this;
  }
  AssetBlob(const AssetBlob&) = delete;
  auto operator=(const AssetBlob&) -> AssetBlob& = delete;

  /// Load a file's full contents: whole-file memory-map when
  /// possible, heap read otherwise. Returns an invalid blob on
  /// failure (missing/unreadable file); does no logging itself, so
  /// callers should report failures with their own context.
  ///
  /// If an archive is mounted (see MountArchive()), paths of the
  /// form "<archive-path>/<entry>" resolve to borrowed spans into
  /// the archive mapping instead of touching the filesystem.
  static auto FromFile(const std::string& path) -> AssetBlob;

  /// Wrap externally-owned memory. The memory must outlive the blob.
  static auto Borrowed(const void* data, size_t size) -> AssetBlob;

  /// Take ownership of heap bytes.
  static auto FromHeap(std::vector<uint8_t> bytes) -> AssetBlob;

  /// Is there a backing? (An existing blob may still be empty).
  auto exists() const -> bool { return backing_ != Backing_::kNone; }
  auto data() const -> const uint8_t* { return data_; }
  auto size() const -> size_t { return size_; }

  /// Copy the full span out as a string (for text payloads).
  auto ToString() const -> std::string {
    return std::string(reinterpret_cast<const char*>(data_), size_);
  }

  /// Register the process's bundled asset archive (e.g. the Android
  /// apk). Call at most once, during bootstrap, before anything can
  /// load archive paths; the archive lives for the process life.
  static void MountArchive(std::unique_ptr<AssetArchive> archive);

  /// Bounds-checked random-access copy out of the span; returns
  /// false (copying nothing) if the range doesn't fully fit.
  auto ReadAt(size_t offset, void* dst, size_t size) const -> bool {
    if (offset > size_ || size > size_ - offset) {
      return false;
    }
    memcpy(dst, data_ + offset, size);
    return true;
  }

 private:
  enum class Backing_ : uint8_t { kNone, kBorrowed, kMapped, kHeap };

  void Release_();

  const uint8_t* data_{};
  size_t size_{};
  Backing_ backing_{Backing_::kNone};
  std::vector<uint8_t> heap_;
};

/// Sequential fread-style cursor over an AssetBlob's span.
///
/// ReadInto() copies out via memcpy, giving parsers alignment-safe
/// field reads with the same call shape as the fread loops they
/// replace. The referenced blob must outlive the reader.
class AssetBlobReader {
 public:
  explicit AssetBlobReader(const AssetBlob& blob)
      : pos_{blob.data()}, remaining_{blob.size()} {}

  /// Copy the next size bytes into dst and advance; returns false
  /// (consuming nothing) if fewer than size bytes remain.
  auto ReadInto(void* dst, size_t size) -> bool {
    if (size > remaining_) {
      return false;
    }
    memcpy(dst, pos_, size);
    pos_ += size;
    remaining_ -= size;
    return true;
  }

  auto remaining() const -> size_t { return remaining_; }

 private:
  const uint8_t* pos_{};
  size_t remaining_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_BLOB_H_
