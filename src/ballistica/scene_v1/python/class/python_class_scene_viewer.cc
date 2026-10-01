// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_viewer.h"

#include <string>

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/support/fixed_camera.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/python/class/python_class_context_ref.h"
#include "ballistica/scene_v1/support/scene_viewer_context.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/ui_v1/python/class/python_class_ui_texture.h"
#include "ballistica/ui_v1/python/class/python_class_viewer_source.h"

namespace ballistica::scene_v1 {

PyTypeObject PythonClassSceneViewer::type_obj;

auto PythonClassSceneViewer::type_name() -> const char* {
  return "SceneViewer";
}

static void CheckSize_(int width, int height) {
  if (width < 1 || height < 1 || width > SceneViewerContext::kMaxSize
      || height > SceneViewerContext::kMaxSize) {
    throw Exception("Invalid size " + std::to_string(width) + "x"
                        + std::to_string(height) + "; each must be 1-"
                        + std::to_string(SceneViewerContext::kMaxSize) + ".",
                    PyExcType::kValue);
  }
}

void PythonClassSceneViewer::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.SceneViewer";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_basicsize = sizeof(PythonClassSceneViewer);

  // clang-format off
  cls->tp_doc =
      "SceneViewer(width: int, height: int)\n"
      "\n"
      "A self-contained scene drawn to a texture, for showing in ui.\n"
      "\n"
      "The scene is this machine's alone and wholly separate from any\n"
      "game going on: it has its own nodes, look, camera, and clock,\n"
      "and makes no sound. Build what should be in it by creating\n"
      "nodes, materials, and so on under its :attr:`context`, and show\n"
      "it by handing its :attr:`source` to a viewer widget (or by\n"
      "drawing its :attr:`texture` some other way). It runs only while\n"
      "its picture is being drawn somewhere and stands still otherwise.\n"
      "\n"
      "Size is in pixels. A viewer widget sets it to the size it shows\n"
      "the picture at, so what is passed here matters only until then\n"
      "(or when drawing the texture some other way).\n"
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

auto PythonClassSceneViewer::GetViewer() const -> SceneViewerContext* {
  SceneViewerContext* viewer = viewer_->get();
  if (viewer == nullptr || viewer->shutting_down()) {
    throw Exception("SceneViewer has been shut down.", PyExcType::kNotFound);
  }
  return viewer;
}

auto PythonClassSceneViewer::tp_new(PyTypeObject* type, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneViewer*>(type->tp_alloc(type, 0));
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
  CheckSize_(width, height);
  if (g_core->HeadlessMode()) {
    throw Exception("SceneViewers are not available in headless builds.");
  }
  auto viewer(Object::New<SceneViewerContext>(width, height));
  self->viewer_ = new Object::Ref<SceneViewerContext>(viewer);
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSceneViewer::tp_dealloc(PythonClassSceneViewer* self) {
  BA_PYTHON_TRY;

  // These have to be deleted in the logic thread - push a call if
  // need be.. otherwise do it immediately.
  Object::Ref<SceneViewerContext>* ptr = self->viewer_;
  if (!g_base->InLogicThread()) {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  } else {
    delete ptr;
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassSceneViewer::tp_repr(PythonClassSceneViewer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("s", std::string("<bascenev1.SceneViewer at "
                                        + Utils::PtrToString(self) + ">")
                                .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::GetContext(PythonClassSceneViewer* self,
                                        void* closure) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  return base::PythonClassContextRef::Create(self->GetViewer());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::GetTexture(PythonClassSceneViewer* self,
                                        void* closure) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  return ui_v1::PythonClassUITexture::Create(
      self->GetViewer()->view()->texture());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::GetSource(PythonClassSceneViewer* self,
                                       void* closure) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  return ui_v1::PythonClassViewerSource::Create(
      self->GetViewer()->viewer_source());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::SetCamera(PythonClassSceneViewer* self,
                                       PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  PyObject* position_obj;
  PyObject* target_obj;
  float field_of_view{30.0f};
  float near_clip{1.0f};
  float far_clip{100.0f};
  float min_horizontal_field_of_view{0.0f};
  static const char* kwlist[] = {
      "position",  "target",   "field_of_view",
      "near_clip", "far_clip", "min_horizontal_field_of_view",
      nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|ffff",
                                   const_cast<char**>(kwlist), &position_obj,
                                   &target_obj, &field_of_view, &near_clip,
                                   &far_clip, &min_horizontal_field_of_view)) {
    return nullptr;
  }
  Vector3f position = base::BasePython::GetPyVector3f(position_obj);
  Vector3f target = base::BasePython::GetPyVector3f(target_obj);
  if ((target - position).LengthSquared() < 0.000001f) {
    throw Exception("Camera position and target must differ.",
                    PyExcType::kValue);
  }
  if (field_of_view < 1.0f || field_of_view > 170.0f) {
    throw Exception("field_of_view must be 1-170 degrees.", PyExcType::kValue);
  }
  if (near_clip <= 0.0f || far_clip <= near_clip) {
    throw Exception("near_clip must be > 0 and far_clip > near_clip.",
                    PyExcType::kValue);
  }
  if (min_horizontal_field_of_view < 0.0f
      || min_horizontal_field_of_view > 170.0f) {
    throw Exception("min_horizontal_field_of_view must be 0-170 degrees.",
                    PyExcType::kValue);
  }
  base::FixedCamera* camera = self->GetViewer()->camera();
  camera->set_position(position);
  camera->set_target(target);
  camera->set_field_of_view_y(field_of_view);
  camera->set_min_field_of_view_x(min_horizontal_field_of_view);
  camera->SetClip(near_clip, far_clip);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::SetSize(PythonClassSceneViewer* self,
                                     PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  int width;
  int height;
  static const char* kwlist[] = {"width", "height", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "ii", const_cast<char**>(kwlist), &width, &height)) {
    return nullptr;
  }
  CheckSize_(width, height);
  self->GetViewer()->SetSize(width, height);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::SetSound(PythonClassSceneViewer* self,
                                      PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  int enabled{};
  float volume{1.0f};
  float pan_scale{1.0f};
  static const char* kwlist[] = {"enabled", "volume", "pan_scale", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p|ff",
                                   const_cast<char**>(kwlist), &enabled,
                                   &volume, &pan_scale)) {
    return nullptr;
  }
  if (volume < 0.0f || pan_scale < 0.0f) {
    throw Exception("volume and pan_scale must be >= 0.", PyExcType::kValue);
  }
  self->GetViewer()->SetSound(static_cast<bool>(enabled), volume, pan_scale);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::SetCameraShake(PythonClassSceneViewer* self,
                                            PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float strength{0.0f};
  float stiffness{30.0f};
  float damping{2.0f};
  float poke_interval_min{0.5f};
  float poke_interval_max{1.0f};
  static const char* kwlist[] = {"strength",          "stiffness",
                                 "damping",           "poke_interval_min",
                                 "poke_interval_max", nullptr};
  if (!PyArg_ParseTupleAndKeywords(
          args, keywds, "f|ffff", const_cast<char**>(kwlist), &strength,
          &stiffness, &damping, &poke_interval_min, &poke_interval_max)) {
    return nullptr;
  }
  if (strength < 0.0f || stiffness < 0.0f || damping < 0.0f) {
    throw Exception("strength, stiffness, and damping must be >= 0.",
                    PyExcType::kValue);
  }
  if (poke_interval_min <= 0.0f || poke_interval_max < poke_interval_min) {
    throw Exception("poke intervals must be > 0, with max no smaller than min.",
                    PyExcType::kValue);
  }
  self->GetViewer()->camera()->SetShake(strength, stiffness, damping,
                                        poke_interval_min, poke_interval_max);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::SetDepthOfField(PythonClassSceneViewer* self,
                                             PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  PyObject* focus_obj;
  PyObject* blur_obj{Py_None};
  static const char* kwlist[] = {"focus", "blur", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|O",
                                   const_cast<char**>(kwlist), &focus_obj,
                                   &blur_obj)) {
    return nullptr;
  }
  base::DepthOfField dof;
  if (focus_obj == Py_None) {
    if (blur_obj != Py_None) {
      throw Exception("blur can't be given without focus.", PyExcType::kValue);
    }
    dof.mode = base::DepthOfField::Mode::kOff;
  } else {
    if (blur_obj == Py_None) {
      throw Exception("blur must be given along with focus.",
                      PyExcType::kValue);
    }
    auto focus = Python::GetFloats(focus_obj);
    auto blur = Python::GetFloats(blur_obj);
    if (focus.size() != 2 || blur.size() != 2) {
      throw Exception("focus and blur must each be 2 distances.",
                      PyExcType::kValue);
    }
    if (!(blur[0] >= 0.0f && blur[0] < focus[0] && focus[0] <= focus[1]
          && focus[1] < blur[1])) {
      throw Exception(
          "Distances must run blur[0] < focus[0] <= focus[1] < blur[1],"
          " none negative.",
          PyExcType::kValue);
    }
    dof.mode = base::DepthOfField::Mode::kRange;
    dof.blur_near = blur[0];
    dof.focus_near = focus[0];
    dof.focus_far = focus[1];
    dof.blur_far = blur[1];
  }
  self->GetViewer()->camera()->set_depth_of_field(dof);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PythonClassSceneViewer::Shutdown(PythonClassSceneViewer* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());

  // Doing this more than once is fine.
  if (SceneViewerContext* viewer = self->viewer_->get()) {
    viewer->Shutdown();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassSceneViewer::tp_methods[] = {
    {"set_camera", (PyCFunction)SetCamera, METH_VARARGS | METH_KEYWORDS,
     "set_camera(position: Sequence[float], target: Sequence[float],\n"
     "  field_of_view: float = 30.0, near_clip: float = 1.0,\n"
     "  far_clip: float = 100.0,\n"
     "  min_horizontal_field_of_view: float = 0.0) -> None\n"
     "\n"
     "Set where the scene is seen from and what is looked at.\n"
     "\n"
     "Field of view is vertical, in degrees, so what is looked at\n"
     "takes up the same share of the picture's height whatever\n"
     "shape the picture is. A picture narrow enough to see less\n"
     "across than min_horizontal_field_of_view (if one is given)\n"
     "sees that much across and more up and down instead, so that\n"
     "what is looked at gets smaller rather than cut off at the\n"
     "sides.\n"
     "\n"
     "Nothing nearer than near_clip or farther than far_clip gets\n"
     "drawn; keep the span between them no wider than the scene\n"
     "needs."},
    {"set_sound", (PyCFunction)SetSound, METH_VARARGS | METH_KEYWORDS,
     "set_sound(enabled: bool, volume: float = 1.0,\n"
     "  pan_scale: float = 1.0) -> None\n"
     "\n"
     "Let the scene make sound (viewers start out silent).\n"
     "\n"
     "Sounds are heard as the viewer's camera would hear them, not\n"
     "the game's: placed relative to it (its steady aim; shake is\n"
     "left out), their gain scaled by volume, and how far to the\n"
     "sides they sit scaled by pan_scale (more pans them wider)."},
    {"set_camera_shake", (PyCFunction)SetCameraShake,
     METH_VARARGS | METH_KEYWORDS,
     "set_camera_shake(strength: float, stiffness: float = 30.0,\n"
     "  damping: float = 2.0, poke_interval_min: float = 0.5,\n"
     "  poke_interval_max: float = 1.0) -> None\n"
     "\n"
     "Give the camera a hand-held shake.\n"
     "\n"
     "The camera stays where it is, but its aim wobbles left/right\n"
     "and up/down on a damped spring, kicked in a random direction\n"
     "every so often (a random time between the two poke intervals,\n"
     "in seconds, apart). Strength is the size of a kick in degrees\n"
     "per second of spin; 0 turns shake off. Stiffness and damping\n"
     "shape the spring: stiffer wobbles faster, more damping settles\n"
     "sooner. Still while camera shake is disabled."},
    {"set_depth_of_field", (PyCFunction)SetDepthOfField,
     METH_VARARGS | METH_KEYWORDS,
     "set_depth_of_field(focus: tuple[float, float] | None,\n"
     "  blur: tuple[float, float] | None = None) -> None\n"
     "\n"
     "Set what of the scene is in focus.\n"
     "\n"
     "Both are pairs of distances out from the camera along the way\n"
     "it is looking, nearer one first. Everything between the two\n"
     "focus distances is sharp; from there things get blurrier out\n"
     "to the blur distances (which lie outside the focus ones),\n"
     "past which they are as blurry as things get. Pass None for\n"
     "focus to have everything in focus, which is how viewers\n"
     "start out.\n"
     "\n"
     "This shows only where graphics quality is high or better;\n"
     "below that everything is sharp regardless."},
    {"set_size", (PyCFunction)SetSize, METH_VARARGS | METH_KEYWORDS,
     "set_size(width: int, height: int) -> None\n"
     "\n"
     "Set the size of our texture in pixels."},
    {"shutdown", (PyCFunction)Shutdown, METH_NOARGS,
     "shutdown() -> None\n"
     "\n"
     "Take the scene down for good.\n"
     "\n"
     "Everything in it is destroyed and most calls on this object\n"
     "raise from here on. Happens by itself when this object goes\n"
     "away; call it to not depend on when that is."},
    {nullptr}  // Sentinel
};

PyGetSetDef PythonClassSceneViewer::tp_getsets[] = {
    {const_cast<char*>("context"), (getter)GetContext, nullptr,
     const_cast<char*>(
         "context: bascenev1.ContextRef\n"
         "\n"
         "The context of our scene. Things created with this as the\n"
         "current context are created in our scene."),
     nullptr},
    {const_cast<char*>("source"), (getter)GetSource, nullptr,
     const_cast<char*>(
         "source: bauiv1.ViewerSource\n"
         "\n"
         "Us as something a viewer widget can show. It holds no claim\n"
         "on us; a widget showing it once we are gone shows nothing."),
     nullptr},
    {const_cast<char*>("texture"), (getter)GetTexture, nullptr,
     const_cast<char*>(
         "texture: bauiv1.Texture\n"
         "\n"
         "The texture our scene is drawn to. Use it like any other;\n"
         "on an image widget, for instance."),
     nullptr},
    {nullptr}  // Sentinel
};

}  // namespace ballistica::scene_v1
