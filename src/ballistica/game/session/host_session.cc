// Released under the MIT License. See LICENSE for details.

#include "ballistica/game/session/host_session.h"

#include "ballistica/game/game_stream.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/game/player.h"
#include "ballistica/generic/lambda_runnable.h"
#include "ballistica/generic/timer.h"
#include "ballistica/graphics/graphics.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/media/component/data.h"
#include "ballistica/media/component/model.h"
#include "ballistica/media/component/sound.h"
#include "ballistica/media/component/texture.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_command.h"
#include "ballistica/python/python_context_call.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

HostSession::HostSession(PyObject* session_type_obj)
    : last_kick_idle_players_decrement_time_(GetRealTime()) {
  assert(g_game);
  assert(InLogicThread());
  assert(session_type_obj != nullptr);

  ScopedSetContext cp(this);

  // FIXME: Should be an attr of the session class, not hard-coded.
  is_main_menu_ =
      static_cast<bool>(strstr(Python::ObjToString(session_type_obj).c_str(),
                               "bastd.mainmenu.MainMenuSession"));
  // Log("MAIN MENU? " + std::to_string(is_main_menu()));

  kick_idle_players_ = g_game->kick_idle_players();

  // Create a timer to step our session scene.
  step_scene_timer_ =
      base_timers_.NewTimer(base_time_, kGameStepMilliseconds, 0, -1,
                            NewLambdaRunnable([this] { StepScene(); }));

  // Set up our output-stream, which will go to a replay and/or the network.
  // We don't dump to a replay if we're doing the main menu; that replay
  // would be boring.
  bool do_replay = !is_main_menu_;

  // At the moment headless-server don't write replays.
  if (HeadlessMode()) {
    do_replay = false;
  }

  output_stream_ = Object::New<GameStream>(this, do_replay);

  // Make a scene for our session-level nodes, etc.
  scene_ = Object::New<Scene>(0);
  if (output_stream_.exists()) {
    output_stream_->AddScene(scene_.get());
  }

  // Fade in from our current blackness.
  g_graphics->FadeScreen(true, 250, nullptr);

  // Start by showing the progress bar instead of hitching.
  g_graphics->EnableProgressBar(true);

  // Now's a good time to run garbage collection; there should be pretty much
  // no game stuff to speak of in existence (provided the last session went
  // down peacefully).
  g_python->obj(Python::ObjID::kGarbageCollectSessionEndCall).Call();

  // Instantiate our Python Session instance.
  PythonRef obj;
  PythonRef session_type(session_type_obj, PythonRef::kAcquire);
  {
    Python::ScopedCallLabel label("Session instantiation");
    obj = session_type.Call();
  }
  if (!obj.exists()) {
    throw Exception("Error creating game session: '" + session_type.Str()
                    + "'");
  }

  // The session python object should have called
  // _ba.register_session() in its constructor to set session_py_obj_.
  if (session_py_obj_ != obj) {
    throw Exception("session not set up correctly");
  }

  // Lastly, keep the python layer fed with our latest player count in case
  // it is updating the master-server with our current/max player counts.
  g_game->SetPublicPartyPlayerCount(static_cast<int>(players_.size()));
}

auto HostSession::GetHostSession() -> HostSession* { return this; }

void HostSession::DestroyHostActivity(HostActivity* a) {
  BA_PRECONDITION(a);
  BA_PRECONDITION(a->GetHostSession() == this);
  if (a == foreground_host_activity_.get()) {
    foreground_host_activity_.Clear();
  }

  // Clear it from our activities list if its still on there.
  for (auto i = host_activities_.begin(); i < host_activities_.end(); i++) {
    if (i->get() == a) {
      host_activities_.erase(i);
      return;
    }
  }

  // The only reason it wouldn't be there should be because the activity is
  // dying due our clearing of the list in our destructor; make sure that's
  // the case.
  assert(shutting_down_);
}

auto HostSession::GetMutableScene() -> Scene* {
  assert(scene_.exists());
  return scene_.get();
}

void HostSession::DebugSpeedMultChanged() {
  // FIXME - should we progress our own scene faster/slower depending on
  //  this too? Is there really a need to?

  // Let all our activities know.
  for (auto&& i : host_activities_) {
    i->DebugSpeedMultChanged();
  }
}

void HostSession::ScreenSizeChanged() {
  // Let our internal scene know.
  scene()->ScreenSizeChanged();

  // Also let all our activities know.
  for (auto&& i : host_activities_) {
    i->ScreenSizeChanged();
  }
}

void HostSession::LanguageChanged() {
  // Let our internal scene know.
  scene()->LanguageChanged();

  // Also let all our activities know.
  for (auto&& i : host_activities_) {
    i->LanguageChanged();
  }
}

void HostSession::GraphicsQualityChanged(GraphicsQuality q) {
  // Let our internal scene know.
  scene()->GraphicsQualityChanged(q);

  // Let all our activities know.
  for (auto&& i : host_activities_) {
    i->GraphicsQualityChanged(q);
  }
}

auto HostSession::DoesFillScreen() const -> bool {
  // FIXME not necessarily the case.
  return true;
}

void HostSession::Draw(FrameDef* f) {
  // First draw our session scene.
  scene()->Draw(f);

  // Let all our activities draw their own scenes/etc.
  for (auto&& i : host_activities_) {
    i->Draw(f);
  }
}

auto HostSession::NewTimer(TimerMedium length, bool repeat,
                           const Object::Ref<Runnable>& runnable) -> int {
  if (shutting_down_) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: Creating game timer during host-session shutdown");
    return 123;  // dummy...
  }
  if (length == 0 && repeat) {
    throw Exception("Can't add game-timer with length 0 and repeat on");
  }
  if (length < 0) {
    throw Exception("Timer length cannot be < 0 (got " + std::to_string(length)
                    + ")");
  }
  int offset = 0;
  Timer* t = sim_timers_.NewTimer(scene()->time(), length, offset,
                                  repeat ? -1 : 0, runnable);
  return t->id();
}

void HostSession::DeleteTimer(int timer_id) {
  assert(InLogicThread());
  if (shutting_down_) return;
  sim_timers_.DeleteTimer(timer_id);
}

auto HostSession::GetSound(const std::string& name) -> Object::Ref<Sound> {
  if (shutting_down_) {
    throw Exception("can't load assets during session shutdown");
  }
  return Media::GetMedia(&sounds_, name, scene());
}

auto HostSession::GetData(const std::string& name) -> Object::Ref<Data> {
  if (shutting_down_) {
    throw Exception("can't load assets during session shutdown");
  }
  return Media::GetMedia(&datas_, name, scene());
}

auto HostSession::GetTexture(const std::string& name) -> Object::Ref<Texture> {
  if (shutting_down_) {
    throw Exception("can't load assets during session shutdown");
  }
  return Media::GetMedia(&textures_, name, scene());
}
auto HostSession::GetModel(const std::string& name) -> Object::Ref<Model> {
  if (shutting_down_) {
    throw Exception("can't load media during session shutdown");
  }
  return Media::GetMedia(&models_, name, scene());
}

auto HostSession::GetForegroundContext() -> Context {
  HostActivity* a = foreground_host_activity_.get();
  if (a) {
    return Context(a);
  }
  return Context(this);
}

void HostSession::RequestPlayer(InputDevice* device) {
  assert(InLogicThread());

  // Ignore if we have no Python session obj.
  if (!GetSessionPyObj()) {
    Log("Error: HostSession::RequestPlayer() called w/no session_py_obj_.");
    return;
  }

  // Need to at least temporarily create and attach to a player for passing to
  // the callback.
  int player_id = next_player_id_++;
  auto player(Object::New<Player>(player_id, this));
  players_.push_back(player);
  device->AttachToLocalPlayer(player.get());

  // Ask the python layer to accept/deny this guy.
  bool accept;
  {
    // Set the session as context.
    ScopedSetContext cp(this);
    accept = static_cast<bool>(
        session_py_obj_.GetAttr("_request_player")
            .Call(PythonRef(Py_BuildValue("(O)", player->BorrowPyRef()),
                            PythonRef::kSteal))
            .ValueAsInt());
    if (accept) {
      player->set_accepted(true);
    } else {
      RemovePlayer(player.get());
    }
  }

  // If he was accepted, update our game roster with the new info.
  if (accept) {
    g_game->UpdateGameRoster();
  }

  // Lastly, keep the python layer fed with our latest player count in case it
  // is updating the master-server with our current/max player counts.
  g_game->SetPublicPartyPlayerCount(static_cast<int>(players_.size()));
}

void HostSession::RemovePlayer(Player* player) {
  assert(player);

  for (auto i = players_.begin(); i != players_.end(); ++i) {
    if (i->get() == player) {
      // Grab a ref to keep the player alive, pull him off the list, then call
      // his leaving callback.
      Object::Ref<Player> player2 = *i;
      players_.erase(i);

      // Only make the callback for this player if they were accepted.
      if (player2->accepted()) {
        IssuePlayerLeft(player2.get());
      }

      // Update our game roster with the departure.
      g_game->UpdateGameRoster();

      // Lastly, keep the python layer fed with our latest player count in case
      // it is updating the master-server with our current/max player counts.
      g_game->SetPublicPartyPlayerCount(static_cast<int>(players_.size()));

      return;
    }
  }
  BA_LOG_ERROR_TRACE("Player not found in HostSession::RemovePlayer()");
}

void HostSession::IssuePlayerLeft(Player* player) {
  assert(player);
  assert(InLogicThread());

  try {
    if (GetSessionPyObj()) {
      if (player) {
        // Make sure we're the context for session callbacks.
        ScopedSetContext cp(this);
        Python::ScopedCallLabel label("Session on_player_leave");
        session_py_obj_.GetAttr("on_player_leave")
            .Call(PythonRef(Py_BuildValue("(O)", player->BorrowPyRef()),
                            PythonRef::kSteal));
      } else {
        BA_LOG_PYTHON_TRACE_ONCE("missing player on IssuePlayerLeft");
      }
    } else {
      Log("WARNING: HostSession: IssuePlayerLeft caled with no "
          "session_py_obj_");
    }
  } catch (const std::exception& e) {
    Log(std::string("Error calling on_player_leave(): ") + e.what());
  }
}

void HostSession::SetKickIdlePlayers(bool enable) {
  // If this has changed, reset our disconnect-time reporting.
  assert(InLogicThread());
  if (enable != kick_idle_players_) {
    last_kick_idle_players_decrement_time_ = GetRealTime();
  }
  kick_idle_players_ = enable;
}

void HostSession::SetForegroundHostActivity(HostActivity* a) {
  assert(a);
  assert(InLogicThread());

  if (shutting_down_) {
    Log("WARNING: SetForegroundHostActivity called during session shutdown; "
        "ignoring.");
    return;
  }

  // Sanity check: make sure the one provided is part of this session.
  bool found = false;
  for (auto&& i : host_activities_) {
    if (i == a) {
      found = true;
      break;
    }
  }
  if ((a->GetHostSession() != this) || !found) {
    throw Exception("HostActivity is not part of this HostSession");
  }

  foreground_host_activity_ = a;

  // Now go through telling each host-activity whether it's foregrounded or not.
  // FIXME: Dying sessions never get told they're un-foregrounded.. could that
  //  ever be a problem?
  bool session_is_foreground = (g_game->GetForegroundSession() != nullptr);
  for (auto&& i : host_activities_) {
    i->SetIsForeground(session_is_foreground && (i == a));
  }
}

void HostSession::AddHostActivity(HostActivity* a) {
  host_activities_.emplace_back(a);
}

// Called by the constructor of the session python object.
void HostSession::RegisterPySession(PyObject* obj) {
  session_py_obj_.Acquire(obj);
}

// Given an activity python type, instantiates and returns a new activity.
auto HostSession::NewHostActivity(PyObject* activity_type_obj,
                                  PyObject* settings_obj) -> PyObject* {
  PythonRef activity_type(activity_type_obj, PythonRef::kAcquire);
  if (!activity_type.CallableCheck()) {
    throw Exception("Invalid HostActivity type passed; not callable");
  }

  // First generate our C++ activity instance and point the context at it.
  auto activity(Object::New<HostActivity>(this));
  AddHostActivity(activity.get());

  ScopedSetContext cp(activity.get());

  // Now instantiate the Python instance.. pass args if some were provided, or
  // an empty dict otherwise.
  PythonRef args;
  if (settings_obj == Py_None) {
    args.Steal(Py_BuildValue("({})"));
  } else {
    args.Steal(Py_BuildValue("(O)", settings_obj));
  }

  PythonRef result = activity_type.Call(args);
  if (!result.exists()) {
    throw Exception("HostActivity creation failed");
  }

  // If all went well, the python activity constructor should have called
  // _ba.register_activity(), so we should be able to get at the same python
  // activity we just instantiated through the c++ class.
  if (activity->GetPyActivity() != result.get()) {
    throw Exception("Error on HostActivity construction");
  }

  PyObject* obj = result.get();
  Py_INCREF(obj);
  return obj;
}

auto HostSession::RegisterPyActivity(PyObject* activity_obj) -> HostActivity* {
  // The context should be pointing to an unregistered HostActivity;
  // register and return it.
  HostActivity* activity = Context::current().GetHostActivity();
  if (!activity)
    throw Exception(
        "No current activity in RegisterPyActivity; did you remember to call "
        "ba.newHostActivity() to instantiate your activity?");
  activity->RegisterPyActivity(activity_obj);
  return activity;
}

void HostSession::DecrementPlayerTimeOuts(millisecs_t millisecs) {
  for (auto&& i : players_) {
    Player* player = i.get();
    assert(player);
    if (player->time_out() < millisecs) {
      std::string kick_str =
          g_game->GetResourceString("kickIdlePlayersKickedText");
      Utils::StringReplaceOne(&kick_str, "${NAME}", player->GetName());
      ScreenMessage(kick_str);
      RemovePlayer(player);
      return;  // Bail for this round since we prolly mucked with the list.
    } else if (player->time_out() > BA_PLAYER_TIME_OUT_WARN
               && (player->time_out() - millisecs <= BA_PLAYER_TIME_OUT_WARN)) {
      std::string kick_str_1 =
          g_game->GetResourceString("kickIdlePlayersWarning1Text");
      Utils::StringReplaceOne(&kick_str_1, "${NAME}", player->GetName());
      Utils::StringReplaceOne(&kick_str_1, "${COUNT}",
                              std::to_string(BA_PLAYER_TIME_OUT_WARN / 1000));
      ScreenMessage(kick_str_1);
      ScreenMessage(g_game->GetResourceString("kickIdlePlayersWarning2Text"));
    }
    player->set_time_out(player->time_out() - millisecs);
  }
}

void HostSession::ProcessPlayerTimeOuts() {
  millisecs_t real_time = GetRealTime();

  if (foreground_host_activity_.exists()
      && foreground_host_activity_->game_speed() > 0.0
      && !foreground_host_activity_->paused()
      && foreground_host_activity_->getAllowKickIdlePlayers()
      && kick_idle_players_) {
    // Let's only do this every now and then.
    if (real_time - last_kick_idle_players_decrement_time_ > 1000) {
      DecrementPlayerTimeOuts(real_time
                              - last_kick_idle_players_decrement_time_);
      last_kick_idle_players_decrement_time_ = real_time;
    }
  } else {
    // If we're not kicking, we still store the latest time (so it doesnt
    // accumulate for when we start again).
    last_kick_idle_players_decrement_time_ = real_time;
  }
}

void HostSession::StepScene() {
  // Run up our game-time timers.
  sim_timers_.Run(scene()->time());

  // And step.
  scene()->Step();
}

void HostSession::Update(int time_advance) {
  assert(InLogicThread());

  // We can be killed at any time, so let's keep an eye out for that.
  WeakRef<HostSession> test_ref(this);
  assert(test_ref.exists());

  ProcessPlayerTimeOuts();

  GameStream* output_stream = GetGameStream();

  // Advance base time by the specified amount,
  // firing all timers along the way.
  millisecs_t target_base_time = base_time_ + time_advance;
  while (!base_timers_.empty()
         && (base_time_ + base_timers_.GetTimeToNextExpire(base_time_)
             <= target_base_time)) {
    base_time_ += base_timers_.GetTimeToNextExpire(base_time_);
    if (output_stream) {
      output_stream->SetTime(base_time_);
    }
    base_timers_.Run(base_time_);
  }
  base_time_ = target_base_time;
  if (output_stream) {
    output_stream->SetTime(base_time_);
  }
  assert(test_ref.exists());

  // Update our activities (iterate via weak-refs as this list may change under
  // us at any time).
  std::vector<Object::WeakRef<HostActivity> > activities =
      PointersToWeakRefs(RefsToPointers(host_activities_));
  for (auto&& i : activities) {
    if (i.exists()) {
      i->Update(time_advance);
      assert(test_ref.exists());
    }
  }
  assert(test_ref.exists());

  // Periodically prune various dead refs.
  if (base_time_ > next_prune_time_) {
    PruneDeadMapRefs(&textures_);
    PruneDeadMapRefs(&sounds_);
    PruneDeadMapRefs(&models_);
    PruneDeadRefs(&python_calls_);
    next_prune_time_ = base_time_ + 5000;
  }
  assert(test_ref.exists());
}

HostSession::~HostSession() {
  try {
    shutting_down_ = true;

    // Put the scene in shut-down mode before we start killing stuff
    // (this generates warnings, suppresses messages, etc).
    scene_->set_shutting_down(true);

    // Clear out all python calls registered in our context
    // (should wipe out refs to our session and prevent them from running
    // without a valid session context).
    for (auto&& i : python_calls_) {
      if (i.exists()) {
        i->MarkDead();
      }
    }

    // Mark all our media dead to clear it out of our output-stream cleanly.
    for (auto&& i : textures_) {
      if (i.second.exists()) {
        i.second->MarkDead();
      }
    }
    for (auto&& i : models_) {
      if (i.second.exists()) {
        i.second->MarkDead();
      }
    }
    for (auto&& i : sounds_) {
      if (i.second.exists()) {
        i.second->MarkDead();
      }
    }

    // Clear our timers and scene; this should wipe out any remaining refs
    // to our session scene.
    base_timers_.Clear();
    sim_timers_.Clear();
    scene_.Clear();

    // Kill our python session object.
    {
      ScopedSetContext cp(this);
      session_py_obj_.Release();
    }

    // Kill any remaining activity data. Generally all activities should die
    // when the session python object goes down, but lets clean up in case any
    // didn't.
    for (auto&& i : host_activities_) {
      ScopedSetContext cp{Object::Ref<ContextTarget>(i)};
      i.Clear();
    }

    // Report outstanding calls. There shouldn't be any at this point. Actually
    // it turns out there's generally 1; whichever call was responsible for
    // killing this activity will still be in progress.. so let's report on 2 or
    // more I guess.
    if (g_buildconfig.debug_build()) {
      PruneDeadRefs(&python_calls_);
      if (python_calls_.size() > 1) {
        std::string s = "WARNING: " + std::to_string(python_calls_.size())
                        + " live PythonContextCalls at shutdown for "
                        + "HostSession" + " (1 call is expected):";
        int count = 1;
        for (auto&& i : python_calls_) {
          s += ("\n  " + std::to_string(count++) + ": "
                + i->GetObjectDescription());
        }
        Log(s);
      }
    }
  } catch (const std::exception& e) {
    Log("Exception in HostSession destructor: " + std::string(e.what()));
  }
}

void HostSession::RegisterCall(PythonContextCall* call) {
  assert(call);
  python_calls_.emplace_back(call);

  // If we're shutting down, just kill the call immediately.
  // (we turn all of our calls to no-ops as we shut down).
  if (shutting_down_) {
    Log("WARNING: adding call to expired session; call will not function: "
        + call->GetObjectDescription());
    call->MarkDead();
  }
}

auto HostSession::GetUnusedPlayerName(Player* p, const std::string& base_name)
    -> std::string {
  // Now find the first non-taken variation.
  int index = 1;
  std::string name_test;
  while (true) {
    if (index > 1) {
      name_test = base_name + " " + std::to_string(index);
    } else {
      name_test = base_name;
    }
    bool name_found = false;
    for (auto&& j : players_) {
      if ((j->GetName() == name_test) && (j.get() != p)) {
        name_found = true;
        break;
      }
    }
    if (!name_found) break;
    index += 1;
  }
  return name_test;
}

void HostSession::DumpFullState(GameStream* out) {
  // Add session-scene.
  if (scene_.exists()) {
    scene_->Dump(out);
  }

  // Dump media associated with session-scene.
  for (auto&& i : textures_) {
    if (Texture* t = i.second.get()) {
      out->AddTexture(t);
    }
  }
  for (auto&& i : sounds_) {
    if (Sound* s = i.second.get()) {
      out->AddSound(s);
    }
  }
  for (auto&& i : models_) {
    if (Model* s = i.second.get()) {
      out->AddModel(s);
    }
  }

  // Dump session-scene's nodes.
  if (scene_.exists()) {
    scene_->DumpNodes(out);
  }

  // Now let our activities dump themselves.
  for (auto&& i : host_activities_) {
    i->DumpFullState(out);
  }
}

void HostSession::GetCorrectionMessages(
    bool blend, std::vector<std::vector<uint8_t> >* messages) {
  std::vector<uint8_t> message;

  // Grab correction for session scene (though there shouldn't be one).
  if (scene_.exists()) {
    message = scene_->GetCorrectionMessage(blend);
    if (message.size() > 4) {
      // A correction packet of size 4 is empty; ignore it.
      messages->push_back(message);
    }
  }

  // Now do same for activity scenes.
  for (auto&& i : host_activities_) {
    if (HostActivity* ha = i.get()) {
      if (Scene* sg = ha->scene()) {
        message = sg->GetCorrectionMessage(blend);
        if (message.size() > 4) {
          // A correction packet of size 4 is empty; ignore it.
          messages->push_back(message);
        }
      }
    }
  }
}

auto HostSession::NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                           const Object::Ref<Runnable>& runnable) -> int {
  // Make sure the runnable passed in is reference-managed already
  // (we may not add an initial reference ourself).
  assert(runnable->is_valid_refcounted_object());

  // We currently support game and base timers.
  switch (timetype) {
    case TimeType::kSim:
    case TimeType::kBase:
      // Game and base timers are the same thing for us.
      return NewTimer(length, repeat, runnable);
    default:
      // Gall back to default for descriptive error otherwise.
      return ContextTarget::NewTimer(timetype, length, repeat, runnable);
  }
}

void HostSession::DeleteTimer(TimeType timetype, int timer_id) {
  switch (timetype) {
    case TimeType::kSim:
    case TimeType::kBase:
      // Game and base timers are the same thing for us.
      DeleteTimer(timer_id);
      break;
    default:
      // Fall back to default for descriptive error otherwise.
      ContextTarget::DeleteTimer(timetype, timer_id);
      break;
  }
}

auto HostSession::GetTime(TimeType timetype) -> millisecs_t {
  switch (timetype) {
    case TimeType::kSim:
    case TimeType::kBase:
      return scene_->time();
    default:
      // Fall back to default for descriptive error otherwise.
      return ContextTarget::GetTime(timetype);
  }
}

}  // namespace ballistica
