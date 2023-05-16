// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/python/python_ref.h"

#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/math/vector2f.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica {

// Note: implicitly using core globals here; our behavior is undefined
// if core has not been imported by anyone yet.
using core::g_base_soft;
using core::g_core;

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "RedundantCast"

PythonRef::PythonRef(PyObject* obj_in, ReferenceBehavior b) {
  assert(Python::HaveGIL());
  switch (b) {
    case kSteal:
      Steal(obj_in);
      break;
    case kStealSoft:
      if (obj_in) {
        Steal(obj_in);
      }
      break;
    case kAcquire:
      Acquire(obj_in);
      break;
    case kAcquireSoft:
      if (obj_in) {
        Acquire(obj_in);
        break;
      }
      break;
  }
}

void PythonRef::Acquire(PyObject* obj_in) {
  BA_PRECONDITION(obj_in);
  assert(Python::HaveGIL());

  // Assign and increment the new one before decrementing our old
  // (in case its the same one or prev gets deallocated and accesses us
  // somehow).
  PyObject* prev = obj_;
  Py_INCREF(obj_in);
  obj_ = obj_in;
  if (prev) {
    Py_DECREF(prev);
  }
}

void PythonRef::AcquireSoft(PyObject* obj_in) {
  if (!obj_in) {
    Release();
    return;
  }
  Acquire(obj_in);
}

void PythonRef::Steal(PyObject* obj_in) {
  BA_PRECONDITION(obj_in);
  assert(Python::HaveGIL());

  // Assign before decrementing the old
  // (in case prev gets deallocated and accesses us somehow).
  PyObject* prev = obj_;
  obj_ = obj_in;
  if (prev) {
    Py_DECREF(prev);
  }
}

void PythonRef::StealSoft(PyObject* obj_in) {
  if (!obj_in) {
    Release();
    return;
  }
  Steal(obj_in);
}

void PythonRef::Release() {
  assert(Python::HaveGIL());

  // Py_CLEAR uses a temp variable and assigns o to nullptr first
  // so we're safe if the clear triggers something that (again) releases or
  // destroys us.
  if (obj_) {
    Py_CLEAR(obj_);
  }
}

auto PythonRef::FromString(const std::string& val) -> PythonRef {
  return Stolen(PyUnicode_FromString(val.c_str()));
}

auto PythonRef::Str() const -> std::string {
  assert(Python::HaveGIL());
  if (!obj_) {
    return "<nullptr PyObject>";
  }
  PyObject* str_obj = PyObject_Str(obj_);
  if (!str_obj) {
    PyErr_Clear();
    return "<error fetching Python obj as string>";
  }
  auto s = PythonRef::Stolen(str_obj);
  assert(PyUnicode_Check(str_obj));  // NOLINT (signed with bitwise)
  return PyUnicode_AsUTF8(s.Get());
}

auto PythonRef::Repr() const -> std::string {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  auto s = PythonRef::Stolen(PyObject_Repr(obj_));
  assert(PyUnicode_Check(s.Get()));  // NOLINT (signed with bitwise)
  return PyUnicode_AsUTF8(s.Get());
}

auto PythonRef::Type() const -> PythonRef {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return {PyObject_Type(obj_), PythonRef::kSteal};
}

auto PythonRef::ValueAsLString() const -> std::string {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  if (g_base_soft) {
    return g_base_soft->GetPyLString(obj_);
  }
  throw Exception("Can't return as LString; _babase not imported.");
}

auto PythonRef::ValueAsString() const -> std::string {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return Python::GetPyString(obj_);
}

void PythonRef::ThrowIfUnset() const {
  if (!obj_) {
    throw Exception("PythonRef is unset.", PyExcType::kValue);
  }
}

auto PythonRef::ValueAsOptionalString() const -> std::optional<std::string> {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  if (obj_ == Py_None) {
    return {};
  }
  return Python::GetPyString(obj_);
}

auto PythonRef::ValueAsInt() const -> int64_t {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return Python::GetPyInt64(obj_);
}

auto PythonRef::GetAttr(const char* name) const -> PythonRef {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  PyObject* val = PyObject_GetAttrString(Get(), name);
  if (!val) {
    PyErr_Clear();
    throw Exception("Attribute not found: '" + std::string(name) + "'.",
                    PyExcType::kAttribute);
  }
  return {val, PythonRef::kSteal};
}

auto PythonRef::DictGetItem(const char* name) const -> PythonRef {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  PyObject* key = PyUnicode_FromString(name);
  PyObject* out = PyDict_GetItemWithError(obj_, key);
  Py_DECREF(key);
  if (out) {
    // 'out' is a borrowed ref.
    return PythonRef::Acquired(out);
  }
  // Ok; we failed. If its because of an error, raise an exception.
  if (PyErr_Occurred()) {
    // Hmm; should we print the Python error here or translate it into our
    // C++ exception str?
    PyErr_Clear();
    throw Exception(
        "PythonRef::DictGetItem() errored. Is your obj not a dict?");
  }
  // Must be because dict key didn't exist. Return empty ref.
  return {};
}

auto PythonRef::NewRef() const -> PyObject* {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  Py_INCREF(obj_);
  return obj_;
}

auto PythonRef::CallableCheck() const -> bool {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return static_cast<bool>(PyCallable_Check(obj_));
}

auto PythonRef::UnicodeCheck() const -> bool {
  ThrowIfUnset();
  assert(Python::HaveGIL());
  return static_cast<bool>(PyUnicode_Check(obj_));
}

auto PythonRef::Call(PyObject* args, PyObject* keywds, bool print_errors) const
    -> PythonRef {
  assert(obj_);
  assert(Python::HaveGIL());
  assert(CallableCheck());
  assert(args);
  assert(PyTuple_Check(args));              // NOLINT (signed bitwise stuff)
  assert(!keywds || PyDict_Check(keywds));  // NOLINT (signed bitwise)
  PyObject* out = PyObject_Call(obj_, args, keywds);
  if (!out) {
    if (print_errors) {
      // Save/restore error or it can mess with context print calls.
      BA_PYTHON_ERROR_SAVE;
      PySys_WriteStderr("Exception in Python call:\n");
      Python::PrintContextAuto();
      BA_PYTHON_ERROR_RESTORE;

      // We pass zero here to avoid grabbing references to this exception
      // which can cause objects to stick around and trip up our deletion checks
      // (nodes, actors existing after their games have ended).
      PyErr_PrintEx(0);
    }
    PyErr_Clear();
  }
  return out ? PythonRef(out, PythonRef::kSteal) : PythonRef();
}

auto PythonRef::Call() const -> PythonRef {
  // NOTE: Using core globals directly here; normally don't do this.
  assert(g_core);
  return Call(
      g_core->python->objs().Get(core::CorePython::ObjID::kEmptyTuple).Get());
}

auto PythonRef::Call(const Vector2f& val) const -> PythonRef {
  assert(Python::HaveGIL());
  PythonRef args(Py_BuildValue("((ff))", val.x, val.y), PythonRef::kSteal);
  return Call(args);
}

PythonRef::~PythonRef() { Release(); }

#pragma clang diagnostic pop

}  // namespace ballistica
