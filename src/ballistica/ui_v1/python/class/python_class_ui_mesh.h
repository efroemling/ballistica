// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_MESH_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_MESH_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::ui_v1 {

class PythonClassUIMesh : public PythonClass {
 public:
  static void SetupType(PyTypeObject* cls);
  static auto type_name() -> const char*;
  static auto Create(const Object::Ref<base::MeshAsset>& mesh) -> PyObject*;
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong types.
  static auto FromPyObj(PyObject* o) -> PythonClassUIMesh& {
    if (Check(o)) {
      return *reinterpret_cast<PythonClassUIMesh*>(o);
    }
    throw Exception(std::string("Expected a ") + type_name() + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  auto mesh() const -> base::MeshAsset& {
    assert(mesh_);
    return **mesh_;
  }

  static PyTypeObject type_obj;

 private:
  static PyMethodDef tp_methods[];
  static auto tp_repr(PythonClassUIMesh* self) -> PyObject*;
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassUIMesh* self);
  Object::Ref<base::MeshAsset>* mesh_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_UI_MESH_H_
