// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/python/python_ref.h"

#include <list>
#include <string>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/math/vector2f.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica {

// Note: implicitly using core globals here; our behavior is undefined
// if core has not been imported by anyone yet.
using core::g_base_soft;
using core::g_core;

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "RedundantCast"

static void ClearPythonExceptionAndWarnIfUnset() {
  // We're assuming that a nullptr passed to us means a Python call has
  // failed and has set an exception. So we're clearing that exception since
  // we'll be handling it by converting it to a C++ one. However let's warn
  // if we were passed nullptr but *no* Python exception is set. We want to
  // avoid that situation because it opens up the possibility of us clearing
  // exceptions that aren't related to our nullptr.
  if (!PyErr_Occurred()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kWarning,
        "A PythonRef acquire/steal call was passed nullptr but no Python "
        "exception is set. This situation should be avoided; only pass "
        "nullptr to acquire/steal if it is the direct result of a Python "
        "exception.");
  } else {
    PyErr_Clear();
  }
}

PythonRef::PythonRef(PyObject* obj, ReferenceBehavior b) {
  switch (b) {
    case kSteal:
      Steal(obj);
      break;
    case kStealSoft:
      StealSoft(obj);
      break;
    case kAcquire:
      Acquire(obj);
      break;
    case kAcquireSoft:
      AcquireSoft(obj);
      break;
  }
}

void PythonRef::SetObj(PyObject* obj_in) {
  // Assign before decrementing the old
  // (in case prev gets deallocated and accesses us somehow).
  PyObject* prev = obj_;
  obj_ = obj_in;
  if (prev) {
    Py_DECREF(prev);
  }
}

void PythonRef::Steal(PyObject* obj_in) {
  assert(Python::HaveGIL());
  if (!obj_in) {
    ClearPythonExceptionAndWarnIfUnset();
    throw Exception("nullptr passed to PythonRef::Steal.");
  }
  SetObj(obj_in);
}

void PythonRef::StealSoft(PyObject* obj_in) {
  assert(Python::HaveGIL());
  if (!obj_in) {
    // 'Soft' versions don't assume nullptr is due to an exception,
    // so we don't touch Python exception state here.
    Release();
    return;
  }
  SetObj(obj_in);
}

void PythonRef::Acquire(PyObject* obj_in) {
  assert(Python::HaveGIL());
  if (!obj_in) {
    ClearPythonExceptionAndWarnIfUnset();
    throw Exception("nullptr passed to PythonRef::Acquire.");
  }
  Py_INCREF(obj_in);
  SetObj(obj_in);
}

void PythonRef::AcquireSoft(PyObject* obj_in) {
  assert(Python::HaveGIL());
  if (!obj_in) {
    // 'Soft' versions don't assume nullptr is due to an exception,
    // so we don't touch Python exception state here.
    Release();
    return;
  }
  Py_INCREF(obj_in);
  SetObj(obj_in);
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

auto PythonRef::SingleStringTuple(const std::string& val) -> PythonRef {
  return Stolen(Py_BuildValue("(s)", val.c_str()));
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
  return PyUnicode_AsUTF8(s.get());
}

auto PythonRef::Repr() const -> std::string {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  auto s = PythonRef::Stolen(PyObject_Repr(obj_));
  assert(PyUnicode_Check(s.get()));  // NOLINT (signed with bitwise)
  return PyUnicode_AsUTF8(s.get());
}

auto PythonRef::Type() const -> PythonRef {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return {PyObject_Type(obj_), PythonRef::kSteal};
}

auto PythonRef::ValueIsNone() const -> bool {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return obj_ == Py_None;
}

auto PythonRef::ValueIsString() const -> bool {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return Python::IsString(obj_);
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
  return Python::GetString(obj_);
}

auto PythonRef::ValueAsStringSequence() const -> std::vector<std::string> {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return Python::GetStrings(obj_);
}

auto PythonRef::ValueAsOptionalInt() const -> std::optional<int64_t> {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  if (obj_ == Py_None) {
    return {};
  }
  return Python::GetInt(obj_);
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
  return Python::GetString(obj_);
}

auto PythonRef::ValueAsOptionalStringSequence() const
    -> std::optional<std::vector<std::string>> {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  if (obj_ == Py_None) {
    return {};
  }
  return Python::GetStrings(obj_);
}

auto PythonRef::ValueAsInt() const -> int64_t {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return Python::GetInt64(obj_);
}

auto PythonRef::ValueAsDouble() const -> double {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  return Python::GetDouble(obj_);
}

auto PythonRef::GetAttr(const char* name) const -> PythonRef {
  assert(Python::HaveGIL());
  ThrowIfUnset();
  PyObject* val = PyObject_GetAttrString(get(), name);
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
  assert(PyDict_Check(obj_));  // Caller's job to ensure this.
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

auto PythonRef::DictItems() const
    -> std::vector<std::pair<PythonRef, PythonRef>> {
  assert(Python::HaveGIL());
  ThrowIfUnset();

  assert(PyDict_Check(obj_));  // Caller's job to ensure this.

  Py_ssize_t pos{};
  PyObject *key, *value;
  std::vector<std::pair<PythonRef, PythonRef>> out;
  out.resize(PyDict_Size(obj_));
  size_t i = 0;
  while (PyDict_Next(obj_, &pos, &key, &value)) {
    out[i].first.Acquire(key);
    out[i].second.Acquire(value);
    i++;
  }
  return out;
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

static inline auto _HandleCallResults(PyObject* out, bool print_errors)
    -> PyObject* {
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
  return out;
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
  out = _HandleCallResults(out, print_errors);
  return out ? PythonRef(out, PythonRef::kSteal) : PythonRef();
}

auto PythonRef::Call(bool print_errors) const -> PythonRef {
  assert(obj_);
  assert(Python::HaveGIL());
  assert(CallableCheck());
  PyObject* out = PyObject_CallNoArgs(obj_);
  out = _HandleCallResults(out, print_errors);
  return out ? PythonRef(out, PythonRef::kSteal) : PythonRef();
}

auto PythonRef::Call(const Vector2f& val, bool print_errors) const
    -> PythonRef {
  assert(Python::HaveGIL());
  PythonRef args(Py_BuildValue("((ff))", val.x, val.y), PythonRef::kSteal);
  return Call(args.get(), nullptr, print_errors);
}

PythonRef::~PythonRef() { Release(); }

#pragma clang diagnostic pop

}  // namespace ballistica
