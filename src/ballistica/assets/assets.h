// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_ASSETS_H_
#define BALLISTICA_ASSETS_ASSETS_H_

#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

/// Global assets wrangling class.
class Assets {
 public:
  Assets();

  /// Handy function to try to return an asset from a std::unordered_map
  /// of weak-refs, loading/adding it if need be.
  template <typename T>
  static auto GetAsset(
      std::unordered_map<std::string, Object::WeakRef<T> >* list,
      const std::string& name, Scene* scene) -> Object::Ref<T> {
    assert(InLogicThread());
    assert(list);
    auto i = list->find(name);

    // If we have an entry pointing to a live component, just return a new ref
    // to it.
    if (i != list->end() && i->second.exists()) {
      return Object::Ref<T>(i->second.get());
    } else {
      // Otherwise make a new one, pop a weak-ref on our list, and return a
      // strong-ref to it.
      auto t(Object::New<T>(name, scene));
      (*list)[name] = t;
      return t;
    }
  }

  auto AddPackage(const std::string& name, const std::string& path) -> void;
  auto Prune(int level = 0) -> void;

  /// Finish loading any assets that have been preloaded but still need to be
  /// loaded by the proper thread.
  auto RunPendingLoadsLogicThread() -> bool;

  /// Return true if audio loads remain to be done.
  auto RunPendingAudioLoads() -> bool;

  /// Return true if graphics loads remain to be done.
  auto RunPendingGraphicsLoads() -> bool;
  auto ClearPendingLoadsDoneList() -> void;
  template <class T>
  auto RunPendingLoadList(std::vector<Object::Ref<T>*>* cList) -> bool;

  /// This function takes a newly allocated pointer which
  /// is deleted once the load is completed.
  auto AddPendingLoad(Object::Ref<AssetComponentData>* c) -> void;
  enum class FileType { kModel, kCollisionModel, kTexture, kSound, kData };
  auto FindAssetFile(FileType fileType, const std::string& file_in)
      -> std::string;

  /// Unload renderer-specific bits only (gl display lists, etc) - used when
  /// recreating/adjusting the renderer.
  auto UnloadRendererBits(bool textures, bool models) -> void;

  /// Should be called from the logic thread after UnloadRendererBits();
  /// kicks off bg loads for all existing unloaded assets.
  auto MarkAllAssetsForLoad() -> void;
  auto PrintLoadInfo() -> void;

  auto GetModelPendingLoadCount() -> int;
  auto GetTexturePendingLoadCount() -> int;
  auto GetSoundPendingLoadCount() -> int;
  auto GetDataPendingLoadCount() -> int;
  auto GetCollideModelPendingLoadCount() -> int;

  /// Return the total number of graphics related pending loads.
  auto GetGraphicalPendingLoadCount() -> int;

  /// Return the total number of pending loads.
  auto GetPendingLoadCount() -> int;

  /// You must hold one of these locks while calling Get*Data() below.
  class AssetListLock {
   public:
    AssetListLock();
    ~AssetListLock();
  };

  /// Load/cache assets (make sure you hold a AssetListLock).
  auto GetTextureData(const std::string& file_name) -> Object::Ref<TextureData>;
  auto GetTextureData(TextPacker* packer) -> Object::Ref<TextureData>;
  auto GetTextureDataQRCode(const std::string& file_name)
      -> Object::Ref<TextureData>;
  auto GetCubeMapTextureData(const std::string& file_name)
      -> Object::Ref<TextureData>;
  auto GetModelData(const std::string& file_name) -> Object::Ref<ModelData>;
  auto GetSoundData(const std::string& file_name) -> Object::Ref<SoundData>;
  auto GetDataData(const std::string& file_name) -> Object::Ref<DataData>;
  auto GetCollideModelData(const std::string& file_name)
      -> Object::Ref<CollideModelData>;

  // Get system assets.
  auto GetTexture(SystemTextureID id) -> TextureData* {
    BA_PRECONDITION_FATAL(system_assets_loaded_);  // Revert to assert later.
    assert(InLogicThread());
    assert(static_cast<size_t>(id) < system_textures_.size());
    return system_textures_[static_cast<int>(id)].get();
  }
  auto GetCubeMapTexture(SystemCubeMapTextureID id) -> TextureData* {
    BA_PRECONDITION_FATAL(system_assets_loaded_);  // Revert to assert later.
    assert(InLogicThread());
    assert(static_cast<size_t>(id) < system_cube_map_textures_.size());
    return system_cube_map_textures_[static_cast<int>(id)].get();
  }
  auto GetSound(SystemSoundID id) -> SoundData* {
    BA_PRECONDITION_FATAL(system_assets_loaded_);  // Revert to assert later.
    assert(InLogicThread());
    assert(static_cast<size_t>(id) < system_sounds_.size());
    return system_sounds_[static_cast<int>(id)].get();
  }
  auto GetModel(SystemModelID id) -> ModelData* {
    BA_PRECONDITION_FATAL(system_assets_loaded_);  // Revert to assert later.
    assert(InLogicThread());
    assert(static_cast<size_t>(id) < system_models_.size());
    return system_models_[static_cast<int>(id)].get();
  }

  /// Load up hard-coded assets for interface, etc.
  auto LoadSystemAssets() -> void;

  auto total_model_count() const -> uint32_t {
    return static_cast<uint32_t>(models_.size());
  }
  auto total_texture_count() const -> uint32_t {
    return static_cast<uint32_t>(textures_.size() + text_textures_.size()
                                 + qr_textures_.size());
  }
  auto total_sound_count() const -> uint32_t {
    return static_cast<uint32_t>(sounds_.size());
  }
  auto total_collide_model_count() const -> uint32_t {
    return static_cast<uint32_t>(collide_models_.size());
  }

 private:
  static auto MarkComponentForLoad(AssetComponentData* c) -> void;
  auto LoadSystemTexture(SystemTextureID id, const char* name) -> void;
  auto LoadSystemCubeMapTexture(SystemCubeMapTextureID id, const char* name)
      -> void;
  auto LoadSystemSound(SystemSoundID id, const char* name) -> void;
  auto LoadSystemData(SystemDataID id, const char* name) -> void;
  auto LoadSystemModel(SystemModelID id, const char* name) -> void;

  template <class T>
  auto GetComponentPendingLoadCount(
      std::unordered_map<std::string, Object::Ref<T> >* t_list, AssetType type)
      -> int;

  template <class T>
  auto GetComponentData(
      const std::string& file_name,
      std::unordered_map<std::string, Object::Ref<T> >* c_list)
      -> Object::Ref<T>;

  std::vector<std::string> asset_paths_;
  bool have_pending_loads_[static_cast<int>(AssetType::kLast)]{};
  std::unordered_map<std::string, std::string> packages_;

  // For use by AssetListLock; don't manually acquire
  std::mutex asset_lists_mutex_;

  // Will be true while a AssetListLock exists. Good to debug-verify this
  // during any asset list access.
  bool asset_lists_locked_{};

  // 'hard-wired' internal assets
  bool system_assets_loaded_{};
  std::vector<Object::Ref<TextureData> > system_textures_;
  std::vector<Object::Ref<TextureData> > system_cube_map_textures_;
  std::vector<Object::Ref<SoundData> > system_sounds_;
  std::vector<Object::Ref<DataData> > system_datas_;
  std::vector<Object::Ref<ModelData> > system_models_;

  // All existing assets by filename (including internal).
  std::unordered_map<std::string, Object::Ref<TextureData> > textures_;
  std::unordered_map<std::string, Object::Ref<TextureData> > text_textures_;
  std::unordered_map<std::string, Object::Ref<TextureData> > qr_textures_;
  std::unordered_map<std::string, Object::Ref<ModelData> > models_;
  std::unordered_map<std::string, Object::Ref<SoundData> > sounds_;
  std::unordered_map<std::string, Object::Ref<DataData> > datas_;
  std::unordered_map<std::string, Object::Ref<CollideModelData> >
      collide_models_;

  // Components that have been preloaded but need to be loaded.
  std::mutex pending_load_list_mutex_;
  std::vector<Object::Ref<AssetComponentData>*> pending_loads_graphics_;
  std::vector<Object::Ref<AssetComponentData>*> pending_loads_sounds_;
  std::vector<Object::Ref<AssetComponentData>*> pending_loads_datas_;
  std::vector<Object::Ref<AssetComponentData>*> pending_loads_other_;
  std::vector<Object::Ref<AssetComponentData>*> pending_loads_done_;
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_ASSETS_H_
