// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/context.h"

namespace ballistica::base {

ContextRef::ContextRef()
    : target_(g_base->context_ref->target_),
      empty_(g_base->context_ref->empty_) {
  assert(g_base->InLogicThread());
}

auto ContextRef::operator==(const ContextRef& other) const -> bool {
  // If our pointer matches theirs and our empty state matches theirs,
  // we're equal. The one exception to this is if we're both pointing to
  // targets that have died; in that case we have no way of knowing so
  // we say we're unequal.
  if (target_.Get() == other.target_.Get() && empty_ == other.empty_) {
    if (!empty_ && target_.Get() == nullptr) {
      return false;
    }
    return true;
  }
  return false;
}

ContextRef::ContextRef(Context* target_in)
    : target_(target_in), empty_(target_in == nullptr) {}

auto ContextRef::GetDescription() const -> std::string {
  if (auto* c = target_.Get()) {
    return c->GetContextDescription();
  }
  return "empty";
}
void Context::RegisterContextCall(PythonContextCall* call) {}

auto Context::GetContextDescription() -> std::string {
  return GetObjectDescription();
}

auto Context::ContextAllowsDefaultTimerTypes() -> bool { return true; }

ScopedSetContext::ScopedSetContext(const Object::Ref<Context>& target)
    : context_prev_(g_base->CurrentContext()) {
  g_base->context_ref->SetTarget(target.Get());
}

ScopedSetContext::ScopedSetContext(Context* target)
    : context_prev_(g_base->CurrentContext()) {
  g_base->context_ref->SetTarget(target);
}

ScopedSetContext::ScopedSetContext(const ContextRef& context)
    : context_prev_(g_base->CurrentContext()) {
  *g_base->context_ref = context;
}

ScopedSetContext::~ScopedSetContext() {
  assert(g_base);
  assert(g_base->InLogicThread());
  // Restore old.
  *g_base->context_ref = context_prev_;
}

}  // namespace ballistica::base
