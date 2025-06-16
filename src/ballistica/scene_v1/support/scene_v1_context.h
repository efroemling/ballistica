// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SCENE_V1_CONTEXT_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SCENE_V1_CONTEXT_H_

#include <string>

#include "ballistica/base/support/context.h"
#include "ballistica/scene_v1/scene_v1.h"

namespace ballistica::scene_v1 {

/// A context-ref specific to SceneV1.
class ContextRefSceneV1 : public base::ContextRef {
 public:
  ContextRefSceneV1() : ContextRef() {}
  explicit ContextRefSceneV1(base::Context* sgc) : ContextRef(sgc) {}

  /// Return a scene_v1 version of the current context_ref-ref.
  static auto FromCurrent() -> ContextRefSceneV1 {
    return ContextRefSceneV1(g_base->CurrentContext().Get());
  }

  /// Creates from app_mode's GetForegroundContext().
  static auto FromAppForegroundContext() -> ContextRefSceneV1;

  /// If the current Context is (or is part of) a HostSession, return it;
  /// otherwise return nullptr. be aware that this will return a session if
  /// the context is *either* a host-activity or a host-session
  auto GetHostSession() const -> HostSession*;

  /// Return the current context as an HostActivity if it is one; otherwise
  /// nullptr (faster than a dynamic_cast)
  auto GetHostActivity() const -> HostActivity*;

  /// If the current context contains a scene that can be manipulated by
  /// standard commands, this returns it. This includes host-sessions,
  /// host-activities, and the UI context.
  auto GetMutableScene() const -> Scene*;
};

/// Object containing some sort of context_ref. App-modes can subclass this
/// to provide the actual context_ref they desire, and then code can use
/// GetTyped() to safely retrieve context_ref as that type.
class SceneV1Context : public base::Context {
 public:
  static auto Current() -> SceneV1Context& {
    return Context::CurrentTyped<SceneV1Context>();
  }

  auto GetContextDescription() -> std::string override;

  /// Return the HostSession associated with this context, (if there is
  /// one).
  virtual auto GetHostSession() -> HostSession*;

  /// Utility functions for casting; faster than dynamic_cast.
  virtual auto GetAsHostActivity() -> HostActivity*;
  virtual auto GetMutableScene() -> Scene*;

  // Timer create/destroy functions.
  // Times are specified in milliseconds.
  // Exceptions should be thrown for unsupported timetypes in NewTimer.
  // Default NewTimer implementation throws a descriptive error, so it can
  // be useful to fall back on for unsupported cases.
  virtual auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                        Runnable* runnable) -> int;
  virtual void DeleteTimer(TimeType timetype, int timer_id);

  virtual auto GetTexture(const std::string& name) -> Object::Ref<SceneTexture>;
  virtual auto GetSound(const std::string& name) -> Object::Ref<SceneSound>;
  virtual auto GetData(const std::string& name) -> Object::Ref<SceneDataAsset>;
  virtual auto GetMesh(const std::string& name) -> Object::Ref<SceneMesh>;
  virtual auto GetCollisionMesh(const std::string& name)
      -> Object::Ref<SceneCollisionMesh>;

  /// Return the current time of a given type in milliseconds. Exceptions
  /// should be thrown for unsupported timetypes. Default implementation
  /// throws a descriptive error so can be useful to fall back on for
  /// unsupported cases
  virtual auto GetTime(TimeType timetype) -> millisecs_t;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SCENE_V1_CONTEXT_H_
