// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/local_scene_context.h"

#include <string>

#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/assets/scene_asset.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/scene_depiction.h"
#include "ballistica/scene_v1/support/spaz_def.h"
#include "ballistica/shared/generic/runnable.h"

namespace ballistica::scene_v1 {

LocalSceneContext::LocalSceneContext(millisecs_t start_time,
                                     int protocol_version) {
  assert(g_base->InLogicThread());

  // Note that we deliberately never give this scene an output stream;
  // that is what keeps everything created in this context local to this
  // machine.
  base::ScopedSetContext ssc(this);  // So scene picks us up as context.
  scene_ = Object::New<Scene>(start_time);
  scene_->set_protocol_version(protocol_version);
}

LocalSceneContext::~LocalSceneContext() { Shutdown(); }

void LocalSceneContext::Shutdown() {
  if (shutting_down_) {
    return;
  }
  shutting_down_ = true;

  // Put the scene in shut-down mode before we start killing stuff.
  if (scene_.exists()) {
    scene_->set_shutting_down(true);
  }

  // Clear out all Python calls registered in our context so nothing
  // runs without a valid context behind it.
  for (auto&& i : context_calls_) {
    if (i.exists()) {
      i->MarkDead();
    }
  }

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
  for (auto&& i : spaz_defs_) {
    if (i.exists()) {
      i->MarkDead();
    }
  }
  for (auto&& i : depictions_) {
    if (i.exists()) {
      i->MarkDead();
    }
  }

  // Clearing timers and the scene should wipe out any remaining refs to
  // our Python side, allowing it to die.
  scene_timers_.Clear();
  scene_.Clear();
}

auto LocalSceneContext::GetMutableScene() -> Scene* {
  if (shutting_down_) {
    return nullptr;
  }
  return scene_.get();
}

void LocalSceneContext::RegisterContextCall(base::PythonContextCall* call) {
  assert(call);
  context_calls_.emplace_back(call);

  // If we're shutting down, just kill the call immediately.
  if (shutting_down_) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "Adding call to expired " + std::string(GetObjectTypeName())
            + "; call will not function: " + call->GetObjectDescription());
    call->MarkDead();
  }
}

void LocalSceneContext::Step() {
  assert(g_base->InLogicThread());
  if (shutting_down_) {
    return;
  }

  // Run our sim-time timers first, outside of our scene's step, so
  // callbacks are free to create/delete nodes in our scene.
  scene_timers_.Run(scene()->time());

  if (shutting_down_) {
    return;  // A timer may have killed us.
  }
  scene()->Step();

  // Periodically prune various dead refs.
  if (scene()->time() > next_prune_time_) {
    PruneDeadMapRefs(&textures_);
    PruneDeadMapRefs(&sounds_);
    PruneDeadMapRefs(&collision_meshes_);
    PruneDeadMapRefs(&meshes_);
    PruneDeadRefs(&materials_);
    PruneDeadRefs(&spaz_defs_);
    PruneDeadRefs(&depictions_);
    PruneDeadRefs(&context_calls_);
    next_prune_time_ = scene()->time() + 5379;
  }
}

void LocalSceneContext::Draw(base::FrameDef* frame_def) {
  if (shutting_down_) {
    return;
  }
  scene()->Draw(frame_def);
}

void LocalSceneContext::OnScreenSizeChange() {
  if (shutting_down_) {
    return;
  }
  scene()->OnScreenSizeChange();
}

void LocalSceneContext::LanguageChanged() {
  if (shutting_down_) {
    return;
  }
  scene()->LanguageChanged();
}

auto LocalSceneContext::NewTimer(TimeType timetype, TimerMedium length,
                                 bool repeat, Runnable* runnable) -> int {
  // Make sure the runnable passed in is reference-managed already.
  assert(Object::IsValidManagedObject(runnable));

  if (timetype != TimeType::kSim) {
    // Fall back to default for descriptive error.
    return SceneV1Context::NewTimer(timetype, length, repeat, runnable);
  }
  if (shutting_down_) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "WARNING: Creating sim timer during local scene shutdown");
    return 123;  // Dummy.
  }
  if (length == 0 && repeat) {
    throw Exception("Can't add sim-timer with length 0 and repeat on");
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

void LocalSceneContext::DeleteTimer(TimeType timetype, int timer_id) {
  assert(g_base->InLogicThread());
  if (timetype != TimeType::kSim) {
    SceneV1Context::DeleteTimer(timetype, timer_id);
    return;
  }
  if (shutting_down_) {
    return;
  }
  scene_timers_.DeleteTimer(timer_id);
}

auto LocalSceneContext::GetTime(TimeType timetype) -> millisecs_t {
  if (timetype == TimeType::kSim && !shutting_down_) {
    return scene()->time();
  }
  return SceneV1Context::GetTime(timetype);
}

auto LocalSceneContext::GetTexture(const std::string& name)
    -> Object::Ref<SceneTexture> {
  if (shutting_down_) {
    throw Exception("can't load assets during local scene shutdown");
  }
  return GetAsset(&textures_, name, scene());
}

auto LocalSceneContext::GetSound(const std::string& name)
    -> Object::Ref<SceneSound> {
  if (shutting_down_) {
    throw Exception("can't load assets during local scene shutdown");
  }
  return GetAsset(&sounds_, name, scene());
}

auto LocalSceneContext::GetData(const std::string& name)
    -> Object::Ref<SceneDataAsset> {
  if (shutting_down_) {
    throw Exception("can't load assets during local scene shutdown");
  }
  return GetAsset(&datas_, name, scene());
}

auto LocalSceneContext::GetMesh(const std::string& name)
    -> Object::Ref<SceneMesh> {
  if (shutting_down_) {
    throw Exception("can't load assets during local scene shutdown");
  }
  return GetAsset(&meshes_, name, scene());
}

auto LocalSceneContext::GetCollisionMesh(const std::string& name)
    -> Object::Ref<SceneCollisionMesh> {
  if (shutting_down_) {
    throw Exception("can't load assets during local scene shutdown");
  }
  return GetAsset(&collision_meshes_, name, scene());
}

auto LocalSceneContext::NewMaterial(const std::string& name)
    -> Object::Ref<Material> {
  if (shutting_down_) {
    throw Exception("can't create materials during local scene shutdown");
  }
  auto m(Object::New<Material>(name, scene()));
  materials_.emplace_back(m);
  return Object::Ref<Material>(m);
}

auto LocalSceneContext::NewSpazDef(const std::string& json)
    -> Object::Ref<SpazDef> {
  if (shutting_down_) {
    throw Exception("can't create spaz defs during local scene shutdown");
  }
  auto d(Object::New<SpazDef>(json, scene()));
  spaz_defs_.emplace_back(d);
  return Object::Ref<SpazDef>(d);
}

auto LocalSceneContext::NewDepiction(const std::string& json)
    -> Object::Ref<SceneDepiction> {
  if (shutting_down_) {
    throw Exception("can't create depictions during local scene shutdown");
  }
  auto d(Object::New<SceneDepiction>(json, scene()));
  depictions_.emplace_back(d);
  return Object::Ref<SceneDepiction>(d);
}

}  // namespace ballistica::scene_v1
