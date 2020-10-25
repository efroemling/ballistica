// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SESSION_HOST_SESSION_H_
#define BALLISTICA_GAME_SESSION_HOST_SESSION_H_

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/context.h"
#include "ballistica/game/session/session.h"
#include "ballistica/generic/timer_list.h"
#include "ballistica/python/python_ref.h"

namespace ballistica {

class HostSession : public Session {
 public:
  explicit HostSession(PyObject* session_type_obj);
  ~HostSession() override;

  // Return a borrowed python ref.
  auto GetSessionPyObj() const -> PyObject* { return session_py_obj_.get(); }

  // Set focus to a Context (it must belong to this session).
  void SetForegroundHostActivity(HostActivity* sgc);
  auto GetSound(const std::string& name) -> Object::Ref<Sound> override;
  auto GetData(const std::string& name) -> Object::Ref<Data> override;
  auto GetTexture(const std::string& name) -> Object::Ref<Texture> override;
  auto GetModel(const std::string& name) -> Object::Ref<Model> override;

  void SetKickIdlePlayers(bool enable);

  // Update the session.
  void Update(int time_advance) override;

  // ContextTarget time/timer support
  auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> int override;
  void DeleteTimer(TimeType timetype, int timer_id) override;
  auto GetTime(TimeType timetype) -> millisecs_t override;

  // Given an activity python type, instantiate a new activity
  // and return a new reference.
  auto NewHostActivity(PyObject* activity_type_obj, PyObject* settings_obj)
      -> PyObject*;
  void DestroyHostActivity(HostActivity* a);
  void RemovePlayer(Player* player);
  void RequestPlayer(InputDevice* device);

  // Return either a host-activity context or the session-context.
  auto GetForegroundContext() -> Context override;
  auto DoesFillScreen() const -> bool override;
  void Draw(FrameDef* f) override;
  void ScreenSizeChanged() override;
  void LanguageChanged() override;
  void GraphicsQualityChanged(GraphicsQuality q) override;
  void DebugSpeedMultChanged() override;
  auto GetHostSession() -> HostSession* override;
  auto GetMutableScene() -> Scene* override;
  auto scene() -> Scene* {
    assert(scene_.exists());
    return scene_.get();
  }
  void RegisterCall(PythonContextCall* call);
  auto GetGameStream() const -> GameStream* { return output_stream_.get(); }
  auto is_main_menu() const -> bool {
    return is_main_menu_;
  }  // fixme remove this
  void DumpFullState(GameStream* out) override;
  void GetCorrectionMessages(bool blend,
                             std::vector<std::vector<uint8_t> >* messages);
  auto base_time() const -> millisecs_t { return base_time_; }
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

 private:
  auto NewTimer(TimerMedium length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> int;
  void DeleteTimer(int timer_id);
  void StepScene();
  void ProcessPlayerTimeOuts();
  void DecrementPlayerTimeOuts(millisecs_t millisecs);
  void IssuePlayerLeft(Player* player);

  bool is_main_menu_;  // FIXME: Remove this.
  Object::Ref<GameStream> output_stream_;
  Timer* step_scene_timer_;
  millisecs_t base_time_ = 0;
  TimerList sim_timers_;
  TimerList base_timers_;
  Object::Ref<Scene> scene_;
  bool shutting_down_ = false;

  // Our list of python calls created in the context of this activity. We
  // clear them as we are shutting down and ensure nothing runs after that
  // point.
  std::list<Object::WeakRef<PythonContextCall> > python_calls_;
  std::vector<Object::Ref<Player> > players_;
  int next_player_id_ = 0;

  // Which host-activity has focus at the moment (Players talking to it, etc).
  Object::WeakRef<HostActivity> foreground_host_activity_;
  std::vector<Object::Ref<HostActivity> > host_activities_;
  PythonRef session_py_obj_;
  bool kick_idle_players_ = false;
  millisecs_t last_kick_idle_players_decrement_time_;
  millisecs_t next_prune_time_ = 0;
  std::unordered_map<std::string, Object::WeakRef<Texture> > textures_;
  std::unordered_map<std::string, Object::WeakRef<Sound> > sounds_;
  std::unordered_map<std::string, Object::WeakRef<Data> > datas_;
  std::unordered_map<std::string, Object::WeakRef<Model> > models_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SESSION_HOST_SESSION_H_
