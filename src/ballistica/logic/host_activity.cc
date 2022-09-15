// Released under the MIT License. See LICENSE for details.

#include "ballistica/logic/host_activity.h"

#include "ballistica/assets/component/collide_model.h"
#include "ballistica/assets/component/data.h"
#include "ballistica/assets/component/model.h"
#include "ballistica/assets/component/sound.h"
#include "ballistica/assets/component/texture.h"
#include "ballistica/dynamics/material/material.h"
#include "ballistica/generic/lambda_runnable.h"
#include "ballistica/generic/timer.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/logic/player.h"
#include "ballistica/logic/session/host_session.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_context_call.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/scene/node/globals_node.h"
#include "ballistica/scene/node/node_type.h"
#include "ballistica/scene/scene_stream.h"

namespace ballistica {

HostActivity::HostActivity(HostSession* host_session) {
  // Store a link to the HostSession and add ourself to it.
  host_session_ = host_session;

  // Create our game timer - gets called whenever game should step.
  step_scene_timer_ =
      base_timers_.NewTimer(base_time_, kGameStepMilliseconds, 0, -1,
                            NewLambdaRunnable([this] { StepScene(); }));
  SetGameSpeed(1.0f);
  {
    ScopedSetContext cp(this);  // So scene picks us up as context.
    scene_ = Object::New<Scene>(0);

    // If there's an output stream, add to it.
    if (SceneStream* out = host_session->GetSceneStream()) {
      out->AddScene(scene_.get());
    }
  }
}

HostActivity::~HostActivity() {
  shutting_down_ = true;

  // Put the scene in shut-down mode before we start killing stuff.
  // (this generates warnings, suppresses messages, etc)
  scene_->set_shutting_down(true);

  // Clear out all python calls registered in our context.
  // (should wipe out refs to our activity and prevent them from running without
  // a valid activity context)
  for (auto&& i : python_calls_) {
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
  for (auto&& i : collide_models_) {
    if (i.second.exists()) {
      i.second->MarkDead();
    }
  }
  for (auto&& i : materials_) {
    if (i.exists()) {
      i->MarkDead();
    }
  }

  // Clear our timers and scene; this should wipe out any remaining refs to our
  // python activity, allowing it to die.
  base_timers_.Clear();
  sim_timers_.Clear();
  scene_.Clear();

  // Report outstanding calls. There shouldn't be any at this point. Actually it
  // turns out there's generally 1; whichever call was responsible for killing
  // this activity will still be in progress.. so let's report on 2 or more I
  // guess.
  if (g_buildconfig.debug_build()) {
    PruneDeadRefs(&python_calls_);
    if (python_calls_.size() > 1) {
      std::string s = std::to_string(python_calls_.size())
                      + " live PythonContextCalls at shutdown for "
                      + "HostActivity" + " (1 call is expected):";
      int count = 1;
      for (auto& python_call : python_calls_)
        s += "\n  " + std::to_string(count++) + ": "
             + (*python_call).GetObjectDescription();
      Log(LogLevel::kWarning, s);
    }
  }
}

auto HostActivity::GetSceneStream() const -> SceneStream* {
  if (!host_session_.exists()) return nullptr;
  return host_session_->GetSceneStream();
}

auto HostActivity::SetGlobalsNode(GlobalsNode* node) -> void {
  globals_node_ = node;
}

void HostActivity::StepScene() {
  int cycle_count = 1;
  if (host_session_->benchmark_type() == BenchmarkType::kCPU) {
    cycle_count = 100;
  }

  for (int cycle = 0; cycle < cycle_count; ++cycle) {
    assert(InLogicThread());

    // Clear our player-positions for this step.
    // FIXME: Move this to scene and/or player node.
    assert(host_session_.exists());
    for (auto&& player : host_session_->players()) {
      assert(player.exists());
      player->set_have_position(false);
    }

    // Run our sim-time timers.
    sim_timers_.Run(scene()->time());

    // Send die-messages/etc to out-of-bounds stuff.
    HandleOutOfBoundsNodes();

    scene()->Step();
  }
}

void HostActivity::RegisterCall(PythonContextCall* call) {
  assert(call);
  python_calls_.emplace_back(call);

  // If we're shutting down, just kill the call immediately.
  // (we turn all of our calls to no-ops as we shut down)
  if (shutting_down_) {
    Log(LogLevel::kWarning,
        "Adding call to expired activity; call will not function: "
            + call->GetObjectDescription());
    call->MarkDead();
  }
}

void HostActivity::start() {
  if (_started) {
    Log(LogLevel::kError, "Start called twice for activity.");
  }
  _started = true;
}

auto HostActivity::GetAsHostActivity() -> HostActivity* { return this; }

auto HostActivity::NewMaterial(const std::string& name)
    -> Object::Ref<Material> {
  if (shutting_down_) {
    throw Exception("can't create materials during activity shutdown");
  }

  auto m(Object::New<Material>(name, scene()));
  materials_.emplace_back(m);
  return m;
}

auto HostActivity::GetTexture(const std::string& name) -> Object::Ref<Texture> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return Assets::GetAsset(&textures_, name, scene());
}

auto HostActivity::GetSound(const std::string& name) -> Object::Ref<Sound> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return Assets::GetAsset(&sounds_, name, scene());
}

auto HostActivity::GetData(const std::string& name) -> Object::Ref<Data> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return Assets::GetAsset(&datas_, name, scene());
}

auto HostActivity::GetModel(const std::string& name) -> Object::Ref<Model> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return Assets::GetAsset(&models_, name, scene());
}

auto HostActivity::GetCollideModel(const std::string& name)
    -> Object::Ref<CollideModel> {
  if (shutting_down_) {
    throw Exception("can't load assets during activity shutdown");
  }
  return Assets::GetAsset(&collide_models_, name, scene());
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
  UpdateStepTimerLength();
}

void HostActivity::UpdateStepTimerLength() {
  if (game_speed_ == 0.0f || paused_) {
    step_scene_timer_->SetLength(-1, true, base_time_);
  } else {
    step_scene_timer_->SetLength(
        std::max(1, static_cast<int>(
                        round(static_cast<float>(kGameStepMilliseconds)
                              / (game_speed_ * g_logic->debug_speed_mult())))),
        true, base_time_);
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
    Log(LogLevel::kWarning,
        "100 consecutive out-of-bounds messages sent."
        " They are probably not being handled properly");
    int j = 0;
    for (auto&& i : scene()->out_of_bounds_nodes()) {
      j++;
      Node* n = i.get();
      if (n) {
        std::string dstr;
        PyObject* delegate = n->GetDelegate();
        if (delegate) {
          dstr = PythonRef(delegate, PythonRef::kAcquire).Str();
        }
        Log(LogLevel::kWarning,
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
  PyObject* obj = py_activity_weak_ref_.get();
  if (!obj) return Py_None;
  return PyWeakref_GetObject(obj);
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
    g_logic->SetForegroundScene(sg);

    // Also push it to clients.
    if (SceneStream* out = GetSceneStream()) {
      out->SetForegroundScene(scene_.get());
    }
  }
}

auto HostActivity::globals_node() const -> GlobalsNode* {
  return globals_node_.get();
}

auto HostActivity::NewSimTimer(millisecs_t length, bool repeat,
                               const Object::Ref<Runnable>& runnable) -> int {
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
  Timer* t = sim_timers_.NewTimer(scene()->time(), length, offset,
                                  repeat ? -1 : 0, runnable);
  return t->id();
}

auto HostActivity::NewBaseTimer(millisecs_t length, bool repeat,
                                const Object::Ref<Runnable>& runnable) -> int {
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

  int offset = 0;
  Timer* t = base_timers_.NewTimer(base_time_, length, offset, repeat ? -1 : 0,
                                   runnable);
  return t->id();
}

void HostActivity::DeleteSimTimer(int timer_id) {
  assert(InLogicThread());
  if (shutting_down_) return;
  sim_timers_.DeleteTimer(timer_id);
}

void HostActivity::DeleteBaseTimer(int timer_id) {
  assert(InLogicThread());
  if (shutting_down_) return;
  base_timers_.DeleteTimer(timer_id);
}

auto HostActivity::Update(millisecs_t time_advance) -> millisecs_t {
  assert(InLogicThread());

  // We can be killed at any time, so let's keep an eye out for that.
  WeakRef<HostActivity> test_ref(this);
  assert(test_ref.exists());

  // If we haven't been told to start yet, don't do anything more.
  if (!_started) {
    return 100;
  }

  // Advance base time by the specified amount, stopping at all timers along the
  // way.
  millisecs_t target_base_time = base_time_ + time_advance;
  while (!base_timers_.empty()
         && (base_time_ + base_timers_.GetTimeToNextExpire(base_time_)
             <= target_base_time)) {
    base_time_ += base_timers_.GetTimeToNextExpire(base_time_);
    base_timers_.Run(base_time_);
    if (!test_ref.exists()) {
      return 1000;  // The last timer run might have killed us.
    }
  }
  base_time_ = target_base_time;

  // Periodically prune various dead refs.
  if (base_time_ > next_prune_time_) {
    PruneDeadMapRefs(&textures_);
    PruneDeadMapRefs(&sounds_);
    PruneDeadMapRefs(&collide_models_);
    PruneDeadMapRefs(&models_);
    PruneDeadRefs(&materials_);
    PruneDeadRefs(&python_calls_);
    next_prune_time_ = base_time_ + 5000;
  }

  // Return the time until the next timer goes off.
  return base_timers_.empty() ? 1000
                              : base_timers_.GetTimeToNextExpire(base_time_);
}

void HostActivity::ScreenSizeChanged() { scene()->ScreenSizeChanged(); }
void HostActivity::LanguageChanged() { scene()->LanguageChanged(); }
void HostActivity::DebugSpeedMultChanged() { UpdateStepTimerLength(); }
void HostActivity::GraphicsQualityChanged(GraphicsQuality q) {
  scene()->GraphicsQualityChanged(q);
}

void HostActivity::Draw(FrameDef* frame_def) {
  if (!_started) {
    return;
  }
  scene()->Draw(frame_def);
}

void HostActivity::DumpFullState(SceneStream* out) {
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
  for (auto&& i : collide_models_) {
    if (CollideModel* m = i.second.get()) {
      out->AddCollideModel(m);
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
                            const Object::Ref<Runnable>& runnable) -> int {
  // Make sure the runnable passed in is reference-managed already.
  // (we may not add an initial reference ourself)
  assert(runnable->is_valid_refcounted_object());

  // We currently support game and base timers.
  switch (timetype) {
    case TimeType::kSim:
      return NewSimTimer(length, repeat, runnable);
    case TimeType::kBase:
      return NewBaseTimer(length, repeat, runnable);
    default:
      // Fall back to default for descriptive error otherwise.
      return ContextTarget::NewTimer(timetype, length, repeat, runnable);
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
      ContextTarget::DeleteTimer(timetype, timer_id);
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
      return ContextTarget::GetTime(timetype);
  }
}

}  // namespace ballistica
