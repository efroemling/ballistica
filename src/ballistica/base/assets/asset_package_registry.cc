// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_package_registry.h"

#include <algorithm>
#include <memory>
#include <mutex>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica::base {

auto AssetPackageRegistry::ApverNumFromKey(const std::string& key)
    -> std::optional<int64_t> {
  if (key.empty() || key.size() > 18) {
    return std::nullopt;
  }
  int64_t out{};
  for (char c : key) {
    if (c < '0' || c > '9') {
      return std::nullopt;
    }
    out = out * 10 + (c - '0');
  }
  return out;
}

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
  std::vector<std::string> touched;
  {
    std::scoped_lock lock(mutex_);

    // Copy-on-write: build a fresh map seeded from the current snapshot,
    // apply the whole batch, then publish it as the new snapshot. Any
    // reader still holding the old snapshot keeps reading it consistently
    // until it releases its shared_ptr. Writes are rare (startup + a
    // resolve commit) so doing the copy under the lock is fine.
    auto next = std::make_shared<PackagesMap>(*packages_);

    // A batch is the COMPLETE set of buckets for each package it covers (a
    // resolve always finalizes every bucket), so REPLACE each touched
    // package's bucket map rather than merging into it. Merging would leave
    // a previously-registered flavor of a runtime-switchable dimension
    // lingering -- e.g. an old ``language/<locale>`` bucket after a language
    // switch, or an old ``textures/<profile>...`` bucket after a future
    // texture-tier switch -- which the prefix lookups (LookupLanguageBucketId
    // et al., "first matching head wins") could then return instead of the
    // freshly-registered one. The clear+set both happen on the not-yet-
    // published copy, so readers only ever see the old or the fully-rebuilt
    // snapshot, never a partial one.
    // Untouched packages keep sharing their published bucket maps; each
    // touched one gets a freshly built map holding just this batch.
    std::unordered_map<std::string, std::shared_ptr<BucketMap>> rebuilt;
    for (auto& spec : buckets) {
      auto& apverid = std::get<0>(spec);
      auto& bucket_id = std::get<1>(spec);
      auto& entries = std::get<2>(spec);
      auto& bucket_map = rebuilt[apverid];
      if (!bucket_map) {
        bucket_map = std::make_shared<BucketMap>();
      }
      (*bucket_map)[bucket_id] = std::move(entries);
    }
    for (auto&& [apverid, bucket_map] : rebuilt) {
      touched.push_back(apverid);
      (*next)[apverid] = std::move(bucket_map);
    }
    packages_ = std::move(next);
    generation_.fetch_add(1, std::memory_order_acq_rel);
  }
  // Build the touched packages' flat listings now (this runs on the
  // resolve's pool thread) so the first character definition that
  // decodes against a freshly registered package pays nothing on the
  // logic thread. Outside the lock: FlatListing takes it itself.
  for (auto&& apverid : touched) {
    FlatListing(apverid);
  }
}

void AssetPackageRegistry::NoteWanted(const std::string& apverid) {
  assert(g_base->InLogicThread());
  millisecs_t now = g_core->AppTimeMillisecs();
  auto it = wanted_.find(apverid);
  if (it != wanted_.end()) {
    it->second = now;
    return;
  }
  if (Snapshot_()->count(apverid)) {
    // Registered already; the holder just hasn't re-attempted yet.
    return;
  }
  if (wanted_.size() >= kMaxWanted_) {
    BA_LOG_ONCE(
        LogName::kBaAssets, LogLevel::kWarning,
        "Wanted asset-package set is full; ignoring '" + apverid + "'.");
    return;
  }
  wanted_[apverid] = now;
  // New entry: let the Python drainer know. Deferred rather than called
  // inline since we can be reached from the middle of a draw.
  g_base->logic->event_loop()->PushCall([] {
    auto& objs = g_base->python->objs();
    auto id = BasePython::ObjID::kWantedAssetPackagesChangedCall;
    if (objs.Exists(id)) {
      objs.Get(id).Call();
    }
  });
}

auto AssetPackageRegistry::TakeWanted(millisecs_t max_age)
    -> std::vector<std::pair<std::string, millisecs_t>> {
  assert(g_base->InLogicThread());
  millisecs_t now = g_core->AppTimeMillisecs();
  auto snapshot = Snapshot_();
  std::vector<std::pair<std::string, millisecs_t>> out;
  for (auto it = wanted_.begin(); it != wanted_.end();) {
    millisecs_t age = now - it->second;
    // Drop what nobody re-noted recently and what has since landed
    // (holders re-note only while their media stays missing, but a
    // fresh note can race the commit; either way an acquired package
    // must never be asked for again).
    if (age > max_age || snapshot->count(it->first)) {
      it = wanted_.erase(it);
    } else {
      out.emplace_back(it->first, age);
      ++it;
    }
  }
  return out;
}

auto AssetPackageRegistry::Snapshot_() const
    -> std::shared_ptr<const PackagesMap> {
  std::scoped_lock lock(mutex_);
  return packages_;
}

auto AssetPackageRegistry::BucketLogicalPathsSorted(
    const std::string& apverid, const std::string& bucket_id) const
    -> std::vector<std::string> {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return {};
  }
  auto bucket_it = pkg_it->second->find(bucket_id);
  if (bucket_it == pkg_it->second->end()) {
    return {};
  }
  std::vector<std::string> paths;
  paths.reserve(bucket_it->second.size());
  for (auto&& entry : bucket_it->second) {
    paths.push_back(entry.first);
  }
  std::sort(paths.begin(), paths.end());
  return paths;
}

auto AssetPackageRegistry::FlatListing(const std::string& apverid) const
    -> std::shared_ptr<const std::vector<std::string>> {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return nullptr;
  }
  {
    std::scoped_lock lock(mutex_);
    auto cached = flat_listings_.find(apverid);
    if (cached != flat_listings_.end()) {
      return cached->second;
    }
  }
  // Build outside the lock (this is the O(package) part); a concurrent
  // builder for the same apverid produces an identical listing, so a
  // lost insert race is harmless. Exactly the four asset bucket kinds
  // the Python half (bacommon.assetspec.AssetBucketKind) unions, so
  // both ends lay out the same domain.
  auto listing = std::make_shared<std::vector<std::string>>();
  for (const std::string& bucket_id :
       {LookupTextureBucketId(apverid), LookupMeshBucketId(apverid),
        LookupAudioBucketId(apverid), LookupConstantBucketId(apverid)}) {
    if (bucket_id.empty()) {
      continue;
    }
    auto bucket_it = pkg_it->second->find(bucket_id);
    if (bucket_it == pkg_it->second->end()) {
      continue;
    }
    for (auto&& entry : bucket_it->second) {
      listing->push_back(entry.first);
    }
  }
  std::sort(listing->begin(), listing->end());
  listing->erase(std::unique(listing->begin(), listing->end()), listing->end());
  std::shared_ptr<const std::vector<std::string>> result = listing;
  {
    std::scoped_lock lock(mutex_);
    flat_listings_.emplace(apverid, result);
  }
  return result;
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
  auto bucket_it = pkg_it->second->find(bucket_id);
  if (bucket_it == pkg_it->second->end()) {
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

auto AssetPackageRegistry::LookupAssetHashByRole(
    const std::string& apverid, const std::string& bucket_id,
    const std::string& logical_path, const std::string& role,
    const std::vector<std::string>& format_prefs) const -> std::string {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return "";
  }
  auto bucket_it = pkg_it->second->find(bucket_id);
  if (bucket_it == pkg_it->second->end()) {
    return "";
  }
  auto entry_it = bucket_it->second.find(logical_path);
  if (entry_it == bucket_it->second.end()) {
    return "";
  }
  // Parts are named ``<role>.<format>`` (decision #35); take the first
  // format present in preference order (empty if none is, e.g. a null
  // asset's empty part map).
  for (auto&& format : format_prefs) {
    auto part_it = entry_it->second.find(role + "." + format);
    if (part_it != entry_it->second.end()) {
      return part_it->second;
    }
  }
  return "";
}

auto AssetPackageRegistry::DebugDescribePackage(
    const std::string& apverid) const -> std::string {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return "package not registered";
  }
  std::string out = "registered buckets:";
  for (auto&& bucket : *pkg_it->second) {
    out +=
        " " + bucket.first + "(" + std::to_string(bucket.second.size()) + ")";
  }
  return out;
}

auto AssetPackageRegistry::LookupBucketIdWithPrefix_(const std::string& apverid,
                                                     const char* prefix) const
    -> std::string {
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return "";
  }
  // Each package registers exactly one bucket per asset-type head — its
  // resolved flavor, e.g. "textures/desktop_v1.gamma.regular" or
  // "textures/fallback_v1.gamma.regular". Find it by prefix. (The heads
  // in use — "textures/", "audio/", "meshes/", "language/" — are
  // mutually non-prefixing, so the first match is unambiguous.)
  for (auto&& bucket : *pkg_it->second) {
    if (bucket.first.rfind(prefix, 0) == 0) {
      return bucket.first;
    }
  }
  return "";
}

auto AssetPackageRegistry::LookupTextureBucketId(
    const std::string& apverid) const -> std::string {
  // Serves both 2D textures and cube maps — they share this bucket (see
  // Assets::FindCasCubeMapTexturePath).
  return LookupBucketIdWithPrefix_(apverid, "textures/");
}

auto AssetPackageRegistry::LookupAudioBucketId(const std::string& apverid) const
    -> std::string {
  return LookupBucketIdWithPrefix_(apverid, "audio/");
}

auto AssetPackageRegistry::LookupMeshBucketId(const std::string& apverid) const
    -> std::string {
  return LookupBucketIdWithPrefix_(apverid, "meshes/");
}

auto AssetPackageRegistry::LookupLanguageBucketId(
    const std::string& apverid) const -> std::string {
  return LookupBucketIdWithPrefix_(apverid, "language/");
}

auto AssetPackageRegistry::LookupConstantBucketId(
    const std::string& apverid) const -> std::string {
  // The constant bucket has no dimensions, so its id is the bare head
  // (no trailing slash) and prefix-matching degenerates to an exact
  // match — which is what we want anyway.
  auto snapshot = Snapshot_();
  auto pkg_it = snapshot->find(apverid);
  if (pkg_it == snapshot->end()) {
    return "";
  }
  for (auto&& bucket : *pkg_it->second) {
    if (bucket.first == "constant") {
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
  return BundledCasBlobPath(hash);
}

auto AssetPackageRegistry::BundledCasBlobPath(const std::string& hash) const
    -> std::string {
  if (hash.size() < 2) {
    return "";
  }
  if (!bundled_cas_root_override_.empty()) {
    // Archive entries always use forward slashes.
    return bundled_cas_root_override_ + "/" + hash.substr(0, 2) + "/"
           + hash.substr(2) + bundled_cas_suffix_;
  }
  std::string shard =
      hash.substr(0, 2) + std::string(BA_DIRSLASH) + hash.substr(2);
  return g_core->GetDataDirectory() + BA_DIRSLASH + "ba_data" + BA_DIRSLASH
         + "assets" + BA_DIRSLASH + shard;
}

void AssetPackageRegistry::SetBundledCasOverride(const std::string& root,
                                                 const std::string& suffix) {
  bundled_cas_root_override_ = root;
  bundled_cas_suffix_ = suffix;
}

void AssetPackageRegistry::SetConstructComplete() {
  construct_complete_.store(true, std::memory_order_release);
}

void AssetPackageRegistry::CheckPreConstructAccess(
    const std::string& apverid, const std::string& logical_path) const {
  // Steady state after hand-off: a single relaxed-ish atomic load and
  // out. Everything below runs only during bring-up.
  if (construct_complete_.load(std::memory_order_acquire)) {
    return;
  }
  if (apverid == kBuiltinAssetsApvernum) {
    return;
  }
  auto msg = std::string("Asset '") + apverid + ":" + logical_path
             + "' accessed before construct-mode finished resolving"
               " asset-packages; only "
             + kBuiltinAssetsApvernum
             + " is guaranteed available this early. Hold the wrapper"
               " reference and load it on first use instead.";
  if (g_buildconfig.debug_build()) {
    FatalError(msg);
  } else {
    // Log-once: a violation on a hot path would otherwise flood.
    if (!did_log_pre_construct_access_.exchange(true,
                                                std::memory_order_acq_rel)) {
      g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kError, msg);
    }
  }
}

}  // namespace ballistica::base
