// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSETS_H_
#define BALLISTICA_BASE_ASSETS_ASSETS_H_

#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

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
  auto SysTexture(SysTextureID id) -> TextureAsset*;
  auto SysCubeMapTexture(SysCubeMapTextureID id) -> TextureAsset*;
  auto IsValidSysSound(SysSoundID id) -> bool;
  auto SysSound(SysSoundID id) -> SoundAsset*;
  auto SysMesh(SysMeshID id) -> MeshAsset*;

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

 private:
  static void MarkAssetForLoad(Asset* c);
  void LoadSystemTexture(SysTextureID id, const char* name);
  void LoadSystemCubeMapTexture(SysCubeMapTextureID id, const char* name);
  void LoadSystemSound(SysSoundID id, const char* name);
  void LoadSystemData(SystemDataID id, const char* name);
  void LoadSystemMesh(SysMeshID id, const char* name);
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

  // For use by AssetListLock; don't manually acquire.
  std::mutex asset_lists_mutex_;

  std::vector<Object::Ref<TextureAsset> > system_textures_;
  std::vector<Object::Ref<TextureAsset> > system_cube_map_textures_;
  std::vector<Object::Ref<SoundAsset> > system_sounds_;
  std::vector<Object::Ref<DataAsset> > system_datas_;
  std::vector<Object::Ref<MeshAsset> > system_meshes_;

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
