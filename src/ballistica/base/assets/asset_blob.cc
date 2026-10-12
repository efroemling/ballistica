// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_blob.h"

#include <cstdio>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_archive.h"
#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::base {

// Bundled asset archive; mounted at most once during bootstrap and
// alive for the process life, so unsynchronized reads are safe.
static std::unique_ptr<AssetArchive> g_mounted_archive;

void AssetBlob::MountArchive(std::unique_ptr<AssetArchive> archive) {
  assert(archive != nullptr);
  assert(g_mounted_archive == nullptr);
  g_mounted_archive = std::move(archive);
}

auto AssetBlob::FromFile(const std::string& path) -> AssetBlob {
  AssetBlob blob;

  // Paths into the mounted archive resolve as borrowed spans.
  if (g_mounted_archive != nullptr) {
    const std::string& archive_path = g_mounted_archive->path();
    if (path.size() > archive_path.size() + 1
        && path.compare(0, archive_path.size(), archive_path) == 0
        && path[archive_path.size()] == '/') {
      auto entry = g_mounted_archive->Get(path.substr(archive_path.size() + 1));
      if (entry.first != nullptr) {
        return Borrowed(entry.first, entry.second);
      }
      // Under the archive but absent/unservable: invalid blob (the
      // filesystem could never serve such a path either).
      return blob;
    }
  }

  // Ideal case: map the file.
  size_t map_size{};
  if (const void* base = g_core->platform->MapFileReadOnly(path, &map_size)) {
    blob.data_ = static_cast<const uint8_t*>(base);
    blob.size_ = map_size;
    blob.backing_ = Backing_::kMapped;
    return blob;
  }

  // Fall back to a plain heap read (also covers empty files, which
  // can't be mapped).
  FILE* f = g_core->platform->FOpen(path.c_str(), "rb");
  if (!f) {
    return blob;
  }
  std::vector<uint8_t> bytes;
  if (fseek(f, 0, SEEK_END) == 0) {
    long fsize = ftell(f);  // NOLINT(runtime/int) (ftell's API type)
    if (fsize >= 0 && fseek(f, 0, SEEK_SET) == 0) {
      bytes.resize(static_cast<size_t>(fsize));
      if (bytes.empty()
          || fread(bytes.data(), 1, bytes.size(), f) == bytes.size()) {
        fclose(f);
        return FromHeap(std::move(bytes));
      }
    }
  }
  fclose(f);
  return blob;
}

auto AssetBlob::Borrowed(const void* data, size_t size) -> AssetBlob {
  AssetBlob blob;
  blob.data_ = static_cast<const uint8_t*>(data);
  blob.size_ = size;
  blob.backing_ = Backing_::kBorrowed;
  return blob;
}

auto AssetBlob::FromHeap(std::vector<uint8_t> bytes) -> AssetBlob {
  AssetBlob blob;
  blob.heap_ = std::move(bytes);
  blob.data_ = blob.heap_.data();
  blob.size_ = blob.heap_.size();
  blob.backing_ = Backing_::kHeap;
  return blob;
}

void AssetBlob::Release_() {
  if (backing_ == Backing_::kMapped) {
    g_core->platform->UnmapFile(data_, size_);
  }
  data_ = nullptr;
  size_ = 0;
  backing_ = Backing_::kNone;
  heap_.clear();
}

}  // namespace ballistica::base
