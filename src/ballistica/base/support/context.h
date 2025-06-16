// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_CONTEXT_H_
#define BALLISTICA_BASE_SUPPORT_CONTEXT_H_

#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Ballistica's context system allows its various subsystems to provide
// arbitrary contextual data for commands to use. Standard callbacks and
// other mechanisms are set up to preserve and restore context before
// running, and objects can also be invalidated or otherwise cleaned up
// when the context they were created under dies.
//
// The end goal of all this is to support api styles for end users where
// standalone snippets of code can be useful; ie: something like
// bs.newnode() to create something meaningful without having to worry
// about acquiring a scene pointer or whatever.

// FIXME: Once we have death-callbacks for objects, we should update this
//  to be aware once a pointed-to context has died. Attempting to use the
//  context-ref in any way after that point should error. Currently it just
//  functions as an empty context in that case which is incorrect.

/// A utility class wrapping a weak-reference to a context_ref with some
/// extra functionality.
class ContextRef {
 public:
  /// Return a description of the context we're pointing at.
  auto GetDescription() const -> std::string;

  /// Default constructor grabs the current context.
  ContextRef();
  explicit ContextRef(Context* sgc);

  /// ContextRefs are considered equal if both are pointing to the exact
  /// same Context object (or both are pointing to no Context).
  auto operator==(const ContextRef& other) const -> bool;

  template <typename T>
  auto GetContextTyped() const -> T* {
    // Ew; dynamic cast.
    //
    // Note: if it ever seems like speed is an issue here, we can cache the
    // results with std::type_index entries. There should generally be a
    // very small number of types involved.
    return dynamic_cast<T*>(target_.get());
  }

  /// An empty context-ref was explicitly set to an empty state. Note that
  /// this is different than an expired context-ref, which originally
  /// pointed to some context that has since died.
  auto IsEmpty() const { return empty_; }

  /// Has this context died since it was set? Note that a context created as
  /// empty is not considered expired.
  auto IsExpired() const -> bool {
    if (empty_) {
      return false;  // Can't kill what was never alive.
    }
    return !target_.exists();
  }

  /// Return the context this ref points to. This will be nullptr for empty
  /// contexts. Throws an exception if a target context was set but has
  /// expired.
  auto Get() const -> Context* {
    auto* target = target_.get();
    if (target == nullptr && !empty_) {
      // We once existed but now don't.
      throw Exception("Context is expired.", PyExcType::kNotFound);
    }
    return target;
  }

  void SetTarget(Context* target) {
    target_ = target;
    empty_ = (target == nullptr);
  }

 private:
  Object::WeakRef<Context> target_;
  bool empty_;
};

/// Object containing the actual context_ref data/information. App-modes can
/// subclass this to provide the actual context_ref they desire, and then
/// code can use CurrentTyped() to safely retrieve context_ref as that type.
class Context : public Object {
 public:
  /// Return the current context_ref cast to a desired type. Throws an
  /// Exception if the context_ref is unset or is another type.
  template <typename T>
  static auto CurrentTyped() -> T& {
    T* t = g_base->CurrentContext().GetContextTyped<T>();
    if (t == nullptr) {
      throw Exception("Context of the provided type is not set.",
                      PyExcType::kContext);
    }
    return *t;
  }

  /// Called when a PythonContextCall is created in this context_ref. The
  /// context_ref class may want to store a weak-reference to the call and
  /// inform the call when the context_ref is going down so that resources
  /// may be freed. Other permanent contexts may not need to bother.
  ///
  /// FIXME: This mechanism can probably be generalized so that other things
  ///  such as assets and timers can use it.
  virtual void RegisterContextCall(PythonContextCall* call);

  /// Return a short description of the context_ref; will be used when
  /// printing context_ref debug information/etc. By default this uses
  /// Object::GetObjectDescription().
  virtual auto GetContextDescription() -> std::string;

  /// Return whether this context should allow default timer-types to be
  /// created within it (AppTimer, DisplayTimer). Scene type contexts
  /// generally have their own timer types which are better integrated with
  /// scenes (responding to changes in game speed/etc.) so this can be used
  /// to encourage/enforce usage of those timers.
  virtual auto ContextAllowsDefaultTimerTypes() -> bool;
};

// Use this to push/pop a change to the current context
class ScopedSetContext {
 public:
  explicit ScopedSetContext(const Object::Ref<Context>& context);
  explicit ScopedSetContext(Context* context);
  explicit ScopedSetContext(const ContextRef& context);
  ~ScopedSetContext();

 private:
  BA_DISALLOW_CLASS_COPIES(ScopedSetContext);
  ContextRef context_prev_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_CONTEXT_H_
