// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_MATERIAL_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_MATERIAL_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

class PythonClassMaterial : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;

  auto GetMaterial(bool doraise = true) const -> Material* {
    Material* m = material_->Get();
    if ((!m) && doraise) throw Exception("Invalid Material");
    return m;
  }

 private:
  static bool s_create_empty_;
  static PyMethodDef tp_methods[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void Delete(Object::Ref<Material>* m);
  static void tp_dealloc(PythonClassMaterial* self);
  static auto tp_getattro(PythonClassMaterial* self, PyObject* attr)
      -> PyObject*;
  static auto tp_setattro(PythonClassMaterial* self, PyObject* attr,
                          PyObject* val) -> int;
  static auto tp_repr(PythonClassMaterial* self) -> PyObject*;
  static auto AddActions(PythonClassMaterial* self, PyObject* args,
                         PyObject* keywds) -> PyObject*;
  static auto Dir(PythonClassMaterial* self) -> PyObject*;
  Object::Ref<Material>* material_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_MATERIAL_H_
