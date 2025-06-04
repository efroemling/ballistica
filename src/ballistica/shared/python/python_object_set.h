// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_OBJECT_SET_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_OBJECT_SET_H_

#include <string>
#include <vector>

#include "ballistica/shared/python/python_ref.h"

namespace ballistica {

class PythonObjectSetBase {
 public:
  explicit PythonObjectSetBase(int objcount) : objs_(objcount) {}
  ~PythonObjectSetBase();
  void StoreObj(int id, PyObject* pyobj);
  void StoreObjCallable(int id, PyObject* pyobj);
  void StoreObj(int id, const char* expression, PyObject* context = nullptr);
  void StoreObjCallable(int id, const char* expression,
                        PyObject* context = nullptr);

  /// Access a particular Python object we've grabbed/stored.
  auto Obj(int id) const -> const PythonRef& {
    assert(id >= 0);
    assert(id < static_cast<int>(objs_.size()));
    assert(objs_[id].exists());
    return objs_[id];
  }

  /// Return whether we have a particular Python object.
  auto ObjExists(int id) const -> bool {
    assert(id >= 0);
    assert(id < static_cast<int>(objs_.size()));
    return objs_[static_cast<int>(id)].exists();
  }

  /// Push a call to a preset obj to the logic thread.
  void PushObjCall(int id) const;

  /// Push a call with a single string arg.
  void PushObjCall(int id, const std::string& arg) const;

 private:
  std::vector<PythonRef> objs_;
};

/// A class to store and retrieve different Python objects based on enums.
/// Object values can be set manually, or a binding_FOO.py file can be used
/// to provide values in a way that integrates cleanly with Python
/// type-checking.
template <typename T>
class PythonObjectSet : public PythonObjectSetBase {
 public:
  PythonObjectSet() : PythonObjectSetBase(static_cast<int>(T::kLast)) {}

  /// Set the value for a named object. This grabs a new reference to the
  /// passed PyObject.
  void Store(T id, PyObject* pyobj) { StoreObj(static_cast<int>(id), pyobj); }

  /// Set the value for a named object and verify that it is a callable.
  /// This grabs a new reference to the passed PyObject.
  void StoreCallable(T id, PyObject* pyobj) {
    StoreObjCallable(static_cast<int>(id), pyobj);
  }

  /// Set the value for a named object to the result of a Python expression.
  /// This grabs a new reference to the passed PyObject.
  void Store(T id, const char* expression, PyObject* context = nullptr) {
    StoreObj(static_cast<int>(id), expression, context);
  }

  /// Set the value for a named object to the result of a Python expression
  /// and verify that it is callable.
  /// This grabs a new reference to the passed PyObject.
  void StoreCallable(T id, const char* expression,
                     PyObject* context = nullptr) {
    StoreObjCallable(static_cast<int>(id), expression, context);
  }

  /// Access a particular Python object we've grabbed/stored.
  auto Get(T id) const -> const PythonRef& { return Obj(static_cast<int>(id)); }

  /// Return whether we have a particular Python object.
  auto Exists(T id) const -> bool { return ObjExists(static_cast<int>(id)); }

  // Note to self: future-me might wonder why we don't simply add PushCall()
  // methods to PythonRef instead of here. The reason is that we would need to
  // jump through more hoops to manage the gil and ref-counts in that case:
  // grabbing the gil in the calling thread, incrementing the obj ref
  // count so it doesn't die before being called, and then decrementing it
  // later from the logic thread. By implementing push-calls at the set level,
  // however, we can simply kick an id over to the logic thread since we
  // know the gil will be held there and we know the obj will remain referenced
  // by the set.

  /// Convenience function to push a call to an obj to the logic thread.
  void PushCall(T id) const { PushObjCall(static_cast<int>(id)); }

  /// Push a call with a single string arg.
  void PushCall(T id, const std::string& arg) const {
    PushObjCall(static_cast<int>(id), arg);
  }
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_OBJECT_SET_H_
