// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_TEXTURE_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_TEXTURE_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::ui_v1 {

class PythonClassUITexture : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto Create(const Object::Ref<base::TextureAsset>& texture)
      -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong types.
  static auto FromPyObj(PyObject* o) -> PythonClassUITexture& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassUITexture*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  auto texture() const -> base::TextureAsset& {
    assert(texture_);
    return **texture_;
  }

  static PyTypeObject type_obj;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassUITexture* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassUITexture* self);
  Object::Ref<base::TextureAsset>* texture_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_TEXTURE_H_
