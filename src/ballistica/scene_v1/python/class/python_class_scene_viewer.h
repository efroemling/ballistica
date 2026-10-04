// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_VIEWER_H_
#define BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_VIEWER_H_

#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::scene_v1 {

/// Python wrapper for a SceneViewerContext. The wrapper owns the
/// context; the viewer lives as long as the wrapper does (or until
/// shutdown() is called on it).
class PythonClassSceneViewer : public PythonClass {
 public:
  static auto type_name() -> const char*;
  static void SetupType(PyTypeObject* cls);
  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }
  static PyTypeObject type_obj;

  /// Return our viewer context; throws an exception if it has been
  /// shut down.
  auto GetViewer() const -> SceneViewerContext*;

 private:
  static PyMethodDef tp_methods[];
  static PyGetSetDef tp_getsets[];
  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject*;
  static void tp_dealloc(PythonClassSceneViewer* self);
  static auto tp_repr(PythonClassSceneViewer* self) -> PyObject*;
  static auto GetContext(PythonClassSceneViewer* self, void* closure)
      -> PyObject*;
  static auto GetTexture(PythonClassSceneViewer* self, void* closure)
      -> PyObject*;
  static auto GetSource(PythonClassSceneViewer* self, void* closure)
      -> PyObject*;
  static auto SetCamera(PythonClassSceneViewer* self, PyObject* args,
                        PyObject* keywds) -> PyObject*;
  static auto SetSize(PythonClassSceneViewer* self, PyObject* args,
                      PyObject* keywds) -> PyObject*;
  static auto SetSound(PythonClassSceneViewer* self, PyObject* args,
                       PyObject* keywds) -> PyObject*;
  static auto SetCameraShake(PythonClassSceneViewer* self, PyObject* args,
                             PyObject* keywds) -> PyObject*;
  static auto SetCameraTiltOrbit(PythonClassSceneViewer* self, PyObject* args,
                                 PyObject* keywds) -> PyObject*;
  static auto SetDepthOfField(PythonClassSceneViewer* self, PyObject* args,
                              PyObject* keywds) -> PyObject*;
  static auto Shutdown(PythonClassSceneViewer* self) -> PyObject*;
  Object::Ref<SceneViewerContext>* viewer_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_CLASS_PYTHON_CLASS_SCENE_VIEWER_H_
