// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_MEDIA_BLOCK_H_
#define BALLISTICA_BASE_SUPPORT_MEDIA_BLOCK_H_

#include <functional>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

/// One asset reference in a server-authored definition (a character, a
/// depiction). Two wire forms: a full (apverid, name) spec, or a flat
/// integer index into the enclosing block's package manifest; indexed
/// refs get their apverid/name filled in at media-load time once the
/// manifest's packages are registered locally.
struct PackageAssetRef {
  std::string apverid;
  std::string name;
  int64_t index{-1};
  auto present() const -> bool { return !name.empty() || index >= 0; }
};

/// Read a ref in either wire form: a bacommon.assetspec spec object
/// ({"a": apverid, "n": logical-name}) or a flat integer index. False
/// if the key is missing or malformed.
auto ReadPackageAssetRef(const JsonRef& obj, const char* key,
                         PackageAssetRef* out) -> bool;

/// Read an array of refs (malformed entries are skipped).
void ReadPackageAssetRefs(const JsonRef& obj, const char* key,
                          std::vector<PackageAssetRef>* out);

/// Read a block's package manifest ('pk') and the producer's digest of
/// the index domain laid out over it ('dg'; empty if none sent).
void ReadPackageManifest(const JsonRef& obj, std::vector<std::string>* out,
                         std::string* digest);

/// Hands out package asset handles for a media block and remembers
/// every texture and mesh it handed out, so "is all of this loaded?" is
/// answered from the same list the handles came from -- a new media
/// field cannot be missed by the check, because obtaining its handle is
/// what registers it. Sounds are handed out but not tracked: they load
/// on demand on the audio thread and never affect the look.
class MediaGetter {
 public:
  explicit MediaGetter(std::vector<Object::Ref<Asset>>* pending);
  auto Texture(const PackageAssetRef& ref) -> Object::Ref<TextureAsset>;
  auto Mesh(const PackageAssetRef& ref) -> Object::Ref<MeshAsset>;
  auto Sound(const PackageAssetRef& ref) -> Object::Ref<SoundAsset>;

 private:
  std::vector<Object::Ref<Asset>>* pending_;
};

/// One self-contained block of media in a definition (a character's
/// icon, its spaz form, an image depiction's textures): the standin
/// rule in one place.
///
/// A block is *ready* only once every texture and mesh it references is
/// fully loaded -- flipping earlier would make the renderer inline-load
/// them on the graphics thread (a hitch); holders draw a standin until
/// then. Getting there takes two things this handles: every referenced
/// package registered locally (packages that aren't are noted as wanted,
/// so the background acquirer fetches them -- character-skins.md, lazy
/// media), and the asset pipeline finishing the loads.
///
/// Composition, not a base class: definitions hold one block per
/// component. Logic thread only.
class MediaBlock {
 public:
  /// A ref still needing (apverid, name) filled in from the manifest,
  /// plus the logical-path prefix its slot's asset kind demands.
  using IndexedRef = std::pair<PackageAssetRef*, const char*>;

  /// Note a ref as needing index resolution, if it is in indexed form.
  static void NoteIndexed(PackageAssetRef* ref, const char* prefix,
                          std::vector<IndexedRef>* refs);

  /// Try to acquire the block's media: decode ``indexed`` refs against
  /// the manifest, require every package ``required`` names to be
  /// registered (noting missing ones as wanted), then call ``get``
  /// under the asset-list lock to take handles. Leaves the block
  /// pending (handles held, loads in flight) or untouched if something
  /// isn't available yet. A no-op once pending or ready.
  void Load(const std::vector<std::string>& packages,
            const std::string& domain_digest,
            const std::vector<IndexedRef>& indexed,
            const std::vector<const PackageAssetRef*>& required,
            const std::function<void(MediaGetter* get)>& get);

  /// Flip pending -> ready if every handed-out asset has loaded.
  /// Returns true if it flipped (so a holder can swap its look).
  auto CheckPending() -> bool;

  auto ready() const -> bool { return ready_; }

  /// Handles held, waiting on the asset pipeline (see Load).
  auto pending() const -> bool { return pending_; }

 private:
  bool ready_{};
  bool pending_{};
  std::vector<Object::Ref<Asset>> pending_assets_;
};

/// Paces a holder's media retries (see CharacterDef::RetryMedia).
///
/// Retry the moment the package registry moved (a background
/// acquisition landed -- an int compare, so free when nothing changes),
/// every frame/step while media is pending on the asset pipeline (a few
/// atomic reads), and otherwise on a slow cadence that keeps missing
/// packages noted as wanted (interest expires if nobody re-notes it).
class MediaRetryPacer {
 public:
  /// Whether a holder whose media isn't ready should retry now.
  /// ``now`` is any millisecond clock the holder steps on.
  auto Due(bool media_pending, millisecs_t now) -> bool;

 private:
  int64_t last_registry_generation_{-1};
  millisecs_t last_retry_ms_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_MEDIA_BLOCK_H_
