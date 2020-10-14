// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_HOST_ACTIVITY_H_
#define BALLISTICA_GAME_HOST_ACTIVITY_H_

#include <list>
#include <map>
#include <string>

#include "ballistica/core/context.h"
#include "ballistica/generic/timer_list.h"
#include "ballistica/python/python_ref.h"

namespace ballistica {

class HostActivity : public ContextTarget {
 public:
  explicit HostActivity(HostSession* host_session);
  ~HostActivity() override;
  auto GetHostSession() -> HostSession* override;
  auto SetGameSpeed(float speed) -> void;
  auto game_speed() const -> float { return game_speed_; }

  // ContextTarget time/timer support.
  auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> int override;
  auto DeleteTimer(TimeType timetype, int timer_id) -> void override;
  auto GetTime(TimeType timetype) -> millisecs_t override;

  /// Return a borrowed ref to the python activity; Py_None if nonexistent.
  auto GetPyActivity() const -> PyObject*;

  // All these commands are propagated into the output stream
  // in addition to being applied locally.
  auto NewMaterial(const std::string& name) -> Object::Ref<Material>;
  auto GetTexture(const std::string& name) -> Object::Ref<Texture> override;
  auto GetSound(const std::string& name) -> Object::Ref<Sound> override;
  auto GetData(const std::string& name) -> Object::Ref<Data> override;
  auto GetModel(const std::string& name) -> Object::Ref<Model> override;
  auto GetCollideModel(const std::string& name)
      -> Object::Ref<CollideModel> override;
  auto Update(millisecs_t time_advance) -> millisecs_t;
  auto base_time() const -> millisecs_t { return base_time_; }
  auto scene() -> Scene* {
    assert(scene_.exists());
    return scene_.get();
  }
  auto start() -> void;

  // A utility function; faster than dynamic_cast.
  auto GetAsHostActivity() -> HostActivity* override;
  auto GetMutableScene() -> Scene* override;
  auto Draw(FrameDef* frame_def) -> void;
  auto ScreenSizeChanged() -> void;
  auto LanguageChanged() -> void;
  auto DebugSpeedMultChanged() -> void;
  auto GraphicsQualityChanged(GraphicsQuality q) -> void;

  // Used to register python calls created in this context so we can make sure
  // they got properly cleaned up.
  auto RegisterCall(PythonContextCall* call) -> void;
  auto shutting_down() const -> bool { return shutting_down_; }
  auto globals_node() const -> GlobalsNode*;
  auto SetPaused(bool val) -> void;
  auto paused() const -> bool { return paused_; }
  auto set_allow_kick_idle_players(bool val) -> void {
    allow_kick_idle_players_ = val;
  }
  auto getAllowKickIdlePlayers() const -> bool {
    return allow_kick_idle_players_;
  }
  auto GetGameStream() const -> GameStream*;
  auto DumpFullState(GameStream* out) -> void;
  auto SetGlobalsNode(GlobalsNode* node) -> void;
  auto SetIsForeground(bool val) -> void;
  auto RegisterPyActivity(PyObject* pyActivity) -> void;

 private:
  auto HandleOutOfBoundsNodes() -> void;
  auto NewSimTimer(millisecs_t length, bool repeat,
                   const Object::Ref<Runnable>& runnable) -> int;
  auto DeleteSimTimer(int timer_id) -> void;
  auto NewBaseTimer(millisecs_t length, bool repeat,
                    const Object::Ref<Runnable>& runnable) -> int;
  auto DeleteBaseTimer(int timer_id) -> void;
  auto UpdateStepTimerLength() -> void;
  auto StepScene() -> void;

  Object::WeakRef<GlobalsNode> globals_node_;
  bool allow_kick_idle_players_ = false;
  Timer* step_scene_timer_ = nullptr;
  std::map<std::string, Object::WeakRef<Texture> > textures_;
  std::map<std::string, Object::WeakRef<Sound> > sounds_;
  std::map<std::string, Object::WeakRef<Data> > datas_;
  std::map<std::string, Object::WeakRef<CollideModel> > collide_models_;
  std::map<std::string, Object::WeakRef<Model> > models_;
  std::list<Object::WeakRef<Material> > materials_;
  bool shutting_down_ = false;

  // Our list of python calls created in the context of this activity;
  // we clear them as we are shutting down and ensure nothing runs after
  // that point.
  std::list<Object::WeakRef<PythonContextCall> > python_calls_;
  millisecs_t next_prune_time_ = 0;
  bool _started = false;
  int out_of_bounds_in_a_row_ = 0;
  bool paused_ = false;
  float game_speed_ = 0.0f;
  millisecs_t base_time_ = 0;
  Object::Ref<Scene> scene_;
  Object::WeakRef<HostSession> host_session_;
  PythonRef py_activity_weak_ref_;

  // Want this at the bottom so it dies first since this may cause Python
  // stuff to access us.
  TimerList sim_timers_;
  TimerList base_timers_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_HOST_ACTIVITY_H_
