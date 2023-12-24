// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_H_

#include <list>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <vector>

#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/generic/runnable.h"
#include "ballistica/shared/math/point2d.h"
#include "ballistica/shared/python/python_object_set.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica {

/// Core Python support/infrastructure class.
class Python {
 public:
  /// When calling a python callable directly, you can use the following
  /// to push and pop a text label which will be printed as 'call' in errors.
  class ScopedCallLabel {
   public:
    explicit ScopedCallLabel(const char* label) {
      prev_label_ = current_label_;
    }
    ~ScopedCallLabel() { current_label_ = prev_label_; }
    static auto current_label() -> const char* { return current_label_; }

   private:
    const char* prev_label_{};
    static const char* current_label_;
    BA_DISALLOW_CLASS_COPIES(ScopedCallLabel);
  };

  /// Use this to protect Python code that may be run in cases where we
  /// don't hold the Global Interpreter Lock (GIL). (Basically anything
  /// outside of the logic thread). This will release and then restore
  /// the GIL if it is held initially; otherwise it is a no-op.
  class ScopedInterpreterLock {
   public:
    ScopedInterpreterLock();
    ~ScopedInterpreterLock();

   private:
    class Impl;
    Impl* impl_{};
  };

  /// Use this for cases where, if we *do* hold the Python GIL, we want to
  /// temporarily release it.
  class ScopedInterpreterLockRelease {
   public:
    ScopedInterpreterLockRelease();
    ~ScopedInterpreterLockRelease();

   private:
    class Impl;
    Impl* impl_{};
  };

  /// Return whether the current thread holds the global-interpreter-lock.
  /// We must always hold the GIL while running python code.
  /// This *should* generally be the case by default, but this can be handy for
  /// sanity checking that.
  static auto HaveGIL() -> bool;

  /// For use in specific cases when a thread exits our control. In most
  /// cases Scoped Locks/Unlocks should be used.
  static void PermanentlyReleaseGIL();

  /// Attempt to print the Python stack trace.
  static void PrintStackTrace();

  /// Pass any PyObject* (including nullptr) to get a readable string
  /// (basically equivalent of str(foo)).
  static auto ObjToString(PyObject* obj) -> std::string;

  /// Pass any PyObject* (including nullptr) to get a readable string
  /// for its type (basically equivalent of str(type(foo)).
  static auto ObjTypeToString(PyObject* obj) -> std::string;

  // Print various context debugging bits to Python's sys.stderr.
  static void PrintContextNotYetBootstrapped();
  static void PrintContextAuto();

  static auto GetContextBaseString() -> std::string;

  /// Borrowed from Python's source code: used in overriding of objects' dir()
  /// results.
  static auto generic_dir(PyObject* self) -> PyObject*;

  /// Return a minimal filename/position string such as 'foo.py:201' based
  /// on the Python stack state. This shouldn't be too expensive to fetch and
  /// is useful as an object identifier/etc.
  static auto GetPythonFileLocation(bool pretty = true) -> std::string;

  // For checking and pulling values out of Python objects.
  // These will all throw Exceptions on errors.

  static auto GetPyString(PyObject* o) -> std::string;
  /// Get string with Lstr objs converted to json.
  static auto GetPyInt64(PyObject* o) -> int64_t;
  static auto GetPyInt(PyObject* o) -> int;
  static auto IsPyString(PyObject* o) -> bool;
  static auto GetPyBool(PyObject* o) -> bool;
  static auto CanGetPyDouble(PyObject* o) -> bool;
  static auto GetPyFloat(PyObject* o) -> float {
    return static_cast<float>(GetPyDouble(o));
  }
  static auto GetPyDouble(PyObject* o) -> double;
  static auto GetPyFloats(PyObject* o) -> std::vector<float>;
  static auto GetPyInts64(PyObject* o) -> std::vector<int64_t>;
  static auto GetPyInts(PyObject* o) -> std::vector<int>;
  static auto GetPyUInts64(PyObject* o) -> std::vector<uint64_t>;
  static auto GetPyPoint2D(PyObject* o) -> Point2D;
  static auto GetPyStringSequence(PyObject* o) -> std::list<std::string>;

  /// Set Python exception from C++ Exception.
  static void SetPythonException(const Exception& exc);

  /// Create a Python list of strings.
  static auto StringList(const std::list<std::string>& values) -> PythonRef;

  /// Create a Python single-member tuple.
  static auto SingleMemberTuple(const PythonRef& member) -> PythonRef;

  static void MarkReachedEndOfModule(PyObject* module);
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_H_
