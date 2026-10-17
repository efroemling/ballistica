// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_mesh_viewer.h"

#include <string>

#include "ballistica/base/graphics/support/mesh_viewer.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/ui_v1/python/class/python_class_viewer_source.h"
#include "ballistica/ui_v1/support/viewer_source.h"

namespace ballistica::ui_v1 {

/// A mesh viewer as seen by ui. Holds no claim on it; once it is gone
/// there is simply nothing to show.
class PythonClassMeshViewer::Source : public ViewerSource {
 public:
  explicit Source(base::MeshViewer* viewer) : viewer_(viewer) {}

  auto GetViewerTexture() -> base::TextureAsset* override {
    base::MeshViewer* viewer = viewer_.get();
    return viewer != nullptr ? viewer->view()->texture() : nullptr;
  }

  void SetViewerPixelSize(int width, int height) override {
    if (base::MeshViewer* viewer = viewer_.get()) {
      viewer->SetSize(width, height);
    }
  }

  auto GetName() const -> std::string override { return "MeshViewer"; }

  void SetViewerOverlay(bool overlay) override {
    if (base::MeshViewer* viewer = viewer_.get()) {
      viewer->SetTransparent(overlay);
    }
  }

  auto IsViewerLoading() const -> bool override {
    base::MeshViewer* viewer = viewer_.get();
    return viewer != nullptr && viewer->loading();
  }

  auto GetViewerFailure() const -> std::string override {
    base::MeshViewer* viewer = viewer_.get();
    return viewer != nullptr ? viewer->failure() : std::string();
  }

 private:
  Object::WeakRef<base::MeshViewer> viewer_;
};

PyTypeObject PythonClassMeshViewer::type_obj;

auto PythonClassMeshViewer::type_name() -> const char* { return "MeshViewer"; }

void PythonClassMeshViewer::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bauiv1.MeshViewer";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_basicsize = sizeof(PythonClassMeshViewer);

  // clang-format off
  cls->tp_doc =
      "MeshViewer(width: int, height: int)\n"
      "\n"
      "A few meshes drawn turning in a picture of their own.\n"
      "\n"
      "What a mesh-viewer depiction shows: give it one with\n"
      ":meth:`set_depiction` and show it by handing its :attr:`source`\n"
      "to whatever draws viewers. It frames its meshes to fill the\n"
      "picture, turns them slowly, and can be swung around\n"
      "(:meth:`orbit`). It runs only while its picture is being drawn.\n"
      "\n"
      "Size is in pixels; whatever shows the picture sets it to the\n"
      "size it shows it at.\n"
      "\n"
      "The viewer lives as long as this object does.\n"
      "\n"
      ":meta private:";
  // clang-format on

  cls->tp_methods = tp_methods;
  cls->tp_getset = tp_getsets;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassMeshViewer::GetViewer_() const -> base::MeshViewer* {
  base::MeshViewer* viewer = viewer_->get();
  if (viewer == nullptr) {
    throw Exception("MeshViewer has been shut down.", PyExcType::kNotFound);
  }
  return viewer;
}

auto PythonClassMeshViewer::tp_new(PyTypeObject* type, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassMeshViewer*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;

  // Do anything that might throw an exception *before* our placement-new
  // stuff so we don't have to worry about cleaning it up on errors.
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  int width;
  int height;
  static const char* kwlist[] = {"width", "height", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "ii", const_cast<char**>(kwlist), &width, &height)) {
    // ew; can't throw an exception here because we want to keep the
    // python one that was just set. Just manually do a free I guess.
    type->tp_free(self);
    return nullptr;
  }
  if (width < 1 || height < 1 || width > base::MeshViewer::kMaxSize
      || height > base::MeshViewer::kMaxSize) {
    throw Exception("Invalid size " + std::to_string(width) + "x"
                        + std::to_string(height) + "; each must be 1-"
                        + std::to_string(base::MeshViewer::kMaxSize) + ".",
                    PyExcType::kValue);
  }
  if (g_core->HeadlessMode()) {
    throw Exception("MeshViewers are not available in headless builds.");
  }
  auto viewer(Object::New<base::MeshViewer>(width, height));
  self->viewer_ = new Object::Ref<base::MeshViewer>(viewer);
  self->source_ = new Object::Ref<Source>(Object::New<Source>(viewer.get()));
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassMeshViewer::tp_dealloc(PythonClassMeshViewer* self) {
  BA_PYTHON_TRY;

  // These have to be deleted in the logic thread - push a call if
  // need be.. otherwise do it immediately.
  Object::Ref<base::MeshViewer>* viewer = self->viewer_;
  Object::Ref<Source>* source = self->source_;
  if (!g_base->InLogicThread()) {
    g_base->logic->event_loop()->PushCall([viewer, source] {
      delete viewer;
      delete source;
    });
  } else {
    delete viewer;
    delete source;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassMeshViewer::tp_repr(PythonClassMeshViewer* self) -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("s", std::string("<bauiv1.MeshViewer at "
                                        + Utils::PtrToString(self) + ">")
                                .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassMeshViewer::GetSource(PythonClassMeshViewer* self,
                                      void* closure) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  self->GetViewer_();  // (Raises if we've been shut down.)
  return PythonClassViewerSource::Create(self->source_->get());
  BA_PYTHON_CATCH;
}

auto PythonClassMeshViewer::SetDepiction(PythonClassMeshViewer* self,
                                         PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  const char* json;
  static const char* kwlist[] = {"json", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &json)) {
    return nullptr;
  }
  if (self->GetViewer_()->SetDepiction(json)) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

auto PythonClassMeshViewer::Orbit(PythonClassMeshViewer* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float dx;
  float dy;
  static const char* kwlist[] = {"dx", "dy", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "ff",
                                   const_cast<char**>(kwlist), &dx, &dy)) {
    return nullptr;
  }
  self->GetViewer_()->Orbit(dx, dy);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassMeshViewer::SetDefaultBackground(PythonClassMeshViewer* self,
                                                 PyObject* args,
                                                 PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float r;
  float g;
  float b;
  static const char* kwlist[] = {"color", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "(fff)",
                                   const_cast<char**>(kwlist), &r, &g, &b)) {
    return nullptr;
  }
  self->GetViewer_()->SetDefaultBackground({r, g, b});
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassMeshViewer::Shutdown(PythonClassMeshViewer* self) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  // Doing this more than once is fine; our source then has nothing to
  // show.
  self->viewer_->Clear();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassMeshViewer::tp_methods[] = {
    {"set_depiction", (PyCFunction)SetDepiction, METH_VARARGS | METH_KEYWORDS,
     "set_depiction(json: str) -> bool\n"
     "\n"
     "Show what a mesh-viewer depiction's json describes.\n"
     "\n"
     "Returns False (and shows nothing) if the json can't be used.\n"
     "Showing the same json again does nothing; showing other meshes\n"
     "reframes to fit them."},
    {"set_default_background", (PyCFunction)SetDefaultBackground,
     METH_VARARGS | METH_KEYWORDS,
     "set_default_background(color: tuple[float, float, float]) -> None\n"
     "\n"
     "Set what shows behind the meshes when a depiction doesn't say.\n"
     "\n"
     "Whoever shows the viewer knows what blends in where (a doc-ui\n"
     "viewer pane's own blank color, say)."},
    {"orbit", (PyCFunction)Orbit, METH_VARARGS | METH_KEYWORDS,
     "orbit(dx: float, dy: float) -> None\n"
     "\n"
     "Swing the view around by a drag.\n"
     "\n"
     "Motion is in fractions of the picture's width and height, up\n"
     "being positive; a full width across is half a turn."},
    {"shutdown", (PyCFunction)Shutdown, METH_NOARGS,
     "shutdown() -> None\n"
     "\n"
     "Let go of the viewer for good.\n"
     "\n"
     "Its source shows nothing from here on and most calls on this\n"
     "object raise. Happens by itself when this object goes away;\n"
     "call it to not depend on when that is."},
    {nullptr}  // Sentinel
};

PyGetSetDef PythonClassMeshViewer::tp_getsets[] = {
    {const_cast<char*>("source"), (getter)GetSource, nullptr,
     const_cast<char*>(
         "source: bauiv1.ViewerSource\n"
         "\n"
         "Us as something a live depiction can show. It holds no claim\n"
         "on us; showing it once we are gone shows nothing."),
     nullptr},
    {nullptr}  // Sentinel
};

}  // namespace ballistica::ui_v1
