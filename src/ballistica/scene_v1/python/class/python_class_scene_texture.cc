// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_texture.h"

#include <string>

#include "ballistica/base/logic/logic.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneTexture::tp_repr(PythonClassSceneTexture* self)
    -> PyObject* {
  BA_PYTHON_TRY;
  auto&& t = *(self->texture_);
  return Py_BuildValue(
      "s", (std::string("<bascenev1.Texture ")
            + (t.exists() ? ("\"" + t->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassSceneTexture::type_name() -> const char* { return "Texture"; }

void PythonClassSceneTexture::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Texture";
  cls->tp_basicsize = sizeof(PythonClassSceneTexture);
  cls->tp_doc =
      "A reference to a texture.\n"
      "\n"
      "Use :meth:`bascenev1.gettexture()` to instantiate one.";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSceneTexture::Create(SceneTexture* texture) -> PyObject* {
  assert(texture != nullptr);

  // Ask Python to create one of us, which will call our tp_new method.
  s_create_empty_ = true;  // prevent class from erroring on create
  assert(TypeIsSetUp(&type_obj));
  auto* t = reinterpret_cast<PythonClassSceneTexture*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("bascenev1.Texture creation failed.");
  }

  // Store a reference to the provided ballistica object.
  *t->texture_ = texture;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassSceneTexture::GetTexture(bool doraise) const -> SceneTexture* {
  SceneTexture* texture = texture_->get();
  if (!texture && doraise) {
    throw Exception("Invalid Texture.", PyExcType::kNotFound);
  }
  return texture;
}

auto PythonClassSceneTexture::tp_new(PyTypeObject* type, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  auto* self =
      reinterpret_cast<PythonClassSceneTexture*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  if (!s_create_empty_) {
    throw Exception(
        "Can't instantiate Textures directly; use bascenev1.gettexture()"
        " to get them.");
  }
  self->texture_ = new Object::Ref<SceneTexture>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassSceneTexture::tp_dealloc(PythonClassSceneTexture* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be released in the logic thread.
  auto* ptr = self->texture_;
  if (g_base->InLogicThread()) {
    delete self->texture_;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassSceneTexture::s_create_empty_ = false;
PyTypeObject PythonClassSceneTexture::type_obj;

}  // namespace ballistica::scene_v1
