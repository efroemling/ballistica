// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset_package_registry.h"

#include <string>
#include <unordered_map>
#include <utility>

#include "ballistica/core/core.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica::base {

AssetPackageRegistry::AssetPackageRegistry() = default;

void AssetPackageRegistry::RegisterBucket(
    const std::string& apverid, const std::string& bucket_id,
    std::unordered_map<std::string, std::string> entries) {
  packages_[apverid][bucket_id] = std::move(entries);
}

auto AssetPackageRegistry::LookupAssetHash(
    const std::string& apverid, const std::string& bucket_id,
    const std::string& logical_path) const -> std::string {
  auto pkg_it = packages_.find(apverid);
  if (pkg_it == packages_.end()) {
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
  return entry_it->second;
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
  return g_core->GetDataDirectory() + BA_DIRSLASH + "ba_data" + BA_DIRSLASH
         + "assets" + BA_DIRSLASH + hash.substr(0, 2) + BA_DIRSLASH
         + hash.substr(2);
}

}  // namespace ballistica::base
