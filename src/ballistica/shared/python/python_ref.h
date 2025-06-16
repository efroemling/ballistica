// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_REF_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_REF_H_

#include <cassert>
#include <optional>
#include <string>
#include <vector>

#include "ballistica/shared/foundation/exception.h"

namespace ballistica {

/// A simple managed Python object reference.
class PythonRef {
 public:
  /// Defines referencing behavior when creating new instances.
  enum ReferenceBehavior {
    /// Steal the provided object reference. If nullptr is passed, it is
    /// assumed to be due to a Python exception occurring. The Python
    /// exception is then cleared, a C++ exception is raised, and a warning
    /// is logged if no Python exception was set.
    kSteal,
    /// Steal the provided object reference. If nullptr is passed, set as
    /// unreferenced. Does not touch Python exception state, so be sure to
    /// clear that yourself if the nullptr case is due to an Exception.
    kStealSoft,
    /// Acquire a new reference to the provided object. If nullptr is
    /// passed, it is assumed to be due to a Python exception occurring. The
    /// Python exception is then cleared, a C++ exception is raised, and a
    /// warning is logged if no Python exception was set.
    kAcquire,
    /// Acquire a new reference to the provided object. If nullptr is
    /// passed, set as unreferenced. Does not touch Python exception state,
    /// so be sure to clear that yourself if the nullptr case is due to an
    /// exception.
    kAcquireSoft
  };

  /// Creates in an unreferenced state.
  PythonRef() {}  // NOLINT (using '= default' here errors)

  /// See ReferenceBehavior docs.
  PythonRef(PyObject* obj, ReferenceBehavior behavior);

  /// Shortcut to create a new PythonRef using ReferenceBehavior::kSteal.
  static auto Stolen(PyObject* obj) -> PythonRef {
    return {obj, ReferenceBehavior::kSteal};
  }

  static auto StolenSoft(PyObject* obj) -> PythonRef {
    return {obj, ReferenceBehavior::kStealSoft};
  }

  /// Shortcut to create a new PythonRef using ReferenceBehavior::kAcquire.
  static auto Acquired(PyObject* obj) -> PythonRef {
    return {obj, ReferenceBehavior::kAcquire};
  }

  static auto AcquiredSoft(PyObject* obj) -> PythonRef {
    return {obj, ReferenceBehavior::kAcquireSoft};
  }

  /// Copy constructor acquires a new reference (or sets as unreferenced)
  /// depending on other.
  PythonRef(const PythonRef& other) { *this = other; }
  virtual ~PythonRef();

  /// Shortcut to create a string object.
  static auto FromString(const std::string& val) -> PythonRef;
  static auto SingleStringTuple(const std::string& val) -> PythonRef;

  /// Assignment from another PythonRef acquires a reference to the object
  /// referenced by other if there is one. If other has no reference, any
  /// reference of ours is cleared to match.
  auto operator=(const PythonRef& other) -> PythonRef& {
    assert(this != &other);  // Shouldn't be self-assigning.
    if (other.exists()) {
      Acquire(other.get());
    } else {
      Release();
    }
    return *this;
  }

  /// Comparing to another PythonRef does a pointer comparison
  /// (so basically the 'is' keyword in Python).
  /// Note that two unreferenced PythonRefs will be equal.
  auto operator==(const PythonRef& other) const -> bool {
    return (get() == other.get());
  }
  auto operator!=(const PythonRef& other) const -> bool {
    return !(*this == other);
  }

  /// Steal the provided object reference. If nullptr is passed, it is
  /// assumed to be due to a Python exception occurring. The Python
  /// exception is then cleared, a C++ exception is raised, and a warning is
  /// logged if no Python exception was set.
  void Steal(PyObject* obj);

  /// Steal the provided object reference. If nullptr is passed, set as
  /// unreferenced. Does not touch Python exception state, so be sure to
  /// clear that yourself if the nullptr case is due to an Exception.
  void StealSoft(PyObject* obj);

  /// Acquire a new reference to the provided object. If nullptr is passed,
  /// it is assumed to be due to a Python exception occurring. The Python
  /// exception is then cleared, a C++ exception is raised, and a warning is
  /// logged if no Python exception was set.
  void Acquire(PyObject* obj);

  /// Acquire a new reference to the provided object. If nullptr is passed,
  /// set as unreferenced. Does not touch Python exception state, so be sure
  /// to clear that yourself if the nullptr case is due to an exception.
  void AcquireSoft(PyObject* obj);

  /// Release the held reference (if one is held).
  void Release();

  /// Clear the ref without decrementing its count and return the raw
  /// PyObject*. Useful for functions that are expected to return a new
  /// Python ref.
  auto HandOver() -> PyObject* {
    assert(obj_);
    PyObject* obj = obj_;
    obj_ = nullptr;
    return obj;
  }

  /// Return the underlying PyObject pointer.
  auto get() const -> PyObject* { return obj_; }

  /// Return the underlying PyObject pointer. Throws an Exception if not set.
  auto operator*() const -> PyObject* {
    if (!obj_) {
      throw Exception("Dereferencing invalid PythonRef");
    }
    return obj_;
  };

  /// Increment the ref-count for the underlying PyObject and return it as a
  /// pointer.
  auto NewRef() const -> PyObject*;

  /// Return whether we are pointing to a PyObject.
  auto exists() const -> bool { return obj_ != nullptr; }

  /// Return a ref to an attribute on our PyObject or throw an Exception.
  auto GetAttr(const char* name) const -> PythonRef;

  /// Return an item from a dict obj. Returns empty ref if nonexistent.
  /// Throws Exception if an error occurs.
  auto DictGetItem(const char* name) const -> PythonRef;

  /// Return all items in a dict as C++ structures.
  auto DictItems() const -> std::vector<std::pair<PythonRef, PythonRef>>;

  /// The equivalent of calling Python str() on the contained PyObject, and
  /// gracefully handles invalid refs. To throw exceptions on invalid refs,
  /// use ValueAsString();
  auto Str() const -> std::string;

  /// The equivalent of calling repr() on the contained PyObject.
  /// Throws Exception on invalid refs.
  auto Repr() const -> std::string;

  /// Return the object's Python type object.
  auto Type() const -> PythonRef;

  auto ValueIsNone() const -> bool;

  /// For string and babase.Lstr types, returns a utf8 string. Throws an
  /// exception for other types.
  auto ValueAsLString() const -> std::string;

  auto ValueIsString() const -> bool;
  auto ValueAsString() const -> std::string;
  auto ValueAsStringSequence() const -> std::vector<std::string>;
  auto ValueAsOptionalString() const -> std::optional<std::string>;
  auto ValueAsOptionalStringSequence() const
      -> std::optional<std::vector<std::string>>;

  auto ValueAsInt() const -> int64_t;
  auto ValueAsDouble() const -> double;
  auto ValueAsOptionalInt() const -> std::optional<int64_t>;

  /// Returns whether the underlying PyObject is callable.
  /// Throws an exception if unset.
  auto CallableCheck() const -> bool;

  /// Return whether the underlying PyObject is unicode.
  /// Throws an exception if unset.
  auto UnicodeCheck() const -> bool;

  /// Call the PyObject. On error, (optionally) prints errors and returns
  /// empty ref.
  auto Call(PyObject* args, PyObject* keywds = nullptr,
            bool print_errors = true) const -> PythonRef;
  auto Call(const PythonRef& args, const PythonRef& keywds = PythonRef(),
            bool print_errors = true) const -> PythonRef {
    return Call(args.get(), keywds.get(), print_errors);
  }
  auto Call(bool print_errors = true) const -> PythonRef;

  /// Call with Vector2f passed as a tuple.
  auto Call(const Vector2f& val, bool print_errors = true) const -> PythonRef;

 private:
  void ThrowIfUnset() const;
  void SetObj(PyObject* obj);
  PyObject* obj_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_REF_H_
