// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/python_ref.h"

#include "ballistica/math/vector2f.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

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
  assert(g_python);
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

void PythonRef::Release() {
  assert(Python::HaveGIL());

  // Py_CLEAR uses a temp variable and assigns o to nullptr first
  // so we're safe if the clear triggers something that (again) releases or
  // destroys us.
  if (obj_) {
    Py_CLEAR(obj_);
  }
}

auto PythonRef::Str() const -> std::string {
  assert(Python::HaveGIL());
  if (!obj_) {
    return "<nullptr PyObject>";
  }
  PyObject* obj = PyObject_Str(obj_);
  if (!obj) {
    return "<error fetching python obj as string>";
  }
  PythonRef s(obj, PythonRef::kSteal);
  assert(PyUnicode_Check(obj));  // NOLINT (signed with bitwise)
  return PyUnicode_AsUTF8(s.get());
}

auto PythonRef::Repr() const -> std::string {
  assert(Python::HaveGIL());
  BA_PRECONDITION(obj_);
  PythonRef s(PyObject_Repr(obj_), PythonRef::kSteal);
  assert(PyUnicode_Check(s.get()));  // NOLINT (signed with bitwise)
  return PyUnicode_AsUTF8(s.get());
}

auto PythonRef::ValueAsString() const -> std::string {
  assert(Python::HaveGIL());
  BA_PRECONDITION(obj_);
  return Python::GetPyString(obj_);
}

auto PythonRef::ValueAsInt() const -> int64_t {
  assert(Python::HaveGIL());
  BA_PRECONDITION(obj_);
  return Python::GetPyInt64(obj_);
}

auto PythonRef::GetAttr(const char* name) const -> PythonRef {
  assert(Python::HaveGIL());
  BA_PRECONDITION(obj_);
  PyObject* val = PyObject_GetAttrString(get(), name);
  if (!val) {
    PyErr_Clear();
    throw Exception("Attribute not found: '" + std::string(name) + "'.",
                    PyExcType::kAttribute);
  }
  return PythonRef(val, PythonRef::kSteal);
}

auto PythonRef::NewRef() const -> PyObject* {
  assert(Python::HaveGIL());
  if (obj_ == nullptr) {
    throw Exception("PythonRef::NewRef() called with nullptr obj_");
  }
  Py_INCREF(obj_);
  return obj_;
}

auto PythonRef::CallableCheck() const -> bool {
  BA_PRECONDITION(obj_);
  assert(Python::HaveGIL());
  return static_cast<bool>(PyCallable_Check(obj_));
}

auto PythonRef::UnicodeCheck() const -> bool {
  BA_PRECONDITION(obj_);
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
  return Call(g_python->obj(Python::ObjID::kEmptyTuple).get());
}

auto PythonRef::Call(const Vector2f& val) const -> PythonRef {
  assert(Python::HaveGIL());
  PythonRef args(Py_BuildValue("((ff))", val.x, val.y), PythonRef::kSteal);
  return Call(args);
}

PythonRef::~PythonRef() { Release(); }

#pragma clang diagnostic pop

}  // namespace ballistica
