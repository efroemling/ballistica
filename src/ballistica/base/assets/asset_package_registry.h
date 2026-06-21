// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_PACKAGE_REGISTRY_H_
#define BALLISTICA_BASE_ASSETS_ASSET_PACKAGE_REGISTRY_H_

#include <memory>
#include <mutex>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

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
/// Thread-safety contract: the registry publishes an immutable
/// snapshot of its package map. Startup registration
/// (:meth:`RegisterBucket`) and runtime registration of
/// downloaded-on-the-fly packages (:meth:`RegisterBucketsAtomic`) both
/// build a fresh snapshot (current ∪ new) and atomically swap it in
/// under a short write lock. Lookups grab the current snapshot under
/// the same lock (just a ``shared_ptr`` copy) and then read it
/// lock-free; an in-flight reader keeps its snapshot alive via the
/// ``shared_ptr`` refcount even as a writer publishes a newer one. So
/// any number of threads can read while the asset-subsystem commits a
/// newly-resolved package, satisfying the "once told an asset is
/// available it stays available" contract.
class AssetPackageRegistry {
 public:
  AssetPackageRegistry();

  // part -> CAS hash. One logical asset can comprise multiple component
  // files keyed by part (a texture's ``.ktx2`` under part ``t`` plus a
  // ``.json`` descriptor under part ``j``, etc.; initiative decision
  // #16). A null/empty asset has an empty part map.
  using PartMap = std::unordered_map<std::string, std::string>;
  // logical_path -> part-keyed component hashes.
  using EntryMap = std::unordered_map<std::string, PartMap>;
  // bucket_id -> entries.
  using BucketMap = std::unordered_map<std::string, EntryMap>;
  // apverid -> buckets.
  using PackagesMap = std::unordered_map<std::string, BucketMap>;
  // One bucket's worth of registration input.
  using BucketSpec = std::tuple<std::string, std::string, EntryMap>;

  /// Register one bucket's worth of entries for a given asset-package
  /// version. Overwrites any prior entries for the same
  /// ``(apverid, bucket_id)``. Used by the startup bundle-manifest
  /// parser; safe to call concurrently with lookups (it goes through
  /// the same atomic-swap path as :meth:`RegisterBucketsAtomic`).
  void RegisterBucket(const std::string& apverid, const std::string& bucket_id,
                      EntryMap entries);

  /// Register several buckets in a single atomic swap. The whole batch
  /// becomes visible at once (or not at all on failure), so the
  /// asset-subsystem can commit a fully-resolved downloaded package
  /// without any window where native sees a half-registered package.
  /// Safe to call concurrently with lookups.
  void RegisterBucketsAtomic(std::vector<BucketSpec> buckets);

  /// Resolve ``(apverid, bucket_id, logical_path, part)`` to a CAS hash.
  /// Returns the hash string, or an empty string if any segment of the
  /// lookup misses (including a missing part — e.g. asking for part
  /// ``t`` on a null asset whose part map is empty). Safe to call
  /// concurrently with registration.
  auto LookupAssetHash(const std::string& apverid, const std::string& bucket_id,
                       const std::string& logical_path,
                       const std::string& part) const -> std::string;

  /// Return the ``textures/...`` bucket id registered for ``apverid`` —
  /// the texture flavor that package actually resolved to (which may be
  /// a fallback if its preferred flavor wasn't available). Empty if the
  /// package isn't registered or has no textures bucket. Lets a texture
  /// lookup track the resolved flavor *per-package* rather than assuming
  /// a single global one (different packages can resolve to different
  /// flavors — e.g. one downloads desktop_v1 while a builtin falls back
  /// to its bundled fallback_v1).
  auto LookupTextureBucketId(const std::string& apverid) const -> std::string;

  /// Cube-map analog of :meth:`LookupTextureBucketId`: the
  /// ``cube_map_textures/...`` bucket id registered for ``apverid``
  /// (decision #24). Empty if the package isn't registered or has no
  /// cube-map bucket.
  auto LookupCubeMapTextureBucketId(const std::string& apverid) const
      -> std::string;

  /// Audio analog of :meth:`LookupTextureBucketId`: the ``audio/...``
  /// bucket id registered for ``apverid`` (decision #25). Empty if the
  /// package isn't registered or has no audio bucket.
  auto LookupAudioBucketId(const std::string& apverid) const -> std::string;

  /// Display-mesh analog of :meth:`LookupTextureBucketId`: the
  /// ``meshes/...`` bucket id registered for ``apverid`` (decision
  /// #26). Empty if the package isn't registered or has no mesh
  /// bucket.
  auto LookupMeshBucketId(const std::string& apverid) const -> std::string;

  /// The flavor-invariant ``constant`` bucket id for ``apverid``
  /// (exact-match; the constant bucket has no dimensions). Collision
  /// meshes live there (decision #26). Empty if the package isn't
  /// registered or has no constant bucket.
  auto LookupConstantBucketId(const std::string& apverid) const -> std::string;

  /// Per-locale-flavored ``language/<locale>`` bucket id registered for
  /// ``apverid`` (the resolved language flavor, e.g. ``language/eng``).
  /// Empty if the package isn't registered or has no language bucket
  /// (strings asset-migration). Analog of :meth:`LookupTextureBucketId`.
  auto LookupLanguageBucketId(const std::string& apverid) const -> std::string;

  /// Single chokepoint for "where is this CAS blob on disk?". Probes
  /// the writable CAS root (``<cache_dir>/assets/<aa>/<rest>``, where
  /// downloaded-on-the-fly blobs land) and falls through to the bundle
  /// root (``<data_dir>/ba_data/assets/<aa>/<rest>``, the shipped
  /// blobs). The probe is an ``fstat`` of the writable location only
  /// (load-time, OS-cached); a writable hit returns it, otherwise the
  /// bundle path is returned unconditionally (it's the canonical home
  /// for bundled blobs and yields a sensible not-found if a hash is
  /// genuinely absent from both). This two-location lookup means
  /// bundled blobs are never copied into the writable root.
  auto CasBlobPath(const std::string& hash) const -> std::string;

 private:
  /// Return the current immutable snapshot (never null). Briefly takes
  /// the write lock to copy the shared_ptr.
  auto Snapshot_() const -> std::shared_ptr<const PackagesMap>;

  /// Shared impl for the per-asset-type bucket-id lookups: the single
  /// bucket registered for ``apverid`` whose id starts with ``prefix``.
  auto LookupBucketIdWithPrefix_(const std::string& apverid,
                                 const char* prefix) const -> std::string;

  mutable std::mutex mutex_;
  // Immutable published snapshot; replaced wholesale on each
  // registration. Guarded by mutex_ for the pointer swap; the pointed-to
  // map is never mutated after publish.
  std::shared_ptr<const PackagesMap> packages_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_PACKAGE_REGISTRY_H_
