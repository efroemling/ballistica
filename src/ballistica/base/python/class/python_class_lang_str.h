// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_LANG_STR_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_LANG_STR_H_

#include <memory>
#include <string>

#include "ballistica/base/support/lang_str.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

/// Python wrapper for the native language-string value (see
/// base::LangStr). Unlike the asset-ref wrapper classes, this is a
/// *value* class: freely constructible from Python (from canonical wire
/// JSON), immutable, content-compared/hashed, and thread-agnostic --
/// the wrapped value's atomic refcount means creation and destruction
/// need no logic-thread involvement. Wrappers are minted per touch;
/// native code never caches one, so no native<->Python ref cycles can
/// form.
class PythonClassLangStr : public PythonClass {
 public:
  static auto type_name() -> const char* { return "LangStr"; }
  static void SetupType(PyTypeObject* cls);
  static PyTypeObject type_obj;
  static PyMethodDef tp_methods[];
  static PyGetSetDef tp_getsets[];

  /// Mint a wrapper around an existing native value.
  static auto Create(std::shared_ptr<const LangStr> value) -> PyObject*;

  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong
  /// types.
  static auto FromPyObj(PyObject* o) -> PythonClassLangStr& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassLangStr*>(o);
    }
    throw Exception(std::string("Expected a babase.LangStr; got a ")
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  auto value() const -> const std::shared_ptr<const LangStr>& {
    assert(value_ && *value_);
    return *value_;
  }

 private:
  static auto tp_repr(PythonClassLangStr* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassLangStr* self);
  static auto tp_richcompare(PythonClassLangStr* self, PyObject* other, int op)
      -> PyObject*;
  static auto tp_hash(PythonClassLangStr* self) -> Py_hash_t;
  static auto FromText(PyObject* cls, PyObject* arg) -> PyObject*;
  static auto GetSpec(PythonClassLangStr* self, void* closure) -> PyObject*;
  static auto Evaluate(PythonClassLangStr* self) -> PyObject*;
  static auto ToJson(PythonClassLangStr* self) -> PyObject*;
  static auto ToResourceJson(PythonClassLangStr* self) -> PyObject*;

  static std::shared_ptr<const LangStr>* s_pending_value_;

  // Heap-allocated so tp_alloc's zero-fill is a valid empty state
  // (C++ constructors never run for Python-allocated instances).
  // Deletable from any thread (atomic refcount).
  std::shared_ptr<const LangStr>* value_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_LANG_STR_H_
