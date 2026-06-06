// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_package_registry.h"

#include <memory>
#include <mutex>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica::base {

AssetPackageRegistry::AssetPackageRegistry()
    : packages_{std::make_shared<const PackagesMap>()} {}

void AssetPackageRegistry::RegisterBucket(const std::string& apverid,
                                          const std::string& bucket_id,
                                          EntryMap entries) {
  std::vector<BucketSpec> buckets;
  buckets.emplace_back(apverid, bucket_id, std::move(entries));
  RegisterBucketsAtomic(std::move(buckets));
}

void AssetPackageRegistry::RegisterBucketsAtomic(
    std::vector<BucketSpec> buckets) {
  std::scoped_lock lock(mutex_);

  // Copy-on-write: build a fresh map seeded from the current snapshot,
  // apply the whole batch, then publish it as the new snapshot. Any
  // reader still holding the old snapshot keeps reading it consistently
  // until it releases its shared_ptr. Writes are rare (startup + a
  // resolve commit) so doing the copy under the lock is fine.
  auto next = std::make_shared<PackagesMap>(*packages_);
  for (auto& spec : buckets) {
    auto& apverid = std::get<0>(spec);
    auto& bucket_id = std::get<1>(spec);
    auto& entries = std::get<2>(spec);
    (*next)[apverid][bucket_id] = std::move(entries);
  }
  packages_ = std::move(next);
}

auto AssetPackageRegistry::Snapshot_() const
    -> std::shared_ptr<const PackagesMap> {
  std::scoped_lock lock(mutex_);
  return packages_;
}

auto AssetPackageRegistry::LookupAssetHash(const std::string& apverid,
                                           const std::string& bucket_id,
                                           const std::string& logical_path,
                                           const std::string& part) const
    -> std::string {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return "";
  }
  auto bucket_it = pkg_it->second.find(bucket_id);
  if (bucket_it == pkg_it->second.end()) {
    return "";
  }
  auto entry_it = bucket_it->second.find(logical_path);
  if (entry_it == bucket_it->second.end()) {
    return "";
  }
  // entry_it->second is the part-keyed component map; pull the
  // requested part (empty string if absent, e.g. a null asset).
  auto part_it = entry_it->second.find(part);
  if (part_it == entry_it->second.end()) {
    return "";
  }
  return part_it->second;
}

auto AssetPackageRegistry::LookupTextureBucketId(
    const std::string& apverid) const -> std::string {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return "";
  }
  // Each package registers exactly one textures bucket — its resolved
  // flavor, e.g. "textures/desktop_v1.gamma.regular" or
  // "textures/fallback_v1.gamma.regular". Find it by prefix.
  for (auto&& bucket : pkg_it->second) {
    if (bucket.first.rfind("textures/", 0) == 0) {
      return bucket.first;
    }
  }
  return "";
}

auto AssetPackageRegistry::CasBlobPath(const std::string& hash) const
    -> std::string {
  // sha256 hex is 64 chars; bail on anything shorter than the
  // shard prefix so we don't form a malformed path.
  if (hash.size() < 2) {
    return "";
  }
  // Layout mirrors bacommon.bacloud.asset_file_cache_path:
  // single-level sharding by the first 2 hex chars.
  std::string shard =
      hash.substr(0, 2) + std::string(BA_DIRSLASH) + hash.substr(2);

  // Writable CAS root: where downloaded-on-the-fly blobs land. Probe it
  // first; an fstat hit here means we have a downloaded blob to use.
  std::string writable = g_core->GetCacheDirectory() + BA_DIRSLASH + "assets"
                         + BA_DIRSLASH + shard;
  if (g_core->platform->FilePathExists(writable)) {
    return writable;
  }
  // Bundle root: shipped blobs. Returned unconditionally on a writable
  // miss — it's the canonical home for bundled blobs, and if a hash is
  // genuinely absent from both this yields a sensible not-found when the
  // caller tries to open it. (Bundled blobs thus never get copied into
  // the writable root.)
  return g_core->GetDataDirectory() + BA_DIRSLASH + "ba_data" + BA_DIRSLASH
         + "assets" + BA_DIRSLASH + shard;
}

}  // namespace ballistica::base
