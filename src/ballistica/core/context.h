// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_CONTEXT_H_
#define BALLISTICA_CORE_CONTEXT_H_

#include <string>

#include "ballistica/core/object.h"

namespace ballistica {

// Stores important environmental state such as the recipient of commands.
// Callbacks and other mechanisms should save/restore the context so that their
// effects properly apply to the place they came from.
class Context {
 public:
  static void Init();

  static auto current() -> const Context& {
    assert(g_context);

    // Context can only be accessed from the game thread.
    BA_PRECONDITION(InGameThread());

    return *g_context;
  }
  static void set_current(const Context& context) {
    // Context can only be accessed from the game thread.
    BA_PRECONDITION(InGameThread());

    *g_context = context;
  }

  // Return the current context target, raising an Exception if there is none.
  static auto current_target() -> ContextTarget& {
    ContextTarget* t = current().target.get();
    if (t == nullptr) {
      throw Exception("No context target set.");
    }
    return *t;
  }

  // Default constructor will capture a copy of the current global context.
  Context();
  explicit Context(ContextTarget* sgc);
  auto operator==(const Context& other) const -> bool;

  Object::WeakRef<ContextTarget> target;

  // If the current Context is (or is part of) a HostSession, return it;
  // otherwise return nullptr. be aware that this will return a session if the
  // context is *either* a host-activity or a host-session
  auto GetHostSession() const -> HostSession*;

  // return the current context as an HostActivity if it is one; otherwise
  // nullptr (faster than a dynamic_cast)
  auto GetHostActivity() const -> HostActivity*;

  // if the current context contains a scene that can be manipulated by
  // standard commands, this returns it.  This includes host-sessions,
  // host-activities, and the UI context.
  auto GetMutableScene() const -> Scene*;

  // return the current context as a UIContext if it is one; otherwise nullptr
  // (faster than a dynamic_cst)
  auto GetUIContext() const -> UI*;
};

// An interface for interaction with the engine; loading and wrangling media,
// nodes, etc.
// Note: it would seem like in an ideal world this could just be a pure
// virtual interface.
// However various things use WeakRef<ContextTarget> so technically they do
// all need to inherit from Object anyway.
class ContextTarget : public Object {
 public:
  ContextTarget();
  ~ContextTarget() override;

  // returns the HostSession associated with this context, (if there is one).
  virtual auto GetHostSession() -> HostSession*;

  // Utility functions for casting; faster than dynamic_cast.
  virtual auto GetAsHostActivity() -> HostActivity*;
  virtual auto GetAsUIContext() -> UI*;
  virtual auto GetMutableScene() -> Scene*;

  // Timer create/destroy functions.
  // Times are specified in milliseconds.
  // Exceptions should be thrown for unsupported timetypes in NewTimer.
  // Default NewTimer implementation throws a descriptive error, so it can
  // be useful to fall back on for unsupported cases.
  // NOTE: make sure runnables passed in here already have non-zero
  // ref-counts since a ref might not be grabbed here.
  virtual auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                        const Object::Ref<Runnable>& runnable) -> int;
  virtual void DeleteTimer(TimeType timetype, int timer_id);

  virtual auto GetTexture(const std::string& name) -> Object::Ref<Texture>;
  virtual auto GetSound(const std::string& name) -> Object::Ref<Sound>;
  virtual auto GetData(const std::string& name) -> Object::Ref<Data>;
  virtual auto GetModel(const std::string& name) -> Object::Ref<Model>;
  virtual auto GetCollideModel(const std::string& name)
      -> Object::Ref<CollideModel>;

  // Return the current time of a given type in milliseconds.
  // Exceptions should be thrown for unsupported timetypes.
  // Default implementation throws a descriptive error so can be
  // useful to fall back on for unsupported cases
  virtual auto GetTime(TimeType timetype) -> millisecs_t;
};

// Use this to push/pop a change to the current context
class ScopedSetContext {
 public:
  explicit ScopedSetContext(const Object::Ref<ContextTarget>& context);
  explicit ScopedSetContext(ContextTarget* context);
  explicit ScopedSetContext(const Context& context);
  ~ScopedSetContext();

 private:
  BA_DISALLOW_CLASS_COPIES(ScopedSetContext);
  Context context_prev_;
};

}  // namespace ballistica

#endif  // BALLISTICA_CORE_CONTEXT_H_
