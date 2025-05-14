// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_HOST_ACTIVITY_H_
#define BALLISTICA_SCENE_V1_SUPPORT_HOST_ACTIVITY_H_

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/generic/timer_list.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

class HostActivity : public SceneV1Context {
 public:
  explicit HostActivity(HostSession* host_session);
  ~HostActivity() override;
  auto GetHostSession() -> HostSession* override;
  void SetGameSpeed(float speed);
  auto game_speed() const -> float { return game_speed_; }

  // ContextTarget time/timer support.
  auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                Runnable* runnable) -> int override;
  void DeleteTimer(TimeType timetype, int timer_id) override;
  auto GetTime(TimeType timetype) -> millisecs_t override;

  /// Return a NEW ref to the Python activity or nullptr if nonexistent.
  auto GetPyActivity() const -> PyObject*;

  // All these commands are propagated into the output stream
  // in addition to being applied locally.
  auto NewMaterial(const std::string& name) -> Object::Ref<Material>;
  auto GetTexture(const std::string& name)
      -> Object::Ref<SceneTexture> override;
  auto GetSound(const std::string& name) -> Object::Ref<SceneSound> override;
  auto GetData(const std::string& name) -> Object::Ref<SceneDataAsset> override;
  auto GetMesh(const std::string& name) -> Object::Ref<SceneMesh> override;
  auto GetCollisionMesh(const std::string& name)
      -> Object::Ref<SceneCollisionMesh> override;
  void StepDisplayTime(millisecs_t time_advance);
  auto base_time() const -> millisecs_t { return base_time_; }
  auto scene() -> Scene* {
    assert(scene_.exists());
    return scene_.get();
  }
  void Start();

  // A utility function; faster than dynamic_cast.
  auto GetAsHostActivity() -> HostActivity* override;
  auto GetMutableScene() -> Scene* override;
  void Draw(base::FrameDef* frame_def);
  void OnScreenSizeChange();
  void LanguageChanged();
  void DebugSpeedMultChanged();

  // Used to register python calls created in this context so we can make sure
  // they got properly cleaned up.
  void RegisterContextCall(base::PythonContextCall* call) override;
  auto shutting_down() const -> bool { return shutting_down_; }
  auto globals_node() const -> GlobalsNode*;
  void SetPaused(bool val);
  auto paused() const -> bool { return paused_; }
  void set_allow_kick_idle_players(bool val) { allow_kick_idle_players_ = val; }
  auto getAllowKickIdlePlayers() const -> bool {
    return allow_kick_idle_players_;
  }
  auto GetSceneStream() const -> SessionStream*;
  void DumpFullState(SessionStream* out);
  void SetGlobalsNode(GlobalsNode* node);
  void SetIsForeground(bool val);
  void RegisterPyActivity(PyObject* pyActivity);

 private:
  void HandleOutOfBoundsNodes();
  auto NewSimTimer(millisecs_t length, bool repeat, Runnable* runnable) -> int;
  void DeleteSimTimer(int timer_id);
  auto NewBaseTimer(millisecs_t length, bool repeat, Runnable* runnable) -> int;
  void DeleteBaseTimer(int timer_id);
  void UpdateStepTimerLength();
  void StepScene();
  void PruneSessionBaseTimers();

  /// Keep track of timers we've created in our session's base-timeline.
  std::vector<int> session_base_timer_ids_;
  Object::WeakRef<GlobalsNode> globals_node_;
  bool allow_kick_idle_players_{};
  int step_scene_timer_id_{};
  std::unordered_map<std::string, Object::WeakRef<SceneTexture> > textures_;
  std::unordered_map<std::string, Object::WeakRef<SceneSound> > sounds_;
  std::unordered_map<std::string, Object::WeakRef<SceneDataAsset> > datas_;
  std::unordered_map<std::string, Object::WeakRef<SceneCollisionMesh> >
      collision_meshes_;
  std::unordered_map<std::string, Object::WeakRef<SceneMesh> > meshes_;
  std::list<Object::WeakRef<Material> > materials_;
  bool shutting_down_{};

  // Our list of Python calls created in the context of this activity;
  // we clear them as we are shutting down and ensure nothing runs after
  // that point.
  std::list<Object::WeakRef<base::PythonContextCall> > context_calls_;
  millisecs_t next_prune_time_{};
  bool started_{};
  int out_of_bounds_in_a_row_{};
  bool paused_{};
  float game_speed_{1.0f};
  millisecs_t base_time_{};
  Object::Ref<Scene> scene_;
  Object::WeakRef<HostSession> host_session_;
  PythonRef py_activity_weak_ref_;
  TimerList scene_timers_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_HOST_ACTIVITY_H_
