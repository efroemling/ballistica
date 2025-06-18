// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/host_session.h"

#include <Python.h>

#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/lambda_runnable.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

HostSession::HostSession(PyObject* session_type_obj)
    : last_kick_idle_players_decrement_time_(g_core->AppTimeMillisecs()) {
  assert(g_base->logic);
  assert(g_base->InLogicThread());
  assert(session_type_obj != nullptr);

  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();
  base::ScopedSetContext ssc(this);

  // FIXME: Should be an attr of the session class, not hard-coded.
  is_main_menu_ =
      static_cast<bool>(strstr(Python::ObjToString(session_type_obj).c_str(),
                               "bascenev1lib.mainmenu.MainMenuSession"));
  // Log(LogLevel::kInfo, "MAIN MENU? " + std::to_string(is_main_menu()));

  kick_idle_players_ = appmode->kick_idle_players();

  // Create a timer to step our session scene.
  step_scene_timer_ =
      base_timers_.NewTimer(base_time_millisecs_, kGameStepMilliseconds, 0, -1,
                            NewLambdaRunnable([this] { StepScene(); }).get());

  // Set up our output-stream, which will go to a replay and/or the network.
  // We don't dump to a replay if we're doing the main menu; that replay
  // would be boring.
  bool do_replay = !is_main_menu_;

  // At the moment headless-server don't write replays.
  if (g_core->HeadlessMode()) {
    do_replay = false;
  }

  output_stream_ = Object::New<SessionStream>(this, do_replay);

  // Make a scene for our session-level nodes, etc.
  scene_ = Object::New<Scene>(0);
  if (output_stream_.exists()) {
    output_stream_->AddScene(scene_.get());
  }

  // Start by showing the progress bar instead of hitching.
  g_base->graphics->EnableProgressBar(true);

  // Now's a good time to run garbage collection; there should be pretty much
  // no game stuff to speak of in existence (provided the last session went
  // down peacefully).
  g_base->python->objs().Get(base::BasePython::ObjID::kAppGCCollectCall).Call();

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
  // _babase.register_session() in its constructor to set session_py_obj_.
  if (session_py_obj_ != obj) {
    throw Exception("session not set up correctly");
  }

  // Lastly, keep the python layer fed with our latest player count in case
  // it is updating the master-server with our current/max player counts.
  appmode->SetPublicPartyPlayerCount(static_cast<int>(players_.size()));
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

void HostSession::OnScreenSizeChange() {
  // Let our internal scene know.
  scene()->OnScreenSizeChange();

  // Also let all our activities know.
  for (auto&& i : host_activities_) {
    i->OnScreenSizeChange();
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

auto HostSession::DoesFillScreen() const -> bool {
  // FIXME not necessarily the case.
  return true;
}

void HostSession::Draw(base::FrameDef* f) {
  // First draw our session scene.
  scene()->Draw(f);

  // Let all our activities draw their own scenes/etc.
  for (auto&& i : host_activities_) {
    i->Draw(f);
  }
}

auto HostSession::GetSound(const std::string& name) -> Object::Ref<SceneSound> {
  if (shutting_down_) {
    throw Exception("can't load assets during session shutdown");
  }
  return GetAsset(&sounds_, name, scene());
}

auto HostSession::GetData(const std::string& name)
    -> Object::Ref<SceneDataAsset> {
  if (shutting_down_) {
    throw Exception("can't load assets during session shutdown");
  }
  return GetAsset(&datas_, name, scene());
}

auto HostSession::GetTexture(const std::string& name)
    -> Object::Ref<SceneTexture> {
  if (shutting_down_) {
    throw Exception("can't load assets during session shutdown");
  }
  return GetAsset(&textures_, name, scene());
}

auto HostSession::GetMesh(const std::string& name) -> Object::Ref<SceneMesh> {
  if (shutting_down_) {
    throw Exception("can't load media during session shutdown");
  }
  return GetAsset(&meshes_, name, scene());
}

auto HostSession::GetForegroundContext() -> base::ContextRef {
  HostActivity* a = foreground_host_activity_.get();
  if (a) {
    return base::ContextRef(a);
  }
  return base::ContextRef(this);
}

void HostSession::RequestPlayer(SceneV1InputDeviceDelegate* device) {
  assert(g_base->InLogicThread());
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // Ignore if we have no Python session Obj.
  if (!GetSessionPyObj()) {
    g_core->logging->Log(
        LogName::kBaNetworking, LogLevel::kError,
        "HostSession::RequestPlayer() called w/no session_py_obj_.");
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
    base::ScopedSetContext ssc(this);
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
    appmode->UpdateGameRoster();
  }

  // Lastly, keep the python layer fed with our latest player count in case it
  // is updating the master-server with our current/max player counts.
  appmode->SetPublicPartyPlayerCount(static_cast<int>(players_.size()));
}

void HostSession::RemovePlayer(Player* player) {
  assert(player);
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // If we find the player amongst our ranks, remove them.
  // Note that it is expected to get redundant calls for this that
  // we silently ignore (for instance if a session removes a player
  // then the player will still try to remove themself from their session
  // as they are going down).
  for (auto i = players_.begin(); i != players_.end(); ++i) {
    if (i->get() == player) {
      // Grab a ref to keep the player alive, pull him off the list, then call
      // his leaving callback.
      auto player2 = Object::Ref<Player>(*i);
      players_.erase(i);

      // Clear the player's attachment to its host-session so it doesn't
      // redundantly ask the host-session to remove it as it is dying.
      player->ClearHostSessionForTearDown();

      // Only make the callback for this player if they were accepted.
      if (player2->accepted()) {
        IssuePlayerLeft(player2.get());
      }

      // Update our game roster with the departure.
      appmode->UpdateGameRoster();

      // Lastly, keep the python layer fed with our latest player count in case
      // it is updating the master-server with our current/max player counts.
      appmode->SetPublicPartyPlayerCount(static_cast<int>(players_.size()));

      return;
    }
  }
  BA_LOG_ERROR_PYTHON_TRACE("Player not found in HostSession::RemovePlayer()");
}

void HostSession::IssuePlayerLeft(Player* player) {
  assert(player);
  assert(g_base->InLogicThread());

  try {
    if (GetSessionPyObj()) {
      if (player) {
        // Make sure we're the context for session callbacks.
        base::ScopedSetContext ssc(this);
        Python::ScopedCallLabel label("Session on_player_leave");
        session_py_obj_.GetAttr("on_player_leave")
            .Call(PythonRef(Py_BuildValue("(O)", player->BorrowPyRef()),
                            PythonRef::kSteal));
      } else {
        BA_LOG_PYTHON_TRACE_ONCE("missing player on IssuePlayerLeft");
      }
    } else {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kWarning,
                           "HostSession: IssuePlayerLeft caled with no "
                           "session_py_obj_");
    }
  } catch (const std::exception& e) {
    g_core->logging->Log(
        LogName::kBaNetworking, LogLevel::kError,
        std::string("Error calling on_player_leave(): ") + e.what());
  }
}

void HostSession::SetKickIdlePlayers(bool enable) {
  // If this has changed, reset our disconnect-time reporting.
  assert(g_base->InLogicThread());
  if (enable != kick_idle_players_) {
    last_kick_idle_players_decrement_time_ = g_core->AppTimeMillisecs();
  }
  kick_idle_players_ = enable;
}

void HostSession::SetForegroundHostActivity(HostActivity* a) {
  assert(a);
  assert(g_base->InLogicThread());

  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();

  if (shutting_down_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "SetForegroundHostActivity called during session shutdown; "
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
  bool session_is_foreground = (appmode->GetForegroundSession() != nullptr);
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

  base::ScopedSetContext ssc(activity.get());

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

  // If all went well, the Python activity constructor should have called
  // register_activity(), so we should be able to get at the same Python
  // activity we just instantiated through the c++ class.

  // GetPyActivity returns a new ref or nullptr.
  auto py_activity{PythonRef::StolenSoft(activity->GetPyActivity())};
  if (!py_activity.exists() || py_activity.get() != result.get()) {
    throw Exception("Error on HostActivity construction");
  }

  return result.NewRef();
}

auto HostSession::RegisterPyActivity(PyObject* activity_obj) -> HostActivity* {
  // The context should be pointing to an unregistered HostActivity;
  // register and return it.
  HostActivity* activity = ContextRefSceneV1::FromCurrent().GetHostActivity();
  if (!activity)
    throw Exception(
        "No current activity in RegisterPyActivity; did you remember to call "
        "babase.newHostActivity() to instantiate your activity?");
  activity->RegisterPyActivity(activity_obj);
  return activity;
}

void HostSession::DecrementPlayerTimeOuts(millisecs_t millisecs) {
  for (auto&& i : players_) {
    Player* player = i.get();
    assert(player);
    if (player->time_out() < millisecs) {
      std::string kick_str =
          g_base->assets->GetResourceString("kickIdlePlayersKickedText");
      Utils::StringReplaceOne(&kick_str, "${NAME}", player->GetName());
      g_base->ScreenMessage(kick_str);
      RemovePlayer(player);
      return;  // Bail for this round since we prolly mucked with the list.
    } else if (player->time_out() > BA_PLAYER_TIME_OUT_WARN
               && (player->time_out() - millisecs <= BA_PLAYER_TIME_OUT_WARN)) {
      std::string kick_str_1 =
          g_base->assets->GetResourceString("kickIdlePlayersWarning1Text");
      Utils::StringReplaceOne(&kick_str_1, "${NAME}", player->GetName());
      Utils::StringReplaceOne(&kick_str_1, "${COUNT}",
                              std::to_string(BA_PLAYER_TIME_OUT_WARN / 1000));
      g_base->ScreenMessage(kick_str_1);
      g_base->ScreenMessage(
          g_base->assets->GetResourceString("kickIdlePlayersWarning2Text"));
    }
    player->set_time_out(player->time_out() - millisecs);
  }
}

void HostSession::ProcessPlayerTimeOuts() {
  millisecs_t real_time = g_core->AppTimeMillisecs();

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

void HostSession::Update(int time_advance_millisecs, double time_advance) {
  assert(g_base->InLogicThread());

  millisecs_t update_time_start = core::CorePlatform::TimeMonotonicMillisecs();

  // HACK: we used to do a bunch of fudging to try and advance time by
  // exactly 16 milliseconds per frame which would give us a clean 2 sim
  // steps per frame on 60hz devices. These days we're trying to be more
  // exact and general since non-60hz devices are becoming more common,
  // but we're somewhat limited in our ability to do that here since
  // our base-timer-list here and our scene-commands system both use
  // milliseconds. Ideally if our sim were stepping by 8.3333 milliseconds and
  // display-time were advancing by a constant 16.6666 then it would do the
  // right thing, but with only integer millisecond precision we'll get aliasing
  // and stuttering and some frames advancing by 1 sim step and others by 3,
  // etc. So until we can upgrade everything to have finer precision (perhaps in
  // scene_v2), let's just using the old trick of forcing 16 millisecond steps
  // if it looks like we're probably running at 60hz.
  if (time_advance_millisecs >= 15 && time_advance_millisecs <= 17) {
    time_advance_millisecs = 16;
  } else {
    if (explicit_bool(false)) {
      printf("NOT: %d %.5f\n", time_advance_millisecs, time_advance);
    }
  }

  // We shouldn't be getting *huge* steps coming through here. Warn if that
  // ever happens so we can fix it at the source.
  if (time_advance_millisecs > 500 || time_advance > 0.5) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                "HostSession::Update() got excessive time_advance ("
                    + std::to_string(time_advance_millisecs) + " ms, "
                    + std::to_string(time_advance) + " s); should not happen.");
  }

  // We can be killed at any time, so let's keep an eye out for that.
  WeakRef<HostSession> test_ref(this);
  assert(test_ref.exists());

  ProcessPlayerTimeOuts();

  SessionStream* output_stream = GetSceneStream();
  auto too_slow{false};

  // Try to advance our base time by the provided amount, firing all timers
  // along the way.
  millisecs_t target_base_time_millisecs =
      base_time_millisecs_ + time_advance_millisecs;
  while (!base_timers_.Empty()
         && (base_time_millisecs_
                 + base_timers_.TimeToNextExpire(base_time_millisecs_)
             <= target_base_time_millisecs)) {
    base_time_millisecs_ += base_timers_.TimeToNextExpire(base_time_millisecs_);
    if (output_stream) {
      output_stream->SetTime(base_time_millisecs_);
    }
    base_timers_.Run(base_time_millisecs_);

    // After each time we step time, abort if we're taking too long. This way we
    // slow down if we're overloaded and have a better chance at maintaining
    // a reasonable frame-rate/etc.
    auto elapsed =
        core::CorePlatform::TimeMonotonicMillisecs() - update_time_start;
    if (elapsed >= 1000 / 30) {
      too_slow = true;
      break;
    }
  }

  // If we didn't abort, set our time to where we were aiming for.
  if (!too_slow) {
    base_time_millisecs_ = target_base_time_millisecs;
    if (output_stream) {
      output_stream->SetTime(base_time_millisecs_);
    }
  }
  assert(test_ref.exists());

  // Let our activities update too (iterate via weak-refs as this list may
  // change under us at any time).
  for (auto&& i : PointersToWeakRefs(RefsToPointers(host_activities_))) {
    if (i.exists()) {
      i->StepDisplayTime(time_advance_millisecs);
      assert(test_ref.exists());
    }
  }
  assert(test_ref.exists());

  // Periodically prune various dead refs.
  if (base_time_millisecs_ > next_prune_time_) {
    PruneDeadMapRefs(&textures_);
    PruneDeadMapRefs(&sounds_);
    PruneDeadMapRefs(&meshes_);
    PruneDeadRefs(&python_calls_);
    next_prune_time_ = base_time_millisecs_ + 5000;
  }
  assert(test_ref.exists());
}

auto HostSession::TimeToNextEvent() -> std::optional<microsecs_t> {
  if (base_timers_.Empty()) {
    return {};
  }
  auto to_next_ms = base_timers_.TimeToNextExpire(base_time_millisecs_);
  return to_next_ms * 1000;  // to microsecs.
}

HostSession::~HostSession() {
  assert(g_base->InLogicThread());
  try {
    shutting_down_ = true;

    // Put the scene in shut-down mode before we start killing stuff
    // (this generates warnings, suppresses messages, etc).
    scene_->set_shutting_down(true);

    // Tell all players not to inform us when they go down.
    for (auto&& player : players_) {
      player->ClearHostSessionForTearDown();
    }

    // Clear out all Python calls registered in our context
    // (should wipe out refs to our session and prevent them from running
    // without a valid session context).
    for (auto&& i : python_calls_) {
      if (auto* j = i.get()) {
        j->MarkDead();
      }
    }

    // Mark all our media dead to clear it out of our output-stream cleanly.
    for (auto&& i : textures_) {
      if (auto* j = i.second.get()) {
        j->MarkDead();
      }
    }
    for (auto&& i : meshes_) {
      if (auto* j = i.second.get()) {
        j->MarkDead();
      }
    }
    for (auto&& i : sounds_) {
      if (auto* j = i.second.get()) {
        j->MarkDead();
      }
    }

    // Clear our timers and scene; this should wipe out any remaining refs
    // to our session scene.
    base_timers_.Clear();
    sim_timers_.Clear();
    scene_.Clear();

    // Kill our Python session object.
    {
      base::ScopedSetContext ssc(this);
      session_py_obj_.Release();
    }

    // Kill any remaining activity data. Generally all activities should die
    // when the session python object goes down, but lets clean up in case any
    // didn't.
    for (auto&& i : host_activities_) {
      base::ScopedSetContext ssc{Object::Ref<Context>(i)};
      i.Clear();
    }

    // Report outstanding calls. There shouldn't be any at this point. Actually
    // it turns out there's generally 1; whichever call was responsible for
    // killing this activity will still be in progress.. so let's report on 2 or
    // more I guess.
    if (g_buildconfig.debug_build()) {
      PruneDeadRefs(&python_calls_);
      if (python_calls_.size() > 1) {
        std::string s = std::to_string(python_calls_.size())
                        + " live PythonContextCalls at shutdown for "
                        + "HostSession" + " (1 call is expected):";
        int count = 1;
        for (auto&& i : python_calls_) {
          s += ("\n  " + std::to_string(count++) + ": "
                + i->GetObjectDescription());
        }
        g_core->logging->Log(LogName::kBa, LogLevel::kWarning, s);
      }
    }
  } catch (const std::exception& e) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "Exception in HostSession destructor: " + std::string(e.what()));
  }
}
auto HostSession::ContextAllowsDefaultTimerTypes() -> bool {
  // We want to discourage the use of app-timers and display-timers
  // in gameplay code; scene-timers and base-timers should be used instead
  // since they properly support game speed changes, slowdowns, etc.
  return false;
}

void HostSession::RegisterContextCall(base::PythonContextCall* call) {
  assert(call);
  python_calls_.emplace_back(call);

  // If we're shutting down, just kill the call immediately.
  // (we turn all of our calls to no-ops as we shut down).
  if (shutting_down_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "Adding call to expired session; call will not function: "
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

void HostSession::DumpFullState(SessionStream* out) {
  // Add session-scene.
  if (scene_.exists()) {
    scene_->Dump(out);
  }

  // Dump media associated with session-scene.
  for (auto&& i : textures_) {
    if (SceneTexture* t = i.second.get()) {
      out->AddTexture(t);
    }
  }
  for (auto&& i : sounds_) {
    if (SceneSound* s = i.second.get()) {
      out->AddSound(s);
    }
  }
  for (auto&& i : meshes_) {
    if (SceneMesh* s = i.second.get()) {
      out->AddMesh(s);
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
                           Runnable* runnable) -> int {
  assert(Object::IsValidManagedObject(runnable));

  // We currently support game and base timers.
  switch (timetype) {
    case TimeType::kSim:
    case TimeType::kBase: {
      if (shutting_down_) {
        BA_LOG_PYTHON_TRACE_ONCE(
            "WARNING: Creating game timer during host-session shutdown");
        return 123;  // dummy...
      }
      if (length == 0 && repeat) {
        throw Exception("Can't add game-timer with length 0 and repeat on");
      }
      if (length < 0) {
        throw Exception("Timer length cannot be < 0 (got "
                        + std::to_string(length) + ")");
      }
      int offset = 0;
      auto&& timerlist =
          timetype == TimeType::kSim ? sim_timers_ : base_timers_;

      Timer* t = timerlist.NewTimer(scene()->time(), length, offset,
                                    repeat ? -1 : 0, runnable);
      return t->id();
    }
    default:
      // Gall back to default for descriptive error otherwise.
      return SceneV1Context::NewTimer(timetype, length, repeat, runnable);
  }
}

void HostSession::DeleteTimer(TimeType timetype, int timer_id) {
  assert(g_base->InLogicThread());
  if (shutting_down_) {
    return;
  }
  switch (timetype) {
    case TimeType::kSim:
      sim_timers_.DeleteTimer(timer_id);
      break;
    case TimeType::kBase:
      // Game and base timers are the same thing for us.
      base_timers_.DeleteTimer(timer_id);
      break;
    default:
      // Fall back to default for descriptive error otherwise.
      SceneV1Context::DeleteTimer(timetype, timer_id);
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
      return SceneV1Context::GetTime(timetype);
  }
}

}  // namespace ballistica::scene_v1
