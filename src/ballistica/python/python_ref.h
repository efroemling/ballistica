// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_PYTHON_PYTHON_REF_H_
#define BALLISTICA_PYTHON_PYTHON_REF_H_

#include <string>

#include "ballistica/ballistica.h"

namespace ballistica {

/// A simple managed Python object reference.
class PythonRef {
 public:
  /// Defines referencing behavior when creating new instances.
  enum ReferenceBehavior {
    /// Steal the provided object reference (and throw an Exception if it is
    /// nullptr).
    kSteal,
    /// Steal the provided object reference or set as unreferenced if it is
    /// nullptr.
    kStealSoft,
    /// Acquire a new reference to the provided object (and throw an Exception
    /// if it is nullptr).
    kAcquire,
    /// Acquire a new reference to the provided object or set as unreferenced if
    /// it is nullptr.
    kAcquireSoft
  };

  /// Creates in an unreferenced state.
  PythonRef() {}  // NOLINT (using '= default' here errors)

  /// See ReferenceBehavior docs.
  PythonRef(PyObject* other, ReferenceBehavior behavior);

  /// Copy constructor acquires a new reference (or sets as unreferenced)
  /// depending on other.
  PythonRef(const PythonRef& other) { *this = other; }
  virtual ~PythonRef();

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

  /// Acquire a new reference to the passed object. Throws an exception if
  /// nullptr is passed.
  void Acquire(PyObject* obj);

  /// Steal the passed reference. Throws an Exception if nullptr is passed.
  void Steal(PyObject* obj);

  /// Release the held reference (if one is held).
  void Release();

  /// Clear the ref without decrementing its count and return the raw PyObject*
  auto HandOver() -> PyObject* {
    assert(obj_);
    PyObject* obj = obj_;
    obj_ = nullptr;
    return obj;
  }

  /// Return the underlying PyObject pointer.
  auto get() const -> PyObject* { return obj_; }

  /// Increment the ref-count for the underlying PyObject and return it as a
  /// pointer.
  auto NewRef() const -> PyObject*;

  /// Return whether we are pointing to a PyObject.
  auto exists() const -> bool { return obj_ != nullptr; }

  /// Return a ref to an attribute on our PyObject or throw an Exception.
  auto GetAttr(const char* name) const -> PythonRef;

  /// The equivalent of calling python str() on the contained PyObject.
  auto Str() const -> std::string;

  /// The equivalent of calling repr() on the contained PyObject.
  auto Repr() const -> std::string;

  /// For unicode, string, and ba.Lstr types, returns a utf8 string.
  /// Throws an exception for other types.
  auto ValueAsString() const -> std::string;
  auto ValueAsInt() const -> int64_t;

  /// Returns whether the underlying PyObject is callable.
  auto CallableCheck() const -> bool;

  /// Call the PyObject. On error, (optionally) prints errors and returns empty
  /// ref.
  auto Call(PyObject* args, PyObject* keywds = nullptr,
            bool print_errors = true) const -> PythonRef;
  auto Call(const PythonRef& args, const PythonRef& keywds = PythonRef(),
            bool print_errors = true) const -> PythonRef {
    return Call(args.get(), keywds.get(), print_errors);
  }
  auto Call() const -> PythonRef;

  /// Call with various args..
  auto Call(const Vector2f& val) const
      -> PythonRef;  // (val will be passed as tuple)

 private:
  PyObject* obj_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_PYTHON_PYTHON_REF_H_
