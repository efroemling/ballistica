// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/scene_v1_context.h"

#include <Python.h>

#include <string>

#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/shared/generic/runnable.h"

namespace ballistica::scene_v1 {

auto ContextRefSceneV1::FromAppForegroundContext() -> ContextRefSceneV1 {
  auto* c = g_base->app_mode()->GetForegroundContext().Get();
  return ContextRefSceneV1(c);
}

auto ContextRefSceneV1::GetHostSession() const -> HostSession* {
  assert(g_base->InLogicThread());
  if (auto* c = GetContextTyped<SceneV1Context>()) {
    return c->GetHostSession();
  }
  return nullptr;
}

auto ContextRefSceneV1::GetHostActivity() const -> HostActivity* {
  assert(g_base->InLogicThread());
  auto* c = GetContextTyped<SceneV1Context>();
  HostActivity* a = c ? c->GetAsHostActivity() : nullptr;
  // This should always match.
  assert(a == dynamic_cast<HostActivity*>(c));
  return a;
}

auto ContextRefSceneV1::GetMutableScene() const -> Scene* {
  assert(g_base->InLogicThread());
  auto* c = GetContextTyped<SceneV1Context>();
  Scene* s = c ? c->GetMutableScene() : nullptr;
  return s;
}

auto SceneV1Context::GetContextDescription() -> std::string {
  if (HostActivity* ha = GetAsHostActivity()) {
    // Return our Python activity class description if possible.

    // GetPyActivity returns a new ref or nullptr.
    auto ha_obj{PythonRef::StolenSoft(ha->GetPyActivity())};
    if (ha_obj.exists() && ha_obj.get() != Py_None) {
      return ha_obj.Str();
    }
  }
  return Context::GetContextDescription();
}

auto SceneV1Context::GetHostSession() -> HostSession* { return nullptr; }

auto SceneV1Context::GetAsHostActivity() -> HostActivity* { return nullptr; }
auto SceneV1Context::GetMutableScene() -> Scene* { return nullptr; }

auto SceneV1Context::NewTimer(TimeType timetype, TimerMedium length,
                              bool repeat, Runnable* runnable) -> int {
  // Make sure the passed runnable has a ref-count already
  // (don't want them to rely on us to create initial one).
  assert(Object::IsValidManagedObject(runnable));

  switch (timetype) {
    case TimeType::kSim:
      throw Exception("Can't create 'sim' type timers in this context_ref");
    case TimeType::kBase:
      throw Exception("Can't create 'base' type timers in this context_ref");
    case TimeType::kReal:
      throw Exception("Can't create 'real' type timers in this context_ref");
    default:
      throw Exception("Can't create that type timer in this context_ref");
  }
}
void SceneV1Context::DeleteTimer(TimeType timetype, int timer_id) {
  // We throw on NewTimer; lets just ignore anything that comes
  // through here to avoid messing up destructors.
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       "ContextTarget::DeleteTimer() called; unexpected.");
}

auto SceneV1Context::GetTime(TimeType timetype) -> millisecs_t {
  throw Exception("Unsupported time type for this context_ref");
}

auto SceneV1Context::GetTexture(const std::string& name)
    -> Object::Ref<SceneTexture> {
  throw Exception("SysTexture() not supported in this context_ref");
}

auto SceneV1Context::GetSound(const std::string& name)
    -> Object::Ref<SceneSound> {
  throw Exception("sound() not supported in this context_ref");
}

auto SceneV1Context::GetData(const std::string& name)
    -> Object::Ref<SceneDataAsset> {
  throw Exception("GetData() not supported in this context_ref");
}

auto SceneV1Context::GetMesh(const std::string& name)
    -> Object::Ref<SceneMesh> {
  throw Exception("SysMesh() not supported in this context_ref");
}

auto SceneV1Context::GetCollisionMesh(const std::string& name)
    -> Object::Ref<SceneCollisionMesh> {
  throw Exception("GetCollisionMesh() not supported in this context_ref");
}

}  // namespace ballistica::scene_v1
