// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_SOUND_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_SOUND_H_

#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::ui_v1 {

class PythonClassUISound : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto Create(base::SoundAsset* sound) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong types.
  static auto FromPyObj(PyObject* o) -> PythonClassUISound& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassUISound*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  auto sound() const -> base::SoundAsset& {
    assert(sound_);
    return **sound_;
  }

  static PyTypeObject type_obj;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassUISound* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassUISound* self);
  static auto Play(PythonClassUISound* self, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static auto Stop(PythonClassUISound* self, PyObject* args, PyObject* keywds)
      -> PyObject*;

  Object::Ref<base::SoundAsset>* sound_;
  bool playing_;
  uint32_t play_id_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_SOUND_H_
