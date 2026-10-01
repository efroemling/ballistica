// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/media_block.h"

#include <algorithm>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_package_registry.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/base.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

auto ReadPackageAssetRef(const JsonRef& obj, const char* key,
                         PackageAssetRef* out) -> bool {
  JsonRef ref = obj[key];
  if (auto index = ref.as_int()) {
    if (*index < 0) {
      return false;
    }
    out->index = *index;
    return true;
  }
  // The package is its version's numeric id (keyed here as text).
  auto apvernum = ref["a"].as_int();
  auto name = ref["n"].as_string();
  if (!apvernum || *apvernum <= 0 || !name || name->empty()) {
    return false;
  }
  out->apverid = std::to_string(*apvernum);
  out->name = std::string(*name);
  return true;
}

void ReadPackageAssetRefs(const JsonRef& obj, const char* key,
                          std::vector<PackageAssetRef>* out) {
  out->clear();
  JsonRef arr = obj[key];
  if (!arr.is_array()) {
    return;
  }
  for (size_t i = 0; i < arr.size(); ++i) {
    PackageAssetRef ref;
    JsonRef entry = arr[i];
    if (auto index = entry.as_int()) {
      if (*index < 0) {
        continue;
      }
      ref.index = *index;
      out->push_back(std::move(ref));
      continue;
    }
    auto apvernum = entry["a"].as_int();
    auto name = entry["n"].as_string();
    if (!apvernum || *apvernum <= 0 || !name || name->empty()) {
      continue;
    }
    ref.apverid = std::to_string(*apvernum);
    ref.name = std::string(*name);
    out->push_back(std::move(ref));
  }
}

void ReadPackageManifest(const JsonRef& obj, std::vector<std::string>* out,
                         std::string* digest) {
  out->clear();
  digest->clear();
  JsonRef pk = obj["pk"];
  if (pk.is_array()) {
    for (size_t i = 0; i < pk.size(); ++i) {
      // Numeric ids, keyed here as text.
      if (auto apvernum = pk[i].as_int(); apvernum && *apvernum > 0) {
        out->emplace_back(std::to_string(*apvernum));
      }
    }
  }
  if (auto dg = obj["dg"].as_string()) {
    *digest = std::string(*dg);
  }
}

namespace {

// The producer's digest of an index domain, reproduced from our
// listings: sha256 over (apverid, NUL, each name + LF, NUL) per package
// in manifest order, hex, first 16 chars -- exactly
// bacommon.assetspec.AssetIndexContext.domain_digest(). Cached per
// manifest (listings are immutable per apverid). Logic thread only
// (hashing goes through Python's hashlib).
auto DomainDigest(
    const std::vector<std::string>& packages,
    const std::vector<std::shared_ptr<const std::vector<std::string>>>&
        listings) -> std::string {
  assert(g_base->InLogicThread());
  static std::unordered_map<std::string, std::string> cache;
  std::string key;
  for (const auto& apverid : packages) {
    key += apverid;
    key += '\n';
  }
  if (auto it = cache.find(key); it != cache.end()) {
    return it->second;
  }
  std::string buffer;
  for (size_t i = 0; i < packages.size(); ++i) {
    buffer += packages[i];
    buffer += '\0';
    for (const auto& name : *listings[i]) {
      buffer += name;
      buffer += '\n';
    }
    buffer += '\0';
  }
  std::string digest = g_base->python->Sha256Hex(buffer).substr(0, 16);
  if (!digest.empty()) {
    cache.emplace(std::move(key), digest);
  }
  return digest;
}

auto PackageRegistered(const std::string& apverid) -> bool {
  auto* registry = g_base->assets->package_registry();
  return !registry->LookupTextureBucketId(apverid).empty()
         || !registry->LookupMeshBucketId(apverid).empty()
         || !registry->LookupAudioBucketId(apverid).empty();
}

// Fill in (apverid, name) for a block's flat-indexed refs from its
// package manifest's listings. False (leaving media not-ready, so the
// standin is drawn) when a manifest package isn't registered yet;
// decode errors -- an index outside the domain, or one landing on the
// wrong asset kind -- also fail but log, since they mean a malformed
// definition rather than a pending download.
auto ResolveIndexedRefs(const std::vector<std::string>& packages,
                        const std::string& expected_digest,
                        const std::vector<MediaBlock::IndexedRef>& refs)
    -> bool {
  if (refs.empty()) {
    return true;
  }
  if (packages.empty()) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "Definition has indexed asset refs but no package manifest.");
    return false;
  }
  // Per-package flat listings come cached from the registry (built
  // once per apverid), so this is a few map lookups per resolve rather
  // than an O(package) copy-and-sort on every spawn or widget.
  auto* registry = g_base->assets->package_registry();
  std::vector<std::shared_ptr<const std::vector<std::string>>> listings;
  std::vector<int64_t> offsets;
  int64_t total = 0;
  for (const auto& apverid : packages) {
    auto listing = registry->FlatListing(apverid);
    if (!listing) {
      // Not registered (yet); no error -- the standin covers this, and
      // noting every missing package lets the background acquirer
      // fetch them (character-skins.md, lazy media).
      for (const auto& missing : packages) {
        if (!registry->FlatListing(missing)) {
          registry->NoteWanted(missing);
        }
      }
      return false;
    }
    offsets.push_back(total);
    total += static_cast<int64_t>(listing->size());
    listings.push_back(std::move(listing));
  }
  // Domain guard: a producer digest that doesn't match ours means the
  // two ends laid the packages out differently, and every index in
  // this block would name the wrong asset. Refuse (standin) and say
  // which slice widths we see, so the drift is locatable.
  if (!expected_digest.empty()) {
    std::string ours = DomainDigest(packages, listings);
    // Producers send a prefix (bacommon.assetspec.wire_digest); accept
    // any of at least kMinWireDigestLength, as digest_matches() does.
    constexpr size_t kMinWireDigestLength{4};
    bool matches{expected_digest.size() >= kMinWireDigestLength
                 && ours.compare(0, expected_digest.size(), expected_digest)
                        == 0};
    if (!matches) {
      std::string widths;
      for (size_t i = 0; i < packages.size(); ++i) {
        widths += (i ? ", " : "") + packages[i] + "="
                  + std::to_string(listings[i]->size());
      }
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Asset-index domain mismatch: producer digest "
                      + expected_digest + ", ours " + ours
                      + "; refusing to decode this block (standin). Our"
                        " slice widths: "
                      + widths + ".");
      return false;
    }
  }
  for (const auto& [ref, prefix] : refs) {
    if (ref->index >= total) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Asset index " + std::to_string(ref->index)
                      + " is outside its manifest domain (total "
                      + std::to_string(total) + ").");
      return false;
    }
    auto it = std::upper_bound(offsets.begin(), offsets.end(), ref->index);
    auto pkg = static_cast<size_t>(std::distance(offsets.begin(), it) - 1);
    const std::string& name =
        (*listings[pkg])[static_cast<size_t>(ref->index - offsets[pkg])];
    if (name.rfind(prefix, 0) != 0) {
      // The slot's kind is a check, not a domain selector; a mismatch
      // means a wrong asset, never a silently different one.
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Asset index " + std::to_string(ref->index) + " decodes to '"
                      + name + "'; expected a '" + prefix + "' asset.");
      return false;
    }
    ref->apverid = packages[pkg];
    ref->name = name;
  }
  return true;
}

// Every referenced package must be registered locally for a block's
// media to be usable; otherwise the standin is drawn. Missing packages
// are noted as wanted, so the background acquirer fetches them.
auto AllPackagesRegistered(const std::vector<const PackageAssetRef*>& refs)
    -> bool {
  bool all{true};
  for (const auto* ref : refs) {
    if (!PackageRegistered(ref->apverid)) {
      g_base->assets->package_registry()->NoteWanted(ref->apverid);
      all = false;
    }
  }
  return all;
}

auto AllLoaded(const std::vector<Object::Ref<Asset>>& assets) -> bool {
  for (const auto& asset : assets) {
    if (!asset->loaded()) {
      return false;
    }
  }
  return true;
}

}  // namespace

MediaGetter::MediaGetter(std::vector<Object::Ref<Asset>>* pending)
    : pending_{pending} {}

auto MediaGetter::Texture(const PackageAssetRef& ref)
    -> Object::Ref<TextureAsset> {
  auto out = g_base->assets->GetPackageTexture(ref.apverid, ref.name);
  pending_->emplace_back(out.get());
  return out;
}

auto MediaGetter::Mesh(const PackageAssetRef& ref) -> Object::Ref<MeshAsset> {
  auto out = g_base->assets->GetPackageMesh(ref.apverid, ref.name);
  pending_->emplace_back(out.get());
  return out;
}

auto MediaGetter::Sound(const PackageAssetRef& ref) -> Object::Ref<SoundAsset> {
  return g_base->assets->GetPackageSound(ref.apverid, ref.name);
}

void MediaBlock::NoteIndexed(PackageAssetRef* ref, const char* prefix,
                             std::vector<IndexedRef>* refs) {
  if (ref->name.empty() && ref->index >= 0) {
    refs->emplace_back(ref, prefix);
  }
}

void MediaBlock::Load(const std::vector<std::string>& packages,
                      const std::string& domain_digest,
                      const std::vector<IndexedRef>& indexed,
                      const std::vector<const PackageAssetRef*>& required,
                      const std::function<void(MediaGetter* get)>& get) {
  assert(g_base->InLogicThread());
  if (ready_ || pending_) {
    return;
  }
  if (!ResolveIndexedRefs(packages, domain_digest, indexed)) {
    return;
  }
  if (!AllPackagesRegistered(required)) {
    return;
  }
  Assets::AssetListLock lock;
  pending_assets_.clear();
  MediaGetter getter(&pending_assets_);
  get(&getter);
  // Ready only once loaded; the pipeline is already on it, and
  // CheckPending flips us the moment it finishes.
  pending_ = true;
}

auto MediaBlock::CheckPending() -> bool {
  if (pending_ && AllLoaded(pending_assets_)) {
    pending_assets_.clear();
    pending_ = false;
    ready_ = true;
    return true;
  }
  return false;
}

auto MediaRetryPacer::Due(bool media_pending, millisecs_t now) -> bool {
  int64_t gen = g_base->assets->package_registry()->generation();
  if (media_pending || gen != last_registry_generation_
      || now - last_retry_ms_ > 1000) {
    last_registry_generation_ = gen;
    last_retry_ms_ = now;
    return true;
  }
  return false;
}

}  // namespace ballistica::base
