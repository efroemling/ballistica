// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_MEDIA_H_
#define BALLISTICA_MEDIA_MEDIA_H_

#include <map>
#include <string>
#include <vector>

#include "ballistica/core/context.h"
#include "ballistica/core/module.h"
#include "ballistica/core/object.h"

namespace ballistica {

/// Global media wrangling class.
class Media {
 public:
  static void Init();
  ~Media();

  /// Handy function to try to return a bit of media from a std::map
  /// of weak-refs, loading/adding it if need be.
  template <typename T>
  static auto GetMedia(std::map<std::string, Object::WeakRef<T> >* list,
                       const std::string& name, Scene* scene)
      -> Object::Ref<T> {
    assert(InGameThread());
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

  void AddPackage(const std::string& name, const std::string& path);
  void Prune(int level = 0);

  /// Finish loading any media that has been preloaded but still needs to be
  /// loaded by the proper thread.
  auto RunPendingLoadsGameThread() -> bool;

  /// Return true if audio loads remain to be done.
  auto RunPendingAudioLoads() -> bool;

  /// Return true if graphics loads remain to be done.
  auto RunPendingGraphicsLoads() -> bool;
  void ClearPendingLoadsDoneList();
  template <class T>
  auto RunPendingLoadList(std::vector<Object::Ref<T>*>* cList) -> bool;

  /// This function takes a newly allocated pointer which
  /// is deleted once the load is completed.
  void AddPendingLoad(Object::Ref<MediaComponentData>* c);
  struct PreloadRunnable;
  enum class FileType { kModel, kCollisionModel, kTexture, kSound, kData };
  auto FindMediaFile(FileType fileType, const std::string& file_in)
      -> std::string;

  /// Unload renderer-specific bits only (gl display lists, etc) - used when
  /// recreating/adjusting the renderer.
  void UnloadRendererBits(bool textures, bool models);

  /// Should be called from the game thread after UnloadRendererBits();
  /// kicks off bg loads for all existing unloaded media.
  void MarkAllMediaForLoad();
  void PrintLoadInfo();

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
  class MediaListsLock {
   public:
    MediaListsLock();
    ~MediaListsLock();
  };

  /// Load/cache media (make sure you hold a MediaListsLock).
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
    BA_PRECONDITION_FATAL(system_media_loaded_);  // Revert to assert later.
    assert(InGameThread());
    assert(static_cast<size_t>(id) < system_textures_.size());
    return system_textures_[static_cast<int>(id)].get();
  }
  auto GetCubeMapTexture(SystemCubeMapTextureID id) -> TextureData* {
    BA_PRECONDITION_FATAL(system_media_loaded_);  // Revert to assert later.
    assert(InGameThread());
    assert(static_cast<size_t>(id) < system_cube_map_textures_.size());
    return system_cube_map_textures_[static_cast<int>(id)].get();
  }
  auto GetSound(SystemSoundID id) -> SoundData* {
    BA_PRECONDITION_FATAL(system_media_loaded_);  // Revert to assert later.
    assert(InGameThread());
    assert(static_cast<size_t>(id) < system_sounds_.size());
    return system_sounds_[static_cast<int>(id)].get();
  }
  auto GetModel(SystemModelID id) -> ModelData* {
    BA_PRECONDITION_FATAL(system_media_loaded_);  // Revert to assert later.
    assert(InGameThread());
    assert(static_cast<size_t>(id) < system_models_.size());
    return system_models_[static_cast<int>(id)].get();
  }

  /// Load up hard-coded media for interface, etc.
  void LoadSystemMedia();

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
  struct PreloadRunnable : public Runnable {
    explicit PreloadRunnable(Object::Ref<MediaComponentData>* c_in) : c(c_in) {}
    void Run() override;
    Object::Ref<MediaComponentData>* c;
  };

 private:
  Media();
  static void MarkComponentForLoad(MediaComponentData* c);
  void LoadSystemTexture(SystemTextureID id, const char* name);
  void LoadSystemCubeMapTexture(SystemCubeMapTextureID id, const char* name);
  void LoadSystemSound(SystemSoundID id, const char* name);
  void LoadSystemData(SystemDataID id, const char* name);
  void LoadSystemModel(SystemModelID id, const char* name);

  template <class T>
  auto GetComponentPendingLoadCount(
      std::map<std::string, Object::Ref<T> >* t_list, MediaType type) -> int;

  template <class T>
  auto GetComponentData(const std::string& file_name,
                        std::map<std::string, Object::Ref<T> >* c_list)
      -> Object::Ref<T>;

  std::vector<std::string> media_paths_;
  bool have_pending_loads_[static_cast<int>(MediaType::kLast)]{};
  std::map<std::string, std::string> packages_;

  // For use by MediaListsLock; don't manually acquire
  std::mutex media_lists_mutex_;

  // Will be true while a MediaListsLock exists. Good to debug-verify this
  // during any media list access.
  bool media_lists_locked_{};

  // 'hard-wired' internal media
  bool system_media_loaded_{};
  std::vector<Object::Ref<TextureData> > system_textures_;
  std::vector<Object::Ref<TextureData> > system_cube_map_textures_;
  std::vector<Object::Ref<SoundData> > system_sounds_;
  std::vector<Object::Ref<DataData> > system_datas_;
  std::vector<Object::Ref<ModelData> > system_models_;

  // All existing media by filename (including internal).
  std::map<std::string, Object::Ref<TextureData> > textures_;
  std::map<std::string, Object::Ref<TextureData> > text_textures_;
  std::map<std::string, Object::Ref<TextureData> > qr_textures_;
  std::map<std::string, Object::Ref<ModelData> > models_;
  std::map<std::string, Object::Ref<SoundData> > sounds_;
  std::map<std::string, Object::Ref<DataData> > datas_;
  std::map<std::string, Object::Ref<CollideModelData> > collide_models_;

  // Components that have been preloaded but need to be loaded.
  std::mutex pending_load_list_mutex_;
  std::vector<Object::Ref<MediaComponentData>*> pending_loads_graphics_;
  std::vector<Object::Ref<MediaComponentData>*> pending_loads_sounds_;
  std::vector<Object::Ref<MediaComponentData>*> pending_loads_datas_;
  std::vector<Object::Ref<MediaComponentData>*> pending_loads_other_;
  std::vector<Object::Ref<MediaComponentData>*> pending_loads_done_;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_MEDIA_H_
