// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_SIMPLE_SOUND_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_SIMPLE_SOUND_H_

#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

/// A simple sound class we can use for minimal internal purposes.
/// This allows us to play sounds even if we are running without
/// a UI feature-set present.
class PythonClassSimpleSound : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto Create(SoundAsset* sound) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong types.
  static auto FromPyObj(PyObject* o) -> PythonClassSimpleSound& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassSimpleSound*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  auto sound() const -> SoundAsset& {
    assert(sound_);
    return **sound_;
  }

  static PyTypeObject type_obj;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassSimpleSound* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSimpleSound* self);
  Object::Ref<SoundAsset>* sound_;
  static auto Play(PythonClassSimpleSound* self, PyObject* args,
                   PyObject* keywds) -> PyObject*;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_SIMPLE_SOUND_H_
