// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_FEATURE_SET_DATA_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_FEATURE_SET_DATA_H_

#include <string>

#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

/// A simple Python class we use to hold a pointer to a C++
/// FeatureSetNativeComponent instance. This allows us to piggyback on Python's
/// import system in our C++ layer.
class PythonClassFeatureSetData : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto Create(FeatureSetNativeComponent* feature_set) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong types.
  static auto FromPyObj(PyObject* o) -> PythonClassFeatureSetData& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassFeatureSetData*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  auto feature_set() const -> FeatureSetNativeComponent* {
    assert(feature_set_);
    return feature_set_;
  }

  static PyTypeObject type_obj;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassFeatureSetData* self);
  FeatureSetNativeComponent* feature_set_{};
  static auto Play(PythonClassFeatureSetData* self, PyObject* args,
                   PyObject* keywds) -> PyObject*;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_FEATURE_SET_DATA_H_
