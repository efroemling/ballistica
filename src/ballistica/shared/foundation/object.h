// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_OBJECT_H_
#define BALLISTICA_SHARED_FOUNDATION_OBJECT_H_

#include <string>
#include <utility>
#include <vector>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica {

/// Objects supporting strong and weak referencing and thread enforcement.
class Object {
 public:
  Object();
  virtual ~Object();

  // Object classes can provide descriptive names for themselves; these are
  // used for debugging and other purposes. The default is to use the C++
  // symbol name, demangling it when possible. IMPORTANT: Do not rely on
  // this being consistent across builds/platforms.
  virtual auto GetObjectTypeName() const -> std::string;

  // Provide a brief description of this particular object; by default
  // returns type-name plus address.
  virtual auto GetObjectDescription() const -> std::string;

  enum class ThreadOwnership {
    /// Uses class' GetDefaultOwnerThread() call.
    kClassDefault,
    /// Requires graphics context to be active.
    kGraphicsContext,
    /// Uses whichever thread next acquires/accesses a reference.
    kNextReferencing
  };

#if BA_DEBUG_BUILD

  /// This is called when adding or removing a reference to an Object; it
  /// can perform sanity-tests to make sure references are not being added
  /// at incorrect times or from incorrect threads. The default
  /// implementation uses the per-object ThreadOwnership/EventLoopID values
  /// accessible below.
  ///
  /// NOTE: This check runs *only* in the debug build so don't include any
  /// logical side-effects in these checks!
  void ObjectThreadCheck() const;

#endif

  /// Called on newly constructed objects by the various New() methods. This
  /// allows classes to run code after their full class heirarchy has been
  /// constructed, meaning things like virtual functions will work as
  /// expected.
  virtual void ObjectPostInit();

  /// Called by the default ObjectThreadCheck() to determine ownership for
  /// an Object. By default, an object is owned by a specific thread,
  /// defaulting to the logic thread.
  virtual auto GetThreadOwnership() const -> ThreadOwnership;

  /// Return the exact thread to check for with
  /// ThreadOwnership::kClassDefault (in the default ObjectThreadCheck
  /// implementation at least). Default returns EventLoopID::kLogic
  virtual auto GetDefaultOwnerThread() const -> EventLoopID;

  /// Set thread ownership for an individual object.
  void SetThreadOwnership(ThreadOwnership ownership) {
#if BA_DEBUG_BUILD
    thread_ownership_ = ownership;
    if (thread_ownership_ == ThreadOwnership::kNextReferencing) {
      owner_thread_ = EventLoopID::kInvalid;
    }
#endif
  }

  // Return true if the provided obj ptr is not null, is ref-counted, and
  // has at least 1 strong ref. This is generally a good thing for calls
  // accepting object ptrs to check. It is considered bad practice to
  // perform operations with not-yet-reffed objects. Note that in some cases
  // this may return false positives, so only use this as a sanity check and
  // only take action for a negative result.
  static auto IsValidManagedObject(Object* obj) -> bool {
    if (!obj) {
      return false;
    }
#if BA_DEBUG_BUILD
    if (obj->object_is_dead_) {
      return false;
    }
#endif
    return (obj->object_strong_ref_count_ > 0);
  }

  // Return true if the object seems to be valid and was allocated as
  // unmanaged. Code that plans to explicitly delete raw passed pointers can
  // check this for peace of mind. Note that for some build types this will
  // return false positives, so only use this as a sanity check and only
  // take action for negative results.
  static auto IsValidUnmanagedObject(Object* obj) -> bool {
    if (!obj) {
      return false;
    }
#if BA_DEBUG_BUILD
    if (obj->object_is_dead_) {
      return false;
    }
    if (!obj->object_is_unmanaged_) {
      return false;
    }
#endif
    // We don't store specifics in release builds; assume everything is
    // peachy.
    return true;
  }

  auto object_strong_ref_count() const -> int {
    return object_strong_ref_count_;
  }

  /// Increment the strong reference count for an Object. In most cases you
  /// should let Ref objects handle this for you and not call this directly.
  void ObjectIncrementStrongRefCount() {
#if BA_DEBUG_BUILD
    ObjectUpdateForAcquire();
    ObjectThreadCheck();

    // Obvs shouldn't be referencing dead stuff.
    assert(!object_is_dead_);

    // Complain if trying ot create a ref to a non-ref-counted obj.
    if (!object_is_ref_counted_) {
      FatalError("Attempting to create a strong-ref to non-refcounted obj: "
                 + GetObjectDescription());
    }
    object_has_been_strong_reffed_ = true;
#endif  // BA_DEBUG_BUILD

    object_strong_ref_count_++;
  }

  /// Decrement the strong reference count for the Object, deleting it if it
  /// hits zero. In most cases you should let Ref objects handle this for
  /// you and not call this directly.
  void ObjectDecrementStrongRefCount() {
#if BA_DEBUG_BUILD
    ObjectThreadCheck();
#endif
    assert(object_strong_ref_count_ > 0);
    object_strong_ref_count_--;
    if (object_strong_ref_count_ == 0) {
#if BA_DEBUG_BUILD
      object_is_dead_ = true;
#endif
      delete this;
    }
  }

  template <typename T = Object>
  class Ref;
  template <typename T = Object>
  class WeakRef;

  class WeakRefBase {
   public:
    WeakRefBase() = default;
    ~WeakRefBase() { Release(); }

    void Release() {
      if (obj_) {
#if BA_DEBUG_BUILD
        obj_->ObjectThreadCheck();
#endif
        if (next_) {
          next_->prev_ = prev_;
        }
        if (prev_) {
          prev_->next_ = next_;
        } else {
          obj_->object_weak_refs_ = next_;
        }
        obj_ = nullptr;
        next_ = prev_ = nullptr;
      } else {
        assert(next_ == nullptr && prev_ == nullptr);
      }
    }

    auto exists() const -> bool { return obj_ != nullptr; }

    void Clear() { Release(); }

   private:
    Object* obj_{};
    WeakRefBase* prev_{};
    WeakRefBase* next_{};
    friend class Object;
  };  // WeakRefBase

  /// A weak-reference to an instance of a specific Object subclass.
  template <typename T>
  class WeakRef : public WeakRefBase {
   public:
    /// Convenience wrapper for Object::IsValidManagedObject.
    auto IsValidManagedObject() const -> bool {
      if (auto* obj = get()) {
        return Object::IsValidManagedObject(obj);
      }
      return false;
    }

    /// Convenience wrapper for Object::IsValidUnmanagedObject.
    auto IsValidUnmanagedObject() const -> bool {
      if (auto* obj = get()) {
        return Object::IsValidUnmanagedObject(obj);
      }
      return false;
    }

    // Return a pointer or nullptr.
    auto get() const -> T* {
      // Yes, reinterpret_cast is evil, but we make sure we only operate on
      // cases where this is valid (see Acquire()).
      return reinterpret_cast<T*>(obj_);
    }

    // ----------------------------- Operators ---------------------------------

    /// Access the referenced object; throws an Exception if ref is invalid.
    auto operator*() const -> T& {
      if (!obj_) {
        throw Exception(
            "Dereferencing invalid " + static_type_name<T>() + " ref.",
            PyExcType::kReference);
      }

      // Yes, reinterpret_cast is evil, but we make sure we only operate on
      // cases where this is valid (see Acquire()).
      return *reinterpret_cast<T*>(obj_);
    }

    /// Access the referenced object; throws an Exception if ref is invalid.
    auto operator->() const -> T* {
      if (!obj_) {
        throw Exception(
            "Dereferencing invalid " + static_type_name<T>() + " ref.",
            PyExcType::kReference);
      }

      // Yes, reinterpret_cast is evil, but we make sure we only operate on
      // cases where this is valid (see Acquire()).
      return reinterpret_cast<T*>(obj_);
    }

    /// Compare to a pointer of any compatible type.
    template <typename U>
    auto operator==(U* ptr) -> bool {
      return (get() == ptr);
    }

    /// Compare to a pointer of any compatible type.
    template <typename U>
    auto operator!=(U* ptr) -> bool {
      return (get() != ptr);
    }

    /// Compare to a strong ref of any compatible type.
    template <typename U>
    auto operator==(const Ref<U>& ref) -> bool {
      return (get() == ref.get());
    }

    /// Compare to a strong ref to a compatible type.
    template <typename U>
    auto operator!=(const Ref<U>& ref) -> bool {
      return (get() != ref.get());
    }

    /// Compare to a weak ref of any compatible type.
    template <typename U>
    auto operator==(const WeakRef<U>& ref) -> bool {
      return (get() == ref.get());
    }

    /// Compare to a weak ref of any compatible type.
    template <typename U>
    auto operator!=(const WeakRef<U>& ref) -> bool {
      return (get() != ref.get());
    }

    /// Assign from our exact type. Note: it might seem like our template
    /// assigment operator (taking typename U) would cover this case, but
    /// that's not how it works. If we remove this, the default generated
    /// piecewise assignment operator gets selected as the best match for
    /// our exact type and we crash horrifically.
    auto operator=(const WeakRef<T>& ref) -> WeakRef<T>& {
      *this = ref.get();
      return *this;
    }

    /// Assign from a pointer of any compatible type.
    template <typename U>
    auto operator=(U* ptr) -> WeakRef<T>& {
      Release();

      // Go through our template type instead of assigning directly to our
      // Object* so we catch invalid assigns at compile-time.
      T* tmp = ptr;
      if (tmp) Acquire(tmp);

      // More debug sanity checks.
      assert(reinterpret_cast<T*>(obj_) == ptr);
      assert(static_cast<T*>(obj_) == ptr);
      assert(dynamic_cast<T*>(obj_) == ptr);
      return *this;
    }

    /// Assign from a strong ref of any compatible type.
    template <typename U>
    auto operator=(const Ref<U>& ref) -> WeakRef<T>& {
      *this = ref.get();
      return *this;
    }

    /// Assign from a weak ref of any compatible type (except our exact
    /// type which has its own overload).
    template <typename U>
    auto operator=(const WeakRef<U>& ref) -> WeakRef<T>& {
      *this = ref.get();
      return *this;
    }

    // ---------------------------- Constructors -------------------------------

    // Default constructor.
    WeakRef() = default;

    /// Copy constructor. Note that, by making this explicit, we require
    /// code to be a bit more verbose. For example, we can't just do 'return
    /// some_ref;' from a function that returns a WeakRef and instead have
    /// to do 'return Object::WeakRef<SomeType>(some_ref)'. However I feel
    /// this extra verbosity is good; we're tossing around a mix of pointers
    /// and strong-refs and weak-refs so it's good to be aware exactly where
    /// refs are being added/etc.
    explicit WeakRef(const WeakRef<T>& ref) { *this = ref.get(); }

    /// Create from a pointer of any compatible type.
    template <typename U>
    explicit WeakRef(U* ptr) {
      *this = ptr;
    }

    /// Create from a strong ref of any compatible type.
    template <typename U>
    explicit WeakRef(const Ref<U>& ref) {
      *this = ref;
    }

    /// Create from a weak ref of any compatible type.
    template <typename U>
    explicit WeakRef(const WeakRef<U>& ref) {
      *this = ref;
    }

    // -------------------------------------------------------------------------

   private:
    void Acquire(T* obj) {
      if (obj == nullptr) {
        throw Exception("Acquiring invalid ptr of " + static_type_name<T>(),
                        PyExcType::kReference);
      }

#if BA_DEBUG_BUILD
      // Seems like it'd be a good idea to prevent creation of weak-refs to
      // objects in their destructors, but it turns out we're currently
      // doing this (session points contexts at itself as it dies, etc.)
      // Perhaps later can untangle that mess and change this behavior.
      obj->ObjectThreadCheck();
      assert(obj_ == nullptr && next_ == nullptr && prev_ == nullptr);
#endif

      if (obj->object_weak_refs_) {
        obj->object_weak_refs_->prev_ = this;
        next_ = obj->object_weak_refs_;
      }
      obj->object_weak_refs_ = this;

      // Sanity check: We make the assumption that static-casting our pointer
      // to/from Object gives the same results as reinterpret-casting it; let's
      // be certain that's the case. In some cases involving multiple
      // inheritance this might not be true, but we avoid those cases in our
      // object hierarchy. (the one type of multiple inheritance we allow is
      // pure virtual 'interfaces' which should not affect pointer offsets)
      assert(static_cast<Object*>(obj) == reinterpret_cast<Object*>(obj));

      // More random sanity checking.
      assert(dynamic_cast<T*>(reinterpret_cast<Object*>(obj)) == obj);
      obj_ = obj;
    }
  };  // WeakRef

  // Strong-ref.
  template <typename T>
  class Ref {
   public:
    ~Ref() { Release(); }
    auto get() const -> T* { return obj_; }

    auto exists() const -> bool { return obj_ != nullptr; }

    void Clear() { Release(); }

    /// Convenience wrapper for Object::IsValidManagedObject.
    auto IsValidManagedObject() const -> bool {
      if (auto* obj = get()) {
        return Object::IsValidManagedObject(obj);
      }
      return false;
    }

    // ----------------------------- Operators ---------------------------------

    /// Access the referenced object; throws an Exception if ref is invalid.
    auto operator*() const -> T& {
      if (!obj_) {
        throw Exception(
            "Dereferencing invalid " + static_type_name<T>() + " ref.",
            PyExcType::kReference);
      }
      return *obj_;
    }

    /// Access the referenced object; throws an Exception if ref is invalid.
    auto operator->() const -> T* {
      if (!obj_) {
        throw Exception(
            "Dereferencing invalid " + static_type_name<T>() + " ref.",
            PyExcType::kReference);
      }
      return obj_;
    }

    /// Compare to a pointer of any compatible type.
    template <typename U>
    auto operator==(U* ptr) -> bool {
      return (get() == ptr);
    }

    /// Compare to a pointer of any compatible type.
    template <typename U>
    auto operator!=(U* ptr) -> bool {
      return (get() != ptr);
    }

    /// Compare to a strong ref of any compatible type.
    template <typename U>
    auto operator==(const Ref<U>& ref) -> bool {
      return (get() == ref.get());
    }

    /// Compare to a strong ref of any compatible type.
    template <typename U>
    auto operator!=(const Ref<U>& ref) -> bool {
      return (get() != ref.get());
    }

    // Note: we don't need to include comparisons to weak-refs because that
    // is handled on the weak-ref side (and we can get ambiguity errors if
    // we handle them here too).

    /// Assign from our exact type. Note: it might seem like our template
    /// assigment operator (taking typename U) would cover this case, but
    /// that's not how it works. If we remove this, the default generated
    /// piecewise assignment operator gets selected as the best match for
    /// our exact type and we crash horrifically.
    auto operator=(const Ref<T>& ref) -> Ref<T>& {
      *this = ref.get();
      return *this;
    }

    /// Assign from a pointer of any compatible type.
    template <typename U>
    auto operator=(U* ptr) -> Ref<T>& {
      Release();
      if (ptr) {
        Acquire(ptr);
      }
      return *this;
    }

    /// Assign from a strong ref of any compatible type (except our exact
    /// type which has its own overload).
    template <typename U>
    auto operator=(const Ref<U>& ref) -> Ref<T>& {
      *this = ref.get();
      return *this;
    }

    /// Assign from a weak ref to any compatible type.
    template <typename U>
    auto operator=(const WeakRef<U>& ref) -> Ref<T>& {
      *this = ref.get();
      return *this;
    }

    // ---------------------------- Constructors -------------------------------

    /// Default constructor.
    Ref() = default;

    /// Copy constructor. Note that, by making this explicit, we require
    /// code to be a bit more verbose. For example, we can't just do 'return
    /// some_ref;' from a function that returns a Ref and instead have to do
    /// 'return Object::Ref<SomeType>(some_ref)'. However I feel this extra
    /// verbosity is good; we're tossing around a mix of pointers and
    /// strong-refs and weak-refs so it's good to be aware exactly where
    /// refs are being added/etc.
    explicit Ref(const Ref<T>& ref) { *this = ref.get(); }

    /// Create from a compatible pointer.
    template <typename U>
    explicit Ref(U* ptr) {
      *this = ptr;
    }

    /// Create from a compatible strong ref.
    template <typename U>
    explicit Ref(const Ref<U>& ref) {
      *this = ref;
    }

    /// Create from a compatible weak ref.
    template <typename U>
    explicit Ref(const WeakRef<U>& ref) {
      *this = ref;
    }

    // -------------------------------------------------------------------------

   private:
    void Acquire(T* obj) {
      if (obj == nullptr) {
        throw Exception("Acquiring invalid ptr of " + static_type_name<T>(),
                        PyExcType::kReference);
      }

      obj->ObjectIncrementStrongRefCount();
      obj_ = obj;
    }

    void Release() {
      if (obj_ != nullptr) {
        auto* obj = obj_;
        // Invalidate ref *before* to avoid potential recursive-release.
        obj_ = nullptr;
        obj->ObjectDecrementStrongRefCount();
      }
    }
    T* obj_{};
  };

  /// Object::New<Type>(): The preferred way to create ref-counted Objects.
  /// Allocates a new Object with the provided args and returns a strong
  /// reference to it.
  ///
  /// Generally you pass a single type to be instantiated and returned, but
  /// you can optionally specify the two separately. For example, you may
  /// want to create a Button but return a Ref to a Widget.
  template <typename TRETURN, typename TALLOC = TRETURN, typename... ARGS>
  [[nodiscard]] static auto New(ARGS&&... args) -> Object::Ref<TRETURN> {
    auto* ptr = new TALLOC(std::forward<ARGS>(args)...);

#if BA_DEBUG_BUILD
    /// Objects assume they are statically allocated by default; it's up
    /// to us to tell them when they're not.
    ptr->object_is_static_allocated_ = false;

    /// Make sure things aren't creating strong refs to themselves in their
    /// constructors.
    if (ptr->object_has_been_strong_reffed_) {
      FatalError("ballistica::Object has already been strong reffed in New: "
                 + ptr->GetObjectDescription());
    }
    ptr->object_is_ref_counted_ = true;
    assert(!ptr->object_is_post_inited_);
#endif

    ptr->ObjectPostInit();

#if BA_DEBUG_BUILD
    // Make sure top level post-init was called.
    assert(ptr->object_is_post_inited_);
#endif

    return Object::Ref<TRETURN>(ptr);
  }

  /// In some cases it may be handy to allocate an object for ref-counting
  /// but not actually create references yet. An example is when creating an
  /// object in one thread to be passed to another which will own said
  /// object. For such cases, allocate using NewDeferred() and then create
  /// the initial strong ref in the desired thread using CompleteDeferred().
  /// Note that, in debug builds, checks may be run to make sure deferred
  /// objects wind up with references added to them at some point. For this
  /// reason, if you want to allocate an object for manual deallocation or
  /// permanent existence, use NewUnmanaged() instead.
  template <typename T, typename... ARGS>
  [[nodiscard]] static auto NewDeferred(ARGS&&... args) -> T* {
    T* ptr = new T(std::forward<ARGS>(args)...);

#if BA_DEBUG_BUILD
    /// Objects assume they are statically allocated by default; it's up
    /// to us to tell them when they're not.
    ptr->object_is_static_allocated_ = false;

    /// Make sure things aren't creating strong refs to themselves in their
    /// constructors.
    if (ptr->object_has_been_strong_reffed_) {
      FatalError(
          "ballistica::Object has already been strong reffed in NewDeferred: "
          + ptr->GetObjectDescription());
    }
    ptr->object_is_pending_deferred_ = true;
    assert(!ptr->object_is_post_inited_);
#endif

    ptr->ObjectPostInit();

#if BA_DEBUG_BUILD
    // Make sure top level post-init was called.
    assert(ptr->object_is_post_inited_);
#endif

    return ptr;
  }

  /// Complete a new-deferred operation, creating an initial strong reference.
  /// One might ask why we require this call and don't simply allow creating an
  /// initial strong ref the 'normal' way. The answer is that we don't want
  /// to encourage a pattern where not-yet-referenced raw pointers are being
  /// passed around casually. This open up too many possibilities for leaks
  /// due to an expected exception preventing a raw pointer from ever getting
  /// its first reference. Deferred allocation should be treated as a very
  /// explicit two-part process with the object unusable until completion.
  template <typename T>
  static auto CompleteDeferred(T* ptr) -> Object::Ref<T> {
#if BA_DEBUG_BUILD
    /// Make sure we're operating on a fresh object created as deferred.
    if (ptr->object_has_been_strong_reffed_) {
      FatalError(
          "ballistica::Object has already been strong reffed in "
          "CompleteDeferred: "
          + ptr->GetObjectDescription());
    }
    if (!ptr->object_is_pending_deferred_) {
      FatalError(
          "ballistica::Object passed to CompleteDeferred was not created as "
          "deferred: "
          + ptr->GetObjectDescription());
    }
    assert(ptr->object_is_post_inited_);
    ptr->object_is_pending_deferred_ = false;
    ptr->object_is_ref_counted_ = true;
#endif

    return Object::Ref<T>(ptr);
  }

  /// Allocate an Object with no ref-counting; for use when an object
  /// will be manually managed/deleted.
  ///
  /// In debug builds, these objects will complain if attempts are made to
  /// create strong references to them.
  template <typename T, typename... ARGS>
  [[nodiscard]] static auto NewUnmanaged(ARGS&&... args) -> T* {
    T* ptr = new T(std::forward<ARGS>(args)...);

#if BA_DEBUG_BUILD
    /// Objects assume they are statically allocated by default; it's up
    /// to us to tell them when they're not.
    ptr->object_is_static_allocated_ = false;
    ptr->object_is_unmanaged_ = true;
    assert(!ptr->object_is_post_inited_);
#endif

    ptr->ObjectPostInit();

#if BA_DEBUG_BUILD
    // Make sure top level post-init was called.
    assert(ptr->object_is_post_inited_);
#endif

    return ptr;
  }

  /// Logs a tally of ba::Object types and counts (debug build only).
  static void LsObjects();

 private:
#if BA_DEBUG_BUILD
  // Making operator new private here purely to help enforce all of our
  // dynamic allocation/deallocation going through our special functions
  // (New(), NewDeferred(), etc.). However, sticking with original new for
  // release builds since we don't actually intend to muck with its runtime
  // behavior and the default might be somehow smarter than ours here.
  auto operator new(size_t size) -> void* { return new char[size]; }
  void ObjectUpdateForAcquire();

  bool object_is_static_allocated_{true};
  bool object_has_been_strong_reffed_{};
  bool object_is_ref_counted_{};
  bool object_is_post_inited_{};
  bool object_is_pending_deferred_{};
  bool object_is_unmanaged_{};
  bool object_is_dead_{};
  Object* object_next_{};
  Object* object_prev_{};
  ThreadOwnership thread_ownership_{ThreadOwnership::kClassDefault};
  EventLoopID owner_thread_{EventLoopID::kInvalid};
  bool thread_checks_enabled_{true};
  millisecs_t object_birth_time_{};
  bool object_printed_warning_{};
#endif
  WeakRefBase* object_weak_refs_{};
  int object_strong_ref_count_{};
  BA_DISALLOW_CLASS_COPIES(Object);
};  // Object

/// Convert a vector of ptrs into a vector of refs.
template <typename T>
auto PointersToRefs(const std::vector<T*>& ptrs)
    -> std::vector<Object::Ref<T> > {
  std::vector<Object::Ref<T> > refs;
  refs.reserve(ptrs.size());
  for (typename std::vector<T*>::const_iterator i = ptrs.begin();
       i != ptrs.end(); i++) {
    refs.push_back(Object::Ref<T>(*i));
  }
  return refs;
}

/// Convert a vector of ptrs into a vector of refs.
template <typename T>
auto PointersToWeakRefs(const std::vector<T*>& ptrs)
    -> std::vector<Object::WeakRef<T> > {
  std::vector<Object::WeakRef<T> > refs;
  refs.reserve(ptrs.size());
  for (typename std::vector<T*>::const_iterator i = ptrs.begin();
       i != ptrs.end(); i++) {
    refs.push_back(Object::WeakRef<T>(*i));
  }
  return refs;
}

/// Convert a vector of refs to a vector of ptrs.
template <typename T>
auto RefsToPointers(const std::vector<Object::Ref<T> >& refs)
    -> std::vector<T*> {
  std::vector<T*> ptrs;
  auto refs_size = refs.size();
  if (refs_size > 0) {
    ptrs.resize(refs_size);

    // Let's just access the memory directly; potentially faster?
    T** p = &(ptrs[0]);
    for (size_t i = 0; i < refs_size; i++) {
      p[i] = refs[i].get();
    }
  }
  return ptrs;
}

/// Prune dead refs out of a vector/list.
template <typename T>
void PruneDeadRefs(T* list) {
  for (typename T::iterator i = list->begin(); i != list->end();) {
    if (!i->exists()) {
      i = list->erase(i);
    } else {
      i++;
    }
  }
}

/// Prune dead refs out of a map/etc.
template <typename T>
void PruneDeadMapRefs(T* map) {
  for (typename T::iterator i = map->begin(); i != map->end();) {
    if (!i->second.exists()) {
      typename T::iterator i_next = i;
      i_next++;
      map->erase(i);
      i = i_next;
    } else {
      i++;
    }
  }
}

/// Print an Object (handles nullptr too).
inline auto ObjToString(Object* obj) -> std::string {
  return obj ? obj->GetObjectDescription() : "<nullptr>";
}

// A handy utility which creates a weak-ref in debug mode
// and a simple pointer in release mode.
// This can be used when a pointer *should* always be valid
// but its nice to be sure when the cpu cycles don't matter.
#if BA_DEBUG_BUILD
#define BA_DEBUG_PTR(TYPE) Object::WeakRef<TYPE>
#else
#define BA_DEBUG_PTR(TYPE) TYPE*
#endif

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_OBJECT_H_
