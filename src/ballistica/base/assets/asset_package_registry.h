// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_PACKAGE_REGISTRY_H_
#define BALLISTICA_BASE_ASSETS_ASSET_PACKAGE_REGISTRY_H_

#include <string>
#include <unordered_map>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// Holds the in-memory CAS manifest registry that the asset-package
/// pipeline (initiative: asset-packages CAS migration) produces. The
/// Python startup path parses the on-disk bundle manifest plus each
/// referenced bucket manifest and pushes the resolved
/// ``logical_path → CAS_hash`` mappings here via
/// :meth:`RegisterBucket`. Hot-path lookups (``gettexture`` etc.) then
/// resolve through :meth:`LookupAssetHash` without any Python or GIL
/// involvement, and use :meth:`CasBlobPath` to translate a hash into
/// the on-disk blob path.
///
/// Thread-safety contract: registration happens once at app startup
/// before any lookups occur; after that the registry is read-only and
/// any number of threads can read concurrently. Phase 3 runtime swaps
/// (language / quality changes) will introduce mutation and need a
/// concurrency strategy — atomic swap of immutable maps is the
/// natural fit but deferred.
class AssetPackageRegistry {
 public:
  AssetPackageRegistry();

  /// Register one bucket's worth of entries for a given asset-package
  /// version. Overwrites any prior entries for the same
  /// ``(apverid, bucket_id)``. Not thread-safe; call only from the
  /// startup path before lookups begin.
  void RegisterBucket(const std::string& apverid, const std::string& bucket_id,
                      std::unordered_map<std::string, std::string> entries);

  /// Resolve ``(apverid, bucket_id, logical_path)`` to a CAS hash.
  /// Returns the hash string, or an empty string if any segment of
  /// the lookup misses. Safe to call concurrently after startup.
  auto LookupAssetHash(const std::string& apverid, const std::string& bucket_id,
                       const std::string& logical_path) const -> std::string;

  /// Single chokepoint for "where is this CAS blob on disk?". Today
  /// returns ``<data_dir>/ba_data/assets/<aa>/<rest>`` matching the
  /// bundled layout. Phase 4+ extends this to consult a writable CAS
  /// root, fall through to the bundle root, and trigger download for
  /// missing hashes — but every caller stays unchanged because the
  /// resolution lives behind this one function.
  auto CasBlobPath(const std::string& hash) const -> std::string;

 private:
  // apverid -> bucket_id -> {logical_path -> hash}
  std::unordered_map<
      std::string,
      std::unordered_map<std::string,
                         std::unordered_map<std::string, std::string>>>
      packages_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_PACKAGE_REGISTRY_H_
