// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_MESH_VIEWER_H_
#define BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_MESH_VIEWER_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::base {
class MeshViewer;
}

namespace ballistica::ui_v1 {

/// Python wrapper for a base::MeshViewer, plus it as a ViewerSource.
/// The wrapper owns the viewer; it lives as long as the wrapper does
/// (or until shutdown() is called on it).
class PythonClassMeshViewer : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;

 private:
  class Source;

  /// Our viewer; throws if it has been shut down.
  auto GetViewer_() const -> base::MeshViewer*;

  static PyMethodDef tp_methods[];
  static PyGetSetDef tp_getsets[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassMeshViewer* self);
  static auto tp_repr(PythonClassMeshViewer* self) -> PyObject*;
  static auto GetSource(PythonClassMeshViewer* self, void* closure)
      -> PyObject*;
  static auto SetDepiction(PythonClassMeshViewer* self, PyObject* args,
                           PyObject* keywds) -> PyObject*;
  static auto Orbit(PythonClassMeshViewer* self, PyObject* args,
                    PyObject* keywds) -> PyObject*;
  static auto SetDefaultBackground(PythonClassMeshViewer* self, PyObject* args,
                                   PyObject* keywds) -> PyObject*;
  static auto Shutdown(PythonClassMeshViewer* self) -> PyObject*;

  Object::Ref<base::MeshViewer>* viewer_;
  Object::Ref<Source>* source_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_PYTHON_CLASS_PYTHON_CLASS_MESH_VIEWER_H_
