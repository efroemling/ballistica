// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSETS_H_
#define BALLISTICA_BASE_ASSETS_ASSETS_H_

#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/assets/asset_package_registry.h"
#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// Global assets wrangling class.
class Assets {
 public:
  Assets();

  void AddPackage(const std::string& name, const std::string& path);
  void Prune(int level = 0);

  /// Finish loading any assets that have been preloaded but still need to be
  /// loaded by the proper thread.
  auto RunPendingLoadsLogicThread() -> bool;

  /// Return true if audio loads remain to be done.
  auto RunPendingAudioLoads() -> bool;

  /// Return true if graphics loads remain to be done.
  auto RunPendingGraphicsLoads() -> bool;
  void ClearPendingLoadsDoneList();
  template <typename T>
  auto RunPendingLoadList(std::vector<Object::Ref<T>*>* assets) -> bool;

  /// This function takes a newly allocated pointer which
  /// is deleted once the load is completed.
  void AddPendingLoad(Object::Ref<Asset>* c);
  enum class FileType { kMesh, kCollisionMesh, kTexture, kSound, kData };
  auto FindAssetFile(FileType fileType, const std::string& file_in)
      -> std::string;

  /// Unload renderer-specific bits only (gl display lists, etc) - used when
  /// recreating/adjusting the renderer.
  void UnloadRendererBits(bool textures, bool meshes);

  /// Phase 1 (logic thread): re-resolve loaded textures/meshes and flag any
  /// whose underlying CAS blob changed (e.g. fallback -> ideal flavor after a
  /// downloading asset-package resolve), then kick off the graphics-thread
  /// unload/reload. No-op when nothing changed. Entry point for the
  /// reload_changed_media binding.
  void ReloadChangedAssets();

  /// Phase 2 (graphics thread): unload the renderer assets flagged for reload
  /// by ReloadChangedAssets(). Returns whether anything was unloaded; if so
  /// the caller MarkAllAssetsForLoad()s + draws a progress bar (see
  /// GraphicsServer::ReloadChangedMedia_).
  auto UnloadReloadPendingRendererBits() -> bool;

  /// Should be called from the logic thread after UnloadRendererBits();
  /// kicks off bg loads for all existing unloaded assets.
  void MarkAllAssetsForLoad();
  void PrintLoadInfo();

  auto GetMeshPendingLoadCount() -> int;
  auto GetTexturePendingLoadCount() -> int;
  auto GetSoundPendingLoadCount() -> int;
  auto GetDataPendingLoadCount() -> int;
  auto GetCollisionMeshPendingLoadCount() -> int;

  /// Return the total number of graphics related pending loads.
  auto GetGraphicalPendingLoadCount() -> int;

  /// Return the total number of pending loads.
  auto GetPendingLoadCount() -> int;

  /// You must hold one of these locks while calling GetXXX() below.
  class AssetListLock {
   public:
    AssetListLock();
    ~AssetListLock();
  };

  /// Enable asset-loads and start loading sys-assets.
  void StartLoading();

  // Get system assets. These are loaded at startup so are always instantly
  // available.
  auto BuiltinCubeMapTextureOld(BuiltinCubeMapTextureOldID id) -> TextureAsset*;
  auto IsValidBuiltinSoundOld(BuiltinSoundOldID id) -> bool;
  auto BuiltinSoundOld(BuiltinSoundOldID id) -> SoundAsset*;
  auto BuiltinMeshOld(BuiltinMeshOldID id) -> MeshAsset*;

  // Same as above but for the new CAS-backed asset-package path. Enum
  // values + load-bindings are generated from the projectconfig
  // ``"assets"`` package by tools/batools/builtinassetids.py.
  auto BuiltinTexture(BuiltinTextureID id) -> TextureAsset*;
  auto BuiltinCubeMapTexture(BuiltinCubeMapTextureID id) -> TextureAsset*;
  auto IsValidBuiltinSound(BuiltinSoundID id) -> bool;
  auto BuiltinSound(BuiltinSoundID id) -> SoundAsset*;
  auto BuiltinMesh(BuiltinMeshID id) -> MeshAsset*;

  /// Load/cache custom assets. Make sure you hold a AssetListLock.
  auto GetTexture(const std::string& file_name) -> Object::Ref<TextureAsset>;
  auto GetTexture(TextPacker* packer) -> Object::Ref<TextureAsset>;
  auto GetQRCodeTexture(const std::string& url) -> Object::Ref<TextureAsset>;
  auto GetCubeMapTexture(const std::string& file_name)
      -> Object::Ref<TextureAsset>;
  auto GetMesh(const std::string& file_name) -> Object::Ref<MeshAsset>;
  auto GetSound(const std::string& file_name) -> Object::Ref<SoundAsset>;
  auto GetDataAsset(const std::string& file_name) -> Object::Ref<DataAsset>;
  auto GetCollisionMesh(const std::string& file_name)
      -> Object::Ref<CollisionMeshAsset>;

  auto total_mesh_count() const -> uint32_t {
    return static_cast<uint32_t>(meshes_.size());
  }
  auto total_texture_count() const -> uint32_t {
    return static_cast<uint32_t>(textures_.size() + text_textures_.size()
                                 + qr_textures_.size());
  }
  auto total_sound_count() const -> uint32_t {
    return static_cast<uint32_t>(sounds_.size());
  }
  auto total_collision_mesh_count() const -> uint32_t {
    return static_cast<uint32_t>(collision_meshes_.size());
  }

  // Text & Language (need to mold this into more asset-like concepts).
  void SetLanguageKeys(
      const std::unordered_map<std::string, std::string>& language);
  auto GetResourceString(const std::string& key) -> std::string;
  auto CharStr(SpecialChar id) -> std::string;
  auto CompileResourceString(const std::string& s, bool* valid = nullptr)
      -> std::string;

  auto sys_assets_loaded() const { return sys_assets_loaded_; }

  auto language_state() const { return language_state_; }

  auto asset_loads_allowed() const { return asset_loads_allowed_; }

  /// In-memory CAS manifest registry for asset-packages. Populated
  /// at startup from the bundled ``manifest.json``; queried on the
  /// hot path by ``gettexture`` and friends when given a qualified
  /// ``<apverid>:<asset_name>`` ref.
  auto package_registry() -> AssetPackageRegistry* {
    return &package_registry_;
  }

  /// The texture *profile* name this build should request for
  /// asset-package resolves (the ``<profile>`` in a
  /// ``textures/<profile>_<quality>`` bucket coord). This is the native
  /// home for texture-format/preference policy (initiative:
  /// asset-packages §7); the Python asset-subsystem reads it to form its
  /// resolve dimensions, so fetch-dims track GPU capability without the
  /// subsystem needing format knowledge.
  ///
  /// Returns ``"null"`` in headless (no renderer; only the NULL flavor is
  /// bundled/needed). Otherwise selects by form factor first, then GPU
  /// capability: desktop (Mac/Windows/Linux) → ``"desktop_v1"`` (BC7) else
  /// ``"fallback_v1"``; mobile (Android/iOS/tvOS) → ``"mobile_v1"`` (ASTC)
  /// else ``"fallback_v1"``. Form factor (not raw format support) picks the
  /// flavor family because a flavor bundles more than its compression
  /// (resolution, etc.). ``BA_FORCE_TEXTURE_PROFILE`` hard-pins the result;
  /// ``BA_FORCE_TEXTURE_FORM_FACTOR=mobile|desktop`` runs the other family's
  /// branch (caps still consulted) for on-desktop testing of the mobile
  /// path. See the implementation.
  auto PreferredTextureProfile() const -> std::string;

  /// Resolve one *part* of a texture qualified-ref (``<apverid>:<name>``)
  /// to its CAS blob path. Textures are single-part today — part ``"t"``
  /// is the texture-data component (the placeholder ``"j"`` sidecar was
  /// dropped; see decision #16 follow-up). The part argument is kept
  /// general so multi-file logical assets (e.g. fonts: atlas + metrics)
  /// can pull individual component files. Returns ``""`` if the name isn't
  /// a CAS ref, the part is absent, or in headless mode. A transitional
  /// seam until the full AssetLayout resolve (decision #16, shape b) lands.
  auto FindCasTexturePartPath(const std::string& name, const std::string& part)
      -> std::string;

 private:
  /// Resolve a qualified-ref name (``<apverid>:<asset_name>``) into a
  /// CAS blob path via :class:`AssetPackageRegistry`. Called from the
  /// top of :meth:`FindAssetFile` when a ``:`` is detected — bare
  /// names continue on the legacy filename-on-disk path. ``colon_pos``
  /// is the location of the first ``:`` in ``name``, hoisted by the
  /// caller to avoid a redundant find.
  auto FindAssetFileCas_(FileType type, const std::string& name,
                         size_t colon_pos) -> std::string;

  static void MarkAssetForLoad(Asset* c);
  void LoadBuiltinCubeMapTextureOld(BuiltinCubeMapTextureOldID id,
                                    const char* name);
  void LoadBuiltinSoundOld(BuiltinSoundOldID id, const char* name);
  void LoadSystemData(SystemDataID id, const char* name);
  void LoadBuiltinMeshOld(BuiltinMeshOldID id, const char* name);
  // CAS-backed builtin loaders; called from the autogen section
  // inside ``Assets::StartLoading()``. ``name`` is the
  // qualified-ref form ``<apverid>:<logical_name>`` baked in by
  // the generator (see tools/batools/builtinassetids.py).
  void LoadBuiltinTexture(BuiltinTextureID id, const char* name);
  void LoadBuiltinCubeMapTexture(BuiltinCubeMapTextureID id, const char* name);
  void LoadBuiltinSound(BuiltinSoundID id, const char* name);
  void LoadBuiltinMesh(BuiltinMeshID id, const char* name);
  void InitSpecialChars();

  template <typename T>
  auto GetAssetPendingLoadCount(
      std::unordered_map<std::string, Object::Ref<T> >* t_list, AssetType type)
      -> int;

  template <typename T>
  auto GetAsset(const std::string& file_name,
                std::unordered_map<std::string, Object::Ref<T> >* c_list)
      -> Object::Ref<T>;

  int language_state_{};
  bool have_pending_loads_[static_cast<int>(AssetType::kLast)]{};

  // Will be true while a AssetListLock exists. Good to debug-verify this
  // during any asset list access.
  bool asset_lists_locked_{};
  bool asset_loads_allowed_{};
  bool sys_assets_loaded_{};

  std::vector<std::string> asset_paths_;
  std::unordered_map<std::string, std::string> packages_;
  AssetPackageRegistry package_registry_;

  // For use by AssetListLock; don't manually acquire.
  std::mutex asset_lists_mutex_;

  std::vector<Object::Ref<TextureAsset> > builtin_cube_map_textures_old_;
  std::vector<Object::Ref<SoundAsset> > builtin_sounds_old_;
  std::vector<Object::Ref<DataAsset> > system_datas_;
  std::vector<Object::Ref<MeshAsset> > builtin_meshes_old_;

  std::vector<Object::Ref<TextureAsset> > builtin_textures_;
  std::vector<Object::Ref<TextureAsset> > builtin_cube_map_textures_;
  std::vector<Object::Ref<SoundAsset> > builtin_sounds_;
  std::vector<Object::Ref<MeshAsset> > builtin_meshes_;

  // All existing assets by filename (including internal).
  std::unordered_map<std::string, Object::Ref<TextureAsset> > textures_;
  std::unordered_map<std::string, Object::Ref<TextureAsset> > text_textures_;
  std::unordered_map<std::string, Object::Ref<TextureAsset> > qr_textures_;
  std::unordered_map<std::string, Object::Ref<MeshAsset> > meshes_;
  std::unordered_map<std::string, Object::Ref<SoundAsset> > sounds_;
  std::unordered_map<std::string, Object::Ref<DataAsset> > datas_;
  std::unordered_map<std::string, Object::Ref<CollisionMeshAsset> >
      collision_meshes_;

  // Components that have been preloaded but need to be loaded.
  std::mutex pending_load_list_mutex_;
  std::vector<Object::Ref<Asset>*> pending_loads_graphics_;
  std::vector<Object::Ref<Asset>*> pending_loads_sounds_;
  std::vector<Object::Ref<Asset>*> pending_loads_datas_;
  std::vector<Object::Ref<Asset>*> pending_loads_other_;
  std::vector<Object::Ref<Asset>*> pending_loads_done_;

  // Text & Language (need to mold this into more asset-like concepts).
  std::mutex language_mutex_;
  std::unordered_map<std::string, std::string> language_;
  std::mutex special_char_mutex_;
  std::unordered_map<SpecialChar, std::string> special_char_strings_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSETS_H_
