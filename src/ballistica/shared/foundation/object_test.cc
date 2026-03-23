// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/object_test.h"

#include <map>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica {

// Minimal concrete Object subclass used by the tests below. Optionally
// writes true to a bool on destruction so tests can verify exactly when
// the object dies. Named to avoid ODR collisions with other TUs.
class ObjectRefCountTestObj : public Object {
 public:
  explicit ObjectRefCountTestObj(bool* destroyed = nullptr)
      : destroyed_(destroyed) {}
  ~ObjectRefCountTestObj() override {
    if (destroyed_) *destroyed_ = true;
  }

  // Tests may run on any thread (e.g. via --command); let the first
  // referencing thread claim ownership rather than requiring kLogic.
  auto GetThreadOwnership() const -> ThreadOwnership override {
    return ThreadOwnership::kNextReferencing;
  }

  int value{};

 private:
  bool* destroyed_{};
};

// Throw a descriptive Exception on failure; BA_PYTHON_CATCH upstream
// converts it to a Python RuntimeError.
static void Check(bool cond, const char* what) {
  if (!cond) {
    throw Exception(std::string("Object test failed: ") + what);
  }
}

// -------------------------------------------------------------------------
// Group 1: Ref<T> core lifetime
// -------------------------------------------------------------------------

static void TestRefBasics() {
  using T = ObjectRefCountTestObj;

  // 1.1 Default Ref is empty.
  {
    Object::Ref<T> r;
    Check(!r.exists(), "1.1 default Ref exists() should be false");
    Check(r.get() == nullptr, "1.1 default Ref get() should be nullptr");
  }

  // 1.2 New() returns a Ref with count == 1.
  {
    bool destroyed = false;
    {
      auto r = Object::New<T>(&destroyed);
      Check(r.exists(), "1.2 new Ref should exist");
      Check(r->object_strong_ref_count() == 1, "1.2 initial count should be 1");
      Check(!destroyed, "1.2 object should not be destroyed yet");
    }
    Check(destroyed, "1.2 object should be destroyed when last Ref drops");
  }

  // 1.3 Copy constructor: count == 2, both refs keep object alive.
  {
    bool destroyed = false;
    {
      auto r1 = Object::New<T>(&destroyed);
      {
        Object::Ref<T> r2(r1);
        Check(r1->object_strong_ref_count() == 2,
              "1.3 count should be 2 after copy");
        Check(!destroyed, "1.3 object alive with 2 refs");
      }
      Check(r1->object_strong_ref_count() == 1,
            "1.3 count should be 1 after copy destroyed");
      Check(!destroyed, "1.3 object alive with 1 ref remaining");
    }
    Check(destroyed, "1.3 object destroyed when last Ref drops");
  }

  // 1.4 Move constructor: count stays 1, source becomes empty.
  {
    bool destroyed = false;
    {
      auto r1 = Object::New<T>(&destroyed);
      T* raw = r1.get();
      Object::Ref<T> r2(std::move(r1));
      Check(!r1.exists(), "1.4 moved-from Ref should be empty");
      Check(r2.get() == raw, "1.4 moved-to Ref should hold the object");
      Check(r2->object_strong_ref_count() == 1,
            "1.4 count should still be 1 after move");
      Check(!destroyed, "1.4 object should not be destroyed");
    }
    Check(destroyed, "1.4 object destroyed when moved-to Ref drops");
  }

  // 1.5 Move assignment: count stays 1, previous referent released.
  {
    bool d1 = false;
    bool d2 = false;
    {
      auto r1 = Object::New<T>(&d1);
      auto r2 = Object::New<T>(&d2);
      T* raw1 = r1.get();
      r2 = std::move(r1);
      Check(!r1.exists(), "1.5 moved-from Ref should be empty");
      Check(r2.get() == raw1, "1.5 moved-to Ref should hold obj1");
      Check(d2, "1.5 obj2 should be destroyed when r2 released it");
      Check(!d1, "1.5 obj1 should not be destroyed");
      Check(r2->object_strong_ref_count() == 1, "1.5 count should be 1");
    }
    Check(d1, "1.5 obj1 destroyed when r2 drops");
  }

  // 1.6 Self-move-assign: object must survive.
  {
    bool destroyed = false;
    {
      auto r = Object::New<T>(&destroyed);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wself-move"
      r = std::move(r);  // guarded by if (this != &other)
#pragma clang diagnostic pop
      Check(r.exists(), "1.6 Ref should survive self-move-assign");
      Check(!destroyed, "1.6 object should survive self-move-assign");
    }
    Check(destroyed, "1.6 object destroyed when Ref drops");
  }

  // 1.7 Self-assign via pointer: this was the latent bug we fixed.
  {
    bool destroyed = false;
    {
      auto r = Object::New<T>(&destroyed);
      r = r.get();
      Check(r.exists(), "1.7 Ref should survive self-assign via ptr");
      Check(!destroyed, "1.7 object should survive self-assign via ptr");
    }
    Check(destroyed, "1.7 object destroyed when Ref drops");
  }

  // 1.8 Self-assign via exact-type ref (routes through pointer overload).
  {
    bool destroyed = false;
    {
      auto r = Object::New<T>(&destroyed);
      r = r;
      Check(r.exists(), "1.8 Ref should survive self-assign via ref");
      Check(!destroyed, "1.8 object should survive self-assign via ref");
    }
    Check(destroyed, "1.8 object destroyed when Ref drops");
  }

  // 1.9 Null assignment: ref becomes empty, object destroyed.
  {
    bool destroyed = false;
    auto r = Object::New<T>(&destroyed);
    r = nullptr;
    Check(!r.exists(), "1.9 Ref should be empty after null assign");
    Check(destroyed, "1.9 object should be destroyed after null assign");
  }

  // 1.10 Clear(): equivalent to null assignment.
  {
    bool destroyed = false;
    auto r = Object::New<T>(&destroyed);
    r.Clear();
    Check(!r.exists(), "1.10 Ref should be empty after Clear()");
    Check(destroyed, "1.10 object should be destroyed after Clear()");
  }

  // 1.11 operator* on empty Ref throws.
  {
    Object::Ref<T> r;
    bool threw = false;
    try {
      [[maybe_unused]] auto& obj = *r;
    } catch (const std::exception&) {
      threw = true;
    }
    Check(threw, "1.11 operator* on empty Ref should throw");
  }

  // 1.12 operator-> on empty Ref throws.
  {
    Object::Ref<T> r;
    bool threw = false;
    try {
      r->value = 42;
    } catch (const std::exception&) {
      threw = true;
    }
    Check(threw, "1.12 operator-> on empty Ref should throw");
  }

  // 1.13 Cross-type assignment: Ref<T> -> Ref<Object>.
  {
    bool destroyed = false;
    {
      auto r_derived = Object::New<T>(&destroyed);
      Object::Ref<Object> r_base;
      r_base = r_derived;
      Check(r_base.exists(), "1.13 cross-type Ref should exist");
      Check(r_derived->object_strong_ref_count() == 2,
            "1.13 count should be 2 with both refs");
    }
    Check(destroyed, "1.13 object destroyed when both refs drop");
  }
}

// -------------------------------------------------------------------------
// Group 2: WeakRef<T> nullification and linked-list integrity
// -------------------------------------------------------------------------

static void TestWeakRefBasics() {
  using T = ObjectRefCountTestObj;

  // 2.1 Default WeakRef is empty.
  {
    Object::WeakRef<T> wr;
    Check(!wr.exists(), "2.1 default WeakRef exists() should be false");
    Check(wr.get() == nullptr, "2.1 default WeakRef get() should be nullptr");
  }

  // 2.2 WeakRef alone does not keep the object alive.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr;
    {
      auto r = Object::New<T>(&destroyed);
      wr = r.get();
      Check(wr.exists(), "2.2 WeakRef should exist while strong ref alive");
    }
    Check(destroyed, "2.2 object should be destroyed when strong ref drops");
    Check(!wr.exists(), "2.2 WeakRef should be null after object destroyed");
  }

  // 2.3 Multiple WeakRefs: all nullify on object death.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr1, wr2, wr3;
    {
      auto r = Object::New<T>(&destroyed);
      wr1 = r.get();
      wr2 = r.get();
      wr3 = r.get();
      Check(wr1.exists() && wr2.exists() && wr3.exists(),
            "2.3 all WeakRefs should exist while strong ref alive");
    }
    Check(destroyed, "2.3 object should be destroyed");
    Check(!wr1.exists() && !wr2.exists() && !wr3.exists(),
          "2.3 all WeakRefs should be null after object destroyed");
  }

  // 2.4 Head removal: newest WeakRef (head of list) cleared before object
  // dies; the remaining one (tail) still nullifies correctly.
  //
  // Insertion order: wr_old first (becomes tail), wr_new second (becomes
  // head, since new entries are prepended).
  {
    bool destroyed = false;
    Object::WeakRef<T> wr_old, wr_new;
    {
      auto r = Object::New<T>(&destroyed);
      wr_old = r.get();  // tail
      wr_new = r.get();  // head
      wr_new.Clear();    // remove head
      Check(wr_old.exists(), "2.4 tail WeakRef should still exist");
      Check(!wr_new.exists(), "2.4 cleared WeakRef should be empty");
    }
    Check(destroyed, "2.4 object should be destroyed");
    Check(!wr_old.exists(), "2.4 remaining WeakRef should be null");
  }

  // 2.5 Tail removal: oldest WeakRef (tail) cleared before object dies;
  // the remaining one (head) still nullifies correctly.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr_old, wr_new;
    {
      auto r = Object::New<T>(&destroyed);
      wr_old = r.get();  // tail
      wr_new = r.get();  // head
      wr_old.Clear();    // remove tail
      Check(wr_new.exists(), "2.5 head WeakRef should still exist");
      Check(!wr_old.exists(), "2.5 cleared WeakRef should be empty");
    }
    Check(destroyed, "2.5 object should be destroyed");
    Check(!wr_new.exists(), "2.5 remaining WeakRef should be null");
  }

  // 2.6 Three WeakRefs, full teardown via object destructor.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr1, wr2, wr3;
    {
      auto r = Object::New<T>(&destroyed);
      wr1 = r.get();  // tail
      wr2 = r.get();  // middle
      wr3 = r.get();  // head
    }
    Check(destroyed, "2.6 object should be destroyed");
    Check(!wr1.exists() && !wr2.exists() && !wr3.exists(),
          "2.6 all three WeakRefs should be null");
  }

  // 2.7 WeakRef copy constructor: both refs nullify on object death.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr2;
    {
      auto r = Object::New<T>(&destroyed);
      Object::WeakRef<T> wr1(r.get());
      // Copy-construct into a temporary, then move-assign to wr2 so it
      // outlives the inner scope.
      wr2 = Object::WeakRef<T>(wr1);
      Check(wr1.exists() && wr2.exists(),
            "2.7 both WeakRefs should exist while strong ref alive");
      Check(wr1.get() == wr2.get(),
            "2.7 both WeakRefs should point to the same object");
    }
    Check(destroyed, "2.7 object destroyed when strong ref drops");
    Check(!wr2.exists(), "2.7 wr2 should be null after object death");
  }

  // 2.8 WeakRef copy assignment: releases old referent, acquires new.
  {
    bool d1 = false;
    bool d2 = false;
    Object::WeakRef<T> wr;
    {
      auto r1 = Object::New<T>(&d1);
      auto r2 = Object::New<T>(&d2);
      wr = r1.get();
      Check(wr.get() == r1.get(), "2.8 wr should point to obj1");
      wr = r2.get();
      Check(wr.get() == r2.get(), "2.8 wr should now point to obj2");
    }
    Check(d1 && d2, "2.8 both objects should be destroyed");
    Check(!wr.exists(), "2.8 wr should be null after both objects die");
  }

  // 2.9 WeakRef move constructor: source becomes empty, moved-to ref
  // takes over the list position and nullifies correctly at object death.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr2;
    {
      auto r = Object::New<T>(&destroyed);
      Object::WeakRef<T> wr1(r.get());
      wr2 = std::move(wr1);
      Check(!wr1.exists(), "2.9 moved-from WeakRef should be empty");
      Check(wr2.exists(), "2.9 moved-to WeakRef should exist");
      Check(wr2.get() == r.get(),
            "2.9 moved-to WeakRef should point to the object");
    }
    Check(destroyed, "2.9 object destroyed");
    Check(!wr2.exists(), "2.9 wr2 should be null after object death");
  }

  // 2.10 WeakRef self-move-assign: object must survive.
  {
    bool destroyed = false;
    {
      auto r = Object::New<T>(&destroyed);
      Object::WeakRef<T> wr(r.get());
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wself-move"
      wr = std::move(wr);  // guarded by if (this != &other)
#pragma clang diagnostic pop
      Check(wr.exists(), "2.10 WeakRef should survive self-move-assign");
      Check(!destroyed, "2.10 object should survive self-move-assign");
    }
    Check(destroyed, "2.10 object destroyed when refs drop");
  }

  // 2.11 WeakRef self-assign via pointer: no list corruption.
  {
    bool destroyed = false;
    {
      auto r = Object::New<T>(&destroyed);
      Object::WeakRef<T> wr(r.get());
      wr = wr.get();  // guarded by if (tmp != obj_)
      Check(wr.exists(), "2.11 WeakRef should survive self-assign via ptr");
      Check(!destroyed, "2.11 object should survive self-assign via ptr");
    }
    Check(destroyed, "2.11 object destroyed when refs drop");
  }
}

// -------------------------------------------------------------------------
// Group 3: Strong/weak interaction
// -------------------------------------------------------------------------

static void TestStrongWeakInteraction() {
  using T = ObjectRefCountTestObj;

  // 3.1 Promote weak to strong while both exist: count goes 1->2.
  {
    bool destroyed = false;
    Object::WeakRef<T> wr;
    {
      auto r1 = Object::New<T>(&destroyed);
      wr = r1.get();
      {
        Object::Ref<T> r2(wr.get());  // promote
        Check(r1->object_strong_ref_count() == 2,
              "3.1 count should be 2 after promotion");
        Check(!destroyed, "3.1 object alive with 2 strong refs");
      }
      Check(r1->object_strong_ref_count() == 1,
            "3.1 count should be 1 after promoted ref drops");
      Check(!destroyed, "3.1 object still alive via r1");
    }
    Check(destroyed, "3.1 object destroyed when r1 drops");
    Check(!wr.exists(), "3.1 WeakRef nullified after death");
  }

  // 3.2 Promote then drop original: object survives via promoted ref.
  {
    bool destroyed = false;
    Object::Ref<T> r2;
    Object::WeakRef<T> wr;
    {
      auto r1 = Object::New<T>(&destroyed);
      wr = r1.get();
      r2 = Object::Ref<T>(wr.get());
    }  // r1 drops; r2 still holds the object
    Check(!destroyed, "3.2 object survives via promoted ref");
    Check(wr.exists(), "3.2 WeakRef still valid while r2 alive");
    r2.Clear();
    Check(destroyed, "3.2 object destroyed when promoted ref drops");
    Check(!wr.exists(), "3.2 WeakRef nullified after death");
  }

  // 3.3 wr.get() on dead object returns nullptr safely.
  {
    Object::WeakRef<T> wr;
    {
      auto r = Object::New<T>();
      wr = r.get();
    }
    Check(!wr.exists(), "3.3 WeakRef should be null after object death");
    Check(wr.get() == nullptr, "3.3 get() should return nullptr on dead ref");
  }
}

// -------------------------------------------------------------------------
// Group 4: Allocation methods
// -------------------------------------------------------------------------

static void TestAllocationMethods() {
  using T = ObjectRefCountTestObj;

  // 4.1 New<Base, Derived>(): two-type form.
  {
    bool destroyed = false;
    {
      Object::Ref<Object> r = Object::New<Object, T>(&destroyed);
      Check(r.exists(), "4.1 two-type New should succeed");
      Check(!destroyed, "4.1 object should be alive");
    }
    Check(destroyed, "4.1 object destroyed when base Ref drops");
  }

  // 4.2 NewDeferred() + CompleteDeferred().
  {
    bool destroyed = false;
    {
      T* raw = Object::NewDeferred<T>(&destroyed);
      Check(!destroyed, "4.2 object should not be destroyed before completion");
      {
        auto r = Object::CompleteDeferred(raw);
        Check(r->object_strong_ref_count() == 1,
              "4.2 count should be 1 after CompleteDeferred");
        Check(!destroyed, "4.2 object should be alive");
      }
      Check(destroyed, "4.2 object destroyed when Ref drops");
    }
  }

  // 4.3 NewUnmanaged() + manual delete.
  {
    bool destroyed = false;
    T* raw = Object::NewUnmanaged<T>(&destroyed);
    Check(!destroyed, "4.3 object not destroyed yet");
    delete raw;
    Check(destroyed, "4.3 object destroyed after manual delete");
  }
}

// -------------------------------------------------------------------------
// Group 5: Container utilities
// -------------------------------------------------------------------------

static void TestContainerUtilities() {
  using T = ObjectRefCountTestObj;

  // 5.1 PruneDeadRefs(): removes dead WeakRefs from a vector.
  {
    bool d1 = false;
    bool d2 = false;
    bool d3 = false;
    auto r2 = Object::New<T>(&d2);  // keep alive throughout
    std::vector<Object::WeakRef<T>> vec;
    {
      auto r1 = Object::New<T>(&d1);
      vec.push_back(Object::WeakRef<T>(r1.get()));
    }
    vec.push_back(Object::WeakRef<T>(r2.get()));
    {
      auto r3 = Object::New<T>(&d3);
      vec.push_back(Object::WeakRef<T>(r3.get()));
    }
    Check(vec.size() == 3, "5.1 vec should have 3 entries before prune");
    Check(d1 && d3, "5.1 obj1 and obj3 should be dead");
    Check(!d2, "5.1 obj2 should be alive");
    PruneDeadRefs(&vec);
    Check(vec.size() == 1, "5.1 pruned vec should have 1 entry");
    Check(vec[0].get() == r2.get(), "5.1 surviving entry should be obj2");
  }

  // 5.2 PruneDeadMapRefs(): removes dead WeakRefs from a map.
  {
    bool d1 = false;
    bool d2 = false;
    auto r2 = Object::New<T>(&d2);
    std::map<int, Object::WeakRef<T>> m;
    {
      auto r1 = Object::New<T>(&d1);
      m[1] = Object::WeakRef<T>(r1.get());
    }
    m[2] = Object::WeakRef<T>(r2.get());
    Check(m.size() == 2, "5.2 map should have 2 entries before prune");
    PruneDeadMapRefs(&m);
    Check(m.size() == 1, "5.2 pruned map should have 1 entry");
    Check(m.count(2) == 1, "5.2 surviving entry should be key 2");
  }

  // 5.3 PointersToRefs(): each pointer becomes a strong ref.
  {
    bool d1 = false;
    bool d2 = false;
    auto r1 = Object::New<T>(&d1);
    auto r2 = Object::New<T>(&d2);
    std::vector<T*> ptrs = {r1.get(), r2.get()};
    auto refs = PointersToRefs(ptrs);
    Check(refs.size() == 2, "5.3 refs should have 2 entries");
    Check(r1->object_strong_ref_count() == 2,
          "5.3 obj1 count should be 2 with extra ref");
    Check(r2->object_strong_ref_count() == 2,
          "5.3 obj2 count should be 2 with extra ref");
    refs.clear();
    Check(r1->object_strong_ref_count() == 1,
          "5.3 obj1 count should be 1 after extras dropped");
    Check(!d1 && !d2, "5.3 objects should still be alive via r1/r2");
  }

  // 5.4 PointersToWeakRefs(): all nullify on object deaths.
  {
    bool d1 = false;
    bool d2 = false;
    std::vector<Object::WeakRef<T>> wrefs;
    {
      auto r1 = Object::New<T>(&d1);
      auto r2 = Object::New<T>(&d2);
      std::vector<T*> ptrs = {r1.get(), r2.get()};
      wrefs = PointersToWeakRefs(ptrs);
      Check(wrefs.size() == 2, "5.4 weak refs should have 2 entries");
      Check(wrefs[0].exists() && wrefs[1].exists(),
            "5.4 both weak refs should exist while strong refs alive");
    }
    Check(d1 && d2, "5.4 both objects should be destroyed");
    Check(!wrefs[0].exists() && !wrefs[1].exists(),
          "5.4 all weak refs should be null after deaths");
  }

  // 5.5 RefsToPointers(): round-trip from refs to raw ptrs.
  {
    auto r1 = Object::New<T>();
    auto r2 = Object::New<T>();
    std::vector<Object::Ref<T>> refs;
    refs.push_back(Object::Ref<T>(r1));
    refs.push_back(Object::Ref<T>(r2));
    auto ptrs = RefsToPointers(refs);
    Check(ptrs.size() == 2, "5.5 ptrs should have 2 entries");
    Check(ptrs[0] == r1.get(), "5.5 ptrs[0] should match r1");
    Check(ptrs[1] == r2.get(), "5.5 ptrs[1] should match r2");
  }
}

// -------------------------------------------------------------------------

void RunObjectTests() {
  TestRefBasics();
  TestWeakRefBasics();
  TestStrongWeakInteraction();
  TestAllocationMethods();
  TestContainerUtilities();
}

}  // namespace ballistica
