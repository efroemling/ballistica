// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_LOCAL_SCENE_CONTEXT_H_
#define BALLISTICA_SCENE_V1_SUPPORT_LOCAL_SCENE_CONTEXT_H_

#include <list>
#include <string>
#include <unordered_map>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/generic/timer_list.h"

namespace ballistica::scene_v1 {

/// A self-contained scene context whose contents exist on this machine
/// only.
///
/// This is essentially a HostActivity stripped down to just the parts
/// needed to run local-only content: it owns a Scene that is never
/// attached to a session stream (so nothing created in it is ever sent
/// to clients or written to replays), sim-time timers, per-context
/// asset maps, and the materials, spaz defs and depictions made in it.
/// It does nothing on its own; whatever owns one steps and draws it.
///
/// Things built on this: LocalDisplayContext (per-machine displays
/// owned by a node in some other scene) and SceneViewerContext (scenes
/// drawn to a texture for display in ui).
class LocalSceneContext : public SceneV1Context {
 public:
  /// Create with our scene's clock starting at a given time and its
  /// simulation behaving as under a given scene-stream protocol.
  LocalSceneContext(millisecs_t start_time, int protocol_version);
  ~LocalSceneContext() override;

  auto GetMutableScene() -> Scene* override;

  // Timer support (sim time only; it advances as our scene steps).
  auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                Runnable* runnable) -> int override;
  void DeleteTimer(TimeType timetype, int timer_id) override;
  auto GetTime(TimeType timetype) -> millisecs_t override;

  auto GetTexture(const std::string& name)
      -> Object::Ref<SceneTexture> override;
  auto GetSound(const std::string& name) -> Object::Ref<SceneSound> override;
  auto GetData(const std::string& name) -> Object::Ref<SceneDataAsset> override;
  auto GetMesh(const std::string& name) -> Object::Ref<SceneMesh> override;
  auto GetCollisionMesh(const std::string& name)
      -> Object::Ref<SceneCollisionMesh> override;
  auto NewMaterial(const std::string& name) -> Object::Ref<Material> override;
  auto NewSpazDef(const std::string& json) -> Object::Ref<SpazDef> override;
  auto NewDepiction(const std::string& json)
      -> Object::Ref<SceneDepiction> override;

  void RegisterContextCall(base::PythonContextCall* call) override;

  /// Run our timers and step our scene once.
  void Step();

  /// Draw our scene.
  void Draw(base::FrameDef* frame_def);

  void OnScreenSizeChange();
  void LanguageChanged();

  /// Tear everything down: kill context calls, mark assets dead, clear
  /// timers and the scene. After this, timer/node creation is refused.
  void Shutdown();

  auto shutting_down() const -> bool { return shutting_down_; }

  auto scene() -> Scene* {
    assert(scene_.exists());
    return scene_.get();
  }

 private:
  bool shutting_down_{};
  Object::Ref<Scene> scene_;
  TimerList scene_timers_;
  std::unordered_map<std::string, Object::WeakRef<SceneTexture> > textures_;
  std::unordered_map<std::string, Object::WeakRef<SceneSound> > sounds_;
  std::unordered_map<std::string, Object::WeakRef<SceneDataAsset> > datas_;
  std::unordered_map<std::string, Object::WeakRef<SceneCollisionMesh> >
      collision_meshes_;
  std::unordered_map<std::string, Object::WeakRef<SceneMesh> > meshes_;
  std::list<Object::WeakRef<Material> > materials_;
  std::list<Object::WeakRef<SpazDef> > spaz_defs_;
  std::list<Object::WeakRef<SceneDepiction> > depictions_;
  std::list<Object::WeakRef<base::PythonContextCall> > context_calls_;
  millisecs_t next_prune_time_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_LOCAL_SCENE_CONTEXT_H_
