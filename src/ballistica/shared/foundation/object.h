// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_OBJECT_H_
#define BALLISTICA_SHARED_FOUNDATION_OBJECT_H_

#include <string>
#include <utility>
#include <vector>

#include "ballistica/shared/ballistica.h"

namespace ballistica {

/// Objects supporting strong and weak referencing and thread enforcement.
/// A rule or two for for Objects:
/// Don't throw exceptions out of object destructors;
/// This will break references to that object and lead to crashes if/when they
/// are used.
class Object {
 public:
  Object();
  virtual ~Object();

  // Object classes can provide descriptive names for themselves;
  // these are used for debugging and other purposes.
  // The default is to use the C++ symbol name, demangling it when possible.
  // IMPORTANT: Do not rely on this being consistent across builds/platforms.
  virtual auto GetObjectTypeName() const -> std::string;

  // Provide a brief description of this particular object; by default returns
  // type-name plus address.
  virtual auto GetObjectDescription() const -> std::string;

  enum class ThreadOwnership {
    kClassDefault,    // Uses class' GetDefaultOwnerThread() call.
    kNextReferencing  // Uses whichever thread next acquires/accesses a ref.
  };

#if BA_DEBUG_BUILD

  /// This is called when adding or removing a reference to an Object;
  /// it can perform sanity-tests to make sure references are not being
  /// added at incorrect times or from incorrect threads.
  /// The default implementation uses the per-object
  /// ThreadOwnership/EventLoopID values accessible below. NOTE: this
  /// check runs only in the debug build so don't add any logical side-effects!
  virtual void ObjectThreadCheck();

#endif

  /// Called by the default ObjectThreadCheck() to determine ThreadOwnership
  /// for an Object.  The default uses the object's individual value
  /// (which defaults to ThreadOwnership::kClassDefault and can be set via
  /// SetThreadOwnership())
  virtual auto GetThreadOwnership() const -> ThreadOwnership;

  /// Return the exact thread to check for with ThreadOwnership::kClassDefault
  /// (in the default ObjectThreadCheck implementation at least).
  /// Default returns EventLoopID::kLogic
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

  // Return true if the provided obj ptr is not null, is ref-counted, and has at
  // least 1 strong ref. This is generally a good thing for calls accepting
  // object ptrs to check. It is considered bad practice to perform operations
  // with not-yet-reffed objects. Note that in some cases this may return
  // false positives, so only use this as a sanity check and only take action
  // for a negative result.
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

  // Return true if the object seems to be valid and was allocated as unmanaged.
  // Code that plans to explicitly delete raw passed pointers can check this
  // for peace of mind. Note that for some build types this will return false
  // positives, so only use this as a sanity check and only take action for
  // negative results.
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
    // We don't store specifics in release builds; assume everything is peachy.
    return true;
  }
  auto object_strong_ref_count() const -> int {
    return object_strong_ref_count_;
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

    auto Exists() const -> bool { return (obj_ != nullptr); }

    void Clear() { Release(); }

   private:
    Object* obj_{};
    WeakRefBase* prev_{};
    WeakRefBase* next_{};
    friend class Object;
  };  // WeakRefBase

  /// Weak-reference to an instance of a specific Object subclass.
  template <typename T>
  class WeakRef : public WeakRefBase {
   public:
    /// Convenience wrapper for Object::IsValidManagedObject.
    auto IsValidManagedObject() const -> bool {
      if (auto* obj = Get()) {
        return Object::IsValidManagedObject(obj);
      }
      return false;
    }

    /// Convenience wrapper for Object::IsValidUnmanagedObject.
    auto IsValidUnmanagedObject() const -> bool {
      if (auto* obj = Get()) {
        return Object::IsValidUnmanagedObject(obj);
      }
      return false;
    }

    // Return a pointer or nullptr.
    auto Get() const -> T* {
      // Yes, reinterpret_cast is evil, but we make sure
      // we only operate on cases where this is valid
      // (see Acquire()).
      return reinterpret_cast<T*>(obj_);
    }

    // These operators throw exceptions if the object is dead.
    auto operator*() const -> T& {
      if (!obj_) {
        throw Exception("Dereferencing invalid " + static_type_name<T>()
                        + " ref.");
      }

      // Yes, reinterpret_cast is evil, but we make sure
      // we only operate on cases where this is valid
      // (see Acquire()).
      return *reinterpret_cast<T*>(obj_);
    }
    auto operator->() const -> T* {
      if (!obj_) {
        throw Exception("Dereferencing invalid " + static_type_name<T>()
                        + " ref.");
      }

      // Yes, reinterpret_cast is evil, but we make sure we only operate
      // on cases where this is valid (see Acquire()).
      return reinterpret_cast<T*>(obj_);
    }

    // Assign/compare with any compatible pointer.
    template <typename U>
    auto operator=(U* ptr) -> WeakRef<T>& {
      Release();

      // Go through our template type instead of assigning directly
      // to our Object* so we catch invalid assigns at compile-time.
      T* tmp = ptr;
      if (tmp) Acquire(tmp);

      // More debug sanity checks.
      assert(reinterpret_cast<T*>(obj_) == ptr);
      assert(static_cast<T*>(obj_) == ptr);
      assert(dynamic_cast<T*>(obj_) == ptr);
      return *this;
    }

    template <typename U>
    auto operator==(U* ptr) -> bool {
      return (Get() == ptr);
    }

    template <typename U>
    auto operator!=(U* ptr) -> bool {
      return (Get() != ptr);
    }

    // Assign/compare with same type ref (apparently the template below
    // doesn't cover this case?).
    //
    // Update: Actually now getting errors that
    // having both is ambiguous, so maybe can kill these now?..

    // Update 2: Oops; we (still?) crash without this.
    // re-enabling for now. Need to get to the bottom of this.
    auto operator=(const WeakRef<T>& ref) -> WeakRef<T>& {
      *this = ref.Get();
      return *this;
    }

    // auto operator==(const WeakRef<T>& ref) -> bool {
    //   return (Get() == ref.Get());
    // }

    // auto operator!=(const WeakRef<T>& ref) -> bool {
    //   return (Get() != ref.Get());
    // }

    // Assign/compare with a compatible weak-ref.
    template <typename U>
    auto operator=(const WeakRef<U>& ref) -> WeakRef<T>& {
      *this = ref.Get();
      return *this;
    }

    template <typename U>
    auto operator==(const WeakRef<U>& ref) -> bool {
      return (Get() == ref.Get());
    }

    template <typename U>
    auto operator!=(const WeakRef<U>& ref) -> bool {
      return (Get() != ref.Get());
    }

    // Assign/compare with a compatible strong-ref.
    template <typename U>
    auto operator=(const Ref<U>& ref) -> WeakRef<T>& {
      *this = ref.Get();
      return *this;
    }

    template <typename U>
    auto operator==(const Ref<U>& ref) -> bool {
      return (Get() == ref.Get());
    }

    template <typename U>
    auto operator!=(const Ref<U>& ref) -> bool {
      return (Get() != ref.Get());
    }

    // Various constructors:

    // Empty.
    WeakRef() = default;

    // From our type pointer.
    explicit WeakRef(T* obj) { *this = obj; }

    // Copy constructor (only non-explicit one).
    WeakRef(const WeakRef<T>& ref) { *this = ref.Get(); }

    // From a compatible pointer.
    template <typename U>
    explicit WeakRef(U* ptr) {
      *this = ptr;
    }

    // From a compatible strong ref.
    template <typename U>
    explicit WeakRef(const Ref<U>& ref) {
      *this = ref;
    }

    // From a compatible weak ref.
    template <typename U>
    explicit WeakRef(const WeakRef<U>& ref) {
      *this = ref;
    }

   private:
    void Acquire(T* obj) {
      if (obj == nullptr) {
        throw Exception("Acquiring invalid ptr of " + static_type_name<T>());
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
    auto Get() const -> T* { return obj_; }

    // These operators throw an Exception if the object is dead.
    auto operator*() const -> T& {
      if (!obj_) {
        throw Exception("Dereferencing invalid " + static_type_name<T>()
                        + " ref.");
      }
      return *obj_;
    }
    auto operator->() const -> T* {
      if (!obj_) {
        throw Exception("Dereferencing invalid " + static_type_name<T>()
                        + " ref.");
      }
      return obj_;
    }
    auto Exists() const -> bool { return (obj_ != nullptr); }
    void Clear() { Release(); }

    /// Convenience wrapper for Object::IsValidManagedObject.
    auto IsValidManagedObject() const -> bool {
      if (auto* obj = Get()) {
        return Object::IsValidManagedObject(obj);
      }
      return false;
    }

    // Assign/compare with any compatible pointer.
    template <typename U>
    auto operator=(U* ptr) -> Ref<T>& {
      Release();
      if (ptr) {
        Acquire(ptr);
      }
      return *this;
    }
    template <typename U>
    auto operator==(U* ptr) -> bool {
      return (Get() == ptr);
    }
    template <typename U>
    auto operator!=(U* ptr) -> bool {
      return (Get() != ptr);
    }

    auto operator==(const Ref<T>& ref) -> bool { return (Get() == ref.Get()); }
    auto operator!=(const Ref<T>& ref) -> bool { return (Get() != ref.Get()); }

    // Assign/compare with same type ref (apparently the generic template below
    // doesn't cover that case?..)
    // DANGER: Seems to still compile if we comment this out, but crashes.
    // Should get to the bottom of that.
    auto operator=(const Ref<T>& ref) -> Ref<T>& {
      assert(this != &ref);  // Shouldn't be self-assigning.
      *this = ref.Get();
      return *this;
    }

    // Assign/compare with a compatible strong-ref.
    template <typename U>
    auto operator=(const Ref<U>& ref) -> Ref<T>& {
      *this = ref.Get();
      return *this;
    }

    template <typename U>
    auto operator==(const Ref<U>& ref) -> bool {
      return (Get() == ref.Get());
    }

    template <typename U>
    auto operator!=(const Ref<U>& ref) -> bool {
      return (Get() != ref.Get());
    }

    // Assign from a compatible weak-ref. Comparing to compatible weak-refs
    // is covered by the operators on the weak-ref side.
    template <typename U>
    auto operator=(const WeakRef<U>& ref) -> Ref<T>& {
      *this = ref.Get();
      return *this;
    }

    // These are already covered by the equivalent operators
    // on the WeakRef side.
    // template <typename U>
    // auto operator==(const WeakRef<U>& ref) -> bool {
    //   return (Get() == ref.Get());
    // }

    // template <typename U>
    // auto operator!=(const WeakRef<U>& ref) -> bool {
    //   return (Get() != ref.Get());
    // }

    // Various constructors:

    // Empty.
    Ref() = default;

    // From our type pointer.
    explicit Ref(T* obj) { *this = obj; }

    // Copy constructor (only non-explicit one).
    Ref(const Ref<T>& ref) { *this = ref.Get(); }

    // From a compatible pointer.
    template <typename U>
    explicit Ref(U* ptr) {
      *this = ptr;
    }

    // From a compatible strong ref.
    template <typename U>
    explicit Ref(const Ref<U>& ref) {
      *this = ref;
    }

    // From a compatible weak ref.
    template <typename U>
    explicit Ref(const WeakRef<U>& ref) {
      *this = ref;
    }

   private:
    void Acquire(T* obj) {
      if (obj == nullptr) {
        throw Exception("Acquiring invalid ptr of " + static_type_name<T>());
      }

#if BA_DEBUG_BUILD
      obj->ObjectUpdateForAcquire();
      obj->ObjectThreadCheck();

      // Obvs shouldn't be referencing dead stuff.
      assert(!obj->object_is_dead_);

      // Complain if trying ot create a ref to a non-ref-counted obj.
      if (!obj->object_is_ref_counted_) {
        FatalError("Attempting to create a strong-ref to non-refcounted obj: "
                   + obj->GetObjectDescription());
      }
      obj->object_has_been_strong_reffed_ = true;
#endif  // BA_DEBUG_BUILD

      obj->object_strong_ref_count_++;
      obj_ = obj;
    }

    void Release() {
      if (obj_ != nullptr) {
#if BA_DEBUG_BUILD
        obj_->ObjectThreadCheck();
#endif
        assert(obj_->object_strong_ref_count_ > 0);
        obj_->object_strong_ref_count_--;
        T* tmp = obj_;

        // Invalidate ref *before* delete to avoid potential double-release.
        obj_ = nullptr;
        if (tmp->object_strong_ref_count_ == 0) {
#if BA_DEBUG_BUILD
          tmp->object_is_dead_ = true;
#endif
          delete tmp;
        }
      }
    }
    T* obj_{};
  };

  /// Object::New<Type>(): The preferred way to create ref-counted Objects.
  /// Allocates a new Object with the provided args and returns a strong
  /// reference to it.
  /// Generally you pass a single type to be instantiated and returned,
  /// but you can optionally specify the two separately.
  /// (for instance you may want to create a Button but return
  /// a Ref to a Widget)
  template <typename TRETURN, typename TALLOC = TRETURN, typename... ARGS>
  [[nodiscard]] static auto New(ARGS&&... args) -> Object::Ref<TRETURN> {
    auto* ptr = new TALLOC(std::forward<ARGS>(args)...);
#if BA_DEBUG_BUILD
    /// Make sure things aren't creating strong refs to themselves in their
    /// constructors.
    if (ptr->object_has_been_strong_reffed_) {
      FatalError("ballistica::Object has already been strong reffed in New: "
                 + ptr->GetObjectDescription());
    }
    ptr->object_is_ref_counted_ = true;
#endif
    return Object::Ref<TRETURN>(ptr);
  }

  /// In some cases it may be handy to allocate an object for ref-counting
  /// but not actually create references yet. An example is when creating an
  /// object in one thread to be passed to another which will own said object.
  /// For such cases, allocate using NewDeferred() and then create the initial
  /// strong ref in the desired thread using CompleteDeferred().
  /// Note that in debug builds, checks may be run to make sure deferred
  /// objects wind up with references added to them at some point. If you
  /// want to allocate an object for manual deallocation or permanent
  /// existence, use NewUnmanaged() instead.
  template <typename T, typename... ARGS>
  [[nodiscard]] static auto NewDeferred(ARGS&&... args) -> T* {
    T* ptr = new T(std::forward<ARGS>(args)...);
#if BA_DEBUG_BUILD
    /// Make sure things aren't creating strong refs to themselves in their
    /// constructors.
    if (ptr->object_has_been_strong_reffed_) {
      FatalError(
          "ballistica::Object has already been strong reffed in NewDeferred: "
          + ptr->GetObjectDescription());
    }
    ptr->object_is_pending_deferred_ = true;
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
    ptr->object_is_pending_deferred_ = false;
    ptr->object_is_ref_counted_ = true;
#endif

    return Object::Ref<T>(ptr);
  }

  /// Allocate an Object with no ref-counting; for use when an object
  /// will be manually managed/deleted.
  /// In debug builds, these objects will complain if attempts are made to
  /// create strong references to them.
  template <typename T, typename... ARGS>
  [[nodiscard]] static auto NewUnmanaged(ARGS&&... args) -> T* {
    T* ptr = new T(std::forward<ARGS>(args)...);
#if BA_DEBUG_BUILD
    ptr->object_is_unmanaged_ = true;
#endif
    return ptr;
  }

  /// Logs a tally of ba::Object types and counts (debug build only).
  static void LsObjects();

 private:
#if BA_DEBUG_BUILD
  // Making operator new private here to help ensure all of our dynamic
  // allocation/deallocation goes through our special functions (New(),
  // NewDeferred(), etc.). However, sticking with original new for release
  // builds since it may handle corner cases that this does not.
  auto operator new(size_t size) -> void* { return new char[size]; }
  void ObjectUpdateForAcquire();
  bool object_has_been_strong_reffed_{};
  bool object_is_ref_counted_{};
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
  int object_strong_ref_count_{};
  WeakRefBase* object_weak_refs_{};
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
      p[i] = refs[i].Get();
    }
  }
  return ptrs;
}

/// Prune dead refs out of a vector/list.
template <typename T>
void PruneDeadRefs(T* list) {
  for (typename T::iterator i = list->begin(); i != list->end();) {
    if (!i->Exists()) {
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
    if (!i->second.Exists()) {
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
