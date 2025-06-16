// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/host_activity.h"

#include <Python.h>

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/node/globals_node.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/player.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/shared/generic/lambda_runnable.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

HostActivity::HostActivity(HostSession* host_session) {
  // Store a link to the HostSession and add ourself to it.
  host_session_ = host_session;

  {
    base::ScopedSetContext ssc(this);  // So scene picks us up as context.
    scene_ = Object::New<Scene>(0);

    // If there's an output stream, add to it.
    if (SessionStream* out = host_session->GetSceneStream()) {
      out->AddScene(scene_.get());
    }
  }
}

HostActivity::~HostActivity() {
  shutting_down_ = true;

  // Put the scene in shut-down mode before we start killing stuff.
  // (this generates warnings, suppresses messages, etc)
  scene_->set_shutting_down(true);

  // Clear out all Python calls registered in our context.
  // (should wipe out refs to our activity and prevent them from running without
  // a valid activity context)
  for (auto&& i : context_calls_) {
    if (i.exists()) {
      i->MarkDead();
    }
  }

  // Mark all our media dead to clear it out of our output-stream cleanly
  for (auto&& i : textures_) {
    if (i.second.exists()) {
      i.second->MarkDead();
    }
  }
  for (auto&& i : meshes_) {
    if (i.second.exists()) {
      i.second->MarkDead();
    }
  }
  for (auto&& i : sounds_) {
    if (i.second.exists()) {
      i.second->MarkDead();
    }
  }
  for (auto&& i : collision_meshes_) {
    if (i.second.exists()) {
      i.second->MarkDead();
    }
  }
  for (auto&& i : materials_) {
    if (i.exists()) {
      i->MarkDead();
    }
  }

  // If the host-session is outliving us, kill all the base-timers we created
  // in it.
  if (auto* host_session = host_session_.get()) {
    for (auto timer_id : session_base_timer_ids_) {
      host_session->DeleteTimer(TimeType::kBase, timer_id);
    }
  }
  // Clear our timers and scene; this should wipe out any remaining refs to our
  // Python activity, allowing it to die.
  // base_timers_.Clear();
  scene_timers_.Clear();
  scene_.Clear();

  // Report outstanding calls. There shouldn't be any at this point. Actually it
  // turns out there's generally 1; whichever call was responsible for killing
  // this activity will still be in progress. So let's report on 2 or more I
  // guess.
  if (g_buildconfig.debug_build()) {
    PruneDeadRefs(&context_calls_);
    if (context_calls_.size() > 1) {
      std::string s = std::to_string(context_calls_.size())
                      + " live PythonContextCalls at shutdown for "
                      + "HostActivity" + " (1 call is expected):";
      int count = 1;
      for (auto& python_call : context_calls_)
        s += "\n  " + std::to_string(count++) + ": "
             + (*python_call).GetObjectDescription();
      g_core->logging->Log(LogName::kBa, LogLevel::kWarning, s);
    }
  }
}

auto HostActivity::GetSceneStream() const -> SessionStream* {
  if (!host_session_.exists()) return nullptr;
  return host_session_->GetSceneStream();
}

void HostActivity::SetGlobalsNode(GlobalsNode* node) { globals_node_ = node; }

void HostActivity::StepScene() {
  int cycle_count = 1;
  if (host_session_->benchmark_type() == base::BenchmarkType::kCPU) {
    cycle_count = 100;
  }

  for (int cycle = 0; cycle < cycle_count; ++cycle) {
    assert(g_base->InLogicThread());

    // Clear our player-positions for this step.
    // FIXME: Move this to scene and/or player node.
    assert(host_session_.exists());
    for (auto&& player : host_session_->players()) {
      assert(player.exists());
      player->set_have_position(false);
    }

    // Run our sim-time timers.
    scene_timers_.Run(scene()->time());

    // Send die-messages/etc to out-of-bounds stuff.
    HandleOutOfBoundsNodes();

    scene()->Step();
  }
}

void HostActivity::RegisterContextCall(base::PythonContextCall* call) {
  assert(call);
  context_calls_.emplace_back(call);

  // If we're shutting down, just kill the call immediately.
  // (we turn all of our calls to no-ops as we shut down)
  if (shutting_down_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "Adding call to expired activity; call will not function: "
            + call->GetObjectDescription());
    call->MarkDead();
  }
}

void HostActivity::Start() {
  if (started_) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "HostActivity::Start() called twice.");
    return;
  }
  started_ = true;
  if (shutting_down_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "HostActivity::Start() called for shutting-down activity.");
    return;
  }
  auto* host_session = host_session_.get();
  if (!host_session) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "HostActivity::Start() called with dead session.");
    return;
  }
  // Create our step timer - gets called whenever scene should step.
  step_scene_timer_id_ =
      host_session->NewTimer(TimeType::kBase, kGameStepMilliseconds, true,
                             NewLambdaRunnable([this] { StepScene(); }).get());
  session_base_timer_ids_.push_back(step_scene_timer_id_);
  UpdateStepTimerLength();
}

auto HostActivity::GetAsHostActivity() -> HostActivity* { return this; }

auto HostActivity::NewMaterial(const std::string& name)
    -> Object::Ref<Material> {
  if (shutting_down_) {
    throw Exception("can't create materials during activity shutdown");
  }

  auto m(Object::New<Material>(name, scene()));
  materials_.emplace_back(m);
  return Object::Ref<Material>(m);
}

auto HostActivity::GetTexture(const std::string& name)
    -> Object::Ref<SceneTexture> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return GetAsset(&textures_, name, scene());
}

auto HostActivity::GetSound(const std::string& name)
    -> Object::Ref<SceneSound> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return GetAsset(&sounds_, name, scene());
}

auto HostActivity::GetData(const std::string& name)
    -> Object::Ref<SceneDataAsset> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return GetAsset(&datas_, name, scene());
}

auto HostActivity::GetMesh(const std::string& name) -> Object::Ref<SceneMesh> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return GetAsset(&meshes_, name, scene());
}

auto HostActivity::GetCollisionMesh(const std::string& name)
    -> Object::Ref<SceneCollisionMesh> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return GetAsset(&collision_meshes_, name, scene());
}

void HostActivity::SetPaused(bool val) {
  if (paused_ == val) {
    return;
  }
  paused_ = val;
  UpdateStepTimerLength();
}

void HostActivity::SetGameSpeed(float speed) {
  if (speed == game_speed_) {
    return;
  }
  assert(speed >= 0.0f);
  game_speed_ = speed;
  if (!started_) {
    return;
  }
  UpdateStepTimerLength();
}

void HostActivity::UpdateStepTimerLength() {
  if (!started_) {
    return;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrFatal();
  auto* host_session = host_session_.get();
  if (!host_session) {
    return;
  }
  if (game_speed_ == 0.0f || paused_) {
    host_session->SetBaseTimerLength(step_scene_timer_id_, -1);
  } else {
    host_session->SetBaseTimerLength(
        step_scene_timer_id_,
        std::max(1, static_cast<int>(
                        round(static_cast<float>(kGameStepMilliseconds)
                              / (game_speed_ * appmode->debug_speed_mult())))));
  }
}

void HostActivity::HandleOutOfBoundsNodes() {
  if (scene()->out_of_bounds_nodes().empty()) {
    out_of_bounds_in_a_row_ = 0;
    return;
  }

  // Make sure someone's handling our out-of-bounds messages.
  out_of_bounds_in_a_row_++;
  if (out_of_bounds_in_a_row_ > 100) {
    g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                         "100 consecutive out-of-bounds messages sent."
                         " They are probably not being handled properly");
    int j = 0;
    for (auto&& i : scene()->out_of_bounds_nodes()) {
      j++;
      Node* n = i.get();
      if (n) {
        std::string dstr;
        // GetDelegate() returns a new ref or nullptr.
        auto delegate{PythonRef::StolenSoft(n->GetDelegate())};
        if (delegate.exists()) {
          dstr = delegate.Str();
        }
        g_core->logging->Log(
            LogName::kBa, LogLevel::kWarning,
            "   node #" + std::to_string(j) + ": type='" + n->type()->name()
                + "' addr=" + Utils::PtrToString(i.get()) + " name='"
                + n->label() + "' delegate=" + dstr);
      }
    }
    out_of_bounds_in_a_row_ = 0;
  }

  // Send out-of-bounds messages to newly out-of-bounds nodes.
  for (auto&& i : scene()->out_of_bounds_nodes()) {
    Node* n = i.get();
    if (n) {
      n->DispatchOutOfBoundsMessage();
    }
  }
}

void HostActivity::RegisterPyActivity(PyObject* pyActivityObj) {
  assert(pyActivityObj && pyActivityObj != Py_None);
  assert(!py_activity_weak_ref_.exists());

  // Store a python weak-ref to this activity.
  py_activity_weak_ref_.Steal(PyWeakref_NewRef(pyActivityObj, nullptr));
}

auto HostActivity::GetPyActivity() const -> PyObject* {
  auto* ref_obj{py_activity_weak_ref_.get()};
  if (!ref_obj) {
    return nullptr;
  }
  PyObject* obj{};
  int result = PyWeakref_GetRef(ref_obj, &obj);
  // Return new obj ref (result 1) or nullptr for dead objs (result 0).
  if (result == 0 || result == 1) {
    return obj;
  }
  // Something went wrong and an exception is set. We don't expect this to
  // ever happen so currently just providing a simple error msg.
  assert(result == -1);
  PyErr_Clear();
  g_core->logging->Log(
      LogName::kBa, LogLevel::kError,
      "HostActivity::GetPyActivity(): error getting weakref obj.");
  return nullptr;
}

auto HostActivity::GetHostSession() -> HostSession* {
  return host_session_.get();
}

auto HostActivity::GetMutableScene() -> Scene* {
  Scene* sg = scene_.get();
  assert(sg);
  return sg;
}

void HostActivity::SetIsForeground(bool val) {
  // If we're foreground, set our scene as foreground.
  Scene* sg = scene();
  if (val && sg) {
    // Set it locally.

    if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
      appmode->SetForegroundScene(sg);
    }

    // Also push it to clients.
    if (SessionStream* out = GetSceneStream()) {
      out->SetForegroundScene(scene_.get());
    }
  }
}

auto HostActivity::globals_node() const -> GlobalsNode* {
  return globals_node_.get();
}

auto HostActivity::NewSimTimer(millisecs_t length, bool repeat,
                               Runnable* runnable) -> int {
  if (shutting_down_) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: Creating game timer during host-activity shutdown");
    return 123;  // Dummy.
  }
  if (length == 0 && repeat) {
    throw Exception("Can't add game-timer with length 0 and repeat on");
  }
  if (length < 0) {
    throw Exception("Timer length cannot be < 0 (got " + std::to_string(length)
                    + ")");
  }

  int offset = 0;
  Timer* t = scene_timers_.NewTimer(scene()->time(), length, offset,
                                    repeat ? -1 : 0, runnable);
  return t->id();
}

auto HostActivity::NewBaseTimer(millisecs_t length, bool repeat,
                                Runnable* runnable) -> int {
  if (shutting_down_) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: Creating session-time timer during host-activity shutdown");
    return 123;  // dummy...
  }
  if (length == 0 && repeat) {
    throw Exception("Can't add session-time timer with length 0 and repeat on");
  }
  if (length < 0) {
    throw Exception("Timer length cannot be < 0");
  }
  auto* host_session = host_session_.get();
  if (!host_session) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: Creating session-time timer in activity but host is dead.");
    return 123;  // dummy...
  }

  int timer_id =
      host_session->NewTimer(TimeType::kBase, length, repeat, runnable);

  session_base_timer_ids_.push_back(timer_id);
  return timer_id;
}

void HostActivity::DeleteSimTimer(int timer_id) {
  assert(g_base->InLogicThread());
  if (shutting_down_) {
    return;
  }
  scene_timers_.DeleteTimer(timer_id);
}

void HostActivity::DeleteBaseTimer(int timer_id) {
  assert(g_base->InLogicThread());
  if (shutting_down_) {
    return;
  }
  if (auto* host_session = host_session_.get()) {
    host_session->DeleteTimer(TimeType::kBase, timer_id);
  }
}

void HostActivity::StepDisplayTime(millisecs_t time_advance) {
  assert(g_base->InLogicThread());

  // If we haven't been told to start yet, don't do anything more.
  if (!started_) {
    return;
  }

  base_time_ += time_advance;

  // Periodically prune various dead refs.
  if (base_time_ > next_prune_time_) {
    PruneDeadMapRefs(&textures_);
    PruneDeadMapRefs(&sounds_);
    PruneDeadMapRefs(&collision_meshes_);
    PruneDeadMapRefs(&meshes_);
    PruneDeadRefs(&materials_);
    PruneDeadRefs(&context_calls_);
    PruneSessionBaseTimers();
    next_prune_time_ = base_time_ + 5379;
  }
}

void HostActivity::PruneSessionBaseTimers() {
  auto* host_session = host_session_.get();
  if (!host_session) {
    return;
  }

  // Quick-out; if all timers still exist, do nothing. This will usually
  // be the case.
  bool found_dead{};
  for (auto timer_id : session_base_timer_ids_) {
    if (!host_session->BaseTimerExists(timer_id)) {
      found_dead = true;
      break;
    }
  }
  if (!found_dead) {
    return;
  }

  // Ok, something died. Rebuild the list.
  std::vector<int> remaining_timer_ids;
  for (auto timer_id : session_base_timer_ids_) {
    if (host_session->BaseTimerExists(timer_id)) {
      remaining_timer_ids.push_back(timer_id);
    }
  }
  remaining_timer_ids.swap(session_base_timer_ids_);
}

void HostActivity::OnScreenSizeChange() { scene()->OnScreenSizeChange(); }
void HostActivity::LanguageChanged() { scene()->LanguageChanged(); }
void HostActivity::DebugSpeedMultChanged() { UpdateStepTimerLength(); }

void HostActivity::Draw(base::FrameDef* frame_def) {
  if (!started_) {
    return;
  }
  scene()->Draw(frame_def);
}

void HostActivity::DumpFullState(SessionStream* out) {
  // Add our scene.
  if (scene_.exists()) {
    scene_->Dump(out);
  }

  // Before doing any nodes, we need to create all materials.
  // (but *not* their components, which may reference the nodes that we haven't
  // made yet)
  for (auto&& i : materials_) {
    if (Material* m = i.get()) {
      out->AddMaterial(m);
    }
  }

  // Add our media.
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
  for (auto&& i : collision_meshes_) {
    if (SceneCollisionMesh* m = i.second.get()) {
      out->AddCollisionMesh(m);
    }
  }

  // Add scene's nodes.
  if (scene_.exists()) {
    scene_->DumpNodes(out);
  }

  // Ok, now we can fill out our materials since nodes/etc they reference
  // exists.
  for (auto&& i : materials_) {
    if (Material* m = i.get()) {
      m->DumpComponents(out);
    }
  }
}

auto HostActivity::NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                            Runnable* runnable) -> int {
  // Make sure the runnable passed in is reference-managed already.
  // (we may not add an initial reference ourself)
  assert(Object::IsValidManagedObject(runnable));

  // We currently support game and base timers.
  switch (timetype) {
    case TimeType::kSim:
      return NewSimTimer(length, repeat, runnable);
    case TimeType::kBase:
      return NewBaseTimer(length, repeat, runnable);
    default:
      // Fall back to default for descriptive error otherwise.
      return SceneV1Context::NewTimer(timetype, length, repeat, runnable);
  }
}

void HostActivity::DeleteTimer(TimeType timetype, int timer_id) {
  switch (timetype) {
    case TimeType::kSim:
      DeleteSimTimer(timer_id);
      break;
    case TimeType::kBase:
      DeleteBaseTimer(timer_id);
      break;
    default:
      // Fall back to default for descriptive error otherwise.
      SceneV1Context::DeleteTimer(timetype, timer_id);
      break;
  }
}

auto HostActivity::GetTime(TimeType timetype) -> millisecs_t {
  switch (timetype) {
    case TimeType::kSim:
      return scene()->time();
    case TimeType::kBase:
      return base_time();
    default:
      // Fall back to default for descriptive error otherwise.
      return SceneV1Context::GetTime(timetype);
  }
}

}  // namespace ballistica::scene_v1
