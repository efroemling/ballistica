// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_HOST_SESSION_H_
#define BALLISTICA_SCENE_V1_SUPPORT_HOST_SESSION_H_

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/support/context.h"
#include "ballistica/scene_v1/support/session.h"
#include "ballistica/shared/generic/timer_list.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::scene_v1 {

class HostSession : public Session {
 public:
  explicit HostSession(PyObject* session_type_obj);
  ~HostSession() override;

  // Return a borrowed python ref.
  auto GetSessionPyObj() const -> PyObject* { return session_py_obj_.Get(); }

  // Set focus to a Context (it must belong to this session).
  void SetForegroundHostActivity(HostActivity* sgc);
  auto GetSound(const std::string& name) -> Object::Ref<SceneSound> override;
  auto GetData(const std::string& name) -> Object::Ref<SceneDataAsset> override;
  auto GetTexture(const std::string& name)
      -> Object::Ref<SceneTexture> override;
  auto GetMesh(const std::string& name) -> Object::Ref<SceneMesh> override;

  void SetKickIdlePlayers(bool enable);

  // Update the session.
  void Update(int time_advance_millisecs, double time_advance) override;

  // ContextTarget time/timer support
  auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                Runnable* runnable) -> int override;
  void DeleteTimer(TimeType timetype, int timer_id) override;
  auto GetTime(TimeType timetype) -> millisecs_t override;

  void SetBaseTimerLength(int timer_id, int length) {
    if (shutting_down_) {
      return;
    }
    auto* timer = base_timers_.GetTimer(timer_id);
    assert(timer);
    if (!timer) {
      return;
    }
    timer->SetLength(length, true, base_time_millisecs_);
  }
  auto BaseTimerExists(int timer_id) -> bool {
    return base_timers_.GetTimer(timer_id) != nullptr;
  }
  // Given an activity python type, instantiate a new activity
  // and return a new reference.
  auto NewHostActivity(PyObject* activity_type_obj, PyObject* settings_obj)
      -> PyObject*;
  void DestroyHostActivity(HostActivity* a);
  void RemovePlayer(Player* player);
  void RequestPlayer(SceneV1InputDeviceDelegate* device);

  // Return either a host-activity context or the session-context.
  auto GetForegroundContext() -> base::ContextRef override;
  auto DoesFillScreen() const -> bool override;
  void Draw(base::FrameDef* f) override;
  void OnScreenSizeChange() override;
  void LanguageChanged() override;
  void DebugSpeedMultChanged() override;
  auto GetHostSession() -> HostSession* override;
  auto GetMutableScene() -> Scene* override;
  auto scene() -> Scene* {
    assert(scene_.Exists());
    return scene_.Get();
  }
  void RegisterContextCall(base::PythonContextCall* call) override;
  auto GetSceneStream() const -> SessionStream* { return output_stream_.Get(); }
  auto is_main_menu() const -> bool {
    return is_main_menu_;
  }  // fixme remove this
  void DumpFullState(SessionStream* out) override;
  void GetCorrectionMessages(bool blend,
                             std::vector<std::vector<uint8_t> >* messages);
  auto base_time() const -> millisecs_t { return base_time_millisecs_; }
  auto players() const -> const std::vector<Object::Ref<Player> >& {
    return players_;
  }

  // Called by new py Session to pass themselves to us.
  void RegisterPySession(PyObject* obj);

  // Called by new py Activities to pass themselves to us.
  auto RegisterPyActivity(PyObject* activity_obj) -> HostActivity*;

  // New HostActivities should call this in their constructors.
  void AddHostActivity(HostActivity* sgc);

  auto GetUnusedPlayerName(Player* p, const std::string& base_name)
      -> std::string;
  auto ContextAllowsDefaultTimerTypes() -> bool override;
  auto TimeToNextEvent() -> std::optional<microsecs_t> override;

 private:
  void StepScene();
  void ProcessPlayerTimeOuts();
  void DecrementPlayerTimeOuts(millisecs_t millisecs);
  void IssuePlayerLeft(Player* player);

  bool is_main_menu_;  // FIXME: Remove this.
  Object::Ref<SessionStream> output_stream_;
  Timer* step_scene_timer_;
  millisecs_t base_time_millisecs_{};
  TimerList sim_timers_;
  TimerList base_timers_;
  Object::Ref<Scene> scene_;
  bool shutting_down_{};

  // Our list of Python calls created in the context of this activity. We
  // clear them as we are shutting down and ensure nothing runs after that
  // point.
  std::list<Object::WeakRef<base::PythonContextCall> > python_calls_;
  std::vector<Object::Ref<Player> > players_;
  int next_player_id_{};

  // Which host-activity has focus at the moment (Players talking to it, etc).
  Object::WeakRef<HostActivity> foreground_host_activity_;
  std::vector<Object::Ref<HostActivity> > host_activities_;
  PythonRef session_py_obj_;
  bool kick_idle_players_{};
  millisecs_t last_kick_idle_players_decrement_time_;
  millisecs_t next_prune_time_{};
  std::unordered_map<std::string, Object::WeakRef<SceneTexture> > textures_;
  std::unordered_map<std::string, Object::WeakRef<SceneSound> > sounds_;
  std::unordered_map<std::string, Object::WeakRef<SceneDataAsset> > datas_;
  std::unordered_map<std::string, Object::WeakRef<SceneMesh> > meshes_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_HOST_SESSION_H_
