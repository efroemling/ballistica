// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/context.h"

#include "ballistica/game/host_activity.h"
#include "ballistica/generic/runnable.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

// Dynamically allocate this; don't want it torn down on quit.
Context* g_context = nullptr;

void Context::Init() {
  assert(!g_context);
  g_context = new Context(nullptr);
}

ContextTarget::ContextTarget() = default;
ContextTarget::~ContextTarget() = default;

auto ContextTarget::GetHostSession() -> HostSession* { return nullptr; }

auto ContextTarget::GetAsHostActivity() -> HostActivity* { return nullptr; }
auto ContextTarget::GetAsUIContext() -> UI* { return nullptr; }
auto ContextTarget::GetMutableScene() -> Scene* { return nullptr; }

Context::Context() : target(g_context->target) { assert(InGameThread()); }

auto Context::operator==(const Context& other) const -> bool {
  return (target.get() == other.target.get());
}

Context::Context(ContextTarget* target_in) : target(target_in) {}

auto Context::GetHostSession() const -> HostSession* {
  assert(InGameThread());
  if (target.exists()) return target->GetHostSession();
  return nullptr;
}

auto Context::GetHostActivity() const -> HostActivity* {
  ContextTarget* c = target.get();
  HostActivity* a = c ? c->GetAsHostActivity() : nullptr;
  assert(a == dynamic_cast<HostActivity*>(c));  // This should always match.
  return a;
}

auto Context::GetMutableScene() const -> Scene* {
  ContextTarget* c = target.get();
  Scene* sg = c ? c->GetMutableScene() : nullptr;
  return sg;
}

auto Context::GetUIContext() const -> UI* {
  ContextTarget* c = target.get();
  UI* uiContext = c ? c->GetAsUIContext() : nullptr;
  assert(uiContext == dynamic_cast<UI*>(c));
  return uiContext;
}

ScopedSetContext::ScopedSetContext(const Object::Ref<ContextTarget>& target) {
  assert(InGameThread());
  assert(g_context);
  context_prev_ = *g_context;
  g_context->target = target;
}

ScopedSetContext::ScopedSetContext(ContextTarget* target) {
  assert(InGameThread());
  assert(g_context);
  context_prev_ = *g_context;
  g_context->target = target;
}

ScopedSetContext::ScopedSetContext(const Context& context) {
  assert(InGameThread());
  assert(g_context);
  context_prev_ = *g_context;
  *g_context = context;
}

ScopedSetContext::~ScopedSetContext() {
  assert(InGameThread());
  assert(g_context);
  // Restore old.
  *g_context = context_prev_;
}

auto ContextTarget::NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                             const Object::Ref<Runnable>& runnable) -> int {
  // Make sure the passed runnable has a ref-count already
  // (don't want them to rely on us to create initial one).
  assert(runnable.exists());
  assert(runnable->is_valid_refcounted_object());

  switch (timetype) {
    case TimeType::kSim:
      throw Exception("Can't create 'sim' type timers in this context");
    case TimeType::kBase:
      throw Exception("Can't create 'base' type timers in this context");
    case TimeType::kReal:
      throw Exception("Can't create 'real' type timers in this context");
    default:
      throw Exception("Can't create that type timer in this context");
  }
}
void ContextTarget::DeleteTimer(TimeType timetype, int timer_id) {
  // We throw on NewTimer; lets just ignore anything that comes
  // through here to avoid messing up destructors.
  Log("ContextTarget::DeleteTimer() called; unexpected.");
}

auto ContextTarget::GetTime(TimeType timetype) -> millisecs_t {
  throw Exception("Unsupported time type for this context");
}

auto ContextTarget::GetTexture(const std::string& name)
    -> Object::Ref<Texture> {
  throw Exception("GetTexture() not supported in this context");
}

auto ContextTarget::GetSound(const std::string& name) -> Object::Ref<Sound> {
  throw Exception("GetSound() not supported in this context");
}

auto ContextTarget::GetData(const std::string& name) -> Object::Ref<Data> {
  throw Exception("GetData() not supported in this context");
}

auto ContextTarget::GetModel(const std::string& name) -> Object::Ref<Model> {
  throw Exception("GetModel() not supported in this context");
}

auto ContextTarget::GetCollideModel(const std::string& name)
    -> Object::Ref<CollideModel> {
  throw Exception("GetCollideModel() not supported in this context");
}

}  // namespace ballistica
